#!/usr/bin/env python3
"""
Writes the sounds and the music of the game to data/, synthesized from scratch:

    data/sounds/<group>/<name>.wav       a sound effect. The game plays it as "<group>.<name>", e.g "car.horn"
    data/sounds/<group>/<name>_<n>.wav   variants of the same sound: the game picks one at random, e.g hero/step_1.wav
    data/music/<name>.ogg                music and loops, streamed: "theme" and "traffic"

    python3 tools/make_sounds.py         (needs numpy, scipy and soundfile)

They are plain files: any .wav, .ogg or .mp3 dropped into data/sounds/<group>/ can be played by its name, without
changing the game.
"""

import os

import numpy as np
import soundfile
from scipy import signal

RATE = 44100
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
rng = np.random.default_rng(11)


def t_of(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def env(length, attack=0.005, release=0.1, curve=4.0):
    """An envelope: a quick rise, then an exponential fall over the length"""
    n = int(length * RATE)
    e = np.exp(-curve * np.arange(n) / max(n, 1))
    a = int(attack * RATE)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    r = int(release * RATE)
    if r > 0:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (RATE / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (RATE / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, low, high, order=2):
    b, a = signal.butter(order, [low / (RATE / 2), high / (RATE / 2)], "band")
    return signal.lfilter(b, a, x)


def sweep(f0, f1, seconds, shape="sine"):
    t = t_of(seconds)
    f = np.geomspace(f0, f1, len(t))
    phase = 2 * np.pi * np.cumsum(f) / RATE
    if shape == "square":
        return np.sign(np.sin(phase))
    if shape == "saw":
        return 2 * ((phase / (2 * np.pi)) % 1) - 1
    return np.sin(phase)


def noise(seconds):
    return rng.uniform(-1, 1, int(seconds * RATE))


def tone(freq, seconds, shape="sine"):
    return sweep(freq, freq, seconds, shape)


def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def save_sound(x, group, name, peak=0.9):
    path = os.path.join(DATA, "sounds", group, name + ".wav")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fade = min(len(x), int(0.004 * RATE))
    x = x.copy()
    x[-fade:] *= np.linspace(1, 0, fade)        # No click at the end
    soundfile.write(path, normalize(x, peak).astype(np.float32), RATE, subtype="PCM_16")
    print(os.path.relpath(path, DATA))


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


#
# Sound effects
#

def hero_sounds():
    for i in range(4):                              # Footsteps on grass: a soft thump and a bit of rustle
        length = 0.09 + 0.02 * i
        thump = tone(90 + 15 * i, length) * env(length, 0.002, 0.02, 8)
        rustle = lowpass(noise(length), 1800 + 300 * i) * env(length, 0.002, 0.03, 10)
        save_sound(thump * 0.6 + rustle * 0.8, "hero", f"step_{i + 1}", peak=0.5)

    length = 0.35                                   # Hurt: a hit, and a short groan going down
    hit = lowpass(noise(0.08), 900) * env(0.08, 0.001, 0.02, 6)
    groan = sweep(260, 140, length, "saw")
    groan = bandpass(groan, 300, 1400) * env(length, 0.02, 0.1, 3)
    save_sound(mix(hit, groan * 0.7), "hero", "hurt", peak=0.7)

    length = 1.2                                    # Run over: a crash, a boom, and glass
    crash = lowpass(noise(length), 3000) * env(length, 0.001, 0.2, 5)
    boom = sweep(120, 40, 0.5) * env(0.5, 0.001, 0.1, 5)
    glass = np.zeros(int(length * RATE))
    for _ in range(14):
        start = int(rng.uniform(0.05, 0.6) * RATE)
        ping_length = rng.uniform(0.1, 0.3)
        ping = tone(rng.uniform(2500, 6000), ping_length) * env(ping_length, 0.001, 0.05, 10)
        glass[start:start + len(ping)] += ping[:len(glass) - start] * 0.3
    save_sound(mix(crash * 0.8, boom * 1.2, glass), "hero", "death")

    length = 0.4                                    # Spawn: a rising sparkle
    rise = sweep(300, 1200, length) * env(length, 0.01, 0.1, 2)
    sparkle = sum(tone(f, length) * env(length, 0.05 * k, 0.1, 4) for k, f in enumerate((1320, 1760, 2640)))
    save_sound(rise * 0.5 + sparkle * 0.25, "hero", "spawn", peak=0.6)

    notes = [523.25, 659.25, 783.99, 1046.5]        # Crossed: a short fanfare up a major chord
    out = np.zeros(int(1.4 * RATE))
    for k, f in enumerate(notes):
        length = 0.9 if k == 3 else 0.22
        note = (tone(f, length, "square") * 0.3 + tone(f * 2, length) * 0.2) * env(length, 0.005, 0.05, 2.5)
        note = lowpass(note, 4000)
        start = int(k * 0.13 * RATE)
        out[start:start + len(note)] += note[:len(out) - start]
    save_sound(out, "hero", "crossed", peak=0.7)


def car_sounds():
    for i, (low, high) in enumerate(((392, 494), (330, 415))):   # Horns: two tones, a bit nasal
        length = 0.45
        horn = (tone(low, length, "square") + tone(high, length, "square")) * env(length, 0.01, 0.06, 0.6)
        horn = bandpass(horn, 300, 2500)
        save_sound(horn, "car", f"horn_{i + 1}", peak=0.6)


def ability_sounds():
    length = 0.45                                   # Sprint: a quick whoosh going up
    whoosh = noise(length)
    whoosh = np.concatenate([bandpass(whoosh[i:i + 2205], 400 + i * 0.12, 1200 + i * 0.25) for i in range(0, len(whoosh), 2205)])
    save_sound(whoosh * env(length, 0.08, 0.15, 1.5), "ability", "sprint", peak=0.6)

    length = 0.55                                   # Charge: lower and rougher
    roar = lowpass(noise(length), 700) * env(length, 0.03, 0.2, 2)
    stomp = sweep(90, 50, 0.25) * env(0.25, 0.001, 0.05, 6)
    save_sound(mix(roar, stomp), "ability", "charge", peak=0.7)

    length = 0.4                                    # Blink: a zap that falls, and a sparkle
    zap = sweep(2400, 200, length, "square") * env(length, 0.002, 0.1, 4)
    zap = lowpass(zap, 5000)
    sparkle = highpass(noise(length), 5000) * env(length, 0.001, 0.1, 6)
    save_sound(zap * 0.4 + sparkle * 0.3, "ability", "blink", peak=0.6)

    length = 0.35                                   # Hook thrown: a whoosh with a rattling chain
    whoosh = bandpass(noise(length), 300, 2000) * env(length, 0.02, 0.1, 2)
    chain = np.zeros(int(length * RATE))
    for k in range(9):
        start = int(k * 0.035 * RATE)
        click = highpass(noise(0.012), 2500) * env(0.012, 0.0005, 0.004, 5)
        chain[start:start + len(click)] += click
    save_sound(whoosh * 0.6 + chain * 0.8, "ability", "hook_throw", peak=0.7)

    length = 0.5                                    # Hook lands: a metal clank
    clank = sum(tone(f, length) * env(length, 0.0005, 0.1, 6 + k) for k, f in enumerate((440, 1187, 2093, 3301)))
    hit = lowpass(noise(0.05), 2000) * env(0.05, 0.0005, 0.02, 5)
    save_sound(mix(clank * 0.3, hit * 0.6), "ability", "hook_hit", peak=0.7)

    length = 1.0                                    # Freeze: an icy shimmer and a crackle
    shimmer = sum(tone(f, length) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t_of(length) + k)) for k, f in enumerate((1568, 2093, 2637, 3136)))
    shimmer *= env(length, 0.01, 0.3, 3)
    crackle = highpass(noise(length) * (rng.random(int(length * RATE)) > 0.97), 3000) * env(length, 0.001, 0.3, 4)
    save_sound(shimmer * 0.2 + crackle * 0.8, "ability", "freeze", peak=0.6)

    length = 0.9                                    # Fade: ghostly, wavering tones
    t = t_of(length)
    ghost = sum(np.sin(2 * np.pi * (f * t + 3 * np.sin(2 * np.pi * 5 * t) / 5)) for f in (440, 443, 659))
    save_sound(lowpass(ghost, 2500) * env(length, 0.2, 0.4, 1), "ability", "fade", peak=0.5)


def ui_sounds():
    click = highpass(noise(0.015), 1500) * env(0.015, 0.0005, 0.005, 6)   # The order to walk somewhere
    save_sound(mix(click, tone(1800, 0.02) * env(0.02, 0.0005, 0.01, 8) * 0.3), "ui", "click", peak=0.35)

    out = np.zeros(int(0.3 * RATE))                 # Not ready: two low beeps
    for k in range(2):
        beep = lowpass(tone(220, 0.09, "square"), 1500) * env(0.09, 0.003, 0.02, 1)
        start = int(k * 0.13 * RATE)
        out[start:start + len(beep)] += beep
    save_sound(out, "ui", "not_ready", peak=0.4)


#
# Music, rendered as loops that start again without a seam: what rings past the end is added to the start
#

def save_music(left, right, name, loop_samples):
    for channel in (left, right):
        tail = channel[loop_samples:]
        channel[:len(tail)] += tail
    stereo = np.stack([left[:loop_samples], right[:loop_samples]], axis=1)
    stereo = stereo / (np.max(np.abs(stereo)) or 1) * 0.85
    path = os.path.join(DATA, "music", name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    soundfile.write(path, stereo.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
    print(os.path.relpath(path, DATA))


def note_freq(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    octave = int(name[-1])
    return 440.0 * 2 ** ((names[name[:-1]] + 12 * (octave - 4)) / 12)


def make_theme():
    """An upbeat, slightly heroic loop in A minor: drums, bass, chords and a lead. 16 bars at 104 BPM"""
    bpm = 104
    beat = 60 / bpm
    bars = 16
    loop = int(bars * 4 * beat * RATE)
    left = np.zeros(loop + 4 * RATE)
    right = np.zeros(loop + 4 * RATE)

    def place(sound, at, pan=0.0, gain=1.0):
        start = int(at * RATE)
        end = min(start + len(sound), len(left))
        left[start:end] += sound[:end - start] * gain * (1 - max(pan, 0))
        right[start:end] += sound[:end - start] * gain * (1 + min(pan, 0))

    kick = sweep(150, 45, 0.3) * env(0.3, 0.001, 0.05, 5)
    snare = mix(bandpass(noise(0.2), 1000, 6000) * env(0.2, 0.001, 0.05, 7), tone(190, 0.1) * env(0.1, 0.001, 0.02, 8) * 0.5)
    hat = highpass(noise(0.05), 7000) * env(0.05, 0.0005, 0.01, 8)
    taiko = lowpass(sweep(110, 60, 0.6) + noise(0.6) * 0.3, 400) * env(0.6, 0.002, 0.1, 4)

    chords = [("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("C3", ["G3", "C4", "E4"]), ("G2", ["G3", "B3", "D4"])]
    for bar in range(bars):
        t0 = bar * 4 * beat
        root, chord = chords[bar % 4]

        # Drums: a kick on 1 and 3, a snare on 2 and 4, hats on the 8ths, and a big drum at the start of every 4 bars
        for b in range(4):
            if b in (0, 2) or (b == 3 and bar % 2 == 1):
                place(kick, t0 + b * beat, gain=0.9)
            if b in (1, 3) and bar >= 2:
                place(snare, t0 + b * beat, gain=0.45)
        for e in range(8):
            if bar >= 1:
                place(hat, t0 + e * beat / 2, pan=0.3 if e % 2 else -0.3, gain=0.18 if e % 2 else 0.25)
        if bar % 4 == 0:
            place(taiko, t0, gain=0.8)

        # Bass: the root in 8ths, with a jump up an octave
        f = note_freq(root)
        for e in range(8):
            length = beat / 2
            n = lowpass(tone(f * (2 if e in (3, 7) else 1), length, "saw"), 600) * env(length, 0.005, 0.05, 2)
            place(n, t0 + e * length, gain=0.35)

        # Chords: soft detuned saws, wide
        length = 4 * beat
        for name in chord:
            fc = note_freq(name)
            pad_l = lowpass(tone(fc * 0.997, length, "saw"), 1400) * env(length, 0.3, 0.6, 0.5)
            pad_r = lowpass(tone(fc * 1.003, length, "saw"), 1400) * env(length, 0.3, 0.6, 0.5)
            place(pad_l, t0, pan=0.7, gain=0.07)
            place(pad_r, t0, pan=-0.7, gain=0.07)

    # The lead: a melody over bars 5-8 and 13-16, the second time an octave up
    melody = [("E5", 1), ("A5", 1), ("G5", 0.5), ("E5", 0.5), ("D5", 1),
              ("C5", 1), ("D5", 0.5), ("E5", 0.5), ("G5", 2),
              ("E5", 1), ("C5", 1), ("D5", 0.5), ("C5", 0.5), ("A4", 1),
              ("G4", 1), ("A4", 1), ("C5", 1), ("A4", 1)]
    for start_bar, octave in ((4, 1), (12, 2)):
        t = start_bar * 4 * beat
        for name, beats in melody:
            length = beats * beat
            f = note_freq(name) * octave
            n = (tone(f, length, "square") * 0.5 + tone(f * 1.005, length, "saw") * 0.5)
            n = lowpass(n, 3500) * env(length, 0.01, 0.08, 1.5)
            place(n, t, pan=0.15, gain=0.16)
            t += length

    save_music(left, right, "theme", loop)


def make_traffic():
    """The hum of the motorway: low rumble, tyres and engines passing, as a loop of 12 seconds"""
    length = 12
    loop = length * RATE
    t = t_of(length + 2)
    rumble = lowpass(np.cumsum(noise(length + 2)) * 0.02, 200)               # Brown noise
    tyres = bandpass(noise(length + 2), 300, 1500) * 0.25
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
    hero_sounds()
    car_sounds()
    ability_sounds()
    ui_sounds()
    make_theme()
    make_traffic()
