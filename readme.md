# Allan over vejen

Allan og hans venner har lavet en leg på motorvejen.

![Allan over vejen](./data/images/aov_map_w3.jpg)

A remake of the Warcraft 3 map *Allan over vejen*, written in [Saad](https://github.com/jakobsaadbye/Saad) with raylib.
Get your hero across a busy motorway without being run over. Every time a car gets you, you go on with a new hero at
random. Every crossing makes the traffic faster, and the next hero starts on the side you got to, and crosses back.

The traffic all drives one way, from the top of the screen to the bottom. Every car has a speed of its own and drives
straight through slower cars in its lane, and the cars are nearly as wide as their lanes, so there is nowhere to hide
between them.

## Running it

With `saad` on the PATH (see the readme of Saad):

```
cd src
saad run main.sd
```

It can be started from any folder: it finds `data/` next to `src/` from where the program is (`src/build/out.exe`).

## The data folder

| | |
| --- | --- |
| `data/textures/` | The pavement (`pavement/pavement.png`), the road (`road/asphalt.png`), the particles and the frames of the UI, the Warcraft cursor |
| `data/models/` | The vehicles (car, van, truck, bus), the heroes, the city and a segment of the wall, as OBJ, each with its hand-painted texture (`car.png` for `car.obj`) |
| `data/icons/` | A 128x128 icon for each ability, item, perk and status, by the name in the code |
| `data/sounds/` | The sound effects, by group: `hero/`, `car/`, `ability/`, `ui/` |
| `data/music/` | The soundtracks, a folder each (`band/`, `quiet/`, `board/`, `toybox/`), whose pieces the game shuffles together anew every game and plays one at a time (the `soundtrack` command of the console picks one alone), and the hum of the traffic (`traffic.ogg`), looped |
| `data/fonts/` | Cinzel (titles) and Fira Sans (text), both under the SIL Open Font License |
| `data/shaders/` | `lighting.vs` and `lighting.fs`: the warm sun, cool light from the sky and warm light from the ground, a rim light and the haze in the distance |
| `data/window_icon.png` | |

The models are made by `tools/make_heroes.py` (the heroes) and `tools/make_models.py` (the vehicles, the wall, the city
and what is on the grass), with `tools/sculpt.py`; the pavement, the asphalt, the particles and the frames of the UI by
`tools/make_textures.py`; the icons by `tools/make_textures.py` and `tools/make_icons.py`, painted by `tools/iconkit.py`;
and the sounds and the music by `tools/make_sounds.py` and `tools/make_hero_sounds.py`. Run them with python3 to write
the files again, e.g `python3 tools/make_heroes.py frosty`. They are plain files that can just as well be edited in
Blender or painted over. `Grass_02.png` and `Ground_03.png` aren't used any more.

**Sculpt** (`tools/sculpt.py`) makes a model out of smooth surfaces: ellipsoids, rounded boxes, lathes (a profile turned
round), tubes (a circle swept along a curve), extrusions and planes. Each is a function from (u, v) to a point, so the
same function gives the mesh and, sampled once for each texel, the texture: a painter colors every texel from where it
is on the model (its position, its normal and its place on the surface). So cloth folds, stripes, faces, bricks, rust and
blood run on across the parts without seams, and the light, the dark creases and the darker feet of a hand-painted
texture are worked out from the shape. `python3 tools/sculpt.py preview data/models/car.obj` draws a model in software,
from the front and from three quarters. Each hero is a `Build` of proportions (a brute with huge
shoulders and hands and a small head pushed forward, a stout one, a slim one, an old one bent over, a kid), with a
cranium, jaw and brow ridge for a face that has a serious look of its own, and is fitted to the height of its hero:
the Butcher, Ivar and Bjørn tower over Gudrun and the twins. Where parts are close to each other, under a brim or
where an arm meets the body, the texture is darker (ambient occlusion, worked out from points all over the model).

**Rig** (`tools/rig.py`) gives a model bones: a skeleton, its parts bound to bones (smoothly between two where a limb
bends), poses and keyframed clips, and writes it as `models/<name>.glb` with its texture, skin and clips.
`tools/anatomy.py` has the bodies the heroes are built from, from where their joints are: a brute's, and a person's
(`human_body`: chunky, big gloved hands and heavy boots), with the rig that fits them and the clips they play: idle,
walk, and one for each ability, named by its icon. The game plays a hero's
GLB when it has one (`core/hero_animation.sd`): the clip of an ability right after it is cast (the Butcher swings his
hook arm when he throws the hook, and heaves with both arms), the walk while it walks, timed by how far it went, and
else idle. The Butcher, Birgit, Frosty, Mira and Magnus have one so far; the others are still OBJ.

The Butcher's face has bones of its own: a jaw, two brows and two eyelids, over sculpted eyeballs, lips, teeth and
tusks. Each clip of the body has a layer for the face (`rig.layered`): he blinks, chews and sneers while he stands,
scowls as he winds up a throw and roars as the hook flies, grimaces under a car and bellows as he heaves it. The
portrait of the HUD looks at his head bone, close up, and plays the face of the clip he is in (`<clip>_face`, the
same face on a body that stands still, so his arm never swings in front of it). His hook is a part of its own in the
GLB (`part="hook"`), which the game leaves out while the hook is thrown. The thrown hook and the links of its chain
are models of their own (`models/meat_hook.obj` and `models/chain_link.obj`, the same hook as on his arm), and the chain
comes from his hand bone: the throw clip starts wound up, so the arm is flung forward the moment the hook leaves. `tools/make_butcher_concepts.py` draws the
directions he was picked from, as sketch sheets.

Birgit is a person on the same skeleton, with a face of the same bones (`human_face`: big eyes under lids that blink,
brows, a chin that drops open, freckles) under a big hard hat, and two more bones for her braid, which swings a moment
after she moves. She carries a framing hammer in her right fist: she stands and now and then tips it up to look at it,
swings it up over her head and slams it into the road to raise her footbridge (the bridge comes up out of the road as the hammer lands), and
tosses her trampoline out underarm, which flies from her hand, tumbling, and pops open where it lands; it bounces no
one until it is down. Her builds are models of their own: a span of the footbridge for each lane and a ramp at each end
with the scaffold under it, so nothing stands where the cars drive (`models/footbridge_span.obj`,
`models/footbridge_ramp.obj`), and the trampoline with its mat apart (`models/trampoline.obj`,
`models/trampoline_mat.obj`), which dips when it bounces someone.

Frosty is a little snow golem on the same skeleton, made round: a big belly of packed snow on stubby snowball feet, a
big head with shiny coal eyes (snow lids blink over them), twig brows, rosy cheeks, a short carrot nose and a smile of
coal pebbles over a chin of snow that drops open, green mittens, shards of blue ice out of his back, and a bobble hat
and a scarf whose pompom and tail are on bones of their own, so they bounce and swing after him. He sways on the spot,
waddles, claps his mittens over his head and flings them out for his cold snap, blowing, and crouches and hugs himself
as his igloo goes up round him. The igloo is a model too (`models/igloo.obj`): rows of snow blocks, a tunnel to a dark
door on the side he is going, icicles. It grows up out of the snow round him, crouching in it, and slumps as it melts.

Magnus is a circus strongman on the brute's body: a striped singlet with straps, black tights, laced boots, iron bracers,
a belt with a gold buckle, slicked hair, a handlebar moustache and a cleft chin, and a giant red horseshoe magnet in his
right fist. He stands with his chest out and now and then flexes his free arm, holds the magnet up over his head and
turns it round to repel the cars, and thrusts it at an enemy and heaves back to pull it in. While he pulls, blue lines
of his field ripple from the magnet in his hand to the enemy (`drawMagnetPull`).

Mira is a tall, slender person on the same skeleton, in a long robe of deep violet scattered with gold stars: its skirt
is bound to her hips and legs, so it follows her steps and swings out when she turns. She has wide bell sleeves, long
silver hair on two bones of its own, and a tall pointed hat with a gold crescent whose tip is on a bone too, so both
swing after her. There is a clock brooch at her collar and a pocket watch on a chain at her sash. In her right hand is a
staff with an hourglass on top, its sand seen through the glass, and her left hand is open (`anatomy.open_hand`), for
casting. She stands and now and then glances up at the hourglass, walks with long unhurried steps, sweeps her left hand
in a circle backwards and pushes it out for Reverse, twirls once as she comes back from a Rewind, and swings the staff
back over her shoulder and thrusts the hourglass at her enemy for Time lock. She turns to what she casts at. The clock
over a hero she locks in time is a model (`models/time_lock_clock.obj`, and its hands `models/clock_hand.obj`): it pops
up over the hero's head, turned and tilted to the camera, its hands running backwards, and shrinks away when the lock
is over.

**Iconkit** (`tools/iconkit.py`) takes the drawings of the icons, which are flat shapes drawn with PIL, keeps each shape
as a layer, and paints them like raised objects: a bevel lit from the top left, lighter at the top, a shine, a little
brush texture and a soft shadow under each, with light behind the symbol and darker corners.

The game expects a model to look towards +z and stand on y = 0, in the units of the game, and puts `<name>.png` on every
material of `<name>.obj`. The body of a vehicle, the part that gets the color of the car, is the material that is pure
white (`Kd 1 1 1`, a part made with `tint=True`), painted light grey so the color shows; the sizes of the vehicles are
those of `config.sd` (`CarWidth`, `CarLength`, ...).

## Sounds

The game plays its sounds through a `SoundPlayer` (`src/core/sound.sd`), which the `Game` owns:
`game.sounds.play("hero.crossed")`, or `game.sounds.playAt("ability.blink", position)` for one that is quieter the further
it is from the camera. The name is the folder and the file in `data/sounds`: `hero.crossed` is
`data/sounds/hero/crossed.wav`. Files that end in a number are variants that are picked at random, e.g `hero/hurt_1.wav`
and `hurt_2.wav` are both `hero.hurt`. So a new sound is a file dropped into a folder there (`.wav`, `.ogg` or `.mp3`), and
a line that plays it. An ability plays the sound in its `sound` in `heroes.sd`.

While the game is paused, the sounds that are playing stop, the hum of the traffic stops with the cars, and the music
fades down to a murmur. M turns the music off and on.

| Sound | When |
| --- | --- |
| `hero.hurt`, `hero.death` | A car on the hero, and run over |
| `hero.spawn`, `hero.crossed` | A new hero, and across the road |
| `ability.<icon>` | Each spell has a sound of its own, named by its icon, e.g `ability.trance_walk` |
| `item.<icon>` | Each item that is used, e.g `item.rubber_chicken` |
| `voice.<hero>_<event>` | What the heroes say (`core/voices.sd`) |
| `ui.not_ready` | An ability that is cooling down |

### Made with ElevenLabs

The sounds of the spells, the items and the heroes, the voices and the music are made with
[ElevenLabs](https://elevenlabs.io) by `tools/make_audio.sd`, a tool in Saad (with `net.http`, `json` and `crypto` of its
standard library, and ffmpeg): the sound effects API for the sounds, text to speech for the voices, and the music API for
the soundtrack. All of it is written in that file:

* **Families.** Each spell belongs to a family (stealth, arcane, mind, time, ice, storm, traffic, motion, force, magnet,
  craft, care, tourist), whose words come into each of its prompts, so spells of a kind sound like each other: smoke and
  shadows hiss and breathe (Kenji's substitution, Ghosty's possession), ice crackles, time ticks and runs backwards.
* **Voices.** Each hero has an ElevenLabs voice, made higher or lower, slower, or put in an echo for its hero (an ogre's
  growl for the Butcher, a ghost in a cave for Ghosty, kids for the twins), and a few lines for each of six events: when
  it comes onto the field, casts, gets across, is run over, gets an enemy run over, and is told to move. A hero says a
  line at most every 4 seconds, only a third of the times it casts, and the hero the camera follows is heard at full
  volume.
* **Frosty doesn't talk:** he is a snow golem, so his lines are cute noises made with the sound effects API instead
  (little squeaks, crunching snow, twinkling ice, a slushy splat when he melts).
* **Moving.** Your hero answers a right-click with one of three short lines ("On my way!", "Meat that way?", "Tick, tock."),
  quietly and only to you, as in Dota 2: the first order after 6 seconds without one gets an answer, and the clicks in
  between don't, nor while it says something else.

Each file is trimmed, made as loud as the others (-16 LUFS, the music -18 with a fade in and out), and written as an .ogg; a file that is there and was made
from the same prompt isn't made again (`data/sounds/.elevenlabs.json`). It needs an API key in `ELEVENLABS_API_KEY`, and
goes through the proxy of `https_proxy` when there is one. Run it from the folder of the repository:

```
saad run tools/make_audio.sd                          what isn't there yet, or has changed
saad run tools/make_audio.sd -- --list                the prompts and the lines
saad run tools/make_audio.sd -- ability.hex voice.hugo_cast_1
saad run tools/make_audio.sd -- music --force         the soundtrack again
```

On Linux, build it with `saad build tools/make_audio.sd --elf` and link `tools/build/out.o` with `tools/linux/link.sh` of
the Saad repository, which links OpenSSL for https.

The music is a soundtrack of four cheerful pieces for a little band, made with the music API of ElevenLabs by the same
tool: `first_light` (a sunny morning, D major), `puddles` (jumping in puddles, A major), `lanterns` (an evening market,
G major) and `far_side` (making it across, D major), from 76 to 107 seconds each. They share one style in their prompts
(a bouncy piano with pizzicato strings, a marimba, a strummed guitar and light percussion, about 112 BPM, major keys), so
they go together. The game plays them one at a time in a random order, never the same one twice in a row, with 3 to 6
seconds of silence between them (`core.Soundtrack` in `core/sound.sd`), so the music changes instead of one tune
looping all game. M turns it off and on.
Any of the files can be replaced by a recording.

## Fonts

The titles are in **Cinzel**, after the Roman capitals that the titles of Dota 2 are in, and the rest in **Fira Sans**,
which is clear at small sizes. Dota 2's own font (Radiance) isn't free to use. Other free fonts that fit, from Google Fonts:

* Titles: **Cinzel** (used), **Cormorant SC**, **Marcellus SC** or **Forum**
* Text: **Fira Sans** (used), **Source Sans 3**, **Noto Sans** or **Inter**

A font is a `.ttf` in `data/fonts`, loaded in `loadFonts()` in `hud.sd`.

## Controls

| | |
| --- | --- |
| Right click | Walk there. On an item in the backpack: lock it, or unlock it |
| Left click on an ability's icon | Cast it. One that is cast at a point (hook, blink, leap, time lock) waits for a left click on the ground; a right click calls it off |
| Q, W, E, R, D, F | The abilities of the hero: the first is on Q, the second on W, ... Passives have no key |
| 1, 2, 3 | Use the item in that slot of the backpack (a left click on it does too). After a crossing, while your hero waits: pick that perk |
| S | Stop |
| Y | Lock or unlock the camera. Locked (at the start), it follows the hero |
| Space (hold) | The camera to the hero |
| Arrow keys, or the mouse at the edge of the window | Move the camera, when it is unlocked |
| Mouse wheel | Zoom |
| M | Music on or off |
| P or Esc | Pause |
| F5 | New game |
| H | Hide the help |
| F1 | The console (twice quickly: over all of the screen). Esc or F1 closes it |
| F4 | The inspector: what a bot thinks. Tab picks the next bot |
| Tab, 1 to 6 | When spectating (`spectate` in the console) or in a replay: watch another player. The camera, the hero card and the banners follow them, and the inspector shows them. Only the view: it isn't recorded, so each viewer of a networked game could watch someone else |
| F8 | Save a recording of the game so far to `src/recordings/` |

### The console

F1 drops down the developer console, like the one of Counter-Strike: a command a line, e.g `setSpeed 8` or
`toggleMute`, and several with `;` between them. `help` lists the commands and `help setSpeed` says how one is used, Tab
completes a name, up and down go through what was typed, and the commands that match what is typed are shown under the
console with how they are used.

A command is any function with the attribute `@console.command`, in any namespace, and its parameters are what is typed
after its name: numbers, `on`/`off`, text, and enums by the names of their values. A parameter with a default or a `?T`
can be left out, and a parameter the program gives (`console.provide`), e.g the `*Game`, isn't typed at all:

```odin
@console.command("Your hero becomes another one, e.g setHero butcher")
setHero :: (game: *Game, hero: HeroKind) { ... }
```

The console itself is in `src/console/` (namespace `console`) and knows nothing of the game. The commands of the game
are in `core/commands.sd`, and the ones that start a new game (`setBots`, `setSeed`, `spectate`, `setDifficulty`,
`replay`, ...) in `main.sd`.

Commands can also be given on the command line, each after a `+`, and run before the game starts. `at <seconds>
<command>` runs one at a time of the game, so the game can be run and looked at without playing it, e.g by an agent:

```
saad run main.sd -- +setBots 5 +setSeed 7
build/out.exe +spectate +inspect 0 +setSpeed 4 +at 8 screenshot shot.png +at 10 quit
```

What a command prints goes to the standard output too. `data/autoexec.cfg`, when there is one, runs first: a command a
line.

The mouse on the icon of an ability shows what it does, and how far it reaches.

## Heroes

Twenty-one heroes, each with its own way across and its own way of getting in the way of the others. Every time a
hero is run over, the player gets another at random.

| Hero | Abilities |
| --- | --- |
| Allan, the Runner | **Sprint** (Q): twice as fast for a moment. **Adrenaline** (passive): a car that misses him by a hair makes his abilities ready again |
| Ghosty, the Restless | **Possess** (Q): slips into a car for 4 seconds; a click beside it steers it a lane over, and it still hits whoever is in its way. He comes out on the side he is going. **Phase walk** (passive): floats through the walls |
| The Butcher, a swamp brute of a butcher-monger | **Meat hook** (Q): bites into the first car it meets, up to 34 away, and he is pulled to the side of the car as it drives on. He can walk while it flies. **Heave** (W): throws a car next to him two lanes over |
| Frosty, the Snowman | **Cold snap** (Q): freezes the cars around him for 2.5 seconds, and the enemies for 1.2. **Igloo** (W): hides in an igloo for up to 10 seconds, healing 10% of his health a second; the cars drive through it and no spell finds him. W again, or a move order, and he comes out. **Chill aura** (passive): cars near him drive 40% slower |
| Bjørn, the Shieldbearer | **Leap** (Q): high over cars and walls. **Shield bash** (W): stuns the nearest enemy and knocks it 9 away. **Iron hide** (passive): half the damage |
| Hilda, the Crossing Guard | **Stop!** (Q): the five lanes around her stop for 3 seconds. **Wave through** (W): the lanes at the cursor drive two and a half times as fast for a moment. **Lollipop lady** (passive): her sign stays up as long as she stands by it, up to 8 seconds |
| Mira, the Timekeeper | **Reverse** (Q): the cars of five lanes back up the road for 2 seconds. **Rewind** (W): back to where she was 3 seconds ago. **Time lock** (E): an enemy can't move or cast for 2 seconds |
| Karl, the Mechanic | **Jack** (Q): jacks up a car for 3 seconds; anyone can walk under it. **Oil change** (W): a puddle of oil at the cursor. **Grease monkey** (passive): doesn't slide on oil |
| Birgit, the Builder | **Footbridge** (Q): a bridge over three lanes for 5 seconds, safe for anyone on it, enemies too. **Trampoline** (W): bounces anyone who walks onto it 12 on, over the cars. **Overtime** (passive): what she builds stays 50% longer |
| Bent, the Bus Driver | **Hop on** (Q): rides on the roof of a car for up to 2.5 seconds, then jumps off towards the far side. **Night bus** (W): a slow bus down the lane at the cursor; nothing gets past it, so the lane behind it is empty. **Timetable** (passive): the lanes light up before a car comes |
| Sigrid, the Witch | **Broom** (Q): flies to the cursor over the cars, without turning. **Hex** (W): turns an enemy into a toad: slow, and it can't cast. **Nine lives** (passive): once a life, a car leaves her alive |
| Tobias, the Tourist | **Flash photo** (Q): the cars in a cone brake, and the enemies in it are blinded (their screen goes white; a bot walks on blind). **Selfie** (W): swaps places with an enemy. **Blend in** (passive): standing still for 1.5 seconds, enemies can't target him |
| Mads, the Skater | **Ollie** (Q): jumps over a car. **Grind** (W): grinds the lane lines towards the cursor, very fast, untouchable. **Rolling** (passive): up to 35% faster going straight on, slower when he turns |
| Ditte, the Paramedic | **Call it in** (Q): an ambulance down the lane at the cursor. **Bandage** (W): heals 36% over 3 seconds while she stands still. **Colleague** (passive): the ambulances never hit her |
| Gudrun, the Grandmother | **Granny's crossing** (Q): for 4 seconds, the cars that come to her stop and wait until she has gone by. **Yarn leash** (W): an enemy is tied to her for 5 seconds and can't get further away; where she walks, it comes along. **Mind the cane** (passive): who walks into her trips. Slow, but 80 health |
| Magnus, the Magnet | **Repel** (Q): for 2.5 seconds, the cars that come near him are pushed into the lanes beside his, and whoever is there had better watch out. **Attract** (W): an enemy is pulled right up to him. **Steel frame** (passive): nobody shoves him or knocks him away |
| Stormy, the Weather Girl | **Lightning rod** (Q): for 6 seconds, lightning strikes the nearest enemy near it every second, or else a car. **Gust** (W): blows the enemies in a cone away, and the cars in it a lane over. **Static charge** (passive): every third spell doesn't cool down |
| Hugo, the Hypnotist | **Trance walk** (Q): for 2.2 seconds he walks slowly, and the cars go through him. **Sleep** (W): an enemy sleeps until it is shoved or hit. **Calm mind** (passive): stuns hold him half as long |
| Tim & Tom, the Twins | **Split up** (Q): the other twin walks on ahead, minding the cars: he waits for a gap, and steps back out of the way. **Swap** (W): they swap places, and the cars go through him for a moment. **Double take** (passive): spells cast on them hit the other twin first |
| Kenji, the Ninja | **Substitution** (Q): leaves a log for 5 seconds; a car that would hit him hits the log, and he is back by it. **Shadow step** (W): into the shadow right behind a car. **Shadowed** (passive): can't be targeted right next to a car |
| Ivar, the Berserker | **Berserk** (Q): for 3 seconds, a car that hits him is thrown a lane aside instead, for a little of his health. **Axe throw** (W): stuns the first enemy it hits. **Bloodlust** (passive): an enemy run over near him makes his abilities ready, and heals him |

A car on a hero takes 100 health a second (vans and trucks more), so a fragile hero (Ghosty, 15) dies at once and a
tough one (the Butcher, 100) survives a car driving over it.

### Making a hero

Each hero is a file in `src/core/heroes/`: its definition (`defineKarl()`), and the casts of the abilities that are its
own. A new hero is a value of `HeroKind`, its file, its line in `defineHero()` (`heroes.sd`), a model
(`tools/make_heroes.py`, with `tools/sculpt.py`), the icons of its abilities (`tools/make_icons.py`) and their sounds
(`tools/make_hero_sounds.py`).

* **An ability** is an `Ability` (`abilities.sd`) with the function that casts it, and numbers whose meaning its cast says
  (range, duration, radius, power, count). Abilities that several heroes share (sprint, blink, leap, freeze) are in
  `abilities.sd`. A cast that fails, e.g with no enemy in range, returns false and doesn't cool down.
* **A passive** is a `Trait` (`traits.sd`). Passives, items and perks are all traits, which add up to the `HeroStats` of the
  hero: its speed, the damage it takes, its auras, what it is immune to. A new kind of trait is a case of `Trait`, what it
  does to the stats, and where the game reads that.
* **What happens to a hero for a while** (stunned, faded, hexed, asleep, scared, a puppet, blinded, ...) is a status
  (`status.sd`): what each kind does is said once, in `statusRules`, and the game asks the hero `canAct()`, `canCast()`,
  `isTargetable()` and `carsPass()`.
* **What an ability leaves in the world** is in `motions.sd` (riding cars, dashes, footbridges), `world_effects.sd`
  (thrown things, traffic cones, decoys, banana peels), and the file of the hero for what is its own (Birgit's trampolines,
  Stormy's lightning rods). Cars can be moved to another lane (`Traffic.moveToLane`, they slide over), and each lane has a
  pace (`Traffic.setPace`): faster, or backwards.
* **The bots** know an ability by its `BotUse` (speed up, stop the cars, escape, disable an enemy, ...), so they play a new
  ability of a kind they know without new code. The forecast knows the bridges, lifted cars, the pace of each lane, the
  cars that slide over to another lane, the queue behind a bus and the immunities.

### What is on a hero

Over the hero card is a row of small icons of everything on the hero: its statuses (stunned, hasted, leashed, ...), its
passives and perks, and what holds it or helps it for a while (in a car, blended in, magnetized, a stench). The good ones
have a green border and start from the left, the bad ones a red border and start from the right. One that runs out
darkens as it goes, and the mouse on one says what it is (`core/buffs.sd`).

## A game

The first to cross the road enough times wins: short (5), medium (10) or long (15), picked on the pause screen (up and
down pick a setting, left and right change it, for the next game) or with `setGameLength` in the console. Then the
results are shown, and a new game starts after 8 seconds (or at once with F5).

Every crossing ends a round: the others stop where they are, and a moment later everyone starts again from the side it
got to, the others with the same hero. So everyone always races from the same side.

Heroes shove each other: one that walks into an enemy pushes it away, a couple of meters, further when it is heavier (by
its health: the Butcher pushes Allan far and hardly moves for him). A car that gets a hero soon after a shove counts as a
kill for the one that shoved. `core/match.sd` has all of this.

## The city

The motorway has 32 lanes and runs through a city. Heroes start on the pavement on either side, past a row of street
lamps along the walls and trees in planters, with benches, hydrants and bins; past the field are blocks of offices,
brick apartments, shops with awnings and towers, with streets between them (`core/scenery.sd`). It is only for the eye:
nothing walks into it.

## Hazards

The road doesn't stay the same, so a crossing is never quite the one before:

| | |
| --- | --- |
| No healing | Nothing heals a hero but a First Aid Kit, so every scrape counts for as long as the hero lives |
| Rush hour | After 35 to 55 calm seconds, a warning, then for 9 to 13 seconds the cars of every lane come much closer after each other. Wait it out, or get across before it comes |
| Ambulances | Every 30 to 55 seconds a siren, arrows flash down three lanes next to each other, and 2.5 seconds later three ambulances come down them, much faster than any car, with their lights flashing; the middle one a bit ahead. They are in a hurry: nothing slows them down, not a freeze, a chill aura, a stop sign or a lane driving backwards |
| Oil | Now and then a car leaks for a moment and leaves a trail of tar on its lane, which dries up after a minute or so. A hero that walks onto it slides on the way it went, a bit faster, and can't turn until it is off the oil |

Rush hour and the ambulances are in `core/traffic_events.sd`, the oil in `core/slicks.sd`. They follow the random numbers
of the game, so a replay has them at the same times. The bots hear the siren too (the forecast has the ambulance from
then on), and see the oil as never safe, so they walk around it. To try them: `rushHour`, `ambulance [lane]` and
`spawnSlick [x] [z]` (a car leaks, or a blob at x and z) in the console.

## Items

Now and then an item lies in the middle of the road, with a beam over it that is seen from far. The first hero that
walks over it puts it in the backpack of its player, which holds two (three with the perk Deep Pockets). An item is for
every hero of that player for the rest of the game; with a full backpack a new item takes the place of the oldest one,
unless it is locked (right click on it). Some items are used, like abilities: with 1, 2 or 3 (the slot), or a left
click on them; the number in their corner is how many uses they have left.

| Item | |
| --- | --- |
| Hard Hat | The cars do 35% less damage |
| Hourglass | The abilities cool down 30% faster |
| Spyglass | The abilities reach 30% further |
| First Aid Kit | 40% more health, and heals 10% of it a second, 1.5 seconds after a car. The only thing that heals, besides Ditte |
| Four-Leaf Clover | Once each hero: a car that would run it over leaves it with a bit of health |
| Garlic | A stench: enemy heroes near the hero walk 30% slower |
| Spring Shoes | A car that hits the hero bounces it over the car. Every 12 seconds |
| Mirror | The next spell cast on the hero goes back to whoever cast it. Every 15 seconds |
| Umbrella | Leaps and flights stay up 40% longer, and the hero is knocked half as far |
| Banana Peel (used, 3) | Thrown at the cursor: the first enemy that steps on it slips |
| Energy Drink (used, 2) | 70% faster for 3 seconds, then 35% slower for 2 |
| Traffic Cone (used, 3) | In the lane at the cursor for 8 seconds: the cars that come to it swerve into the lane beside it |
| Megaphone (used) | 3 seconds more on every cooldown of every enemy |
| Rubber Chicken (used) | The enemies near the hero walk towards it for a moment |
| Decoy Balloon (used) | A balloon like the hero walks on ahead; spells cast on the hero hit it first |
| Lucky Dice (used) | Casts a random ability of a random hero |
| Remote Control (used) | Steers the car at the cursor two lanes over, away from the hero |
| Stopwatch (used) | All the abilities are ready at once. Every 40 seconds |
| Snow Globe (used, 1) | Every car but the ambulances stops dead, and every enemy is frozen in time, for 1.5 seconds |
| Portal Gun (used) | A portal where the hero stands and one at the cursor, for 6 seconds: anyone who walks into one comes out of the other |

An item is a value of `ItemKind` and its definition (`core/items.sd`): its traits, and for one that is used, an `Ability`
with its charges (`core/item_abilities.sd`). The bots go for an item when the way past it isn't much longer than the way
across, and use items by their `BotUse`, like abilities. To try one: `giveItem bananaPeel`, then `useItemNow 0 x z`;
`items` says what everyone has.

## Perks

After each crossing, every player is offered three perks, at random, and keeps the one it picks for the rest of the
game: a click on its card, or 1, 2 or 3 while the hero waits for the next round. After 12 seconds one is picked for it.
They are traits, like the items, so two players with the same hero play it differently.

| Perk | |
| --- | --- |
| Thick Soles | Doesn't slip on banana peels, nor slide on oil |
| Thick Skin | 20% more health |
| Scavenger | Picks items up from 3 further away |
| Revenge | Whoever got it run over has 3 seconds more on all cooldowns |
| Hit and Run | Getting an enemy run over makes all the abilities ready again |
| Deep Pockets | One more slot in the backpack |
| Nimble | Steps aside by itself when a car is about to hit it. Every 20 seconds |
| Cold Blooded | Cars it freezes, stops or slows stay so 1 second longer |
| Hot Potato | Shoving an enemy swaps an item with it |
| Scrapper | Shoves enemies twice as far |
| Focus | 12% shorter cooldowns |
| Long Arms | The abilities reach 15% further |

A perk is a value of `PerkKind` and its definition (`core/perks.sd`). In the console, `offerPerksNow` offers perks at once,
and `perks` lists them and who has which.

## The look of the UI

Every panel, slot, icon, bar, banner, tooltip and menu is drawn with the few pieces of `core/ui.sd`, in the style of
Warcraft 3, so they all look alike: `uiPanel` (dark stone in a beveled bronze frame with gold studs), `uiSlot` (a sunken
slot, for the portrait and the items), `uiIconFrame` (the gold frame of an icon, lit up when it is active or aimed),
`uiBar` (a bar in a sunken trough), `uiPlaque` (a title on a plaque, e.g the name of the hero and the banners),
`uiDivider` (a gold line with a gem) and `uiTooltip`. The colors are `UiGold`, `UiGoldDim` and `Parchment`. The frames are
textures drawn as nine patches, so they fit any size; `tools/make_textures.py ui` makes them.

## Particles

Blood, dust, sparks, snow, stench, sparkles and the like are particles (`core/particles.sd`). What an effect looks like is
a `ParticleStyle` in `core/effect_styles.sd`, named by a value of `Fx`, and code only says where and how many:
`particles.emit(.blood, at, 60, push: ...)`, or `emitRate(.stench, at, 7, dt)` for one that goes on, like an aura.

A style has many knobs: the texture (soft, spark, smoke, drop, star, ring) and blend (alpha or additive), lifetime,
speed, the shape they start in (point, sphere, disc, ring) and the cone they set off in, gravity (below 0 rises), drag,
wobble, size and how much they grow, three colors over their life, spin, stretch along their way (sparks, drops), and
what happens on the ground (go through, bounce, lie there, or leave a stain, which is drawn flat on the road and fades).

They are quick: a pool for each texture and blend mode, without holes or allocations while playing, each drawn as one
batch of quads that face the camera. An update of 15000 takes under a millisecond with LLVM. Only a game in a window
makes them, so tests and training don't pay for them, and they have random numbers of their own, so a replay is the
same with or without them. The textures are made by `tools/make_textures.py particles`. In the console, `effect blood
60` makes one at your hero, `particles` says how many there are and what they cost, and `particleStorm 8000` makes a
lot to see it. The debug overlay (`toggleDebugOverlay`) shows the cost too.

## Speed

The game aims at 120 frames a second, also in a debug build. Where the time of a frame goes is measured
(`core/profiler.sd`): `profile` in the console, and the debug overlay (`toggleDebugOverlay`), show what the bots, the
heroes, the traffic, the effects, the city, the cars, the particles and the HUD each cost, on average and at the worst
of the last 2 seconds. To time another part, put it between `profileBegin(.part)` and `profileEnd(.part)`.

What keeps it quick:

* The bots search for their ways on threads of their own, one for each bot, so a frame never waits for a search: a bot
  goes on with the plan it has until the new one comes, a frame or a few later (`bots/search_job.sd`). Only in the
  window: the tests, the arena and training search on the thread of the game, so a seed always plays the same game.
  `toggleAsyncBots` in the console switches it.
* The forecast of the bots is made in a fraction of a millisecond: the cells the walls block are worked out once for
  each size of hero, and the safe times of a cell only when the search asks for them. Where the cars will be is the
  same for every bot, so it is worked out once a frame and copied (`trafficSnapshot`), and the distances to an item are
  kept for the last few items and sizes of hero, instead of being made again for each bot that looks.
* A search only looks 8 lanes to either side of the bot (`SearchLanes`), and a plan that doesn't get across is only
  searched again for a better one when what it keeps the bot alive for gets short, or every 2 seconds.
* Only what the camera sees is drawn: cars, their shadows, and the buildings and blocks of the city outside of the view
  are skipped. The lines on the road are one mesh, made when the game starts.

## Players and bots

Up to six players race across the same road: you and the bots. Each has a hero, a score and a side it starts on, which
flips with each crossing, and the traffic gets faster with the crossings of the player that is ahead. Some abilities are
cast on the others: the Butcher's hook drags an enemy back, Bjørn's shield bash knocks one into the traffic, and Mira's
time lock leaves one standing in the road.

Everything a player does is a `Command` (`game.sd`): walk to a point, stop, or cast an ability at a point. Your keys and
mouse make commands, and so do the bots, so a bot can do exactly what you can and nothing else. That is also what a
multiplayer game would send over the network.

A bot is a `Brain` (`core/game.sd`): anything with the methods `think`, `reset`, `free`, `setDifficulty`, `wasHit`, and
the ones the inspector draws with. The game knows nothing else of the bots, which are in their own namespace, `bots`
(`src/bots/`). The bot there
thinks in three parts, which can each be changed on its own:

1. **Forecast** (`forecast.sd`): when each cell of a grid on the ground is free of cars, for the next 24 seconds. A car
   only drives along its lane, so where it will be is a few straight pieces (frozen, sped up or backing up with its lane, held at a stop
   sign, at its own speed), and when it covers a cell is solved from them exactly. The next car of each lane is in it too,
   from when it could come at the earliest until the slowest it could be (a truck) has gone. A car after that isn't known
   at all, so a cell of the road is only known to be free until such a car could get to it: that is where what the bot
   knows of the cell ends (`known`). The other heroes are in the way too, walking on the way they walk for a moment, so
   the bots don't walk into each other and shove each other in front of a car. The intervals of a cell are only worked
   out when the search asks for them.
2. **Plan** (`planner.sd`): the fastest way across through those free times, with *Safe Interval Path Planning* (SIPP).
   It is A*, but with a state for each cell and *interval of time it is free*, instead of each cell at each step of time,
   so it waits for a gap where it must and has far fewer states. Its heuristic is the distance around the walls to the
   goal, made once for each side and size of hero, so the search only spreads out where the cars make it.

   The road is 32 lanes wide, so a way all the way across is seldom known yet. Then the plan goes to the state furthest
   across (a meter across the road counts for more than one along it, and the top and the bottom of the field count
   against it) from which the bot can stay alive for a while from now (the gene `survive`): by waiting there, or by a way
   on from there, which the search finds back from the leaves of its tree. So it doesn't walk into a corner, e.g in front
   of a car at the end of the field, or into a lane where a car that is known will catch it. When there is no such state,
   it takes the way that lives the longest. A plan is checked against each new forecast, a few times a second; one that
   doesn't get across is searched again as more is known, when what it keeps the bot alive for gets short, and a plan
   that still holds isn't swapped for a worse one. While it walks to the next point of its plan, the next search starts there, when it gets there. The
   bots take turns, one search a frame.
3. **Tactics** (`bot.sd`): which ability to cast and where, from a score per ability: e.g a blink out of the way of a car,
   a stop sign while it waits for a gap, or a hook at an enemy that is ahead. Under the plan is a reflex that steps away
   from a car that is about to hit it, e.g after an enemy moved it.

How a bot plays is its **genome** (`genome.sd`): every number of the planner, the reflex and the tactics is a gene, e.g
how often it plans, how quick it reacts, how much time it keeps before a car, when it thinks it is in danger, and how much
it values escaping, stopping the traffic, sprinting, shortcuts and casting on enemies. A new gene is a value of `Gene`
with a range in `GeneRanges`, read with `genome.get(.name)`.

### Training the bots

`src/bot_train.sd` evolves the genomes. A population plays games against each other, three to a game with one of the
hall of fame (the best of earlier generations) as the fourth. Two ways of learning from them (`--method`):

* **CMA-ES** (`cmaes`, the default, `bots/cmaes.sd`): the genomes are drawn from a cloud, a normal distribution with a
  middle, a size and a shape. From the order the genomes came in, the middle moves towards the better half, the shape
  stretches the way the steps that worked went (so it learns which genes go together, e.g. that more `survive` only
  helps with less `leadTime`), and the cloud gets bigger while it keeps going the same way and smaller near the best. It
  only uses the order, so a lucky game counts for less, and the middle of the cloud is what it keeps.
* **A genetic algorithm** (`ga`): the fittest have the children of the next generation (tournaments, crossover of the
  genes, and mutations that get smaller as it goes). The best are kept as they are and played again, so a lucky genome
  doesn't stay. Fitness (`fitnessOf` in `genome.sd`) is crossings, deaths,
kills (an enemy a car gets within 3 seconds of being hooked, bashed or locked), how far across the hero is at the end,
and how fast the best crossing was.

So that what it learns works for any game, and not only the games it happened to play: in each round of a generation
every game has the same seed (the same traffic, and the same heroes in each seat), and the candidates are shuffled into
the seats, so they are compared on the same road; the seeds are new each round, so the heroes and the events are always
others; and the traffic starts at a level at random each round (`--levels N`, up to 6), so it plays slow and fast traffic
alike.

The best of a generation is often just the luckiest in its few games, so at the end there is a playoff (`--playoff N`
games each): the hall of fame, the last elite and the hand tuned genome play against each other, and the one with the
best mean is written to `data/bots/genomes.json` (it is also written after each generation, in case training is
stopped). It is saved by the names of the genes, so it can be read and changed by hand, and the game plays with it. Games run on many threads; build it with LLVM, which makes the bots
think about 10 times as fast:

```
cd src
saad build bot_train.sd --llvm
build/out.exe --generations 50 --population 36 --games 8 --seconds 150 --threads 4
```

It starts from the trained genome (or the hand tuned one with `--from-default`), so training again goes on from where
it was.

### Difficulty

Every difficulty plays the trained genome. Expert plays it as it is; hard, normal and easy with a handicap (`difficulty.sd`):
slower to react, planning less often, later to dodge, less keen on abilities and enemies, and hesitant: it waits for
bigger gaps than it needs. `bot_arena.sd --mixed` plays a bot of each difficulty in every game, in a different seat each
game, and says how each did. With the trained genome, 20 games of 180 s on the 32 lanes:

| Difficulty | Across | Run over | Kills | Fitness a game |
|------------|-------:|---------:|------:|---------------:|
| easy       | 1      | 41       | 0     | 0.4            |
| normal     | 2      | 34       | 0     | 5.0            |
| hard       | 6      | 43       | 1     | 8.3            |
| expert     | 11     | 32       | 5     | 15.2           |

### The inspector

F4 opens the inspector on a bot, and Tab picks the next one. In the world it shows what that bot knows: the cells around
it in the color of how long they stay free of cars (red now, yellow soon, green for a while, grey for walls), its plan,
with a yellow ball where it waits for a gap, and a ring around it in the color of how soon a car is on it. The panel says
what it is doing (waiting for a gap and for how long, walking, dodging, casting, stunned), when a car gets to it, its
plan, what its last search cost, and the score of each of its abilities against the bar it casts at. The plans of the
other bots are drawn too. When you spectate, the inspector shows the player you watch (Tab); otherwise hold space to follow the inspected bot.

What the inspector shows comes from the brain (`drawInspection` and `describe` of `Brain`), so another kind of bot
shows what it thinks with.

### Recordings

F8 saves what was played so far to `src/recordings/<date>.json`, and the command `replay FILE` plays it back, e.g to see again what a
bot did, or to show a bug. The game is the same each time for the same seed, so a recording is only its settings and, for
each frame, its time step and the commands of the players. In a replay the bots think too, so the inspector works, but
their commands are the recorded ones. A checksum of the heroes every second shows when a replay stops matching, e.g
because the game was changed since it was recorded, in a banner and on the console.

```
saad run main.sd -- +replay recordings/2026-11-15_19-48-02.json +inspect 1 +setSpeed 2
```

`src/bot_arena.sd` lets bots play on their own without a window, as fast as they can, and says how they did: crossings,
deaths, the time they waited and walked, and what their thinking cost. Run it before and after changing a bot:

```
saad run bot_arena.sd -- --bots 4 --games 3 --seconds 180
saad run bot_arena.sd -- --peaceful --hits      # no casting on each other, and what a bot did when a car got it
```

## The code

The game is in the namespace `core`, in `src/core/`, and the bots in the namespace `bots`, in `src/bots/`. The core
doesn't use the bots: a bot is a `Brain` to it, and `bots.newGame` makes a game with bots in it. `src/main.sd` opens the
window and runs the loop.

| File | |
| --- | --- |
| `config.sd` | The numbers that tune the game: the size of the field, the road, the traffic |
| `heroes.sd`, `heroes/` | The heroes: what they all have, and a file for each with its abilities |
| `abilities.sd`, `traits.sd`, `status.sd` | Abilities and casting them, the traits that add up to the stats of a hero, and statuses |
| `motions.sd`, `world_effects.sd` | Riding cars, dashes, footbridges; thrown things, rain, decoys, banana peels |
| `perks.sd`, `item_abilities.sd` | The perks, and the items that are used |
| `world.sd` | The walls with their openings, and the collisions of the heroes with them |
| `traffic.sd` | The lanes and the cars |
| `game.sd` | The game itself: the players, their commands, the heroes, being run over, crossing, the next hero |
| `camera.sd` | The RTS camera |
| `effects.sd`, `particles.sd`, `effect_styles.sd` | The click marker and the rings of the abilities, the particles, and the effects made of them |
| `assets.sd`, `lighting.sd` | The textures, models and shader of the data folder |
| `inspector.sd`, `recording.sd` | The inspector of the bots (F4), and recordings and replays |
| `render.sd`, `hud.sd` | The 3D scene and the 2D overlay, with the hero drawn in 3D in its portrait |
| `sound.sd` | The `SoundPlayer`: the sounds and the music by name |
| `items.sd` | The items on the road and in the backpacks, and what they boost |
| `traffic_events.sd`, `slicks.sd` | Rush hour and the ambulances, and the oil slicks |
| `ui.sd` | The pieces every part of the UI is drawn with, in the style of Warcraft 3 |
| `temp.sd` | The temporary allocator: memory for one frame, e.g of a text that is drawn, all freed at once |
| `commands.sd`, `console_view.sd` | The console commands of the game, and the console on the screen (F1) |

`src/console/console.sd` (namespace `console`) is the console itself: it finds the commands, reads what is typed into their
parameters, and keeps the lines and the history.

| `src/bots/` | |
| --- | --- |
| `games.sd` | Games with bots, and replays of them |
| `bot.sd`, `planner.sd`, `forecast.sd` | What the bots think, how they plan a way across, what they know of the cars |
| `genome.sd`, `difficulty.sd` | The genes of a bot, the fitness training aims for, and the difficulties |
| `inspection.sd` | What a bot shows in the inspector (F4) |

`src/simulation_test.sd` plays the game without a window and checks the rules: the walls, the traffic (one way, cars
passing through each other, no room between the lanes), being run over, crossing and crossing back, the abilities, the
spells on enemies, that the forecast of the bots is right, and that a bot gets across.

```
cd src
saad run simulation_test.sd
```
