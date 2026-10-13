"""Vin 리뷰 후보 (PROTOTYPE — 승인 전) — Blender에서 처음부터 다시 만든 메시.
  bl/bin/python tools/blender/vin.py  (환경 변수 ODD_OUT = 출력 폴더)
키 24 cm · 원판 지름 16 cm(중심 17.5 cm) · 게임 리그의 관절 위치(rigs.json)에 맞춘다. 게임 좌표 cm → G(x, y, z, .01).
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler, noise
import odd
from odd import G

STAGE = os.environ.get('VIN_STAGE', 'all')
RIG = json.load(open(os.environ.get('ODD_RIGS', os.path.join(odd.OUT, 'rigs.json'))))['vin']
P = lambda x, y, z: G(x, y, z, .01)
RP = lambda k: G(*RIG[k]['p'])               # rigs.json은 미터 단위

sc = odd.reset()
C = P(0, 17.5, 0)            # 원판 중심
R = .080                     # 원판 반지름 (16 cm)
TEX = os.path.join(odd.OUT, 'vin_tex')
os.makedirs(TEX, exist_ok=True)


# =====================================================================================
# 1. 레코드 몸: 단면(반지름 r → 앞면 높이 hf, 뒷면 hb)을 설계해 돌린다
#    가운데 구멍 · 라벨 단(뒷면) · 런아웃 · 홈 영역 · 트랙 사이 띠 · 리드인 · 바깥 비드 · 둥근 가장자리
# =====================================================================================
def profile():
    pts = []                                   # (r, y) — y < 0 앞면(−Y), y > 0 뒷면
    hole = .0035
    def hf(r):                                 # 앞면 두께(중심면에서 앞으로)
        h = .0050
        if r < .0425: h = .0054                # 앞 라벨 단 (빨간 종이 라벨 · 눈이 그 위에 얹힌다 — 콘셉트 시트)
        elif r < .0465: h = .0050 - .0002 * math.sin((r - .0425) / .004 * math.pi)  # 런아웃 골
        bead = math.exp(-((r - .0772) / .0016) ** 2) * .0011   # 바깥 비드
        return h + bead
    def hb(r):
        h = .0050
        if r < .0215: h = .0056               # 라벨 단 (뒷면)
        elif r < .0235: h = .0056 - .0006 * (r - .0215) / .002
        bead = math.exp(-((r - .0772) / .0016) ** 2) * .0011
        return h + bead
    # 앞면: 가운데 → 바깥 (구멍은 뒷면에서만 3.8 mm 깊이 — 앞에서는 눈 사이가 매끈하다)
    rs = list(np.linspace(hole, .0420, 18)) + [.0428, .0438, .0452, .0465] + list(np.linspace(.0478, .0742, 7)) + list(np.linspace(.0754, .0786, 4))
    for r in [0.0, .0018] + rs:
        pts.append((r, -hf(r)))
    # 둥근 가장자리: r .0786 → .0800 반원 (앞 → 뒤)
    re = .0786; t0 = hf(re); t1 = hb(re)
    for k in range(1, 12):
        a = -math.pi / 2 + math.pi * k / 12
        pts.append((re + (R - re) * math.cos(a), (t0 if a < 0 else t1) * math.sin(a)))
    for r in reversed(rs):
        pts.append((r, hb(r)))
    pts += [(hole * .97, .0030), (hole * .9, .0019), (.0026, .0017), (0.0, .0017)]      # 막힌 구멍 벽 · 바닥
    return pts


def revolve(name, prof, n=160, closed_hole=True):
    """단면(r, y)을 Y축(원판 법선) 둘레로 돌린 메시. 구멍 벽은 첫 점과 끝 점을 잇는 면."""
    verts, faces = [], []
    m = len(prof)
    for i in range(n):
        a = TAU * i / n
        for r, y in prof:
            verts.append((C.x + r * math.cos(a), C.y + y, C.z + r * math.sin(a)))
    for i in range(n):
        j = (i + 1) % n
        for k in range(m - 1 + (1 if closed_hole else 0)):
            k2 = (k + 1) % m
            faces.append((i * m + k, j * m + k, j * m + k2, i * m + k2))
    return odd.mesh_obj(name, verts, faces)


TAU = math.tau
prof = profile()
body = revolve('Vin_Body', prof, n=128, closed_hole=False)
_bm = bmesh.new(); _bm.from_mesh(body.data)
bmesh.ops.remove_doubles(_bm, verts=_bm.verts, dist=1e-7)
bmesh.ops.dissolve_degenerate(_bm, edges=_bm.edges, dist=1e-7)
bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces)
_bm.to_mesh(body.data); _bm.free(); body.data.shade_smooth()

# 원판 좌표(반지름 · 각도 · 앞/뒤)
def polar(a):
    rel = a - np.array(C)
    r = np.hypot(rel[:, 0], rel[:, 2]); th = np.arctan2(rel[:, 2], rel[:, 0])
    return rel, r, th

# 미세한 휨(warp): 두 번 접힌 물결 — 가장자리에서 최대 0.9 mm
def _warp(a):
    rel, r, th = polar(a)
    a[:, 1] += .0009 * (r / R) ** 2 * np.sin(2 * th + .7) + .0004 * (r / R) ** 3 * np.sin(3 * th - 1.1)
    return a
odd.warp(body, _warp)

# ---------- 눈 자리: 콘셉트 시트처럼 두 눈이 거의 닿게 가운데로 모은다 (리그의 눈 높이 · 가운데는 그대로) ----------
_E0, _E1 = RP('eye0'), RP('eye1'); _xm = (_E0.x + _E1.x) / 2
EA = (.0150, .0265)            # 눈알 반지름 (가로 · 세로) — 세로로 긴 알약 모양
EYE = [Vector((_xm - .0162, _E0.y, _E0.z)), Vector((_xm + .0162, _E1.y, _E1.z))]

# =====================================================================================
# 2. 눈: 라벨 위에 얹힌 흰 유광 구슬(세로로 긴 타원 · 앞이 둥글게 볼록) — 눈꺼풀 없음 (콘셉트 시트)
# =====================================================================================
def eyeball(name, c, ax, ay, depth, tilt=0.0):
    """구를 펴서 만든 쿼드 볼 → 타원 · 뒤 납작 · 앞 볼록을 직접 조형. tilt: 위가 바깥으로 기우는 각도(라디안)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=7, use_grid_fill=True)
    for v in bm.verts:
        v.co = v.co.normalized()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); odd.link(o); me.shade_smooth()
    a = odd.co(o)
    x, y, z = a[:, 0], a[:, 1], a[:, 2]          # y < 0 앞
    yy = np.where(y < 0, y * depth * (1 + .06 * np.exp(-((x * x + z * z) / .25))), y * depth * .45)   # 앞 볼록 · 뒤 납작
    X, Z = x * ax, z * ay; ct, st = math.cos(tilt), math.sin(tilt)
    a = np.stack([X * ct - Z * st, yy, X * st + Z * ct], 1) + np.array(c)
    odd.set_co(o, a)
    odd.subsurf(o, 1)
    return o

eyes = []; eye_c = {}
for i, e in enumerate(EYE):
    c = Vector((e.x, C.y - .0062, e.z))                                    # 라벨 면(앞 5.4 mm) 바로 앞 — 앞으로 약 1 cm 볼록
    eyes.append(eyeball(f'Vin_Eye{i}', c, EA[0], EA[1], .0098, tilt=(.10 if i == 0 else -.10))); eye_c[eyes[-1].name] = c



# =====================================================================================
# 3. 장갑: SDF 스컬프트(손바닥 · 손가락 4개 따로 · 손가락 뿌리만 녹여 붙임) → 쿼드 리토폴로지 → 박음질 홈 · 손가락 주름
#    + 말린 커프(단면 로프트 → 두께)
# =====================================================================================
def hand_frame(i):
    """손목 기준 틀: d = 손가락 방향(아래), b = 손등 법선(바깥 · 조금 앞), t = 엄지 쪽(안 · 앞)."""
    w = RP(f'hand{i}'); side = 1 if i == 0 else -1          # 0 = 왼손(−x)
    d = (RP(f'arm{i}_6') - RP(f'arm{i}_5')).normalized()
    d = (d + Vector((0, -.18, 0))).normalized()               # 손끝이 살짝 앞으로
    out = Vector((-side, 0, 0)); fwd = Vector((0, -1, 0))
    b = (out * math.cos(math.radians(38)) + fwd * math.sin(math.radians(38)))
    b = (b - d * b.dot(d)).normalized()
    t = (b.cross(d) * side).normalized()
    return w, d, b, t, side


def glove(i):
    w, d, b, t, side = hand_frame(i)
    Rm = np.column_stack([np.array(t), np.array(b), np.array(d)])
    W = lambda lx, ly, lz: np.array(w + (t * lx + b * ly + d * lz) * .01)
    cm = .01
    fingers = [(.93, 14, 1.95), (0.0, 2, 2.15), (-.92, -11, 1.9)]
    def fn(p):
        dd = odd.sd_ellipsoid(p, W(0, .05, 1.95), np.array([1.38, .66, 1.18]) * cm, Rm)
        dd = odd.smin(dd, odd.sd_round_cone(p, W(0, 0, .3), W(0, .02, 1.3), .92 * cm, 1.12 * cm), .3 * cm)
        fd = None
        for lx0, ang, L in fingers:
            a = math.radians(ang); base = np.array([lx0, -.05, 2.5])
            dirv = np.array([math.sin(a), 0, math.cos(a)])
            p0 = W(*base); p1 = W(*(base + dirv * L * .5 + np.array([0, -.16, 0])))
            p2 = W(*(base + dirv * L * .93 + np.array([0, -.46, 0])))
            f = odd.sd_chain(p, [p0, p1, p2], [.41 * cm, .405 * cm, .43 * cm], k=.12 * cm)
            fd = f if fd is None else np.minimum(fd, f)
        th = odd.sd_chain(p, [W(1.0, -.28, 1.3), W(1.58, -.52, 1.92), W(1.9, -.78, 2.5)], [.47 * cm, .44 * cm, .45 * cm], k=.1 * cm)
        fd = np.minimum(fd, th)
        return odd.smin(dd, fd, .2 * cm)
    pts = np.array([W(x, y, z) for x in (-3, 3) for y in (-2, 2) for z in (-.5, 5.6)])
    dense = odd.sdf_mesh(f'_gl{i}', fn, pts.min(0) - .004, pts.max(0) + .004, .00035)
    odd.smooth(dense, 2, .4)
    g = odd.retopo(dense, 1150, 1, f'Vin_Glove{i}')
    odd.delete(dense)
    # 손등 박음질 홈 3줄 (손목 쪽에서 손가락 사이로)
    for lx in (-.55, 0, .55):
        a_, b_ = odd.project(g, [W(lx * .8, .8, .9), W(lx, .8, 2.25)])
        odd.crease(g, a_, b_, .0007, .00028)
    # 손가락 마디 주름 (손등 쪽 짧은 홈 두 개씩)
    for lx0, ang, L in fingers:
        a = math.radians(ang); base = np.array([lx0, -.05, 2.5]); dirv = np.array([math.sin(a), 0, math.cos(a)])
        for f_ in (.38, .5):
            c = base + dirv * L * f_ + np.array([0, .3, 0]); perp = np.array([math.cos(a), 0, -math.sin(a)])
            a_, b_ = odd.project(g, [W(*(c - perp * .2)), W(*(c + perp * .2))])
            odd.crease(g, a_, b_, .0006, .00018)
    # 말린 커프: 단면 (반지름, 손목 축 위치) → 둘레로 돌린 로프트 → 두께
    prof = [(1.0, .6), (1.03, .2), (1.09, -.3), (1.2, -.68), (1.34, -.9), (1.47, -.95), (1.53, -.86), (1.47, -.76)]
    rings = []
    for r, z in prof:
        ring = []
        for k in range(28):
            a = TAU * k / 28; ring.append(Vector(W(r * math.cos(a), r * .86 * math.sin(a), z)))
        rings.append(ring)
    cf = odd.loft(f'Vin_Cuff{i}', rings)
    odd.solidify(cf, .0009, offset=-1)
    odd.subsurf(cf, 1)
    return g, cf

gloves = [glove(0)]
# 오른손 = 왼손의 거울 (같은 UV · 텍스처를 쓴다) — 리그의 0.2 cm 비대칭만큼 옮긴다
_dh = RP('hand1') - Vector((-RP('hand0').x, RP('hand0').y, RP('hand0').z))
gloves.append(tuple(odd.mirror_copy(o, o.name.replace('0', '1')) for o in gloves[0]))
for o in gloves[1]:
    odd.set_co(o, odd.co(o) + np.array(_dh))

# =====================================================================================
# 4. 고무호스 팔다리: 원판 가장자리의 고무 부트(넓게 → 좁게) · 가운데가 살짝 굵은 몸 · 손목 · 발목으로 가늘게
# =====================================================================================
def limb(name, pts, rad, n=22):
    path, L = odd.spline(pts, n)
    s = np.linspace(0, 1, n); rk = np.array([r for _, r in rad]); sk = np.array([q for q, _ in rad])
    rr = np.interp(s, sk, rk)
    o = odd.skin(name, path, [(k, k + 1) for k in range(n - 1)], [float(r) for r in rr], levels=2)
    return o, path

def grommet(name, at, axis):
    """팔다리가 원판 가장자리에 끼워지는 고무 그로밋: 둥근 테가 있는 짧은 슬리브 (단면을 팔다리 축 둘레로)."""
    axis = axis.normalized(); u = axis.orthogonal().normalized(); v = axis.cross(u)
    prof = [(.0049, -.0034), (.0064, -.0031), (.0074, -.0022), (.0079, -.0008), (.0079, .0008), (.0074, .0021), (.0066, .0030), (.0058, .0035), (.0054, .0040)]
    rings = [[at + axis * z + (u * math.cos(TAU * k / 24) + v * math.sin(TAU * k / 24)) * r for k in range(24)] for r, z in prof]
    o = odd.loft(name, rings); odd.solidify(o, .0007, offset=-1)
    return o

arms, legs, grommets = [], [], []
for i in (0, 1):
    a0 = RP(f'arm{i}_0'); dirv = Vector((a0.x - C.x, 0, a0.z - C.z)).normalized(); rim = C + dirv * R
    pts = [rim - dirv * .002, rim + dirv * .002] + [RP(f'arm{i}_{k}') for k in range(1, 7)] + [RP(f'hand{i}') + hand_frame(i)[1] * .006]
    o, path = limb(f'Vin_Arm{i}', pts, [(0, .0042), (.04, .0060), (.25, .0057), (.6, .0055), (.85, .0051), (1, .0049)])
    arms.append(o); grommets.append(grommet(f'Vin_Grommet_Arm{i}', rim, path[2] - path[0]))
    l0 = RP(f'leg{i}_0'); dirv = Vector((l0.x - C.x, 0, l0.z - C.z)).normalized(); rim = C + dirv * R
    pts = [rim - dirv * .002, rim + dirv * .003] + [RP(f'leg{i}_{k}') for k in range(2, 7)] + [RP(f'leg{i}_6') + Vector((0, .002, -.012))]
    o, path = limb(f'Vin_Leg{i}', pts, [(0, .0046), (.04, .0068), (.3, .0064), (.65, .0062), (.85, .0059), (1, .0057)])
    legs.append(o); grommets.append(grommet(f'Vin_Grommet_Leg{i}', rim, path[2] - path[0]))

# =====================================================================================
# 5. 빨간 하이탑 (shoe.py): 오른발(캐릭터 오른쪽 = −X)을 만들고 거울로 왼발
# =====================================================================================
import shoe
def place0(v):
    o = RP('shoe0'); return o + Vector((-v.x, -v.y, v.z)) * .01
shoes0 = shoe.build('Vin_Shoe0', place0, side=1, collar_y=-.9)
shoes1 = {k: odd.mirror_copy(o, o.name.replace('Shoe0', 'Shoe1')) for k, o in shoes0.items()}

if STAGE in ('body', 'upper'):
    odd.lookdev_scene('studio', size=.3)
    m = odd.Mat('clay'); m.set(Base_Color=(.08, .08, .085, 1), Roughness=.35)
    w = odd.Mat('white'); w.set(Base_Color=(.9, .9, .88, 1), Roughness=.2)
    body.data.materials.append(m.m)
    for e in eyes: e.data.materials.append(w.m)
    for o in arms + legs + grommets: o.data.materials.append(m.m)
    for g_, c_ in gloves: g_.data.materials.append(w.m); c_.data.materials.append(w.m)
    red = odd.Mat('redclay'); red.set(Base_Color=(.5, .06, .05, 1), Roughness=.6)
    for sh in (shoes0, shoes1):
        for k, o in sh.items():
            o.data.materials.append(red.m if k in ('upper', 'tongue') else w.m)
    print(odd.render_views(os.path.join(odd.OUT, 'vin_body'), C - Vector((0, 0, .055)), .27, views=('front', 'side', 'back', 'q34')))
    ctr = Vector(np.mean(odd.co(shoes0['upper']), 0))
    print(odd.render_views(os.path.join(odd.OUT, 'vin_shoe'), ctr, .065, views=('front', 'side', 'q34', 'back', 'close:1:-50', 'close:1:-130')))
    hw = gloves[1][0]; ctr = Vector(np.mean(odd.co(hw), 0))
    print(odd.render_views(os.path.join(odd.OUT, 'vin_glove'), ctr, .07, views=('front', 'side', 'q34', 'back', 'close:1:-60')))
    sys.exit(0)

# =====================================================================================
# 6. 재질 · 텍스처 (tex.py: UV 텍셀마다 3D 위치 · 법선을 구워 그 위에 그린다)
# =====================================================================================
import tex
from PIL import Image, ImageDraw, ImageFont
TD = os.path.join(odd.OUT, 'vin_tex'); os.makedirs(TD, exist_ok=True)
rng = np.random.default_rng(7)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT2 = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'

def polar_uv(o):
    """레코드 UV: u = 둘레 각도(이방성 반사 방향 = 홈 방향), v = 반지름 (앞면 0..0.49 · 뒷면 0.51..1)."""
    me = o.data; uv = me.uv_layers.new(name='UVMap'); a = odd.co(o)
    rel = a - np.array(C); r = np.hypot(rel[:, 0], rel[:, 2]); th = (np.arctan2(rel[:, 2], rel[:, 0]) / TAU) % 1.0
    for poly in me.polygons:
        vi = [me.loops[li].vertex_index for li in poly.loop_indices]
        back = np.mean(rel[vi, 1]) > 0
        us = th[vi].copy()
        if us.max() - us.min() > .5: us[us < .5] += 1
        for li, u in zip(poly.loop_indices, us):
            v_ = me.loops[li].vertex_index
            uv.data[li].uv = (u, (.51 if back else 0) + min(r[v_] / R, 1) * .49)

def planar_uv(o, c, half, flip=False):
    me = o.data; uv = me.uv_layers.new(name='UVMap'); a = odd.co(o)
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = a[me.loops[li].vertex_index]
            u = .5 + (p[0] - c[0]) / (2 * half) * (-1 if flip else 1); v = .5 + (p[2] - c[2]) / (2 * half)
            uv.data[li].uv = (u, v)

def groove_height(rr, front):
    """반지름(m) → 홈 높이(0..1)와 홈 영역 마스크. 앞면은 빨간 라벨 밖(4.65 cm)부터, 뒷면은 가운데 단 밖(3.0 cm)부터."""
    r_in = .0465 if front else .030
    field = (rr > r_in) & (rr < .0732)
    gaps = np.zeros_like(rr)
    for g in (.040, .049, .058, .066):
        gaps = np.maximum(gaps, np.exp(-((rr - g) / .00035) ** 2))
    dyn = .55 + .45 * tex.fbm(np.stack([rr * 900, rr * 0, rr * 0], 1), 1.0, 3, seed=3 if front else 5)   # 음량 → 홈 폭/깊이
    period = .00062
    g = (.5 - .5 * np.cos(TAU * rr / period)) * dyn
    h = np.where(field, g * (1 - gaps) - .6 * gaps, 0.0)
    return h, field, dyn

# ---------- 레코드 몸 ----------
polar_uv(body)
S = tex.Surf(body, 2048)
p = S.p; rel = p - np.array(C); rr = np.hypot(rel[:, 0], rel[:, 2]); front = rel[:, 1] < 0; th = np.arctan2(rel[:, 2], rel[:, 0])
hF, fF, dynF = groove_height(rr, True); hB, fB, dynB = groove_height(rr, False)
h = np.where(front, hF, hB); field = np.where(front, fF, fB); dyn = np.where(front, dynF, dynB)
# 런아웃(라벨 쪽 매끈한 부분)의 나선 홈 한 줄 · 바깥 리드인
lead = np.where(front, .0448, .0272)
h += np.exp(-((rr - lead - .0002 * np.sin(th)) / .00012) ** 2) * .9
# 긁힘: 원판 면 위의 짧은 호 · 직선 (3D 거리)
scr = np.zeros(len(p))
for k in range(46):
    side = rng.choice([-1, 1]); r0 = rng.uniform(.03, .078); a0 = rng.uniform(0, TAU); L = rng.uniform(.004, .02)
    if rng.random() < .55:   # 호 (턴테이블 위에서 미끄러진 자국)
        aa = np.linspace(a0, a0 + L / r0, 6); pts = [np.array([C.x + r0 * math.cos(t), C.y + side * .006, C.z + r0 * math.sin(t)]) for t in aa]
    else:
        d0 = rng.normal(size=2); d0 /= np.linalg.norm(d0); st = np.array([C.x + r0 * math.cos(a0), C.z + r0 * math.sin(a0)])
        pts = [np.array([st[0] + d0[0] * L * t, C.y + side * .006, st[1] + d0[1] * L * t]) for t in (0, .5, 1)]
    q = p.copy(); q[:, 1] = C.y + side * .006
    d, _ = tex.polyline_dist(q, pts)
    w = rng.uniform(.00004, .00011)
    scr = np.maximum(scr, np.clip(1 - d / w, 0, 1) * ((rel[:, 1] > 0) == (side > 0)) * rng.uniform(.4, 1))
smudge = np.clip(tex.fbm(p, 60, 4, seed=11) * 1.6 + .1, 0, 1) ** 2          # 지문 · 손자국
dust = (tex.vnoise(p, 2600, seed=21) > .93) * (tex.vnoise(p, 300, seed=22) > .2)
edge = np.clip((rr - .0775) / .002, 0, 1)                                   # 가장자리 비드 — 닳은 자국
wear = edge * np.clip(tex.fbm(p, 400, 3, seed=31) + .2, 0, 1)
hgt = h * .9 - scr * 1.4
base = np.full((len(p), 3), .016) + tex.fbm(p, 30, 3, seed=1)[:, None] * .004
base += dust[:, None] * .22 + wear[:, None] * .05 + scr[:, None] * .03
rough = .2 + .07 * field * (1 - dyn) + .22 * smudge * field + .35 * scr + .5 * dust + .2 * wear
body_m = tex.material('Vin_Vinyl', TD, S.img(base), S.img(rough), tex.h2n(S.img(hgt), 2.2), coat=(.5, .12), aniso=(.55, 0.0))
body.data.materials.append(body_m)

# ---------- 앞면 빨간 종이 라벨 (따로 붙인 종이 · 평면 UV) — 콘셉트: 두 눈이 빨간 라벨 위에 얹혀 있다. 뒷면은 검은 비닐 그대로 ----------
LR = .0420
def label_mesh():
    rings = []
    for k, r in enumerate(np.linspace(.0006, LR, 16)):
        rings.append([Vector((C.x + r * math.cos(TAU * j / 128), C.y - .0054 - .00006, C.z + r * math.sin(TAU * j / 128))) for j in range(128)])
    o = odd.loft('Vin_Label', rings)
    odd.warp(o, _warp)
    return o
label = label_mesh(); odd.recalc(label)
if np.mean(odd.nrm(label)[:, 1]) > 0: odd.recalc(label, inside=True)
planar_uv(label, C, LR * 1.015)
L_ = 1024; img = Image.new('RGB', (L_, L_), (150, 22, 24)); dr = ImageDraw.Draw(img); cx = cy = L_ / 2; Rl = L_ / 2 / 1.015
dr.ellipse([cx - Rl, cy - Rl, cx + Rl, cy + Rl], fill=(158, 24, 26))
dr.ellipse([cx - Rl * .985, cy - Rl * .985, cx + Rl * .985, cy + Rl * .985], outline=(96, 12, 14), width=int(L_ * .022))   # 가장자리 짙은 테
dr.ellipse([cx - Rl * .9, cy - Rl * .9, cx + Rl * .9, cy + Rl * .9], outline=(120, 16, 18), width=3)
f1 = ImageFont.truetype(FONT2, int(L_ * .06)); f3 = ImageFont.truetype(FONT, int(L_ * .026))
def ctext(t, y, f, col=(232, 205, 170)):
    w = dr.textlength(t, font=f); dr.text((cx - w / 2, y), t, font=f, fill=col)
ctext('ODD HAUS RECORDS', cy + Rl * .62, f1)                             # 눈 아래로 보이는 글자 (위쪽은 눈에 가린다)
ctext('VIN  ·  SIDE A  ·  45 RPM', cy + Rl * .76, f3, (220, 190, 150))
lab = np.asarray(img).astype(np.float64)[::-1] / 255
yy, xx = np.mgrid[0:L_, 0:L_]; rr2 = np.hypot(xx - cx, yy - cy) / Rl
P3 = np.stack([xx / L_, yy / L_, np.zeros_like(xx, float)], -1).reshape(-1, 3)
age = (tex.fbm(P3, 6, 4, seed=41).reshape(L_, L_) * .5 + .5)
lab *= (1 - .10 * age[..., None]) * np.array([1, .98, .94])
spin = np.zeros((L_, L_)); ang = np.arctan2(yy - cy, xx - cx)
for k in range(5):                                                    # 바깥 테 가까이 긁힌 자국 · 손때
    a0 = rng.uniform(-math.pi, math.pi); r0 = rng.uniform(.82, .95); da = rng.uniform(.2, .7)
    m = (np.abs((ang - a0 + math.pi) % TAU - math.pi) < da / 2) & (np.abs(rr2 - r0) < .006)
    spin = np.maximum(spin, m * rng.uniform(.3, .7))
lab *= (1 - spin[..., None] * .8)
rgh = .62 + .12 * age + .2 * spin
lh = age * .4 + np.clip(1 - np.abs(rr2 - .985) / .02, 0, 1) * .8
label_m = tex.material('Vin_Label', TD, lab, rgh, tex.h2n(lh, 1.5))
label.data.materials.append(label_m)

# ---------- 눈 · 동공 (눈알 표면을 따라 붙은 얇은 껍질 — 게임에서 리그의 pupil 노드가 움직인다) ----------
def pupil(i):
    """동공: 콘셉트처럼 눈 안쪽 · 조금 아래에 세로 타원 — 격자를 눈알 표면으로 투영해 0.2 mm 띄운 매끈한 껍질.
    (게임에 넣을 때 리그의 pupil 노드를 이 자리로 옮긴다 — 겉모습만 바뀐다)"""
    from mathutils.bvhtree import BVHTree
    e = eyes[i]; ec = eye_c[e.name]; inward = 1 if i == 0 else -1
    pc = Vector((ec.x + inward * .0066, ec.y, ec.z - .0032)); bvh = BVHTree.FromObject(e, bpy.context.evaluated_depsgraph_get())
    ax, az = .0060, .0092; nr, ns = 7, 36; verts = []; faces = []
    for k in range(nr + 1):
        f = (k / nr) ** .8
        for j in range(ns if k else 1):
            a = TAU * j / ns; x = pc.x + ax * f * math.cos(a); z = pc.z + az * f * math.sin(a)
            hit, n_, _, _ = bvh.ray_cast(Vector((x, C.y - .05, z)), Vector((0, 1, 0)))
            verts.append(hit + n_ * .0002 if hit is not None else Vector((x, C.y - .015, z)))
    for j in range(ns):
        faces.append((0, 1 + j, 1 + (j + 1) % ns))
    for k in range(1, nr):
        b0 = 1 + (k - 1) * ns; b1 = 1 + k * ns
        for j in range(ns):
            faces.append((b0 + j, b1 + j, b1 + (j + 1) % ns, b0 + (j + 1) % ns))
    o = odd.mesh_obj(f'Vin_Pupil{i}', verts, faces)
    if np.mean(odd.nrm(o)[:, 1]) > 0: odd.recalc(o, inside=True)
    planar_uv(o, pc, .0095)
    return o
pupils = [pupil(0), pupil(1)]
P_ = 256; yy, xx = np.mgrid[0:P_, 0:P_] / P_
pc_img = np.full((P_, P_, 3), .012)
for (cx_, cy_, r_) in ((.60, .72, .09), (.42, .40, .04)):               # 캐치라이트 (작게 — 유광 반사는 재질이 만든다)
    pc_img = np.maximum(pc_img, (np.hypot(xx - cx_, (yy - cy_) * 1.15) < r_)[..., None] * .95)
pr = np.full((P_, P_), .06)
pupil_m = tex.material('Vin_Pupil', TD, pc_img, pr, None, coat=(1, .03))
for o in pupils: o.data.materials.append(pupil_m)
eye_m = odd.gltf_material('Vin_EyeWhite', base_value=(.93, .925, .9, 1), rough_value=.14, coat=(1, .05))
for i, o in enumerate(eyes):
    planar_uv(o, eye_c[o.name], .03)
    Se = tex.Surf(o, 512); c = np.array(eye_c[o.name])
    rim = np.clip(1 - (-Se.n[:, 1]), 0, 1) ** 2                          # 가장자리로 갈수록 살짝 그늘 (눈꺼풀 · 소켓 접촉)
    top = np.clip((Se.p[:, 2] - c[2]) / EA[1], 0, 1) ** 2
    col = np.array([.94, .93, .9]) - (rim * .1 + top * .1)[:, None] * np.array([1, 1.05, 1.1])
    if i == 0: eyeM = tex.material('Vin_Eye', TD, Se.img(col), Se.img(np.full(len(col), .12)), None, coat=(1, .04))
    o.data.materials.append(eyeM)

# ---------- 검은 비닐(눈꺼풀) · 고무(팔다리 · 그로밋) ----------
def rubber(o, name, size, col, rough, grain=.4, sheen=None):
    odd.uv_smart(o, 66, .006); Sx = tex.Surf(o, size)
    n1 = tex.fbm(Sx.p, 900, 3, seed=sum(map(ord, name)) % 97); n2 = tex.fbm(Sx.p, 120, 3, seed=5)
    c = np.array(col)[None, :] * (1 + .12 * n2[:, None]) + (n1 > .55)[:, None] * .03
    rgh = rough + .08 * n2 + .1 * np.clip(n1, 0, 1)
    hh = n1 * grain
    kw = {'sheen': sheen} if sheen else {}
    m = tex.material(name, TD, Sx.img(c), Sx.img(rgh), tex.h2n(Sx.img(hh), 1.0), **kw)
    o.data.materials.append(m); return m
limb_m = rubber(arms[0], 'Vin_Limb', 512, (.022, .022, .024), .46, .5, sheen=(.3, .5, (.25, .25, .27, 1)))
for o in arms[1:] + legs:
    odd.uv_smart(o, 66, .006); o.data.materials.append(limb_m)
grom_m = rubber(grommets[0], 'Vin_Grommet', 256, (.03, .028, .028), .55, .6)
for o in grommets[1:]:
    odd.uv_smart(o, 66, .006); o.data.materials.append(grom_m)

# ---------- 장갑: 천(결) · 손등 박음질 · 손바닥 · 손끝 때 ----------
g0, c0 = gloves[0]; w, d_, b_, t_, side_ = hand_frame(0)
Wl = lambda lx, ly, lz: np.array(w + (t_ * lx + b_ * ly + d_ * lz) * .01)
odd.uv_smart(g0, 66, .006); Sg = tex.Surf(g0, 1024)
ph = Sg.p; hh = np.zeros(len(ph))
for lx in (-.55, 0, .55):
    pts = odd.project(g0, [Wl(lx * .8, .8, .9), Wl(lx * .9, .8, 1.6), Wl(lx, .8, 2.25)])
    hh += tex.stitches(ph, [np.array(q) for q in pts], .0011, .0007, .00022)
weave = np.sin(ph @ np.array([1, 0, 0]) * 9000) * np.sin(ph @ np.array([0, .7, .7]) * 9000) * .15
pal = np.clip(-(Sg.n @ np.array(b_)), 0, 1)
tip = np.clip(((ph - np.array(w)) @ np.array(d_) - .036) / .012, 0, 1)
dirt = np.clip(tex.fbm(ph, 200, 4, seed=51) * .8 + .2, 0, 1) * (pal * .5 + tip * .7)
col = np.array([.90, .89, .86])[None, :] * (1 - .02 * tex.fbm(ph, 600, 2, seed=52)[:, None]) - dirt[:, None] * np.array([.10, .11, .13])
rgh = .72 + .1 * dirt
glove_m = tex.material('Vin_Glove', TD, Sg.img(col), Sg.img(rgh), tex.h2n(Sg.img(hh * 3 + weave), 1.4), sheen=(.35, .6, (1, 1, 1, 1)))
odd.uv_smart(c0, 66, .006); Sc = tex.Surf(c0, 512)
cuff_col = np.array([.90, .89, .86])[None, :] * (1 - .03 * tex.fbm(Sc.p, 300, 3, seed=53)[:, None])
cuff_m = tex.material('Vin_Cuff', TD, Sc.img(cuff_col), Sc.img(np.full(len(cuff_col), .7)), tex.h2n(Sc.img(np.sin(Sc.p @ np.array([1, 1, 0]) * 9000) * .12), 1.2), sheen=(.35, .6, (1, 1, 1, 1)))
for g_, c_ in gloves:
    g_.data.materials.append(glove_m); c_.data.materials.append(cuff_m)

# ---------- 신발 ----------
sh = shoes0; o0 = np.array(RP('shoe0'))
def sl(p):                                   # 신발 로컬(cm): x 바깥(+) · y 앞 · z 위  (place0: (-x, -y, z))
    q = (p - o0) / .01; return np.stack([-q[:, 0], -q[:, 1], q[:, 2]], 1)
def tex_upper():
    o = sh['upper']; odd.uv_smart(o, 60, .005); Su = tex.Surf(o, 1024); q = sl(Su.p)
    hh = np.zeros(len(q))
    # 박음질: 칼라 아래 두 줄 · 끈 자리 옆 두 줄 · vamp/quarter 이음선 · backstay 양쪽
    cn = np.array([0, .35, 1]) / np.linalg.norm([0, .35, 1]); cd = (q - np.array([0, -.9, 4.5])) @ cn
    for off in (.22, .32):
        hh += np.clip(1 - np.abs(cd + off) / .035, 0, 1) * (np.sin((q[:, 0] * 3 + q[:, 1] * 3) * 7) > -.2)
    for sx in (-1, 1):
        for off in (.1, .19):
            hh += np.clip(1 - np.abs(np.abs(q[:, 0]) - (.36 + off)) / .03, 0, 1) * ((q[:, 0] * sx) > 0) * (q[:, 2] > 2.2) * (np.sin(q[:, 2] * 40) > -.2)
    for sx in (-1, 1):
        seam = [np.array([sx * .5, 1.8, 2.9]), np.array([sx * 1.25, 1.35, 2.0]), np.array([sx * 1.45, .95, 1.25])]
        d, s_ = tex.polyline_dist(q, seam)
        hh += -np.exp(-(d / .03) ** 2) * .8 + np.clip(1 - np.abs(d - .09) / .03, 0, 1) * (np.sin(s_ * 40) > -.2)
        hh += np.clip(1 - np.abs(np.abs(q[:, 0]) - .38) / .03, 0, 1) * (q[:, 1] < -2.0) * (np.sin(q[:, 2] * 40) > -.2)
    weave = (np.sin(q[:, 0] * 260 + q[:, 2] * 12) + np.sin(q[:, 1] * 260 + q[:, 2] * 260)) * .07
    near_sole = np.clip((1.9 - q[:, 2]) / 1.0, 0, 1); toe = np.clip((q[:, 1] - 2.2) / 1.5, 0, 1)
    grime = np.clip(tex.fbm(Su.p, 160, 4, seed=61) * .9 + .3, 0, 1) * (near_sole * .7 + toe * .3)
    fade = np.clip(tex.fbm(Su.p, 40, 3, seed=62) * .5 + .5, 0, 1)
    col = np.array([.62, .055, .05])[None, :] * (.88 + .2 * fade[:, None]) * (1 - grime[:, None] * .35) + grime[:, None] * np.array([.05, .035, .025])
    crease_dark = np.clip(-tex.fbm(Su.p, 90, 2, seed=63), 0, 1) * toe
    col *= (1 - crease_dark[:, None] * .3)
    rgh = .86 + .06 * grime
    m = tex.material('Vin_ShoeCanvas', TD, Su.img(col), Su.img(rgh), tex.h2n(Su.img(hh * .9 + weave), 1.6), sheen=(.4, .5, (1, .7, .7, 1)))
    return m
def tex_sole():
    o = sh['sole']; odd.uv_smart(o, 60, .005); Ss = tex.Surf(o, 1024); q = sl(Ss.p); n = Ss.n
    down = np.clip(-n[:, 2], 0, 1)
    col = np.tile(np.array([.86, .84, .78]), (len(q), 1))
    stripe = (np.abs(q[:, 2] - .38) < .05) * (down < .5)
    col = np.where(stripe[:, None], np.array([.62, .07, .06]), col)
    heel = (q[:, 1] < -2.1) & (np.abs(q[:, 0]) < .55) & (q[:, 2] > .52) & (q[:, 2] < .86)
    col = np.where(heel[:, None], np.array([.15, .14, .16]), col)
    grime = np.clip(tex.fbm(Ss.p, 220, 4, seed=71) * .8 + .35, 0, 1) * np.clip((.45 - q[:, 2]) / .45, 0, 1)
    col = col * (1 - grime[:, None] * .45) + grime[:, None] * np.array([.06, .05, .04])
    col = np.where(down[:, None] > .5, np.array([.62, .6, .55]) * (1 - .25 * np.clip(tex.fbm(Ss.p, 150, 3, seed=72), 0, 1))[:, None], col)
    tread = (np.abs(((q[:, 0] + q[:, 1]) * 4.5) % 1 - .5) < .17) | (np.abs(((q[:, 0] - q[:, 1]) * 4.5) % 1 - .5) < .17)
    hh = tread.astype(float) * down * 1.0 - (np.abs(q[:, 2] - .38) < .05).astype(float) * .2
    rgh = .62 + .2 * grime + .1 * down
    return tex.material('Vin_ShoeRubber', TD, Ss.img(col), Ss.img(rgh), tex.h2n(Ss.img(hh), 1.6))
def tex_toecap():
    o = sh['toecap']; odd.uv_smart(o, 60, .005); St = tex.Surf(o, 512); q = sl(St.p)
    dia = (np.abs(((q[:, 0] + q[:, 2]) * 3.2) % 1 - .5) < .08) | (np.abs(((q[:, 0] - q[:, 2]) * 3.2) % 1 - .5) < .08)
    grime = np.clip(tex.fbm(St.p, 220, 4, seed=81) * .8 + .2, 0, 1) * .5
    col = np.array([.87, .85, .8])[None, :] * (1 - grime[:, None] * .3) + grime[:, None] * np.array([.03, .025, .02])
    return tex.material('Vin_ToeCap', TD, St.img(col), St.img(.55 + .15 * grime), tex.h2n(St.img(-dia.astype(float) * .6), 1.4))
def tex_tongue():
    o = sh['tongue']; odd.uv_smart(o, 60, .005); Sn = tex.Surf(o, 512); q = sl(Sn.p)
    patch = (np.abs(q[:, 0]) < .42) & (q[:, 2] > 4.35) & (Sn.n @ np.array(F_fwd) > .2)
    col = np.where(patch[:, None], np.array([.92, .9, .84]), np.array([.6, .055, .05]))
    weave = (np.sin(q[:, 0] * 260) + np.sin(q[:, 2] * 260)) * .07
    return tex.material('Vin_Tongue', TD, Sn.img(col), Sn.img(np.where(patch, .7, .86)), tex.h2n(Sn.img(weave + patch.astype(float) * .3), 1.4))
F_fwd = (place0(Vector((0, 1, 0))) - place0(Vector((0, 0, 0)))).normalized()
shoe_m = {'upper': tex_upper(), 'sole': tex_sole(), 'toecap': tex_toecap(), 'tongue': tex_tongue(),
          'laces': odd.gltf_material('Vin_Laces', base_value=(.86, .85, .8, 1), rough_value=.92, sheen=(.4, .5, (1, 1, 1, 1))),
          'eyelets': odd.gltf_material('Vin_Eyelets', base_value=(.78, .78, .8, 1), rough_value=.32, metal_value=1.0)}
for k, o in shoes0.items(): o.data.materials.append(shoe_m[k])
for k, o in shoes1.items():
    if k in ('upper', 'sole', 'toecap', 'tongue'):
        o.data.uv_layers.clear() if False else None
    o.data.materials.append(shoe_m[k])

# ---------- 오른쪽 신발 · 장갑 UV: 거울 복제 시 UV는 복사 전 상태 → 복사본을 다시 만든다 ----------
for k in list(shoes1):
    odd.delete(shoes1[k]); shoes1[k] = odd.mirror_copy(shoes0[k], shoes0[k].name.replace('Shoe0', 'Shoe1'))
g1, c1 = gloves[1]; odd.delete(g1); odd.delete(c1)
g1 = odd.mirror_copy(g0, 'Vin_Glove1'); c1 = odd.mirror_copy(c0, 'Vin_Cuff1')
for o in (g1, c1): odd.set_co(o, odd.co(o) + np.array(_dh))
gloves[1] = (g1, c1)

print('MATERIALS DONE')

# =====================================================================================
# 7. 내보내기 (리뷰 후보 — 게임에 넣지 않는다) · 확인 렌더
# =====================================================================================
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.data.materials:
        print('NO MATERIAL', o.name)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in meshes)
GLB = os.path.join(odd.OUT, 'review', 'chr_vin_review.glb')
size = odd.export_glb(GLB, meshes, tangents=True)
print('GLB', GLB, size, 'bytes', 'tris', tris, 'objects', len(meshes))
if os.environ.get('VIN_RENDER', '1') == '1':
    for mode in ('studio', 'game'):
        for ob in [o for o in bpy.data.objects if o.type in ('LIGHT',) or o.name in ('floor',)]:
            bpy.data.objects.remove(ob, do_unlink=True)
        odd.lookdev_scene(mode, size=.3)
        print(odd.render_views(os.path.join(odd.OUT, f'vin_{mode}'), C - Vector((0, 0, .055)), .27, views=('front', 'side', 'back', 'q34'), samples=64))
    print(odd.render_views(os.path.join(odd.OUT, 'vin_close'), C, .12, views=('front', 'q34', 'back'), samples=64))
