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
| `data/textures/` | The grass (`grass/grass.png`), the road (`road/asphalt.png`), the Warcraft cursor |
| `data/models/` | The vehicles (car, van, truck), the heroes and a segment of the wall, as OBJ with a MTL of their colors |
| `data/icons/` | A 64x64 icon for each ability, by the name in `heroes.sd` |
| `data/sounds/` | The sound effects, by group: `hero/`, `car/`, `ability/`, `ui/` |
| `data/music/` | The music (`theme.ogg`) and the hum of the traffic (`traffic.ogg`), looped |
| `data/fonts/` | Cinzel (titles) and Fira Sans (text), both under the SIL Open Font License |
| `data/shaders/` | `lighting.vs` and `lighting.fs`: the sun, ambient light and the haze in the distance |
| `data/window_icon.png` | |

The models were made by `tools/make_models.py`, the grass, the asphalt and the icons by `tools/make_textures.py`, and
the sounds and the music by `tools/make_sounds.py`
(run them with python3 to write the files again), but they are plain files that can just as well be edited in Blender or
painted over. `Grass_02.png` and `Ground_03.png` aren't used any more. The game expects a model to look towards +z and stand on y = 0, in the units
of the game. The body of a vehicle, the part that gets the color of the car, is the material that is pure white
(`Kd 1 1 1`), and the sizes of the vehicles are those of `config.sd` (`CarWidth`, `CarLength`, ...).

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
| `ability.*` | The abilities: `sprint`, `charge`, `blink`, `hook_throw`, `hook_hit`, `freeze`, `fade`, `leap`, `land`, `stop_sign`, `time_warp`, `rewind` |
| `ui.not_ready` | An ability that is cooling down |

The music (`theme`) is a loop of a minute for a small orchestra in D minor: strings, cellos, horns, a choir, a harp and
war drums. `tools/make_sounds.py` synthesizes all of it in layers (a low body, a sharp front and a tail of reverb), from
noise, filters, struck metal, formant voices and plucked strings, so it sounds like a fantasy game rather than an 8-bit one.
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

| Hero | Abilities |
| --- | --- |
| Allan | **Sprint** (Q): runs twice as fast for a moment. **Blink** (W): jumps to the cursor. **Quick feet** (passive): 10% faster |
| Ghosty | **Fade** (Q): the cars drive through him for 1.5 seconds. **Phase walk** (passive): floats through the walls |
| Butcher | **Meat hook** (Q): an enemy the hook hits is dragged back to him; else he pulls himself to where it bites. **Charge** (W): very fast for a short moment |
| Frosty | **Cold snap** (Q): freezes the cars around him. **Slide** (W): slides to the cursor. **Chill aura** (passive): cars near him drive 40% slower |
| Bjørn | A viking. **Leap** (Q): jumps to the cursor, high over the cars and the walls. **Shield bash** (W): stuns the nearest enemy and knocks it 9 away, e.g into the traffic. **Iron hide** (passive): half the damage from the cars |
| Hilda | A crossing guard. **Stop!** (Q): raises her stop sign, and the five lanes around her stop for 3 seconds while their cars queue up. **Brisk walker** (passive): 15% faster |
| Mira | A chronomancer. **Time warp** (Q): every car on the road drives 70% slower for 3 seconds. **Rewind** (W): back to where she was 3 seconds ago, with the health she had. A ring shows where that is. **Time lock** (E): the enemy nearest the cursor can't move or cast for 2 seconds |

Every hero has health. A car on a hero takes 100 a second (vans and trucks more), and a hero heals after 1.5 seconds without
one. Allan (25), Ghosty (15) and Mira (20) don't last long, but the Butcher (100) and Bjørn (60, at half the damage) survive a car driving over them.

A hero can have any number of abilities, as many cast ones as there are keys, and passives. They are defined in `defineHeroes()` in `heroes.sd`: a
name, a description, an icon, a cooldown and an effect. A new kind of effect is a variant of `AbilityEffect`, what it does
is in `cast()` in `game.sd` (or, for a passive, where it has its effect), and when the bots use it is its case in
`scoreAbility()` in `bot.sd`. Both are switches over every effect, so the compiler says where a new one is missing.

## A game

The first to cross the road enough times wins: short (5), medium (10) or long (15), picked on the pause screen (up and
down pick a setting, left and right change it, for the next game) or with `setGameLength` in the console. Then the
results are shown, and a new game starts after 8 seconds (or at once with F5).

Every crossing ends a round: the others stop where they are, and a moment later everyone starts again from the side it
got to, the others with the same hero. So everyone always races from the same side.

Heroes shove each other: one that walks into an enemy pushes it away, a couple of meters, further when it is heavier (by
its health: the Butcher pushes Allan far and hardly moves for him). A car that gets a hero soon after a shove counts as a
kill for the one that shoved. `core/match.sd` has all of this.

## Hazards

The road doesn't stay the same, so a crossing is never quite the one before:

| | |
| --- | --- |
| No healing | Nothing heals a hero but a First Aid Kit, so every scrape counts for as long as the hero lives |
| Rush hour | After 35 to 55 calm seconds, a warning, then for 9 to 13 seconds the cars of every lane come much closer after each other. Wait it out, or get across before it comes |
| Ambulances | Every 30 to 55 seconds a siren, arrows flash down three lanes next to each other, and 2.5 seconds later three ambulances come down them, much faster than any car, with their lights flashing; the middle one a bit ahead |
| Oil | Now and then a car leaks for a moment and leaves a trail of tar on its lane, which dries up after a minute or so. A hero that walks onto it slides on the way it went, a bit faster, and can't turn until it is off the oil |

Rush hour and the ambulances are in `core/traffic_events.sd`, the oil in `core/slicks.sd`. They follow the random numbers
of the game, so a replay has them at the same times. The bots hear the siren too (the forecast has the ambulance from
then on), and see the oil as never safe, so they walk around it. To try them: `rushHour`, `ambulance [lane]` and
`spawnSlick [x] [z]` (a car leaks, or a blob at x and z) in the console.

## Items

Now and then an item lies in the middle of the road, with a beam over it that is seen from far. The first hero that
walks over it puts it in the backpack of its player, which holds two. An item boosts every hero of that player for the
rest of the game, also the heroes after the one that picked it up; with a full backpack a hero leaves an item for the
others. The first comes 10 seconds into a game, and the next 15 to 30 seconds after one is picked up. The scoreboard
shows the backpacks and when the next item comes, and the hero card yours (the mouse on an item says what it does).

| Item | |
| --- | --- |
| Sneakers | Walks 15% faster |
| Hard Hat | The cars do 35% less damage |
| Hourglass | The abilities cool down 30% faster |
| Spyglass | The abilities reach 30% further |
| First Aid Kit | 40% more health (the grey part of the health bar), and heals 10% of it a second, 1.5 seconds after a car was on it. The only thing that heals |
| Four-Leaf Clover | Once each hero: a car that would run it over leaves it with a bit of health, out of the way for a moment |
| Frost Charm | An aura of cold: the cars near the hero drive 30% slower |
| Garlic | A stench: enemy heroes near the hero walk 30% slower |
| Spring Shoes | A car that hits the hero bounces it over the car, towards the far side. Every 12 seconds |

Two of the same do it twice. With a full backpack a new item takes the place of the oldest one, unless it is locked
(right click on it); with both locked, a hero walks over items. The backpack shows the cooldown of Spring Shoes, and a
used clover darkened until the next hero. An item is a value of `ItemKind`, its definition, and what it does in `boostOf`
(`core/items.sd`); its icon is drawn by `tools/make_textures.py items`. The bots go for an item when the way past it
isn't more than the gene `itemDetour` longer than the way across. To try one: `spawnItem hourglass` or
`giveItem clover` in the console, and `items` says what everyone has.

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

1. **Forecast** (`forecast.sd`): when each cell of a grid on the ground is free of cars, for the next 12 seconds. A car
   only drives along its lane, so where it will be is a few straight pieces (frozen, slowed by a time warp, held at a stop
   sign, at its own speed), and when it covers a cell is solved from them exactly. The next car of each lane is in it too.
   The intervals of a cell are only worked out when the search asks for them.
2. **Plan** (`planner.sd`): the fastest way across through those free times, with *Safe Interval Path Planning* (SIPP).
   It is A*, but with a state for each cell and *interval of time it is free*, instead of each cell at each step of time,
   so it waits for a gap where it must and has far fewer states. Its heuristic is the distance around the walls to the
   goal, made once for each side and size of hero, so the search only spreads out where the cars make it. A plan is
   checked against each new forecast, a few times a second, and only searched again when it doesn't hold. The bots take
   turns, one search a frame.
3. **Tactics** (`bot.sd`): which ability to cast and where, from a score per ability: e.g a blink out of the way of a car,
   a stop sign while it waits for a gap, or a hook at an enemy that is ahead. Under the plan is a reflex that steps away
   from a car that is about to hit it, e.g after an enemy moved it.

How a bot plays is its **genome** (`genome.sd`): every number of the planner, the reflex and the tactics is a gene, e.g
how often it plans, how quick it reacts, how much time it keeps before a car, when it thinks it is in danger, and how much
it values escaping, stopping the traffic, sprinting, shortcuts and casting on enemies. A new gene is a value of `Gene`
with a range in `GeneRanges`, read with `genome.get(.name)`.

### Training the bots

`src/bot_train.sd` evolves the genomes with a genetic algorithm. A population plays games against each other, three to
a game with one of the hall of fame (the best of earlier generations) as the fourth, and the fittest have the children of
the next generation (tournaments, crossover of the genes, and mutations that get smaller as it goes). The best are kept
as they are and played again, so a lucky genome doesn't stay. Fitness (`fitnessOf` in `genome.sd`) is crossings, deaths,
kills (an enemy a car gets within 3 seconds of being hooked, bashed or locked), how far across the hero is at the end,
and how fast the best crossing was.

The best of a generation is often just the luckiest in its few games, so at the end there is a playoff (`--playoff N`
games each): the hall of fame, the last elite and the hand tuned genome play against each other, and the one with the
best mean is written to `data/bots/genomes.json` (it is also written after each generation, in case training is
stopped). It is saved by the names of the genes, so it can be read and changed by hand, and the game plays with it. Games run on many threads; build it with LLVM, which makes the bots
think about 10 times as fast:

```
cd src
saad build bot_train.sd --llvm
build/out.exe --generations 60 --population 24 --games 8 --seconds 120 --threads 4
```

It starts from the trained genome (or the hand tuned one with `--from-default`), so training again goes on from where
it was.

### Difficulty

Every difficulty plays the trained genome. Expert plays it as it is; hard, normal and easy with a handicap (`difficulty.sd`):
slower to react, planning less often, later to dodge, less keen on abilities and enemies, and hesitant: it waits for
bigger gaps than it needs. `bot_arena.sd --mixed` plays a bot of each difficulty in every game, in a different seat each
game, and says how each did. With the trained genome, 40 games of 120 s:

| Difficulty | Across | Run over | Kills | Fitness a game |
|------------|-------:|---------:|------:|---------------:|
| easy       | 24     | 37       | 0     | 0.5            |
| normal     | 29     | 40       | 6     | 2.3            |
| hard       | 47     | 42       | 19    | 8.0            |
| expert     | 61     | 31       | 19    | 13.7           |

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
| `heroes.sd` | The heroes, their stats and their abilities |
| `world.sd` | The walls with their openings, and the collisions of the heroes with them |
| `traffic.sd` | The lanes and the cars |
| `game.sd` | The game itself: the players, their commands, the heroes, being run over, crossing, the next hero |
| `camera.sd` | The RTS camera |
| `effects.sd` | The click marker, the stains, the bits flying and the rings of the abilities |
| `assets.sd`, `lighting.sd` | The textures, models and shader of the data folder |
| `inspector.sd`, `recording.sd` | The inspector of the bots (F4), and recordings and replays |
| `render.sd`, `hud.sd` | The 3D scene and the 2D overlay, with the hero drawn in 3D in its portrait |
| `sound.sd` | The `SoundPlayer`: the sounds and the music by name |
| `items.sd` | The items on the road and in the backpacks, and what they boost |
| `traffic_events.sd`, `slicks.sd` | Rush hour and the ambulances, and the oil slicks |
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
