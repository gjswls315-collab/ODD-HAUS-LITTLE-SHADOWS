"""Bully 리뷰 후보 (PROTOTYPE — 승인 전) — 150 cm stylized human boy, 처음부터 다시.
  머리: SDF 조형(두개 · 아래턱 · 통통한 볼 · 코 · 콧방울 · 눈썹뼈 · 눈구멍 · 위아래 눈꺼풀 · 얄미운 입 · 귀) → 리토폴로지
  머리카락: 금발 다발(뿌리 → 끝이 가늘어지는 납작한 다발)을 두피에서 뻗게 — 캡 밑 · 옆 · 뒤 · 앞 구멍으로 삐져나온다
  캡: 뒤로 쓴 버건디 캡 — 6조각 크라운(이음선 · 꼭대기 단추) · 챙(두께 · 휨) · 앞쪽 스냅백 구멍
  옷: 큰 검정 티(천 두께 · 주름) · 청바지(무릎 · 발목 주름 · 접은 밑단) · 빨간 하이탑(shoe.py) · 빨간 손목 밴드
  손: 손가락 다섯 · 손톱 · 마디 / 기타: 빨간 플라잉V(몸통 모서리 베벨 · 넥 · 헤드 · 픽업 · 줄) + 몸을 가로지르는 스트랩
게임 리그(rigs.json, 미터) 관절 위치에 맞춘다.
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import odd, tex
from odd import G

STAGE = os.environ.get('BULLY_STAGE', 'all')
RIG = json.load(open(os.environ.get('ODD_RIGS', os.path.join(odd.OUT, 'rigs.json'))))['bully']
J = {k: np.array(RIG[k]['p']) * 100 for k in RIG}          # 관절 (게임 cm)
cmv = lambda x, y, z: G(x, y, z, .01)
TAU = math.tau
sc = odd.reset()
TD = os.path.join(odd.OUT, 'bully_tex'); os.makedirs(TD, exist_ok=True)
rng = np.random.default_rng(5)
S_, E_, C_ = odd.sd_round_cone, odd.sd_ellipsoid, odd.sd_chain
sm, sx_ = odd.smin, odd.smax


def gcm(p):
    return np.stack([p[:, 0] / .01, p[:, 2] / .01, -p[:, 1] / .01], 1)


def box_of(lo, hi):
    a = np.array(cmv(*lo)); b = np.array(cmv(*hi)); return np.minimum(a, b), np.maximum(a, b)


def sdf_obj(name, fn_cm, lo, hi, vox, faces, subdiv=1, smooth_it=2):
    lo_, hi_ = box_of(lo, hi)
    d = odd.sdf_mesh('_' + name, lambda p: fn_cm(gcm(p)) * .01, lo_, hi_, vox)
    odd.drop_islands(d)
    odd.smooth(d, smooth_it, .4)
    o = odd.retopo(d, faces, subdiv, name); odd.delete(d)
    odd.recalc(o)                                                                                   # 면 방향을 다시 바깥으로 (뒤집힌 면은 웹 뷰어에서 사라진다)
    return o


# =====================================================================================
# 1. 머리 (게임 cm)
# =====================================================================================
EYE = [J['eye0'], J['eye1']]
EYE_R = 1.5
def head_sdf(q):
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    d = E_(q, (0, 140.2, 2.2), (9.6, 10.9, 10.8))                                   # 두개 (크게)
    jaw = E_(q, (0, 130.9, 4.7), (6.5, 6.0, 6.75))                                   # 아래 얼굴 · 턱 (좁게 · 입 둘레가 주둥이처럼 나오지 않게)
    d = sm(d, jaw, 3.0)
    chin = E_(q, (0, 126.4, 9.7), (2.9, 2.3, 2.1)); d = sm(d, chin, 2.2)                  # 턱끝을 앞으로 (입 아래가 깊게 들어가면 주둥이처럼 보인다)
    for s in (-1, 1):
        cheek = E_(q, (s * 4.5, 132.6, 8.3), (2.6, 2.3, 2.3)); d = sm(d, cheek, 2.2)   # 통통한 볼 (붓지 않게)
    brow = E_(q, (0, 141.6, 10.2), (7.2, 1.6, 2.2)); d = sm(d, brow, 2.6)           # 눈썹뼈 (부드럽게)
    # 코: 콧대 → 코끝 공 · 콧방울
    nose = S_(q, (0, 139.0, 12.0), (0, 134.8, 14.0), .75, .95)
    nose = sm(nose, E_(q, (0, 134.3, 14.3), (1.15, 1.0, 1.05)), .8)                  # 작고 둥근 코끝 (아이 코)
    for s in (-1, 1):
        nose = sm(nose, E_(q, (s * 1.1, 133.9, 13.3), (.75, .65, .7)), .6)
    d = sm(d, nose, 1.0)
    for s in (-1, 1):                                                                 # 콧구멍
        d = sx_(d, -E_(q, (s * .55, 133.4, 13.8), (.32, .2, .4)), .25)
    # 입: 윗입술 · 아랫입술 볼록 + 입술 사이 골 (오른쪽 입꼬리가 올라간 얄미운 웃음)
    upl = E_(q, (0, 131.2, 11.6), (1.9, .38, .4)); lol = E_(q, (.2, 129.95, 11.4), (1.6, .46, .45))
    d = sm(d, sm(upl, lol, .4), .6)
    mpts = [np.array([-2.2, 130.75, 11.0]), np.array([-1.2, 130.6, 11.85]), np.array([0, 130.62, 12.15]), np.array([1.3, 130.85, 11.9]), np.array([2.4, 131.6, 11.1])]
    mouth = C_(q, mpts, [.13, .1, .1, .11, .15], .1)
    d = sx_(d, -mouth, .3)
    d = sx_(d, -E_(q, (2.65, 131.75, 10.8), (.3, .28, .4)), .25)                       # 올라간 입꼬리 보조개
    for e in EYE:                                                                     # 눈구멍 + 눈꺼풀
        d = sx_(d, -E_(q, e + np.array([0, 0, -.5]), (2.2, 1.75, 1.85)), .55)
        upl_ = E_(q, e + np.array([0, .82, .38]), (2.15, .8, 1.4))                    # 위 눈꺼풀이 눈동자 위를 덮는다 (반쯤 감긴 눈 — 콘셉트)
        lol_ = E_(q, e + np.array([0, -1.25, .2]), (1.9, .5, 1.15))
        lidcut = -E_(q, e + np.array([0, -.3, 1.0]), (1.62, .6, 1.4))                 # 눈 뜬 틈 (가늘게)
        d = sm(d, sx_(sm(upl_, lol_, .3), lidcut, .25), .5)
    neck = S_(q, (0, 114, 0.5), (0, 129, 1.8), 6.0, 5.2); d = sm(d, neck, 2.2)
    return d

head = sdf_obj('Bully_Head', head_sdf, (-12, 112, -10), (12, 153, 18), .0016, 5200)

def eyeball(name, c, r):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        v.co = v.co.normalized() * r
        if v.co.y < -r * .6: v.co.y *= 1.06                     # 각막
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); odd.link(o); me.shade_smooth()
    odd.set_co(o, odd.co(o) + np.array(c)); odd.subsurf(o, 1)
    return o
eyes = [eyeball(f'Bully_Eye{i}', cmv(*(e + np.array([0, 0, -.75]))), EYE_R * .01) for i, e in enumerate(EYE)]

def ear_sdf(q, s):
    """귀: 나선 테(helix)가 둘러싼 둥근 귓바퀴 + 오목한 귀 안(concha) + 귓불."""
    c = np.array([s * 8.9, 135.6, 0.4])
    R = np.column_stack([np.array([0, 0, 1.0]), np.array([0, 1.0, 0]), np.array([s * 1.0, 0, 0])])
    shell = E_(q, c, (.85, 3.1, 2.3))
    shell = sm(shell, E_(q, c + np.array([s * .1, -2.15, .35]), (.7, 1.15, 1.3)), .7)         # 귓불
    rim = None
    for k in range(10):
        a0 = -1.9 + 3.6 * k / 9; a1 = -1.9 + 3.6 * (k + 1) / 9
        p0 = c + np.array([s * .35, 3.1 * math.sin(a0) * 1.0, 2.05 * math.cos(a0)]); p1 = c + np.array([s * .35, 3.1 * math.sin(a1), 2.05 * math.cos(a1)])
        seg = S_(q, p0, p1, .48, .48); rim = seg if rim is None else np.minimum(rim, seg)
    shell = sm(shell, rim, .35)
    shell = sx_(shell, -E_(q, c + np.array([s * .75, -.2, .25]), (.7, 1.7, 1.25)), .45)    # 귀 안
    stem = S_(q, c + np.array([-s * 1.5, 0, 0]), c, 1.6, 1.0)
    return sm(shell, stem, .6)
ears = [sdf_obj(f'Bully_Ear{i}', (lambda q, s=s: ear_sdf(q, s)), (s * 5, 130, -4), (s * 12.5, 141, 4.5), .0008, 900) for i, s in enumerate((-1, 1))]

# =====================================================================================
# 2. 몸(피부 — 팔 · 목만 보인다, 나머지는 옷이 닿는 충돌 몸) · 손
# =====================================================================================
SHO = [J['sho0'], J['sho1']]; ELB = [J['elb0'], J['elb1']]; WR = [J['hand0'], J['hand1']]
HIP = [J['hip0'], J['hip1']]; KNE = [J['knee0'], J['knee1']]; ANK = [J['foot0'], J['foot1']]
def torso_sdf(q, infl=0.0):
    d = E_(q, (0, 104, 1.2), (12.6 + infl, 14.5 + infl, 8.6 + infl))
    d = sm(d, E_(q, (0, 89, .4), (11.2 + infl, 9.5 + infl, 7.8 + infl)), 5)
    d = sm(d, E_(q, (0, 78, 0), (12.6 + infl, 9.0 + infl, 8.6 + infl)), 5)
    for s in (0, 1):
        d = sm(d, S_(q, (np.sign(SHO[s][0]) * 8, 114, 1.2), SHO[s], 5.6 + infl, 5.2 + infl), 3.5)
    return d
def arm_sdf(q, s, infl=0.0, upper_only=False):
    u = S_(q, SHO[s], ELB[s], 4.5 + infl, 3.7 + infl)
    if upper_only: return u
    return sm(u, S_(q, ELB[s], WR[s], 3.5 + infl, 2.7 + infl), 1.0)
def leg_sdf(q, s, infl=0.0):
    t = S_(q, HIP[s] + np.array([0, 2, 0]), KNE[s], 7.2 + infl, 5.0 + infl)
    return sm(t, S_(q, KNE[s], ANK[s] + np.array([0, -2, 0]), 4.9 + infl, 3.5 + infl), 1.5)
def body_sdf(q):
    d = torso_sdf(q)
    for s in (0, 1):
        d = sm(d, arm_sdf(q, s), 2.0); d = sm(d, leg_sdf(q, s), 3.0)
    d = sm(d, S_(q, (0, 112, .5), (0, 126, 1.8), 6.0, 5.2), 2.0)
    return d
skin = sdf_obj('Bully_Body', body_sdf, (-30, 2, -14), (30, 128, 14), .005, 4200)

def hand_frame(s):
    w = WR[s]; d = w - ELB[s]; d /= np.linalg.norm(d)
    inward = np.array([-np.sign(w[0]), 0, 0.0]); b = inward - d * (inward @ d); b /= np.linalg.norm(b)      # 손바닥이 허벅지 쪽
    t = np.cross(b, d); t = t if t[2] > 0 else -t                                                          # 엄지가 앞쪽
    return w, d, b, t
def hand_sdf(q, s):
    w, d, b, t = hand_frame(s); R = np.column_stack([t, b, d])
    P = lambda a, bb, c: w + t * a + b * bb + d * c
    h = E_(q, P(0, -.2, 4.6), (3.6, 1.45, 4.4), R)                                  # 손바닥
    h = sm(h, S_(q, P(0, 0, -1.5), P(0, 0, 1.5), 2.7, 2.9), 1.5)                   # 손목
    for k, (a, L1, L2, L3) in enumerate([(2.3, 3.0, 2.1, 1.7), (.8, 3.4, 2.3, 1.8), (-.8, 3.2, 2.2, 1.7), (-2.3, 2.6, 1.8, 1.5)]):
        curl = .25 + .08 * k
        p0 = P(a, -.1, 8.4); dirv = d * math.cos(curl) - b * math.sin(curl)
        p1 = p0 + d * L1; p2 = p1 + dirv * L2; p3 = p2 + (d * math.cos(curl * 2.2) - b * math.sin(curl * 2.2)) * L3
        r0 = .86 - .04 * abs(k - 1.5)
        h = sm(h, C_(q, [p0, p1, p2, p3], [r0, r0 * .9, r0 * .82, r0 * .74], .25), .7)
    th = [P(2.6, -.5, 2.6), P(4.0, -1.6, 5.0), P(4.4, -2.4, 7.4), P(4.3, -2.9, 9.2)]
    h = sm(h, C_(q, th, [1.15, .95, .85, .74], .3), .9)
    return h
hands = []
for s in (0, 1):
    w = WR[s]
    hands.append(sdf_obj(f'Bully_Hand{s}', (lambda q, s=s: hand_sdf(q, s)), tuple(w - 15), tuple(w + 15), .0012, 1900))

# =====================================================================================
# 3. 큰 검정 티: 몸을 3 cm 부풀린 껍질 → 밑단 · 소매 끝 · 목둘레를 잘라 열고 → 천 시뮬레이션(어깨 고정)으로 늘어뜨린다
# =====================================================================================
def tee_sdf(q):
    """큰 티: 몸통은 3 cm 넉넉하게, 어깨는 몸에 얹히듯(1 cm), 소매는 어깨 조금 아래에서 시작해 팔꿈치 위까지 헐렁하게."""
    infl = 3.0
    d = E_(q, (0, 104, 1.2), (12.6 + infl, 14.5 + infl * .7, 8.6 + infl))
    d = sm(d, E_(q, (0, 89, .4), (11.2 + infl, 9.5 + infl, 7.8 + infl)), 5)
    d = sm(d, E_(q, (0, 78, 0), (12.6 + infl, 9.0 + infl, 8.6 + infl)), 5)
    for s in (0, 1):
        d = sm(d, S_(q, (np.sign(SHO[s][0]) * 7.5, 114.5, 1.2), SHO[s] + np.array([0, -.6, 0]), 6.4, 5.9), 3.0)
        a0 = SHO[s] + (ELB[s] - SHO[s]) * .1
        d = sm(d, S_(q, a0, SHO[s] + (ELB[s] - SHO[s]) * .7, 6.2, 5.8), 2.5)
    return d
tee = sdf_obj('Bully_Tee', tee_sdf, (-34, 60, -16), (34, 130, 16), .006, 5200, subdiv=0)
def bis(o, co_, no, inner=False, outer=False):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co_, plane_no=no, clear_inner=inner, clear_outer=outer)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.0005); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=.0005)
    bm.to_mesh(o.data); bm.free()
gv = lambda x, y, z: Vector((x, -z, y)).normalized()
bis(tee, cmv(0, 70.5, 0), gv(0, 1, -.06), inner=True)                              # 밑단 (뒤가 살짝 길다)
for s in (0, 1):
    a = SHO[s] + (ELB[s] - SHO[s]) * .62; ax = (ELB[s] - SHO[s]) / np.linalg.norm(ELB[s] - SHO[s])
    bis(tee, cmv(*a), Vector((ax[0], -ax[2], ax[1])))                               # 소매 끝 (팔꿈치 위) — 자르는 선만 만들고
    bm = bmesh.new(); bm.from_mesh(tee.data)
    kill = []
    for f in bm.faces:                                                              # 소매 쪽 면만 지운다 (몸통은 그대로)
        c = gcm(np.array([f.calc_center_median()]))[0]
        if (c - a) @ ax > 0 and abs(c[0]) > 13.0 and np.sign(c[0]) == np.sign(a[0]): kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(tee.data); bm.free()
a = odd.co(tee); g = gcm(a)
bm = bmesh.new(); bm.from_mesh(tee.data); bm.verts.ensure_lookup_table()
neckkill = [f for f in bm.faces if (lambda c: (c[1] > 118.5) and (c[0] ** 2 / 7.6 ** 2 + ((c[2] - 1.2) ** 2) / 6.4 ** 2 < 1.0))(gcm(np.array([f.calc_center_median()]))[0])]
bmesh.ops.delete(bm, geom=neckkill, context='FACES'); bm.to_mesh(tee.data); bm.free()
odd.subsurf(tee, 1)
# 처짐 · 주름 (천 시뮬레이션 대신 직접): 큰 티가 어깨에서 늘어진다
a = odd.co(tee); g = gcm(a); nn = odd.nrm(tee)
low = np.clip((100 - g[:, 1]) / 28, 0, 1)
inward = np.stack([-g[:, 0], np.zeros(len(g)), -(g[:, 2] - .5)], 1); inward /= np.maximum(np.linalg.norm(inward, axis=1, keepdims=True), 1e-6)
side = np.clip(np.abs(g[:, 0]) / 15, 0, 1)
dispg = inward * (low * side * .9)[:, None] + np.array([0, -1, 0]) * (low * .6)[:, None]          # 옆이 안쪽 아래로 처진다
ripple = np.sin(TAU * (g[:, 1] / (4.2 + 1.6 * tex.fbm(g * .05, 1.0, 2, seed=4))) + tex.fbm(g * .06, 1.0, 2, seed=2) * 3.2) * np.clip((94 - g[:, 1]) / 10, 0, 1) * .32 * np.clip(np.abs(g[:, 0]) / 9, .3, 1)   # 허리 물결 주름 (옆쪽에 더)
a += np.stack([dispg[:, 0], -dispg[:, 2], dispg[:, 1]], 1) * .01 + nn * (ripple * .01)[:, None]
odd.set_co(tee, a)
for sgn in (-1, 1):
    for fz in (6.5, -6.5):                                                                      # 겨드랑이 → 허리 대각 주름 (앞 · 뒤)
        pts = odd.project(tee, [cmv(sgn * 12.5, 109, fz * .4), cmv(sgn * 10.0, 97, fz * .9), cmv(sgn * 7.0, 84, fz * 1.15)])
        for a_, b_ in zip(pts[:-1], pts[1:]):
            odd.crease(tee, a_, b_, .013, .0045); odd.ridge(tee, a_ + Vector((0, 0, .012)), b_ + Vector((0, 0, .012)), .012, .0025)
    a_, b_ = odd.project(tee, [cmv(*(SHO[0 if sgn < 0 else 1] + np.array([0, -5, 3]))), cmv(*(SHO[0 if sgn < 0 else 1] + (ELB[0 if sgn < 0 else 1] - SHO[0 if sgn < 0 else 1]) * .55 + np.array([0, 0, 4])))])
    odd.crease(tee, a_, b_, .01, .004)                                                           # 소매 주름
odd.smooth(tee, 1, .3)
odd.solidify(tee, .0035, offset=-1)
# 목둘레 립 · 밑단 말림
rib = []
for (dr, dy) in ((-.2, -.6), (.35, -.4), (.45, .3), (.2, .9), (-.25, 1.0)):
    rib.append([cmv(7.9 * math.cos(TAU * k / 48) + dr * math.cos(TAU * k / 48), 118.6 + dy + .5 * math.sin(TAU * k / 48), 1.2 + (6.7 + dr) * math.sin(TAU * k / 48)) for k in range(48)])
neckrib = odd.loft('Bully_TeeRib', rib); odd.solidify(neckrib, .003, offset=-1); odd.subsurf(neckrib, 1)

# =====================================================================================
# 4. 헐렁한 검정 카고 바지 (콘셉트 시트): 다리를 3 cm 이상 부풀린 일자 통 · 허벅지 바깥 카고 주머니(덮개) · 밑단이 신발 위에 쌓여 주름진다
# =====================================================================================
# 다리 단면: 리그의 좁은 자세(발 ±5 cm)에서도 두 다리가 붙지 않도록 중심을 바깥으로 옮기고 반지름을 키운다 → 안쪽 선은 그대로, 바깥 · 앞뒤만 헐렁
P_OFF = (1.2, 2.6, 2.2); P_RAD = (9.2, 7.9, 6.3)                                               # (엉덩이 · 무릎 · 발목) 바깥 이동 · 반지름
def pant_leg(q, s):
    sg = np.sign(HIP[s][0]); o = lambda j: np.array([sg * P_OFF[j], 0, 0])
    t_ = S_(q, HIP[s] + np.array([0, 2, 0]) + o(0), KNE[s] + o(1), P_RAD[0], P_RAD[1])
    b_ = S_(q, KNE[s] + o(1), ANK[s] + np.array([0, -4.5, 0]) + o(2), P_RAD[1], P_RAD[2])
    return sm(t_, b_, 2.0)
def pocket_c(s):
    """허벅지 바깥 면의 카고 주머니 자리 (게임 cm)."""
    t = (HIP[s][1] + 2 - 56) / (HIP[s][1] + 2 - KNE[s][1]); cx = HIP[s][0] + (KNE[s][0] - HIP[s][0]) * t + np.sign(HIP[s][0]) * (P_OFF[0] + (P_OFF[1] - P_OFF[0]) * t)
    rad = P_RAD[0] + (P_RAD[1] - P_RAD[0]) * t
    return np.array([np.sign(HIP[s][0]) * (min(abs(cx) + rad, PANTS_X) - .3), 56.0, .8])
PANTS_X = 17.4                                                                                    # 바깥 옆선 한계: 늘어뜨린 손(손목 x ±20 cm)과 겹치지 않게
def jeans_sdf(q):
    d = E_(q, (0, 79, 0), (14.4, 8.6, 10.4))
    d = sm(d, np.minimum(pant_leg(q, 0), pant_leg(q, 1)), 3.0)                                   # 두 다리는 딱 합친다 (치마처럼 이어지지 않게)
    for s in (0, 1):
        pc = pocket_c(s); sg = np.sign(HIP[s][0])
        d = sm(d, odd.sd_box(q, pc, (1.0, 5.4, 4.3), None, .7), .7)                                  # 카고 주머니
        d = sm(d, odd.sd_box(q, pc + np.array([sg * .45, 5.6, 0]), (.75, 1.3, 4.7), None, .5), .4)   # 주머니 덮개
    return sx_(d, np.abs(q[:, 0]) - (PANTS_X + 1.0), 1.0)
jeans = sdf_obj('Bully_Pants', jeans_sdf, (-30, 2, -18), (30, 90, 18), .006, 5200, subdiv=1)
bis(jeans, cmv(0, 82.5, 0), gv(0, 1, 0), outer=True)
bis(jeans, cmv(0, 11.0, 0), gv(0, 1, -.12), inner=True)                             # 밑단: 뒤가 조금 더 내려온다
for s in (0, 1):
    # 밑단이 신발 위에 쌓인 겹주름 (불규칙) · 무릎 앞 · 오금 주름
    rs_ = np.random.default_rng(40 + s)
    for k, yy in enumerate((13.5, 16.2, 19.4, 22.8, 26.5)):
        tilt = rs_.uniform(-1.2, 1.2)
        for fz in (4.6, -4.4):
            a_, b_ = odd.project(jeans, [cmv(ANK[s][0] - 6.6, yy + tilt, fz * 1.25), cmv(ANK[s][0] + 6.6, yy - tilt, fz * 1.25)])
            odd.crease(jeans, a_, b_, .012, .0042 - .0005 * k)
    for yy, dz in ((45.0, 5.6), (48.5, 5.2), (40.5, -5.6), (43.5, -5.8)):
        a_, b_ = odd.project(jeans, [cmv(KNE[s][0] - 4.2, yy, dz), cmv(KNE[s][0] + 4.2, yy + 1.4, dz)])
        odd.crease(jeans, a_, b_, .010, .003)
    for yy in (62, 66):                                                                    # 사타구니 쪽 주름 (V)
        a_, b_ = odd.project(jeans, [cmv(np.sign(HIP[s][0]) * 2.0, yy + 3, 9.6), cmv(np.sign(HIP[s][0]) * 8.0, yy, 9.6)])
        odd.crease(jeans, a_, b_, .008, .0024)
    pc = pocket_c(s)                                                                       # 주머니 아래로 늘어진 천 주름
    a_, b_ = odd.project(jeans, [cmv(*(pc + np.array([0, -6.5, -3]))), cmv(*(pc + np.array([0, -11, 2])))])
    odd.crease(jeans, a_, b_, .010, .003)
odd.solidify(jeans, .0028, offset=-1)
cuffs = []

# =====================================================================================
# 5. 신발 (shoe.py — Vin과 같은 구조, 3.4배) · 손목 밴드
# =====================================================================================
import shoe
SC = 3.4
def place_b(v, s):
    o = cmv(ANK[s][0], 0, 2.4); return o + Vector((-v.x, -v.y, v.z)) * .01 * SC
shoesB0 = shoe.build('Bully_Shoe0', lambda v: place_b(v, 0), side=1, collar_y=-.9, H=3.9, scale=SC, retopo_faces=1100)
shoesB1 = {k: odd.mirror_copy(o, o.name.replace('Shoe0', 'Shoe1')) for k, o in shoesB0.items()}
bands = []
for s in (0, 1):
    w, d, b, t = hand_frame(s); c = w - d * 2.4
    u = b; v_ = t; rings = []
    for (dr, dz) in ((-.3, -2.6), (.25, -2.4), (.4, 0), (.25, 2.4), (-.3, 2.6)):
        rings.append([cmv(*(c + d * dz + (u * math.cos(TAU * k / 32) + v_ * math.sin(TAU * k / 32)) * (3.05 + .4 + dr))) for k in range(32)])
    bd = odd.loft(f'Bully_Band{s}', rings); odd.solidify(bd, .003, offset=-1); odd.subsurf(bd, 1); bands.append(bd)

# 옷 속에 가려진 피부 면은 지운다 (보이는 곳: 목 · 팔뚝 · 손목)
bm = bmesh.new(); bm.from_mesh(skin.data)
cen = np.array([f.calc_center_median() for f in bm.faces]); gc = gcm(cen)
keep_fore = np.zeros(len(gc), bool)
for s_ in (0, 1):                                                                       # 소매 끝 너머(팔뚝)는 남긴다
    a_ = SHO[s_] + (ELB[s_] - SHO[s_]) * .62; ax_ = (ELB[s_] - SHO[s_]) / np.linalg.norm(ELB[s_] - SHO[s_])
    keep_fore |= ((gc - a_) @ ax_ > -.5) & (np.sign(gc[:, 0]) == np.sign(a_[0])) & (np.abs(gc[:, 0]) > 12)
neck_keep = (np.abs(gc[:, 0]) < 7.0) & (gc[:, 1] > 117) & (np.abs(gc[:, 2] - 1) < 7)
hidden = ((tee_sdf(gc) < 1.0) & (gc[:, 1] > 69) & (gc[:, 1] < 125) & ~keep_fore & ~neck_keep) | ((jeans_sdf(gc) < -.5) & (gc[:, 1] < 83) & (gc[:, 1] > 13))
kill = [f for f, h in zip(bm.faces, hidden) if h]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(skin.data); bm.free()

# =====================================================================================
# 6. 뒤로 쓴 캡: 6조각 크라운(이음선 · 꼭대기 단추) · 앞쪽 스냅백 구멍 + 똑딱이 띠 · 뒤로 향한 챙(두께 · 양옆이 휜다)
# =====================================================================================
BN = np.array([0, 1, -.244]); BN /= np.linalg.norm(BN); B0 = np.array([0, 143.9, 10.0])
band_y = lambda z: B0[1] + .244 * (z - B0[2])                                                     # 띠 높이 (z에서)
CAPR = np.array([10.35, 11.55, 11.45]); CAPC = np.array([0, 140.6, 2.2])
def crown_sdf(q):
    """크라운: 두께 0.36 cm의 얇은 껍질 (머리 + 머리카락 위) — 띠 평면 아래와 앞쪽 스냅백 구멍을 부드럽게 비운다."""
    outer = E_(q, CAPC, CAPR)
    d = np.abs(outer + .18) - .18
    d = sx_(d, -((q - B0) @ BN), .25)
    hole = E_(q, (0, 145.0, 10.8), (3.1, 2.9, 4.0))
    d = sx_(d, -hole, .35)
    return d
cap = sdf_obj('Bully_Cap', crown_sdf, (-13, 134, -13), (13, 154.5, 15), .0009, 3400, subdiv=0)
top = Vector(cmv(0, 152.0, 1.6))
for k in range(6):
    a = TAU * k / 6 + .52
    e = cmv(10.5 * math.sin(a), 141 + 3.2 * math.cos(a), 2.2 + 10.8 * math.cos(a))
    pts = odd.project(cap, [top.lerp(Vector(e), t) for t in (0, .35, .7, 1.0)])
    for a_, b_ in zip(pts[:-1], pts[1:]):
        odd.crease(cap, a_, b_, .0035, .0011)
odd.subsurf(cap, 1)
button = sdf_obj('Bully_CapButton', lambda q: E_(q, (0, 152.1, 1.6), (1.05, .55, 1.05)), (-2, 150.6, 0), (2, 153.6, 3.2), .0004, 200)
snap = odd.curve_tube('Bully_CapSnap', [cmv(-3.4, 144.5, 11.9), cmv(-1.2, 144.25, 13.0), cmv(1.2, 144.25, 13.0), cmv(3.4, 144.5, 11.9)], .0035, res=8, bevel_res=2)
# 챙: 안쪽 가장자리는 뒤통수의 캡 띠 곡선에 붙고, 바깥은 D자(뒤로 7.6 cm) · 살짝 위로 · 양옆이 아래로 휜다
def brim_pt(u, vv):
    xi = 8.7 * u; zi = CAPC[2] - (CAPR[2] - .25) * math.sqrt(max(0.0, 1 - (xi / (CAPR[0] - .2)) ** 2)); yi = band_y(zi) + .15
    w = math.sqrt(max(0.0, 1 - u * u))
    xo = xi * (1 + .07 * w); zo = zi - 7.6 * w ** .8; yo = yi + .5 * w - 1.6 * u * u * w
    t = vv; arch = -.35 * t * (1 - t) * w                                                     # 앞뒤로도 살짝 굽은 면
    return cmv(xi + (xo - xi) * t, yi + (yo - yi) * t + arch, zi + (zo - zi) * t)
rows = [[brim_pt(uu, vv) for uu in np.linspace(-1, 1, 25)] for vv in np.linspace(0, 1, 10)]
verts = [v for r in rows for v in r]; faces = []
for r_ in range(len(rows) - 1):
    for c_ in range(24):
        a0 = r_ * 25 + c_; faces.append((a0, a0 + 1, a0 + 26, a0 + 25))
brim = odd.mesh_obj('Bully_CapBrim', verts, faces)
odd.solidify(brim, .0045, offset=0); odd.subsurf(brim, 1)

# =====================================================================================
# 7. 금발: 캡 밑 머리 덩어리(두피 · 옆 · 뒤) + 다발(뿌리 → 끝 가늘게, 끝이 살짝 뻗친다) + 스냅백 구멍 앞머리 + 눈썹
# =====================================================================================
HLN = np.array([0, 1, -.4]); HLN /= np.linalg.norm(HLN)
NPN = np.array([0, 1, -.38]); NPN /= np.linalg.norm(NPN)
HC, HR = np.array([0, 140.4, 2.2]), 11.1
def lock_path(a, L, rs, r0, spread=0.0, flick=0.0, flare=0.0):
    """캡 띠 밑(뿌리)에서 아래로 떨어지는 머리 다발의 중심선: 위에서는 두개를 따라 눕고, 목덜미 쪽에서는 곧게 떨어지며 끝이 살짝 들린다."""
    sa, ca = math.sin(a), math.cos(a)
    y0 = 141.0
    for _ in range(20):                                                                          # 뿌리 = 캡 띠보다 0.9 cm 위 (캡 속)
        e = math.asin(np.clip((y0 - HC[1]) / HR, -1, 1)); z = HC[2] + HR * math.cos(e) * ca
        y0 = band_y(z) + .9
    pts = []
    for t in np.linspace(0, 1, 5):
        y = y0 - L * t
        f = math.sqrt(max(0.0, 1 - ((y - HC[1]) / HR) ** 2)) if y > HC[1] else 1.0
        f = max(f, .86 if abs(ca) > .5 else .97)                                                  # 뒤는 목덜미를 따라 조금 안으로, 옆은 곧게
        lift = -.7 * r0 + (.7 * r0 + .3) * min(1.0, t / .3) + flick * t * t + flare * t ** 1.0     # 뿌리는 캡 속 머리 안에서 시작 → 위로 떠오름 → 끝으로 갈수록 바깥으로 부푼다 (cm)
        rad = f + lift / HR
        aw = a + spread * t ** 1.5                                                               # 끝으로 갈수록 갈라진다
        pts.append(np.array([HR * .9 * rad * math.sin(aw), y, HC[2] + HR * rad * math.cos(aw)]))
    return pts
def flat_map(n, k):
    """다발을 n 방향으로 1/k 만큼 납작하게: 좌표를 n 방향으로 k배 늘린 공간에서 둥근 관을 잰다 (둥근 막대 → 머리에 눕는 납작한 다발)."""
    n = np.array(n, float); n /= np.linalg.norm(n)
    return np.eye(3) + (k - 1) * np.outer(n, n)
LOCKS = []
_rl = np.random.default_rng(11)
for g in range(26):                                                                              # 옆 · 뒤: 큰 뭉치 26개 × 가는 다발 2–4 (뿌리에서 뭉치고 끝에서 갈라져 방향이 다르다)
    side_ = -1 if g % 2 else 1
    a_g = side_ * (math.radians(38) + (math.pi - math.radians(38)) * ((g // 2) + _rl.uniform(-.25, .25)) / 12.6)  # 관자놀이부터 (앞머리와 옆머리 사이가 비지 않게)
    back = abs(math.cos(a_g)) if math.cos(a_g) < 0 else 0
    face_side = abs(a_g) < math.radians(70)                                                      # 얼굴 옆 다발: 눈가를 덮지 않게 짧고 덜 부푼다
    Lg = (_rl.uniform(10.5, 13.0) + 2.2 * back) * (.82 if face_side else 1.0)                   # 콘셉트: 귀를 덮고 턱 · 목덜미까지 오는 더벅머리
    flare_g = (.9 if face_side else 2.6) * _rl.uniform(.8, 1.2)                                   # 콘셉트: 캡 밑에서 바깥으로 부푼 더벅머리
    fan = _rl.uniform(-.06, .06)
    nsub = int(_rl.integers(2, 5))
    for j in range(nsub):
        u = (j - (nsub - 1) / 2)
        a = a_g + u * .06 + _rl.uniform(-.015, .015)
        L = Lg * _rl.uniform(.74, 1.1)
        r0 = _rl.uniform(.75, 1.05)
        pts = lock_path(a, L, _rl, r0, spread=fan + u * _rl.uniform(.05, .12), flick=_rl.uniform(.0, .9) * (1 if _rl.random() < .6 else .2), flare=flare_g)
        rad = [r0, r0 * .95, r0 * .82, r0 * .62, r0 * .34]                                       # 끝을 바늘처럼 뾰족하게 하지 않는다 (고드름처럼 보인다)
        lo_ = np.min(pts, 0) - r0 - 1.2; hi_ = np.max(pts, 0) + r0 + 1.2                      # smin 폭(.55)보다 넉넉히 — 경계에서 값이 튀지 않게
        LOCKS.append((pts, rad, lo_, hi_, flat_map((math.sin(a), 0, math.cos(a)), 1.5)))       # 머리 쪽(바깥 방향)으로 납작한 다발
_hbvh = BVHTree.FromObject(head, bpy.context.evaluated_depsgraph_get())
def face_z(x, y):
    """실제 조형된 머리 표면의 앞 z (게임 cm) — 앞에서 광선을 쏴서 찾는다 (두개 타원 추정은 눈썹뼈 쪽에서 1 cm 가까이 안쪽이라 앞머리가 묻힌다)."""
    hit, _, _, _ = _hbvh.ray_cast(Vector(cmv(x, y, 40)), Vector((0, 1, 0)))
    if hit is not None: return -hit.y / .01
    e2 = 1 - (x / 9.6) ** 2 - ((y - 140.2) / 10.9) ** 2
    return 2.2 + 10.8 * math.sqrt(max(e2, .05))
def bang_path(x0, L, sweep, rs, r0):
    """앞머리 다발 중심선: 캡 띠 밑 → 이마 표면 위로 자기 두께만큼 떠서 내려오며 옆으로 쓸린다."""
    pts = []; y0 = band_y(12.0) + .6 - .02 * x0 * x0
    rads = [1.0, .92, .76, .54, .3]
    for k, t in enumerate(np.linspace(0, 1, 5)):
        x = x0 + sweep * t ** 1.3; y = y0 - L * t
        lift = -.4 * r0 if k == 0 else rads[k] * r0 * .75 + .18 + rs.uniform(0, .3) * t * t
        pts.append(np.array([x, y, face_z(x, y) + lift]))
    return pts
_rb = np.random.default_rng(17)
for k in range(18):                                                                              # 앞머리 다발 18개 (뿌리 사이로 이마가 비치지 않게 촘촘히)
    x0 = -6.0 + 12.0 * (k + _rb.uniform(-.3, .3)) / 17
    Lb = _rb.uniform(5.0, 7.4) * (1 - .25 * min(1, abs(x0) / 6))
    sweep = -1.7 * _rb.uniform(.6, 1.2) + .4 * np.sign(x0) * min(1, abs(x0) / 4)
    r0 = _rb.uniform(.85, 1.15); pts = bang_path(x0, Lb, sweep, _rb, r0)
    LOCKS.append((pts, [r0, r0 * .92, r0 * .76, r0 * .54, r0 * .3], np.min(pts, 0) - r0 - 1.2, np.max(pts, 0) + r0 + 1.2, flat_map((0, .25, 1), 1.8)))
def locks_sdf(q):
    d = np.full(len(q), 1e3)
    for pts, rad, lo_, hi_, M in LOCKS:
        m = np.all((q >= lo_) & (q <= hi_), 1)
        if m.any():
            d[m] = np.minimum(d[m], C_(q[m] @ M.T, [M @ p_ for p_ in pts], rad, .35))
    return d
HL2 = np.array([0, 1, -.5]); HL2 /= np.linalg.norm(HL2)
def scalp_sdf(q):
    """두피 위 얇은 머리 층 (0.55 cm): 앞머리 · 옆머리 다발 사이로 이마 · 관자놀이 살이 비치지 않게 — 캡 띠 밑 2 cm 정도까지만."""
    d = np.full(len(q), 1e3)
    m = (q[:, 1] > 130) & (np.abs(E_(q, (0, 140.2, 2.2), (9.6, 10.9, 10.8))) < 3.0)
    if m.any():
        d[m] = head_sdf(q[m]) - .55
    return sx_(d, -((q - np.array([0, 142.0, 11.0])) @ HL2), .5)
def hair_mass_sdf(q):
    d = E_(q, (0, 140.4, 2.2), (9.95, 11.1, 11.1))
    d = sx_(d, -((q - np.array([0, 135.8, 0])) @ NPN), .8)                                       # 옆은 귀 위까지, 뒤는 목덜미 쪽으로 낮게
    d = sx_(d, -((q - np.array([0, 143.2, 11.0])) @ HLN), .6)                                     # 앞머리선 (캡 띠 바로 밑)
    d = sm(d, sx_(E_(q, (0, 145.6, 11.6), (3.4, 2.9, 1.5)), -((q - np.array([0, 143.6, 11.0])) @ HLN), .4), .8)   # 스냅백 구멍으로 부푼 머리
    d = sm(d, scalp_sdf(q), .5)                                                                      # 다발 사이 두피를 덮는 얇은 층
    d = sm(d, locks_sdf(q), .55)                                                                     # 다발이 머리 덩어리에서 자라 나온다
    return d
hairmass = sdf_obj('Bully_HairMass', hair_mass_sdf, (-17, 120, -18.5), (17, 154, 15.5), .0013, 9000)
dg = bpy.context.evaluated_depsgraph_get(); hbvh = BVHTree.FromObject(hairmass, dg)
clumps = []
def clump(root_cm, dir_cm, L, r0, curl=(0, 0, 0), seed=0, bvh=None, stick=4, off=(.004, .004), radii=None, flat=.45):
    bvh = bvh or hbvh
    r_ = np.random.default_rng(seed)
    root = Vector(cmv(*root_cm)); dv = Vector(cmv(*dir_cm)) - Vector(cmv(0, 0, 0)); dv.normalize()
    pts = []; p_ = root
    for k in range(6):
        t = k / 5
        loc, nrm_, _, _ = bvh.find_nearest(p_)
        if loc is not None and k < stick:
            p_ = loc + nrm_ * (off[0] + off[1] * t)
        pts.append(p_.copy())
        p_ = p_ + dv * (L * .01 / 5) + Vector(cmv(*curl)) * (t * t) - Vector(cmv(0, 0, 0)) * 0
    radii = radii or [1.0, .97, .88, .72, .52, .26]
    o = odd.curve_tube('_clump', pts, r0 * .01, res=6, bevel_res=2, radii=radii)
    # 납작하게: 머리 표면 법선 방향 두께를 줄여 머리에 눕는 다발로 (둥근 막대 → 납작한 머리 다발)
    P = np.array([tuple(p) for p in pts]); V = odd.co(o)
    seg_a, seg_b = P[:-1], P[1:]; ab = seg_b - seg_a; L2 = np.maximum((ab * ab).sum(1), 1e-12)
    t_ = np.clip(np.einsum('vsk,sk->vs', V[:, None, :] - seg_a[None], ab) / L2, 0, 1)
    C = seg_a[None] + t_[..., None] * ab[None]; di = np.linalg.norm(V[:, None, :] - C, axis=2); j = di.argmin(1)
    Cn = C[np.arange(len(V)), j]
    N = np.array([tuple(bvh.find_nearest(Vector(c))[1] or Vector((0, 0, 1))) for c in Cn])
    off_ = V - Cn; along = (off_ * N).sum(1)
    odd.set_co(o, V - N * (along * flat)[:, None])
    clumps.append(o)
r_ = np.random.default_rng(3)
headbvh = BVHTree.FromObject(head, dg)
for k in range(7):                                                                               # 가는 가닥: 앞머리 위에 눕혀 다발 결을 나눈다 (튀어나오면 가시처럼 보인다)
    x0 = -5.8 + 11.6 * ((k % 11) + r_.uniform(-.4, .4)) / 6
    y0 = band_y(11.5) - .2 - .02 * x0 * x0 + r_.uniform(-.2, .3)
    side = np.sign(x0) * min(1, abs(x0) / 4)
    clump((x0, y0, 13.4), (side * r_.uniform(.15, .5) + r_.uniform(-.3, .2) - .32, -1.0, 0), r_.uniform(3.6, 5.6) * (1 - .15 * abs(side)),
          r_.uniform(.22, .3), curl=(side * r_.uniform(.1, .3), 0, 0), seed=100 + k, bvh=hbvh, stick=6, off=(.0012, .0004),
          radii=[.7, 1.0, .9, .7, .45, .2], flat=.6)
hair = odd.join(clumps, 'Bully_Hair')
brows = []
for s in (0, 1):
    sg = -1 if s == 0 else 1; e = EYE[s]
    inner = e + np.array([-sg * 1.7, 2.6 - .35 * (s == 0), 1.15]); mid = e + np.array([sg * .2, 3.35, 1.25]); outer = e + np.array([sg * 2.3, 3.1 + .5 * (s == 1), .55])
    brows.append(odd.curve_tube(f'Bully_Brow{s}', [cmv(*inner), cmv(*mid), cmv(*outer)], .0062, res=8, bevel_res=3, radii=[.9, 1.0, .45]))
    odd.scale_region(brows[-1], cmv(*mid), .05, (1, 1, .55), kind='flat') if False else None

# =====================================================================================
# 8. 빨간 스트랫 기타 (콘셉트 시트): 더블 컷어웨이 몸통(긴 위 혼 · 팔 받침 · 배 받침 깎임 · 둥근 모서리) · 흰 픽가드 · 싱글 픽업 3 ·
#    크롬 브리지 · 크림 노브 3 · 메이플 넥 + 로즈우드 지판 · 6-in-line 헤드(페그 6) · 줄 6
#    오른쪽 허리 앞에 들고 넥은 왼쪽 위로. 갈색 가죽 스트랩: 꼬리 핀 → 오른쪽 허리 → 등을 가로질러 → 왼쪽 어깨 → 가슴 → 위 혼 핀
#    (게임 리그의 guitar 노드는 지금 등에 있다 — 게임에 넣을 때 쉬는 자세의 기타 자리를 앞으로 옮긴다: 겉모습만)
# =====================================================================================
NF = np.array([0, .14, 1.0]); NF /= np.linalg.norm(NF)                                           # 몸통 앞면: 앞(살짝 위)
A_ = np.array([math.cos(math.radians(27)), math.sin(math.radians(27)), 0.0]); A_ -= NF * (A_ @ NF); A_ /= np.linalg.norm(A_)   # 넥: 캐릭터 왼쪽 위
U_ = np.cross(NF, A_); U_ /= np.linalg.norm(U_)                                                   # +u = 위 혼(베이스 쪽)
GS = .88
BODYC = np.array([-6.5, 77.5, 15.6])                                                              # 몸통 가운데 (오른쪽 허리 앞)
G0 = BODYC + A_ * (22 * GS)
def gl(u, a, w):                     # 기타 로컬(cm) → 게임 cm
    return G0 + U_ * (u * GS) + A_ * ((a - 2) * GS) + NF * (w * GS)
def sd_poly2(px, py, poly):
    d = np.full(len(px), 1e9); inside = np.zeros(len(px), bool)
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        ex, ey = x1 - x0, y1 - y0; wx, wy = px - x0, py - y0
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, np.hypot(wx - ex * t, wy - ey * t))
        c1 = (py >= y0) != (py >= y1); xc = x0 + (py - y0) * ex / (ey + 1e-12)
        inside ^= c1 & (px < xc)
    return np.where(inside, -d, d)
BODY_P = [(2.9, -1.0), (3.4, 1.8), (4.4, 4.4), (5.9, 5.6), (7.6, 5.0), (9.6, 2.4), (12.0, -1.5), (14.6, -6.5), (15.9, -11.5), (15.2, -15.5), (13.9, -18.5),
          (14.3, -22.0), (15.6, -26.5), (16.1, -31.0), (15.4, -35.5), (13.0, -39.4), (9.0, -42.0), (4.0, -43.2), (0.0, -43.4),
          (-4.0, -43.2), (-9.0, -42.0), (-13.0, -39.4), (-15.4, -35.5), (-16.1, -31.0), (-15.6, -26.5), (-14.2, -22.0), (-13.6, -18.5),
          (-14.6, -14.0), (-15.0, -9.0), (-14.0, -4.5), (-12.0, -1.2), (-9.4, 1.2), (-7.0, 2.4), (-5.3, 1.9), (-4.0, .4), (-3.2, -1.0)]
HEAD_P = [(-2.3, 33.4), (2.3, 33.4), (2.9, 36.0), (4.5, 40.0), (4.9, 46.5), (4.1, 51.2), (2.2, 52.9), (.3, 52.4), (-.9, 50.2), (-1.5, 46.5), (-1.8, 41.0), (-2.1, 36.5)]
PG_P = [(2.9, -1.4), (7.5, -1.8), (10.6, -5.0), (11.8, -10.0), (10.8, -15.0), (8.6, -19.5), (6.6, -22.0), (5.6, -25.5), (4.6, -29.0), (3.0, -28.6), (-3.0, -28.6),
        (-4.8, -29.8), (-6.5, -33.8), (-9.2, -37.0), (-12.0, -36.4), (-13.6, -32.2), (-13.2, -27.0), (-11.0, -21.8), (-9.6, -16.0), (-10.3, -9.5),
        (-9.2, -4.6), (-6.6, -2.2), (-3.4, -1.8)]
def ext(d2, w, t, r):
    qx = d2 + r; qy = np.abs(w) - t / 2 + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
def to_g(q):
    rel = (q - G0) / GS; return rel @ U_, rel @ A_ + 2, rel @ NF
def gbody_sdf(q):
    u, a, w = to_g(q)
    d = ext(sd_poly2(u, a, BODY_P), w, 4.5, 1.05)
    wt = 2.25 - 1.25 * np.clip((u - 9.5) / 6, 0, 1) * np.clip((-a - 14) / 8, 0, 1)                 # 팔 받침 (앞면 위 혼 쪽 아래 둘레)
    d = sx_(d, (w - wt) * .9, .6)
    wb = -2.25 + 1.0 * np.clip((u - 8) / 6, 0, 1) * np.clip((a + 22) / 8, 0, 1)                    # 배 받침 (뒷면 위 혼 쪽)
    d = sx_(d, (wb - w) * .9, .6)
    return d
def gneck_sdf(q):
    u, a, w = to_g(q)
    hw = 2.8 - .7 * np.clip(a / 34, 0, 1)
    neck = ext(np.maximum(np.abs(u) - hw, np.maximum(-a - 4, a - 34.2)), w - 1.75, 2.3, .9)
    head_ = ext(sd_poly2(u, a, HEAD_P), w - 1.7, 1.4, .35)
    return np.minimum(neck, head_)
def pg_sdf(q):
    u, a, w = to_g(q); return ext(sd_poly2(u, a, PG_P), w - 2.39, .28, .08) * GS
gbox = [gl(u, a, w) for u in (-20, 20) for a in (-47, 56) for w in (-4, 6)]
glo = np.min(gbox, 0); ghi = np.max(gbox, 0)
gbody = sdf_obj('Bully_GuitarBody', lambda q: gbody_sdf(q) * GS, tuple(glo), tuple(ghi), .0025, 2600)
gneck = sdf_obj('Bully_GuitarNeck', lambda q: gneck_sdf(q) * GS, tuple(glo), tuple(ghi), .002, 1800)
pickguard = sdf_obj('Bully_Pickguard', pg_sdf, tuple(np.min([gl(u, a, w) for u in (-15, 13) for a in (-39, 1) for w in (1.5, 3.5)], 0)),
                    tuple(np.max([gl(u, a, w) for u in (-15, 13) for a in (-39, 1) for w in (1.5, 3.5)], 0)), .0012, 900, subdiv=0)
def part_box(name, u, a, w, hu, ha, hw_, r, vox=.0008, faces=300):
    def fn(q):
        uu, aa, ww = to_g(q); qq = np.stack([uu - u, aa - a, ww - w], 1)
        return odd.sd_box(qq, (0, 0, 0), (hu, ha, hw_), None, r) * GS
    pts_ = np.array([gl(u + du, a + da, w + dw) for du in (-hu - 1, hu + 1) for da in (-ha - 1, ha + 1) for dw in (-hw_ - 1, hw_ + 1)])
    return sdf_obj(name, fn, tuple(pts_.min(0)), tuple(pts_.max(0)), vox, faces)
pick = [part_box(f'Bully_Pickup{k}', 0, a, 2.95, 4.1, .9, .45, .4) for k, a in enumerate((-14.8, -20.8, -26.4))]
bridge = part_box('Bully_Bridge', 0, -31.6, 2.5, 3.7, 2.2, .22, .15)
tailp = part_box('Bully_Saddles', 0, -30.9, 2.95, 3.3, .45, .3, .15)                              # 안장 6 (한 줄)
knobs = [sdf_obj(f'Bully_Knob{k}', (lambda q, uu=uu, aa=aa: S_(q, gl(uu, aa, 2.5), gl(uu, aa, 3.9), 1.05 * GS, .9 * GS)),
                 tuple(np.minimum(gl(uu - 2, aa - 2, 2), gl(uu + 2, aa + 2, 5))), tuple(np.maximum(gl(uu - 2, aa - 2, 2), gl(uu + 2, aa + 2, 5))), .0005, 140)
         for k, (uu, aa) in enumerate(((-6.4, -25.0), (-8.6, -29.2), (-10.6, -33.6)))]
knobs.append(sdf_obj('Bully_Switch', (lambda q: S_(q, gl(-8.4, -20.0, 2.5), gl(-8.0, -20.0, 3.8), .35 * GS, .45 * GS)),
                     tuple(np.minimum(gl(-10, -22, 2), gl(-6, -18, 5))), tuple(np.maximum(gl(-10, -22, 2), gl(-6, -18, 5))), .0004, 100))
TUN = [(2.95 - .1 * k, 36.8 + 2.75 * k) for k in range(6)]                                          # 페그 기둥 (헤드 위쪽 가장자리를 따라)
tuners = []
for k, (tu, ta) in enumerate(TUN):
    post = (lambda q, tu=tu, ta=ta: sm(S_(q, gl(tu, ta, 2.3), gl(tu, ta, 3.5), .45 * GS, .38 * GS),
                                       sm(S_(q, gl(tu, ta, .9), gl(tu + 2.6, ta, .9), .3 * GS, .3 * GS), E_(q, gl(tu + 3.3, ta, .9), (1.05 * GS, .95 * GS, .32 * GS),
                                          np.column_stack([U_, A_, NF])), .2), .2))
    tuners.append(sdf_obj(f'_tuner{k}', post, tuple(np.minimum(gl(tu - 1.5, ta - 1.6, -.5), gl(tu + 5, ta + 1.6, 4.2))), tuple(np.maximum(gl(tu - 1.5, ta - 1.6, -.5), gl(tu + 5, ta + 1.6, 4.2))), .0004, 260, subdiv=0))
tuners = odd.join(tuners, 'Bully_Tuners')
strings = []
for k in range(6):                                                                                 # k = 0 굵은 6번 줄 (위 혼 쪽)
    ub = (2.5 - k) * 1.05; un = (2.5 - k) * .72; tu, ta = TUN[k]
    strings.append(odd.curve_tube('_str', [cmv(*gl(ub, -30.6, 3.25)), cmv(*gl((ub + un) / 2, 2.0, 3.15)), cmv(*gl(un, 34.0, 3.0)), cmv(*gl(tu, ta, 3.3))],
                                  (.03 + .009 * (5 - k)) * .01 * GS, res=6, bevel_res=1))
gstrings = odd.join(strings, 'Bully_GuitarStrings')
# 스트랩
dg = bpy.context.evaluated_depsgraph_get(); tbvh = BVHTree.FromObject(tee, dg)
route = [gl(0, -43.9, 0), (-21, 72, 9), (-17.5, 79, -2), (-12, 88, -10.5), (-3, 99, -11.8), (6.5, 110, -9.8), (12.4, 118, -2.6), (12.0, 116.5, 5.2), (8.0, 105, 11.8), gl(6.0, 6.0, 0)]
spts, snrm = [], []
for k, rp in enumerate(route):
    P_ = Vector(cmv(*rp))
    if 0 < k < len(route) - 1:
        loc, nrm_, _, _ = tbvh.find_nearest(P_); P_ = loc + nrm_ * .004; snrm.append(nrm_)
    else:
        snrm.append(Vector(cmv(*NF)) - Vector(cmv(0, 0, 0)))
    spts.append(P_)
sp, _ = odd.spline(spts, 48)
sn = []
for P_ in sp:
    loc, nrm_, _, _ = tbvh.find_nearest(P_); sn.append(nrm_ if (loc - P_).length < .03 else (P_ - Vector(cmv(0, 100, 0))).normalized())
axis_c = Vector(cmv(0, 100, 0))
for _ in range(4):
    sn = [((sn[max(i - 1, 0)] + sn[i] * 2 + sn[min(i + 1, len(sn) - 1)]) / 4).normalized() for i in range(len(sn))]
sn = [n_ if n_.dot((P_ - Vector((axis_c.x, axis_c.y, P_.z))).normalized()) > -.2 else -n_ for P_, n_ in zip(sp, sn)]
strap = odd.ribbon('Bully_Strap', [P_ + n_ * .006 for P_, n_ in zip(sp, sn)], [.046] * len(sp), normals=sn)
odd.solidify(strap, .0038, offset=0)
# 가슴 위 버클 (금속 사각 고리) — 스트랩 길이 조절
bi = int(len(sp) * .86); bp = sp[bi]; bt = (sp[bi + 1] - sp[bi - 1]).normalized(); bn = sn[bi]; bb = bt.cross(bn).normalized()
Mb = np.column_stack([np.array(bb), np.array(bt), np.array(bn)])
def buckle_sdf(p):
    q = (p - np.array(bp + bn * .008)) @ Mb
    o_ = odd.sd_box(q, (0, 0, 0), (.029, .016, .0028), None, .0015); i_ = odd.sd_box(q, (0, 0, 0), (.024, .011, .006), None, .001)
    return np.maximum(o_, -i_)
buckle = odd.sdf_mesh('Bully_Buckle', buckle_sdf, np.array(bp) - .05, np.array(bp) + .05, .0005)   # 얇은 고리라 리토폴로지 대신 표면을 다듬고 줄인다
odd.drop_islands(buckle); odd.smooth(buckle, 2, .4); odd.decimate(buckle, .1); buckle.data.shade_smooth()
# 목걸이: 가는 체인 + 작은 펜던트 (콘셉트 정면)
neck_pts = [(-6.6, 117.6, 4.2), (-4.8, 112.4, 9.6), (-1.6, 109.0, 12.0), (1.6, 109.0, 12.0), (4.8, 112.4, 9.6), (6.6, 117.6, 4.2), (4.5, 119.6, -3.5), (-4.5, 119.6, -3.5)]
npts = []
for q_ in neck_pts:
    loc, nrm_, _, _ = tbvh.find_nearest(Vector(cmv(*q_))); npts.append(loc + nrm_ * .003)
chain = odd.curve_tube('Bully_Chain', npts, .0012, res=10, bevel_res=2, closed=True)
pend = sdf_obj('Bully_Pendant', lambda q: odd.sd_box(q, (0, 107.4, 12.6), (.7, 1.1, .18), None, .15), (-2, 105, 11), (2, 110, 14.5), .0003, 200)

if STAGE in ('head', 'body') and False:
    odd.lookdev_scene('studio', size=1.0)
    m = odd.Mat('skin'); m.set(Base_Color=(.85, .62, .5, 1), Roughness=.55)
    w = odd.Mat('eye'); w.set(Base_Color=(.9, .9, .9, 1), Roughness=.1)
    for o in [head] + ears + hands + [skin]: o.data.materials.append(m.m)
    for o in eyes: o.data.materials.append(w.m)
    k_ = odd.Mat('tee'); k_.set(Base_Color=(.06, .06, .065, 1), Roughness=.8)
    jn = odd.Mat('jean'); jn.set(Base_Color=(.08, .1, .18, 1), Roughness=.85)
    rd = odd.Mat('red'); rd.set(Base_Color=(.5, .05, .04, 1), Roughness=.6)
    tee.data.materials.append(k_.m); jeans.data.materials.append(jn.m)
    for o in cuffs: o.data.materials.append(jn.m)
    for o in bands: o.data.materials.append(rd.m)
    for sh in (shoesB0, shoesB1):
        for k, o in sh.items(): o.data.materials.append(rd.m if k in ('upper', 'tongue') else w.m)
    for o in [cap, brim, button, snap]: o.data.materials.append(rd.m)
    yl = odd.Mat('blond'); yl.set(Base_Color=(.85, .66, .3, 1), Roughness=.5)
    for o in [hairmass, hair] + brows: o.data.materials.append(yl.m)
    for o in [gbody, gneck] + pick + [bridge, tailp] + knobs + [gstrings, strap, neckrib]: o.data.materials.append(rd.m if o in (gbody,) else k_.m)
    print(odd.render_views(os.path.join(odd.OUT, 'bully_head'), cmv(0, 135, 4), .34, views=('front', 'side', 'q34', 'close:0.6:25')))
    print(odd.render_views(os.path.join(odd.OUT, 'bully_body'), cmv(0, 76, 0), 1.6, views=('front', 'side', 'back', 'q34')))
    print(odd.render_views(os.path.join(odd.OUT, 'bully_hand'), cmv(*(WR[1] + np.array([0, -6, 0]))), .25, views=('front', 'side', 'q34')))
    sys.exit(0)

# 면 예산: 조형이 끝난 뒤 큰 메시를 형태를 지키며 줄인다 (잔디테일은 노멀맵)
BUDGET = {'Bully_Tee': 30000, 'Bully_Pants': 24000, 'Bully_Head': 24000, 'Bully_Hair': 12000, 'Bully_HairMass': 16000, 'Bully_Cap': 12000,
          'Bully_GuitarBody': 9000, 'Bully_GuitarNeck': 7000, 'Bully_Tuners': 4000, 'Bully_Hand0': 9000, 'Bully_Hand1': 9000, 'Bully_CapBrim': 3500,
          'Bully_Shoe0_Upper': 6500, 'Bully_Ear0': 3500, 'Bully_Ear1': 3500}
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name in BUDGET:
        t = sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
        if t > BUDGET[o.name] * 1.05:
            odd.decimate(o, BUDGET[o.name] / t); o.data.shade_smooth()
for k in list(shoesB1):
    odd.delete(shoesB1[k]); shoesB1[k] = odd.mirror_copy(shoesB0[k], shoesB0[k].name.replace('Shoe0', 'Shoe1'))

# =====================================================================================
# 9. 재질 · 텍스처
# =====================================================================================
from PIL import Image, ImageDraw, ImageFont
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def S_of(o, size, angle=60, margin=.004):
    odd.uv_smart(o, angle, margin); S = tex.Surf(o, size); return S, gcm(S.p)

# 피부 (얼굴 · 귀 · 목 · 팔 · 손): 볼 홍조 · 코끝 · 귀 붉게 · 주근깨 · 입술 · 손등 마디
SKIN = np.array([.86, .66, .55])
def skin_color(g, seed=0):
    c = np.tile(SKIN, (len(g), 1)) * (1 + .05 * tex.fbm(g, .25, 3, seed=seed))[:, None]
    blush = np.zeros(len(g))
    for sg in (-1, 1):
        blush += np.exp(-np.sum(((g - np.array([sg * 4.6, 132.2, 9.6])) / np.array([2.6, 2.0, 3])) ** 2, 1))
    blush += .7 * np.exp(-np.sum(((g - np.array([0, 134.3, 14.6])) / 1.4) ** 2, 1))                    # 코끝
    blush += .6 * np.clip((np.abs(g[:, 0]) - 8.2) / 1.2, 0, 1) * (np.abs(g[:, 1] - 135.5) < 4.5)          # 귀
    c = c * (1 - .18 * blush[:, None]) + np.array([.86, .45, .42])[None, :] * (.18 * blush[:, None])
    lips = np.exp(-(((g[:, 0]) / 2.6) ** 2 + ((g[:, 1] - 130.6) / .9) ** 2)) * (g[:, 2] > 11.5)
    c = c * (1 - .45 * lips[:, None]) + np.array([.74, .42, .40])[None, :] * (.45 * lips[:, None])
    for e_ in EYE:                                                                                        # 눈 밑 그늘
        uh = np.exp(-(((g[:, 0] - e_[0]) / 1.9) ** 2 + ((g[:, 1] - (e_[1] - 1.7)) / .8) ** 2)) * (g[:, 2] > 9)
        c = c * (1 - .16 * uh[:, None]) + np.array([.55, .42, .47])[None, :] * (.16 * uh[:, None])
    from scipy.spatial import cKDTree
    rs_ = np.random.default_rng(77); fp = []
    while len(fp) < 90:                                                                                      # 주근깨: 코 · 볼 위에 흩어진 작은 점
        c0 = np.array([rs_.uniform(-6.2, 6.2), rs_.uniform(131.0, 136.4), 0])
        if abs(c0[0]) < 1.0 and c0[1] < 133.0: continue
        if rs_.random() > np.exp(-((abs(c0[0]) - 3.2) / 3.0) ** 2) * .9 + .1: continue
        fp.append(c0)
    fp = np.array(fp); fr_r = rs_.uniform(.08, .17, len(fp)); fr_k = rs_.uniform(.35, .8, len(fp))
    tree = cKDTree(fp[:, :2]); dd, ii = tree.query(g[:, :2])
    on = (g[:, 2] > 8.0) * np.clip(1 - dd / fr_r[ii], 0, 1) ** .7 * fr_k[ii]
    c = c * (1 - on[:, None] * np.array([.22, .34, .42])[None, :])
    return c, lips
Sh, g = S_of(head, 2048)
hc, lips = skin_color(g)
pores = tex.vnoise(g, 9.0, seed=3) * .3 + tex.vnoise(g, 3.0, seed=4) * .3
head_m = tex.material('Bully_Skin', TD, Sh.img(np.clip(hc, 0, 1)), Sh.img(.55 - .15 * lips + .05 * pores), tex.h2n(Sh.img(pores), .6), sheen=(.25, .5, (1, .85, .8, 1)))
head.data.materials.append(head_m)
for o in ears + [skin] + hands:
    Sx, gx = S_of(o, 1024 if o in hands or o is skin else 512)
    cx, _ = skin_color(gx, seed=len(o.name))
    if o in hands:                                                                                         # 손톱 · 마디 붉게
        knuck = np.clip(tex.vnoise(gx, .9, seed=5), 0, 1)
        cx = cx * (1 - .08 * knuck[:, None])
    o.data.materials.append(tex.material(o.name + '_M', TD, Sx.img(np.clip(cx, 0, 1)), Sx.img(np.full(len(cx), .56)), tex.h2n(Sx.img(tex.vnoise(gx, 6, seed=7) * .3), .6), sheen=(.25, .5, (1, .85, .8, 1))))

# 눈: 회녹색 홍채(방사 무늬 · 어두운 테) · 동공 · 반사 · 흰자 가장자리 분홍
for i, (eo, e) in enumerate(zip(eyes, EYE)):
    c = Vector(cmv(*(e + np.array([0, 0, -.75])))); out = Vector((0, -1, 0)); u_ = Vector((1, 0, 0)); v_ = Vector((0, 0, 1))
    uv = eo.data.uv_layers.new(name='UVMap'); a = odd.co(eo)
    for poly in eo.data.polygons:
        for li in poly.loop_indices:
            p_ = Vector(a[eo.data.loops[li].vertex_index]) - c
            uv.data[li].uv = (.5 + p_.dot(u_) / (2 * EYE_R * .01), .5 + p_.dot(v_) / (2 * EYE_R * .01))
N_ = 512; yy, xx = (np.mgrid[0:N_, 0:N_] + .5) / N_ - .5; rr_ = np.hypot(xx, yy) / .5; an = np.arctan2(yy, xx)
img = np.tile(np.array([.93, .9, .88]), (N_, N_, 1)) * (1 - .25 * np.clip((rr_ - .55) / .4, 0, 1))[..., None]
img = img * (1 - .2 * np.clip((rr_ - .7) / .3, 0, 1)[..., None]) + np.array([.9, .55, .55]) * (.2 * np.clip((rr_ - .7) / .3, 0, 1)[..., None])
iris = np.array([.40, .44, .40]) * (.72 + .38 * (np.sin(an * 44) * .5 + .5) ** 2)[..., None] * (1 - .6 * np.clip((rr_ - .33) / .1, 0, 1))[..., None]   # 회녹색 (콘셉트)
img = np.where((rr_ < .43)[..., None], iris, img)
img = np.where((rr_ < .19)[..., None], np.array([.02, .02, .025]), img)
img = np.where((np.hypot(xx - .07, yy - .09) < .05)[..., None], np.array([.98, .98, .98]), img)
eyeM = tex.material('Bully_Eye', TD, img, np.full((N_, N_), .06), None, coat=(1, .03))
for eo in eyes: eo.data.materials.append(eyeM)

# 머리카락 · 눈썹: 금발 (뿌리 어둡게 · 끝 밝게)
for o, nm in ((hairmass, 'Bully_HairMass'), (hair, 'Bully_Hair')):
    Sx, gx = S_of(o, 1024, margin=.016)                                                          # 섬 간격을 넓게: 뿌리(진한)와 끝(밝은) 섬이 밉맵에서 섞여 밝은 테두리가 생기지 않게
    from scipy.spatial import cKDTree
    dm_, _ = cKDTree(gcm(odd.co(hairmass))).query(gx)
    tip = np.clip(dm_ / 3.0, 0, 1) if o is hair else np.clip((141 - gx[:, 1]) / 7, 0, 1)
    strand = tex.vnoise(gx * np.array([6, 1.2, 6]), 1.0, seed=9)
    cx = np.array([.58, .43, .22])[None, :] * (1 - tip[:, None]) + np.array([.95, .85, .60])[None, :] * tip[:, None]
    cx *= (.85 + .25 * (strand * .5 + .5))[:, None]
    hb = tex.bump(Sx, lambda p_, n_: tex.vnoise(gcm(p_) * np.array([6, 1.2, 6]), 1.0, seed=9) * .5, .0008, 1.0)   # 섬 경계에 줄이 생기지 않는 3D 미분 노멀
    o.data.materials.append(tex.material(nm, TD, Sx.img(np.clip(cx, 0, 1)), Sx.img(.45 + .1 * strand), hb, sheen=(.5, .35, (1, .9, .7, 1)), double=True))
browM = odd.gltf_material('Bully_Brow', base_value=(.5, .35, .17, 1), rough_value=.6)
for o in brows: o.data.materials.append(browM)

# 캡: 버건디 능직 · 이음선 박음질 · 통풍 구멍 · 뒤(챙 위) 패치 · 챙 밑면 어두운 회녹색 · 단추 · 스냅 띠
Sc, gc = S_of(cap, 1024)
twill = tex.vnoise(gc * np.array([1.0, 1.0, 1.0]), 9.0, seed=33) * .05 + tex.fbm(gc, 1.2, 3, seed=34) * .08
hh = twill.copy()
topg = np.array([0, 152.0, 1.6])
for k in range(6):
    a = TAU * k / 6 + .52
    e = np.array([10.5 * math.sin(a), 141 + 3.2 * math.cos(a), 2.2 + 10.8 * math.cos(a)])
    d, s_ = tex.polyline_dist(gc, [topg, topg + (e - topg) * .5, e])
    hh += -np.exp(-(d / .06) ** 2) * 1.2
    for off in (.28, -.28):
        hh += np.clip(1 - np.abs(d - abs(off)) / .05, 0, 1) * (np.sin(s_ * 18) > -.2)
    vent = topg + (e - topg) * .32 + (np.cross(e - topg, gc[:, :3].mean(0) - topg) * 0)
    hh -= np.exp(-np.sum((gc - (topg + (e - topg) * .3 + np.array([math.cos(a), 0, -math.sin(a)]) * 1.6)) ** 2, 1) / .06) * 2.5
ccol = np.array([.50, .09, .085])[None, :] * (.9 + .15 * tex.fbm(gc, .6, 3, seed=31))[:, None]
sunb = np.clip((gc[:, 1] - 146) / 6, 0, 1) * np.clip(tex.fbm(gc, .35, 3, seed=36) * 1.2 + .5, 0, 1)        # 햇빛에 바랜 꼭대기
ccol = ccol * (1 - .45 * sunb[:, None]) + np.array([.66, .32, .26])[None, :] * (.45 * sunb[:, None])
dust_c = np.clip(tex.fbm(gc, 1.5, 4, seed=37) * 1.6 - .5, 0, 1)
ccol = ccol * (1 - .25 * dust_c[:, None]) + np.array([.45, .36, .3])[None, :] * (.25 * dust_c[:, None])
ccol *= (1 - .45 * np.clip(-hh, 0, 1) * 0)[:, None]
vents = np.zeros(len(gc))
for k in range(6):
    a = TAU * k / 6 + .52; e = np.array([10.5 * math.sin(a), 141 + 3.2 * math.cos(a), 2.2 + 10.8 * math.cos(a)])
    vents = np.maximum(vents, np.exp(-np.sum((gc - (topg + (e - topg) * .3 + np.array([math.cos(a), 0, -math.sin(a)]) * 1.6)) ** 2, 1) / .06))
ccol = ccol * (1 - .8 * vents[:, None])
patch = np.exp(-(((gc[:, 0]) / 2.8) ** 2 + ((gc[:, 1] - 143.5) / 2.2) ** 2)) * (gc[:, 2] < -6)
ring = (np.abs(np.hypot(gc[:, 0], gc[:, 1] - 143.5) - 1.6) < .32) & (gc[:, 2] < -6)
ccol = np.where(ring[:, None], np.array([.92, .88, .8]), ccol)
cap_m = tex.material('Bully_Cap', TD, Sc.img(np.clip(ccol, 0, 1)), Sc.img(.82 - .2 * ring), tex.h2n(Sc.img(hh * .5 + ring * .6), 1.4), sheen=(.35, .5, (1, .8, .8, 1)))
cap.data.materials.append(cap_m); odd.uv_smart(button, 60, .01); button.data.materials.append(cap_m)
Sb, gb = S_of(brim, 1024)
upf = Sb.n[:, 2] > 0                                                                                  # 위를 보는 면 = 챙 윗면
outer = [np.array(gcm(np.array([brim_pt(uu, 1.0)]))[0]) for uu in np.linspace(-1, 1, 41)]
dout, _ = tex.polyline_dist(gb, outer)
rows_ = np.zeros(len(gb))
for k in range(1, 7):                                                                                 # 바깥 가장자리를 따라가는 박음질 줄
    rows_ += np.clip(1 - np.abs(dout - k * .85) / .06, 0, 1)
fray = np.clip(1 - dout / .5, 0, 1) * np.clip(tex.fbm(gb, 2.0, 3, seed=38) + .3, 0, 1)                        # 챙 가장자리 닳음
bcol = np.where(upf[:, None], np.array([.50, .09, .085]), np.array([.12, .13, .11]))
bcol = bcol * (1 - .5 * fray[:, None]) + np.array([.62, .45, .38])[None, :] * (.5 * fray[:, None])
brim_m = tex.material('Bully_Brim', TD, Sb.img(bcol), Sb.img(np.full(len(gb), .8)), tex.h2n(Sb.img(rows_ * upf * .6 + tex.vnoise(gb, 9.0, seed=35) * .05), 1.4))
brim.data.materials.append(brim_m)
snap.data.materials.append(odd.gltf_material('Bully_Snap', base_value=(.26, .14, .07, 1), rough_value=.55))   # 갈색 가죽 조절 띠

# 티: 빛바랜 검정 면 저지 · 주름 위가 바랜 · 구멍 · 앞 프린트(해골 + 흰 가시 + 빨간 물감 — 콘셉트) · 목 립
P_ = 1024; pim = Image.new('RGBA', (P_, P_), (0, 0, 0, 0)); dr = ImageDraw.Draw(pim)
W_ = (238, 232, 220, 255); R_ = (196, 30, 32, 255)
rsp = np.random.default_rng(23)
for k in range(26):                                                                                  # 흰 가시 · 튄 조각 (해골 둘레로 뻗는다)
    a = rsp.uniform(0, TAU); L = rsp.uniform(150, 330); wdt = rsp.uniform(10, 26)
    x0, y0 = 512 + math.cos(a) * 120, 430 + math.sin(a) * 120; x1, y1 = 512 + math.cos(a) * L, 430 + math.sin(a) * L
    nx, ny = -math.sin(a), math.cos(a)
    dr.polygon([(x0 + nx * wdt, y0 + ny * wdt), (x1, y1), (x0 - nx * wdt, y0 - ny * wdt)], fill=(205, 200, 190, 255))
for k in range(70):                                                                                  # 빨간 물감 방울 · 흘러내림
    a = rsp.uniform(0, TAU); r0 = rsp.uniform(60, 300); x, y = 512 + math.cos(a) * r0, 440 + math.sin(a) * r0 * 1.15; rr = rsp.uniform(6, 34)
    dr.ellipse([x - rr, y - rr * rsp.uniform(.7, 1.3), x + rr, y + rr * rsp.uniform(.7, 1.3)], fill=R_)
    if rsp.random() < .35: dr.rectangle([x - rr * .25, y, x + rr * .25, y + rsp.uniform(40, 140)], fill=R_)
dr.ellipse([362, 270, 662, 560], fill=W_)                                                           # 해골
dr.rectangle([428, 520, 596, 636], fill=W_)
for ex in (448, 576):
    dr.ellipse([ex - 50, 372, ex + 50, 474], fill=(10, 10, 12, 255))
    dr.ellipse([ex - 16, 404, ex + 16, 440], fill=R_)                                                # 빨간 눈 빛
dr.polygon([(512, 486), (490, 532), (534, 532)], fill=(10, 10, 12, 255))
for tx in range(440, 600, 30):
    dr.rectangle([tx, 590, tx + 13, 636], fill=(10, 10, 12, 255))
parr = np.asarray(pim).astype(float) / 255
crack = (tex.vnoise(np.stack([np.repeat(np.arange(P_), P_) / 18., np.tile(np.arange(P_), P_) / 18., np.zeros(P_ * P_)], 1), 1.0, seed=3).reshape(P_, P_) > .62)
parr[..., 3] *= np.where(crack, .25, 1.0)                                                            # 갈라진 프린트
St, gt = S_of(tee, 2048)
front = (St.n @ np.array([0, -1.0, 0])) > .25
u_p = ((gt[:, 0] + 11.0) / 22.0); v_p = ((112 - gt[:, 1]) / 22.0)
inb = front & (u_p > 0) & (u_p < 1) & (v_p > 0) & (v_p < 1)
pi = np.clip((v_p * (P_ - 1)).astype(int), 0, P_ - 1); pj = np.clip((u_p * (P_ - 1)).astype(int), 0, P_ - 1)
pr = parr[pi, pj]; pa = pr[:, 3] * inb
fold_hi = np.clip(tex.fbm(gt, .2, 3, seed=6) * .8, 0, 1)
tcol = np.array([.095, .09, .095])[None, :] * (1 + .7 * fold_hi)[:, None] + np.array([.06, .055, .055])[None, :] * np.clip(tex.fbm(gt, 1.2, 3, seed=7), 0, 1)[:, None]   # 빨아서 바랜 검정
holes = np.clip(tex.fbm(gt, 1.1, 3, seed=19) * 2.2 - 1.55, 0, 1) * (np.abs(gt[:, 1] - 80) < 9)                 # 밑단 쪽 작은 구멍 · 해짐
tcol = tcol * (1 - .7 * holes[:, None])
tcol = tcol * (1 - pa[:, None]) + pr[:, :3] * .82 * pa[:, None]
knit = (np.sin(gt[:, 0] * 70) * .5 + .5) * .25 + tex.vnoise(gt, 25, seed=2) * .1
tee_m = tex.material('Bully_Tee', TD, St.img(np.clip(tcol, 0, 1)), St.img(.86 - .35 * pa), tex.h2n(St.img(knit + pa * .2), 1.0), sheen=(.5, .6, (.5, .5, .55, 1)))
tee.data.materials.append(tee_m)
Sr, gr = S_of(neckrib, 512)
neckrib.data.materials.append(tex.material('Bully_TeeRib', TD, Sr.img(np.tile([.04, .04, .045], (len(gr), 1))), Sr.img(np.full(len(gr), .88)), tex.h2n(Sr.img(np.sin(np.arctan2(gr[:, 2] - 1.2, gr[:, 0]) * 120) * .5), 1.4)))

# 카고 바지: 차콜 · 검정 능직 — 허벅지 · 무릎 바램, 무릎 해짐(구멍 · 실밥), 밑단 흙먼지, 박음질 · 카고 주머니 테 (콘셉트)
Sj, gj = S_of(jeans, 2048)
tw_ = np.sin((gj[:, 0] * .7 + gj[:, 1]) * 26 + tex.vnoise(gj, 2, seed=1) * .6) * .5
fade = np.zeros(len(gj)); rip = np.zeros(len(gj))
for s in (0, 1):
    fade += np.exp(-(((gj[:, 0] - KNE[s][0]) / 5.5) ** 2 + ((gj[:, 1] - 55) / 13) ** 2)) * (gj[:, 2] > 0) * .7
    fade += np.exp(-(((gj[:, 0] - KNE[s][0]) / 4.5) ** 2 + ((gj[:, 1] - 43) / 5) ** 2)) * .6
    kc = np.array([KNE[s][0] + (1.5 if s else -1.5), 41.5 + 2.5 * s, 8.5])
    rip = np.maximum(rip, np.clip(1 - np.sum(((gj - kc) / np.array([2.6, 1.5, 6])) ** 2, 1), 0, 1))
fade += .45 * np.clip(tex.fbm(gj, .25, 3, seed=14) * 1.4, 0, 1)
dirt = np.clip((24 - gj[:, 1]) / 12, 0, 1) * np.clip(tex.fbm(gj, .8, 3, seed=15) + .6, 0, 1)
jcol = np.array([.20, .195, .20])[None, :] * (1 + .25 * tw_)[:, None]                               # 빨아서 바랜 차콜 (콘셉트)
jcol = jcol * (1 - (fade * .6)[:, None]) + np.array([.38, .36, .33])[None, :] * (fade * .6)[:, None]
jcol = jcol * (1 - (dirt * .45)[:, None]) + np.array([.30, .25, .19])[None, :] * (dirt * .45)[:, None]
threads = (np.sin(gj[:, 0] * 9 + tex.vnoise(gj, 4, seed=16) * 2) > .3) * (rip > .05) * (rip < .55)
jcol = np.where((rip > .55)[:, None], np.array([.80, .62, .52]) * .55, jcol)                       # 구멍 (안쪽 그늘 · 살)
jcol = np.where(threads[:, None], np.array([.62, .6, .56]), jcol)                                   # 해진 실밥
seamh = np.zeros(len(gj))
for s in (0, 1):
    sg = np.sign(HIP[s][0]); pc = pocket_c(s)
    edge_p = (np.abs(np.abs(gj[:, 2] - pc[2]) - 4.0) < .14) & (np.abs(gj[:, 1] - pc[1]) < 5.2) | (np.abs(gj[:, 1] - (pc[1] - 5.1)) < .14) & (np.abs(gj[:, 2] - pc[2]) < 4.0)
    flap = (np.abs(gj[:, 1] - (pc[1] + 4.4)) < .14) & (np.abs(gj[:, 2] - pc[2]) < 4.5)
    side_ = (sg * gj[:, 0] > 9) & (np.abs(gj[:, 2] - .5) < .2)
    seamh += (edge_p | flap) * (sg * gj[:, 0] > 10) + side_
    pk = (np.abs(np.abs(gj[:, 0] - sg * 6.8) - 4.4) < .12) | (np.abs(gj[:, 1] - 76) < .12)
    seamh += pk * (gj[:, 2] < -6) * (gj[:, 1] > 64) * (gj[:, 1] < 77) * (np.abs(gj[:, 0] - sg * 6.8) < 4.5)
stitch = np.clip(seamh, 0, 1) * (np.sin((gj[:, 1] + gj[:, 0] + gj[:, 2]) * 9) > 0)
jcol = jcol * (1 - .6 * stitch[:, None]) + np.array([.30, .29, .27])[None, :] * (.6 * stitch[:, None])
jeans_m = tex.material('Bully_Pants', TD, Sj.img(np.clip(jcol, 0, 1)), Sj.img(.86 + .05 * tw_ - .1 * dirt), tex.h2n(Sj.img(tw_ * .5 + seamh * .4 - rip * .8), 1.2))
jeans.data.materials.append(jeans_m)

# 손목: 갈색 가죽 커프 (가장자리 박음질 · 주름 · 닳음 · 금속 징) — 콘셉트
for bi_, o in enumerate(bands):
    Sw, gw = S_of(o, 512)
    w_, d_, b_, t_ = hand_frame(bi_); cw = w_ - d_ * 2.4
    along_ = (gw - cw) @ d_
    edge_b = np.clip(1 - (2.2 - np.abs(along_)) / .35, 0, 1)
    stw = (np.abs(np.abs(along_) - 1.8) < .1) * (np.sin(np.arctan2((gw - cw) @ t_, (gw - cw) @ b_) * 30) > 0)
    studs = np.zeros(len(gw))
    if bi_ == 1:
        for k in range(8):
            ang_ = TAU * k / 8; sc_ = cw + (b_ * math.cos(ang_) + t_ * math.sin(ang_)) * 3.8
            studs = np.maximum(studs, np.clip(1 - np.linalg.norm(gw - sc_, axis=1) / .45, 0, 1))
    leather = tex.fbm(gw, 3.0, 4, seed=8 + bi_)
    bc = np.array([.24, .13, .07])[None, :] * (.85 + .3 * leather)[:, None] * (1 - .35 * edge_b)[:, None] + np.array([.5, .4, .3])[None, :] * (.25 * stw)[:, None]
    bc = np.where((studs > .2)[:, None], np.array([.72, .72, .74]), bc)
    o.data.materials.append(tex.material(f'Bully_Band{bi_}', TD, Sw.img(np.clip(bc, 0, 1)), Sw.img(np.where(studs > .2, .25, .62 - .1 * leather)), tex.h2n(Sw.img(leather * .3 + studs * 1.2 - stw * .3), 1.4)))

# 신발
o_s = np.array(cmv(ANK[0][0], 0, 2.4))
def slB(p):
    q = (p - o_s) / (.01 * SC); return np.stack([-q[:, 0], -q[:, 1], q[:, 2]], 1)
fwdB = (place_b(Vector((0, 1, 0)), 0) - place_b(Vector((0, 0, 0)), 0)).normalized()
shoe.paint(shoesB0, slB, fwdB, TD, 'Bully', scale=SC, H=3.9, collar_y=-.9)
for k in list(shoesB1):
    odd.delete(shoesB1[k]); shoesB1[k] = odd.mirror_copy(shoesB0[k], shoesB0[k].name.replace('Shoe0', 'Shoe1'))

# 기타 (콘셉트): 닳은 빨강 유광 — 모서리 · 팔 닿는 곳은 칠이 벗겨져 밝은 나무, 잔 긁힘 · 찍힘, 아래 둘레에 둥근 ODD 스티커 /
#       흰 3겹 픽가드(긁힘) / 메이플 넥 + 로즈우드 지판(프렛 · 점) / 메이플 헤드 / 크롬 브리지 · 페그 / 검정 픽업 / 크림 노브
Sg, gg = S_of(gbody, 2048)
u, a, w = to_g(gg)
dpoly = sd_poly2(u, a, BODY_P)
edge = np.clip(1 - np.abs(dpoly) / .9, 0, 1) * np.clip(tex.fbm(gg, 1.2, 3, seed=12) * 1.4 + .25, 0, 1)
arm = np.clip(1 - np.hypot(u - 12.5, a + 26) / 6, 0, 1) * (w > 0) * np.clip(tex.fbm(gg, .9, 3, seed=13) + .5, 0, 1)   # 팔이 닿아 벗겨진 곳
bare = np.clip(edge * 1.3 + arm * .9 - .35, 0, 1)
scr = np.clip(tex.fbm(gg * np.array([1, 6, 1]), 2.4, 3, seed=17) * 1.8 - 1.0, 0, 1) * .6
stk_c = np.array([-7.8, -36.8]); rst = np.hypot(u - stk_c[0], a - stk_c[1])
sticker = (rst < 2.6) & (w > 0)
wood = np.array([.80, .62, .40])[None, :] * (1 + .08 * np.sin(a * 3.0 + tex.vnoise(gg, 1.5, seed=18) * 2))[:, None]
gcol = np.array([.60, .045, .04])[None, :] * (1 + .07 * tex.fbm(gg, .4, 2, seed=11))[:, None] * (1 - .2 * scr)[:, None]
gcol = gcol * (1 - bare[:, None]) + wood * bare[:, None]
from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
sim = _I.new('RGB', (256, 256), (236, 230, 216)); sd_ = _D.Draw(sim); sd_.ellipse([10, 10, 246, 246], outline=(180, 30, 30), width=14)
f_ = _F.truetype(FB, 78); tw_s = sd_.textlength('ODD', font=f_); sd_.text((128 - tw_s / 2, 82), 'ODD', font=f_, fill=(180, 30, 30))
sar = np.asarray(sim).astype(float) / 255
si = np.clip(((stk_c[1] + 2.6 - a) / 5.2 * 255).astype(int), 0, 255); sj = np.clip(((u - stk_c[0] + 2.6) / 5.2 * 255).astype(int), 0, 255)
scol = sar[si, sj] * (1 - .3 * np.clip(tex.fbm(gg, 3, 3, seed=19) + .2, 0, 1))[:, None]
gcol = np.where(sticker[:, None], scol, gcol)
gbody.data.materials.append(tex.material('Bully_GuitarBody', TD, Sg.img(np.clip(gcol, 0, 1)), Sg.img(np.clip(.2 + .45 * bare + .25 * scr + .4 * sticker, 0, 1)), tex.h2n(Sg.img(-bare * .4 - scr * .5), 1.0), coat=(1, .06)))
Spg, gpg = S_of(pickguard, 1024)
pgs = np.clip(tex.fbm(gpg * np.array([3, 1, 3]), 3.0, 3, seed=27) * 1.6 - .7, 0, 1)
pu_, pa_, pw_ = to_g(gpg); ply = np.clip(1 - np.abs(sd_poly2(pu_, pa_, PG_P)) / .12, 0, 1)
pgc = np.array([.90, .88, .82])[None, :] * (1 - .12 * pgs)[:, None] * (1 - .55 * ply)[:, None]      # 가장자리 검은 겹
pickguard.data.materials.append(tex.material('Bully_Pickguard', TD, Spg.img(np.clip(pgc, 0, 1)), Spg.img(.28 + .3 * pgs), tex.h2n(Spg.img(-pgs * .4), .8), coat=(.6, .1)))
Sn_, gn = S_of(gneck, 1024)
u, a, w = to_g(gn)
board = (w > 2.25) & (a < 34.1) & (a > -4)
frets = np.zeros(len(gn)); SCL = 64.8
for kf in range(1, 22):
    pos = 34 - SCL * (1 - 2 ** (-kf / 12))
    if pos > -3.6: frets = np.maximum(frets, (np.abs(a - pos) < .07).astype(float))
dots = np.zeros(len(gn))
for kf in (3, 5, 7, 9, 12, 15, 17, 19):
    pos = 34 - SCL * (1 - 2 ** (-(kf - .5) / 12))
    for du in ((-.9, .9) if kf == 12 else (0,)):
        dots = np.maximum(dots, (np.hypot(u - du, a - pos) < .3).astype(float))
headf = (a > 34) & (w > 1.9)
maple = np.array([.86, .66, .40])[None, :] * (1 + .06 * np.sin(a * 2.2 + tex.vnoise(gn, 1.0, seed=29) * 3))[:, None]
ncol = np.where(board[:, None], np.array([.16, .085, .05]), maple)
ncol = np.where((board & (frets > 0))[:, None], np.array([.80, .78, .74]), ncol)
ncol = np.where((board & (dots > 0))[:, None], np.array([.92, .90, .84]), ncol)
ncol = np.where((headf & (np.hypot(u - .2, a - 41.5) < 1.1))[:, None], np.array([.04, .04, .04]), ncol)   # 헤드 작은 로고
gneck.data.materials.append(tex.material('Bully_GuitarNeck', TD, Sn_.img(np.clip(ncol, 0, 1)), Sn_.img(np.where(board, .55, .3) - .3 * frets), tex.h2n(Sn_.img(frets * .8), 1.0), coat=(.7, .1)))
chrome = odd.gltf_material('Bully_Chrome', base_value=(.85, .85, .87, 1), rough_value=.2, metal_value=1.0)
blackp = odd.gltf_material('Bully_PickupBlack', base_value=(.03, .03, .035, 1), rough_value=.35)
for o in pick: o.data.materials.append(blackp)
for o in (bridge, tailp, gstrings, tuners, buckle): o.data.materials.append(chrome)
cream = odd.gltf_material('Bully_Knob', base_value=(.86, .82, .70, 1), rough_value=.3)
for o in knobs: o.data.materials.append(cream)
silver = odd.gltf_material('Bully_Silver', base_value=(.62, .62, .64, 1), rough_value=.3, metal_value=1.0)
for o in (chain, pend): o.data.materials.append(silver)
Ss_, gs_ = S_of(strap, 1024)
lth = tex.fbm(gs_, 1.5, 4, seed=21)
st_edge = np.zeros(len(gs_))
scol_ = np.array([.33, .17, .08])[None, :] * (.8 + .35 * (lth * .5 + .5))[:, None]
strapM = tex.material('Bully_Strap', TD, Ss_.img(np.clip(scol_, 0, 1)), Ss_.img(.5 + .12 * lth), tex.h2n(Ss_.img(lth * .3 + tex.vnoise(gs_, 6, seed=22) * .2), .8))
strap.data.materials.append(strapM)

# =====================================================================================
# 10. 내보내기 (리뷰 후보) · 확인 렌더
# =====================================================================================
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.data.materials:
        print('NO MATERIAL', o.name)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in meshes)
GLB = os.path.join(odd.OUT, 'review', 'enemy_bully_review.glb')
print('GLB', GLB, odd.export_glb(GLB, meshes), 'bytes', 'tris', tris, 'objects', len(meshes))
