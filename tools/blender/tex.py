"""텍스처 그리기 — 메시의 UV 공간에 '그 텍셀이 3D에서 어디인지(위치) · 어느 쪽을 보는지(법선)'를 구워 두고,
그 위에 홈 · 긁힘 · 먼지 · 박음질 · 결 · 때를 3D 기준으로 그린다 (UV 섬 경계에서 끊기지 않는다).
결과: 색(sRGB) · 거칠기 · 노멀(탄젠트 공간) 이미지 → glTF 재질.
"""
import os, math
import numpy as np
import bpy
import odd

_PERM = None


def _perm():
    global _PERM
    if _PERM is None:
        rng = np.random.default_rng(1234); p = rng.permutation(256); _PERM = np.concatenate([p, p]).astype(np.int64)
    return _PERM


def vnoise(P, scale=1.0, seed=0):
    """3D 값 노이즈 (−1..1), 벡터화."""
    perm = _perm(); q = np.asarray(P) * scale + seed * 17.13
    i = np.floor(q).astype(np.int64); f = q - i; u = f * f * (3 - 2 * f)
    def h(dx, dy, dz):
        a = perm[(i[:, 0] + dx) & 255]; b = perm[(a + i[:, 1] + dy) & 255]; c = perm[(b + i[:, 2] + dz) & 255]
        return c / 127.5 - 1
    x0 = h(0, 0, 0) * (1 - u[:, 0]) + h(1, 0, 0) * u[:, 0]
    x1 = h(0, 1, 0) * (1 - u[:, 0]) + h(1, 1, 0) * u[:, 0]
    x2 = h(0, 0, 1) * (1 - u[:, 0]) + h(1, 0, 1) * u[:, 0]
    x3 = h(0, 1, 1) * (1 - u[:, 0]) + h(1, 1, 1) * u[:, 0]
    y0 = x0 * (1 - u[:, 1]) + x1 * u[:, 1]; y1 = x2 * (1 - u[:, 1]) + x3 * u[:, 1]
    return y0 * (1 - u[:, 2]) + y1 * u[:, 2]


def fbm(P, scale=1.0, octaves=4, seed=0, gain=.5):
    v = 0; a = 1; s = scale; tot = 0
    for k in range(octaves):
        v = v + a * vnoise(P, s, seed + k * 7); tot += a; a *= gain; s *= 2.03
    return v / tot


class Surf:
    """한 오브젝트의 UV 텍셀 ↔ 3D 위치 · 법선 (굽기 결과)."""

    def __init__(self, o, size, margin=6):
        self.o = o; self.size = size
        self.P, self.mask = _bake_vec(o, size, 'pos')
        self.N, _ = _bake_vec(o, size, 'nrm')
        self.N /= np.maximum(np.linalg.norm(self.N, axis=2, keepdims=True), 1e-9)
        self.idx = np.nonzero(self.mask.ravel())[0]
        self.p = self.P.reshape(-1, 3)[self.idx]; self.n = self.N.reshape(-1, 3)[self.idx]
        self.margin = margin

    def img(self, vals, fill=0.0):
        """텍셀 값(마스크 안) → 전체 이미지 (H, W[, C]) + 경계 밖으로 번지게."""
        vals = np.asarray(vals)
        shape = (self.size, self.size) + vals.shape[1:]
        out = np.full(shape, fill, np.float64); out.reshape((-1,) + vals.shape[1:])[self.idx] = vals
        return dilate(out, self.mask)


def _bake_vec(o, size, what):
    """위치(pos) 또는 월드 법선(nrm)을 32비트 이미지로 굽는다 (방출 셰이더)."""
    saved = [s.material for s in o.material_slots]
    M = odd.Mat('_bk_' + what); g = M.node('ShaderNodeNewGeometry'); em = M.node('ShaderNodeEmission')
    # 구운 텍셀만 골라내려고 값을 옮겨 굽는다 (위치 +100 m, 법선 +2): 굽기 전 지우기는 알파까지 1로 채워서 알파로는 구분이 안 된다
    OFF = 100.0 if what == 'pos' else 2.0
    add = M.node('ShaderNodeVectorMath'); add.operation = 'ADD'; add.inputs[1].default_value = (OFF, OFF, OFF)
    M.link(g.outputs['Position' if what == 'pos' else 'Normal'], add.inputs[0])
    M.link(add.outputs['Vector'], em.inputs['Color'])
    M.link(em.outputs['Emission'], M.out.inputs['Surface'])
    if not o.material_slots:
        o.data.materials.append(M.m)
    for s in o.material_slots:
        s.material = M.m
    im = bpy.data.images.new('_bk', size, size, alpha=True, float_buffer=True, is_data=True)
    im.generated_color = (0, 0, 0, 0)
    n = M.node('ShaderNodeTexImage'); n.image = im; M.nt.nodes.active = n
    for x in bpy.context.view_layer.objects:
        if x: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    sc = bpy.context.scene; sc.cycles.samples = 1
    with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
    a = np.empty(size * size * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(size, size, 4)
    for s, m in zip(o.material_slots, saved):
        s.material = m
    if not saved:
        o.data.materials.clear()
    bpy.data.images.remove(im); bpy.data.materials.remove(M.m)
    rgb = a[:, :, :3].astype(np.float64)
    mask = rgb.min(axis=2) > OFF * .5                                                         # 구운 텍셀 = 옮긴 값 (지운 텍셀은 0)
    return np.where(mask[..., None], rgb - OFF, 0.0), mask


def dilate(img, mask):
    from scipy.ndimage import distance_transform_edt
    if mask.all():
        return img
    _, (iy, ix) = distance_transform_edt(~mask, return_indices=True)
    return img[iy, ix]


def h2n(h, strength=1.0, px_world=None):
    """높이(이미지) → 탄젠트 공간 노멀(0..1). strength: 높이 1이 텍셀 몇 개 크기의 기울기인가."""
    gy, gx = np.gradient(h)
    n = np.stack([-gx * strength, -gy * strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * .5 + .5


def save(arr, path, srgb=True, quality=90):
    """(H, W[, C]) 0..1 → 파일 (Blender 이미지는 아래가 0행 → PIL은 위가 0행이라 뒤집는다)."""
    from PIL import Image
    a = np.clip(np.asarray(arr), 0, 1)
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    a = (a[::-1] * 255 + .5).astype(np.uint8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.fromarray(a if (a.shape[2] == 4 and not path.endswith('.jpg')) else a[:, :, :3])   # PNG는 알파(4채널)를 지킨다
    if path.endswith('.jpg'):
        im.save(path, quality=quality)
    else:
        im.save(path)
    return path


def load(path, data=False):
    im = bpy.data.images.load(path, check_existing=False)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    return im


def material(name, out_dir, base, rough, normal, **kw):
    """이미지 세 장으로 glTF 재질 (base: sRGB 색, rough: 0..1, normal: 0..1 인코딩)."""
    bp = save(base, os.path.join(out_dir, name + '_c.jpg'))
    rp = save(rough, os.path.join(out_dir, name + '_r.jpg'))
    nps = save(normal, os.path.join(out_dir, name + '_n.png')) if normal is not None else None
    return odd.gltf_material(name, base=load(bp), rough=load(rp, True), normal=load(nps, True) if nps else None, **kw)


def seg_dist(p, a, b):
    """점 배열 p(N×3)에서 선분 a-b까지 거리 · 선분 매개변수 t."""
    a = np.asarray(a, float); b = np.asarray(b, float); d = b - a; L2 = max(d @ d, 1e-18)
    t = np.clip(((p - a) @ d) / L2, 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, d)), axis=1), t


def polyline_dist(p, pts):
    """점 배열에서 꺾은선까지 최소 거리 · 그 지점의 누적 길이."""
    best = np.full(len(p), 1e9); s_at = np.zeros(len(p)); acc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        d, t = seg_dist(p, a, b); L = np.linalg.norm(np.asarray(b) - np.asarray(a))
        m = d < best; best[m] = d[m]; s_at[m] = acc + t[m] * L; acc += L
    return best, s_at


def stitches(p, pts, spacing, length, width, height=1.0):
    """꺾은선을 따라 점선 박음질 높이 (실이 표면 위로 도톰하게)."""
    d, s = polyline_dist(p, pts)
    ph = (s / spacing) % 1.0
    on = np.clip(1 - np.abs(ph - .5) / (length / spacing / 2), 0, 1) ** .6
    prof = np.clip(1 - (d / width) ** 2, 0, 1)
    hole = np.exp(-((ph - .02) / .05) ** 2) + np.exp(-((ph - .98) / .05) ** 2)
    return height * prof * on - .4 * height * np.exp(-(d / (width * 1.2)) ** 2) * hole


def tangent_frame(S):
    """텍셀마다 UV 방향의 3D 접선 T(+u) · B(+v) — 같은 UV 섬 안의 이웃으로만 미분 (섬 경계 자국 없음)."""
    from scipy.ndimage import label
    lab, _ = label(S.mask)
    P = S.P; H, W = S.mask.shape
    def diff(axis):
        fwd = np.roll(P, -1, axis); bwd = np.roll(P, 1, axis)
        lf = np.roll(lab, -1, axis); lb = np.roll(lab, 1, axis)
        okf = (lf == lab) & S.mask; okb = (lb == lab) & S.mask
        d = np.where((okf & okb)[..., None], (fwd - bwd) / 2, np.where(okf[..., None], fwd - P, np.where(okb[..., None], P - bwd, 0)))
        return d
    T = diff(1).reshape(-1, 3)[S.idx]; B = diff(0).reshape(-1, 3)[S.idx]
    n = S.n
    T = T - n * np.sum(T * n, 1, keepdims=True); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    B = B - n * np.sum(B * n, 1, keepdims=True) - T * np.sum(B * T, 1, keepdims=True)
    B /= np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-12)
    # UV가 뒤집힌 섬이면 B가 n×T 반대쪽 — 그대로 두면 glTF 탄젠트 규칙(부호 w)과 맞는다
    return T, B


def bump(S, hfun, eps, strength=1.0):
    """3D 높이 함수 hfun(points, normals) → 탄젠트 공간 노멀 이미지 (0..1). eps: 미분 간격(m). strength: 높이 1 = eps 몇 배의 볼록함."""
    T, B = tangent_frame(S); p = S.p; n = S.n
    dT = (hfun(p + T * eps, n) - hfun(p - T * eps, n)) / 2
    dB = (hfun(p + B * eps, n) - hfun(p - B * eps, n)) / 2
    v = np.stack([-dT * strength, -dB * strength, np.ones(len(p))], 1)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return S.img(v * .5 + .5, fill=.5)
