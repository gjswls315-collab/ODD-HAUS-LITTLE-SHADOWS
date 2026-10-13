"""Lounge 구역 리뷰 후보 (PROTOTYPE — 승인 전) — 거실의 한 귀퉁이를 실제 크기로, 물건 하나하나를 조형한다.
  벽(웨인스코팅 · 몰딩 · 다마스크 벽지) · 월넛 마루(널마다 높이 · 틈) · 창(깊은 창턱) + 무거운 벨벳 커튼(천 시뮬레이션) ·
  체스터필드 소파(단추 터프팅 · 말린 팔걸이 · 눌린 쿠션 · 파이핑 · 주름) · 사이드 테이블(서랍 틈 · 놋쇠 손잡이 · 깨진 모서리) ·
  도자기 램프(두께 있는 천 갓 · 전구) · 처진 전선 + 플러그 · 페르시아 러그(두께 · 술 · 말린 모서리) · 책 더미 · LP 슬리브 더미.
게임의 동선(충돌 · 트리거)은 이 파일과 무관 — 승인 뒤 게임에 넣을 때 충돌 상자에 맞춘다.
단위 m, Blender Z 위, 정면 = −Y.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from mathutils import Vector
import odd, tex

STAGE = os.environ.get('LOUNGE_STAGE', 'all')
TAU = math.tau
sc = odd.reset()
TD = os.path.join(odd.OUT, 'lounge_tex'); os.makedirs(TD, exist_ok=True)
rng = np.random.default_rng(21)
E_, S_, B_ = odd.sd_ellipsoid, odd.sd_round_cone, odd.sd_box
sm, sx_ = odd.smin, odd.smax
WALL_Y = .95; X0, X1 = -1.35, 1.35


def sdf_obj(name, fn, lo, hi, vox, faces, subdiv=1, smooth_it=2):
    d = odd.sdf_mesh('_' + name, fn, np.array(lo), np.array(hi), vox)
    odd.smooth(d, smooth_it, .4)
    o = odd.retopo(d, faces, subdiv, name); odd.delete(d)
    return o


# =====================================================================================
# 1. 소파 (체스터필드) — 프레임(등받이 · 말린 팔걸이 · 받침) + 단추 터프팅 + 쿠션 2개(눌림 · 파이핑) + 다리
# =====================================================================================
SX, SY = -.22, .52                  # 소파 중심
HW, HD = .80, .42                   # 반폭 · 반깊이
def L(p):                           # 소파 로컬
    return p - np.array([SX, SY, 0])
TUFT = []
for row in range(3):
    zz = .53 + row * .075
    n_ = 7 if row % 2 == 0 else 6
    for k in range(n_):
        xx = -HW + .16 + (k + (.5 if row % 2 else 0)) * ((2 * HW - .32) / 6)
        TUFT.append(np.array([xx, HD - .205 + row * .012, zz]))
def frame_sdf(p):
    q = L(p); x, y, z = q[:, 0], q[:, 1], q[:, 2]
    base = B_(q, (0, 0, .26), (HW, HD, .14), None, .035)
    back = B_(q, (0, HD - .1, .45), (HW, .1, .3), None, .06)
    back = sm(back, S_(q, (-HW + .05, HD - .1, .72), (HW - .05, HD - .1, .72), .085, .085), .05)      # 등받이 위 둥근 말림
    d = sm(base, back, .04)
    for s in (-1, 1):
        arm = B_(q, (s * (HW - .075), 0, .4), (.075, HD, .26), None, .04)
        roll = S_(q, (s * (HW - .045), -HD + .03, .64), (s * (HW - .045), HD - .06, .66), .095, .09)      # 바깥으로 말린 팔걸이
        d = sm(d, sm(arm, roll, .05), .04)
    # 터프팅: 단추 자리 오목 + 단추 사이 다이아몬드 주름
    for t in TUFT:
        d = sx_(d, -E_(q, t + np.array([0, -.004, 0]), (.022, .02, .022)), .03)
    for i, a in enumerate(TUFT):
        for b in TUFT[i + 1:]:
            if .06 < np.linalg.norm(a - b) < .14:
                d = sx_(d, -S_(q, a + np.array([0, -.006, 0]), b + np.array([0, -.006, 0]), .0045, .0045), .012)
    # 팔걸이 안쪽 세로 주름 (말린 부분 아래로 모이는 주름)
    for s in (-1, 1):
        for k in range(5):
            yy = -HD + .1 + k * .17
            d = sx_(d, -S_(q, (s * (HW - .16), yy, .62), (s * (HW - .155), yy + .01, .44), .005, .003), .015)
    # 고르지 않은 속 (낮은 주파수 울퉁불퉁)
    return d - .006 * tex.fbm(q * 9, 1.0, 2, seed=4)
frame = sdf_obj('Lounge_SofaFrame', frame_sdf, (SX - HW - .05, SY - HD - .05, .1), (SX + HW + .05, SY + HD + .05, .82), .006, 7000)

def cushion_sdf_fn(cx, dent):
    hw, hd = .355, .30
    def fn(p):
        q = L(p) - np.array([cx, -.07, 0]); x, y, z = q[:, 0], q[:, 1], q[:, 2]
        crown = .03 * np.clip(1 - (x / hw) ** 2, 0, 1) ** .7 * np.clip(1 - (y / hd) ** 2, 0, 1) ** .7
        dz = dent[2] * np.exp(-((x - dent[0]) / .14) ** 2 - ((y - dent[1]) / .16) ** 2)        # 앉았던 자리 눌림
        top = .555 + crown - dz + .004 * tex.fbm(q * 14, 1.0, 2, seed=int(cx * 100) % 7)
        rect = np.hypot(np.maximum(np.abs(x) - (hw - .06), 0), np.maximum(np.abs(y) - (hd - .06), 0)) - .06
        d = sx_(sx_(rect, z - top, .045), .40 - z, .03)
        return d
    return fn
cushions, pipings = [], []
for i, (cx, dent) in enumerate(((-.39, (.04, -.05, .022)), (.39, (-.06, .02, .014)))):
    o = sdf_obj(f'Lounge_SofaCushion{i}', cushion_sdf_fn(cx, dent), (SX + cx - .4, SY - .07 - .35, .38), (SX + cx + .4, SY - .07 + .35, .6), .004, 2600)
    # 주름: 앞 모서리 · 눌린 자리에서 퍼지는 주름
    c0 = Vector((SX + cx + dent[0], SY - .07 + dent[1], .56))
    for k in range(5):
        a = TAU * k / 5 + .4 * i
        p0 = c0 + Vector((math.cos(a) * .05, math.sin(a) * .05, 0)); p1 = c0 + Vector((math.cos(a) * .17, math.sin(a) * .15, 0))
        a_, b_ = odd.project(o, [p0, p1]); odd.crease(o, a_, b_, .008, .0025)
    cushions.append(o)
    # 파이핑: 쿠션 위 · 아래 둘레를 따라 도는 가는 관
    for zl, inset in ((.548, .0), (.405, .0)):
        loop = []
        for k in range(64):
            a = TAU * k / 64; ca, sa = math.cos(a), math.sin(a)
            ex = np.sign(ca) * min(1, abs(ca) * 2.2) * .355; ey = np.sign(sa) * min(1, abs(sa) * 2.2) * .30
            loop.append(Vector((SX + cx + ex, SY - .07 + ey, zl)))
        pts_ = odd.project(o, loop)
        pipings.append(odd.curve_tube('_pipe', pts_ + [pts_[0]], .0045, res=2, bevel_res=2))
piping = odd.join(pipings, 'Lounge_SofaPiping')
buttons = []
for t in TUFT:
    c = t + np.array([SX, SY, 0]) + np.array([0, -.008, 0])
    buttons.append(sdf_obj('_btn', (lambda p, c=c: E_(p, c, (.011, .007, .011))), c - .02, c + .02, .0012, 60, subdiv=0))
sofa_buttons = odd.join(buttons, 'Lounge_SofaButtons')
legs = []
for sxl in (-1, 1):
    for syl in (-1, 1):
        c = np.array([SX + sxl * (HW - .07), SY + syl * (HD - .07), 0])
        def legfn(p, c=c):
            d = E_(p, c + np.array([0, 0, .065]), (.042, .042, .05))
            d = sm(d, S_(p, c + np.array([0, 0, .1]), c + np.array([0, 0, .13]), .035, .03), .015)
            return sm(d, E_(p, c + np.array([0, 0, .02]), (.03, .03, .022)), .015)
        legs.append(sdf_obj('_leg', legfn, c - np.array([.06, .06, 0]), c + np.array([.06, .06, .16]), .0015, 500))
sofa_legs = odd.join(legs, 'Lounge_SofaLegs')

# =====================================================================================
# 2. 사이드 테이블 (월넛): 상판(둥근 모서리 · 깨진 모서리) · 에이프런 · 서랍(틈 · 놋쇠 손잡이) · 가늘어지는 다리
# =====================================================================================
TX, TY = .84, .66
def table_sdf(p):
    q = p - np.array([TX, TY, 0])
    top = B_(q, (0, 0, .595), (.23, .2, .016), None, .007)
    top = sx_(top, -E_(q, (.235, -.205, .61), (.018, .014, .01)), .004)                              # 깨진 모서리
    apron = B_(q, (0, 0, .535), (.2, .17, .045), None, .004)
    apron = sx_(apron, -B_(q, (0, -.172, .535), (.135, .01, .032), None, .002), .002)                # 서랍 자리 (틈)
    d = sm(top, apron, .006)
    for sxl in (-1, 1):
        for syl in (-1, 1):
            c = np.array([sxl * .185, syl * .155])
            t = np.clip((.58 - q[:, 2]) / .58, 0, 1)
            hwl = .017 - .007 * t
            leg = np.maximum(np.maximum(np.abs(q[:, 0] - c[0]) - hwl, np.abs(q[:, 1] - c[1]) - hwl), np.maximum(q[:, 2] - .58, -q[:, 2])) - .003
            d = sm(d, leg, .006)
    return d
table = sdf_obj('Lounge_Table', table_sdf, (TX - .26, TY - .23, -.01), (TX + .26, TY + .23, .62), .0025, 3200)
drawer = sdf_obj('Lounge_TableDrawer', lambda p: B_(p - np.array([TX, TY, 0]), (0, -.171, .535), (.132, .006, .029), None, .002), (TX - .15, TY - .19, .5), (TX + .15, TY - .15, .57), .0012, 500)
knob = sdf_obj('Lounge_TableKnob', lambda p: sm(E_(p, (TX, TY - .186, .536), (.009, .006, .009)), S_(p, (TX, TY - .178, .536), (TX, TY - .184, .536), .004, .004), .003),
               (TX - .02, TY - .2, .52), (TX + .02, TY - .17, .55), .0005, 200, subdiv=0)

# =====================================================================================
# 3. 램프: 도자기 몸통(꽃병 모양) · 놋쇠 목 · 하프 · 전구 · 두께 있는 천 갓(위아래 말린 테)
# =====================================================================================
LX, LY = TX - .05, TY + .04; LZ = .611
def lamp_base_sdf(p):
    q = p - np.array([LX, LY, LZ])
    d = E_(q, (0, 0, .11), (.075, .075, .1))
    d = sm(d, S_(q, (0, 0, .015), (0, 0, .04), .055, .06), .02)
    d = sm(d, S_(q, (0, 0, .19), (0, 0, .24), .028, .02), .02)
    return d
lamp_base = sdf_obj('Lounge_LampBase', lamp_base_sdf, (LX - .1, LY - .1, LZ - .01), (LX + .1, LY + .1, LZ + .26), .0015, 1400)
neck = odd.curve_tube('Lounge_LampNeck', [Vector((LX, LY, LZ + .23)), Vector((LX, LY, LZ + .3)), Vector((LX, LY, LZ + .36))], .006, res=4, bevel_res=3)
harp = odd.curve_tube('Lounge_LampHarp', [Vector((LX - .07, LY, LZ + .3)), Vector((LX - .072, LY, LZ + .42)), Vector((LX, LY, LZ + .5)), Vector((LX + .072, LY, LZ + .42)), Vector((LX + .07, LY, LZ + .3))], .0018, res=8, bevel_res=2)
bulb = sdf_obj('Lounge_LampBulb', lambda p: sm(E_(p, (LX, LY, LZ + .41), (.03, .03, .036)), S_(p, (LX, LY, LZ + .36), (LX, LY, LZ + .385), .013, .013), .01),
               (LX - .04, LY - .04, LZ + .34), (LX + .04, LY + .04, LZ + .46), .0012, 400, subdiv=0)
prof = [(.105, .345), (.108, .342), (.112, .345), (.111, .35), (.085, .51), (.083, .515), (.086, .519), (.089, .515)]   # 아래 테 말림 → 옆면 → 위 테 말림
NPL = 26                                                                                       # 주름 수 (콘셉트: 주름 잡힌 호박색 천 갓)
def _pleat(t):
    return (abs(math.sin(t * NPL * math.pi)) - .64) * .045
rings = [[Vector((LX + r * (1 + _pleat(k / 208) * (1 if .2 < z < .51 else .25)) * math.cos(TAU * k / 208), LY + r * (1 + _pleat(k / 208) * (1 if .2 < z < .51 else .25)) * math.sin(TAU * k / 208), LZ + z)) for k in range(208)] for r, z in prof]
shade = odd.loft('Lounge_LampShade', rings); odd.solidify(shade, .0018, offset=-1); odd.subsurf(shade, 1)

# =====================================================================================
# 4. 전선: 램프 뒤 → 테이블 뒷다리 → 바닥에서 처지며 → 걸레받이의 콘센트에 꽂힌 플러그 + 여분 고리
# =====================================================================================
OUT_X = .55
cpts = [Vector((LX + .02, LY + .07, LZ + .02)), Vector((LX + .06, LY + .16, LZ - .01)), Vector((TX + .17, TY + .16, .45)), Vector((TX + .18, TY + .17, .2)),
        Vector((TX + .14, TY + .22, .006)), Vector((.72, .9, .006)), Vector((.62, .93, .02)), Vector((OUT_X + .02, WALL_Y - .045, .1)), Vector((OUT_X, WALL_Y - .03, .11))]
cord, _ = odd.spline(cpts, 60)
cable = odd.curve_tube('Lounge_Cable', cord, .0028, res=2, bevel_res=2)
loopc = [Vector((.66 + .05 * math.cos(TAU * k / 14), .86 + .035 * math.sin(TAU * k / 14), .004 + .002 * k / 14)) for k in range(15)]
cable_loop = odd.curve_tube('Lounge_CableLoop', loopc, .0028, res=4, bevel_res=2)
plug = sdf_obj('Lounge_Plug', lambda p: B_(p, (OUT_X, WALL_Y - .02, .11), (.016, .012, .022), None, .004), (OUT_X - .03, WALL_Y - .04, .08), (OUT_X + .03, WALL_Y, .14), .0008, 300)
outlet = sdf_obj('Lounge_Outlet', lambda p: B_(p, (OUT_X, WALL_Y - .006, .11), (.035, .004, .055), None, .003), (OUT_X - .05, WALL_Y - .02, .04), (OUT_X + .05, WALL_Y + .01, .18), .0008, 300)

# =====================================================================================
# 5. 벽: 걸레받이 · 웨인스코팅(두드러진 판 · 몰딩) · 체어 레일 · 벽지 면 + 창(틀 · 깊은 창턱 · 유리)
# =====================================================================================
WIN = (.38, 1.12, 1.0, 1.95)        # 창 x0, x1, z0, z1
def wall_sdf(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    slab = np.maximum(np.maximum(y - (WALL_Y + .06), WALL_Y - y), np.maximum(np.maximum(X0 - x, x - X1), np.maximum(-z, z - 2.35)))
    hole = np.maximum(np.maximum(WIN[0] - x, x - WIN[1]), np.maximum(WIN[2] - z, z - WIN[3]))
    return np.maximum(slab, -hole)
wall = sdf_obj('Lounge_Wall', wall_sdf, (X0 - .02, WALL_Y - .02, -.02), (X1 + .02, WALL_Y + .08, 2.37), .01, 2400, subdiv=0)
def mold(name, z, prof, x0=X0, x1=X1):
    """벽을 따라 가는 몰딩 (단면 (앞으로 나온 깊이, 높이) 로프트)."""
    rings = []
    for xx in np.linspace(x0, x1, 2):
        rings.append([Vector((xx, WALL_Y - d, z + h)) for d, h in prof])
    o = odd.loft(name, rings, closed=False); return o
base_m = mold('Lounge_Baseboard', 0, [(0, .16), (.006, .158), (.012, .15), (.014, .13), (.018, .12), (.018, .01), (.02, .0), (0, 0)])
rail_m = mold('Lounge_ChairRail', .88, [(0, .0), (.012, .005), (.022, .018), (.024, .03), (.016, .042), (.02, .052), (.012, .062), (0, .066)])
panels = []
for k in range(5):
    x0 = X0 + .08 + k * .54; x1 = x0 + .44
    if x1 > WIN[0] - .02 and x0 < WIN[1] + .02 and False: continue
    def pfn(p, x0=x0, x1=x1):
        q = p - np.array([(x0 + x1) / 2, WALL_Y, .52])
        raised = B_(q, (0, -.006, 0), ((x1 - x0) / 2, .008, .28), None, .006)
        bevel = B_(q, (0, -.012, 0), ((x1 - x0) / 2 - .05, .006, .23), None, .01)
        return sm(raised, bevel, .02)
    panels.append(sdf_obj('_panel', pfn, (x0 - .02, WALL_Y - .04, .2), (x1 + .02, WALL_Y + .01, .84), .003, 500, subdiv=0))
wainscot = odd.join(panels, 'Lounge_Wainscot')
def window_sdf(p):
    q = p
    frame_ = np.maximum(np.maximum(np.maximum(WIN[0] - .05 - q[:, 0], q[:, 0] - WIN[1] - .05), np.maximum(WIN[2] - .05 - q[:, 2], q[:, 2] - WIN[3] - .05)), np.abs(q[:, 1] - (WALL_Y - .01)) - .025)
    inner = np.maximum(np.maximum(WIN[0] - q[:, 0], q[:, 0] - WIN[1]), np.maximum(WIN[2] - q[:, 2], q[:, 2] - WIN[3]))
    d = np.maximum(frame_, -inner)
    for xx in ((WIN[0] + WIN[1]) / 2,):
        d = np.minimum(d, odd.sd_box(q, (xx, WALL_Y + .02, (WIN[2] + WIN[3]) / 2), (.018, .02, (WIN[3] - WIN[2]) / 2), None, .003))
    for zz in (WIN[2] + (WIN[3] - WIN[2]) * .5,):
        d = np.minimum(d, odd.sd_box(q, ((WIN[0] + WIN[1]) / 2, WALL_Y + .02, zz), ((WIN[1] - WIN[0]) / 2, .02, .018), None, .003))
    sill = odd.sd_box(q, ((WIN[0] + WIN[1]) / 2, WALL_Y - .03, WIN[2] - .035), ((WIN[1] - WIN[0]) / 2 + .1, .08, .02), None, .006)
    return np.minimum(d, sill)
window = sdf_obj('Lounge_Window', window_sdf, (WIN[0] - .2, WALL_Y - .14, WIN[2] - .1), (WIN[1] + .2, WALL_Y + .06, WIN[3] + .1), .004, 2200, subdiv=0)
glass = odd.mesh_obj('Lounge_Glass', [(WIN[0], WALL_Y + .035, WIN[2]), (WIN[1], WALL_Y + .035, WIN[2]), (WIN[1], WALL_Y + .035, WIN[3]), (WIN[0], WALL_Y + .035, WIN[3])], [(0, 1, 2, 3)])

# =====================================================================================
# 6. 커튼: 주름 잡힌 천(위 고정) → 천 시뮬레이션으로 무겁게 늘어뜨림 · 고르지 않은 밑단 + 놋쇠 봉 · 고리 · 끝 장식
# =====================================================================================
RODZ = 2.08
def curtain(name, x0, x1, seed, yb=.12, ampk=1.0):
    r_ = np.random.default_rng(seed); cols, rows = 46, 44; verts = []; faces = []
    ph = np.cumsum(r_.uniform(.6, 1.4, 12)); ph = ph / ph[-1] * 5.0; amp = r_.uniform(.025, .06, 12)
    for r in range(rows):
        t = r / (rows - 1); z = RODZ - .03 - t * (RODZ - .03 + .02) - (r_.uniform(0, .025) if r == rows - 1 else 0)
        for c in range(cols):
            u = c / (cols - 1); x = x0 + (x1 - x0) * u
            kk = min(11, int(np.searchsorted(ph, u * 5.0)))                                # 불규칙한 주름 (간격 · 깊이 제각각)
            y = WALL_Y - yb - ampk * amp[kk] * math.sin(np.interp(u * 5.0, np.concatenate([[0], ph]), np.arange(13) * math.pi)) * (1 - .35 * t) + .01 * math.sin(t * 5 + seed)
            verts.append((x, y, z))
    for r in range(rows - 1):
        for c in range(cols - 1):
            a = r * cols + c; faces.append((a, a + 1, a + cols + 1, a + cols))
    o = odd.mesh_obj(name, verts, faces)
    uv = o.data.uv_layers.new(name='UVMap')
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            vi = o.data.loops[li].vertex_index; uv.data[li].uv = ((vi % cols) / (cols - 1) * 2, 1 - (vi // cols) / (rows - 1) * 4)
    odd.vgroup(o, 'pin', [1.0 if i < cols else 0.0 for i in range(len(verts))])
    return o
floor_c = odd.mesh_obj('_floorcol', [(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [(0, 1, 2, 3)])
wall_c = odd.mesh_obj('_wallcol', [(-3, WALL_Y, 0), (3, WALL_Y, 0), (3, WALL_Y, 3), (-3, WALL_Y, 3)], [(0, 1, 2, 3)])
cur_l = curtain('Lounge_CurtainL', WIN[0] - .3, WIN[0] + .1, 3)
cur_r = curtain('Lounge_CurtainR', WIN[1] - .1, WIN[1] + .28, 4)
sheer = curtain('Lounge_Sheer', WIN[0] - .02, WIN[1] + .02, 7, yb=.055, ampk=.35)                 # 창 안쪽 얇은 레이스 (콘셉트)
for o in (cur_l, cur_r, sheer):
    odd.cloth_sim(o, frames=55, pin_group='pin', colliders=[floor_c, wall_c], quality=7, mass=.6, tension=25, bending=6, collide_dist=.004, thickness_outer=.004)
    odd.solidify(o, .004, offset=-1); odd.subsurf(o, 1)
odd.delete(floor_c); odd.delete(wall_c)
rod = odd.curve_tube('Lounge_Rod', [Vector((WIN[0] - .36, WALL_Y - .12, RODZ)), Vector((WIN[1] + .34, WALL_Y - .12, RODZ))], .012, res=2, bevel_res=4)
fin = []
for xx in (WIN[0] - .38, WIN[1] + .36):
    fin.append(sdf_obj('_fin', (lambda p, xx=xx: sm(E_(p, (xx, WALL_Y - .12, RODZ), (.03, .03, .03)), S_(p, (xx + np.sign(xx) * .0, WALL_Y - .12, RODZ), (xx + np.sign(xx - .7) * .03, WALL_Y - .12, RODZ), .012, .02), .01)),
                       (xx - .05, WALL_Y - .17, RODZ - .05), (xx + .05, WALL_Y - .07, RODZ + .05), .0015, 300))
finials = odd.join(fin, 'Lounge_RodFinials')

# ---------- 액자: 소파 위 벽에 조금 비뚤게 걸린 낡은 금박 액자 2개 + 그림 판 (콘셉트: 그림이 많이 걸린 어두운 벽) ----------
FRAMES = [(-.64, 1.36, .36, .46, .02), (-.12, 1.30, .30, .36, -.015)]
frames_, pics = [], []
for k, (fx, fz, fw, fh, rot) in enumerate(FRAMES):
    cr, sr_ = math.cos(rot), math.sin(rot); Rf = np.array([[cr, 0, -sr_], [0, 1, 0], [sr_, 0, cr]])
    def ffn(p, fx=fx, fz=fz, fw=fw, fh=fh, Rf=Rf):
        q = (p - np.array([fx, WALL_Y - .018, fz])) @ Rf
        outer = B_(q, (0, 0, 0), (fw / 2, .016, fh / 2), None, .006)
        inner = B_(q, (0, -.02, 0), (fw / 2 - .045, .03, fh / 2 - .045), None, .003)
        bead = B_(q, (0, -.012, 0), (fw / 2 - .02, .006, fh / 2 - .02), None, .004)               # 안쪽 테 (몰딩 단)
        return sx_(sm(outer, bead, .006), -inner, .004)
    frames_.append(sdf_obj(f'_frame{k}', ffn, (fx - fw / 2 - .05, WALL_Y - .06, fz - fh / 2 - .05), (fx + fw / 2 + .05, WALL_Y + .01, fz + fh / 2 + .05), .002, 1200, subdiv=0))
    hw_, hh_ = fw / 2 - .043, fh / 2 - .043
    corners = [np.array([-hw_, -.006, -hh_]), np.array([hw_, -.006, -hh_]), np.array([hw_, -.006, hh_]), np.array([-hw_, -.006, hh_])]
    pv = [tuple(np.array([fx, WALL_Y - .018, fz]) + Rf @ c_) for c_ in corners]
    pic = odd.mesh_obj(f'Lounge_Picture{k}', pv, [(0, 1, 2, 3)])
    if np.mean(odd.nrm(pic)[:, 1]) > 0: odd.recalc(pic, inside=True)
    uvp = pic.data.uv_layers.new(name='UVMap')
    for li, uvv in zip(pic.data.polygons[0].loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]): uvp.data[li].uv = uvv
    pics.append(pic)
picture_frames = odd.join(frames_, 'Lounge_PictureFrames')
# ---------- 소파 오른쪽 팔걸이 · 등받이에 걸친 무늬 담요 (천 시뮬레이션) ----------
BW, BD = .9, .62; nb_x, nb_y = 46, 32; bverts = []; bfaces = []
for j in range(nb_y):
    for i in range(nb_x):
        u = i / (nb_x - 1) - .5; v = j / (nb_y - 1) - .5
        a_ = .35; x_ = u * BW; y_ = v * BD
        bverts.append((SX + HW - .2 + x_ * math.cos(a_) - y_ * math.sin(a_), SY + .02 + x_ * math.sin(a_) + y_ * math.cos(a_), .95 + .02 * math.sin(u * 6)))
for j in range(nb_y - 1):
    for i in range(nb_x - 1):
        a0 = j * nb_x + i; bfaces.append((a0, a0 + 1, a0 + nb_x + 1, a0 + nb_x))
throw = odd.mesh_obj('Lounge_Throw', bverts, bfaces)
uvt = throw.data.uv_layers.new(name='UVMap')
for poly in throw.data.polygons:
    for li in poly.loop_indices:
        vi = throw.data.loops[li].vertex_index; uvt.data[li].uv = ((vi % nb_x) / (nb_x - 1), (vi // nb_x) / (nb_y - 1))
_fc = odd.mesh_obj('_floorcol2', [(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [(0, 1, 2, 3)])
odd.cloth_sim(throw, frames=45, colliders=[frame] + cushions + [_fc], quality=7, mass=.25, tension=18, bending=.6, collide_dist=.004, thickness_outer=.006)
odd.delete(_fc)
odd.solidify(throw, .004, offset=1); odd.subsurf(throw, 1)

# =====================================================================================
# 7. 러그: 두께 1.2 cm 슬래브 · 물결치는 가장자리 · 말린 모서리 + 양 끝 술
# =====================================================================================
RW, RD = .95, .62; RCX, RCY = -.15, -.12
nx, ny = 64, 44; verts = []; faces = []
for j in range(ny):
    for i in range(nx):
        u = i / (nx - 1) * 2 - 1; v = j / (ny - 1) * 2 - 1
        x = RCX + u * RW + .006 * math.sin(v * 9 + 1.3) * (abs(u) > .97); y = RCY + v * RD + .007 * math.sin(u * 11) * (abs(v) > .97)
        lift = .12 * max(0, (u - .82) / .18) ** 2 * max(0, (-v - .7) / .3) ** 2          # 오른쪽 앞 모서리가 말려 올라감
        verts.append((x, y, .012 + lift + .0015 * math.sin(u * 7) * math.sin(v * 5)))
for j in range(ny - 1):
    for i in range(nx - 1):
        a = j * nx + i; faces.append((a, a + 1, a + nx + 1, a + nx))
rug = odd.mesh_obj('Lounge_Rug', verts, faces)
uv = rug.data.uv_layers.new(name='UVMap')
for poly in rug.data.polygons:
    for li in poly.loop_indices:
        vi = rug.data.loops[li].vertex_index; uv.data[li].uv = ((vi % nx) / (nx - 1), (vi // nx) / (ny - 1))
odd.solidify(rug, .011, offset=-1)
fr = []
for s in (-1, 1):
    for k in range(70):
        y = RCY - RD + .02 + k * (2 * RD - .04) / 69; x = RCX + s * RW
        L_ = rng.uniform(.04, .06); bend = rng.uniform(-.01, .01)
        lift = .12 * max(0, (1 - .82) / .18) ** 2 * max(0, (-(y - RCY) / RD - .7) / .3) ** 2 if s > 0 else 0
        fr.append(odd.curve_tube('_fr', [Vector((x, y, .006 + lift)), Vector((x + s * L_ * .5, y + bend * .5, .003 + lift * .6)), Vector((x + s * L_, y + bend, .002))], .0011, res=2, bevel_res=1))
fringe = odd.join(fr, 'Lounge_RugFringe')

# =====================================================================================
# 8. 책: 하나하나 크기 · 두께가 다르고(표지판 + 안쪽으로 들어간 종이 묶음), 기울고 휜 표지 / LP 슬리브: 고르지 않게 기대어 쌓임
# =====================================================================================
def book(name, c, size, rot_z=0.0, tilt=0.0, bend=0.0):
    w, d, h = size                                                     # 가로(앞뒤) · 세로 · 두께
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, math.cos(tilt), -math.sin(tilt)], [0, math.sin(tilt), math.cos(tilt)]])
    def fn(p):
        q = (p - np.array(c)) @ R
        cover = B_(q, (0, 0, 0), (w / 2, d / 2, h / 2), None, .0025)
        pages = B_(q, (.004, 0, 0), (w / 2 - .002, d / 2 - .004, h / 2 - .0028), None, .001)
        groove = B_(q, (.006, 0, 0), (w / 2 - .0035, d / 2 + .01, h / 2 - .0035), None, .001)
        d_ = sx_(cover, -groove, .0008)
        d_ = np.minimum(d_, pages)
        return d_ - bend * np.clip((q[:, 0] + w / 2) / w, 0, 1) ** 2 * (q[:, 2] > 0)
    ext = np.array([w, d, h]).max() * .8 + .02
    o = sdf_obj(name, fn, np.array(c) - ext, np.array(c) + ext, .0012, 700, subdiv=0)
    o['size'] = list(size); o['c'] = list(c); o['R'] = R.tolist()
    return o
books = []
zc = .0
for k, (w, d, h, rz) in enumerate([(.24, .17, .045, .05), (.22, .15, .03, -.12), (.2, .14, .038, .2), (.18, .125, .022, -.05), (.17, .12, .032, .3)]):
    books.append(book(f'Lounge_Book{k}', (1.08 - .02 * k, .38 + .01 * k, zc + h / 2), (w, d, h), rz, 0, .004 * (k == 1))); zc += h
books.append(book('Lounge_Book5', (1.2, .52, .12), (.26, .18, .035), 1.5, -1.2))                                  # 테이블 다리에 기대 선 책
for k, (w, d, h, rz) in enumerate([(.19, .13, .028, .1), (.17, .12, .02, -.15)]):
    books.append(book(f'Lounge_TBook{k}', (TX + .07, TY - .06, .611 + h / 2 + k * .028), (w, d, h), rz))
sleeves = []
for k in range(11):                                                                                          # 바닥에 납작하게 쌓인 LP (가장자리가 고르지 않게)
    phi = rng.uniform(-.25, .25); c = np.array([.40 + rng.uniform(-.015, .015), .06 + rng.uniform(-.015, .015), .0045 + k * .0042])
    R = np.array([[math.cos(phi), -math.sin(phi), 0], [math.sin(phi), math.cos(phi), 0], [0, 0, 1]])
    def sfn(p, c=c, R=R, k=k):
        q = (p - c) @ R
        return B_(q, (0, 0, 0), (.1575, .1575, .0018), None, .0012)
    o = sdf_obj(f'_stack{k}', sfn, c - .2, c + .2, .0014, 260, subdiv=0)
    o['c'] = c.tolist(); o['R'] = R.tolist(); sleeves.append(o)
for k in range(9):                                                                                           # 소파 왼쪽 팔걸이에 기대어 선 LP
    ang = math.radians(70 + k * 1.6 + rng.uniform(-1.5, 1.5)); x = SX - HW - .05 - k * .007
    c = np.array([x - .16 * math.cos(ang), .25 + k * .004 + rng.uniform(-.008, .008), .158 * math.sin(ang)])
    R = np.array([[math.cos(ang), 0, -math.sin(ang)], [0, 1, 0], [math.sin(ang), 0, math.cos(ang)]])
    def sfn(p, c=c, R=R, k=k):
        q = (p - c) @ R
        warp_ = .004 * np.sin(q[:, 1] * 8 + k) * (q[:, 0] / .16)
        return B_(q - np.stack([np.zeros(len(q)), np.zeros(len(q)), warp_], 1), (0, 0, 0), (.1575, .1575, .0018), None, .0012)
    o = sdf_obj(f'_sleeve{k}', sfn, c - .2, c + .2, .0014, 300, subdiv=0)
    o['c'] = c.tolist(); o['R'] = R.tolist(); sleeves.append(o)

# =====================================================================================
# 9. 마루: 널(폭 9 cm · 길이 제각각) — 널마다 높이 · 기울기가 조금씩 다르고 사이에 틈
# =====================================================================================
planks = []
y = -.85
while y < WALL_Y:
    x = X0 - rng.uniform(0, .8)
    while x < X1:
        L_ = rng.uniform(.9, 1.7); x0, x1 = max(x, X0), min(x + L_, X1)
        if x1 - x0 > .05:
            h = rng.uniform(-.0012, .0012); tl = rng.uniform(-.004, .004)
            verts = [(x0 + .0015, y + .0015, h), (x1 - .0015, y + .0015, h + tl * (x1 - x0)), (x1 - .0015, y + .088, h + tl * (x1 - x0)), (x0 + .0015, y + .088, h),
                     (x0 + .0015, y + .0015, -.02), (x1 - .0015, y + .0015, -.02), (x1 - .0015, y + .088, -.02), (x0 + .0015, y + .088, -.02)]
            faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            planks.append(odd.mesh_obj('_pl', verts, faces, smooth=False))
        x += L_
    y += .0895
floor = odd.join(planks, 'Lounge_Floor')
odd.bevel(floor, .0015, 2, math.radians(30))

if STAGE == 'clay':
    odd.lookdev_scene('studio', size=2.6, floor=False)
    m = odd.Mat('clay'); m.set(Base_Color=(.7, .66, .6, 1), Roughness=.7)
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.data.materials]: o.data.materials.append(m.m)
    print(odd.render_views(os.path.join(odd.OUT, 'lounge_clay'), Vector((0, .3, .8)), 2.2, views=('front', 'q34', 'close:0.5:20'), res=(640, 480)))
    sys.exit(0)

# =====================================================================================
# 10. 재질 · 텍스처
# =====================================================================================
from PIL import Image, ImageDraw, ImageFont
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FS = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
BUDGET = {'Lounge_SofaFrame': 22000, 'Lounge_Wall': 2000, 'Lounge_Window': 6000, 'Lounge_Table': 7000, 'Lounge_CurtainL': 14000, 'Lounge_CurtainR': 14000, 'Lounge_LampBase': 3000}
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name in BUDGET:
        t = sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
        if t > BUDGET[o.name] * 1.05: odd.decimate(o, BUDGET[o.name] / t); o.data.shade_smooth()

def S_of(o, size, angle=60, margin=.004, keep_uv=False):
    if not keep_uv or not o.data.uv_layers: odd.uv_smart(o, angle, margin)
    return tex.Surf(o, size)

def wood(p, axis, ring=.006, seed=0, dark=(.16, .085, .045), light=(.36, .2, .1)):
    """월넛 결: 결 방향 axis로 긴 나이테 + 잔결 (3D)."""
    a = np.array(axis, float); a /= np.linalg.norm(a); b = np.cross(a, [0, 0, 1.0] if abs(a[2]) < .9 else [1.0, 0, 0]); b /= np.linalg.norm(b); c = np.cross(a, b)
    pa, pb, pc = p @ a, p @ b, p @ c
    warp_ = tex.fbm(np.stack([pa * 2, pb * 30, pc * 30], 1), 1.0, 3, seed=seed) * 1.2
    r = np.hypot(pb + .05 + seed * .013, pc - .03) / ring + warp_
    rings = (np.sin(r * TAU) * .5 + .5) ** 2
    streak = tex.fbm(np.stack([pa * 6, pb * 400, pc * 400], 1), 1.0, 2, seed=seed + 3) * .5 + .5
    t = np.clip(rings * .55 + streak * .45, 0, 1)
    col = np.array(dark)[None, :] * (1 - t[:, None]) + np.array(light)[None, :] * t[:, None]
    return col, rings, streak

def scratches(p, count, area_c, area_r, seed, width=.0004, length=(.01, .06)):
    r_ = np.random.default_rng(seed); out = np.zeros(len(p))
    for _ in range(count):
        c = np.array(area_c) + r_.uniform(-1, 1, 3) * np.array(area_r); d = r_.normal(size=3); d /= np.linalg.norm(d)
        L_ = r_.uniform(*length); dist, _ = tex.seg_dist(p, c, c + d * L_)
        out = np.maximum(out, np.clip(1 - dist / width, 0, 1) * r_.uniform(.3, 1))
    return out

# ---------- 벨벳 (소파 · 쿠션 · 파이핑 · 단추) ----------
def velvet(o, name, size, base=(.22, .02, .035), seed=0):
    S = S_of(o, size); p = S.p
    crush = tex.fbm(p * np.array([30, 30, 60]), 1.0, 4, seed=seed)                     # 눌린 결 (방향 따라 빛이 달라 보이는 얼룩)
    top = np.clip(S.n[:, 2], 0, 1)
    edge_wear = np.zeros(len(p))
    if 'Frame' in name:
        for sx in (-1, 1):                                                            # 팔걸이 말림 위가 닳았다
            d, _ = tex.seg_dist(p, (SX + sx * (HW - .045), SY - HD + .03, .73), (SX + sx * (HW - .045), SY + HD - .06, .75))
            edge_wear = np.maximum(edge_wear, np.clip(1 - d / .07, 0, 1) * top)
    if 'Cushion' in name:
        edge_wear = np.clip((SY - .07 - .25 - p[:, 1]) / .06 + 1, 0, 1) * (p[:, 2] > .5)  # 앞 모서리
    worn = np.clip(edge_wear * (tex.fbm(p, 40, 3, seed=seed + 1) * .6 + .7), 0, 1)
    col = np.array(base)[None, :] * (1 + .22 * crush)[:, None]
    col = col * (1 - worn[:, None] * .45) + np.array([.36, .12, .13])[None, :] * (worn[:, None] * .45)
    hh = crush * .5 + tex.vnoise(p, 900, seed=seed + 2) * .25
    m = tex.material(name, TD, S.img(np.clip(col, 0, 1)), S.img(.62 + .15 * worn), tex.h2n(S.img(hh), .8), sheen=(.42, .45, (.58, .17, .2, 1)))
    o.data.materials.append(m); return m
velvet(frame, 'Lounge_SofaVelvet', 2048)
cm_ = velvet(cushions[0], 'Lounge_SofaCushion', 1024, seed=5)
S_of(cushions[1], 64); cushions[1].data.materials.append(cm_)
pv = odd.gltf_material('Lounge_Piping', base_value=(.17, .018, .03, 1), rough_value=.6, sheen=(.4, .4, (.5, .16, .2, 1)))
piping.data.materials.append(pv); sofa_buttons.data.materials.append(pv)
S = S_of(sofa_legs, 512); col, rings, st = wood(S.p, (0, 0, 1), .004, 3)
sofa_legs.data.materials.append(tex.material('Lounge_SofaLegs', TD, S.img(col * .8), S.img(.32 + .2 * st), tex.h2n(S.img(rings * .3), .6), coat=(.6, .2)))

# ---------- 사이드 테이블: 월넛 · 바니시 긁힘 · 모서리 닳음 · 컵 자국 ----------
S = S_of(table, 2048); p = S.p
col, rings, st = wood(p, (1, 0, 0), .005, 7)
scr = scratches(p, 70, (TX, TY, .612), (.22, .19, .001), 9)
ring_mark = np.clip(1 - np.abs(np.hypot(p[:, 0] - (TX - .12), p[:, 1] - (TY - .09)) - .038) / .003, 0, 1) * (p[:, 2] > .605) * (tex.fbm(p, 200, 2, seed=4) > -.3)
edge = np.clip(1 - np.abs(np.abs(p[:, 0] - TX) - .233) / .006, 0, 1) + np.clip(1 - np.abs(np.abs(p[:, 1] - TY) - .2) / .006, 0, 1)
edge = np.clip(edge * (np.abs(p[:, 2] - .6) < .02), 0, 1)
col = col * (1 - .35 * ring_mark[:, None]) * (1 + .35 * scr[:, None]) * (1 + .5 * edge[:, None])
rgh = .28 + .25 * scr + .3 * edge + .15 * ring_mark + .1 * st
tm = tex.material('Lounge_Walnut', TD, S.img(np.clip(col, 0, 1)), S.img(np.clip(rgh, 0, 1)), tex.h2n(S.img(rings * .25 - scr * .8), .9), coat=(.5, .15))
table.data.materials.append(tm)
S = S_of(drawer, 512); col, rings, st = wood(S.p, (1, 0, 0), .005, 8)
drawer.data.materials.append(tex.material('Lounge_Drawer', TD, S.img(col), S.img(.3 + .1 * st), tex.h2n(S.img(rings * .25), .9), coat=(.5, .15)))
brass = odd.gltf_material('Lounge_Brass', base_value=(.78, .6, .3, 1), rough_value=.32, metal_value=1.0)
oldbrass = odd.gltf_material('Lounge_OldBrass', base_value=(.55, .42, .22, 1), rough_value=.45, metal_value=1.0)
for o in (knob, neck, harp): o.data.materials.append(brass)
for o in (rod, finials): o.data.materials.append(oldbrass)

# ---------- 램프: 유약 도자기(빙열 · 흘러내린 유약) · 전구(따뜻한 빛) · 리넨 갓(안쪽이 은은히 밝다) ----------
S = S_of(lamp_base, 1024); p = S.p
f1, f2 = None, None
crack = np.abs(tex.vnoise(p, 260, seed=2)) < .04
drip = np.clip(tex.fbm(p * np.array([60, 60, 8]), 1.0, 3, seed=3), 0, 1)
col = np.array([.52, .27, .10])[None, :] * (1 + .35 * drip[:, None]) * np.where(crack[:, None], .7, 1.0)   # 호박 · 황토 유약 (콘셉트)
lamp_base.data.materials.append(tex.material('Lounge_Ceramic', TD, S.img(col), S.img(.12 + .1 * crack), tex.h2n(S.img(crack.astype(float) * .4 + drip * .2), 1.0), coat=(1, .05)))
bulb.data.materials.append(odd.gltf_material('Lounge_Bulb', base_value=(1, .9, .7, 1), rough_value=.2, emission=((1, .72, .38, 1), 6.0)))
S = S_of(shade, 1024); p = S.p
inner = (S.n[:, 0] * (p[:, 0] - LX) + S.n[:, 1] * (p[:, 1] - LY)) < 0
weave = (np.sin(np.arctan2(p[:, 1] - LY, p[:, 0] - LX) * 900) * .5 + np.sin(p[:, 2] * 3000) * .5) * .3
col = np.where(inner[:, None], np.array([.98, .74, .42]), np.array([.80, .50, .22]) * (1 - .1 * np.clip(tex.fbm(p, 30, 3, seed=6), 0, 1))[:, None])
emit = np.where(inner[:, None], np.array([1, .66, .32]), np.array([.9, .52, .2]) * .55)                  # 불 켜진 호박색 천 갓 (빛이 천을 통과한다)
shade_m = tex.material('Lounge_Shade', TD, S.img(col), S.img(np.full(len(p), .9)), tex.h2n(S.img(weave), .8), emission=((1, 1, 1, 1), 0.0))
nt = shade_m.node_tree; em = nt.nodes.new('ShaderNodeTexImage'); em.image = tex.load(tex.save(S.img(emit), os.path.join(TD, 'Lounge_Shade_e.jpg')))
nt.links.new(em.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Emission Color']); nt.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.6
shade.data.materials.append(shade_m)

# ---------- 전선 · 플러그 · 콘센트 ----------
S = S_of(cable, 512); braid = np.sin((S.p[:, 0] + S.p[:, 1] + S.p[:, 2]) * 3500) * .5
rub = tex.fbm(S.p, 300, 3, seed=8)
cord_m = tex.material('Lounge_Cord', TD, S.img(np.tile([.03, .03, .033], (len(S.p), 1)) * (1 + .4 * np.clip(rub, 0, 1)[:, None])), S.img(.5 + .15 * rub), tex.h2n(S.img(rub * .2), .6))   # 검은 고무 (콘셉트)
cable.data.materials.append(cord_m); S_of(cable_loop, 64); cable_loop.data.materials.append(cord_m)
plug.data.materials.append(odd.gltf_material('Lounge_Bakelite', base_value=(.03, .03, .03, 1), rough_value=.35))
outlet.data.materials.append(oldbrass)

# ---------- 벽: 다마스크 벽지(누렇게 바램 · 얼룩 · 위쪽 그을음) · 웨인스코팅 · 몰딩 ----------
S = S_of(wall, 2048); p = S.p
u = (p[:, 0] - X0) / .30; v = p[:, 2] / .42
row = np.floor(v); u = u + .5 * (row % 2)                                                 # 반씩 어긋난 반복 (half-drop)
x_ = (u % 1) - .5; y_ = (v % 1) - .5; ax = np.abs(x_)                                      # 좌우 대칭
def damask_tile(W=600, H=840, ss=2):
    """다마스크 한 칸(30 × 42 cm): 가운데 줄기 · 위 팔메트(세 꽃잎) · 아칸서스 잎이 달린 오지(ogee) 메달리온 · 안쪽 큰 잎 · 아래 두 잎과 봉오리 ·
    양 끝 작은 장미꽃 — 왼쪽 반을 그리고 좌우 대칭. 손으로 그린 판화처럼 굵기가 변하는 선."""
    from PIL import Image, ImageDraw
    im = Image.new('L', (W * ss, H * ss), 0); dr = ImageDraw.Draw(im)
    def P(x, y): return (x * ss, y * ss)
    def both(fn, pts, *a):
        fn([P(x, y) for x, y in pts], *a); fn([P(W - x, y) for x, y in pts], *a)
    def bez(p0, p1, p2, n=24):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]
    def leaf(p0, p2, w, bend=0.0, n=24):
        """끝이 뾰족한 잎: 곡선을 따라 폭 sin(πt)^.8."""
        mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2; dx, dy = p2[0] - p0[0], p2[1] - p0[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L; c = bez(p0, (mx + nx * bend, my + ny * bend), p2, n)
        left, right = [], []
        for k, (x, y) in enumerate(c):
            t = k / (n - 1); hw = w / 2 * math.sin(math.pi * t) ** .8
            a = c[min(k + 1, n - 1)]; b = c[max(k - 1, 0)]; tx, ty = a[0] - b[0], a[1] - b[1]; tl = math.hypot(tx, ty) or 1
            left.append((x - ty / tl * hw, y + tx / tl * hw)); right.append((x + ty / tl * hw, y - tx / tl * hw))
        return left + right[::-1], c
    def stroke(pts, w0, w1):
        for k in range(len(pts) - 1):
            w = w0 + (w1 - w0) * k / (len(pts) - 1)
            for x, y in (pts[k],):
                dr.ellipse([P(x - w / 2, y - w / 2), P(x + w / 2, y + w / 2)], fill=255)
            dr.line([P(*pts[k]), P(*pts[k + 1])], fill=255, width=int(w * ss))
    def mstroke(pts, w0, w1):
        stroke(pts, w0, w1); stroke([(W - x, y) for x, y in pts], w0, w1)
    def spiral(cx, cy, r0, a0, turns, w0, w1, sgn=1):
        return [(cx + r0 * math.exp(-.28 * t) * math.cos(a0 + sgn * t), cy + r0 * math.exp(-.28 * t) * math.sin(a0 + sgn * t)) for t in np.linspace(0, turns * math.tau, 40)]
    cx = W / 2
    stroke([(cx, 650), (cx, 160)], 11, 9)                                                         # 줄기
    poly, _ = leaf((cx, 255), (cx, 70), 50); dr.polygon([P(x, y) for x, y in poly], fill=255)     # 위 팔메트: 가운데 꽃잎
    poly, _ = leaf((cx - 6, 240), (cx - 92, 140), 36, bend=-26); both(dr.polygon, poly, 255)       # 옆 꽃잎 (바깥으로 말림)
    mstroke(spiral(cx - 104, 150, 22, 0.3, 1.1, 9, 4, -1), 9, 4)
    dr.ellipse([P(cx - 15, 40), P(cx + 15, 72)], fill=255)                                        # 맨 위 봉오리
    og = bez((cx, 262), (cx - 30, 302), (cx - 110, 322)) + bez((cx - 110, 322), (cx - 185, 345), (cx - 160, 460))[1:] + bez((cx - 160, 460), (cx - 135, 565), (cx - 30, 590))[1:]   # 뾰족한 오지 메달리온 테
    mstroke(og, 18, 12)
    mstroke(spiral(cx - 40, 615, 30, -1.2, 1.25, 12, 5, 1), 12, 5)                               # 아래 끝 말림
    for (a_, b_, w_, bd) in [((cx - 150, 345), (cx - 196, 262), 30, -16), ((cx - 166, 430), (cx - 214, 350), 30, -18), ((cx - 152, 515), (cx - 214, 448), 28, -18),
                             ((cx - 118, 560), (cx - 196, 540), 24, 12)]:
        poly, _ = leaf(a_, b_, w_, bend=bd); both(dr.polygon, poly, 255)                          # 테를 따라 위로 자라는 아칸서스 잎
    mstroke(spiral(cx - 206, 252, 16, 2.4, 1.0, 6, 3, 1), 6, 3)
    poly, c_ = leaf((cx, 560), (cx, 330), 92); dr.polygon([P(x, y) for x, y in poly], fill=255)  # 안쪽 큰 잎
    dr.line([P(*c_[2]), P(*c_[-3])], fill=0, width=int(5 * ss))                                    # 잎맥 (비움)
    for k in range(4):
        y0 = 380 + k * 42; dr.line([P(cx, y0), P(cx - 26 + k * 2, y0 - 26)], fill=0, width=int(3 * ss)); dr.line([P(cx, y0), P(cx + 26 - k * 2, y0 - 26)], fill=0, width=int(3 * ss))
    poly, _ = leaf((cx - 4, 640), (cx - 70, 745), 34, bend=18); both(dr.polygon, poly, 255)        # 아래 두 잎
    dr.ellipse([P(cx - 13, 690), P(cx + 13, 740)], fill=255)                                      # 늘어진 봉오리
    for ex in (0, W):                                                                             # 양 끝(옆 칸과 나누는) 작은 장미꽃
        for k in range(5):
            a = math.tau * k / 5 - math.pi / 2
            dr.ellipse([P(ex + 26 * math.cos(a) - 13, 420 + 26 * math.sin(a) - 13), P(ex + 26 * math.cos(a) + 13, 420 + 26 * math.sin(a) + 13)], fill=255)
        dr.ellipse([P(ex - 9, 411), P(ex + 9, 429)], fill=0)
    im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0
DT = damask_tile(); DTH, DTW = DT.shape
dam = DT[np.clip(((.5 - y_) * DTH).astype(int), 0, DTH - 1), np.clip(((x_ + .5) * DTW).astype(int), 0, DTW - 1)]
age = np.clip(tex.fbm(p, 2.0, 4, seed=11) * .7 + .3, 0, 1); stain = np.clip(tex.fbm(p, .8, 3, seed=12) * 1.6 - .5, 0, 1)
soot = np.clip((p[:, 2] - 1.7) / .6, 0, 1)
col = np.array([.085, .07, .052])[None, :] * (1 - dam[:, None]) + np.array([.17, .14, .095])[None, :] * dam[:, None]
col = col * (1 - .25 * age[:, None]) * (1 - .3 * soot[:, None]) + np.array([.25, .19, .08])[None, :] * (stain * .35)[:, None]
lower = p[:, 2] < .9
wcol = wood(p, (0, 0, 1), .007, 13)[0] * .7
col = np.where(lower[:, None], wcol, col)
wall.data.materials.append(tex.material('Lounge_Wallpaper', TD, S.img(np.clip(col, 0, 1)), S.img(np.where(lower, .35, .8 - .25 * dam)), tex.h2n(S.img(dam * .3), .8)))
for o, axis, sd in ((wainscot, (0, 0, 1), 14), (base_m, (1, 0, 0), 15), (rail_m, (1, 0, 0), 16)):
    S = S_of(o, 1024); col, rings, st = wood(S.p, axis, .006, sd)
    scuff = scratches(S.p, 40, (0, WALL_Y, .08), (1.3, .01, .07), sd) if o is base_m else np.zeros(len(S.p))
    o.data.materials.append(tex.material(o.name + '_M', TD, S.img(col * (1 + .4 * scuff[:, None])), S.img(.32 + .2 * st + .3 * scuff), tex.h2n(S.img(rings * .2 - scuff), .8), coat=(.4, .2)))

# ---------- 창: 칠한 나무(벗겨짐 · 때) · 밤 유리 ----------
S = S_of(window, 1024); p = S.p
chip = np.clip(tex.fbm(p, 60, 4, seed=21) * 2 - .9, 0, 1)
col = np.array([.78, .74, .64])[None, :] * (1 - .25 * np.clip(tex.fbm(p, 8, 3, seed=22), 0, 1))[:, None]
col = col * (1 - chip[:, None]) + wood(p, (1, 0, 0), .006, 23)[0] * chip[:, None]
window.data.materials.append(tex.material('Lounge_WindowPaint', TD, S.img(col), S.img(.55 + .2 * chip), tex.h2n(S.img(chip * .5), 1.0)))
glass.data.materials.append(odd.gltf_material('Lounge_Glass', base_value=(.02, .035, .07, 1), rough_value=.05, spec=1.0))

# ---------- 커튼: 짙은 붉은 벨벳(무겁게) · 밑단 먼지 + 창 안쪽 레이스 (콘셉트) ----------
for o, nm in ((cur_l, 'Lounge_CurtainL'), (cur_r, 'Lounge_CurtainR')):
    S = S_of(o, 1024); p = S.p
    dust = np.clip((.25 - p[:, 2]) / .25, 0, 1)
    col = np.array([.26, .03, .045])[None, :] * (1 + .25 * tex.fbm(p * np.array([20, 20, 4]), 1.0, 3, seed=31))[:, None] * (1 + .6 * dust[:, None])
    o.data.materials.append(tex.material(nm, TD, S.img(col), S.img(.7 + .1 * dust), tex.h2n(S.img(tex.vnoise(p, 700, seed=32) * .3), .6), sheen=(.7, .45, (.75, .25, .28, 1))))
L2 = 1024; lv, lu = (np.mgrid[0:L2, 0:L2] + .5) / L2
lace = ((np.sin(lu * TAU * 30) * np.sin(lv * TAU * 40) > .55) | (np.abs(np.hypot((lu * 10) % 1 - .5, (lv * 12) % 1 - .5) - .3) < .04)).astype(float)
la = np.clip(.38 + .45 * lace, 0, 1)
lc = np.dstack([np.full((L2, L2), .86), np.full((L2, L2), .84), np.full((L2, L2), .78), la])
lp_ = tex.save(lc, os.path.join(TD, 'Lounge_Sheer_c.png'))
sheer_m = odd.gltf_material('Lounge_Sheer', base=tex.load(lp_), rough_value=.8, alpha_tex='base', alpha_mode='BLEND', double=True)
sheer.data.materials.append(sheer_m)

# ---------- 러그: 페르시아 무늬(메달리온 · 테두리 띠 · 잔무늬) · 바랜 색 · 닳은 길(씨실이 보인다) ----------
R_ = 1024; vv, uu = (np.mgrid[0:R_, 0:R_] + .5) / R_
xx_ = (uu - .5) * 2; yy_ = (vv - .5) * 2
ax_ = np.abs(xx_); ay_ = np.abs(yy_)
RED = np.array([.30, .04, .05]); RED2 = np.array([.24, .03, .04]); NAVY = np.array([.05, .07, .16]); IVORY = np.array([.64, .55, .42]); GOLD = np.array([.55, .38, .14]); TEAL = np.array([.08, .2, .2])
def put_(img, m, col):
    return img * (1 - m[..., None]) + np.asarray(col)[None, None, :] * m[..., None]
def soft(m, w=.004):
    return np.clip(.5 - m / w, 0, 1)                                                              # 거리 → 부드러운 마스크
bmax = np.maximum(ax_, ay_ * 1.0)
# 바탕: 붉은 들판 + 씨실 방향 색 띠(아브라시)
abrash = (np.sin(yy_ * 7 + tex.fbm(np.stack([uu.ravel(), vv.ravel(), np.zeros(R_ * R_)], 1), 2.0, 2, seed=44).reshape(R_, R_) * 2) * .5 + .5)
img = RED[None, None, :] * (1 - .25 * abrash[..., None]) + RED2[None, None, :] * (.25 * abrash[..., None])
# 들판: 헤라티 격자 (마름모 줄기 + 마디 꽃 + 잎)
gu, gv = xx_ * 9, yy_ * 6
lat = np.minimum(np.abs(((gu + gv) % 2) - 1), np.abs(((gu - gv) % 2) - 1))
img = put_(img, soft(lat - .06, .05) * .9, NAVY)
nodes = np.hypot(((gu + 1) % 2) - 1, ((gv + 1) % 2) - 1)
petal = np.cos(np.arctan2(((gv + 1) % 2) - 1, ((gu + 1) % 2) - 1) * 4) * .08 + .22
img = put_(img, soft(nodes - petal, .04), IVORY); img = put_(img, soft(nodes - .08, .03), GOLD)
leaf = np.hypot((gu % 2) - 1, ((gv % 2) - 1) * 1.8)
img = put_(img, soft(leaf - .18, .04) * .8, TEAL)
# 모서리 반 메달리온 (스팬드럴)
for sx in (-1, 1):
    for sy in (-1, 1):
        cd = np.hypot((xx_ - sx * .78) * 1.0, (yy_ - sy * .78) * 1.45)
        img = put_(img, soft(cd - .34, .01), NAVY); img = put_(img, soft(np.abs(cd - .34) - .012, .006), IVORY)
        img = put_(img, soft(np.abs(cd - .24) - .01, .006) * .8, GOLD)
# 가운데 메달리온: 꽃잎 테(12갈래) · 남색 · 상아 테 · 붉은 별 · 금색 · 위아래 펜던트
th = np.arctan2(yy_ * 1.45, xx_); md = np.hypot(xx_, yy_ * 1.45)
lob = .36 + .035 * np.cos(th * 12)
img = put_(img, soft(md - lob, .008), NAVY); img = put_(img, soft(np.abs(md - lob) - .012, .006), IVORY)
star = .2 + .06 * np.cos(th * 8)
img = put_(img, soft(md - star, .006), RED); img = put_(img, soft(np.abs(md - star) - .008, .005), GOLD)
img = put_(img, soft(md - .07, .006), IVORY); img = put_(img, soft(md - .035, .005), NAVY)
for sy in (-1, 1):
    pd = np.hypot(xx_ * 2.2, (yy_ - sy * .47) * 2.6)
    img = put_(img, soft(pd - .1, .01), NAVY); img = put_(img, soft(np.abs(pd - .1) - .01, .006), IVORY)
img = put_(img, soft(np.abs(xx_) - .006, .004) * (ay_ < .62) * (ay_ > .38), IVORY)
# 테두리: 바깥 가드 줄 · 남색 큰 띠(로제트 + 금색 덩굴) · 안쪽 가드 줄
img = put_(img, ((bmax > .78) & (bmax < .955)).astype(float), NAVY)
for g0 in (.955, .965, .975, .76, .77):
    img = put_(img, soft(np.abs(bmax - g0) - .003, .002), IVORY if g0 in (.965, .77) else RED)
img = put_(img, (bmax > .98).astype(float), RED2)
bt = np.where(ax_ > ay_, yy_, xx_) * (np.where(ax_ > ay_, 1.0, 1.45))                              # 띠를 따라가는 좌표
bw_ = (bmax - .7775) / (.955 - .7775)                                                             # 띠 안의 깊이 0..1
inband = (bw_ > 0) & (bw_ < 1)
vine = soft(np.abs(bw_ - .5 - .22 * np.sin(bt * 22)) - .03, .02) * inband
img = put_(img, vine, GOLD)
ros = np.hypot(((bt * 11) % 1 - .5) * 1.0, (bw_ - .5) * 1.6) * inband
rth = np.arctan2(bw_ - .5, (bt * 11) % 1 - .5)
img = put_(img, soft(ros - (.26 + .07 * np.cos(rth * 8)), .03) * inband, RED)
img = put_(img, soft(ros - .1, .02) * inband, IVORY)
# 바램 · 닳은 길(씨실이 보인다) · 먼지
P2 = np.stack([uu.ravel() * 3, vv.ravel() * 2, np.zeros(R_ * R_)], 1)
fade = (tex.fbm(P2, 2.0, 4, seed=41).reshape(R_, R_) * .5 + .5)
path = np.exp(-((xx_ - .1) / .5) ** 2) * np.clip(1 - (yy_ + .2) / 1.4, 0, 1)
worn = np.clip(path * (fade * 1.1) - .5, 0, 1) * .7
warp_lines = (np.sin(uu * 900) > .3)
img = img * (1 - .12 * fade[..., None]) + np.array([.42, .34, .28]) * (.12 * fade[..., None])
img = img * (1 - worn[..., None] * .35) + np.where(warp_lines[..., None], np.array([.7, .64, .56]), np.array([.45, .4, .34])) * (worn[..., None] * .35)
pile = (tex.vnoise(np.stack([uu.ravel() * 500, vv.ravel() * 500, np.zeros(R_ * R_)], 1), 1.0, seed=3).reshape(R_, R_)) * (1 - worn)
rug.data.materials.append(tex.material('Lounge_Rug', TD, np.clip(img, 0, 1), .88 + .08 * worn, tex.h2n(pile * .8, 1.2)))     # 결 반사(sheen) 없음 — 바닥에서 비스듬히 보면 분홍빛으로 번진다
S_of(fringe, 64); fringe.data.materials.append(odd.gltf_material('Lounge_Fringe', base_value=(.78, .72, .6, 1), rough_value=.9))

# ---------- 책: 천 표지(색 제각각) · 책등 금박 띠 · 종이(크림 · 결) · 윗면 먼지 ----------
COVERS = [(.36, .07, .06), (.08, .13, .26), (.2, .26, .12), (.55, .4, .12), (.06, .05, .05), (.3, .18, .1), (.4, .3, .25), (.12, .2, .22)]
for k, o in enumerate(books):
    S = S_of(o, 512); p = S.p
    c = np.array(o['c']); R = np.array(o['R']); w, d, h = o['size']
    q = (p - c) @ R
    pages = (q[:, 0] > -w / 2 + .006) & (np.abs(q[:, 2]) < h / 2 - .0025) & (np.abs(q[:, 1]) < d / 2 - .002)
    spine = q[:, 0] < -w / 2 + .004
    bands = spine & ((np.abs(q[:, 1] - d * .32) < .003) | (np.abs(q[:, 1] + d * .32) < .003) | (np.abs(q[:, 1]) < .012) & (np.abs(q[:, 2]) < h * .3))
    cov = np.array(COVERS[k % len(COVERS)])
    dust = np.clip(S.n @ (R @ np.array([0, 0, 1.0])), 0, 1) * np.clip(tex.fbm(p, 120, 3, seed=k) * .5 + .7, 0, 1)
    col = np.where(pages[:, None], np.array([.84, .78, .64]), cov[None, :] * (1 + .15 * tex.fbm(p, 400, 2, seed=k)[:, None]))
    col = np.where(bands[:, None], np.array([.72, .56, .25]), col)
    col = col * (1 - .35 * dust[:, None]) + np.array([.55, .52, .48])[None, :] * (.35 * dust[:, None]) * (~pages)[:, None]
    lines = pages * (np.sin(q[:, 2] * 9000) * .5)
    o.data.materials.append(tex.material(o.name, TD, S.img(np.clip(col, 0, 1)), S.img(np.where(bands, .35, np.where(pages, .9, .75))), tex.h2n(S.img(lines + bands * .4), 1.0)))
book_all = odd.join(books, 'Lounge_Books')

# ---------- LP 슬리브: 앨범 아트 6종 · 원판 자국(링 마모) · 모서리 닳음 ----------
def album(seed, title):
    r_ = np.random.default_rng(seed); A = 512; im = Image.new('RGB', (A, A), tuple(int(c * 255) for c in r_.uniform(.15, .8, 3))); dr = ImageDraw.Draw(im)
    for _ in range(r_.integers(3, 7)):
        col = tuple(int(c * 255) for c in r_.uniform(0, 1, 3)); x0, y0 = r_.uniform(0, A, 2); s_ = r_.uniform(60, 300)
        if r_.random() < .5: dr.ellipse([x0 - s_ / 2, y0 - s_ / 2, x0 + s_ / 2, y0 + s_ / 2], fill=col)
        else: dr.rectangle([x0, y0, x0 + s_, y0 + s_ * r_.uniform(.2, 1)], fill=col)
    f = ImageFont.truetype(FS, 46); dr.text((30, A - 90), title, font=f, fill=(245, 238, 220))
    return np.asarray(im).astype(float)[::-1] / 255
TITLES = ['MIDNIGHT HOUSE', 'THE ODD TRIO', 'VELVET STATIC', 'LP No.7', 'SLOW LAMP', 'BLUE ATTIC']
arts = [album(50 + k, TITLES[k]) for k in range(6)]
for k, o in enumerate(sleeves):
    S = S_of(o, 512); p = S.p; c = np.array(o['c']); R = np.array(o['R']); q = (p - c) @ R
    art = arts[k % 6]; ui = np.clip(((q[:, 0] / .315 + .5) * 511).astype(int), 0, 511); vi = np.clip(((q[:, 1] / .315 + .5) * 511).astype(int), 0, 511)
    col = art[vi, ui]
    ring = np.clip(1 - np.abs(np.hypot(q[:, 0], q[:, 1]) - .148) / .006, 0, 1) * .5 + np.clip(1 - np.hypot(q[:, 0], q[:, 1]) / .02, 0, 1) * .3
    edgew = np.clip((np.maximum(np.abs(q[:, 0]), np.abs(q[:, 1])) - .145) / .012, 0, 1)
    col = col * (1 - .3 * ring[:, None] - .3 * edgew[:, None]) + np.array([.8, .76, .66])[None, :] * ((.3 * ring + .35 * edgew)[:, None])
    o.data.materials.append(tex.material(f'Lounge_Sleeve{k}', TD, S.img(np.clip(col, 0, 1)), S.img(.7 + .1 * edgew), None))
sleeve_all = odd.join(sleeves, 'Lounge_LPSleeves')

# ---------- 마루: 널마다 다른 월넛 · 긁힘 · 벽 쪽 먼지 · 소파 앞 닳은 길 ----------
S = S_of(floor, 2048, angle=30, margin=.002); p = S.p
plank = np.floor((p[:, 1] + .85) / .0895)
col, rings, st = wood(p + np.stack([np.zeros(len(p)), np.zeros(len(p)), plank * .37], 1), (1, 0, 0), .005, 41, dark=(.09, .048, .026), light=(.22, .12, .06))   # 짙은 월넛 (콘셉트)
col = col * (.8 + .4 * ((plank * 7919) % 13 / 13.))[:, None]
scr = scratches(p, 160, (0, .05, 0), (1.3, .9, .0), 43, .0005, (.02, .12))
dust = np.clip((p[:, 1] - (WALL_Y - .12)) / .1, 0, 1) * .5
pathw = np.exp(-((p[:, 1] + .45) / .2) ** 2) * .5
col = col * (1 + .4 * scr[:, None] + .25 * pathw[:, None]) * (1 - .1 * dust[:, None]) + np.array([.35, .32, .28])[None, :] * dust[:, None] * .4
floor.data.materials.append(tex.material('Lounge_Floor', TD, S.img(np.clip(col, 0, 1)), S.img(np.clip(.24 + .25 * scr + .2 * pathw + .3 * dust + .1 * st, 0, 1)), tex.h2n(S.img(rings * .3 - scr), .9), coat=(.6, .12)))

# ---------- 액자: 낡은 금박(오목한 곳은 어둡게) · 그림 2점(초상 · 달밤 풍경, 바랜 유화) ----------
S = S_of(picture_frames, 1024); p = S.p
gild_w = np.clip(tex.fbm(p, 60, 3, seed=51) * 1.4 + .2, 0, 1)
fcol = np.array([.46, .33, .14])[None, :] * (.7 + .4 * gild_w)[:, None] * np.where((S.n[:, 1] < -.6)[:, None], 1.0, .55)
picture_frames.data.materials.append(tex.material('Lounge_FrameGilt', TD, S.img(np.clip(fcol, 0, 1)), S.img(.42 + .2 * (1 - gild_w)), tex.h2n(S.img(gild_w * .3), .8), metal_value=.7))
def painting(kind, W, H):
    """바랜 유화 한 점: 겹친 붓 모양을 흐리게 섞고, 붓결 노이즈 · 비네트 · 누런 니스 · 빙열."""
    from PIL import ImageFilter
    def layer(draw_fn, blur):
        im = Image.new('L', (W, H), 0); draw_fn(ImageDraw.Draw(im)); return np.asarray(im.filter(ImageFilter.GaussianBlur(blur))).astype(float) / 255
    gy, gx = np.mgrid[0:H, 0:W]; yy, xx = gy / H, gx / W
    def over(base, m, col):
        return base * (1 - m[..., None]) + np.array(col)[None, None, :] * m[..., None]
    if kind == 0:                                                                                     # 초상: 어두운 배경 · 빛 받은 얼굴 · 검은 옷 · 흰 깃
        a = np.dstack([.16 + .1 * (1 - yy), .12 + .07 * (1 - yy), .08 + .03 * (1 - yy)])
        glow = np.exp(-(((xx - .45) / .45) ** 2 + ((yy - .35) / .4) ** 2)); a = a + glow[..., None] * np.array([.12, .08, .04])
        body = layer(lambda d: d.polygon([(W * .08, H), (W * .26, H * .62), (W * .5, H * .58), (W * .74, H * .62), (W * .92, H)], fill=255), 6)
        a = over(a, body, (.07, .065, .07))
        collar = layer(lambda d: d.polygon([(W * .38, H * .6), (W * .5, H * .72), (W * .62, H * .6), (W * .56, H * .58), (W * .5, H * .64), (W * .44, H * .58)], fill=255), 3)
        a = over(a, collar * .9, (.78, .74, .64))
        neck = layer(lambda d: d.rectangle([W * .43, H * .45, W * .57, H * .6], fill=255), 4); a = over(a, neck, (.5, .36, .26))
        face = layer(lambda d: d.ellipse([W * .34, H * .2, W * .66, H * .54], fill=255), 5)
        shade = np.clip((xx - .42) / .25, 0, 1)                                                        # 오른쪽은 그늘
        fcol = np.dstack([.78 - .3 * shade, .58 - .24 * shade, .44 - .2 * shade])
        a = a * (1 - face[..., None]) + fcol * face[..., None]
        def hair_(d):
            d.ellipse([W * .3, H * .13, W * .7, H * .36], fill=255); d.rectangle([W * .3, H * .24, W * .37, H * .42], fill=255); d.rectangle([W * .63, H * .24, W * .7, H * .42], fill=255)
        a = over(a, layer(hair_, 5), (.13, .09, .06))
        for ex in (.44, .56):
            a = over(a, layer(lambda d, ex=ex: d.ellipse([W * (ex - .025), H * .34, W * (ex + .025), H * .365], fill=255), 1.5), (.18, .12, .1))
    else:                                                                                             # 달밤 풍경: 하늘 · 달빛 번짐 · 언덕 · 나무 · 호수
        a = np.dstack([.10 + .14 * yy, .12 + .12 * yy, .18 + .04 * yy])
        moon = layer(lambda d: d.ellipse([W * .66, H * .14, W * .82, H * .28], fill=255), 2)
        halo = layer(lambda d: d.ellipse([W * .56, H * .04, W * .92, H * .38], fill=255), 22)
        a = a + halo[..., None] * np.array([.18, .17, .12]); a = over(a, moon, (.86, .82, .62))
        hill = layer(lambda d: d.polygon([(0, H * .72), (W * .3, H * .6), (W * .6, H * .7), (W, H * .58), (W, H), (0, H)], fill=255), 4)
        a = over(a, hill, (.08, .1, .07))
        def trees_(d):
            for tx in (.16, .27, .5): d.polygon([(W * tx, H * .28), (W * (tx - .08), H * .72), (W * (tx + .08), H * .72)], fill=255)
        a = over(a, layer(trees_, 3), (.05, .07, .05))
        lake = layer(lambda d: d.ellipse([W * .55, H * .78, W * .95, H * .9], fill=255), 5); a = over(a, lake * .6, (.3, .32, .3))
    P3 = np.column_stack([xx.ravel() * 3, yy.ravel() * 3, np.zeros(W * H)])
    brush = tex.fbm(P3 * np.array([60, 14, 1]), 1.0, 3, seed=54 + kind).reshape(H, W)
    a = a * (1 + .1 * brush[..., None])
    vig = np.clip(1 - (((xx - .5) / .6) ** 2 + ((yy - .5) / .65) ** 2), 0, 1) ** .5
    a = a * (.55 + .45 * vig[..., None]) * np.array([1.0, .92, .74])                                   # 비네트 · 누런 니스
    crq = (np.abs(tex.vnoise(P3 * 20, 1.0, seed=52 + kind)).reshape(H, W) < .03)
    a = a * (1 - .2 * crq[..., None])
    return np.clip(a, 0, 1)[::-1], crq[::-1]
for k, o in enumerate(pics):
    W, H = (360, 460) if k == 0 else (300, 360)
    a, crq = painting(k, W, H)
    o.data.materials.append(tex.material(f'Lounge_Painting{k}', TD, a, .55 + .3 * crq, tex.h2n(crq.astype(float) * .5, 1.0), coat=(.4, .25)))
# ---------- 담요: 짙은 남색 · 녹 · 크림 줄 무늬 직물 + 양 끝 술 (알파) ----------
T2 = 1024; tv, tu = (np.mgrid[0:T2, 0:T2] + .5) / T2
bandk = np.floor(tu * 14) % 5
tcol = np.select([(bandk == 0)[..., None], (bandk == 1)[..., None], (bandk == 2)[..., None], (bandk == 3)[..., None]], [np.array([.08, .1, .2]), np.array([.55, .25, .1]), np.array([.78, .7, .55]), np.array([.08, .1, .2])], np.array([.36, .08, .07]))
zig = (np.abs(((tv * 20) % 1) - .5) * 2 > np.abs(((tu * 70) % 1) - .5) * 2) & (bandk == 2)
tcol = np.where(zig[..., None], np.array([.36, .08, .07]), tcol)
weave_t = (np.sin(tu * 1400) * np.sin(tv * 1400)) * .5
fringe_m = (tu < .05) | (tu > .95)
alpha_t = np.where(fringe_m, (np.sin(tv * 380) > .1).astype(float), 1.0)
tcol = np.where(fringe_m[..., None], np.array([.76, .68, .54]), tcol) * (1 + .1 * weave_t[..., None])
tp_ = tex.save(np.dstack([np.clip(tcol, 0, 1), alpha_t]), os.path.join(TD, 'Lounge_Throw_c.png'))
throw.data.materials.append(odd.gltf_material('Lounge_Throw', base=tex.load(tp_), rough_value=.9, alpha_tex='base', alpha_mode='MASK', double=True, sheen=(.4, .5, (.7, .6, .5, 1))))

# =====================================================================================
# 11. 내보내기 (리뷰 후보)
# =====================================================================================
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.data.materials: print('NO MATERIAL', o.name)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in meshes)
GLB = os.path.join(odd.OUT, 'review', 'env_lounge_section_review.glb')
print('GLB', GLB, odd.export_glb(GLB, meshes), 'bytes', 'tris', tris, 'objects', len(meshes))
