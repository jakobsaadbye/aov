#!/usr/bin/env python3
"""
Makes the sounds of the spells, the items and the heroes, and the voices of the heroes, with ElevenLabs: the sound
effects API for the sounds, text to speech for the voices. Each is written as an .ogg to data/sounds/, where the game
plays it by its name (core/sound.sd), and the .wav of make_sounds.py that it replaces is removed.

    python3 tools/make_audio.py                      what isn't there yet
    python3 tools/make_audio.py --force              all of it again
    python3 tools/make_audio.py sfx                  only the sounds (or: voices)
    python3 tools/make_audio.py ability.hex voice.hugo_cast_1     only these
    python3 tools/make_audio.py --list               what it would make, with the prompts

It needs an ElevenLabs API key in ELEVENLABS_API_KEY (or a network proxy that adds it, as in a Claude Code cloud
session), and ffmpeg.

How it sounds is all in this file: every spell belongs to a FAMILY, whose words come into each of its prompts, so that
spells of a kind sound like each other (smoke and shadows hiss and breathe, ice crackles, time ticks and runs
backwards), and every hero has a VOICE, with its lines for when it comes onto the field, casts, gets across, is run
over and gets an enemy run over. The sounds are trimmed, made as loud as each other, and the voices are pitched and put
in a room for their hero, e.g a deeper ogre or a ghost in an echo.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
SOUNDS = os.path.join(DATA, "sounds")
API = "https://api.elevenlabs.io/v1"
CACHE = os.path.join(SOUNDS, ".elevenlabs.json")     # What each file was made from, so a changed prompt is made again

#
# Sound effects
#

# The feel of each kind of spell, which comes into every prompt of the kind
FAMILY = {
    "stealth": "soft breathy whoosh of dark smoke and shadow, hissing vapor, muffled and mysterious",
    "arcane":  "witchy magic, sparkling arcane shimmer, fairy-tale fantasy",
    "mind":    "dreamy hypnotic shimmer, warbling chimes, slow and eerie",
    "time":    "clockwork ticking and a reversed swoosh, time bending, magical",
    "ice":     "crisp crackling ice and frost, glassy crystal tinkles, cold wind",
    "storm":   "electric crackle and rumbling thunder, wind",
    "traffic": "street sounds, car horns, tyres and brakes",
    "motion":  "fast athletic movement, whoosh of air",
    "force":   "heavy physical impact, punchy and weighty",
    "magnet":  "deep magnetic hum and metallic resonance",
    "craft":   "workshop and tools, wood and metal",
    "care":    "gentle and soothing",
    "tourist": "a cheerful tourist with a camera and a phone",
    "item":    "a cartoony game item, short and clear",
    "game":    "a fantasy game interface sound, short and polished",
}

# name: (family, what it is, seconds)
SFX = {
    # Allan
    "ability.sprint":         ("motion", "quick burst of running footsteps on asphalt speeding up with a rushing whoosh", 1.0),
    # Bent
    "ability.hop_on":         ("motion", "a man jumps onto the metal roof of a moving car, a thud on sheet metal and wind rushing past", 1.2),
    "ability.night_bus":      ("traffic", "a big old city bus honks a deep two-tone horn and its diesel engine roars away", 2.0),
    # Birgit
    "ability.footbridge":     ("craft", "quick hammering, wooden planks slapping into place and a creaking bridge going up", 1.6),
    "ability.trampoline":     ("craft", "metal springs stretching and a bouncy trampoline boing", 1.0),
    # Bjorn
    "ability.leap":           ("motion", "a heavy warrior launches into a mighty leap, armor rattling, big whoosh upwards", 1.0),
    "ability.land":           ("force", "a heavy armored warrior lands hard on the ground, deep thud and rattle", 0.8),
    "ability.shield_bash":    ("force", "a big wooden round shield slams into someone, deep thump with metal rim clang", 0.8),
    # Butcher
    "ability.hook":           ("force", "a heavy iron meat hook flung on a rattling chain, whirring through the air", 1.2),
    "ability.hook_hit":       ("force", "a heavy iron hook bites into a car door, metal clank and crunch, chain snapping taut", 0.8),
    "ability.heave":          ("force", "a huge brute grunts and heaves a car, metal groaning, then it crashes down", 1.5),
    # Ditte
    "ability.call_ambulance": ("traffic", "a crackling radio call and an ambulance siren starting up in the distance", 2.0),
    "ability.bandage":        ("care", "a bandage unrolling and wrapping with soft fabric rustle, and a warm healing chime", 1.4),
    # Frosty
    "ability.freeze":         ("ice", "a sudden snap of freezing, ice spreading fast over metal with a crackle", 1.4),
    "ability.igloo":          ("ice", "snow blocks packed and stacked quickly, crunching snow, a dome closing", 1.5),
    # Ghosty
    "ability.possess":        ("stealth", "a ghostly wail sweeping into a car, eerie spectral whoosh with a metallic shudder", 1.5),
    # Gudrun
    "ability.grannys_crossing": ("traffic", "a pedestrian crossing signal beeping and cars braking to a polite stop", 1.6),
    "ability.yarn_leash":     ("craft", "knitting needles clicking and a ball of yarn whipping through the air", 1.2),
    "ability.cane":           ("force", "a wooden walking cane hooks someone's ankle with a crack, and a body falls over", 0.9),
    # Hilda
    "ability.stop_sign":      ("traffic", "a sharp crossing guard whistle and cars screeching to a stop", 1.4),
    "ability.wave_through":   ("traffic", "a short whistle and cars accelerating hard away with revving engines", 1.6),
    # Hugo
    "ability.trance_walk":    ("mind", "a hypnotic drone swelling into a smoky dreamlike haze", 1.8),
    "ability.sleep":          ("mind", "a drowsy lullaby chime and a long sleepy sigh", 1.5),
    # Ivar
    "ability.berserk":        ("force", "a furious berserker battle roar with a pounding heartbeat", 1.6),
    "ability.axe_throw":      ("force", "a heavy throwing axe spinning through the air, whum whum whum", 1.0),
    "ability.axe_hit":        ("force", "an axe striking and knocking someone, a dull thunk", 0.6),
    # Karl
    "ability.jack":           ("craft", "a car jack ratcheting quickly, click click click, and a car being lifted with a metal groan", 1.4),
    "ability.oil_change":     ("craft", "thick motor oil glugging out of a can and splashing on asphalt", 1.2),
    # Kenji
    "ability.substitution":   ("stealth", "a puff of smoke bursting, and a wooden log thudding where a ninja stood", 1.0),
    "ability.shadow_step":    ("stealth", "a ninja vanishes into a shadow with a swift dark swish", 0.8),
    # Mads
    "ability.ollie":          ("motion", "a skateboard ollie: tail pop, wheels in the air, and landing on the board", 1.0),
    "ability.grind":          ("motion", "a skateboard grinding along a metal rail at speed, scraping", 1.2),
    # Magnus
    "ability.repel":          ("magnet", "a powerful magnetic pulse pushing outwards, a deep whoom and metal rattling away", 1.4),
    "ability.attract":        ("magnet", "a rising magnetic hum pulling something in fast, ending in a metal clank", 1.2),
    # Mira
    "ability.reverse":        ("time", "cars rewinding backwards, a tape rewinding whoosh and engines running in reverse", 1.6),
    "ability.rewind":         ("time", "a reversed whoosh sucking backwards and a clock ticking back", 1.2),
    "ability.time_lock":      ("time", "a clock freezing with a deep clang and the ticking stopping", 1.2),
    # Sigrid
    "ability.broom":          ("arcane", "a witch takes off on a broomstick, whooshing flight with a cackle", 1.4),
    "ability.hex":            ("arcane", "a magical hex, a puff of green magic and a frog croaking", 1.2),
    # Stormy
    "ability.lightning_rod":  ("storm", "a metal rod hammered into the ground and starting to hum with electricity", 1.4),
    "ability.lightning":      ("storm", "a lightning bolt striking down with a sharp crack and a thunder rumble", 1.2),
    "ability.gust":           ("storm", "a powerful gust of wind blasting past", 1.2),
    # Tobias
    "ability.flash_photo":    ("tourist", "a big camera flash charging up with a whine and popping bright, shutter click", 1.0),
    "ability.selfie":         ("tourist", "a phone camera shutter click and a quick magical swap whoosh", 1.0),
    # Tim & Tom
    "ability.split":          ("motion", "two pairs of small feet running apart, a playful whoosh", 1.0),
    "ability.swap":           ("arcane", "a quick sparkly zip of two people swapping places", 0.7),
    # Others the world plays
    "ability.blink":          ("arcane", "a quick bright teleport zap", 0.6),
    "ability.fade":           ("stealth", "a ghostly fade away, airy whisper and shimmer", 1.0),

    # Items
    "item.banana_peel":       ("item", "a banana peel dropped with a squish", 0.6),
    "item.banana":            ("item", "someone slipping on a banana peel, squeak and a tumble", 0.9),
    "item.energy_drink":      ("item", "a soda can cracked open with a fizz and gulped down", 1.2),
    "item.traffic_cone":      ("item", "a plastic traffic cone plonked down on asphalt", 0.6),
    "item.megaphone":         ("item", "a megaphone squealing with feedback and a loud blast", 1.0),
    "item.rubber_chicken":    ("item", "a rubber chicken squeaking loudly", 0.8),
    "item.balloon":           ("item", "a balloon inflated quickly with a squeaky rubber stretch", 1.0),
    "item.lucky_dice":        ("item", "dice rattling in a hand and rolling across a table", 1.0),
    "item.remote_control":    ("item", "a car key remote beeping twice and a car horn answering", 1.0),
    "item.stopwatch":         ("time", "a stopwatch clicked and ticking fast", 1.0),
    "item.snow_globe":        ("ice", "a glass snow globe shaken with a sparkling jingle, and freezing", 1.2),
    "item.portal_gun":        ("arcane", "a sci-fi portal gun firing and a swirling portal opening", 1.0),
    "item.pickup":            ("item", "a sparkly magical pickup chime", 0.6),
    "item.mirror":            ("item", "a shimmering glassy mirror ring", 0.8),

    # The heroes and the game
    "hero.spawn":             ("game", "a magical appearance, a bright chime and a soft whoosh", 0.9),
    "hero.crossed":           ("game", "a short triumphant fanfare for reaching the goal", 1.6),
    "hero.death":             ("game", "a cartoonish car crash: a thump, a crunch and glass tinkling", 1.2),
    "hero.hurt_1":            ("force", "a car bumper knocking into someone, a thump", 0.5),
    "hero.hurt_2":            ("force", "a body bumped by a car, a dull smack", 0.5),
    "ui.not_ready":           ("game", "a soft low error blip", 0.5),
}

#
# Voices
#

# The events a hero says something at, and how many lines each has
EVENTS = ("spawn", "cast", "crossed", "death", "kill")

# hero: the ElevenLabs voice, how much higher or lower it is made (semitones), its speed, a room (none, echo, cave),
# how steady it is (low is more expressive), and its lines for each event
VOICES = {
    "allan": dict(voice="TX3LPaxmHKxFdv7VOQHJ", pitch=0, stability=0.35, lines={
        "spawn": ["Let's go, let's go!", "On your marks!"],
        "cast": ["Catch me if you can!", "Full speed!", "Too slow!"],
        "crossed": ["Personal best!", "Easy!"],
        "death": ["Not fast enough!", "Oof!"],
        "kill": ["Should have run!", "Lapped you!"]}),
    "bent": dict(voice="iP95p4xoKVk53GoZ742B", pitch=-1, stability=0.45, lines={
        "spawn": ["Next stop: the other side.", "All aboard."],
        "cast": ["Mind the gap!", "Hold on to something.", "Right on schedule."],
        "crossed": ["End of the line.", "On time, as always."],
        "death": ["Missed my stop!", "That's not on the timetable!"],
        "kill": ["Tickets, please.", "Should've waited for the next one."]}),
    "birgit": dict(voice="XrExE9yKIg1WjnnlVkGX", pitch=0, stability=0.4, lines={
        "spawn": ["Hard hats on!", "Let's build something."],
        "cast": ["Up she goes!", "Built to last!", "Watch your step!"],
        "crossed": ["Job done.", "On budget and on time!"],
        "death": ["That wasn't up to code!", "My back!"],
        "kill": ["Should've used the bridge.", "Demolished!"]}),
    "bjorn": dict(voice="pNInz6obpgDQGcFmaJgB", pitch=-2, stability=0.45, room="echo", lines={
        "spawn": ["Shields up!", "For the clan!"],
        "cast": ["Stand aside!", "Hah!", "Feel the shield!"],
        "crossed": ["Victory!", "The road is conquered!"],
        "death": ["Not like this!", "Valhalla awaits!"],
        "kill": ["Another one falls!", "Too weak!"]}),
    "butcher": dict(voice="SOYHLrjzK2X1ezoPC6cr", pitch=-6, speed=0.92, stability=0.35, lines={
        "spawn": ["Fresh meat!", "Butcher's open!"],
        "cast": ["Come here!", "Get over here!", "Hungry!"],
        "crossed": ["Hah! Butcher wins!", "More meat over here!"],
        "death": ["Butcher... falls...", "Ugh, tough meat!"],
        "kill": ["Tenderized!", "Ha ha! Mince!"]}),
    "ditte": dict(voice="hpp4J3VqNfWAUOO0d1Us", pitch=0, stability=0.45, lines={
        "spawn": ["Paramedic on scene.", "Stay calm, everyone."],
        "cast": ["I'm calling it in!", "Hold still!", "Clear!"],
        "crossed": ["Patient stable.", "Made it, safe and sound."],
        "death": ["Somebody call... me!", "Medic!"],
        "kill": ["I'll call you a ride.", "That'll need stitches."]}),
    "frosty": dict(voice="N2lVS1w4EtoT3dr4eOWO", pitch=1, stability=0.35, lines={
        "spawn": ["Chill out, I'm here.", "Brr, let's go."],
        "cast": ["Freeze!", "Cool it!", "Snow way!"],
        "crossed": ["Ice and easy.", "Still frosty!"],
        "death": ["I'm melting!", "Slush!"],
        "kill": ["Put on ice!", "Cold as ice."]}),
    "ghosty": dict(voice="SAz9YHcvj6GT2YYXdXww", pitch=-1, speed=0.9, stability=0.3, room="cave", lines={
        "spawn": ["I have returned...", "Boo."],
        "cast": ["Through the walls...", "Mine now...", "Whooo..."],
        "crossed": ["Rest at last...", "Haunting the other side..."],
        "death": ["Again?", "I was already dead..."],
        "kill": ["Join me...", "Welcome to the other side..."]}),
    "gudrun": dict(voice="pFZP5JQG7iQjIQuC4Bku", pitch=1, speed=0.88, stability=0.4, lines={
        "spawn": ["Now where are my glasses?", "In my day, roads were smaller."],
        "cast": ["Let granny through, dear.", "Mind your manners!", "Wait your turn!"],
        "crossed": ["There, that wasn't so hard.", "I'll have a cup of tea now."],
        "death": ["Oh, my hip!", "Young drivers these days!"],
        "kill": ["Serves you right, dear.", "Should have helped granny across."]}),
    "hilda": dict(voice="Xb7hH8MSUJpSbSDYk0k2", pitch=0, stability=0.4, lines={
        "spawn": ["Everybody, single file!", "Look both ways!"],
        "cast": ["Stop!", "Go, go, go!", "Hold it right there!"],
        "crossed": ["Safely across.", "That's how it's done."],
        "death": ["I had the right of way!", "Didn't you see the sign?"],
        "kill": ["You should have waited.", "Ticket!"]}),
    "hugo": dict(voice="nPczCjzI2devNBz1zQrb", pitch=-1, speed=0.9, stability=0.35, room="echo", lines={
        "spawn": ["Look into my eyes...", "You are getting sleepy..."],
        "cast": ["The cars are not real...", "Sleep now...", "Relax..."],
        "crossed": ["Just as I foresaw.", "And... awake."],
        "death": ["That was... real?", "I didn't see that coming..."],
        "kill": ["Sweet dreams.", "You will remember nothing."]}),
    "ivar": dict(voice="SOYHLrjzK2X1ezoPC6cr", pitch=-2, stability=0.3, lines={
        "spawn": ["Blood and glory!", "Who wants to fight?"],
        "cast": ["Raaagh!", "Out of my way!", "Catch this!"],
        "crossed": ["Another road conquered!", "Ha! Next!"],
        "death": ["A worthy... car...", "I'll be back!"],
        "kill": ["Who's next?", "Ha! Too easy!"]}),
    "karl": dict(voice="pqHfZKP75CvOlQylNhV4", pitch=0, stability=0.45, lines={
        "spawn": ["Right, let's have a look.", "Tools ready."],
        "cast": ["Up she goes.", "Needs an oil change.", "There's your problem."],
        "crossed": ["All fixed up.", "Running smooth."],
        "death": ["That'll cost extra!", "My wrench!"],
        "kill": ["You've sprung a leak.", "Total write-off."]}),
    "kenji": dict(voice="onwK4e9ZLuTAKqWW03F9", pitch=0, speed=0.95, stability=0.5, lines={
        "spawn": ["I am the shadow.", "Silent. Swift."],
        "cast": ["Now you see me...", "Too slow.", "Hm."],
        "crossed": ["The path is clear.", "Unseen, as always."],
        "death": ["A log... I needed a log...", "Dishonor..."],
        "kill": ["You never saw me.", "Strike from the shadows."]}),
    "mads": dict(voice="bIHbv24MWmeRgasZH58o", pitch=1, stability=0.35, lines={
        "spawn": ["Let's shred!", "Sick road, dude."],
        "cast": ["Kickflip!", "Grinding!", "Woo!"],
        "crossed": ["Nailed it!", "Gnarly!"],
        "death": ["Bail!", "Not the board!"],
        "kill": ["Get wrecked!", "Totally bodied."]}),
    "magnus": dict(voice="nPczCjzI2devNBz1zQrb", pitch=-3, stability=0.45, room="echo", lines={
        "spawn": ["Magnus is here.", "Nothing moves me."],
        "cast": ["Get back!", "Come to me!", "Opposites attract."],
        "crossed": ["Unstoppable.", "Steel wins."],
        "death": ["Demagnetized...", "Not... possible..."],
        "kill": ["Pulled you in.", "Drawn to your doom."]}),
    "mira": dict(voice="EXAVITQu4vr4xnSDxMaL", pitch=0, stability=0.45, room="echo", lines={
        "spawn": ["Right on time.", "Time is on my side."],
        "cast": ["Back we go.", "Stop!", "Let's try that again."],
        "crossed": ["Perfectly timed.", "Exactly as planned."],
        "death": ["Out of time!", "I'll rewind that."],
        "kill": ["Your time is up.", "Late again."]}),
    "sigrid": dict(voice="FGY2WhTYpPnrIDTdsKH5", pitch=-1, stability=0.3, lines={
        "spawn": ["Double, double, toil and traffic!", "Hee hee hee!"],
        "cast": ["Ribbit!", "Up, up and away!", "A little hex!"],
        "crossed": ["Hee hee! Made it!", "Magic always wins."],
        "death": ["My broom!", "There goes a life..."],
        "kill": ["Enjoy being a toad!", "Hexed and wrecked!"]}),
    "stormy": dict(voice="cgSgspJ2msm6clMCkdW9", pitch=0, stability=0.35, lines={
        "spawn": ["Today's forecast: chaos!", "Storm's coming!"],
        "cast": ["Lightning!", "Gusts up to a hundred!", "Brace yourself!"],
        "crossed": ["Clear skies ahead!", "Sunny on this side!"],
        "death": ["Didn't see that in the forecast!", "Cloudy..."],
        "kill": ["Blown away!", "Struck down!"]}),
    "tobias": dict(voice="IKne3meq5aSn9XLyUdCD", pitch=0, stability=0.35, lines={
        "spawn": ["Ooh, what a view!", "Is this the way to the beach?"],
        "cast": ["Say cheese!", "Selfie time!", "Smile!"],
        "crossed": ["Gotta post this!", "What a trip!"],
        "death": ["My camera!", "Not in the brochure!"],
        "kill": ["That's going in the album.", "Great shot!"]}),
    "twins": dict(voice="TX3LPaxmHKxFdv7VOQHJ", pitch=5, stability=0.3, lines={
        "spawn": ["We're here!", "Two of us!"],
        "cast": ["Over here!", "Switch!", "Bet you can't tell!"],
        "crossed": ["We made it!", "Twin power!"],
        "death": ["Tom!", "Tim!"],
        "kill": ["Double trouble!", "Ha! Fooled you!"]}),
}

MODEL = "eleven_multilingual_v2"

#
# Making them
#


def key():
    return os.environ.get("ELEVENLABS_API_KEY", "proxy-injected")


def post(path, body, tries=4):
    for attempt in range(tries):
        request = urllib.request.Request(API + path, data=json.dumps(body).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "xi-api-key": key()})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and attempt + 1 < tries:
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f"{path}: HTTP {e.code}: {text}")
    raise RuntimeError(f"{path}: gave up")


def sfx_prompt(name):
    family, what, seconds = SFX[name]
    return f"{what}. {FAMILY[family]}. Clean game sound effect, no music, no voices", seconds


def make_sfx(name):
    prompt, seconds = sfx_prompt(name)
    audio = post("/sound-generation?output_format=mp3_44100_128",
                 {"text": prompt, "duration_seconds": seconds, "prompt_influence": 0.6})
    return audio, {"prompt": prompt, "seconds": seconds}


def voice_files():
    """Every line of every hero: (name, hero, event, text), e.g ("voice.hugo_cast_1", "hugo", "cast", "Sleep now...")"""
    out = []
    for hero, v in VOICES.items():
        for event in EVENTS:
            for i, text in enumerate(v["lines"][event]):
                out.append((f"voice.{hero}_{event}_{i + 1}", hero, event, text))
    return out


def make_voice(hero, text):
    v = VOICES[hero]
    settings = {"stability": v.get("stability", 0.4), "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True}
    audio = post(f"/text-to-speech/{v['voice']}?output_format=mp3_44100_128",
                 {"text": text, "model_id": MODEL, "voice_settings": settings})
    return audio, {"text": text, "voice": v["voice"], "settings": settings}


def finish(audio, name, is_voice, hero=None):
    """The mp3 from ElevenLabs as the .ogg of the game: trimmed, as loud as the others, and pitched and put in a room
    for the voice of its hero. The .wav of make_sounds.py by the same name goes"""
    group, base = name.split(".", 1)
    folder = os.path.join(SOUNDS, group)
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, base + ".ogg")
    filters = ["silenceremove=start_periods=1:start_threshold=-45dB",
               "areverse", "silenceremove=start_periods=1:start_threshold=-45dB", "areverse"]
    if is_voice:
        v = VOICES[hero]
        rate = 2 ** (v.get("pitch", 0) / 12)
        tempo = v.get("speed", 1.0) / rate
        if rate != 1 or tempo != 1:
            filters += [f"asetrate={int(44100 * rate)}", "aresample=44100", f"atempo={tempo:.4f}"]
        room = v.get("room")
        if room == "echo":
            filters.append("aecho=0.8:0.6:60|120:0.25|0.15")
        elif room == "cave":
            filters.append("aecho=0.8:0.7:180|400|700:0.35|0.25|0.15")
    filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    channels = "1" if is_voice else "2"
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio)
        source = f.name
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", source, "-af", ",".join(filters), "-ar", "44100",
                        "-ac", channels, "-c:a", "libvorbis", "-q:a", "5", out], check=True)
    finally:
        os.remove(source)
    old = os.path.join(folder, base + ".wav")
    if os.path.exists(old):
        os.remove(old)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    jobs = []
    if not args or "sfx" in args or any(a in SFX for a in args):
        for name in SFX:
            if args and "sfx" not in args and name not in args:
                continue
            jobs.append((name, False, None, None))
    if not args or "voices" in args or any(a.startswith("voice.") for a in args):
        for name, hero, event, text in voice_files():
            if args and "voices" not in args and name not in args:
                continue
            jobs.append((name, True, hero, text))

    if "--list" in sys.argv:
        for name, is_voice, hero, text in jobs:
            print(name, "|", text if is_voice else sfx_prompt(name)[0])
        print(len(jobs), "files")
        return

    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))
    made = 0
    for name, is_voice, hero, text in jobs:
        group, base = name.split(".", 1)
        out = os.path.join(SOUNDS, group, base + ".ogg")
        if is_voice:
            what = json.dumps({k: v for k, v in VOICES[hero].items() if k != "lines"}, sort_keys=True) + "|" + text
        else:
            what = json.dumps(SFX[name])
        digest = hashlib.sha1((what + "|" + json.dumps(FAMILY, sort_keys=True) * (not is_voice)).encode()).hexdigest()
        if not force and os.path.exists(out) and cache.get(name) == digest:
            continue
        try:
            audio, info = make_voice(hero, text) if is_voice else make_sfx(name)
        except RuntimeError as e:
            print("FAILED", name, e)
            if "quota" in str(e).lower() or "401" in str(e):
                break
            continue
        finish(audio, name, is_voice, hero)
        cache[name] = digest
        json.dump(cache, open(CACHE, "w"), indent=1, sort_keys=True)
        made += 1
        print(name, "|", info.get("text") or info.get("prompt"))
    print(f"Made {made} of {len(jobs)}")


if __name__ == "__main__":
    main()
