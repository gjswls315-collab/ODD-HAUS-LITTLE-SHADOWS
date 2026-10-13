"""ODD HAUS — Blender(bpy 4.5) 제작 도구 공용 함수.

최종 아트 후보는 '도형 조립'이 아니라 조형 과정으로 만든다:
  · 스킨 골격(ZSphere 방식) → 서브디비전 케이지 → 고밀도 메시
  · 스컬프트 브러시(잡아당기기 · 부풀리기 · 주름 · 꼬집기 · 납작하게 · 매끈하게) — 위치 · 반경 · 감쇠를 정해 표면을 직접 다듬는다
  · 천 시뮬레이션(커튼 · 티셔츠 · 넥타이 · 쿠션 눌림)
  · 절차 재질(Cycles) → 이미지 텍스처로 굽기(색 · 거칠기 · 노멀) → glTF
좌표: Blender Z 위, 캐릭터 정면 = −Y (glTF로 내보내면 +Z 정면 · Y 위 = 게임 좌표).
게임 좌표 (x, y, z) → Blender (x, −z, y): G(x, y, z).
"""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix, noise, Euler, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

OUT = os.environ.get('ODD_OUT', os.path.join(os.getcwd(), 'out'))
TAU = math.tau


def G(x, y, z, s=1.0):
    """게임 좌표(Y 위, +Z 정면) → Blender 좌표(Z 위, −Y 정면). s = 단위 배율(cm → m 이면 0.01)."""
    return Vector((x * s, -z * s, y * s))


# ---------------------------------------------------------------- 장면
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 32
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = 'AgX'
    return sc


def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def mesh_obj(name, verts, faces, smooth=True, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    if smooth:
        me.shade_smooth()
    o = bpy.data.objects.new(name, me)
    link(o, coll)
    return o


def apply_mods(o):
    """모디파이어를 모두 적용한 메시로 바꾼다 (연산자 없이 — 백그라운드에서도 안전)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def join(objs, name):
    """여러 메시를 하나로 (재질은 슬롯으로 유지)."""
    objs = [o for o in objs if o]
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        remap = []
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons:
            if remap:
                p.material_index = remap[p.material_index]
        tmp = bmesh.new(); tmp.from_mesh(me)
        me2 = bpy.data.meshes.new('_j'); tmp.to_mesh(me2); tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2); bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out); bm.free()
    for m in mats:
        out.materials.append(m)
    o = bpy.data.objects.new(name, out); link(o)
    for x in objs:
        bpy.data.objects.remove(x, do_unlink=True)
    return o


def delete(o):
    if o and o.name in bpy.data.objects:
        bpy.data.objects.remove(o, do_unlink=True)


# ---------------------------------------------------------------- 케이지 · 스킨
def skin(name, pts, edges, radii, root=0, levels=2, smooth_shade=True, branch_smoothing=0.0, coll=None):
    """스킨 골격(점 · 선 · 반지름)으로 사각면 케이지를 만들고 서브디비전을 적용한다 (ZSphere 방식 베이스 메시).
    radii: 각 점의 반지름 r 또는 (rx, ry)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [tuple(e) for e in edges], [])
    o = bpy.data.objects.new(name, me); link(o, coll)
    m = o.modifiers.new('skin', 'SKIN')
    m.use_smooth_shade = smooth_shade
    m.branch_smoothing = branch_smoothing
    sv = me.skin_vertices[0].data
    for i, r in enumerate(radii):
        sv[i].radius = (r, r) if isinstance(r, (int, float)) else tuple(r)
        sv[i].use_root = (i == root)
    if levels:
        s = o.modifiers.new('sub', 'SUBSURF'); s.levels = levels; s.render_levels = levels
    apply_mods(o)
    if smooth_shade:
        o.data.shade_smooth()
    return o


def subsurf(o, levels=1, apply=True, crease=None):
    s = o.modifiers.new('sub', 'SUBSURF'); s.levels = levels; s.render_levels = levels
    if apply:
        apply_mods(o)
    return o


def solidify(o, t, offset=-1.0, apply=True, rim=True):
    m = o.modifiers.new('sol', 'SOLIDIFY'); m.thickness = t; m.offset = offset; m.use_rim = rim; m.use_even_offset = False; m.use_quality_normals = True
    if apply:
        apply_mods(o)
    return o


def bevel(o, w, segs=3, angle=math.radians(35), apply=True, profile=0.5):
    m = o.modifiers.new('bev', 'BEVEL'); m.width = w; m.segments = segs; m.limit_method = 'ANGLE'; m.angle_limit = angle
    m.profile = profile; m.harden_normals = False
    if apply:
        apply_mods(o)
    return o


def weighted_normals(o):
    m = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.keep_sharp = True
    apply_mods(o)
    return o


def remesh_voxel(o, size, smooth=True):
    m = o.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = size; m.use_smooth_shade = smooth
    apply_mods(o)
    return o


def decimate(o, ratio):
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = ratio
    apply_mods(o)
    return o


def shrinkwrap(o, target, offset=0.0, mode='NEAREST_SURFACEPOINT', wrap='OUTSIDE_SURFACE', apply=True, vgroup=None):
    m = o.modifiers.new('sw', 'SHRINKWRAP'); m.target = target; m.offset = offset; m.wrap_method = mode
    if mode != 'PROJECT':
        m.wrap_mode = wrap
    if vgroup:
        m.vertex_group = vgroup
    if apply:
        apply_mods(o)
    return o


# ---------------------------------------------------------------- 정점 배열 · 스컬프트 브러시
def co(o):
    a = np.empty(len(o.data.vertices) * 3, np.float64); o.data.vertices.foreach_get('co', a); return a.reshape(-1, 3)


def set_co(o, a):
    o.data.vertices.foreach_set('co', np.asarray(a, np.float64).ravel()); o.data.update()


def nrm(o):
    o.data.update()
    a = np.empty(len(o.data.vertices) * 3, np.float64); o.data.vertex_normals.foreach_get('vector', a); return a.reshape(-1, 3)


def edges(o):
    a = np.empty(len(o.data.edges) * 2, np.int64); o.data.edges.foreach_get('vertices', a); return a.reshape(-1, 2)


def falloff(d, r, kind='smooth'):
    t = np.clip(d / max(r, 1e-9), 0, 1)
    if kind == 'smooth':
        return (1 - t * t) ** 2
    if kind == 'sharp':
        return (1 - t) ** 3
    if kind == 'flat':
        return np.where(t < .6, 1.0, (1 - (t - .6) / .4) ** 2)
    return 1 - t


def _w(o, c, r, kind='smooth', a=None):
    a = co(o) if a is None else a
    d = np.linalg.norm(a - np.asarray(c), axis=1)
    return a, falloff(d, r, kind)


def grab(o, c, r, delta, kind='smooth'):
    """잡아당기기: 중심 c 반경 r 안의 표면을 delta만큼 (감쇠) 옮긴다."""
    a, w = _w(o, c, r, kind); a += np.outer(w, np.asarray(delta)); set_co(o, a)


def inflate(o, c, r, amt, kind='smooth'):
    """부풀리기(+) / 꺼뜨리기(−): 법선 방향."""
    n = nrm(o); a, w = _w(o, c, r, kind); a += n * (w * amt)[:, None]; set_co(o, a)


def scale_region(o, c, r, s, kind='smooth', axis_mask=(1, 1, 1)):
    a, w = _w(o, c, r, kind); c = np.asarray(c); m = np.asarray(axis_mask)
    a += (a - c) * (np.asarray(s) - 1) * w[:, None] * m; set_co(o, a)


def seg_dist(a, p, q):
    p, q = np.asarray(p), np.asarray(q); d = q - p; L2 = max(d @ d, 1e-12)
    t = np.clip(((a - p) @ d) / L2, 0, 1)
    cl = p + np.outer(t, d)
    return np.linalg.norm(a - cl, axis=1), cl, t


def crease(o, p, q, r, depth, kind='sharp'):
    """선을 따라 파인 주름(+depth = 안으로)."""
    n = nrm(o); a = co(o); d, cl, t = seg_dist(a, p, q); w = falloff(d, r, kind)
    a -= n * (w * depth)[:, None]; set_co(o, a)


def ridge(o, p, q, r, h, kind='smooth'):
    crease(o, p, q, r, -h, kind)


def pinch(o, p, q, r, k):
    """선 쪽으로 끌어모으기 (주름 · 이음매 날을 세운다)."""
    a = co(o); d, cl, t = seg_dist(a, p, q); w = falloff(d, r, 'smooth') * k
    a += (cl - a) * w[:, None]; set_co(o, a)


def flatten(o, c, r, normal, k=1.0, kind='flat'):
    """평면(c, normal)으로 눌러 납작하게."""
    a, w = _w(o, c, r, kind); nn = np.asarray(normal) / np.linalg.norm(normal)
    dist = (a - np.asarray(c)) @ nn; a -= np.outer(dist * w * k, nn); set_co(o, a)


def smooth(o, iters=1, k=0.5, mask=None, keep_volume=True):
    """라플라시안 매끈하게 (mask: 정점별 0..1). keep_volume: Taubin 방식으로 줄어들지 않게."""
    e = edges(o); n = len(o.data.vertices)
    deg = np.bincount(e.ravel(), minlength=n).astype(np.float64); deg[deg == 0] = 1
    m = np.ones(n) if mask is None else np.asarray(mask)
    a = co(o)
    for _ in range(iters):
        for lam in ((k, -k * 1.02) if keep_volume else (k,)):
            s = np.zeros_like(a); np.add.at(s, e[:, 0], a[e[:, 1]]); np.add.at(s, e[:, 1], a[e[:, 0]])
            a = a + (s / deg[:, None] - a) * (lam * m)[:, None]
    set_co(o, a)


def mask_box(o, lo, hi, soft=0.0):
    a = co(o); lo = np.asarray(lo); hi = np.asarray(hi)
    if soft <= 0:
        return np.all((a >= lo) & (a <= hi), axis=1).astype(np.float64)
    d = np.maximum(np.maximum(lo - a, a - hi), 0); dd = np.linalg.norm(d, axis=1)
    return np.clip(1 - dd / soft, 0, 1)


def fbm(p, octaves=4, lac=2.0, gain=0.5):
    v = 0.0; amp = 1.0; f = 1.0
    for _ in range(octaves):
        v += amp * noise.noise(Vector(p) * f); amp *= gain; f *= lac
    return v


def noise_field(a, scale, octaves=3, offset=(0, 0, 0), kind='perlin'):
    off = Vector(offset); out = np.empty(len(a))
    for i, p in enumerate(a):
        q = Vector(p) * scale + off
        if kind == 'perlin':
            out[i] = fbm(q, octaves)
        elif kind == 'voronoi':
            d, _ = noise.voronoi(q, distance_metric='DISTANCE')
            out[i] = d[0]
        else:
            out[i] = noise.turbulence(q, octaves, False)
    return out


def displace(o, amount, scale, octaves=3, mask=None, offset=(0, 0, 0)):
    a = co(o); n = nrm(o); f = noise_field(a, scale, octaves, offset)
    m = np.ones(len(a)) if mask is None else mask
    a += n * (f * amount * m)[:, None]; set_co(o, a)


def warp(o, fn):
    """임의 변형: fn(a) → 새 좌표 배열."""
    set_co(o, fn(co(o)))


def vgroup(o, name, weights):
    g = o.vertex_groups.get(name) or o.vertex_groups.new(name=name)
    for i, w in enumerate(weights):
        if w > 1e-4:
            g.add([i], float(min(1, w)), 'REPLACE')
    return g


# ---------------------------------------------------------------- 곡선(끈 · 케이블 · 머리 다발)
def curve_tube(name, pts, radius, taper=None, res=12, bevel_res=4, closed=False, radii=None, tilt=None, coll=None):
    """곡선을 따라 둥근 단면 (케이블 · 끈 · 머리 다발). radii: 점별 반지름 배율."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.resolution_u = res
    cu.bevel_depth = radius; cu.bevel_resolution = bevel_res; cu.use_fill_caps = True
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
        if radii is not None:
            sp.points[i].radius = radii[i]
        if tilt is not None:
            sp.points[i].tilt = tilt[i]
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts)); sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu); link(o, coll)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o); bpy.data.curves.remove(cu)
    mo = bpy.data.objects.new(name, me); link(mo, coll); me.shade_smooth()
    return mo


def ribbon(name, pts, widths, normal_hint=(0, 0, 1), twist=None, coll=None, uv_len=True, normals=None):
    """폭이 변하는 띠 (머리카락 카드 · 털 카드 · 끈 띠 · 스트랩). UV: u = 폭 방향 0..1, v = 길이 0..1.
    normals: 점마다 띠 면의 바깥 방향 (몸을 감아 도는 스트랩)."""
    pts = [Vector(p) for p in pts]; n = len(pts)
    verts, faces, uvs = [], [], []
    hint = Vector(normal_hint)
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        if normals is not None:
            hint = Vector(normals[i])
        side = t.cross(hint)
        if side.length < 1e-6:
            side = t.orthogonal()
        side.normalize()
        if twist is not None:
            side = Quaternion(t, twist[i]) @ side
        w = widths[i]
        verts += [p - side * w / 2, p + side * w / 2]
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    o = mesh_obj(name, verts, faces, coll=coll)
    uv = o.data.uv_layers.new(name='UVMap')
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            vi = o.data.loops[li].vertex_index
            uv.data[li].uv = (vi % 2, (vi // 2) / (n - 1))
    return o


# ---------------------------------------------------------------- 천 시뮬레이션
def cloth_sim(o, frames=60, pin_group=None, colliders=(), quality=8, mass=0.3, tension=15, bending=0.5,
              shrink=0.0, pressure=None, self_collision=False, gravity=(0, 0, -9.81), air=1.0, collide_dist=0.003, thickness_outer=0.003):
    """천 시뮬레이션을 돌리고 마지막 프레임 모양으로 굳힌다."""
    sc = bpy.context.scene
    for c in colliders:
        cm = c.modifiers.new('col', 'COLLISION'); c.collision.thickness_outer = thickness_outer; c.collision.cloth_friction = 8
    m = o.modifiers.new('cloth', 'CLOTH'); s = m.settings
    s.quality = quality; s.mass = mass; s.tension_stiffness = tension; s.compression_stiffness = tension
    s.bending_stiffness = bending; s.air_damping = air; s.shrink_min = shrink
    if pin_group:
        s.vertex_group_mass = pin_group
    if pressure is not None:
        s.use_pressure = True; s.uniform_pressure_force = pressure
    m.collision_settings.use_self_collision = self_collision
    m.collision_settings.distance_min = collide_dist
    sc.gravity = gravity
    m.point_cache.frame_start = 1; m.point_cache.frame_end = frames
    sc.frame_start = 1; sc.frame_end = frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    apply_mods(o)
    for c in colliders:
        for mm in list(c.modifiers):
            if mm.type == 'COLLISION':
                c.modifiers.remove(mm)
    sc.frame_set(1)
    return o


# ---------------------------------------------------------------- UV · 재질 · 굽기
def uv_smart(o, angle=60, margin=0.004, island_margin=None):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.view_layer.objects:
        if x: x.select_set(False)
    o.select_set(True)
    with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin if island_margin is None else island_margin, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    return o


def uv_cylinder(o, axis_origin, axis_dir=(0, 0, 1), name='UVMap'):
    """원통 좌표 UV (u = 둘레 각도, v = 축 방향 길이) — 털 · 결이 흐르는 방향."""
    a = co(o); c = np.asarray(axis_origin); d = np.asarray(axis_dir) / np.linalg.norm(axis_dir)
    rel = a - c; v = rel @ d; perp = rel - np.outer(v, d)
    ref = np.cross(d, [1, 0, 0]) if abs(d[0]) < .9 else np.cross(d, [0, 1, 0]); ref /= np.linalg.norm(ref); ref2 = np.cross(d, ref)
    ang = np.arctan2(perp @ ref2, perp @ ref) / TAU + .5
    uv = o.data.uv_layers.get(name) or o.data.uv_layers.new(name=name)
    lo, hi = v.min(), v.max()
    for poly in o.data.polygons:
        us = [ang[o.data.loops[li].vertex_index] for li in poly.loop_indices]
        mu = max(us) - min(us)
        for li in poly.loop_indices:
            vi = o.data.loops[li].vertex_index; u = ang[vi]
            if mu > .5 and u < .5:
                u += 1
            uv.data[li].uv = (u, (v[vi] - lo) / max(hi - lo, 1e-9))
    return o


class Mat:
    """노드 재질 작성기 (Cycles 룩데브용 절차 재질 — 나중에 이미지로 굽는다)."""

    def __init__(self, name):
        self.m = bpy.data.materials.new(name); self.m.use_nodes = True
        self.nt = self.m.node_tree; self.N = self.nt.nodes; self.L = self.nt.links
        self.bsdf = self.N['Principled BSDF']; self.out = self.N['Material Output']

    def node(self, t, **kw):
        n = self.N.new(t)
        for k, v in kw.items():
            if k.startswith('i_'):
                n.inputs[k[2:].replace('_', ' ')].default_value = v
            else:
                setattr(n, k, v)
        return n

    def link(self, a, b):
        self.L.new(a, b); return self

    def set(self, **kw):
        for k, v in kw.items():
            self.bsdf.inputs[k.replace('_', ' ')].default_value = v
        return self

    def inp(self, name):
        return self.bsdf.inputs[name]


def tex_coord(M, kind='Object'):
    tc = M.node('ShaderNodeTexCoord'); return tc.outputs[kind]


def noise_tex(M, vec, scale=5.0, detail=4.0, rough=0.5, dist=0.0):
    n = M.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough; n.inputs['Distortion'].default_value = dist
    if vec is not None:
        M.link(vec, n.inputs['Vector'])
    return n


def ramp(M, fac, stops):
    """stops: [(pos, (r,g,b,a)), ...]"""
    r = M.node('ShaderNodeValToRGB'); cr = r.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1]
    for p, c in stops[1:]:
        e = cr.elements.new(p); e.color = c
    M.link(fac, r.inputs['Fac'])
    return r


def math_node(M, op, a=None, b=None, va=None, vb=None, clamp=False):
    n = M.node('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    if a is not None:
        M.link(a, n.inputs[0])
    elif va is not None:
        n.inputs[0].default_value = va
    if b is not None:
        M.link(b, n.inputs[1])
    elif vb is not None:
        n.inputs[1].default_value = vb
    return n.outputs[0]


def mix_rgb(M, fac, a, b, blend='MIX'):
    n = M.node('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend
    if isinstance(fac, (int, float)):
        n.inputs[0].default_value = fac
    else:
        M.link(fac, n.inputs[0])
    for idx, v in ((6, a), (7, b)):
        if isinstance(v, (tuple, list)):
            n.inputs[idx].default_value = v
        else:
            M.link(v, n.inputs[idx])
    return n.outputs[2]


def bump(M, height, strength=0.3, distance=0.002, normal=None):
    b = M.node('ShaderNodeBump'); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = distance
    M.link(height, b.inputs['Height'])
    if normal is not None:
        M.link(normal, b.inputs['Normal'])
    return b.outputs['Normal']


def new_image(name, size, alpha=False, data=False, color=(0, 0, 0, 1)):
    im = bpy.data.images.new(name, size, size, alpha=alpha, float_buffer=False, is_data=data)
    im.generated_color = color
    if data:
        im.colorspace_settings.name = 'Non-Color'
    return im


def bake(o, kind, size, name=None, samples=4, margin=8, normal_space='TANGENT', pass_filter=None, alpha=False):
    """o의 모든 재질에서 kind(DIFFUSE · ROUGHNESS · NORMAL · AO · EMIT · GLOSSY)를 이미지로 굽는다."""
    sc = bpy.context.scene; sc.cycles.samples = samples
    im = new_image(name or f'{o.name}_{kind}', size, alpha=alpha, data=kind in ('NORMAL', 'ROUGHNESS', 'AO'),
                   color=(.5, .5, 1, 1) if kind == 'NORMAL' else (0, 0, 0, 1))
    nodes = []
    for slot in o.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; nt.nodes.active = n; n.select = True; nodes.append((nt, n))
    for x in bpy.context.view_layer.objects:
        if x: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    kw = dict(type=kind, margin=margin, use_clear=True)
    if kind == 'NORMAL':
        kw['normal_space'] = normal_space
    if kind == 'DIFFUSE':
        kw['pass_filter'] = pass_filter or {'COLOR'}
    with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.bake(**kw)
    for nt, n in nodes:
        nt.nodes.remove(n)
    return im


def save_image(im, path, fmt='PNG', quality=90):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.filepath_raw = path; im.file_format = fmt
    if fmt == 'JPEG':
        bpy.context.scene.render.image_settings.quality = quality
    im.save()
    return im


def gltf_material(name, base=None, rough=None, normal=None, base_value=(1, 1, 1, 1), rough_value=0.5, metal_value=0.0,
                  normal_strength=1.0, alpha_tex=None, alpha_mode=None, sheen=None, coat=None, aniso=None, emission=None,
                  occlusion=None, double=False, spec=0.5):
    """굽힌 텍스처로 glTF가 그대로 읽을 수 있는 재질."""
    M = Mat(name); b = M.bsdf
    if base is not None:
        t = M.node('ShaderNodeTexImage'); t.image = base; M.link(t.outputs['Color'], b.inputs['Base Color'])
        if alpha_tex == 'base':
            M.link(t.outputs['Alpha'], b.inputs['Alpha'])
    else:
        b.inputs['Base Color'].default_value = base_value
    if rough is not None:
        t = M.node('ShaderNodeTexImage'); t.image = rough; t.image.colorspace_settings.name = 'Non-Color'
        M.link(t.outputs['Color'], b.inputs['Roughness'])
    else:
        b.inputs['Roughness'].default_value = rough_value
    b.inputs['Metallic'].default_value = metal_value
    b.inputs['Specular IOR Level'].default_value = spec
    if normal is not None:
        t = M.node('ShaderNodeTexImage'); t.image = normal; t.image.colorspace_settings.name = 'Non-Color'
        nm = M.node('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_strength
        M.link(t.outputs['Color'], nm.inputs['Color']); M.link(nm.outputs['Normal'], b.inputs['Normal'])
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen[0]; b.inputs['Sheen Roughness'].default_value = sheen[1]
        b.inputs['Sheen Tint'].default_value = sheen[2]
    if coat:
        b.inputs['Coat Weight'].default_value = coat[0]; b.inputs['Coat Roughness'].default_value = coat[1]
    if aniso:
        b.inputs['Anisotropic'].default_value = aniso[0]; b.inputs['Anisotropic Rotation'].default_value = aniso[1]
    if emission:
        b.inputs['Emission Color'].default_value = emission[0]; b.inputs['Emission Strength'].default_value = emission[1]
    if alpha_mode:
        M.m.blend_method = 'CLIP' if alpha_mode == 'MASK' else 'BLEND'
        try:
            M.m.surface_render_method = 'DITHERED'
        except Exception:
            pass
    M.m.use_backface_culling = not double
    return M.m


def bake_to_gltf(o, size, kinds=('DIFFUSE', 'ROUGHNESS', 'NORMAL'), out_dir=None, jpeg=True, keep=False, **mat_kw):
    """o의 절차 재질 → 이미지 굽기 → glTF용 재질 하나로 교체."""
    out_dir = out_dir or os.path.join(OUT, 'tex')
    ims = {}
    for k in kinds:
        im = bake(o, k, size, name=f'{o.name}_{k.lower()}', samples=1 if k == 'DIFFUSE' else 4)
        fmt = 'JPEG' if (jpeg and k != 'NORMAL') else 'PNG'
        save_image(im, os.path.join(out_dir, f'{o.name}_{k.lower()}.' + ('jpg' if fmt == 'JPEG' else 'png')), fmt)
        im2 = bpy.data.images.load(im.filepath_raw); im2.name = im.name + '_f'
        if k in ('NORMAL', 'ROUGHNESS'):
            im2.colorspace_settings.name = 'Non-Color'
        ims[k] = im2
    m = gltf_material(o.name + '_M', base=ims.get('DIFFUSE'), rough=ims.get('ROUGHNESS'), normal=ims.get('NORMAL'), **mat_kw)
    if not keep:
        o.data.materials.clear()
    o.data.materials.append(m)
    if not keep:
        for p in o.data.polygons:
            p.material_index = 0
    return m


# ---------------------------------------------------------------- 내보내기 · 확인 렌더
def export_glb(path, objs=None, extras=None, vcol='MATERIAL', tangents=False):
    """tangents=True: MikkTSpace 접선을 함께 넣는다 — 이방성 반사(레코드 홈)는 접선이 없으면 three.js가 삼각형마다 접선을 따로 계산해 면마다 계단처럼 끊긴다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for x in bpy.context.view_layer.objects:
        if x: x.select_set(False)
    objs = objs or [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_image_format='WEBP', export_image_quality=88, export_tangents=tangents, export_extras=True, export_animations=False,
                              export_cameras=False, export_lights=False, export_vertex_color=vcol)
    srcmap = {os.path.splitext(os.path.basename(im.filepath))[0]: bpy.path.abspath(im.filepath) for im in bpy.data.images if im.filepath}
    lossless_normals(path, srcmap)
    fix_color0(path)
    return os.path.getsize(path)


def fix_color0(path):
    """내보내기가 흰색 COLOR_0을 따로 만들고 진짜 정점 색을 COLOR_1에 넣는 경우가 있다 — three.js는 COLOR_0만 읽으므로
    (털 카드가 전부 흰 종이띠처럼 보이던 원인) 진짜 색을 COLOR_0으로 올리고 흰 것은 뺀다. JSON만 고친다."""
    import json, struct
    b = open(path, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + jl]); rest = b[20 + jl:]
    BIN = rest[8:]
    acc = J['accessors']; fixed = 0
    def white(ai):
        a = acc[ai]; v = J['bufferViews'][a['bufferView']]
        dt = {5126: np.float32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]; n = {'VEC3': 3, 'VEC4': 4}[a['type']]
        if v.get('byteStride') and v['byteStride'] != n * np.dtype(dt).itemsize:
            return False
        x = np.frombuffer(BIN, dtype=dt, count=a['count'] * n, offset=v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, n)[:, :3]
        full = 1.0 if dt is np.float32 else np.iinfo(dt).max
        return bool(np.all(x == full))
    for m in J.get('meshes', []):
        for p in m['primitives']:
            at = p['attributes']
            if 'COLOR_0' in at and 'COLOR_1' in at and white(at['COLOR_0']):
                at['COLOR_0'] = at.pop('COLOR_1'); fixed += 1
    if not fixed:
        return 0
    js = json.dumps(J, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + len(rest))); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(rest)
    print('color0 fixed', path, fixed)
    return fixed


def lossless_normals(path, srcmap, grow=1.5):
    """노멀맵(이름이 _n)을 원본 파일에서 무손실 WebP로 다시 넣는다.
    손실 WebP는 고운 홈 · 박음질 같은 줄무늬를 16×16 블록으로 깨뜨린다 (레코드 홈이 계단처럼 보이던 원인).
    무손실이 손실보다 grow배(또는 +60 KB)를 넘게 커지면 그대로 둔다."""
    import io, json, struct
    from PIL import Image
    b = open(path, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + jl]); o2 = 20 + jl
    bl = struct.unpack('<I', b[o2:o2 + 4])[0]; BIN = b[o2 + 8:o2 + 8 + bl]
    views = J['bufferViews']; datas = [BIN[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']] for v in views]
    changed = []
    for im in J.get('images', []):
        nm = im.get('name', '')
        if not nm.endswith('_n') or nm not in srcmap or 'bufferView' not in im or not os.path.exists(srcmap[nm]):
            continue
        cur = datas[im['bufferView']]
        try:
            size = Image.open(io.BytesIO(cur)).size
        except Exception:
            continue
        src = Image.open(srcmap[nm])
        if src.size != size:
            continue
        out = io.BytesIO(); src.convert('RGB').save(out, 'WEBP', lossless=True, quality=100, method=6); out = out.getvalue()
        if len(out) <= max(grow * len(cur), len(cur) + 60000):
            datas[im['bufferView']] = out; changed.append((nm, len(cur), len(out)))
    if not changed:
        return []
    nb = bytearray()
    for v, d in zip(views, datas):
        while len(nb) % 4: nb.append(0)
        v['byteOffset'] = len(nb); v['byteLength'] = len(d); nb += d
    while len(nb) % 4: nb.append(0)
    J['buffers'][0]['byteLength'] = len(nb)
    js = json.dumps(J, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(nb)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total)); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(nb), 0x004E4942)); f.write(bytes(nb))
    print('lossless normals', path, changed)
    return changed


def lookdev_scene(mode='studio', floor=True, size=1.0):
    """확인용 조명: studio = 중립 회색 3점 조명 · game = 어두운 푸른 회색 + 따뜻한 램프 + 차가운 림."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (.18, .18, .19, 1) if mode == 'studio' else (.012, .016, .026, 1)
    bg.inputs['Strength'].default_value = 1.0
    def light(name, kind, loc, energy, color, size_=0.5, rot=None):
        L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
        if kind == 'AREA':
            L.size = size_
        o = bpy.data.objects.new(name, L); link(o); o.location = loc
        d = Vector((0, 0, size * .4)) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return o
    s = size
    if mode == 'studio':
        light('key', 'AREA', (-1.2 * s, -1.6 * s, 1.6 * s), 220 * s * s, (1, .97, .93), 1.0 * s)
        light('fill', 'AREA', (1.6 * s, -1.2 * s, .8 * s), 80 * s * s, (.93, .96, 1), 1.4 * s)
        light('rim', 'AREA', (.4 * s, 1.8 * s, 1.4 * s), 160 * s * s, (1, 1, 1), .8 * s)
    else:
        light('lamp', 'POINT', (-.9 * s, -.6 * s, .9 * s), 60 * s * s, (1, .72, .42))
        light('rim', 'AREA', (.5 * s, 1.2 * s, .9 * s), 90 * s * s, (.55, .68, 1), .5 * s)
    if floor:
        f = mesh_obj('floor', [(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [(0, 1, 2, 3)])
        fm = Mat('floorM'); fm.set(Base_Color=(.32, .32, .33, 1) if mode == 'studio' else (.05, .05, .06, 1), Roughness=.8)
        f.data.materials.append(fm.m)
    return sc


def render_views(path, target, height, views=('front', 'side', 'back', 'q34'), res=(420, 560), samples=48, dist=None, fov=24):
    """정면 · 옆 · 뒤 · 3/4 (· close) 렌더를 한 장으로 붙인다 (PIL)."""
    from PIL import Image
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = res; sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    cam = bpy.data.objects.get('ldcam') or link(bpy.data.objects.new('ldcam', bpy.data.cameras.new('ldcam')))
    cam.data.angle = math.radians(fov); cam.data.clip_start = 0.001; sc.camera = cam
    tgt = Vector(target)
    d = dist or height * 1.25 / (2 * math.tan(math.radians(fov) / 2))
    ang = {'front': 0, 'side': 90, 'back': 180, 'q34': 35, 'q34b': 145, 'sideL': -90}
    tiles = []
    for v in views:
        if v.startswith('close'):
            _, zf, yaw = (v.split(':') + ['0.5', '25'])[:3]
            a = math.radians(float(yaw)); dd = d * float(zf)
        else:
            a = math.radians(ang[v]); dd = d
        cam.location = tgt + Vector((math.sin(a) * dd, -math.cos(a) * dd, height * .05))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        p = path + f'_{v.replace(":", "_")}.png'; sc.render.filepath = p
        bpy.ops.render.render(write_still=True); tiles.append(Image.open(p).convert('RGB'))
    W = sum(t.width for t in tiles); H = max(t.height for t in tiles)
    sheet = Image.new('RGB', (W, H)); x = 0
    for t in tiles:
        sheet.paste(t, (x, 0)); x += t.width
    sheet.save(path + '.png')
    for v in views:
        try:
            os.remove(path + f'_{v.replace(":", "_")}.png')
        except OSError:
            pass
    return path + '.png'


# ---------------------------------------------------------------- 경로 · 로프트
def spline(pts, n):
    """Catmull-Rom 곡선으로 n개 점 (호 길이 균등)."""
    P_ = [Vector(p) for p in pts]
    P_ = [P_[0] * 2 - P_[1]] + P_ + [P_[-1] * 2 - P_[-2]]
    dense = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for k in range(24):
            t = k / 24
            dense.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(P_[-2])
    L = [0.0]
    for i in range(1, len(dense)):
        L.append(L[-1] + (dense[i] - dense[i - 1]).length)
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1); j = max(1, min(len(L) - 1, int(np.searchsorted(L, s))))
        t = (s - L[j - 1]) / max(L[j] - L[j - 1], 1e-12); out.append(dense[j - 1].lerp(dense[j], t))
    return out, L[-1]


def loft(name, rings, closed=True, cap_start=False, cap_end=False, coll=None):
    """링(같은 점 수) 목록을 이어 붙인 면 — 신발 갑피 · 커프 · 쿠션 단면 로프트."""
    m = len(rings[0]); verts = [tuple(p) for r in rings for p in r]; faces = []
    for i in range(len(rings) - 1):
        for k in range(m if closed else m - 1):
            k2 = (k + 1) % m
            faces.append((i * m + k, i * m + k2, (i + 1) * m + k2, (i + 1) * m + k))
    if cap_start:
        faces.append(tuple(reversed(range(m))))
    if cap_end:
        faces.append(tuple((len(rings) - 1) * m + k for k in range(m)))
    return mesh_obj(name, verts, faces, coll=coll)


# ---------------------------------------------------------------- SDF 스컬프트 (부드럽게 녹여 붙인 덩어리 → 표면)
def _np(v):
    return np.asarray(v, np.float64)


def sd_round_cone(p, a, b, ra, rb):
    """두 끝 반지름이 다른 캡슐(손가락 · 팔다리 · 털 다발)."""
    a = _np(a); b = _np(b); ba = b - a; l2 = ba @ ba; rr = ra - rb; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = p - a; y = pa @ ba; z = y - l2
    x = pa * l2 - np.outer(y, ba); x2 = np.einsum('ij,ij->i', x, x); y2 = y * y * l2; z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d1 = np.sqrt(x2 + z2) * il2 - rb
    d2 = np.sqrt(x2 + y2) * il2 - ra
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - ra
    return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))


def sd_chain(p, pts, radii, k=0.0):
    """점 · 반지름 사슬 (둥근 원뿔들을 부드럽게 합침)."""
    d = None
    for i in range(len(pts) - 1):
        di = sd_round_cone(p, pts[i], pts[i + 1], radii[i], radii[i + 1])
        d = di if d is None else (smin(d, di, k) if k > 0 else np.minimum(d, di))
    return d


def sd_ellipsoid(p, c, r, R=None):
    """타원체 (근사 거리). R: 회전 행렬(로컬 → 월드)."""
    q = p - _np(c)
    if R is not None:
        q = q @ _np(R)
    r = _np(r); k0 = np.linalg.norm(q / r, axis=1); k1 = np.linalg.norm(q / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12)


def sd_box(p, c, half, R=None, rad=0.0):
    q = p - _np(c)
    if R is not None:
        q = q @ _np(R)
    q = np.abs(q) - (_np(half) - rad)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - rad


def smin(a, b, k):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def sdf_mesh(name, fn, lo, hi, vox, coll=None, chunk=2_000_000):
    """fn(점 배열 N×3) → 거리. 격자에서 0 등위면을 뽑아 메시로 (마칭 큐브)."""
    from skimage.measure import marching_cubes
    lo = _np(lo); hi = _np(hi); n = np.ceil((hi - lo) / vox).astype(int) + 1
    xs = [lo[i] + np.arange(n[i]) * vox for i in range(3)]
    X, Y, Z = np.meshgrid(*xs, indexing='ij'); pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    vals = np.empty(len(pts))
    for s in range(0, len(pts), chunk):
        vals[s:s + chunk] = fn(pts[s:s + chunk])
    vol = vals.reshape(n)
    v, f, _, _ = marching_cubes(vol, 0.0, spacing=(vox, vox, vox))
    v += lo
    o = mesh_obj(name, v.tolist(), f[:, ::-1].tolist(), coll=coll)
    recalc(o)
    return o


def drop_islands(o, min_frac=.01):
    """마칭 큐브가 남긴 작은 떠다니는 조각을 지운다 (Quadriflow가 멈추는 원인)."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        comps.append(comp)
    n = len(bm.verts); kill = [v for c in comps if len(c) < n * min_frac for v in c]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data)
    bm.free()
    return len(kill)


def quad_remesh(o, faces=4000, smooth=True):
    """쿼드 흐름 리메시 (Quadriflow) — 고른 사각면 토폴로지로."""
    for x in bpy.context.view_layer.objects:
        if x: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    n0 = len(o.data.polygons)
    a = co(o); c = (a.max(0) + a.min(0)) / 2; k = 2.0 / max((a.max(0) - a.min(0)).max(), 1e-9)
    set_co(o, (a - c) * k)                      # Quadriflow는 몇 cm짜리 메시에서 실패한다 → 크기를 키워 리메시하고 되돌린다
    with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.quadriflow_remesh(target_faces=faces, use_preserve_sharp=False, use_preserve_boundary=False, use_mesh_symmetry=False, smooth_normals=smooth, mode='FACES')
    set_co(o, co(o) / k + c)
    if len(o.data.polygons) > faces * 3:
        raise RuntimeError(f'quad_remesh failed on {o.name}: {n0} → {len(o.data.polygons)} faces (non-manifold?)')
    if smooth:
        o.data.shade_smooth()
    return o


def project(o, pts):
    """점들을 메시 표면의 가장 가까운 점으로 (표면 위에 선 · 홈을 그릴 때)."""
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(o, dg)
    out = []
    for p in pts:
        loc, n, i, d = bvh.find_nearest(Vector(p)); out.append(loc if loc is not None else Vector(p))
    return out


def retopo(dense, faces=3000, subdiv=1, name=None):
    """SDF 스컬프트(삼각 고밀도) → 쿼드 흐름 리토폴로지 → 서브디비전 → 원래 표면에 다시 붙인다."""
    lo = bpy.data.objects.new(name or dense.name + '_rt', dense.data.copy()); link(lo)
    try:
        quad_remesh(lo, faces)
    except RuntimeError:
        # 마칭 큐브의 아주 작은 삼각형 때문에 Quadriflow가 멈추면: 복셀 리메시로 고른 사각면을 만든 뒤 다시
        a = co(lo); ext = (a.max(0) - a.min(0)).max()
        remesh_voxel(lo, ext / 120)
        quad_remesh(lo, faces)
    if subdiv:
        subsurf(lo, subdiv)
    shrinkwrap(lo, dense, mode='NEAREST_SURFACEPOINT')
    smooth(lo, 1, .25)
    shrinkwrap(lo, dense, mode='NEAREST_SURFACEPOINT')
    recalc(lo)                                     # 얇은 곳(머리 다발 등)은 감싸 붙이면서 면이 뒤집힐 수 있다 — 웹 뷰어(한 면만 그림)에서 구멍처럼 사라진다
    lo.data.shade_smooth()
    return lo


def recalc(o, inside=False):
    """면 방향을 바깥으로 맞춘다 (닫힌 메시)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inside:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def mirror_copy(o, name, plane_x=0.0):
    """X = plane_x 평면에 대한 거울 복제 (면 방향 유지)."""
    me = o.data.copy(); m2 = bpy.data.objects.new(name, me); link(m2)
    a = co(m2); a[:, 0] = 2 * plane_x - a[:, 0]; set_co(m2, a)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for m in o.data.materials:
        pass
    return m2
