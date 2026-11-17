"""
Rig: bones and animations for the models of tools/sculpt.py.

A Rig is a skeleton of bones, each with a head (the joint it turns about), a tail and a parent. The surfaces of a model
are bound to bones (Model.add(..., bones="fore_r"), or bones=["upper_r", "fore_r"] for a part that bends between two):
a vertex of a surface bound to more than one bone gets a weight for each, from how near it is to each of them, so a
limb bends smoothly at its joint. A pose turns bones about their heads (degrees, in the frame of the parent, x then y
then z), and can move the root ("pos"). A clip is a list of (time, pose) keys.

    rig = Rig()
    rig.bone("hips", (0, 2.0, 0), (0, 2.4, 0))
    rig.bone("spine", (0, 2.4, 0), (0, 3.4, 0), "hips")
    ...
    rig.mirror()                                  # every bone ending in _r gets a twin ending in _l
    m.rig = rig
    m.clips = {"walk": walk_cycle(), ...}
    write_glb(m)                                  # data/models/<name>.glb: the mesh, the skin and the clips
    render_posed(m, pose)                         # an image of the model in a pose, in software

The game loads the GLB with raylib, which plays its clips (UpdateModelAnimation).
"""

import json
import math
import os
import struct

import numpy as np
from PIL import Image

from sculpt import OUT, mirror_bone_name, rotation


class Bone:
    def __init__(self, name, head, tail, parent):
        self.name, self.parent = name, parent
        self.head = np.asarray(head, dtype=float)
        self.tail = np.asarray(tail, dtype=float)


class Rig:
    def __init__(self):
        self.bones = {}
        self.order = []

    def bone(self, name, head, tail, parent=None):
        assert parent is None or parent in self.bones, parent
        self.bones[name] = Bone(name, head, tail, parent)
        self.order.append(name)
        return name

    def mirror(self):
        """A twin on the -x side for every bone whose name ends in _r"""
        for name in list(self.order):
            if not name.endswith("_r"):
                continue
            b = self.bones[name]
            F = np.array([-1.0, 1.0, 1.0])
            parent = mirror_bone_name(b.parent) if b.parent else None
            self.bone(mirror_bone_name(name), b.head * F, b.tail * F, parent)

    def scaled(self, k, offset):
        r = Rig()
        for name in self.order:
            b = self.bones[name]
            r.bone(name, b.head * k + offset, b.tail * k + offset, b.parent)
        return r

    def index(self, name):
        return self.order.index(name)

    # Poses

    def matrices(self, pose):
        """The 4x4 matrix of each bone in a pose, which takes a vertex where it was made to where it is in the pose"""
        out = {}
        for name in self.order:
            b = self.bones[name]
            p = pose.get(name, (0, 0, 0))
            rot, pos = (p.get("rot", (0, 0, 0)), p.get("pos", (0, 0, 0))) if isinstance(p, dict) else (p, (0, 0, 0))
            R = np.eye(4)
            R[:3, :3] = euler(rot)
            T, Ti = np.eye(4), np.eye(4)
            T[:3, 3] = b.head + np.asarray(pos, dtype=float)
            Ti[:3, 3] = -b.head
            local = T @ R @ Ti
            out[name] = (out[b.parent] @ local) if b.parent else local
        return out


def euler(rot):
    """A rotation from degrees: x, then y, then z, each about the axes of the parent"""
    rx, ry, rz = (math.radians(a) for a in rot)
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def quaternion(M):
    """(x, y, z, w) of a rotation matrix"""
    m = M
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return ((m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s)
    if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        return (0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s)
    if m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        return ((m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s)
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
    return ((m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s)


def sample(clip, t):
    """The pose of a clip at a time: its keys blended, the clip looping (or held at its last key, if it is played once)"""
    keys = clip["keys"]
    duration = clip["duration"]
    if clip.get("once"):
        t = min(max(t, 0.0), duration)
        loop = []
    else:
        t = t % duration
        loop = [(duration + keys[0][0], keys[0][1])]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:] + loop):
        if t0 <= t <= t1:
            k = (t - t0) / max(t1 - t0, 1e-9)
            k = k * k * (3 - 2 * k)
            return blend(p0, p1, k)
    return keys[-1][1] if clip.get("once") else keys[0][1]


def blend(a, b, k):
    out = {}
    for name in set(a) | set(b):
        pa, pb = a.get(name, (0, 0, 0)), b.get(name, (0, 0, 0))
        ra = pa.get("rot", (0, 0, 0)) if isinstance(pa, dict) else pa
        rb = pb.get("rot", (0, 0, 0)) if isinstance(pb, dict) else pb
        qa = pa.get("pos", (0, 0, 0)) if isinstance(pa, dict) else (0, 0, 0)
        qb = pb.get("pos", (0, 0, 0)) if isinstance(pb, dict) else (0, 0, 0)
        out[name] = {"rot": tuple(ra[i] + (rb[i] - ra[i]) * k for i in range(3)),
                     "pos": tuple(qa[i] + (qb[i] - qa[i]) * k for i in range(3))}
    return out


def clip(duration, *keys):
    return {"duration": duration, "keys": list(keys)}


#
# The mesh of a model, with the bones and weights of each vertex
#


def _segment_distance(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=-1)


def skinned_mesh(m):
    """The mesh of a model (its texture must be packed): vertices, normals, uvs (as in the OBJ), triangles, whether
    each triangle is tinted, and four bones and weights for each vertex"""
    if not getattr(m, "_packed", False):
        m._pack()
        m._packed = True
    rig = m.rig.scaled(m.post[0], m.post[1]) if getattr(m, "rig", None) else None
    V, N, U, T, tint, J, W = [], [], [], [], [], [], []
    count = 0
    for s in m.surfaces:
        verts, norms, uvs, tris = m._mesh(s)
        V.append(verts)
        N.append(norms)
        U.append(uvs)
        T.extend([(a + count, b + count, c + count) for a, b, c in tris])
        tint.extend([s.tint] * len(tris))
        joints = np.zeros((len(verts), 4), dtype=int)
        weights = np.zeros((len(verts), 4))
        if rig is not None:
            names = s.bones or [rig.order[0]]
            if len(names) == 1:
                joints[:, 0] = rig.index(names[0])
                weights[:, 0] = 1
            else:
                d = np.stack([_segment_distance(verts, rig.bones[n].head, rig.bones[n].tail) for n in names], -1)
                w = 1.0 / (d ** 4 + 1e-4)
                order = np.argsort(-w, axis=1)[:, :4]
                ws = np.take_along_axis(w, order, 1)
                ws /= ws.sum(1, keepdims=True)
                idx = np.array([rig.index(n) for n in names])
                joints[:, :order.shape[1]] = idx[order]
                weights[:, :order.shape[1]] = ws
        J.append(joints)
        W.append(weights)
        count += len(verts)
    return (np.vstack(V), np.vstack(N), np.vstack(U), np.array(T), np.array(tint), np.vstack(J), np.vstack(W), rig)


def pose_mesh(mesh, pose):
    V, N, U, T, tint, J, W, rig = mesh
    if rig is None or not pose:
        return V, N
    mats = rig.matrices(pose)
    stack = np.stack([mats[n] for n in rig.order])
    Vh = np.column_stack([V, np.ones(len(V))])
    outV = np.zeros_like(V)
    outN = np.zeros_like(N)
    for k in range(4):
        M = stack[J[:, k]]
        w = W[:, k:k + 1]
        outV += w * np.einsum("nij,nj->ni", M, Vh)[:, :3]
        outN += w * np.einsum("nij,nj->ni", M[:, :3, :3], N)
    outN /= np.maximum(np.linalg.norm(outN, axis=-1, keepdims=True), 1e-9)
    return outV, outN


#
# Pictures: the model in a pose, lit, or as a sketch with ink lines on paper
#


def render(mesh, tex, pose=None, size=420, yaw=30.0, pitch=15.0, tint_color=(0.8, 0.25, 0.2), sketch=False,
           frame=None, background=(0.2, 0.22, 0.26)):
    V, N = pose_mesh(mesh, pose)
    _, _, U, T, tint, _, _, _ = mesh
    R = rotation(pitch, yaw, 0)
    pv, pn = V @ R.T, N @ R.T
    if frame is None:
        lo, hi = pv.min(0), pv.max(0)
        frame = (lo, hi)
    lo, hi = frame
    scale = size * 0.86 / max(hi[0] - lo[0], hi[1] - lo[1])
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    sx = (pv[:, 0] - cx) * scale + size / 2
    sy = size / 2 - (pv[:, 1] - cy) * scale
    img = np.zeros((size, size, 3))
    img[:] = background
    zbuf = np.full((size, size), -1e9)
    nbuf = np.zeros((size, size, 3))
    idbuf = np.full((size, size), -1)
    light = np.array([-0.45, 0.75, 0.5])
    light /= np.linalg.norm(light)
    for fi, (a, b, c) in enumerate(T):
        xs = np.array([sx[a], sx[b], sx[c]])
        ys = np.array([sy[a], sy[b], sy[c]])
        area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
        if area >= 0:
            continue
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, size))
        y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, size))
        if x0 >= x1 or y0 >= y1:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        w0 = ((xs[1] - X) * (ys[2] - Y) - (xs[2] - X) * (ys[1] - Y)) / area
        w1 = ((xs[2] - X) * (ys[0] - Y) - (xs[0] - X) * (ys[2] - Y)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * pv[a, 2] + w1 * pv[b, 2] + w2 * pv[c, 2]
        zb = zbuf[y0:y1, x0:x1]
        msk = inside & (z > zb)
        if not msk.any():
            continue
        n = w0[..., None] * pn[a] + w1[..., None] * pn[b] + w2[..., None] * pn[c]
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        t = w0[..., None] * U[a] + w1[..., None] * U[b] + w2[..., None] * U[c]
        tx = np.clip((t[..., 0] * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)
        ty = np.clip(((1 - t[..., 1]) * tex.shape[0]).astype(int), 0, tex.shape[0] - 1)
        col = tex[ty, tx]
        if tint[fi]:
            col = col * np.array(tint_color)
        d = np.clip(n @ light, 0, 1)
        if sketch:
            lit = col * (0.72 + 0.4 * d)[..., None]
        else:
            rim = (1 - np.clip(n[..., 2], 0, 1)) ** 3 * 0.3
            lit = col * (0.55 + 0.6 * d)[..., None] + rim[..., None] * np.array([1.0, 0.92, 0.8])
        zb[msk] = z[msk]
        img[y0:y1, x0:x1][msk] = np.clip(lit[msk], 0, 1)
        nbuf[y0:y1, x0:x1][msk] = n[msk]
        idbuf[y0:y1, x0:x1][msk] = fi
    if sketch:
        img = _ink(img, zbuf, nbuf, background)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), frame


def _ink(img, zbuf, nbuf, background):
    """Ink lines where the depth or the normal jumps, hatching in the shade, on warm paper"""
    from scipy import ndimage
    covered = zbuf > -1e8
    z = np.where(covered, zbuf, zbuf[covered].min() - 1 if covered.any() else 0)
    gz = np.hypot(ndimage.sobel(z, 0), ndimage.sobel(z, 1))
    gn = sum(np.hypot(ndimage.sobel(nbuf[..., k], 0), ndimage.sobel(nbuf[..., k], 1)) for k in range(3))
    edge = np.clip((gz / (np.percentile(gz[covered], 90) + 1e-6) - 1.5) * 0.6, 0, 1) + np.clip((gn - 1.2) * 0.6, 0, 1)
    silhouette = ndimage.binary_dilation(covered) & ~ndimage.binary_erosion(covered)
    edge = np.clip(edge + silhouette * 1.0, 0, 1)
    edge = ndimage.gaussian_filter(edge, 0.6)
    h, w = covered.shape
    y, x = np.mgrid[0:h, 0:w]
    paper = np.array([0.93, 0.89, 0.8]) * (0.96 + 0.04 * np.random.default_rng(1).random((h, w)))[..., None]
    lum = img.mean(-1)
    hatch = (((x + y) % 7) < 1) & (lum < 0.33) & covered
    out = np.where(covered[..., None], img * 0.9 + paper * 0.12, paper)
    out = out * (1 - 0.35 * hatch[..., None])
    ink = np.array([0.12, 0.09, 0.07])
    return out * (1 - edge[..., None]) + ink * edge[..., None]


def texture_of(m):
    path = os.path.join(OUT, m.name + ".png")
    return np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255


#
# GLB: the mesh, its texture, the skin and the clips, for raylib
#


def write_glb(m, out=OUT, fps=15):
    mesh = skinned_mesh(m)
    V, N, U, T, tint, J, W, rig = mesh
    tex_path = os.path.join(out, m.name + ".png")
    png = open(tex_path, "rb").read()
    blob = bytearray()
    views, accessors = [], []

    def add_view(data, target=None):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    def add_accessor(arr, comp, kind, target=None, minmax=False, normalized=False):
        dtype = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[comp]
        arr = np.ascontiguousarray(arr, dtype=dtype)
        view = add_view(arr.tobytes(), target)
        a = {"bufferView": view, "componentType": comp, "count": int(arr.shape[0]), "type": kind}
        if minmax:
            a["min"] = [float(x) for x in arr.min(0)]
            a["max"] = [float(x) for x in arr.max(0)]
        if normalized:
            a["normalized"] = True
        accessors.append(a)
        return len(accessors) - 1

    pos = add_accessor(V.astype(np.float32), 5126, "VEC3", 34962, minmax=True)
    nor = add_accessor(N.astype(np.float32), 5126, "VEC3", 34962)
    uv = U.astype(np.float32).copy()
    uv[:, 1] = 1 - uv[:, 1]                 # glTF counts v from the top of the image
    tco = add_accessor(uv, 5126, "VEC2", 34962)
    attrs = {"POSITION": pos, "NORMAL": nor, "TEXCOORD_0": tco}
    if rig is not None:
        attrs["JOINTS_0"] = add_accessor(J.astype(np.uint8), 5121, "VEC4", 34962)
        attrs["WEIGHTS_0"] = add_accessor(W.astype(np.float32), 5126, "VEC4", 34962)
    big = len(V) > 65535
    prims = []
    for mat, which in ((0, False), (1, True)):
        tris = T[tint == which]
        if len(tris) == 0:
            continue
        idx = add_accessor(tris.reshape(-1).astype(np.uint32 if big else np.uint16), 5125 if big else 5123, "SCALAR", 34963)
        prims.append({"attributes": attrs, "indices": idx, "material": mat})
    img_view = add_view(png)
    gltf = {
        "asset": {"version": "2.0", "generator": "tools/rig.py"},
        "scene": 0,
        "images": [{"bufferView": img_view, "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987}],
        "textures": [{"source": 0, "sampler": 0}],
        "materials": [
            {"name": "paint", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "baseColorFactor": [0.98, 0.98, 0.98, 1], "metallicFactor": 0}},
            {"name": "body", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0}},
        ],
        "meshes": [{"name": m.name, "primitives": prims}],
    }
    # The bones come first, in the order of the skin, and the mesh last: raylib counts on it
    nodes, scene_nodes = [], []
    if rig is not None:
        base = 0
        for name in rig.order:
            b = rig.bones[name]
            parent = rig.bones[b.parent].head if b.parent else np.zeros(3)
            nodes.append({"name": name, "translation": [float(x) for x in b.head - parent]})
        for name in rig.order:
            b = rig.bones[name]
            if b.parent:
                nodes[base + rig.index(b.parent)].setdefault("children", []).append(base + rig.index(name))
            else:
                scene_nodes.append(base + rig.index(name))
        inv = np.stack([np.eye(4) for _ in rig.order]).astype(np.float32)
        for i, name in enumerate(rig.order):
            inv[i][:3, 3] = -rig.bones[name].head
        inv_acc = add_accessor(np.transpose(inv, (0, 2, 1)).reshape(len(rig.order), 16), 5126, "MAT4")
        gltf["skins"] = [{"joints": [base + i for i in range(len(rig.order))], "inverseBindMatrices": inv_acc}]
    mesh_node = {"name": m.name, "mesh": 0}
    if rig is not None:
        mesh_node["skin"] = 0
    nodes.append(mesh_node)
    scene_nodes.append(len(nodes) - 1)
    if rig is not None:
        anims = []
        for cname, c in getattr(m, "clips", {}).items():
            frames = max(2, int(round(c["duration"] * fps)) + 1)
            times = np.linspace(0, c["duration"], frames).astype(np.float32)
            t_acc = add_accessor(times[:, None], 5126, "SCALAR", minmax=True)
            accessors[t_acc]["type"] = "SCALAR"
            samplers, channels = [], []
            poses = [sample(c, float(t)) for t in times]
            for i, name in enumerate(rig.order):
                q = []
                p = []
                for pose in poses:
                    e = pose.get(name, {"rot": (0, 0, 0), "pos": (0, 0, 0)})
                    q.append(quaternion(euler(e["rot"])))
                    p.append(e["pos"])
                q_acc = add_accessor(np.array(q, dtype=np.float32), 5126, "VEC4")
                samplers.append({"input": t_acc, "output": q_acc, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": base + i, "path": "rotation"}})
                b = rig.bones[name]
                parent = rig.bones[b.parent].head if b.parent else np.zeros(3)
                tr = (np.array(p, dtype=float) * m.post[0] + (b.head - parent)).astype(np.float32)
                p_acc = add_accessor(tr, 5126, "VEC3")
                samplers.append({"input": t_acc, "output": p_acc, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": base + i, "path": "translation"}})
            anims.append({"name": cname, "samplers": samplers, "channels": channels})
        if anims:
            gltf["animations"] = anims
    gltf["nodes"] = nodes
    gltf["scenes"] = [{"nodes": scene_nodes}]
    while len(blob) % 4:
        blob.append(0)
    gltf["buffers"] = [{"byteLength": len(blob)}]
    gltf["bufferViews"] = views
    gltf["accessors"] = accessors
    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    path = os.path.join(out, m.name + ".glb")
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
    return path
