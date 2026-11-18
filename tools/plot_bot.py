"""
Draws what a bot did, from the output of bot_arena.sd --trace (one bot works best: --bots 1):

    build/out.exe --games 1 --bots 1 --peaceful --trace > trace.txt
    python3 tools/plot_bot.py trace.txt path.png                     where it was over time: x across, z along the road
    python3 tools/plot_bot.py trace.txt snaps.png --from 20 --to 28  the road around it every half second: the cars,
                                                                     the bot and its plan

In the first, the color is what it was doing (walking, waiting for a gap, without a plan, dodging) and a red line is a
car that hit it. Needs matplotlib.
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

ROAD_HALF_WIDTH = 96
LANE_WIDTH = 6
CAR_WIDTH = 5.2
MODES = {"walking": "g", "waiting": "b", "noPlan": "r", "dodging": "m", "casting": "k"}


def read(path):
    frames, hits, snaps = [], [], []
    for line in open(path):
        p = line.split()
        if not p:
            continue
        if p[0] == "TRACE":
            frames.append((float(p[1]), p[2], float(p[4][1:]), float(p[5][:-1])))
        elif p[0] == "HIT" and p[1].startswith("t="):
            hits.append(float(p[1][2:]))
        elif p[0] == "SNAP":
            snaps.append({"t": float(p[1]), "x": float(p[2]), "z": float(p[3]), "cars": [], "plan": []})
        elif p[0] == "CAR" and snaps:
            snaps[-1]["cars"].append(tuple(float(v) for v in p[1:5]))
        elif p[0] == "PLAN" and snaps:
            snaps[-1]["plan"].append(tuple(float(v) for v in p[1:5]))
    return frames, hits, snaps


def path(frames, hits, out):
    fig, ax = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    t = [f[0] for f in frames]
    colors = [MODES.get(f[1], "y") for f in frames]
    ax[0].scatter(t, [f[2] for f in frames], c=colors, s=2)
    ax[0].set_ylabel("x (across)")
    for edge in (-ROAD_HALF_WIDTH, ROAD_HALF_WIDTH):
        ax[0].axhline(edge, color="#888", lw=0.8)
    ax[1].scatter(t, [f[3] for f in frames], c=colors, s=2)
    ax[1].set_ylabel("z (along)")
    ax[1].set_xlabel("seconds")
    for h in hits:
        for a in ax:
            a.axvline(h, color="r", alpha=0.4)
    ax[0].set_title("green walking, blue waiting, red without a plan, magenta dodging, black casting; red lines: hit")
    plt.tight_layout()
    plt.savefig(out, dpi=70)


def snapshots(snaps, out, start, end):
    snaps = [s for s in snaps if start <= s["t"] <= end][:16]
    if not snaps:
        raise SystemExit("No snapshots in that time")
    cols = 4
    rows = (len(snaps) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4.6), squeeze=False)
    for ax, s in zip(axes.flat, snaps):
        for k in range(-20, 21):
            ax.axvline(-ROAD_HALF_WIDTH + LANE_WIDTH * k, color="#ccc", lw=0.5)
        for x, z, length, speed in s["cars"]:
            ax.add_patch(Rectangle((x - CAR_WIDTH / 2, z - length / 2), CAR_WIDTH, length, color="#d33", alpha=0.7))
            ax.annotate("", xy=(x, z + length / 2 + speed * 0.5), xytext=(x, z + length / 2),
                        arrowprops=dict(arrowstyle="->", color="#a00"))
        ax.plot([s["x"]] + [w[0] for w in s["plan"]], [s["z"]] + [w[1] for w in s["plan"]], "g.-", lw=1, ms=3)
        ax.add_patch(Circle((s["x"], s["z"]), 0.8, color="b"))
        ax.set_xlim(s["x"] - 25, s["x"] + 25)
        ax.set_ylim(s["z"] + 30, s["z"] - 30)     # The cars drive down, towards the camera, as in the game
        ax.set_aspect("equal")
        ends = s["plan"][-1][3] if s["plan"] else s["t"]
        ax.set_title("%.1f s, plan of %d points to %.1f s" % (s["t"], len(s["plan"]), ends), fontsize=8)
    for ax in list(axes.flat)[len(snaps):]:
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(out, dpi=60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trace")
    parser.add_argument("out")
    parser.add_argument("--from", dest="start", type=float)
    parser.add_argument("--to", dest="end", type=float)
    args = parser.parse_args()
    frames, hits, snaps = read(args.trace)
    if args.start is not None:
        snapshots(snaps, args.out, args.start, args.end if args.end is not None else args.start + 8)
    else:
        path(frames, hits, args.out)
    print(args.out)
