# Allan over vejen

Allan og hans venner har lavet en leg på motorvejen.

![Allan over vejen](./data/images/aov_map_w3.jpg)

A remake of the Warcraft 3 map *Allan over vejen*, written in [Saad](https://github.com/jakobsaadbye/Saad) with raylib.
Get your hero across a busy motorway without being run over. Every time a car gets you, you go on with a new hero at
random. Every crossing makes the traffic faster.

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
| `data/textures/` | The grass, the road, the Warcraft cursor |
| `data/models/` | The vehicles (car, van, truck) and the heroes, as OBJ with a MTL of their colors |
| `data/shaders/` | `lighting.vs` and `lighting.fs`: the sun, ambient light and the haze in the distance |
| `data/window_icon.png` | |

The models were made by `tools/make_models.py` (`python3 tools/make_models.py` writes them again), but they are plain OBJ
and can just as well be edited in Blender. The game expects a model to look towards +z and stand on y = 0, in the units
of the game. The body of a vehicle, the part that gets the color of the car, is the material that is pure white
(`Kd 1 1 1`), and the sizes of the vehicles are those of `config.sd` (`CarWidth`, `CarLength`, ...).

## Controls

| | |
| --- | --- |
| Right click (or left) | Walk there |
| Q | Use the ability of the hero |
| S | Stop |
| Space (hold) | Keep the camera on the hero |
| Arrow keys, or the mouse at the edge of the window | Move the camera |
| Mouse wheel | Zoom |
| P or Esc | Pause |
| F5 | New game |
| H | Hide the help |
| F1 / F2 / F3 | Wireframes / hitboxes / debug numbers |

## Heroes

| Hero | Ability |
| --- | --- |
| Allan | **Sprint** (Q): runs twice as fast for a moment |
| Ghosty | **Phase walk** (passive): floats straight through the walls, so the way across is shorter |
| Butcher | **Meat hook** (Q): hooks the ground at the cursor and pulls himself there. Big and slow |
| Frosty | **Cold snap** (Q): freezes the cars around him, and the cars behind them queue up |

## The code

All of the game is in the namespace `aov`, in `src/aov/`. `src/main.sd` opens the window and runs the loop.

| File | |
| --- | --- |
| `config.sd` | The numbers that tune the game: the size of the field, the road, the traffic |
| `heroes.sd` | The heroes, their stats and their abilities (a union) |
| `world.sd` | The walls with their openings, and the collisions of the heroes with them |
| `traffic.sd` | The lanes and the cars |
| `game.sd` | The game itself: input, the hero, being run over, crossing, the next hero |
| `camera.sd` | The RTS camera |
| `effects.sd` | The click marker, the stains, the bits flying and the rings of the abilities |
| `assets.sd`, `lighting.sd` | The textures, models and shader of the data folder |
| `render.sd`, `hud.sd` | The 3D scene and the 2D overlay |

`src/simulation_test.sd` plays the game without a window and checks the rules: the walls, the traffic (one way, cars
passing through each other, no room between the lanes), being run over, crossing and the abilities.

```
cd src
saad run simulation_test.sd
```
