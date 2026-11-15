# Allan over vejen

Allan og hans venner har lavet en leg på motorvejen.

![Allan over vejen](./data/images/aov_map_w3.jpg)

A remake of the Warcraft 3 map *Allan over vejen*, written in [Saad](https://github.com/jakobsaadbye/Saad) with raylib.
Get your hero across a busy motorway without being run over. Every time a car gets you, you go on with a new hero at
random. Every crossing makes the traffic faster.

## Running it

With `saad` on the PATH (see the readme of Saad):

```
cd src
saad run main.sd
```

The game needs no files of its own: the textures and the shader are made when it starts. When the `data` folder is next
to `src` (it isn't in git), its grass and asphalt textures, the Warcraft cursor and the window icon are used instead.

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
| `traffic.sd` | The lanes and the cars, which keep their distance to the car in front |
| `game.sd` | The game itself: input, the hero, being run over, crossing, the next hero |
| `camera.sd` | The RTS camera |
| `effects.sd` | The click marker, the stains, the bits flying and the rings of the abilities |
| `assets.sd`, `lighting.sd` | The textures and meshes that are made at the start, and the shader of the sun |
| `render.sd`, `hud.sd` | The 3D scene and the 2D overlay |

`src/simulation_test.sd` plays the game without a window and checks the rules: the walls, the traffic, being run over,
crossing and the abilities.

```
cd src
saad run simulation_test.sd
```
