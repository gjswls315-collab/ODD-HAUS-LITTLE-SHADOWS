"""빨간 하이탑 운동화 (Vin · Bully 공용) — 부품을 실제 신발 구조대로 따로 만든다.
  밑창: 발 모양 윤곽 로프트(둥근 바닥 모서리 · 폭싱 옆벽 · 줄 홈 · 앞코 범퍼가 올라온다)
  갑피: SDF 라스트(발등 · 발목 기둥 · 뒤꿈치 · 앞코를 녹여 붙임) → 쿼드 리토폴로지 → 칼라 · 끈 자리를 평면으로 잘라 열고 두께
  혀: 끈 자리 아래 원래 표면을 떼어 넓히고 안으로 넣어 패드 두께, 칼라 위로 나온다
  토캡: 앞코 표면을 덮는 고무 껍질 · 아일릿: 끈 자리 가장자리를 따라 금속 고리
  끈: 아일릿 사이를 엇갈려 혀 위로 지나 위에서 나비 매듭 (고리 둘 · 끝 두 가닥 · 애글릿)
로컬 단위 cm: x 바깥쪽(+), y 앞(+), z 위. place(Vector cm) → 월드(m).
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import odd

TAU = math.tau


def footprint(y, L0, L1):
    """발바닥 윤곽 반폭(cm) — 뒤꿈치 둥글게 · 허리 잘록 · 볼 넓게 · 앞코 둥글게."""
    t = (y - L0) / (L1 - L0)
    w = 1.30 + .45 * math.exp(-((t - .70) / .22) ** 2) - .12 * math.exp(-((t - .38) / .12) ** 2)
    if t < .14:
        w *= math.sqrt(max(0.0, 1 - ((.14 - t) / .14) ** 2)) * .92 + .08 * (t / .14)
    if t > .86:
        w *= math.sqrt(max(0.0, 1 - ((t - .86) / .14) ** 2))
    return w


def outline(n, L0, L1, inset=0.0):
    ys = [L0 + (L1 - L0) * (1 - math.cos(math.pi * k / (n // 2))) / 2 for k in range(n // 2 + 1)]
    right = [(max(footprint(y, L0, L1) - inset, .02), y) for y in ys]
    return right + [(-x, y) for x, y in reversed(right[1:-1])]


class Frame:
    """로컬(cm) ↔ 월드 변환. side = 바깥쪽 x 부호."""

    def __init__(self, place, side):
        self.place = place; self.side = side
        o = place(Vector((0, 0, 0)))
        self.o = np.array(o)
        self.M = np.column_stack([np.array(place(Vector(e)) - o) for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))])
        self.Mi = np.linalg.inv(self.M)

    def W(self, x, y, z):
        return self.place(Vector((x * self.side, y, z)))

    def L(self, a):
        q = (np.asarray(a) - self.o) @ self.Mi.T
        q[:, 0] *= self.side
        return q

    def dir(self, x, y, z):
        return (self.W(x, y, z) - self.W(0, 0, 0)).normalized()


def _clean(o, dist):
    """평면 자르기로 생긴 아주 짧은 모서리 · 얇은 조각 면을 합친다 (두께를 줄 때 가시가 생기지 않게)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=dist)
    bm.to_mesh(o.data); bm.free(); o.data.update()


def _keep_faces(o, pred):
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [f for f in bm.faces if not pred(f)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(o.data); bm.free()


def _bisect(o, co, no, clear_inner=False, clear_outer=False):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_inner=clear_inner, clear_outer=clear_outer)
    bm.to_mesh(o.data); bm.free()


def build(prefix, place, side=1, L0=-2.4, L1=4.8, H=4.6, collar_y=-1.0, scale=1.0, retopo_faces=950):
    F = Frame(place, side); W = F.W; mm = .001 * scale        # mm: 1 mm (Vin 크기 기준) → 월드
    parts = {}
    # ---------------- 밑창 ----------------
    n = 64
    levels = [(0.00, .12), (.03, .05), (.10, .0), (.55, .0), (.62, .03), (.66, -.02), (.92, -.02), (.98, .05), (1.0, .14)]
    sole = odd.loft(prefix + '_Sole', [[W(x, y, z) for x, y in outline(n, L0, L1, ins)] for z, ins in levels], cap_start=True, cap_end=True)
    a = odd.co(sole); q = F.L(a)
    up = np.clip((q[:, 1] - (L1 - 1.4)) / 1.4, 0, 1) ** 1.5 * .55 + np.clip(((L0 + .7) - q[:, 1]) / .7, 0, 1) * .12
    top = np.clip((q[:, 2] - .5) / .5, 0, 1)
    odd.set_co(sole, a + np.array(F.dir(0, 0, 1)) * (up * top * 10 * mm)[:, None])
    odd.subsurf(sole, 1)
    a = odd.co(sole); q = F.L(a); nn = odd.nrm(sole)
    side_wall = np.abs(nn @ np.array(F.dir(0, 0, 1))) < .6
    groove = np.exp(-((q[:, 2] - .38) / .035) ** 2) * side_wall
    odd.set_co(sole, a - nn * (groove * .35 * mm)[:, None])
    parts['sole'] = sole

    # ---------------- 갑피 라스트 (SDF) ----------------
    def lastfn(p):
        q = F.L(p); x, y, z = q[:, 0], q[:, 1], q[:, 2]
        hw = np.array([footprint(v, L0, L1) for v in np.clip(y, L0, L1)]) - .05 - .24 * np.clip((1.2 - z) / .5, 0, 1)   # 아래는 밑창 테 안으로 들어간다
        top = np.interp(y, [L0, collar_y - .5, collar_y + 1.0, 1.4, 2.6, 3.8, L1], [2.2, 2.9, 3.0, 2.75, 2.25, 1.85, 1.2])
        foot = odd.smax(np.abs(x) - hw, odd.smax(z - top, .62 - z, .25), .55)
        foot = odd.smax(foot, odd.smax(y - L1 + .05, L0 + .05 - y, .45), .45)
        sh = odd.sd_round_cone(q, (0, collar_y, 1.5), (0, collar_y - .1, H + .9), 1.42, 1.30)
        d = odd.smin(foot, sh, .6)
        # 밑창 테 안으로 들어가게: 낮은 곳은 발바닥 윤곽(조금 안쪽) 밖으로 나가지 않는다
        tuck = .05 + .24 * np.clip((1.2 - z) / .5, 0, 1)
        g = odd.smax(np.abs(x) - (np.array([footprint(v, L0, L1) for v in np.clip(y, L0, L1)]) - tuck), odd.smax(y - (L1 - tuck), (L0 + tuck) - y, .3), .3)
        return odd.smax(d, g, .15) * .01 * scale
    box = np.array([np.array(W(x, y, z)) for x in (-2.8, 2.8) for y in (L0 - 1.0, L1 + .8) for z in (-.4, H + 2.6)])
    dense = odd.sdf_mesh(prefix + '_last', lastfn, box.min(0), box.max(0), .4 * mm)
    odd.smooth(dense, 2, .4)
    shell = odd.retopo(dense, retopo_faces, 1, prefix + '_Upper')
    # 칼라(앞이 낮게 기울어진 평면) · 바닥(밑창 속) 자르기
    _bisect(shell, W(0, collar_y, H - .1), F.dir(0, .35, 1), clear_outer=True)
    _bisect(shell, W(0, 0, .72), F.dir(0, 0, 1), clear_inner=True)
    # 끈 자리: x = ±.36 평면 + 발등 끝 평면으로 나눈다
    for sx in (-.36, .36):
        _bisect(shell, W(sx, 0, 0), F.dir(1, 0, 0))
    TE = (0, 1.75, 2.6); TEn = F.dir(0, 1, .55)
    _bisect(shell, W(*TE), TEn)
    _clean(shell, .12 * mm)

    def throat(f):
        c = F.L(np.array([f.calc_center_median()]))[0]
        return abs(c[0]) < .36 and c[2] > 1.9 and c[1] > collar_y + .35 and (c[1] - TE[1]) + (c[2] - TE[2]) * .55 < 0
    def tongue_area(f):                       # 혀는 끈 자리보다 넓고(눈 · 아일릿 밑까지) 발등 쪽으로 더 길다
        c = F.L(np.array([f.calc_center_median()]))[0]
        return abs(c[0]) < .64 and c[2] > 1.9 and c[1] > collar_y + .35 and (c[1] - TE[1] - .5) + (c[2] - TE[2]) * .55 < 0
    tg = bpy.data.objects.new(prefix + '_Tongue', shell.data.copy()); odd.link(tg)
    _keep_faces(tg, tongue_area)
    _keep_faces(shell, lambda f: not throat(f))
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(shell, dg)

    # ---------------- 토캡 (앞코 고무) ----------------
    tc = bpy.data.objects.new(prefix + '_ToeCap', shell.data.copy()); odd.link(tc)
    _bisect(tc, W(0, L1 - 1.35, 1.0), F.dir(0, 1, -.35), clear_inner=True)
    _bisect(tc, W(0, 0, 2.15), F.dir(0, 0, 1), clear_outer=True)
    _clean(tc, .12 * mm)
    a = odd.co(tc); odd.set_co(tc, a + odd.nrm(tc) * .45 * mm)
    odd.solidify(tc, .9 * mm, offset=1)
    parts['toecap'] = tc

    # ---------------- 아일릿 자리: 끈 자리 테두리(경계 정점)를 따라 ----------------
    bm = bmesh.new(); bm.from_mesh(shell.data); bm.verts.ensure_lookup_table()
    A = np.array([0, TE[1], TE[2]]); B = np.array([0, collar_y + .45, H - .55]); AB = B - A
    edge = {-1: [], 1: []}
    for e in bm.edges:
        if not e.is_boundary:
            continue
        for v in e.verts:
            q = F.L(np.array([v.co]))[0]
            if abs(abs(q[0]) - .36) < .04 and q[2] > 1.9:
                s = (q - A) @ AB / (AB @ AB); edge[1 if q[0] > 0 else -1].append((s, Vector(v.co)))
    bm.free()
    eyelets = {-1: [], 1: []}
    for sx in (-1, 1):
        pts = sorted(edge[sx], key=lambda t: t[0])
        for s in np.linspace(.1, .9, 6):
            k = min(range(len(pts)), key=lambda j: abs(pts[j][0] - s)); p = pts[k][1]
            p = p + F.dir(sx, 0, 0) * (.17 * 10 * mm)
            loc, nrm_, _, _ = bvh.find_nearest(p); eyelets[sx].append((loc, nrm_))
    rings = []
    for sx in (-1, 1):
        for p, nv in eyelets[sx]:
            rings.append(_eyelet('_ey', p, nv, 1.25 * mm, .4 * mm))
    parts['eyelets'] = odd.join(rings, prefix + '_Eyelets')

    # ---------------- 혀: 넓히고 안으로, 위를 칼라 밖으로 늘려 패드 두께 ----------------
    bm = bmesh.new(); bm.from_mesh(tg.data)
    top_edges = [e for e in bm.edges if e.is_boundary and all(F.L(np.array([v.co]))[0][2] > H - 1.2 for v in e.verts)]
    ext = bmesh.ops.extrude_edge_only(bm, edges=top_edges)
    nv = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(F.dir(0, -.25, 1) * (8.5 * mm)))
    bm.to_mesh(tg.data); bm.free()
    a = odd.co(tg); q = F.L(a)
    widen = np.array(F.dir(1, 0, 0)) * (q[:, 0] * .08 * 10 * mm)[:, None]
    s_ = (q - A) @ AB / (AB @ AB)                              # 끈 자리 축 위치: 발등 끝(0) → 칼라(1)
    depth = 1.6 * np.clip(s_ / .22, .12, 1)                    # 발등 끝에서는 혀가 갑피 바로 밑에 붙는다 (틈 없음)
    odd.set_co(tg, a + widen - odd.nrm(tg) * (depth * mm)[:, None])
    odd.smooth(tg, 2, .3)
    odd.solidify(tg, 2.2 * mm, offset=-1); odd.subsurf(tg, 1)
    parts['tongue'] = tg

    # ---------------- 갑피 두께 · 칼라 패드 · 앞코 굽힘 주름 ----------------
    odd.solidify(shell, 1.3 * mm, offset=-1)
    a = odd.co(shell); q = F.L(a); nn = odd.nrm(shell)
    cd = (q - np.array([0, collar_y, H - .1])) @ (np.array([0, .35, 1]) / np.linalg.norm([0, .35, 1]))
    odd.set_co(shell, a + nn * (np.exp(-((cd + .25) / .22) ** 2) * 1.0 * mm)[:, None])
    for yy, dz in ((2.55, 0.0), (2.95, -.12)):
        a_, b_ = odd.project(shell, [W(-.9, yy, 2.4 + dz), W(.9, yy - .15, 2.4 + dz)])
        odd.crease(shell, a_, b_, 1.0 * mm, .28 * mm)
    # 패널 이음선: 앞 갑피(vamp)와 옆 갑피(quarter) — 끈 자리 아래 모서리에서 밑창 쪽으로 내려가는 곡선
    for sx in (-1, 1):
        ptsl = odd.project(shell, [W(sx * .5, TE[1] + .05, TE[2] + .3), W(sx * 1.25, 1.35, 2.0), W(sx * 1.45, .95, 1.25)])
        for a_, b_ in zip(ptsl[:-1], ptsl[1:]):
            odd.crease(shell, a_, b_, .7 * mm, .32 * mm)
    # 뒤꿈치 덧댐(backstay): 가운데 세로로 도톰한 띠 + 양쪽 이음선
    hb = odd.project(shell, [W(0, L0 - .5, 1.15), W(0, L0 - .5, H - .1)])
    a = odd.co(shell); d_, _, t_ = odd.seg_dist(a, hb[0], hb[1]); nn = odd.nrm(shell)
    odd.set_co(shell, a + nn * (np.clip(1 - (d_ / (3.2 * mm)) ** 4, 0, 1) * (t_ < .985) * .35 * mm)[:, None])
    for sx in (-1, 1):
        e_ = odd.project(shell, [W(sx * .33, L0 - .45, 1.15), W(sx * .3, L0 - .3, H - .3)])
        odd.crease(shell, e_[0], e_[1], .6 * mm, .25 * mm)
    parts['upper'] = shell

    # ---------------- 끈 ----------------
    lift = lambda p, nv, h: p + nv * (h * mm)
    laces = []
    L_, R_ = eyelets[-1], eyelets[1]
    for k in range(len(L_) - 1):
        for (pa, na), (pb, nb) in ((L_[k], R_[k + 1]), (R_[k], L_[k + 1])):
            nm = (na + nb).normalized(); mid = (pa + pb) / 2 + nm * (1.4 * mm)
            laces.append(odd.curve_tube('_lace', [lift(pa, na, .6), mid, lift(pb, nb, .6)], .5 * mm, res=6, bevel_res=2))
    (pa, na), (pb, nb) = L_[0], R_[0]
    laces.append(odd.curve_tube('_lace', [lift(pa, na, .5), (pa + pb) / 2 + (na + nb).normalized() * 1.0 * mm, lift(pb, nb, .5)], .5 * mm, res=6, bevel_res=2))
    (pa, na), (pb, nb) = L_[-1], R_[-1]
    out = (na + nb).normalized(); knot = (pa + pb) / 2 + out * 1.8 * mm
    dn = F.dir(0, .25, -1); sd = F.dir(1, 0, 0)
    for s_ in (-1, 1):
        loop = [knot, knot + sd * s_ * 4.5 * mm + dn * -2 * mm + out * 2.5 * mm, knot + sd * s_ * 8.5 * mm + dn * 1 * mm + out * 3.5 * mm,
                knot + sd * s_ * 4.5 * mm + dn * 3 * mm + out * 2 * mm, knot + out * .5 * mm]
        laces.append(odd.curve_tube('_lace', loop, .48 * mm, res=8, bevel_res=2))
        tail = [knot, knot + sd * s_ * 2 * mm + dn * 5 * mm + out * 2 * mm, knot + sd * s_ * 3.5 * mm + dn * 11 * mm + out * 1.5 * mm, knot + sd * s_ * 4 * mm + dn * 13 * mm + out * 1.4 * mm]
        laces.append(odd.curve_tube('_lace', tail, .48 * mm, res=8, bevel_res=2, radii=[1, 1, 1.25, 1.25]))
    laces.append(odd.curve_tube('_knot', [knot - sd * 1.2 * mm, knot + out * 1 * mm, knot + sd * 1.2 * mm], 1.1 * mm, res=6, bevel_res=3))
    parts['laces'] = odd.join(laces, prefix + '_Laces')
    odd.delete(dense)
    return parts


def _eyelet(name, p, n, r, t):
    """금속 아일릿: 둥근 단면 고리 (표면 법선 방향)."""
    n = n.normalized(); u = n.orthogonal().normalized(); v = n.cross(u)
    rings = []
    for k in range(10):
        a = TAU * k / 10; cr = r + math.cos(a) * t; ch = math.sin(a) * t
        rings.append([p + n * (ch + t * .5) + (u * math.cos(TAU * j / 12) + v * math.sin(TAU * j / 12)) * cr for j in range(12)])
    return odd.loft(name, rings + [rings[0]], closed=True)


def paint(parts, sl, fwd, TD, prefix, scale=1.0, H=4.6, collar_y=-1.0, size=1024):
    """신발 재질: 빨간 캔버스(결 · 박음질 · 이음선 · 밑창 쪽 때 · 앞코 주름 그늘) · 흰 고무 밑창(빨간 줄 · 뒤꿈치 라벨 · 바닥 트레드 · 때) ·
    토캡(다이아몬드 무늬) · 혀(흰 라벨 패치) · 끈 · 아일릿. sl: 월드 점 → 신발 로컬(cm, 배율 전), fwd: 앞 방향(월드)."""
    import tex
    k = 1.0 / scale                                   # 노이즈 주파수는 크기에 맞춘다
    out = {}
    o = parts['upper']; odd.uv_smart(o, 60, .005); Su = tex.Surf(o, size); q = sl(Su.p)
    hh = np.zeros(len(q))
    cn = np.array([0, .35, 1]) / np.linalg.norm([0, .35, 1]); cd = (q - np.array([0, collar_y, H - .1])) @ cn
    for off in (.22, .32):
        hh += np.clip(1 - np.abs(cd + off) / .035, 0, 1) * (np.sin((q[:, 0] * 3 + q[:, 1] * 3) * 7) > -.2)
    for sx in (-1, 1):
        for off in (.1, .19):
            hh += np.clip(1 - np.abs(np.abs(q[:, 0]) - (.36 + off)) / .03, 0, 1) * ((q[:, 0] * sx) > 0) * (q[:, 2] > 2.2) * (np.sin(q[:, 2] * 40) > -.2)
        seam = [np.array([sx * .5, 1.8, 2.9]), np.array([sx * 1.25, 1.35, 2.0]), np.array([sx * 1.45, .95, 1.25])]
        d, s_ = tex.polyline_dist(q, seam)
        hh += -np.exp(-(d / .03) ** 2) * .8 + np.clip(1 - np.abs(d - .09) / .03, 0, 1) * (np.sin(s_ * 40) > -.2)
        hh += np.clip(1 - np.abs(np.abs(q[:, 0]) - .38) / .03, 0, 1) * (q[:, 1] < -2.0) * (np.sin(q[:, 2] * 40) > -.2)
    weave = (np.sin(q[:, 0] * 260 + q[:, 2] * 12) + np.sin(q[:, 1] * 260 + q[:, 2] * 260)) * .07
    near_sole = np.clip((1.9 - q[:, 2]) / 1.0, 0, 1); toe = np.clip((q[:, 1] - 2.2) / 1.5, 0, 1)
    P = Su.p * k
    grime = np.clip(tex.fbm(P, 160, 4, seed=61) * .9 + .3, 0, 1) * (near_sole * .7 + toe * .3)
    fade = np.clip(tex.fbm(P, 40, 3, seed=62) * .5 + .5, 0, 1)
    col = np.array([.62, .055, .05])[None, :] * (.88 + .2 * fade[:, None]) * (1 - grime[:, None] * .35) + grime[:, None] * np.array([.05, .035, .025])
    col *= (1 - np.clip(-tex.fbm(P, 90, 2, seed=63), 0, 1)[:, None] * toe[:, None] * .3)
    out['upper'] = tex.material(prefix + '_ShoeCanvas', TD, Su.img(col), Su.img(.86 + .06 * grime), tex.h2n(Su.img(hh * .9 + weave), 1.6), sheen=(.4, .5, (1, .7, .7, 1)))
    o = parts['sole']; odd.uv_smart(o, 60, .005); Ss = tex.Surf(o, size); q = sl(Ss.p); P = Ss.p * k
    down = np.clip(-(Ss.n @ np.array([0, 0, 1.0])), 0, 1)
    col = np.tile(np.array([.86, .84, .78]), (len(q), 1))
    stripe = (np.abs(q[:, 2] - .38) < .05) & (down < .5)
    col = np.where(stripe[:, None], np.array([.62, .07, .06]), col)
    heel = (q[:, 1] < -2.1) & (np.abs(q[:, 0]) < .55) & (q[:, 2] > .52) & (q[:, 2] < .86)
    col = np.where(heel[:, None], np.array([.15, .14, .16]), col)
    grime = np.clip(tex.fbm(P, 220, 4, seed=71) * .8 + .35, 0, 1) * np.clip((.45 - q[:, 2]) / .45, 0, 1)
    col = col * (1 - grime[:, None] * .45) + grime[:, None] * np.array([.06, .05, .04])
    col = np.where(down[:, None] > .5, np.array([.62, .6, .55]) * (1 - .25 * np.clip(tex.fbm(P, 150, 3, seed=72), 0, 1))[:, None], col)
    tread = (np.abs(((q[:, 0] + q[:, 1]) * 4.5) % 1 - .5) < .17) | (np.abs(((q[:, 0] - q[:, 1]) * 4.5) % 1 - .5) < .17)
    hh = tread.astype(float) * down - stripe.astype(float) * .2
    out['sole'] = tex.material(prefix + '_ShoeRubber', TD, Ss.img(col), Ss.img(.62 + .2 * grime + .1 * down), tex.h2n(Ss.img(hh), 1.6))
    o = parts['toecap']; odd.uv_smart(o, 60, .005); St = tex.Surf(o, size // 2); q = sl(St.p)
    dia = (np.abs(((q[:, 0] + q[:, 2]) * 3.2) % 1 - .5) < .08) | (np.abs(((q[:, 0] - q[:, 2]) * 3.2) % 1 - .5) < .08)
    grime = np.clip(tex.fbm(St.p * k, 220, 4, seed=81) * .8 + .2, 0, 1) * .5
    col = np.array([.87, .85, .8])[None, :] * (1 - grime[:, None] * .3) + grime[:, None] * np.array([.03, .025, .02])
    out['toecap'] = tex.material(prefix + '_ToeCap', TD, St.img(col), St.img(.55 + .15 * grime), tex.h2n(St.img(-dia.astype(float) * .6), 1.4))
    o = parts['tongue']; odd.uv_smart(o, 60, .005); Sn = tex.Surf(o, size // 2); q = sl(Sn.p)
    patch = (np.abs(q[:, 0]) < .42) & (q[:, 2] > H - .25) & (Sn.n @ np.array(fwd) > .2)
    col = np.where(patch[:, None], np.array([.92, .9, .84]), np.array([.6, .055, .05]))
    weave = (np.sin(q[:, 0] * 260) + np.sin(q[:, 2] * 260)) * .07
    out['tongue'] = tex.material(prefix + '_Tongue', TD, Sn.img(col), Sn.img(np.where(patch, .7, .86)), tex.h2n(Sn.img(weave + patch.astype(float) * .3), 1.4))
    out['laces'] = odd.gltf_material(prefix + '_Laces', base_value=(.86, .85, .8, 1), rough_value=.92, sheen=(.4, .5, (1, 1, 1, 1)))
    out['eyelets'] = odd.gltf_material(prefix + '_Eyelets', base_value=(.78, .78, .8, 1), rough_value=.32, metal_value=1.0)
    for key, o in parts.items():
        o.data.materials.append(out[key])
    return out
