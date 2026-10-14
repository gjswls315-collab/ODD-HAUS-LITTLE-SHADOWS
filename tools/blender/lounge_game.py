"""게임 거실 맞춤 가구 — 승인된 리뷰 구역(lounge_section.py)의 조형 · 재질을 게임 충돌 상자 크기 그대로 다시 만든다.
"동선은 안 바꾸고 보이는 모양만 바꾼다": 소파(좌면 · 팔걸이 · 등받이 윗면 = 충돌 높이) · 사이드 테이블(상판 · 아래 선반 = 충돌 높이) ·
램프(게임 빛 자리) · 창 양옆 벨벳 커튼 · 금박 액자 3점 + 그림 · 페르시아 러그(8 × 1.7 m) · 소파 담요.
레이스 커튼은 넣지 않는다 — 게임의 달빛 그림자를 막아 창 앞 빛 웅덩이가 사라진다.
나머지 방(벽 · 마루 · 책장 · 벽난로 · 시계 · LP 캐비닛 · 스피커 …)은 v2.9 거실 GLB 그대로 — glb_merge.py가 바꾼 자리만 잘라내고 합친다.
충돌 상자: lounge_colliders.json (게임 좌표 m). Blender 좌표 = (x, −z, y).
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy
from mathutils import Vector
import odd, tex

TAU = math.tau
sc = odd.reset()
TD = os.path.join(odd.OUT, 'lounge_game_tex'); os.makedirs(TD, exist_ok=True)
rng = np.random.default_rng(31)
E_, S_, B_ = odd.sd_ellipsoid, odd.sd_round_cone, odd.sd_box
sm, sx_ = odd.smin, odd.smax
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'lounge_colliders.json')))
COLS = CFG['colliders']
WALL_Y = -CFG['wall_z']                                       # 뒷벽 (Blender y)
def bl(c):                                                    # 게임 충돌 상자 → Blender 상자 (x0, x1, y0, y1, z0, z1)
    return c['min'][0], c['max'][0], -c['max'][2], -c['min'][2], c['min'][1], c['max'][1]


def sdf_obj(name, fn, lo, hi, vox, faces, subdiv=1, smooth_it=2):
    d = odd.sdf_mesh('_' + name, fn, np.array(lo), np.array(hi), vox)
    odd.drop_islands(d)
    odd.smooth(d, smooth_it, .4)
    o = odd.retopo(d, faces, subdiv, name); odd.delete(d)
    odd.recalc(o)
    return o


# =====================================================================================
# 1. 소파 (체스터필드) — 충돌 상자: 받침 0.18–0.40 · 쿠션 윗면 0.48 · 팔걸이 윗면 0.64 · 등받이 윗면 0.86 · 다리 0.18
# =====================================================================================
sofa = [c for c in COLS if c['tag'] == 'sofa']
BASE = bl(next(c for c in sofa if abs(c['min'][1] - .18) < .01 and c['max'][1] < .45 and c['max'][0] - c['min'][0] > 2))
BACK = bl(next(c for c in sofa if c['max'][1] > .8))
ARMS = [bl(c) for c in sofa if abs(c['max'][1] - .64) < .01]
CUSH = sorted([bl(c) for c in sofa if abs(c['max'][1] - .48) < .005], key=lambda b: b[0])
LEGS = [bl(c) for c in COLS if c['tag'] == 'sofaLeg']
SX = (BASE[0] + BASE[1]) / 2; SYC = (BASE[2] + BASE[3]) / 2; HW = (BASE[1] - BASE[0]) / 2; HD = (BASE[3] - BASE[2]) / 2
BK_Y = (BACK[2] + BACK[3]) / 2; BK_R = (BACK[3] - BACK[2]) / 2; BK_TOP = BACK[5]; BK_AZ = .1; BK_Z = BK_TOP - BK_AZ      # 등받이 윗단 = 깊이 전체 둥근 말림 (윗면 = 0.86)
ARM_TOP = ARMS[0][5]; ARM_AZ = .09; ARM_AX = .135                                                     # 팔걸이 말림: 가로 타원 (폭 전체에서 윗면 0.64 ± 2 cm)
FRONT = BASE[2]
TUFT = []
inner0, inner1 = ARMS[0][1], ARMS[1][0]
for row in range(3):
    zz = BACK[4] + .14 + row * .085
    n_ = 9 if row % 2 == 0 else 8
    for k in range(n_):
        xx = inner0 + .1 + (k + (.5 if row % 2 else 0)) * ((inner1 - inner0 - .2) / 8)
        TUFT.append(np.array([xx, BACK[2] + .004, zz]))
def ell_cyl(p, cx, cz, ax, az, y0, y1, r_end=.03, axis=1):
    """axis(1 = y · 0 = x) 방향 타원 기둥 (양 끝 둥글게): 팔걸이 · 등받이 말림. cx = 가로축 중심, ax = 가로 반지름"""
    h = 0 if axis == 1 else 1
    dx = (p[:, h] - cx) / ax; dz = (p[:, 2] - cz) / az; rr = np.sqrt(dx * dx + dz * dz)
    d_xz = (rr - 1) * min(ax, az)
    d_y = np.maximum(y0 - p[:, axis], p[:, axis] - y1)
    return np.hypot(np.maximum(d_xz + r_end, 0), np.maximum(d_y + r_end, 0)) + np.minimum(np.maximum(d_xz, d_y), 0) - r_end
def frame_sdf(p):
    base = B_(p, (SX, SYC, (BASE[4] + BASE[5]) / 2), (HW - .01, HD, (BASE[5] - BASE[4]) / 2), None, .035)
    back = B_(p, (SX, BK_Y, (BACK[4] + BK_Z) / 2), (HW - .01, BK_R, (BK_Z - BACK[4]) / 2 + .02), None, .05)
    back = sm(back, ell_cyl(p, BK_Y, BK_TOP - BK_AZ, BK_R, BK_AZ, BACK[0] + .01, BACK[1] - .01, .05, axis=0), .04)      # 윗단 말림: 깊이 전체 · 윗면 0.86
    d = sm(base, back, .04)
    for a in ARMS:
        cx = (a[0] + a[1]) / 2; hw = (a[1] - a[0]) / 2
        arm = B_(p, (cx, (a[2] + a[3]) / 2, (BASE[4] + ARM_TOP - ARM_AZ) / 2), (hw - .005, (a[3] - a[2]) / 2, (ARM_TOP - ARM_AZ - BASE[4]) / 2), None, .04)
        roll = ell_cyl(p, cx, ARM_TOP - ARM_AZ, ARM_AX, ARM_AZ, a[2] + .005, a[3] - .01)
        d = sm(d, sm(arm, roll, .04), .03)
    for t in TUFT:                                                                   # 터프팅: 단추 자리 오목 + 단추 사이 다이아몬드 주름
        d = sx_(d, -E_(p, t + np.array([0, .004, 0]), (.022, .02, .022)), .03)
    for i, a in enumerate(TUFT):
        for b in TUFT[i + 1:]:
            if .06 < np.linalg.norm(a - b) < .16:
                d = sx_(d, -S_(p, a + np.array([0, .006, 0]), b + np.array([0, .006, 0]), .0045, .0045), .012)
    for a in ARMS:                                                                   # 팔걸이 안쪽 세로 주름
        s = 1 if a[0] < SX else -1; xin = a[1] if s > 0 else a[0]
        for k in range(6):
            yy = FRONT + .08 + k * .15
            d = sx_(d, -S_(p, (xin + s * .004, yy, ARM_TOP - .06), (xin + s * .006, yy + .01, BASE[5] + .04), .005, .003), .015)
    return d - .005 * tex.fbm((p - np.array([SX, SYC, 0])) * 9, 1.0, 2, seed=4)
frame = sdf_obj('Lounge_SofaFrame', frame_sdf, (BASE[0] - .06, BASE[2] - .05, BASE[4] - .02), (BASE[1] + .06, BASE[3] + .05, BK_TOP + .03), .007, 9000)

def cushion_sdf_fn(cb, dent, seed):
    cx = (cb[0] + cb[1]) / 2; cy = (cb[2] + cb[3]) / 2; hw = (cb[1] - cb[0]) / 2; hd = (cb[3] - cb[2]) / 2; top0 = cb[5] - .006
    def fn(p):
        x, y, z = p[:, 0] - cx, p[:, 1] - cy, p[:, 2]
        crown = .008 * np.clip(1 - (x / hw) ** 2, 0, 1) ** .7 * np.clip(1 - (y / hd) ** 2, 0, 1) ** .7
        dz = dent[2] * np.exp(-((x - dent[0]) / .16) ** 2 - ((y - dent[1]) / .18) ** 2)          # 앉았던 자리 눌림
        top = top0 + crown - dz + .003 * tex.fbm(p * 14, 1.0, 2, seed=seed)
        rect = np.hypot(np.maximum(np.abs(x) - (hw - .05), 0), np.maximum(np.abs(y) - (hd - .05), 0)) - .05
        return sx_(sx_(rect, z - top, .03), (BASE[5] - .015) - z, .02)
    return fn, cx, cy, hw, hd
cushions, pipings = [], []
for i, (cb, dent) in enumerate(zip(CUSH, ((.05, -.05, .012), (-.07, .03, .009)))):
    fn, cx, cy, hw, hd = cushion_sdf_fn(cb, dent, 3 + i)
    o = sdf_obj(f'Lounge_SofaCushion{i}', fn, (cb[0] - .03, cb[2] - .03, BASE[5] - .03), (cb[1] + .03, cb[3] + .03, cb[5] + .03), .004, 3200)
    c0 = Vector((cx + dent[0], cy + dent[1], cb[5]))
    for k in range(5):
        a = TAU * k / 5 + .4 * i
        p0 = c0 + Vector((math.cos(a) * .05, math.sin(a) * .05, 0)); p1 = c0 + Vector((math.cos(a) * .18, math.sin(a) * .16, 0))
        a_, b_ = odd.project(o, [p0, p1]); odd.crease(o, a_, b_, .008, .0022)
    cushions.append(o)
    for zl in (cb[5] - .008, BASE[5] - .005):
        loop = []
        for k in range(72):
            a = TAU * k / 72; ca, sa = math.cos(a), math.sin(a)
            loop.append(Vector((cx + np.sign(ca) * min(1, abs(ca) * 2.2) * hw, cy + np.sign(sa) * min(1, abs(sa) * 2.2) * hd, zl)))
        pts_ = odd.project(o, loop)
        pipings.append(odd.curve_tube('_pipe', pts_ + [pts_[0]], .0045, res=2, bevel_res=2))
piping = odd.join(pipings, 'Lounge_SofaPiping')
buttons = []
for t in TUFT:
    c = t + np.array([0, .008, 0])
    buttons.append(sdf_obj('_btn', (lambda p, c=c: E_(p, c, (.011, .007, .011))), c - .02, c + .02, .0012, 60, subdiv=0))
sofa_buttons = odd.join(buttons, 'Lounge_SofaButtons')
legs = []
for lb in LEGS:
    c = np.array([(lb[0] + lb[1]) / 2, (lb[2] + lb[3]) / 2, 0]); H = lb[5]
    def legfn(p, c=c, H=H):                                                            # 돌린 다리 (받침 밑 18 cm)
        d = E_(p, c + np.array([0, 0, H * .5]), (.04, .04, H * .36))
        d = sm(d, S_(p, c + np.array([0, 0, H * .78]), c + np.array([0, 0, H + .01]), .034, .03), .015)
        return sm(d, E_(p, c + np.array([0, 0, .02]), (.028, .028, .022)), .015)
    legs.append(sdf_obj('_leg', legfn, c - np.array([.06, .06, 0]), c + np.array([.06, .06, H + .03]), .0015, 600))
sofa_legs = odd.join(legs, 'Lounge_SofaLegs')

# =====================================================================================
# 2. 사이드 테이블 (월넛): 상판 0.66–0.70 · 다리 4 · 아래 선반 0.20–0.23 (충돌 상자 그대로) · 서랍 · 놋쇠 손잡이 + 램프 · 책
# =====================================================================================
TOPB = bl(next(c for c in COLS if c['tag'] == 'sideTable'))
TLEGS = [bl(c) for c in COLS if c['tag'] == '' and c['max'][1] > .6 and c['max'][1] < .67]
SHELF = bl(next(c for c in COLS if c['tag'] == '' and abs(c['min'][1] - .2) < .01))
TX = (TOPB[0] + TOPB[1]) / 2; TY = (TOPB[2] + TOPB[3]) / 2; THW = (TOPB[1] - TOPB[0]) / 2; THD = (TOPB[3] - TOPB[2]) / 2; TTOP = TOPB[5]
def table_sdf(p):
    q = p - np.array([TX, TY, 0])
    top = B_(q, (0, 0, (TOPB[4] + TOPB[5]) / 2), (THW, THD, (TOPB[5] - TOPB[4]) / 2), None, .007)
    top = sx_(top, -E_(q, (THW + .005, -THD - .005, TTOP), (.018, .014, .012)), .004)                 # 깨진 모서리
    apron = B_(q, (0, 0, TOPB[4] - .04), (THW - .03, THD - .03, .04), None, .004)
    apron = sx_(apron, -B_(q, (0, -(THD - .03), TOPB[4] - .04), (THW * .6, .01, .028), None, .002), .002)   # 서랍 자리 (틈)
    d = sm(top, apron, .006)
    for lb in TLEGS:
        c = np.array([(lb[0] + lb[1]) / 2 - TX, (lb[2] + lb[3]) / 2 - TY]); hw0 = (lb[1] - lb[0]) / 2
        t = np.clip((TOPB[4] - q[:, 2]) / TOPB[4], 0, 1); hwl = hw0 - .006 * t
        leg = np.maximum(np.maximum(np.abs(q[:, 0] - c[0]) - hwl, np.abs(q[:, 1] - c[1]) - hwl), np.maximum(q[:, 2] - TOPB[4], -q[:, 2])) - .002
        d = sm(d, leg, .006)
    shelf = B_(q, ((SHELF[0] + SHELF[1]) / 2 - TX, (SHELF[2] + SHELF[3]) / 2 - TY, (SHELF[4] + SHELF[5]) / 2), ((SHELF[1] - SHELF[0]) / 2 + .015, (SHELF[3] - SHELF[2]) / 2 + .015, (SHELF[5] - SHELF[4]) / 2), None, .004)
    return sm(d, shelf, .006)
table = sdf_obj('Lounge_Table', table_sdf, (TX - THW - .03, TY - THD - .03, -.01), (TX + THW + .03, TY + THD + .03, TTOP + .02), .0025, 4200)
DRZ = TOPB[4] - .04; DRY = TY - (THD - .03)
drawer = sdf_obj('Lounge_TableDrawer', lambda p: B_(p - np.array([TX, DRY, DRZ]), (0, .001, 0), (THW * .6 - .003, .006, .025), None, .002), (TX - THW, DRY - .02, DRZ - .04), (TX + THW, DRY + .02, DRZ + .04), .0012, 500)
knob = sdf_obj('Lounge_TableKnob', lambda p: sm(E_(p, (TX, DRY - .014, DRZ), (.009, .006, .009)), S_(p, (TX, DRY - .006, DRZ), (TX, DRY - .012, DRZ), .004, .004), .003),
               (TX - .02, DRY - .03, DRZ - .02), (TX + .02, DRY + .01, DRZ + .02), .0005, 200, subdiv=0)
# 램프: 게임 빛(스프라이트 · 빛 웅덩이)이 있는 자리 · 크기에 맞춘다 (갓 = 게임 재질 DR.shade — 게임이 밝기를 바꾼다)
LP = CFG['table_lamp']['pos']; LX, LY, LZ = LP[0], -LP[2], LP[1]; KL = .4
def lamp_base_sdf(p):
    q = (p - np.array([LX, LY, LZ])) / KL
    d = E_(q, (0, 0, .11), (.075, .075, .1))
    d = sm(d, S_(q, (0, 0, .015), (0, 0, .04), .055, .06), .02)
    d = sm(d, S_(q, (0, 0, .19), (0, 0, .24), .028, .02), .02)
    return d * KL
lamp_base = sdf_obj('Lounge_LampBase', lamp_base_sdf, (LX - .05, LY - .05, LZ - .005), (LX + .05, LY + .05, LZ + .11), .0008, 1400)
neck = odd.curve_tube('Lounge_LampNeck', [Vector((LX, LY, LZ + .23 * KL)), Vector((LX, LY, LZ + .3 * KL)), Vector((LX, LY, LZ + .36 * KL))], .006 * KL * 1.4, res=4, bevel_res=3)
harp = odd.curve_tube('Lounge_LampHarp', [Vector((LX - .07 * KL, LY, LZ + .3 * KL)), Vector((LX - .072 * KL, LY, LZ + .42 * KL)), Vector((LX, LY, LZ + .5 * KL)), Vector((LX + .072 * KL, LY, LZ + .42 * KL)), Vector((LX + .07 * KL, LY, LZ + .3 * KL))], .0012, res=8, bevel_res=2)
bulb = sdf_obj('Lounge_LampBulb', lambda p: sm(E_(p, (LX, LY, LZ + .41 * KL), (.03 * KL, .03 * KL, .036 * KL)), S_(p, (LX, LY, LZ + .36 * KL), (LX, LY, LZ + .385 * KL), .013 * KL, .013 * KL), .004),
               (LX - .02, LY - .02, LZ + .13), (LX + .02, LY + .02, LZ + .2), .0006, 400, subdiv=0)
prof = [(.105, .345), (.108, .342), (.112, .345), (.111, .35), (.085, .51), (.083, .515), (.086, .519), (.089, .515)]
NPL = 26
def _pleat(t):
    return (abs(math.sin(t * NPL * math.pi)) - .64) * .045
rings = [[Vector((LX + KL * r * (1 + _pleat(k / 208) * (1 if .2 < z < .51 else .25)) * math.cos(TAU * k / 208), LY + KL * r * (1 + _pleat(k / 208) * (1 if .2 < z < .51 else .25)) * math.sin(TAU * k / 208), LZ + KL * z)) for k in range(208)] for r, z in prof]
shade = odd.loft('Lounge_TableLampShade', rings); odd.solidify(shade, .0012, offset=-1); odd.subsurf(shade, 1)
shade['matRef'] = 'DR.shade'
# 전선: 램프 뒤 → 뒷다리 → 바닥 → 뒷벽 콘센트
OUTX = TX - .25
cpts = [Vector((LX + .01, LY + .03, LZ + .008)), Vector((LX + .03, LY + .07, LZ - .004)), Vector((TX + THW - .02, TY + THD - .01, TOPB[4] - .1)), Vector((TX + THW - .02, TY + THD, .25)),
        Vector((TX + THW - .05, TY + THD + .05, .016)), Vector((TX + .1, TY + .7, .016)), Vector((OUTX + .05, WALL_Y - .3, .006)), Vector((OUTX + .02, WALL_Y - .045, .1)), Vector((OUTX, WALL_Y - .03, .11))]
cord, _ = odd.spline(cpts, 70)
cable = odd.curve_tube('Lounge_LampCable', cord, .0028, res=2, bevel_res=2)
plug = sdf_obj('Lounge_Plug', lambda p: B_(p, (OUTX, WALL_Y - .02, .11), (.016, .012, .022), None, .004), (OUTX - .03, WALL_Y - .04, .08), (OUTX + .03, WALL_Y, .14), .0008, 300)
outlet = sdf_obj('Lounge_Outlet', lambda p: B_(p, (OUTX, WALL_Y - .006, .11), (.035, .004, .055), None, .003), (OUTX - .05, WALL_Y - .02, .04), (OUTX + .05, WALL_Y + .01, .18), .0008, 300)

# 책: 아래 선반 위 3권 (선반 윗면 0.23 — 선반 충돌 상자는 그대로이니 책은 선반 뒤쪽에 낮게)
def book(name, c, size, rot_z=0.0, tilt=0.0, bend=0.0):
    w, d, h = size
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, math.cos(tilt), -math.sin(tilt)], [0, math.sin(tilt), math.cos(tilt)]])
    def fn(p):
        q = (p - np.array(c)) @ R
        cover = B_(q, (0, 0, 0), (w / 2, d / 2, h / 2), None, .0025)
        pages = B_(q, (.004, 0, 0), (w / 2 - .002, d / 2 - .004, h / 2 - .0028), None, .001)
        groove = B_(q, (.006, 0, 0), (w / 2 - .0035, d / 2 + .01, h / 2 - .0035), None, .001)
        return np.minimum(sx_(cover, -groove, .0008), pages) - bend * np.clip((q[:, 0] + w / 2) / w, 0, 1) ** 2 * (q[:, 2] > 0)
    ext = np.array([w, d, h]).max() * .8 + .02
    o = sdf_obj(name, fn, np.array(c) - ext, np.array(c) + ext, .0012, 700, subdiv=0)
    o['size'] = list(size); o['c'] = list(c); o['R'] = R.tolist()
    return o
books = []
zc = SHELF[5]
for k, (w, d, h, rz) in enumerate([(.22, .15, .03, .06), (.2, .14, .022, -.1), (.18, .13, .026, .14)]):
    books.append(book(f'Lounge_ShelfBook{k}', (TX - .02 + .01 * k, TY + .04, zc + h / 2), (w, d, h), rz)); zc += h

# =====================================================================================
# 3. 커튼: 창 양옆 짙은 붉은 벨벳 (천 시뮬레이션) + 놋쇠 봉 · 끝 장식
# =====================================================================================
W_ = CFG['window']; RODZ = W_['rod_y']; CY = -W_['rod_z']
def curtain(name, x0, x1, seed, ampk=1.0):
    r_ = np.random.default_rng(seed); cols, rows = 40, 48; verts = []; faces = []
    ph = np.cumsum(r_.uniform(.6, 1.4, 12)); ph = ph / ph[-1] * 5.0; amp = r_.uniform(.025, .055, 12)
    for r in range(rows):
        t = r / (rows - 1); z = RODZ - .03 - t * (RODZ - .03 + .02) - (r_.uniform(0, .025) if r == rows - 1 else 0)
        for c in range(cols):
            u = c / (cols - 1); x = x0 + (x1 - x0) * u
            kk = min(11, int(np.searchsorted(ph, u * 5.0)))
            y = CY - ampk * amp[kk] * math.sin(np.interp(u * 5.0, np.concatenate([[0], ph]), np.arange(13) * math.pi)) * (1 - .35 * t) + .01 * math.sin(t * 5 + seed)
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
floor_c = odd.mesh_obj('_floorcol', [(8, -3, 0), (13, -3, 0), (13, 3, 0), (8, 3, 0)], [(0, 1, 2, 3)])
wall_c = odd.mesh_obj('_wallcol', [(8, WALL_Y, 0), (13, WALL_Y, 0), (13, WALL_Y, 3), (8, WALL_Y, 3)], [(0, 1, 2, 3)])
sill_c = odd.mesh_obj('_sillcol', [(9.48, 1.43, .87), (11.12, 1.43, .87), (11.12, 1.7, .87), (9.48, 1.7, .87), (9.48, 1.43, .93), (11.12, 1.43, .93), (11.12, 1.7, .93), (9.48, 1.7, .93)],
                      [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], smooth=False)       # 게임 창턱 (커튼이 걸쳐 늘어진다)
(cl0, cl1), (cr0, cr1) = W_['curtains_x']
cur_l = curtain('Lounge_CurtainL', cl0 - .14, cl1 + .04, 3)
cur_r = curtain('Lounge_CurtainR', cr0 - .04, cr1 + .14, 4)
for o in (cur_l, cur_r):
    odd.cloth_sim(o, frames=55, pin_group='pin', colliders=[floor_c, wall_c, sill_c], quality=7, mass=.6, tension=25, bending=6, collide_dist=.004, thickness_outer=.004)
    odd.solidify(o, .004, offset=-1); odd.subsurf(o, 1)
odd.delete(floor_c); odd.delete(wall_c); odd.delete(sill_c)
rod = odd.curve_tube('Lounge_Rod', [Vector((cl0 - .2, CY - .01, RODZ)), Vector((cr1 + .2, CY - .01, RODZ))], .012, res=2, bevel_res=4)
fin = []
for xx, sg in ((cl0 - .22, -1), (cr1 + .22, 1)):
    fin.append(sdf_obj('_fin', (lambda p, xx=xx, sg=sg: sm(E_(p, (xx, CY - .01, RODZ), (.03, .03, .03)), S_(p, (xx, CY - .01, RODZ), (xx - sg * .03, CY - .01, RODZ), .012, .02), .01)),
                       (xx - .05, CY - .06, RODZ - .05), (xx + .05, CY + .04, RODZ + .05), .0015, 300))
finials = odd.join(fin, 'Lounge_RodFinials')

# =====================================================================================
# 4. 금박 액자 3점 (소파 위 · 벽난로 위 · LP 캐비닛 위) + 그림
# =====================================================================================
frames_, pics = [], []
for k, (gx, gy, gw, gh) in enumerate(CFG['frames_gilt']):
    fx, fz, fw, fh = gx, gy, gw + .11, gh + .11; rot = (.012, -.01, .008)[k]
    cr, sr_ = math.cos(rot), math.sin(rot); Rf = np.array([[cr, 0, -sr_], [0, 1, 0], [sr_, 0, cr]])
    def ffn(p, fx=fx, fz=fz, fw=fw, fh=fh, Rf=Rf):
        q = (p - np.array([fx, WALL_Y - .022, fz])) @ Rf
        outer = B_(q, (0, 0, 0), (fw / 2, .02, fh / 2), None, .007)
        inner = B_(q, (0, -.025, 0), (fw / 2 - .055, .04, fh / 2 - .055), None, .003)
        bead = B_(q, (0, -.014, 0), (fw / 2 - .025, .008, fh / 2 - .025), None, .005)
        d = sx_(sm(outer, bead, .007), -inner, .004)                                           # 그림 자리 구멍
        return sx_(d, -B_(q, (0, -.034, 0), (fw / 2 - .035, .006, fh / 2 - .035), None, .004), .004)      # 바깥 테와 안쪽 테 사이 오목한 단
    frames_.append(sdf_obj(f'_frame{k}', ffn, (fx - fw / 2 - .05, WALL_Y - .07, fz - fh / 2 - .05), (fx + fw / 2 + .05, WALL_Y + .01, fz + fh / 2 + .05), .002, 1600, subdiv=0))
    hw_, hh_ = fw / 2 - .053, fh / 2 - .053
    corners = [np.array([-hw_, -.008, -hh_]), np.array([hw_, -.008, -hh_]), np.array([hw_, -.008, hh_]), np.array([-hw_, -.008, hh_])]
    pv = [tuple(np.array([fx, WALL_Y - .022, fz]) + Rf @ c_) for c_ in corners]
    pic = odd.mesh_obj(f'Lounge_Picture{k}', pv, [(0, 1, 2, 3)])
    if np.mean(odd.nrm(pic)[:, 1]) > 0: odd.recalc(pic, inside=True)
    uvp = pic.data.uv_layers.new(name='UVMap')
    for li, uvv in zip(pic.data.polygons[0].loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]): uvp.data[li].uv = uvv
    pic['dims'] = [gw, gh]; pics.append(pic)
picture_frames = odd.join(frames_, 'Lounge_PictureFrames')

# =====================================================================================
# 5. 러그 (8 × 1.7 m 런너): 두께 1.2 cm · 물결치는 가장자리 + 양 끝 술 (말린 모서리 없음 — 플레이어 길 위)
# =====================================================================================
RG = CFG['rug']; RCX = (RG['x'][0] + RG['x'][1]) / 2; RCY = -(RG['z'][0] + RG['z'][1]) / 2; RW = (RG['x'][1] - RG['x'][0]) / 2; RD = (RG['z'][1] - RG['z'][0]) / 2
nx, ny = 200, 44; verts = []; faces = []
for j in range(ny):
    for i in range(nx):
        u = i / (nx - 1) * 2 - 1; v = j / (ny - 1) * 2 - 1
        x = RCX + u * RW + .006 * math.sin(v * 9 + 1.3) * (abs(u) > .99); y = RCY + v * RD + .007 * math.sin(u * 37) * (abs(v) > .97)
        verts.append((x, y, .012 + .001 * math.sin(u * 23) * math.sin(v * 5)))
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
    for k in range(110):
        y = RCY - RD + .02 + k * (2 * RD - .04) / 109; x = RCX + s * RW
        L_ = rng.uniform(.04, .06); bend = rng.uniform(-.01, .01)
        fr.append(odd.curve_tube('_fr', [Vector((x, y, .006)), Vector((x + s * L_ * .5, y + bend * .5, .003)), Vector((x + s * L_, y + bend, .002))], .0011, res=2, bevel_res=1))
fringe = odd.join(fr, 'Lounge_RugFringe')

# =====================================================================================
# 6. 담요: 소파 오른쪽 팔걸이에 걸친 무늬 담요 (천 시뮬레이션)
# =====================================================================================
BW, BD = .7, .62; nb_x, nb_y = 40, 34; bverts = []; bfaces = []
AR = ARMS[1]; acx = (AR[0] + AR[1]) / 2
for j in range(nb_y):
    for i in range(nb_x):
        u = i / (nb_x - 1) - .5; v = j / (nb_y - 1) - .5
        bverts.append((acx - .12 + u * BW, SYC + .02 + v * BD, ARM_TOP + .12 + .02 * math.sin(u * 6)))
for j in range(nb_y - 1):
    for i in range(nb_x - 1):
        a0 = j * nb_x + i; bfaces.append((a0, a0 + 1, a0 + nb_x + 1, a0 + nb_x))
throw = odd.mesh_obj('Lounge_Throw', bverts, bfaces)
uvt = throw.data.uv_layers.new(name='UVMap')
for poly in throw.data.polygons:
    for li in poly.loop_indices:
        vi = throw.data.loops[li].vertex_index; uvt.data[li].uv = ((vi % nb_x) / (nb_x - 1), (vi // nb_x) / (nb_y - 1))
_fc = odd.mesh_obj('_floorcol2', [(3, -3, 0), (8, -3, 0), (8, 3, 0), (3, 3, 0)], [(0, 1, 2, 3)])
odd.cloth_sim(throw, frames=50, colliders=[frame] + cushions + [_fc], quality=7, mass=.25, tension=18, bending=.6, collide_dist=.004, thickness_outer=.005)
odd.delete(_fc)
odd.solidify(throw, .003, offset=1); odd.subsurf(throw, 1)

# =====================================================================================
# 7. 재질 · 텍스처 (리뷰 구역과 같은 방식)
# =====================================================================================
from PIL import Image, ImageDraw
BUDGET = {'Lounge_SofaFrame': 26000, 'Lounge_Table': 8000, 'Lounge_CurtainL': 12000, 'Lounge_CurtainR': 12000, 'Lounge_LampBase': 2000, 'Lounge_Rug': 18000,
          'Lounge_SofaCushion0': 9000, 'Lounge_SofaCushion1': 9000, 'Lounge_TableLampShade': 5000, 'Lounge_Throw': 9000, 'Lounge_SofaLegs': 6000,
          'Lounge_Plug': 800, 'Lounge_Outlet': 800, 'Lounge_RodFinials': 1500}          # 게임 면 예산 (잔디테일은 노멀맵)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name in BUDGET:
        t = sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
        if t > BUDGET[o.name] * 1.05: odd.decimate(o, BUDGET[o.name] / t); o.data.shade_smooth()

def S_of(o, size, angle=60, margin=.004, keep_uv=False):
    if not keep_uv or not o.data.uv_layers: odd.uv_smart(o, angle, margin)
    return tex.Surf(o, size)
def wood(p, axis, ring=.006, seed=0, dark=(.16, .085, .045), light=(.36, .2, .1)):
    a = np.array(axis, float); a /= np.linalg.norm(a); b = np.cross(a, [0, 0, 1.0] if abs(a[2]) < .9 else [1.0, 0, 0]); b /= np.linalg.norm(b); c = np.cross(a, b)
    pa, pb, pc = p @ a, p @ b, p @ c
    warp_ = tex.fbm(np.stack([pa * 2, pb * 30, pc * 30], 1), 1.0, 3, seed=seed) * 1.2
    r = np.hypot(pb + .05 + seed * .013, pc - .03) / ring + warp_
    rings = (np.sin(r * TAU) * .5 + .5) ** 2
    streak = tex.fbm(np.stack([pa * 6, pb * 400, pc * 400], 1), 1.0, 2, seed=seed + 3) * .5 + .5
    t = np.clip(rings * .55 + streak * .45, 0, 1)
    return np.array(dark)[None, :] * (1 - t[:, None]) + np.array(light)[None, :] * t[:, None], rings, streak
def scratches(p, count, area_c, area_r, seed, width=.0004, length=(.01, .06)):
    r_ = np.random.default_rng(seed); out = np.zeros(len(p))
    for _ in range(count):
        c = np.array(area_c) + r_.uniform(-1, 1, 3) * np.array(area_r); d = r_.normal(size=3); d /= np.linalg.norm(d)
        L_ = r_.uniform(*length); dist, _ = tex.seg_dist(p, c, c + d * L_)
        out = np.maximum(out, np.clip(1 - dist / width, 0, 1) * r_.uniform(.3, 1))
    return out

# 벨벳 (소파 · 쿠션 · 파이핑 · 단추): 짙은 와인 벨벳 · 눌린 결 · 팔걸이 위 · 쿠션 앞 모서리 닳음
def velvet(o, name, size, base=(.46, .085, .10), seed=0):            # 게임 밤 조명용 밝기 (v2.9 소파와 같은 밝기 · 거칠기) — 리뷰 구역의 (.22, .02, .035)는 게임 조명에서 푸른 반사에 묻혀 회보라로 보였다
    S = S_of(o, size); p = S.p
    crush = tex.fbm(p * np.array([30, 30, 60]), 1.0, 4, seed=seed)
    top = np.clip(S.n[:, 2], 0, 1); edge_wear = np.zeros(len(p))
    if 'Frame' in name:
        for a in ARMS:
            d, _ = tex.seg_dist(p, ((a[0] + a[1]) / 2, a[2] + .03, ARM_TOP), ((a[0] + a[1]) / 2, a[3] - .06, ARM_TOP))
            edge_wear = np.maximum(edge_wear, np.clip(1 - d / .08, 0, 1) * top)
    if 'Cushion' in name:
        edge_wear = np.clip((FRONT + .06 - p[:, 1]) / .06, 0, 1) * (p[:, 2] > CUSH[0][5] - .03)
    worn = np.clip(edge_wear * (tex.fbm(p, 40, 3, seed=seed + 1) * .6 + .7), 0, 1)
    col = np.array(base)[None, :] * (1 + .22 * crush)[:, None]
    col = col * (1 - worn[:, None] * .45) + np.array([.62, .26, .25])[None, :] * (worn[:, None] * .45)
    hh = crush * .5 + tex.vnoise(p, 900, seed=seed + 2) * .25
    m = tex.material(name, TD, S.img(np.clip(col, 0, 1)), S.img(np.clip(.78 + .12 * worn, 0, 1)), tex.h2n(S.img(hh), .8), sheen=(1.0, .42, (.85, .48, .42, 1)))
    o.data.materials.append(m); return m
velvet(frame, 'Lounge_SofaVelvet', 2048)
cm_ = velvet(cushions[0], 'Lounge_SofaCushion', 1024, seed=5)
S_of(cushions[1], 64); cushions[1].data.materials.append(cm_)
pv = odd.gltf_material('Lounge_Piping', base_value=(.09, .006, .01, 1), rough_value=.8, sheen=(1.0, .45, (.72, .35, .3, 1)))       # 선형 값 (텍스처 없는 재질)
piping.data.materials.append(pv); sofa_buttons.data.materials.append(pv)
S = S_of(sofa_legs, 512); col, rings, st = wood(S.p, (0, 0, 1), .004, 3)
sofa_legs.data.materials.append(tex.material('Lounge_SofaLegs', TD, S.img(col * .8), S.img(.32 + .2 * st), tex.h2n(S.img(rings * .3), .6), coat=(.6, .2)))

# 사이드 테이블: 월넛 · 바니시 긁힘 · 모서리 닳음 · 컵 자국
S = S_of(table, 2048); p = S.p
col, rings, st = wood(p, (1, 0, 0), .005, 7)
scr = scratches(p, 70, (TX, TY, TTOP), (THW, THD, .001), 9)
ring_mark = np.clip(1 - np.abs(np.hypot(p[:, 0] - (TX - .12), p[:, 1] - (TY - .09)) - .038) / .003, 0, 1) * (p[:, 2] > TTOP - .006) * (tex.fbm(p, 200, 2, seed=4) > -.3)
edge = np.clip(1 - np.abs(np.abs(p[:, 0] - TX) - THW) / .006, 0, 1) + np.clip(1 - np.abs(np.abs(p[:, 1] - TY) - THD) / .006, 0, 1)
edge = np.clip(edge * (np.abs(p[:, 2] - TTOP) < .02), 0, 1)
col = col * (1 - .35 * ring_mark[:, None]) * (1 + .35 * scr[:, None]) * (1 + .5 * edge[:, None])
rgh = .28 + .25 * scr + .3 * edge + .15 * ring_mark + .1 * st
table.data.materials.append(tex.material('Lounge_TableWalnut', TD, S.img(np.clip(col, 0, 1)), S.img(np.clip(rgh, 0, 1)), tex.h2n(S.img(rings * .25 - scr * .8), .9), coat=(.5, .15)))
S = S_of(drawer, 512); col, rings, st = wood(S.p, (1, 0, 0), .005, 8)
drawer.data.materials.append(tex.material('Lounge_Drawer', TD, S.img(col), S.img(.3 + .1 * st), tex.h2n(S.img(rings * .25), .9), coat=(.5, .15)))
brass = odd.gltf_material('Lounge_LampBrass', base_value=(.78, .6, .3, 1), rough_value=.32, metal_value=1.0)
oldbrass = odd.gltf_material('Lounge_OldBrass', base_value=(.55, .42, .22, 1), rough_value=.45, metal_value=1.0)
for o in (knob, neck, harp): o.data.materials.append(brass)
for o in (rod, finials, outlet): o.data.materials.append(oldbrass)
# 램프: 호박 · 황토 유약 도자기 · 전구 · 갓(게임 재질로 바뀐다 — 여기 색은 게임 밖에서 볼 때)
S = S_of(lamp_base, 1024); p = S.p
crack = np.abs(tex.vnoise(p, 600, seed=2)) < .04
drip = np.clip(tex.fbm(p * np.array([150, 150, 20]), 1.0, 3, seed=3), 0, 1)
col = np.array([.52, .27, .10])[None, :] * (1 + .35 * drip[:, None]) * np.where(crack[:, None], .7, 1.0)
lamp_base.data.materials.append(tex.material('Lounge_LampCeramic', TD, S.img(col), S.img(.12 + .1 * crack), tex.h2n(S.img(crack.astype(float) * .4 + drip * .2), 1.0), coat=(1, .05)))
bulb.data.materials.append(odd.gltf_material('Lounge_Bulb', base_value=(1, .9, .7, 1), rough_value=.2, emission=((1, .72, .38, 1), 6.0)))
shade.data.materials.append(odd.gltf_material('Lounge_ShadeFallback', base_value=(.8, .5, .22, 1), rough_value=.9, emission=((1, .66, .32, 1), 1.2)))
S = S_of(cable, 512); rub = tex.fbm(S.p, 300, 3, seed=8)
cable.data.materials.append(tex.material('Lounge_Cord', TD, S.img(np.tile([.03, .03, .033], (len(S.p), 1)) * (1 + .4 * np.clip(rub, 0, 1)[:, None])), S.img(.5 + .15 * rub), tex.h2n(S.img(rub * .2), .6)))
plug.data.materials.append(odd.gltf_material('Lounge_PlugBakelite', base_value=(.03, .03, .03, 1), rough_value=.35))
COVERS = [(.36, .07, .06), (.08, .13, .26), (.2, .26, .12)]
for k, o in enumerate(books):
    S = S_of(o, 512); p = S.p; c = np.array(o['c']); R = np.array(o['R']); w, d, h = o['size']; q = (p - c) @ R
    pages = (q[:, 0] > -w / 2 + .006) & (np.abs(q[:, 2]) < h / 2 - .0025) & (np.abs(q[:, 1]) < d / 2 - .002)
    spine = q[:, 0] < -w / 2 + .004
    bands = spine & ((np.abs(q[:, 1] - d * .32) < .003) | (np.abs(q[:, 1] + d * .32) < .003) | (np.abs(q[:, 1]) < .012) & (np.abs(q[:, 2]) < h * .3))
    col = np.where(pages[:, None], np.array([.84, .78, .64]), np.array(COVERS[k])[None, :] * (1 + .15 * tex.fbm(p, 400, 2, seed=k)[:, None]))
    col = np.where(bands[:, None], np.array([.72, .56, .25]), col)
    o.data.materials.append(tex.material(o.name, TD, S.img(np.clip(col, 0, 1)), S.img(np.where(bands, .35, np.where(pages, .9, .75))), tex.h2n(S.img(pages * np.sin(q[:, 2] * 9000) * .5 + bands * .4), 1.0)))
book_all = odd.join(books, 'Lounge_ShelfBooks')

# 커튼: 짙은 붉은 벨벳 (무겁게) · 밑단 먼지
for o, nm in ((cur_l, 'Lounge_CurtainL'), (cur_r, 'Lounge_CurtainR')):
    S = S_of(o, 1024); p = S.p
    dust = np.clip((.25 - p[:, 2]) / .25, 0, 1)
    col = np.array([.40, .05, .07])[None, :] * (1 + .25 * tex.fbm(p * np.array([20, 20, 4]), 1.0, 3, seed=31))[:, None] * (1 + .6 * dust[:, None])      # 게임 밤 조명용 밝기
    o.data.materials.append(tex.material(nm, TD, S.img(np.clip(col, 0, 1)), S.img(.78 + .1 * dust), tex.h2n(S.img(tex.vnoise(p, 700, seed=32) * .3), .6), sheen=(1.0, .45, (.75, .35, .32, 1))))

# 액자: 낡은 금박 · 그림 3점 (달밤 풍경 · 초상 · 붉은 옷의 초상)
S = S_of(picture_frames, 2048); p = S.p
gild_w = np.clip(tex.fbm(p, 60, 3, seed=51) * 1.4 + .2, 0, 1)
fcol = np.array([.46, .33, .14])[None, :] * (.7 + .4 * gild_w)[:, None] * np.where((S.n[:, 1] < -.6)[:, None], 1.0, .55)
picture_frames.data.materials.append(tex.material('Lounge_FrameGilt', TD, S.img(np.clip(fcol, 0, 1)), S.img(.42 + .2 * (1 - gild_w)), tex.h2n(S.img(gild_w * .3), .8), metal_value=.7))
def painting(kind, W, H):
    from PIL import ImageFilter
    def layer(draw_fn, blur):
        im = Image.new('L', (W, H), 0); draw_fn(ImageDraw.Draw(im)); return np.asarray(im.filter(ImageFilter.GaussianBlur(blur))).astype(float) / 255
    gy, gx = np.mgrid[0:H, 0:W]; yy, xx = gy / H, gx / W
    def over(base, m, col):
        return base * (1 - m[..., None]) + np.array(col)[None, None, :] * m[..., None]
    if kind in (0, 2):                                                                                # 초상 (2: 녹색 배경 · 붉은 옷 · 묶은 머리)
        bgc = (np.array([.16, .12, .08]), np.array([.08, .06, .03])) if kind == 0 else (np.array([.10, .15, .11]), np.array([.05, .08, .05]))
        a = np.dstack([bgc[0][i] + bgc[1][i] * (1 - yy) for i in range(3)])
        glow = np.exp(-(((xx - .45) / .45) ** 2 + ((yy - .35) / .4) ** 2)); a = a + glow[..., None] * np.array([.12, .08, .04])
        body = layer(lambda d: d.polygon([(W * .08, H), (W * .26, H * .62), (W * .5, H * .58), (W * .74, H * .62), (W * .92, H)], fill=255), 6)
        a = over(a, body, (.07, .065, .07) if kind == 0 else (.36, .06, .06))
        collar = layer(lambda d: d.polygon([(W * .38, H * .6), (W * .5, H * .72), (W * .62, H * .6), (W * .56, H * .58), (W * .5, H * .64), (W * .44, H * .58)], fill=255), 3)
        a = over(a, collar * (.9 if kind == 0 else .5), (.78, .74, .64))
        neck_ = layer(lambda d: d.rectangle([W * .43, H * .45, W * .57, H * .6], fill=255), 4); a = over(a, neck_, (.5, .36, .26))
        face = layer(lambda d: d.ellipse([W * .34, H * .2, W * .66, H * .54], fill=255), 5)
        shd = np.clip((xx - .42) / .25, 0, 1)
        fcol_ = np.dstack([.78 - .3 * shd, .58 - .24 * shd, .44 - .2 * shd])
        a = a * (1 - face[..., None]) + fcol_ * face[..., None]
        def hair_(d):
            d.ellipse([W * .3, H * .13, W * .7, H * .36], fill=255)
            if kind == 0: d.rectangle([W * .3, H * .24, W * .37, H * .42], fill=255); d.rectangle([W * .63, H * .24, W * .7, H * .42], fill=255)
            else: d.ellipse([W * .42, H * .04, W * .58, H * .17], fill=255)
        a = over(a, layer(hair_, 5), (.13, .09, .06) if kind == 0 else (.32, .18, .08))
        for ex in (.44, .56):
            a = over(a, layer(lambda d, ex=ex: d.ellipse([W * (ex - .025), H * .34, W * (ex + .025), H * .365], fill=255), 1.5), (.18, .12, .1))
    else:                                                                                             # 달밤 풍경
        a = np.dstack([.10 + .14 * yy, .12 + .12 * yy, .18 + .04 * yy])
        moon = layer(lambda d: d.ellipse([W * .7, H * .14, W * .8, H * .29], fill=255), 2)
        halo = layer(lambda d: d.ellipse([W * .6, H * .02, W * .9, H * .4], fill=255), 24)
        a = a + halo[..., None] * np.array([.18, .17, .12]); a = over(a, moon, (.86, .82, .62))
        hill = layer(lambda d: d.polygon([(0, H * .72), (W * .25, H * .6), (W * .55, H * .7), (W * .8, H * .62), (W, H * .66), (W, H), (0, H)], fill=255), 4)
        a = over(a, hill, (.08, .1, .07))
        def trees_(d):
            for tx in (.1, .18, .26, .44): d.polygon([(W * tx, H * .3), (W * (tx - .05), H * .72), (W * (tx + .05), H * .72)], fill=255)
            d.rectangle([W * .6, H * .52, W * .68, H * .66], fill=255); d.polygon([(W * .58, H * .52), (W * .64, H * .44), (W * .7, H * .52)], fill=255)   # 작은 집
        a = over(a, layer(trees_, 3), (.05, .07, .05))
        win_ = layer(lambda d: d.rectangle([W * .625, H * .56, W * .645, H * .6], fill=255), 1); a = over(a, win_, (.85, .6, .25))
        lake = layer(lambda d: d.ellipse([W * .5, H * .8, W * .98, H * .92], fill=255), 5); a = over(a, lake * .6, (.3, .32, .3))
    P3 = np.column_stack([xx.ravel() * 3, yy.ravel() * 3, np.zeros(W * H)])
    brush = tex.fbm(P3 * np.array([60, 14, 1]), 1.0, 3, seed=54 + kind).reshape(H, W)
    a = a * (1 + .1 * brush[..., None])
    vig = np.clip(1 - (((xx - .5) / .6) ** 2 + ((yy - .5) / .65) ** 2), 0, 1) ** .5
    a = a * (.55 + .45 * vig[..., None]) * np.array([1.0, .92, .74])
    crq = (np.abs(tex.vnoise(P3 * 20, 1.0, seed=52 + kind)).reshape(H, W) < .03)
    a = a * (1 - .2 * crq[..., None])
    return np.clip(a, 0, 1)[::-1], crq[::-1]
for k, o in enumerate(pics):
    gw, gh = o['dims']; W = int(560 * gw / max(gw, gh)); H = int(560 * gh / max(gw, gh))
    a, crq = painting((1, 0, 2)[k], W, H)
    o.data.materials.append(tex.material(f'Lounge_Painting{k}', TD, a, .55 + .3 * crq, tex.h2n(crq.astype(float) * .5, 1.0), coat=(.4, .25)))

# 러그: 페르시아 런너 — 붉은 들판 + 헤라티 격자 · 남색 큰 테두리(덩굴 · 로제트) · 메달리온 3개 · 바램 · 플레이어 길 닳음
RX_, RY_ = 4096, 870; AS = RW / RD
vv, uu = (np.mgrid[0:RY_, 0:RX_] + .5) / np.array([RY_, RX_])[:, None, None]
xx_ = (uu - .5) * 2 * AS; yy_ = (vv - .5) * 2; ax_ = np.abs(xx_); ay_ = np.abs(yy_)
RED = np.array([.30, .04, .05]); RED2 = np.array([.24, .03, .04]); NAVY = np.array([.05, .07, .16]); IVORY = np.array([.64, .55, .42]); GOLD = np.array([.55, .38, .14]); TEAL = np.array([.08, .2, .2])
def put_(img, m, col):
    return img * (1 - m[..., None]) + np.asarray(col)[None, None, :] * m[..., None]
def soft(m, w=.004):
    return np.clip(.5 - m / w, 0, 1)
edge_d = np.minimum(AS - ax_, 1 - ay_)                                                               # 가장자리까지 거리 (폭 단위)
bmax = 1 - edge_d
P2r = np.stack([uu.ravel() * 3 * AS, vv.ravel() * 2, np.zeros(RX_ * RY_)], 1)
abrash = (np.sin(xx_ * 3 + tex.fbm(P2r, 2.0, 2, seed=44).reshape(RY_, RX_) * 2) * .5 + .5)
img = RED[None, None, :] * (1 - .25 * abrash[..., None]) + RED2[None, None, :] * (.25 * abrash[..., None])
gu, gv = xx_ * 6, yy_ * 6
lat = np.minimum(np.abs(((gu + gv) % 2) - 1), np.abs(((gu - gv) % 2) - 1))
img = put_(img, soft(lat - .06, .05) * .9, NAVY)
nodes = np.hypot(((gu + 1) % 2) - 1, ((gv + 1) % 2) - 1)
petal = np.cos(np.arctan2(((gv + 1) % 2) - 1, ((gu + 1) % 2) - 1) * 4) * .08 + .22
img = put_(img, soft(nodes - petal, .04), IVORY); img = put_(img, soft(nodes - .08, .03), GOLD)
leaf = np.hypot((gu % 2) - 1, ((gv % 2) - 1) * 1.8)
img = put_(img, soft(leaf - .18, .04) * .8, TEAL)
for mx in (-AS * .62, 0.0, AS * .62):                                                               # 메달리온 3개 + 위아래 펜던트
    th = np.arctan2(yy_ * 1.0, xx_ - mx); md = np.hypot(xx_ - mx, yy_ * 1.0)
    lob = .52 + .045 * np.cos(th * 12)
    img = put_(img, soft(md - lob, .01), NAVY); img = put_(img, soft(np.abs(md - lob) - .016, .008), IVORY)
    star = .3 + .08 * np.cos(th * 8)
    img = put_(img, soft(md - star, .008), RED); img = put_(img, soft(np.abs(md - star) - .011, .006), GOLD)
    img = put_(img, soft(md - .1, .008), IVORY); img = put_(img, soft(md - .05, .006), NAVY)
    for sx in (-1, 1):
        pd = np.hypot((xx_ - mx - sx * .66) * 2.6, yy_ * 2.2)
        img = put_(img, soft(pd - .14, .012), NAVY); img = put_(img, soft(np.abs(pd - .14) - .012, .007), IVORY)
for sx in (-1, 1):                                                                                   # 모서리 반 메달리온 (스팬드럴)
    for sy in (-1, 1):
        cd = np.hypot((xx_ - sx * (AS - .22)), (yy_ - sy * .78) * 1.45)
        img = put_(img, soft(cd - .3, .01), NAVY); img = put_(img, soft(np.abs(cd - .3) - .012, .006), IVORY)
img = put_(img, ((bmax > .78) & (bmax < .955)).astype(float), NAVY)
for g0 in (.955, .965, .975, .76, .77):
    img = put_(img, soft(np.abs(bmax - g0) - .003, .002), IVORY if g0 in (.965, .77) else RED)
img = put_(img, (bmax > .98).astype(float), RED2)
side = (AS - ax_) < (1 - ay_)
bt = np.where(side, yy_, xx_)
bw_ = (bmax - .7775) / (.955 - .7775); inband = (bw_ > 0) & (bw_ < 1)
img = put_(img, soft(np.abs(bw_ - .5 - .22 * np.sin(bt * 22)) - .03, .02) * inband, GOLD)
ros = np.hypot(((bt * 6) % 1 - .5) * 1.0, (bw_ - .5) * 1.0) * inband
rth = np.arctan2(bw_ - .5, (bt * 6) % 1 - .5)
img = put_(img, soft(ros - (.26 + .07 * np.cos(rth * 8)), .03) * inband, RED)
img = put_(img, soft(ros - .1, .02) * inband, IVORY)
fade = (tex.fbm(P2r, 2.0, 4, seed=41).reshape(RY_, RX_) * .5 + .5)
path = np.exp(-((yy_ - .05) / .45) ** 2)                                                              # 플레이어 길 (방 가운데 줄)
worn = np.clip(path * (fade * 1.1) - .55, 0, 1) * .6
warp_lines = (np.sin(uu * 900 * AS) > .3)
img = img * (1 - .12 * fade[..., None]) + np.array([.42, .34, .28]) * (.12 * fade[..., None])
img = img * (1 - worn[..., None] * .35) + np.where(warp_lines[..., None], np.array([.7, .64, .56]), np.array([.45, .4, .34])) * (worn[..., None] * .35)
pile = (tex.vnoise(np.stack([uu.ravel() * 500 * AS, vv.ravel() * 500, np.zeros(RX_ * RY_)], 1), 1.0, seed=3).reshape(RY_, RX_)) * (1 - worn)
rug.data.materials.append(tex.material('Lounge_PersianRunner', TD, np.clip(img, 0, 1), .88 + .08 * worn, tex.h2n(pile * .8, 1.2)))
S_of(fringe, 64); fringe.data.materials.append(odd.gltf_material('Lounge_RunnerFringe', base_value=(.78, .72, .6, 1), rough_value=.9))

# 담요: 짙은 남색 · 녹 · 크림 줄 무늬 + 양 끝 술 (알파)
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
# 8. 내보내기 (맞춤 가구만 — glb_merge.py가 v2.9 거실과 합친다)
# =====================================================================================
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.data.materials: print('NO MATERIAL', o.name)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons) for o in meshes)
GLB = os.path.join(odd.OUT, 'game', 'lounge_fit.glb')
print('GLB', GLB, odd.export_glb(GLB, meshes), 'bytes', 'tris', tris, 'objects', len(meshes))
