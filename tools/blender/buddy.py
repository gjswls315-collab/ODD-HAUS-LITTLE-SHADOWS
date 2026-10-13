"""Buddy 리뷰 후보 (PROTOTYPE — 승인 전) — 처음부터 다시 만든 shaggy dog.
  몸: SDF 조형(통통한 몸통 · 가슴 · 굵은 목 · 큰 둥근 머리 · 짧은 주둥이 · 볼 · 네 다리 · 발 · 꼬리 · 눈구멍)
      → 쿼드 리토폴로지 → 털 다발(셀 노이즈 · 아래로 처짐)로 표면을 직접 부스스하게 → 실루엣 자체가 shaggy
  털 카드: 눈썹 · 수염 · 귀 끝 · 가슴 · 꼬리 · 발목에만 겹친다 (알파 마스크 띠)
  눈: 유리 같은 갈색 홍채 · 깊은 동공 · 젖은 반사 / 코: 부드러운 검정 가죽(콧구멍 · 인중) / 귀: 두께 있는 처진 귀(위에서 한 번 접힘)
  목걸이 · 천 넥타이(천 시뮬레이션으로 가슴 위에 떨어짐) · BUDDY 이름표.
게임 리그(rigs.json, 미터)의 관절 위치에 맞춘다: 어깨 높이 약 33 cm.
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import odd, tex
from odd import G

STAGE = os.environ.get('BUDDY_STAGE', 'all')
RIG = json.load(open(os.environ.get('ODD_RIGS', os.path.join(odd.OUT, 'rigs.json'))))['buddy']
RP = lambda k: G(*RIG[k]['p'])                 # 미터
cmv = lambda x, y, z: G(x, y, z, .01)           # 게임 cm → Blender
TAU = math.tau
sc = odd.reset()
TD = os.path.join(odd.OUT, 'buddy_tex'); os.makedirs(TD, exist_ok=True)
rng = np.random.default_rng(11)


def to_game_cm(p):
    """Blender 좌표(m) → 게임 cm (x, y 위, z 앞)."""
    return np.stack([p[:, 0] / .01, p[:, 2] / .01, -p[:, 1] / .01], 1)


# =====================================================================================
# 1. 몸 SDF (게임 좌표 cm로 설계)
# =====================================================================================
J = {k: np.array(RIG[k]['p']) * 100 for k in RIG}          # 관절 (cm)
EYE_R = 2.6
def body_sdf(q):
    S, E, C = odd.sd_round_cone, odd.sd_ellipsoid, odd.sd_chain
    sm, mn = odd.smin, np.minimum
    torso = E(q, (0, 20.0, -2.0), (9.2, 9.6, 14.6))
    chest = E(q, (0, 21.0, 7.0), (9.4, 10.4, 7.8))
    d = sm(torso, chest, 4.0)
    rump = E(q, (0, 19.0, -12.0), (9.0, 8.4, 7.0)); d = sm(d, rump, 3.0)
    neck = S(q, (0, 24, 8), (0, 33.5, 8.5), 7.6, 7.0); d = sm(d, neck, 4.0)
    head = E(q, (0, 44.6, 8.0), (10.8, 10.2, 9.8))
    brow = E(q, (0, 47.0, 12.5), (8.6, 4.2, 4.6)); head = sm(head, brow, 3.0)
    muzzle = E(q, (0, 38.4, 16.0), (6.0, 4.8, 4.9))
    cheeks = mn(E(q, (-5.4, 38.2, 12.8), (4.4, 4.2, 3.9)), E(q, (5.4, 38.2, 12.8), (4.4, 4.2, 3.9)))
    head = sm(head, sm(muzzle, cheeks, 2.0), 3.2)
    d = sm(d, head, 4.5)
    # 앞다리 (어깨 → 팔꿈치 → 손목 → 발)
    for sx in (-1, 1):
        fl = C(q, [(sx * 5.4, 21, 8.5), (sx * 6.0, 12.5, 11.8), (sx * 6.0, 4.6, 13.6)], [4.8, 3.7, 3.3], 1.5)
        paw = E(q, (sx * 6.0, 1.9, 14.9), (3.2, 2.0, 3.7))
        d = sm(d, sm(fl, paw, 1.5), 2.5)
        # 뒷다리: 굵은 넓적다리(엉덩이) → 무릎 → 뒤꿈치 → 발
        hl = C(q, [(sx * 6.2, 15.0, -9.0), (sx * 6.4, 7.0, -12.8), (sx * 6.4, 3.4, -10.6)], [6.0, 3.6, 3.1], 1.6)
        hpaw = E(q, (sx * 6.4, 1.8, -7.9), (3.2, 2.0, 3.7))
        d = sm(d, sm(hl, hpaw, 1.4), 3.0)
    tail = C(q, [tuple(J['tail0']), tuple(J['tail1']), tuple(J['tail2']), tuple(J['tail3'])], [2.8, 2.6, 2.3, 1.9], 1.0)
    d = sm(d, tail, 2.0)
    # 눈구멍 (눈알이 들어갈 자리)
    for k in ('eye0', 'eye1'):
        e = J[k] + np.array([0, 0, -.6])
        d = odd.smax(d, -(np.linalg.norm(q - e, axis=1) - (EYE_R + .25)), .8)
    return d

def sdf_m(p):
    return body_sdf(to_game_cm(p)) * .01

lo = np.array(cmv(-20, -2, -36)); hi = np.array(cmv(20, 60, 26))
lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
dense = odd.sdf_mesh('_buddy_dense', sdf_m, lo, hi, .003)
odd.smooth(dense, 2, .4)
body = odd.retopo(dense, 9000, 1, 'Buddy_Body')
odd.delete(dense)


# =====================================================================================
# 2. 털 다발: 셀(보로노이) 다발마다 볼록 + 아래로 처짐 → 실루엣 자체를 부스스하게
# =====================================================================================
def cells(P, scale, stretch=(1, .45, 1), seed=0):
    """3D 셀 노이즈: 가장 가까운 점까지 거리(F1)와 두 번째(F2) — 다발 하나 = 셀 하나."""
    q = P * scale / np.array(stretch); i0 = np.floor(q).astype(np.int64)
    f1 = np.full(len(q), 9.0); f2 = np.full(len(q), 9.0); cid = np.zeros(len(q), np.int64); cc = np.zeros_like(q)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = i0 + np.array([dx, dy, dz])
                h = (c[:, 0] * 73856093 ^ c[:, 1] * 19349663 ^ c[:, 2] * 83492791 ^ seed * 2654435761) & 0xFFFFFF
                jit = np.stack([(h & 255) / 255., ((h >> 8) & 255) / 255., ((h >> 16) & 255) / 255.], 1)
                d = np.linalg.norm(q - (c + jit), axis=1)
                m1 = d < f1; f2 = np.where(m1, f1, np.minimum(f2, d)); cid = np.where(m1, h, cid); f1 = np.where(m1, d, f1)
                cc = np.where(m1[:, None], c + jit, cc)
    return f1, f2, cid, q - cc

def fur_amp(g):
    """부위별 털 길이(cm): 몸 · 가슴 · 다리 길게, 얼굴 · 발 짧게, 눈 · 코 둘레 0."""
    x, y, z = g[:, 0], g[:, 1], g[:, 2]
    a = np.full(len(g), 1.1)
    a += .6 * np.exp(-(((y - 24) / 5) ** 2 + ((z - 12) / 5) ** 2))                    # 가슴 털
    a += .35 * np.clip((22 - y) / 10, 0, 1)                                          # 배 · 다리 아래로 갈수록
    head = np.clip((y - 33) / 4, 0, 1)
    a = a * (1 - head) + head * .75
    for k in ('eye0', 'eye1'):
        a *= 1 - .95 * np.exp(-np.sum((g - J[k]) ** 2, 1) / (3.4 ** 2))
    a *= 1 - .9 * np.exp(-np.sum((g - np.array([0, 40.5, 20.6])) ** 2, 1) / (3.0 ** 2))   # 코
    beard = np.exp(-(((y - 35.5) / 3.2) ** 2 + (x / 6.5) ** 2 + ((z - 15.5) / 4.5) ** 2))
    a += 1.3 * beard                                                                   # 턱수염 · 주둥이 털
    a *= 1 - .6 * np.clip((3.0 - y) / 2.5, 0, 1)                                      # 발바닥
    return a

def flow_field(g, n_g):
    """털이 흐르는 방향 (게임 좌표, 표면 접선): 몸 · 다리는 아래(등은 뒤로), 머리는 코에서 바깥 · 아래로, 꼬리는 바깥으로."""
    x, y, z = g[:, 0], g[:, 1], g[:, 2]
    f = np.tile(np.array([0, -1.0, 0]), (len(g), 1))
    top = np.clip((n_g[:, 1] - .3) / .5, 0, 1)                     # 등 · 정수리: 뒤로 눕는다
    f += np.outer(top, [0, 0, -1.4])
    head = np.clip((y - 33) / 4, 0, 1)[:, None]
    face = g - np.array([0, 41, 22]); face /= np.maximum(np.linalg.norm(face, axis=1, keepdims=True), 1e-6)
    f = f * (1 - head) + head * (face * 1.0 + np.array([0, -.9, -.2]))
    tl = np.clip(-(z + 17) / 3, 0, 1)[:, None] * np.clip((y - 15) / 3, 0, 1)[:, None]
    tdir = g - np.array([0, 18, -19]); tdir /= np.maximum(np.linalg.norm(tdir, axis=1, keepdims=True), 1e-6)
    f = f * (1 - tl) + tl * tdir
    f -= n_g * np.sum(f * n_g, 1, keepdims=True)
    return f / np.maximum(np.linalg.norm(f, axis=1, keepdims=True), 1e-6)


def shag(o, seed=0, k_amp=1.0):
    """겹 다발(shingle): 흐름 방향으로 긴 다발 — 뿌리 쪽은 얇고 끝으로 갈수록 두꺼워졌다가 끝에서 떨어진다 → 다발 끝이 아래로 겹쳐 층이 생긴다.
    옆 · 아래를 보는 다발 끝은 처져 실루엣이 들쭉날쭉해진다."""
    a = odd.co(o); n = odd.nrm(o); g = to_game_cm(a)
    n_g = np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1)
    amp = fur_amp(g) * k_amp
    f = flow_field(g, n_g); c = np.cross(n_g, f)
    warp_ = tex.fbm(g * .12, 1.0, 3, seed=seed) * 1.6
    across = np.sum(g * c, 1) / 1.9 + warp_                       # 다발 폭 1.9 cm
    lid = np.floor(across); fr = across - lid
    hsh = ((lid.astype(np.int64) * 2654435761 + seed * 97) & 0xFFFF) / 65535.
    prof_c = np.clip(1 - np.abs(fr - .5) * 2, 0, 1) ** .7          # 다발 가로 단면 (가운데 볼록)
    along = np.sum(g * f, 1) / (4.2 + 1.5 * hsh) + hsh * 3.7 + tex.fbm(g * .2, 1.0, 2, seed=seed + 3) * .5
    ph = along - np.floor(along)                                   # 0 뿌리 → 1 끝
    saw = np.clip(ph, 0, 1) ** .85 * np.clip((1 - ph) / .12, 0, 1)  # 끝으로 갈수록 두껍고 끝에서 떨어짐
    h = amp * (.3 + .7 * saw * (.55 + .45 * prof_c)) * (.75 + .25 * hsh)
    down = np.array(cmv(0, -1, 0)) / .01
    up_ = n_g[:, 1]
    side = np.clip(1 - np.abs(up_), 0, 1); belly = np.clip(-up_, 0, 1)
    droop = amp * saw ** 2 * prof_c * (.6 * side + .7 * belly)      # 처진 다발 끝
    disp = n * (h * .01)[:, None] + down * (droop * .01)[:, None]
    odd.set_co(o, a + disp)
    return f

FLOW = shag(body, 1)
odd.smooth(body, 1, .2)

# =====================================================================================
# 3. 눈 · 눈꺼풀 테 · 코
# =====================================================================================
def eyeball(name, c, r):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        v.co = v.co.normalized() * r
        if v.co.y < 0: v.co.y *= 1.05                      # 각막 쪽 살짝 볼록
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); odd.link(o); me.shade_smooth()
    odd.set_co(o, odd.co(o) + np.array(c)); odd.subsurf(o, 1)
    return o
eyes = []; eye_c = []
for k in ('eye0', 'eye1'):
    c = cmv(*(J[k] + np.array([0, 0, -.6]))); eye_c.append(c)
    eyes.append(eyeball('Buddy_Eye' + k[-1], c, EYE_R * .01))

def eye_rim(name, c, r):
    """눈 둘레 검은 피부 테 (눈꺼풀 가장자리)."""
    out = (c - cmv(0, 44, 2)).normalized(); out = (out + Vector((0, -1, 0)) * 1.4).normalized()
    u = out.orthogonal().normalized(); v = out.cross(u)
    prof = [(1.00, -.15), (1.06, .05), (1.12, .18), (1.18, .2), (1.24, .1), (1.26, -.1)]
    rings = [[c + out * (r * z) + (u * math.cos(TAU * j / 40) + v * math.sin(TAU * j / 40)) * (r * rr) for j in range(40)] for rr, z in prof]
    o = odd.loft(name, rings); odd.solidify(o, .0012, offset=-1); odd.subsurf(o, 1)
    return o
rims = [eye_rim('Buddy_EyeRim' + str(i), eye_c[i], EYE_R * .01) for i in range(2)]

def nose_sdf(q):
    """개 코: 위가 넓고 아래가 좁은 둥근 삼각형 — 윗면은 주둥이로 이어지고, 콧구멍은 앞 옆에 쉼표 모양, 가운데 인중 홈."""
    c = np.array([0, 40.5, 20.6])
    q = q.copy(); taper = 1 + .45 * np.clip((c[1] - q[:, 1]) / 1.6, 0, 1); q[:, 0] = q[:, 0] * taper
    d = odd.sd_ellipsoid(q, c, (2.05, 1.35, 1.3))
    d = odd.smin(d, odd.sd_ellipsoid(q, c + np.array([0, .7, -1.1]), (2.0, .95, 1.5)), .7)      # 윗면 → 주둥이
    for sx in (-1, 1):
        nos = c + np.array([sx * .95, -.25, 1.05])
        d = odd.smax(d, -odd.sd_round_cone(q, nos + np.array([-sx * .15, .1, .2]), nos + np.array([sx * .45, -.15, -.1]), .34, .2), .2)
    d = odd.smax(d, -odd.sd_round_cone(q, c + np.array([0, -.35, 1.3]), c + np.array([0, -1.4, .8]), .13, .1), .18)   # 인중
    return d
nd = odd.sdf_mesh('_nose', lambda p: nose_sdf(to_game_cm(p)) * .01, np.minimum(cmv(-3.5, 37, 18), cmv(3.5, 43.5, 23.5)), np.maximum(cmv(-3.5, 37, 18), cmv(3.5, 43.5, 23.5)), .0007)
odd.smooth(nd, 2, .4)
nose = odd.retopo(nd, 700, 1, 'Buddy_Nose'); odd.delete(nd)

# =====================================================================================
# 4. 귀: 두께 1.4 cm 처진 귀 — 머리 옆에서 나와 한 번 접혀 아래로 (SDF 사슬)
# =====================================================================================
def ear(i):
    sx = -1 if i == 0 else 1; e0 = J[f'ear{i}']
    path = [e0 + np.array([-sx * 3.0, 2.2, 0]), e0 + np.array([-sx * .6, 3.6, .3]), e0 + np.array([sx * .8, 2.0, .8]),
            e0 + np.array([sx * .9, -3.5, 1.4]), e0 + np.array([sx * .4, -9.0, 1.8]), e0 + np.array([-sx * .3, -13.0, 1.6])]
    wid = [3.0, 3.6, 4.0, 4.7, 5.2, 4.6]
    def fn(p):
        q = to_game_cm(p); d = None
        for a, b, wa, wb in zip(path[:-1], path[1:], wid[:-1], wid[1:]):
            ax = b - a; L = np.linalg.norm(ax); ax /= L
            nrm_ = np.array([sx, 0, 0.0]); nrm_ = nrm_ - ax * (nrm_ @ ax); nrm_ /= np.linalg.norm(nrm_)
            sd = np.cross(ax, nrm_)
            R = np.column_stack([sd, nrm_, ax])
            seg = odd.sd_ellipsoid(q, (a + b) / 2, (max(wa, wb), 1.0 + .25 * (wb > 4.5), L / 2 + 1.2), R)
            d = seg if d is None else odd.smin(d, seg, 1.2)
        return d * .01
    pts = np.array([cmv(*p) for p in path]); lo_ = pts.min(0) - .06; hi_ = pts.max(0) + .06
    dd = odd.sdf_mesh(f'_ear{i}', fn, lo_, hi_, .0012); odd.smooth(dd, 2, .4)
    o = odd.retopo(dd, 900, 1, f'Buddy_Ear{i}'); odd.delete(dd)
    return o
ears = [ear(0), ear(1)]
for i, o in enumerate(ears):
    shag(o, 5 + i, .75)

if STAGE == 'clay':
    odd.lookdev_scene('studio', size=1.0)
    m = odd.Mat('clay'); m.set(Base_Color=(.6, .52, .42, 1), Roughness=.8)
    dk = odd.Mat('dk'); dk.set(Base_Color=(.03, .025, .02, 1), Roughness=.4)
    wt = odd.Mat('wt'); wt.set(Base_Color=(.35, .2, .1, 1), Roughness=.1)
    for o in [body] + ears: o.data.materials.append(m.m)
    for o in [nose] + rims: o.data.materials.append(dk.m)
    for o in eyes: o.data.materials.append(wt.m)
    tgt = cmv(0, 28, -2)
    print(odd.render_views(os.path.join(odd.OUT, 'buddy_clay'), tgt, .62, views=('front', 'side', 'back', 'q34')))
    print(odd.render_views(os.path.join(odd.OUT, 'buddy_face'), cmv(0, 42, 12), .28, views=('front', 'q34', 'side')))
    sys.exit(0)

# 오른쪽 귀 = 왼쪽 귀의 거울 (같은 UV · 텍스처) — 리그 비대칭만큼 옮긴다
odd.delete(ears[1])
ears[1] = odd.mirror_copy(ears[0], 'Buddy_Ear1')
_de = RP('ear1') - Vector((-RP('ear0').x, RP('ear0').y, RP('ear0').z)); odd.set_co(ears[1], odd.co(ears[1]) + np.array(_de))

# =====================================================================================
# 5. 털 색 (부위 · 다발 · 결) — 몸 텍스처와 털 카드 색이 같은 함수를 쓴다
# =====================================================================================
CREAM = np.array([.84, .76, .62]); TAUPE = np.array([.46, .40, .35]); BROWN = np.array([.36, .25, .17]); BLAZE = np.array([.92, .88, .8])
def fur_color(g, n_g=None):
    x, y, z = g[:, 0], g[:, 1], g[:, 2]
    top = np.clip((y - 15) / 6, 0, 1) * np.clip(1 - np.abs(x) / 12, 0, 1) * np.clip((-z + 12) / 6, 0, 1)   # 등 · 엉덩이 · 옆구리 위
    col = CREAM[None, :] * (1 - top[:, None]) + TAUPE[None, :] * top[:, None]
    head = np.clip((y - 39) / 3, 0, 1) * np.clip((15 - z) / 4, 0, 1)                                    # 정수리 · 뒤통수
    col = col * (1 - head[:, None]) + (TAUPE * 1.05)[None, :] * head[:, None]
    blaze = np.exp(-((x / 1.6) ** 2 + ((z - 15) / 4) ** 2)) * np.clip((y - 43) / 2, 0, 1)               # 이마 흰 줄
    col = col * (1 - blaze[:, None]) + BLAZE[None, :] * blaze[:, None]
    for k in ('eye0', 'eye1'):                                                                          # 눈가 얼룩
        e = np.exp(-np.sum((g - (J[k] + np.array([0, .8, -1.5]))) ** 2, 1) / 9.0)
        col = col * (1 - .55 * e[:, None]) + BROWN[None, :] * (.55 * e[:, None])
    tl = np.clip(-(z + 19) / 2, 0, 1)
    col = col * (1 - tl[:, None]) + (TAUPE * .95)[None, :] * tl[:, None]
    tiptail = np.clip((y - 24) / 3, 0, 1) * tl
    col = col * (1 - tiptail[:, None]) + CREAM[None, :] * tiptail[:, None]
    return col

# =====================================================================================
# 6. 털 카드 (필요한 곳만): 배 · 가슴 · 턱수염 · 눈썹 · 귀 끝 · 꼬리 · 발목 · 정수리
# =====================================================================================
def card_texture(path, seed):
    """털 띠 알파 텍스처: 가는 가닥 30여 개 (뿌리 어둡게 · 끝 가늘게)."""
    from PIL import Image
    r_ = np.random.default_rng(seed); W_, H_ = 256, 1024
    v = np.linspace(0, 1, H_)[:, None]; u = np.linspace(0, 1, W_)[None, :]
    A = np.zeros((H_, W_)); Cc = np.zeros((H_, W_))
    for k in range(38):
        x0 = r_.uniform(.08, .92); w = r_.uniform(.012, .03); L = r_.uniform(.55, 1.0); v0 = r_.uniform(0, .12)
        wave = .03 * np.sin(v * r_.uniform(4, 9) + r_.uniform(0, 6)) + (x0 - .5) * v * r_.uniform(-.15, .35)
        taper = np.clip(1 - (v - v0) / (L - v0 + 1e-6), 0, 1) ** .6 * (v > v0)
        prof = np.clip(1 - np.abs(u - x0 - wave) / (w * (.35 + .65 * taper) + 1e-6), 0, 1)
        a = prof ** .8 * np.clip(taper * 3, 0, 1)
        shade = r_.uniform(.78, 1.0) * (.72 + .28 * np.clip(v / .35, 0, 1))
        upd = a > A; Cc = np.where(upd, shade, Cc); A = np.maximum(A, a)
    rgba = np.stack([Cc, Cc * .99, Cc * .97, np.clip(A * 1.3, 0, 1)], -1)
    Image.fromarray((rgba[::-1] * 255).astype(np.uint8), 'RGBA').save(path)
    return path

ctex = tex.load(card_texture(os.path.join(TD, 'Buddy_Card_c.png'), 3))
card_m = odd.gltf_material('Buddy_FurCard', base=ctex, rough_value=.68, alpha_tex='base', alpha_mode='MASK', double=True, sheen=(.6, .5, (1, .95, .85, 1)))
card_m.alpha_threshold = .45 if hasattr(card_m, 'alpha_threshold') else None

cards = []
def add_card(P, N, F, L, w0, w1, droop=.25, lift=.004, twist=0.0, col=(1, 1, 1)):
    P = Vector(P); N = Vector(N).normalized(); F = Vector(F); F = (F - N * F.dot(N)).normalized()
    down = Vector((0, 0, -1)); pts = []; ws = []
    for k in range(6):
        t = k / 5
        pts.append(P - N * .002 + F * (L * t) + N * (lift * math.sin(math.pi * t * .8)) + down * (L * droop * t * t))
        ws.append(w0 + (w1 - w0) * t)
    o = odd.ribbon('_card', pts, ws, normal_hint=N, twist=[twist * t / 5 for t in range(6)])
    ca = o.data.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    for i in range(len(o.data.vertices)):
        tt = (i // 2) / 5; shade = .62 + .38 * tt                                                   # 뿌리는 몸 털 속 그늘처럼 어둡게
        lin = [((c_ + .055) / 1.055) ** 2.4 if c_ > .04045 else c_ / 12.92 for c_ in col]            # 정점 색은 선형 값 (몸 텍스처는 sRGB)
        ca.data[i].color = (lin[0] * shade, lin[1] * shade, lin[2] * shade, 1)
    cards.append(o)

def sample(o, mask_fn, count, seed):
    a = odd.co(o); n = odd.nrm(o); g = to_game_cm(a); n_g = np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1)
    idx = np.nonzero(mask_fn(g, n_g))[0]
    r_ = np.random.default_rng(seed)
    pick = r_.choice(idx, size=min(count, len(idx)), replace=False) if len(idx) else []
    return [(a[i], n[i], g[i], n_g[i]) for i in pick]

def gdir(v):                     # 게임 방향 → Blender
    return Vector((v[0], -v[2], v[1]))

flow_all = None
def flow_at(g, n_g):
    return flow_field(g[None, :], n_g[None, :])[0]

def ear_color(g):
    up = np.clip((g[:, 1] - 38) / 4, 0, 1)[:, None]
    return BROWN[None, :] * 1.05 * (1 - up) + (TAUPE * .9)[None, :] * up
def put(o, mask_fn, count, seed, L, w, droop=.3, rot=0.0, flow_bias=(0, 0, 0), colfn=None):
    r_ = np.random.default_rng(seed + 100)
    for P, N, g, n_g in sample(o, mask_fn, count, seed):
        f = flow_at(g, n_g) + np.array(flow_bias); col = (colfn or fur_color)(g[None, :])[0] * r_.uniform(.9, 1.05)   # 몸 텍스처와 같은 색 (카드 텍스처 명암이 결 그늘 역할)
        Lk = r_.uniform(*L) * .01
        add_card(P, N, gdir(f), Lk, w * r_.uniform(.8, 1.2) * .01, w * .35 * .01, droop=droop, twist=r_.uniform(-rot, rot), col=np.clip(col, 0, 1))

# 배 · 옆구리 아래 술 (실루엣을 깨는 늘어진 털)
put(body, lambda g, n: (g[:, 1] > 9) & (g[:, 1] < 16) & (np.abs(g[:, 2]) < 13) & (n[:, 1] < .2), 70, 1, (3.5, 5.5), 2.6, .45, .5)
put(body, lambda g, n: (g[:, 1] > 19) & (g[:, 1] < 31) & (g[:, 2] > 9) & (n[:, 2] > .3), 34, 2, (4.0, 6.0), 2.8, .35, .4)          # 가슴
put(body, lambda g, n: (g[:, 1] > 32) & (g[:, 1] < 39) & (g[:, 2] > 12) & (np.abs(g[:, 0]) < 8) & (n[:, 1] < .4), 28, 3, (2.4, 3.8), 1.8, .4, .5)   # 턱수염
for k in ('eye0', 'eye1'):                                                                                                       # 눈썹
    e = J[k]
    put(body, lambda g, n, e=e: (np.linalg.norm(g - (e + np.array([0, 3.0, -.8])), axis=1) < 2.4) & (n[:, 2] > .1), 12, 4 + int(e[0] > 0), (2.4, 3.4), 1.6, .25, .6, flow_bias=(0, .2, 1.2))
put(body, lambda g, n: (g[:, 1] < 9.5) & (g[:, 1] > 2.5) & (np.abs(g[:, 0]) > 3) & (n[:, 1] < .4), 46, 6, (2.0, 3.2), 1.8, .35, .6)   # 다리 · 발목
put(body, lambda g, n: (g[:, 2] < -18) & (g[:, 1] > 16), 26, 7, (3.5, 5.0), 2.4, .15, .8)                                        # 꼬리
put(body, lambda g, n: (g[:, 1] > 51) & (n[:, 1] > .5), 12, 8, (3.0, 4.0), 2.2, .4, .6)                                          # 정수리
for i, eo in enumerate(ears):
    put(eo, lambda g, n: g[:, 1] < (g[:, 1].min() + 6.0), 22, 20 + i, (3.0, 4.6), 2.4, .35, .6, colfn=ear_color)                   # 귀 끝 (귀 색)
    put(eo, lambda g, n: (np.abs(n[:, 0]) < .5) & (g[:, 1] < g[:, 1].max() - 3), 16, 30 + i, (2.2, 3.4), 2.0, .4, .7, colfn=ear_color)  # 귀 앞 · 뒤 가장자리
fur_cards = odd.join(cards, 'Buddy_FurCards')
fur_cards.data.materials.append(card_m)
print('cards', len(fur_cards.data.polygons))

# =====================================================================================
# 7. 목걸이 · 천 넥타이(천 시뮬레이션) · 이름표
# =====================================================================================
dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(body, dg)
cy = 31.0; ctr = cmv(0, cy, 8.8)
ring = []
for k in range(48):
    a = TAU * k / 48; dv = gdir(np.array([math.cos(a), 0, math.sin(a)]))
    hit, n_, _, d_ = bvh.ray_cast(ctr + dv * .16, -dv)
    rr = ((hit - ctr).length if hit is not None else .075) - .0035
    ring.append((dv, rr))
def collar_ring(off_h, off_r):
    return [ctr + Vector((0, 0, off_h)) + dv * (rr + off_r) for dv, rr in ring]
collar = odd.loft('Buddy_Collar', [collar_ring(-.006, -.001), collar_ring(-.0065, .0012), collar_ring(.0065, .0012), collar_ring(.006, -.001)])
odd.subsurf(collar, 1)
front = ctr + gdir(np.array([0, 0, 1])) * (ring[12][1] + .0015)       # 앞 (a = 90°)
# 넥타이 매듭
kn = odd.sdf_mesh('_knot', lambda p: (odd.sd_ellipsoid(to_game_cm(p), np.array([0, cy - .4, 0]) + np.array([0, 0, (front.y * -100)]), (1.15, 1.2, .75))) * .01,
                  np.array(front) - .02, np.array(front) + .02, .0004)
odd.smooth(kn, 2, .4); knot = odd.retopo(kn, 300, 1, 'Buddy_TieKnot'); odd.delete(kn)
# 넥타이 몸: 격자 천 → 가슴 위로 떨어뜨린다 (위 끝 고정)
cols, rows = 9, 22; Lt = .092; verts = []; faces = []
for r_i in range(rows):
    t = r_i / (rows - 1); wid = .012 + .018 * t
    for c_i in range(cols):
        u = c_i / (cols - 1) - .5; tipv = max(0.0, t - .9) / .1
        zoff = -abs(u) * .012 * tipv
        keel = -.0022 * (1 - abs(u) * 2) * (t > .05)                                   # 가운데가 앞으로 살짝 접힌 단면
        verts.append(front + gdir(np.array([0, 0, 1])) * .006 + Vector((u * wid * 2 + .002 * math.sin(t * 3.0), -.004 - t * .012 + keel - .004 * math.sin(t * math.pi), -.008 - t * Lt)) + Vector((0, 0, -abs(u) * .022 * (t > .92))))
for r_i in range(rows - 1):
    for c_i in range(cols - 1):
        a0 = r_i * cols + c_i; faces.append((a0, a0 + 1, a0 + cols + 1, a0 + cols))
tie = odd.mesh_obj('Buddy_Tie', verts, faces)
_uv = tie.data.uv_layers.new(name='UVMap')
for poly in tie.data.polygons:
    for li in poly.loop_indices:
        vi = tie.data.loops[li].vertex_index; _uv.data[li].uv = ((vi % cols) / (cols - 1), 1 - (vi // cols) / (rows - 1))
odd.vgroup(tie, 'pin', [1.0 if i < cols * 2 else 0.0 for i in range(len(verts))])
colb = bpy.data.objects.new('_colb', body.data.copy()); odd.link(colb)
odd.cloth_sim(tie, frames=50, pin_group='pin', colliders=[colb], quality=8, mass=.05, tension=20, bending=2.0, collide_dist=.0015, thickness_outer=.004)
odd.delete(colb)
odd.solidify(tie, .0012, offset=1); odd.subsurf(tie, 1)
# 이름표: 놋쇠 테 + 파란 에나멜 + 노란 BUDDY (D링에 매달림)
tc_ = front + gdir(np.array([2.6, -2.2, .4])) * .01
tag = odd.sdf_mesh('_tag', lambda p: odd.smax(np.linalg.norm((p - np.array(tc_))[:, [0, 2]], axis=1) - .0125, np.abs((p - np.array(tc_))[:, 1]) - .0009, .0006),
                   np.array(tc_) - .016, np.array(tc_) + .016, .00025)
odd.smooth(tag, 1, .3); tagm = odd.retopo(tag, 400, 1, 'Buddy_Tag'); odd.delete(tag)
dring = odd.curve_tube('Buddy_TagRing', [front + gdir(np.array([1.4, -.6, .2])) * .01, tc_ + Vector((0, 0, .0135)) + gdir(np.array([0, 0, .1])) * .01,
                                          front + gdir(np.array([2.2, -.4, .3])) * .01], .0008, res=8, bevel_res=3)

if STAGE == 'clay2':
    odd.lookdev_scene('studio', size=1.0)
    m = odd.Mat('clay'); m.set(Base_Color=(.6, .52, .42, 1), Roughness=.8)
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.data.materials]: o.data.materials.append(m.m)
    print(odd.render_views(os.path.join(odd.OUT, 'buddy_clay2'), cmv(0, 28, -2), .62, views=('front', 'side', 'q34')))
    print(odd.render_views(os.path.join(odd.OUT, 'buddy_face2'), cmv(0, 38, 14), .3, views=('front', 'q34', 'side')))
    sys.exit(0)

# =====================================================================================
# 8. 텍스처
# =====================================================================================
def strands_h(g, n_g, seed=0, width=.32, L=3.0):
    """털 결: 3 cm 격자 구역마다 그 자리의 흐름 방향으로 다발 · 가닥 줄무늬를 그리고 8개 이웃 구역을 부드럽게 섞는다
    (휘는 흐름에서도 소용돌이 무늬가 생기지 않는다). 반환: 가닥 높이 · 다발 난수 · 다발 끝 위상 · 다발 단면."""
    f = flow_field(g, n_g); c_ = np.cross(n_g, f)
    base = np.floor(g / L); fr = g / L - base; fr = fr * fr * (3 - 2 * fr)
    fine = np.zeros(len(g)); hsh = np.zeros(len(g)); ph = np.zeros(len(g)); lp = np.zeros(len(g))
    for cx in (0, 1):
        for cy_ in (0, 1):
            for cz in (0, 1):
                cr = np.array([cx, cy_, cz]); w = np.prod(np.where(cr == 1, fr, 1 - fr), 1)
                ci = (base + cr).astype(np.int64)
                hh = (ci[:, 0] * 73856093 ^ ci[:, 1] * 19349663 ^ ci[:, 2] * 83492791 ^ (seed + 1) * 2654435761) & 0xFFFFFF
                r1 = (hh & 1023) / 1023.; r2 = ((hh >> 10) & 1023) / 1023.
                rel = g - (base + cr) * L
                across = np.sum(rel * c_, 1) / 1.9 + r1 * 7.3
                lid = np.floor(across); lfr = across - lid
                lh = ((lid.astype(np.int64) * 2654435761 + hh) & 0xFFFF) / 65535.
                lpk = np.clip(1 - np.abs(lfr - .5) * 2, 0, 1) ** .6
                sk = lfr * 1.9 / width + r2 * 3.1
                fk = ((np.sin(TAU * sk) * .5 + .5) ** 1.5 - .3) * (.5 + .5 * lpk)
                along = np.sum(rel * f, 1)
                pk = (along / (4.2 + 1.5 * lh) + lh * 3.7) % 1.0
                fine += w * fk; hsh += w * lh; ph += w * pk; lp += w * lpk
    return fine, hsh, ph, lp

def soft_ph(ph):
    """다발 끝 위상: 0→1로 두꺼워지다 끝(0.8–1)에서 부드럽게 줄어든다 — 톱니처럼 뚝 떨어지면 가로 줄무늬가 생긴다."""
    t = np.clip((ph - .8) / .2, 0, 1); return ph * (1 - t * t * (3 - 2 * t))
def fur_h(p, n):
    g_ = to_game_cm(p); n_g_ = np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1)
    fine, _, ph, lp = strands_h(g_, n_g_, 3)
    return fine * .5 + soft_ph(ph) * .28 + lp * .4

odd.uv_smart(body, 60, .003)
Sb = tex.Surf(body, 2048); g = to_game_cm(Sb.p); n_g = np.stack([Sb.n[:, 0], Sb.n[:, 2], -Sb.n[:, 1]], 1)
fine, hsh, ph, lp = strands_h(g, n_g, 3)
face = np.clip((g[:, 1] - 33) / 3, 0, 1) * np.clip((g[:, 2] - 8) / 4, 0, 1)
patch = np.clip(tex.fbm(g, .085, 3, seed=8) * 1.6 + .05, 0, 1) * (1 - face) * .5                  # 큰 회갈색 얼룩 (부드럽게)
col = fur_color(g) * (1 - patch[:, None]) + (TAUPE * 1.04)[None, :] * patch[:, None]
col = col * (.9 + .2 * hsh)[:, None] * (.87 + .13 * np.clip(soft_ph(ph) * 1.4, 0, 1))[:, None] * (.95 + .07 * fine)[:, None] * (.9 + .1 * lp)[:, None]
col *= (1 + .06 * tex.fbm(g, .35, 3, seed=5))[:, None]
rgh = .64 + .08 * (1 - soft_ph(ph)) + .05 * fine
body_m = tex.material('Buddy_Fur', TD, Sb.img(np.clip(col, 0, 1)), Sb.img(rgh), tex.bump(Sb, fur_h, .0008, 1.2), sheen=(.7, .45, (1, .93, .82, 1)))
body.data.materials.append(body_m)

odd.uv_smart(ears[0], 60, .004)
Se = tex.Surf(ears[0], 1024); g = to_game_cm(Se.p); n_g = np.stack([Se.n[:, 0], Se.n[:, 2], -Se.n[:, 1]], 1)
fine, hsh, ph, lp = strands_h(g, n_g, 7)
ecol = BROWN[None, :] * (.9 + .35 * hsh)[:, None] * (.85 + .18 * np.clip(soft_ph(ph) * 1.3, 0, 1))[:, None] * (.9 + .12 * fine)[:, None]
ecol = ecol * (1 - np.clip((g[:, 1] - 38) / 4, 0, 1))[:, None] + (TAUPE * .9)[None, :] * np.clip((g[:, 1] - 38) / 4, 0, 1)[:, None]
ear_m = tex.material('Buddy_Ear', TD, Se.img(np.clip(ecol, 0, 1)), Se.img(.66 + .06 * fine), tex.bump(Se, fur_h, .0008, 1.2), sheen=(.7, .45, (1, .93, .82, 1)))
ear_tex_done = True
# 귀 1은 귀 0의 거울 복제 → UV · 재질을 함께 쓰도록 다시 복제
odd.delete(ears[1]); ears[0].data.materials.append(ear_m)
ears[1] = odd.mirror_copy(ears[0], 'Buddy_Ear1'); odd.set_co(ears[1], odd.co(ears[1]) + np.array(_de))

# 눈: 깊은 갈색 홍채(방사 무늬 · 어두운 테) · 큰 동공 · 젖은 반사
for i, (eo, c) in enumerate(zip(eyes, eye_c)):
    out = (c - cmv(0, 44, 2)).normalized(); out = (out + Vector((0, -1.6, 0))).normalized()
    u_ax = Vector((0, 0, 1)).cross(out).normalized(); v_ax = out.cross(u_ax)
    uv = eo.data.uv_layers.new(name='UVMap'); a = odd.co(eo)
    for poly in eo.data.polygons:
        for li in poly.loop_indices:
            p_ = Vector(a[eo.data.loops[li].vertex_index]) - c
            uv.data[li].uv = (.5 + p_.dot(u_ax) / (2 * EYE_R * .01), .5 + p_.dot(v_ax) / (2 * EYE_R * .01))
E_ = 512; yy, xx = (np.mgrid[0:E_, 0:E_] + .5) / E_ - .5
rr_ = np.hypot(xx, yy) / .5; an = np.arctan2(yy, xx)
iris = np.array([.30, .15, .06]) * (.75 + .35 * (np.sin(an * 38) * .5 + .5) ** 2)[..., None] * (1 - .5 * np.clip((rr_ - .55) / .25, 0, 1))[..., None]
eye_img = np.where((rr_ < .8)[..., None], iris, np.array([.12, .07, .04]))
eye_img = np.where((rr_ < .36)[..., None], np.array([.012, .01, .01]), eye_img)
for (cx_, cy_, r_) in ((.16, .18, .11), (-.12, -.1, .05)):
    eye_img = np.where((np.hypot(xx - cx_, yy - cy_) < r_)[..., None], np.array([.95, .95, .95]), eye_img)
eye_m = tex.material('Buddy_Eye', TD, eye_img, np.full((E_, E_), .05), None, coat=(1, .02))
for eo in eyes: eo.data.materials.append(eye_m)
rim_m = odd.gltf_material('Buddy_EyeRim', base_value=(.045, .03, .025, 1), rough_value=.4)
for o in rims: o.data.materials.append(rim_m)

# 코: 부드러운 검정 가죽 (자갈 무늬 · 콧구멍 안쪽 더 어둡게 · 약간 젖은 윤기)
odd.uv_smart(nose, 60, .005); Sn = tex.Surf(nose, 512); g = to_game_cm(Sn.p)
f1, f2, _, _ = cells(g, 6.0, (1, 1, 1), 2)
pebble = np.clip((f2 - f1) / .3, 0, 1)
ncol = np.array([.035, .03, .03])[None, :] * (.85 + .3 * pebble)[:, None]
nostril = np.zeros(len(g))
for sx in (-1, 1):
    nostril = np.maximum(nostril, np.exp(-np.sum((g - np.array([sx * 1.0, 40.25, 21.65])) ** 2, 1) / .15))
ncol *= (1 - .7 * nostril)[:, None]
nose_m = tex.material('Buddy_Nose', TD, Sn.img(ncol), Sn.img(.42 - .15 * pebble), tex.h2n(Sn.img(pebble), 2.0), coat=(.35, .2))
nose.data.materials.append(nose_m)

# 넥타이: 파랑 + 노란 사선 줄무늬 (천 결) · 목걸이: 파란 가죽 (박음질) · 이름표: 놋쇠 테 + 파란 에나멜 + 노란 BUDDY
from PIL import Image, ImageDraw, ImageFont
T_ = 512; yy, xx = (np.mgrid[0:T_, 0:T_] + .5) / T_
stripe = (((xx + yy * 1.6) * 7) % 1.0 < .22)
tcol = np.where(stripe[..., None], np.array([.95, .78, .16]), np.array([.10, .22, .62]))
weave = (np.sin(xx * 900) * np.sin(yy * 900)) * .5
tie_m = tex.material('Buddy_Tie', TD, tcol, np.full((T_, T_), .55) + .05 * weave, tex.h2n(weave * .3 + stripe * .2, 1.0), sheen=(.5, .35, (.8, .85, 1, 1)))
tie.data.materials.append(tie_m); odd.uv_smart(knot, 60, .01); knot.data.materials.append(tie_m)
odd.uv_smart(collar, 60, .01); Sc = tex.Surf(collar, 512); g = to_game_cm(Sc.p)
edge = np.clip(1 - np.abs(np.abs(g[:, 1] - cy) - .45) / .06, 0, 1) * (np.sin(np.arctan2(g[:, 2] - 8.8, g[:, 0]) * 160) > 0)
ccol = np.array([.12, .25, .62])[None, :] * (.85 + .2 * tex.fbm(g, 2.0, 3, seed=9)[:, None]) + edge[:, None] * .3
collar_m = tex.material('Buddy_Collar', TD, Sc.img(np.clip(ccol, 0, 1)), Sc.img(.5 - .1 * edge), tex.h2n(Sc.img(edge), 1.5))
collar.data.materials.append(collar_m)
c3 = np.array(tc_); planar = tagm.data.uv_layers.new(name='UVMap'); a = odd.co(tagm)
for poly in tagm.data.polygons:
    for li in poly.loop_indices:
        p_ = a[tagm.data.loops[li].vertex_index] - c3; planar.data[li].uv = (.5 + p_[0] / .027, .5 + p_[2] / .027)
img = Image.new('RGB', (512, 512), (190, 150, 60)); dr = ImageDraw.Draw(img)
dr.ellipse([30, 30, 482, 482], fill=(28, 66, 160)); dr.ellipse([30, 30, 482, 482], outline=(222, 182, 80), width=14)
fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 92); w_ = dr.textlength('BUDDY', font=fnt)
dr.text((256 - w_ / 2, 200), 'BUDDY', font=fnt, fill=(248, 206, 52))
tag_c = np.asarray(img).astype(float)[::-1] / 255
rim_mask = np.hypot(xx - .5, yy - .5) > .43
tag_m = tex.material('Buddy_Tag', TD, tag_c, np.where(rim_mask, .3, .2), tex.h2n(rim_mask.astype(float) * .5, 3.0), metal_value=0.0, coat=(1, .05))
tagm.data.materials.append(tag_m)
dring.data.materials.append(odd.gltf_material('Buddy_Ring', base_value=(.82, .68, .35, 1), rough_value=.3, metal_value=1.0))

# =====================================================================================
# 9. 내보내기 (리뷰 후보) · 확인 렌더
# =====================================================================================
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.data.materials:
        print('NO MATERIAL', o.name)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in meshes)
GLB = os.path.join(odd.OUT, 'review', 'npc_buddy_review.glb')
print('GLB', GLB, odd.export_glb(GLB, meshes, vcol='ACTIVE'), 'bytes', 'tris', tris, 'objects', len(meshes))
if os.environ.get('BUDDY_RENDER', '1') == '1':
    for mode in ('studio', 'game'):
        for ob in [o for o in bpy.data.objects if o.type == 'LIGHT' or o.name == 'floor']:
            bpy.data.objects.remove(ob, do_unlink=True)
        odd.lookdev_scene(mode, size=1.0)
        print(odd.render_views(os.path.join(odd.OUT, f'buddy_{mode}'), cmv(0, 28, -2), .62, views=('front', 'side', 'back', 'q34'), samples=64))
    print(odd.render_views(os.path.join(odd.OUT, 'buddy_close'), cmv(0, 38, 14), .3, views=('front', 'q34', 'side'), samples=64))
