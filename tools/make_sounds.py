#!/usr/bin/env python3
"""
Writes the sounds and the music of the game to data/, synthesized from scratch:

    data/sounds/<group>/<name>.wav       a sound effect. The game plays it as "<group>.<name>", e.g "hero.crossed"
    data/sounds/<group>/<name>_<n>.wav   variants of the same sound: the game picks one at random
    data/music/<name>.ogg                music and loops, streamed: "theme" and "traffic"

    python3 tools/make_sounds.py         (needs numpy, scipy and soundfile)

The aim is the sound of a fantasy game rather than of an 8-bit one: every effect is built in layers (a low body, a
transient on top, and a tail), from noise, filters, inharmonic metal, formant voices and plucked strings instead of
square waves, and all of it is put in a room with a convolution reverb. The music is a small orchestra: strings,
cellos, horns, a choir, a harp and war drums.

They are plain files: any .wav, .ogg or .mp3 dropped into data/sounds/<group>/ can be played by its name, without
changing the game.
"""

import os
import shutil
import subprocess

import numpy as np
import soundfile
from scipy import signal

RATE = 44100
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
rng = np.random.default_rng(11)


#
# Building blocks
#

def n_of(seconds):
    return int(round(seconds * RATE))


def t_of(seconds):
    return np.arange(n_of(seconds)) / RATE


def noise(seconds):
    return rng.standard_normal(n_of(seconds)) * 0.4


def env(length, attack=0.005, decay=4.0, release=0.05):
    """A quick rise, then an exponential fall over the length"""
    n = n_of(length)
    e = np.exp(-decay * np.arange(n) / max(n, 1))
    a = n_of(attack)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a) ** 2
    r = min(n_of(release), n)
    if r > 0:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def adsr(length, attack, release, sustain=1.0, decay=0.1):
    n = n_of(length)
    e = np.full(n, sustain)
    a, d, r = n_of(attack), n_of(decay), n_of(release)
    a = min(a, n)
    e[:a] = np.linspace(0, 1, a)
    d = min(d, n - a)
    e[a:a + d] = np.linspace(1, sustain, d)
    r = min(r, n)
    if r > 0:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def sos(kind, freq, order=2):
    nyq = RATE / 2
    if isinstance(freq, (list, tuple)):
        freq = [min(max(f, 10), nyq * 0.95) / nyq for f in freq]
    else:
        freq = min(max(freq, 10), nyq * 0.95) / nyq
    return signal.butter(order, freq, kind, output="sos")


def lowpass(x, cutoff, order=2):
    return signal.sosfilt(sos("low", cutoff, order), x)


def highpass(x, cutoff, order=2):
    return signal.sosfilt(sos("high", cutoff, order), x)


def bandpass(x, low, high, order=2):
    return signal.sosfilt(sos("band", [low, high], order), x)


def peak(x, freq, q):
    """A resonant peak: a band of the signal around freq, e.g a formant of a voice"""
    b, a = signal.iirpeak(min(freq, RATE * 0.45), q, fs=RATE)
    return signal.lfilter(b, a, x)


def sweep_filter(x, kind, f0, f1, block=256, order=2):
    """A filter whose frequency glides from f0 to f1 over the sound, e.g a whoosh"""
    out = np.zeros_like(x)
    blocks = (len(x) + block - 1) // block
    freqs = np.geomspace(f0, f1, max(blocks, 1))
    zi = None
    for i in range(blocks):
        f = freqs[i]
        s = sos(kind, [f / 1.6, f * 1.6] if kind == "band" else f, order)
        if zi is None:
            zi = signal.sosfilt_zi(s) * 0
        chunk = x[i * block:(i + 1) * block]
        out[i * block:(i + 1) * block], zi = signal.sosfilt(s, chunk, zi=zi)
    return out


def glide(f0, f1, seconds, curve="geom"):
    n = n_of(seconds)
    if curve == "geom":
        return np.geomspace(f0, f1, n)
    return np.linspace(f0, f1, n)


def osc(freq, shape="sine", phase=0.0):
    """An oscillator over an array of frequencies (or a number and a length via glide)"""
    ph = 2 * np.pi * np.cumsum(freq) / RATE + phase
    if shape == "saw":
        return signal.sawtooth(ph)
    if shape == "tri":
        return signal.sawtooth(ph, 0.5)
    if shape == "pulse":
        return np.sign(np.sin(ph)) * 0.5 + signal.sawtooth(ph) * 0.5
    return np.sin(ph)


def tone(freq, seconds, shape="sine"):
    return osc(np.full(n_of(seconds), float(freq)), shape)


def fm(carrier, ratio, index, seconds, index_decay=3.0):
    """A bell or a glassy tone: a carrier modulated by a partial whose depth fades"""
    t = t_of(seconds)
    mod = np.sin(2 * np.pi * carrier * ratio * t) * index * np.exp(-index_decay * t)
    return np.sin(2 * np.pi * carrier * t + mod)


def modal(freqs, decays, amps, seconds):
    """Something struck: a sum of partials that each ring out, e.g metal or glass"""
    t = t_of(seconds)
    out = np.zeros(len(t))
    for f, d, a in zip(freqs, decays, amps):
        out += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-d * t)
    return out


def pluck(freq, seconds, brightness=0.5, decay=0.996):
    """A plucked string (Karplus-Strong), e.g a harp"""
    n = n_of(seconds)
    period = max(2, int(RATE / freq))
    buf = lowpass(rng.uniform(-1, 1, period), 1500 + 6000 * brightness, 1)
    out = np.zeros(n)
    for start in range(0, n, period):
        end = min(start + period, n)
        out[start:end] = buf[:end - start]
        buf = decay * 0.5 * (buf + np.roll(buf, 1))
    return out


def voice(pitch, seconds, vowel="ah", breath=0.15, vibrato=0.0):
    """A voice: a train of pulses from the throat, shaped by the formants of a vowel"""
    formants = {
        "ah": [(800, 1.0), (1150, 0.5), (2900, 0.25)],
        "oh": [(450, 1.0), (800, 0.5), (2830, 0.15)],
        "uh": [(520, 1.0), (1190, 0.4), (2390, 0.15)],
        "eh": [(600, 1.0), (1800, 0.45), (2600, 0.2)],
        "oo": [(320, 1.0), (800, 0.3), (2400, 0.08)],
    }[vowel]
    n = n_of(seconds)
    f = np.broadcast_to(np.asarray(pitch, dtype=float), (n,)).copy()
    if vibrato:
        f *= 1 + vibrato * np.sin(2 * np.pi * 5.2 * t_of(seconds)) * np.linspace(0, 1, n)
    source = osc(f, "saw") + noise(seconds) * breath
    out = np.zeros(n)
    for fr, gain in formants:
        out += peak(source, fr, 6) * gain
    return out


def saturate(x, drive=2.0):
    return np.tanh(x * drive) / np.tanh(drive)


def reverb_ir(seconds, damp=4000, stereo=True, predelay=0.012, seed=0):
    r = np.random.default_rng(seed)
    t = t_of(seconds)
    decay = np.exp(-6.9 * t / seconds)
    channels = []
    for c in range(2 if stereo else 1):
        ir = r.standard_normal(len(t)) * decay
        # The tail darkens: mix a bright and a dark copy, from one to the other
        dark = lowpass(ir, damp * 0.3)
        bright = lowpass(ir, damp)
        mixw = np.linspace(0, 1, len(t)) ** 0.6
        ir = bright * (1 - mixw) + dark * mixw
        ir = np.concatenate([np.zeros(n_of(predelay + 0.003 * c)), ir])
        channels.append(ir / np.sqrt(np.sum(ir ** 2)))
    return channels


def reverb(x, seconds=1.4, wet=0.3, damp=5000, seed=0):
    """Puts a sound in a room: a stereo pair (left, right) of the dry sound and its convolution with a decaying noise"""
    left_ir, right_ir = reverb_ir(seconds, damp, seed=seed)
    tail = n_of(seconds) + n_of(0.05)
    dry = np.concatenate([x, np.zeros(tail)])
    left = signal.fftconvolve(dry, left_ir)[:len(dry)]
    right = signal.fftconvolve(dry, right_ir)[:len(dry)]
    return dry * (1 - wet) + left * wet, dry * (1 - wet) + right * wet


def place(out, sound, at):
    start = n_of(at)
    if start >= len(out):
        return
    end = min(start + len(sound), len(out))
    out[start:end] += sound[:end - start]


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def normalize(x, level=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * level


def save_sound(group, name, x, level=0.85, room=1.0, wet=0.22, damp=5000):
    """Saves a mono sound, put in a room of `room` seconds of reverb, as a stereo wav"""
    x = highpass(x, 25)
    if room > 0:
        left, right = reverb(x, room, wet, damp, seed=sum(name.encode()))
    else:
        left, right = x, x
    stereo = np.stack([left, right], axis=1)
    # Trim the silence at the end, and fade so there is no click
    loud = np.where(np.max(np.abs(stereo), axis=1) > np.max(np.abs(stereo)) * 0.002)[0]
    end = (loud[-1] + n_of(0.02)) if len(loud) else len(stereo)
    stereo = stereo[:end]
    fade = min(len(stereo), n_of(0.03))
    stereo[-fade:] *= np.linspace(1, 0, fade)[:, None]
    stereo = normalize(stereo, level)
    path = os.path.join(DATA, "sounds", group, name + ".wav")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    soundfile.write(path, stereo.astype(np.float32), RATE, subtype="PCM_16")
    print(os.path.relpath(path, DATA), f"{len(stereo) / RATE:.2f} s")


#
# Layers that many sounds share
#

def thud(f0=90, f1=40, seconds=0.35, drive=2.5):
    """The low body of an impact"""
    body = osc(glide(f0, f1, seconds), "sine") * env(seconds, 0.001, 5)
    return saturate(body, drive)


def crack(seconds=0.05, cutoff=2500):
    """The sharp front of an impact"""
    return highpass(noise(seconds), cutoff) * env(seconds, 0.0005, 9)


def whoosh(seconds, f0, f1, width=1.0):
    """Air moving past: noise through a band that glides, louder in the middle"""
    n = n_of(seconds)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    w = sweep_filter(noise(seconds), "band", f0, f1)
    if width > 1:
        w += sweep_filter(noise(seconds), "band", f0 * width, f1 * width) * 0.5
    return w * shape


def metal(base, seconds, ring=1.0, brightness=1.0):
    """Struck iron: inharmonic partials"""
    ratios = [1.0, 2.32, 4.25, 6.63, 9.38, 12.4, 15.9]
    freqs = [base * r for r in ratios]
    decays = [(3 + 2.5 * i) / ring for i in range(len(ratios))]
    amps = [1.0 / (1 + i * (1.6 - brightness)) for i in range(len(ratios))]
    return modal(freqs, decays, amps, seconds)


def glass_shards(seconds, count=16, start=0.0, spread=0.5):
    out = np.zeros(n_of(seconds))
    for _ in range(count):
        length = rng.uniform(0.08, 0.3)
        f = rng.uniform(2500, 7500)
        ping = modal([f, f * 1.47, f * 2.11], [30, 45, 60], [1, 0.5, 0.3], length)
        place(out, ping * rng.uniform(0.1, 0.35), start + rng.exponential(spread * 0.4))
    return out


def debris(seconds, count=20, start=0.05):
    """Small bits falling and rattling"""
    out = np.zeros(n_of(seconds))
    t = start
    for _ in range(count):
        t += rng.exponential(0.035)
        length = rng.uniform(0.02, 0.06)
        f = rng.uniform(600, 3000)
        bit = bandpass(noise(length), f * 0.7, f * 1.4) * env(length, 0.0005, 8)
        place(out, bit * rng.uniform(0.3, 1.0) * np.exp(-(t - start) * 2), t)
    return out


def chord_bells(freqs, seconds, index=2.0, ratio=3.5):
    return sum(fm(f, ratio, index, seconds, 4) * env(seconds, 0.002, 3.5) for f in freqs) / len(freqs)


#
# Sound effects
#

def hero_sounds():
    # Hurt: a heavy hit and a grunt. Two variants
    for i, (pitch, vowel) in enumerate(((150, "uh"), (125, "ah"))):
        grunt = voice(glide(pitch * 1.15, pitch * 0.8, 0.28), 0.28, vowel, breath=0.4) * env(0.28, 0.01, 3)
        hit = mix(thud(110, 50, 0.22) * 0.9, bandpass(noise(0.07), 300, 2500) * env(0.07, 0.0005, 6) * 1.4)
        save_sound("hero", f"hurt_{i + 1}", mix(hit, np.concatenate([np.zeros(n_of(0.02)), grunt * 0.55])), level=0.75, room=0.6)

    # Run over: a crash of metal, a low boom, glass and bits, in a big room
    length = 2.5
    boom = thud(70, 28, 1.2, 3.0) * 1.3
    crunch = metal(310, 0.9, ring=0.6, brightness=1.2) * env(0.9, 0.0005, 4) * 0.5
    crunch += metal(173, 0.9, ring=0.5) * env(0.9, 0.0005, 5) * 0.4
    body = bandpass(noise(0.4), 200, 3000) * env(0.4, 0.001, 6) * 1.2
    cry = voice(glide(330, 150, 0.5), 0.5, "ah", breath=0.3, vibrato=0.02) * env(0.5, 0.02, 2.5) * 0.35
    out = mix(boom, crunch, body, crack(0.04, 1500) * 2, glass_shards(length, 22, 0.03, 0.6), debris(length, 26))
    place(out, cry, 0.0)
    save_sound("hero", "death", out, level=0.9, room=1.8, wet=0.25)

    # Spawn: a swell that rises out of nothing into a soft chime, like a hero that is summoned
    length = 1.8
    swell_src = mix(*(tone(f, 1.0, "saw") for f in (146.8, 220.0, 293.7)))
    swell_src = lowpass(swell_src, 1800) * 0.4 + highpass(noise(1.0), 3000) * 0.3
    sl, _ = reverb(swell_src * env(1.0, 0.01, 6), 1.2, 0.9, 6000, seed=4)
    swell = sl[::-1][-n_of(0.9):] * np.linspace(0, 1, n_of(0.9)) ** 2      # Reversed: it grows towards the chime
    chime = chord_bells([587.3, 880.0, 1174.7, 1480.0], 1.4, index=1.6, ratio=3.01)
    out = np.zeros(n_of(length))
    place(out, swell * 0.8, 0.0)
    place(out, mix(chime * 0.7, thud(120, 80, 0.3, 1.5) * 0.4), 0.88)
    save_sound("hero", "spawn", out, level=0.6, room=1.6, wet=0.35)

    # Across: a short fanfare of brass with timpani and a choir, in D major
    length = 3.0
    out = np.zeros(n_of(length))
    def brass(freq, seconds, accent=1.0):
        n = n_of(seconds)
        f = np.full(n, freq) * (1 + 0.004 * np.sin(2 * np.pi * 5 * t_of(seconds)) * np.linspace(0, 1, n))
        raw = osc(f, "saw") + osc(f * 1.003, "saw") * 0.7
        bright = sweep_filter(raw, "low", 600 + 2600 * accent, 900, order=2)        # The blat of a horn
        return bright * adsr(seconds, 0.03, 0.25, 0.8, 0.2)
    pickup = [(293.7, 0.0, 0.18), (370.0, 0.16, 0.18), (440.0, 0.32, 0.18)]
    for f, at, d in pickup:
        place(out, brass(f, d + 0.05, 0.7) * 0.5, at)
    for f in (293.7, 370.0, 440.0, 587.3):
        place(out, brass(f, 1.9, 1.0) * 0.45, 0.5)
        place(out, brass(f / 2, 1.9, 0.6) * 0.3, 0.5)
    timpani = lambda f: mix(saturate(osc(glide(f * 1.08, f, 0.9)) * env(0.9, 0.002, 3.5), 1.5), bandpass(noise(0.08), 100, 800) * env(0.08, 0.001, 8) * 0.5)
    for k in range(6):
        place(out, timpani(73.4) * (0.2 + 0.06 * k), k * 0.07)
    place(out, timpani(73.4) * 0.9, 0.5)
    for f in (293.7, 440.0, 587.3):
        place(out, voice(f, 2.0, "ah", 0.08, 0.012) * adsr(2.0, 0.25, 0.8, 0.9) * 0.08, 0.5)
    place(out, glass_shards(1.5, 12, 0.0, 1.0) * 0.6, 0.55)
    save_sound("hero", "crossed", out, level=0.8, room=2.2, wet=0.3)


def ability_sounds():
    # Sprint: a rush of wind that rises, and quick light steps
    length = 0.9
    out = whoosh(length, 300, 2600, 1.8) * 1.4
    for k in range(5):
        place(out, bandpass(noise(0.03), 800, 3000) * env(0.03, 0.001, 8) * 0.4, 0.1 + k * 0.11)
    save_sound("ability", "sprint", out, level=0.7, room=0.8)

    # Charge: a roar and a stomp, and the air he pushes ahead
    length = 1.0
    roar = voice(glide(95, 70, 0.8), 0.8, "oh", breath=0.6, vibrato=0.03) * adsr(0.8, 0.05, 0.3, 0.9)
    roar = saturate(roar * 2, 2.5)
    out = mix(roar * 0.6, whoosh(length, 200, 900, 2.0) * 0.8)
    place(out, mix(thud(80, 35, 0.5, 3) * 0.9, crack(0.03, 800)), 0.0)
    save_sound("ability", "charge", out, level=0.8, room=1.0)

    # Blink: a crack, a zip that falls away, and a glittering tail where he appears
    length = 0.8
    zip_ = osc(glide(4200, 280, 0.14), "sine") * env(0.14, 0.001, 2) * 0.6
    zip_ += sweep_filter(noise(0.14), "band", 6000, 900) * 0.8
    sparkle = chord_bells([2637, 3136, 3951], 0.6, 2.5, 2.0) * 0.25
    out = mix(crack(0.02, 3000) * 1.5, zip_)
    place(out, mix(sparkle, crack(0.015, 4000) * 0.6), 0.12)
    save_sound("ability", "blink", out, level=0.65, room=1.2, wet=0.32)

    # The hook: thrown with a heavy whoosh and a running chain, and it bites with a clang of iron
    length = 0.7
    out = whoosh(length, 250, 1400, 1.5) * 1.0
    t = 0.0
    for k in range(14):
        t += 0.045 - k * 0.0015
        f = rng.uniform(1800, 3200)
        link = metal(f / 4, 0.06, ring=0.15) * env(0.06, 0.0003, 6)
        place(out, link * 0.35, t)
    save_sound("ability", "hook_throw", out, level=0.7, room=0.7)

    length = 1.2
    clang = metal(196, length, ring=1.2, brightness=1.1) * env(length, 0.0005, 4) * 0.7
    out = mix(clang, thud(140, 60, 0.25, 2) * 0.8, crack(0.03, 1200) * 1.6)
    place(out, bandpass(noise(0.12), 200, 1400) * env(0.12, 0.002, 5) * 0.8, 0.03)     # Into flesh, or turf
    save_sound("ability", "hook_hit", out, level=0.8, room=1.0)

    # Freeze: a gust of cold air, glass that rings, the crackle of ice forming, and a deep thump
    length = 2.0
    gust = whoosh(1.2, 2500, 600, 1.6) * 0.7
    bells = sum(fm(f, 3.7, 3.0, length, 2.5) * env(length, 0.002, 3.0) for f in (1318.5, 1975.5, 2637.0, 3520.0)) * 0.12
    crackle = np.zeros(n_of(length))
    t = 0.05
    while t < 1.4:
        t += rng.exponential(0.018)
        length_c = rng.uniform(0.004, 0.015)
        c = highpass(noise(length_c), rng.uniform(2500, 6000)) * env(length_c, 0.0002, 5)
        place(crackle, c * rng.uniform(0.3, 1.0) * np.exp(-t * 1.5), t)
    out = mix(gust, bells, crackle * 1.2, thud(65, 40, 0.6, 2) * 0.6)
    save_sound("ability", "freeze", out, level=0.75, room=2.0, wet=0.35, damp=7000)

    # Fade: breath that turns into a ghostly choir, which leaves a hollow echo
    length = 1.6
    t = t_of(length)
    choir = sum(voice(f * (1 + 0.006 * np.sin(2 * np.pi * (0.7 + k) * t)), length, "oo", 0.5, 0.02) for k, f in enumerate((392, 466.2, 587.3)))
    choir *= adsr(length, 0.35, 0.9, 0.8, 0.3)
    air = whoosh(length, 1200, 4000) * 0.5
    save_sound("ability", "fade", mix(choir * 0.3, air), level=0.55, room=2.5, wet=0.5, damp=6000)

    # Leap: a shout and the air rushing by. Land: the ground takes him, with dirt and stones
    length = 0.9
    shout = voice(glide(170, 210, 0.3), 0.3, "ah", breath=0.5) * env(0.3, 0.01, 2.5)
    out = mix(saturate(shout * 2, 2) * 0.5, whoosh(length, 300, 2000, 1.8) * 1.0)
    save_sound("ability", "leap", out, level=0.75, room=0.8)

    length = 1.6
    out = mix(thud(60, 26, 1.0, 3.5) * 1.3, crack(0.04, 700) * 1.5, bandpass(noise(0.5), 100, 1500) * env(0.5, 0.002, 5) * 0.9,
              debris(length, 30, 0.04) * 1.2)
    save_sound("ability", "land", out, level=0.85, room=1.4, wet=0.25)

    # Stop!: a crossing guard's whistle, and the cars braking hard
    length = 2.2
    t = t_of(0.7)
    trill = 1 + 0.035 * np.sign(np.sin(2 * np.pi * 26 * t)) * 0.5 + 0.02 * np.sin(2 * np.pi * 26 * t)
    whistle = osc(2950 * trill) * adsr(0.7, 0.02, 0.08, 0.9) + bandpass(noise(0.7), 2500, 4000) * adsr(0.7, 0.01, 0.08, 0.7) * 0.8
    whistle += osc(5900 * trill) * adsr(0.7, 0.02, 0.08, 0.9) * 0.12
    out = np.zeros(n_of(length))
    place(out, whistle * 0.35, 0.0)
    for k, (f, at) in enumerate(((1850, 0.5), (2300, 0.62), (1600, 0.75))):        # Squealing brakes
        d = rng.uniform(0.9, 1.3)
        tt = t_of(d)
        squeal = osc(f * (1 + 0.01 * np.sin(2 * np.pi * 7 * tt)) * np.linspace(1.03, 0.97, len(tt)), "tri")
        squeal = bandpass(squeal, f * 0.8, f * 3) * adsr(d, 0.06, 0.3, 0.8) * 0.12
        squeal += bandpass(noise(d), 1500, 5000) * adsr(d, 0.05, 0.3, 0.7) * 0.1
        place(out, squeal, at)
    save_sound("ability", "stop_sign", out, level=0.7, room=1.2, wet=0.28)

    # Time warp: the world drops in pitch and slows down, with a clock that ticks slower and slower
    length = 2.6
    dive = sum(osc(glide(f, f / 4, 1.8), "saw") for f in (220, 221.5, 329.6, 331.0))
    dive = sweep_filter(dive, "low", 3000, 200) * adsr(1.8, 0.02, 0.6, 0.8, 0.2) * 0.35
    rise = whoosh(0.5, 400, 3000)[::-1] * 0.6                                          # Reversed: it sucks in
    out = np.zeros(n_of(length))
    place(out, rise, 0.0)
    place(out, mix(dive, thud(90, 30, 1.2, 2) * 0.7), 0.45)
    tick = lambda f: mix(bandpass(noise(0.03), f * 0.8, f * 1.2) * env(0.03, 0.0005, 7), modal([f, f * 2.7], [60, 90], [0.5, 0.2], 0.05))
    t = 0.5
    gap = 0.12
    for k in range(9):
        place(out, tick(1800 if k % 2 == 0 else 1500) * 0.4, t)
        t += gap
        gap *= 1.22
    save_sound("ability", "time_warp", out, level=0.75, room=2.4, wet=0.4, damp=4500)

    # Rewind: a sound played backwards, with a tape winding back
    length = 1.3
    forward = mix(chord_bells([659.3, 987.8, 1318.5], 1.0, 2.0, 2.0) * 0.6, crack(0.02, 2500))
    fl, _ = reverb(forward, 1.0, 0.6, 7000, seed=9)
    backwards = fl[::-1][-n_of(1.0):]
    tape = osc(glide(300, 2400, 0.9) * (1 + 0.15 * np.sin(2 * np.pi * 18 * t_of(0.9))), "tri") * adsr(0.9, 0.05, 0.1, 0.8) * 0.12
    tape = bandpass(tape, 300, 5000)
    out = mix(backwards * 0.9, tape, whoosh(1.0, 3000, 500) * 0.4)
    place(out, mix(crack(0.02, 3000), thud(150, 90, 0.15, 1.2) * 0.5), 0.98)
    save_sound("ability", "rewind", out, level=0.65, room=1.0, wet=0.3)

    # Shield bash: a heavy wooden thump with iron in it, and a grunt
    length = 1.2
    wood = modal([180, 410, 690, 1130], [18, 24, 32, 45], [1, 0.6, 0.35, 0.2], 0.4)
    out = mix(thud(95, 45, 0.5, 3.0) * 1.2, wood * 0.6, metal(260, 0.6, ring=0.4) * env(0.6, 0.0005, 5) * 0.35, crack(0.03, 900) * 1.4)
    place(out, saturate(voice(glide(180, 120, 0.22), 0.22, "uh", breath=0.5) * env(0.22, 0.01, 2.5) * 2, 2) * 0.35, 0.0)
    save_sound("ability", "shield_bash", out, level=0.85, room=1.0)

    # Time lock: a clock that stops with a clunk, inside a deep shimmer, and chains
    length = 2.2
    out = np.zeros(n_of(length))
    tick = lambda f: mix(bandpass(noise(0.03), f * 0.8, f * 1.2) * env(0.03, 0.0005, 7), modal([f, f * 2.7], [60, 90], [0.5, 0.2], 0.05))
    for k in range(4):
        place(out, tick(1700 if k % 2 == 0 else 1400) * 0.35, k * 0.09)
    place(out, mix(thud(70, 50, 0.6, 1.5) * 0.8, metal(130, 1.2, ring=1.5) * env(1.2, 0.001, 3) * 0.4), 0.36)
    hum = sum(osc(glide(f, f * 0.98, 1.6), "saw") for f in (110, 110.6, 165))
    place(out, lowpass(hum, 900) * adsr(1.6, 0.2, 0.8, 0.8) * 0.12, 0.36)
    for k in range(6):
        place(out, metal(rng.uniform(450, 700), 0.08, ring=0.15) * env(0.08, 0.0003, 6) * 0.3, 0.4 + k * 0.05)
    save_sound("ability", "time_lock", out, level=0.75, room=2.0, wet=0.35)


def ui_sounds():
    # Not ready: a short, muted knock of wood, low enough not to annoy
    knock = mix(modal([196, 452, 905], [40, 60, 90], [1, 0.4, 0.15], 0.15), bandpass(noise(0.02), 300, 1200) * env(0.02, 0.0005, 6) * 0.5)
    save_sound("ui", "not_ready", knock, level=0.4, room=0.3, wet=0.1)


def item_sounds():
    # Picking an item up: a quick rising arpeggio of bells
    out = np.zeros(n_of(1.0))
    for k, f in enumerate((784, 988, 1175, 1568)):
        place(out, chord_bells([f], 0.7, index=1.5) * (0.5 + 0.1 * k), k * 0.06)
    save_sound("item", "pickup", out, level=0.6, room=1.2, wet=0.25)


#
# Music, rendered as loops that start again without a seam: what rings past the end is added to the start
#

def save_music(left, right, name, loop_samples):
    for channel in (left, right):
        tail = channel[loop_samples:]
        channel[:len(tail)] += tail
    stereo = np.stack([left[:loop_samples], right[:loop_samples]], axis=1)
    stereo = stereo / (np.max(np.abs(stereo)) or 1) * 0.75     # Room for the encoder, which overshoots
    path = os.path.join(DATA, "music", name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # libsndfile can crash writing long Vorbis files, so ffmpeg encodes them when it is there
    if shutil.which("ffmpeg"):
        wav = path + ".tmp.wav"
        soundfile.write(wav, stereo.astype(np.float32), RATE, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "6", path], check=True)
        os.remove(wav)
    else:
        soundfile.write(path, stereo.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
    print(os.path.relpath(path, DATA), f"{loop_samples / RATE:.1f} s")


NOTE_NAMES = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3,
              "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}


def note_freq(name):
    octave = int(name[-1])
    return 440.0 * 2 ** ((NOTE_NAMES[name[:-1]] + 12 * (octave - 4)) / 12)


class Score:
    """Stereo tracks, each sent to the hall reverb by its own amount"""

    def __init__(self, seconds):
        self.n = n_of(seconds)
        self.dry = [np.zeros(self.n), np.zeros(self.n)]
        self.send = np.zeros(self.n)

    def add(self, sound, at, pan=0.0, gain=1.0, wet=0.3):
        start = n_of(at)
        if start >= self.n:
            return
        end = min(start + len(sound), self.n)
        s = sound[:end - start] * gain
        left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.dry[0][start:end] += s * left * (1 - wet * 0.5)
        self.dry[1][start:end] += s * right * (1 - wet * 0.5)
        self.send[start:end] += s * wet

    def render(self, hall=3.2):
        left_ir, right_ir = reverb_ir(hall, 5000, predelay=0.03, seed=21)
        wet_l = signal.fftconvolve(self.send, left_ir)[:self.n]
        wet_r = signal.fftconvolve(self.send, right_ir)[:self.n]
        return self.dry[0] + wet_l * 0.9, self.dry[1] + wet_r * 0.9


def strings(freq, seconds, attack=0.6, voices=5, cutoff=2400):
    """A section of strings: detuned saws with a slow bow and a little vibrato"""
    n = n_of(seconds)
    t = t_of(seconds)
    out = np.zeros(n)
    for v in range(voices):
        detune = 1 + (v - (voices - 1) / 2) * 0.0035
        vib = 1 + 0.003 * np.sin(2 * np.pi * (5 + v * 0.3) * t + v)
        out += osc(freq * detune * vib, "saw", v)
    out = lowpass(out / voices, cutoff, 2)
    out = peak(out, 400, 1.2) * 0.4 + out                                   # The wooden body
    return out * adsr(seconds, attack, min(0.8, seconds * 0.4), 0.85, 0.2)


def cello(freq, seconds, accent=1.0):
    """A short, driving bowed note"""
    n = n_of(seconds)
    raw = osc(np.full(n, freq), "saw") + osc(np.full(n, freq * 1.004), "saw") * 0.6
    raw = sweep_filter(raw, "low", 1500 * accent, 500)
    return raw * adsr(seconds, 0.02, seconds * 0.5, 0.6, seconds * 0.3)


def horn(freq, seconds, swell=0.25):
    """A French horn: a mellow saw with a filter that opens as it swells"""
    n = n_of(seconds)
    t = t_of(seconds)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t) * np.clip(t / 0.4, 0, 1)
    raw = osc(freq * vib, "saw") + osc(freq * vib * 1.002, "tri") * 0.5
    e = adsr(seconds, swell, min(0.4, seconds * 0.3), 0.9, 0.2)
    out = np.zeros(n)
    # The brightness follows the loudness, in blocks
    block = 512
    zi = None
    for i in range(0, n, block):
        level = e[i]
        s = sos("low", 350 + 1500 * level)
        if zi is None:
            zi = signal.sosfilt_zi(s) * 0
        out[i:i + block], zi = signal.sosfilt(s, raw[i:i + block], zi=zi)
    return out * e


def choir(freq, seconds, vowel="ah"):
    out = sum(voice(freq * (1 + d), seconds, vowel, 0.25, 0.01) for d in (-0.004, 0.0, 0.005))
    return out * adsr(seconds, 0.7, 1.0, 0.9, 0.4) / 3


def war_drum(seconds=1.4, pitch=58):
    body = osc(glide(pitch * 1.6, pitch, 0.25, "lin").tolist() + [pitch] * (n_of(seconds) - n_of(0.25)))
    body = saturate(body * env(seconds, 0.002, 4), 1.8)
    skin = bandpass(noise(0.12), 80, 900) * env(0.12, 0.001, 6)
    return mix(body, skin * 0.7)


def tom(pitch, seconds=0.6):
    return mix(saturate(osc(glide(pitch * 1.4, pitch, 0.08, "lin").tolist() + [pitch] * (n_of(seconds) - n_of(0.08))) * env(seconds, 0.001, 6), 1.5),
               bandpass(noise(0.06), 200, 2000) * env(0.06, 0.001, 7) * 0.4)


def cymbal_swell(seconds):
    c = highpass(noise(seconds), 5000) + metal(410, seconds, 3, 1.5) * 0.05
    return c * np.linspace(0, 1, n_of(seconds)) ** 3


def make_theme():
    """A heroic loop in D minor for a small orchestra: 24 bars at 84 BPM"""
    bpm = 84
    beat = 60 / bpm
    bar = 4 * beat
    bars = 24
    loop_seconds = bars * bar
    score = Score(loop_seconds + 5)

    # i - VI - III - VII - iv - VI - VII - V, in D minor
    progression = [("D", ["D", "F", "A"]), ("Bb", ["Bb", "D", "F"]), ("F", ["F", "A", "C"]), ("C", ["C", "E", "G"]),
                   ("G", ["G", "Bb", "D"]), ("Bb", ["Bb", "D", "F"]), ("C", ["C", "E", "G"]), ("A", ["A", "C#", "E"])]
    opening = [0, 0, 1, 1, 2, 2, 3, 7]                  # Slower at first: two bars a chord
    chord_of_bar = [progression[opening[b]] if b < 8 else progression[(b - 8) % 8] for b in range(bars)]

    for b in range(bars):
        t0 = b * bar
        root, chord = chord_of_bar[b]
        intro = b < 4
        full = b >= 16

        # Strings: the chord, sustained over the bar, spread wide
        for k, name in enumerate(chord):
            octave = 3 if k == 0 else 4
            f = note_freq(name + str(octave))
            score.add(strings(f, bar + 0.4, attack=0.5 if intro else 0.25), t0, pan=-0.6 + 0.6 * k, gain=0.13, wet=0.45)
        if full:
            f = note_freq(chord[1] + "5")
            score.add(strings(f, bar + 0.3, attack=0.3, cutoff=3200), t0, pan=0.4, gain=0.07, wet=0.5)

        # Cellos and basses: the root in driving eighths, once the intro is over
        if not intro:
            f = note_freq(root + "2")
            for e in range(8):
                accent = 1.0 if e % 4 == 0 else 0.6
                octave = 2 if e in (3, 7) else 1
                score.add(cello(f * octave, beat * 0.45, accent), t0 + e * beat / 2, pan=-0.2, gain=0.22 * (1.1 if e % 2 == 0 else 0.85), wet=0.2)
            score.add(strings(f / 2, bar, attack=0.05, voices=3, cutoff=500), t0, gain=0.12, wet=0.1)

        # Harp: an arpeggio up and down the chord in sixteenths, in the intro and the last part
        if intro or full:
            notes = [note_freq(n + "4") for n in chord] + [note_freq(chord[0] + "5")]
            pattern = notes + notes[-2:0:-1]
            for s in range(16):
                f = pattern[s % len(pattern)]
                score.add(pluck(f, 1.2, 0.6), t0 + s * beat / 4, pan=0.5 - 0.3 * (s % 2), gain=0.11 if intro else 0.07, wet=0.4)

        # War drums: a big one on the one, and a pattern that grows
        if not intro or b == 3:
            score.add(war_drum(1.6, 52), t0, pan=0.0, gain=0.55, wet=0.35)
        if b >= 4:
            score.add(war_drum(1.2, 62), t0 + 2.5 * beat, pan=0.1, gain=0.35, wet=0.35)
            score.add(war_drum(1.2, 62), t0 + 3 * beat, pan=-0.1, gain=0.4, wet=0.35)
        if b >= 8:
            for s in (1.5, 3.5):
                score.add(tom(140), t0 + s * beat, pan=0.4, gain=0.2, wet=0.3)
        if b % 4 == 3 and b >= 4:
            for k, p in enumerate((180, 160, 140, 120, 105, 95)):                  # A fill into the next phrase
                score.add(tom(p), t0 + 3 * beat + k * beat / 6, pan=-0.5 + k * 0.2, gain=0.22, wet=0.3)
            score.add(cymbal_swell(bar * 0.5), t0 + bar * 0.5, pan=0.3, gain=0.08, wet=0.6)

        # Choir: long ahs from bar 13
        if b >= 12:
            for k, name in enumerate(chord):
                f = note_freq(name + ("4" if k else "3"))
                score.add(choir(f, bar + 0.5), t0, pan=-0.3 + 0.3 * k, gain=0.12, wet=0.55)

    # The horns: the melody, first alone, then an octave up with a second horn under it
    melody_a = [("A4", 1.5), ("D5", 0.5), ("F5", 1), ("E5", 1),
                ("D5", 1.5), ("C5", 0.5), ("Bb4", 2),
                ("A4", 1.5), ("F4", 0.5), ("C5", 1.5), ("Bb4", 0.5),
                ("A4", 2), ("E4", 2),
                ("F4", 1.5), ("G4", 0.5), ("A4", 1), ("D5", 1),
                ("C5", 1.5), ("Bb4", 0.5), ("A4", 1), ("G4", 1),
                ("F4", 1), ("A4", 1), ("G4", 1), ("E4", 1),
                ("D4", 3), ("C#4", 1)]
    melody_b = [("D5", 1), ("E5", 1), ("F5", 1.5), ("G5", 0.5), ("A5", 2), ("F5", 2),
                ("G5", 1), ("F5", 1), ("E5", 1), ("C5", 1), ("D5", 2), ("A4", 2),
                ("Bb4", 1), ("C5", 1), ("D5", 1), ("F5", 1), ("E5", 2), ("C5", 2),
                ("D5", 1.5), ("E5", 0.5), ("C#5", 2), ("A4", 4)]

    def play_melody(melody, start_bar, octave=1.0, gain=0.16, harmony=False):
        t = start_bar * bar
        for name, beats in melody:
            f = note_freq(name) * octave
            length = beats * beat
            score.add(horn(f, length + 0.08, swell=min(0.2, length * 0.3)), t, pan=0.15, gain=gain, wet=0.45)
            if harmony:
                score.add(horn(f * 2 ** (-5 / 12), length + 0.08, swell=min(0.2, length * 0.3)), t, pan=-0.25, gain=gain * 0.55, wet=0.5)
            t += length

    play_melody(melody_a, 4, 1.0, 0.17)
    play_melody(melody_b, 12, 1.0, 0.15)
    play_melody(melody_a, 16, 2.0, 0.12, harmony=True)

    left, right = score.render()
    loop = n_of(loop_seconds)
    # Gentle glue on the mix
    left, right = saturate(left / np.max(np.abs(left)) * 1.2, 1.2), saturate(right / np.max(np.abs(right)) * 1.2, 1.2)
    save_music(left, right, "theme", loop)


def make_traffic():
    """The hum of the motorway: low rumble, tyres and engines passing, as a loop of 12 seconds"""
    length = 12
    loop = length * RATE
    rumble = lowpass(np.cumsum(rng.uniform(-1, 1, (length + 2) * RATE)) * 0.02, 200)       # Brown noise
    tyres = bandpass(rng.uniform(-1, 1, (length + 2) * RATE), 300, 1500) * 0.25
    left, right = rumble + tyres, rumble * 0.9 + tyres * 1.1
    for _ in range(18):                                                        # Cars passing by, left to right or back
        at = rng.uniform(0, length)
        dur = rng.uniform(1.5, 3.0)
        f = rng.uniform(70, 140)
        n = int(dur * RATE)
        engine = signal.sawtooth(2 * np.pi * np.cumsum(np.linspace(f * 1.1, f * 0.9, n)) / RATE)  # Doppler
        engine = lowpass(engine, 500) * np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.3
        start = int(at * RATE)
        pan = np.linspace(-1, 1, n) * (1 if rng.random() < 0.5 else -1)
        end = min(start + n, len(left))
        left[start:end] += (engine * (1 - pan) / 2)[:end - start]
        right[start:end] += (engine * (1 + pan) / 2)[:end - start]
    save_music(left, right, "traffic", loop)


if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    for name, make in (("hero", hero_sounds), ("ability", ability_sounds), ("ui", ui_sounds), ("item", item_sounds),
                       ("theme", make_theme), ("traffic", make_traffic)):
        if not only or name in only:
            make()
