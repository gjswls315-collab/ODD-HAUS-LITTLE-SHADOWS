"""리뷰 후보 GLB → 게임용 GLB (겉모습만 바뀐다 — 이동 · 점프 · 충돌 · 퍼즐 · AI 코드는 그대로)

리뷰 후보는 게임 리그의 묶음 자세(rigs.json) 그대로 한 덩어리로 조형돼 있다. 게임은 GLB 노드의 extras.link = '<리그 이름>'을 보고
그 노드를 게임 리그 객체 밑으로 옮겨 붙인다(로컬 = 원점). 그래서 여기서는 메시를 바꾸지 않고 노드 구조만 만든다:
  - 단단한 부위(머리 · 손 · 신발 · 눈 · 기타 …): 리그 노드 밑에 붙이고, 메시 노드 행렬 = (리그 노드 묶음 자세)⁻¹
  - 휘는 부위(팔다리 · 몸통 · 바지 · 털 몸): 리그 노드를 뼈로 쓰는 스킨 — 정점마다 뼈 캡슐까지 거리로 가중치(가까운 4개)
  - Bully 기타: 게임 기타 노드(넥 = 로컬 +X, 앞면 = +Z, 0.88배)의 좌표계로 옮긴다 — 브리지 자리를 맞춰 손 IK 목표(줄 치는 곳 · 넥)가 기타 위에 온다
사용: python game_link.py <vin|buddy|bully> <리뷰.glb> <rigs.json> <출력.glb>
"""
import sys, json, struct, re, math
import numpy as np


# ---------------------------------------------------------------- GLB 읽기 · 쓰기
def read_glb(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'glTF'
    jl = struct.unpack('<I', b[12:16])[0]; J = json.loads(b[20:20 + jl])
    o = 20 + jl; bl = struct.unpack('<I', b[o:o + 4])[0]
    return J, bytearray(b[o + 8:o + 8 + bl])


def write_glb(path, J, bin_):
    while len(bin_) % 4: bin_.append(0)
    J['buffers'] = [{'byteLength': len(bin_)}]
    js = json.dumps(J, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    while len(js) % 4: js += b' '
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
    open(path, 'wb').write(out)


CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def acc_read(J, bin_, i):
    a = J['accessors'][i]; bv = J['bufferViews'][a['bufferView']]; dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); stride = bv.get('byteStride', dt.itemsize * n)
    raw = np.frombuffer(bin_, np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * n, offset=off)
    rows = np.lib.stride_tricks.as_strided(raw, (a['count'], dt.itemsize * n), (stride, 1))
    return np.ascontiguousarray(rows).view(dt).reshape(a['count'], n)


def acc_add(J, bin_, arr, comp, typ, target=None):
    arr = np.ascontiguousarray(arr.astype(CT[comp]))
    while len(bin_) % 4: bin_.append(0)
    off = len(bin_); bin_ += arr.tobytes()
    bv = {'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes}
    if target: bv['target'] = target
    J['bufferViews'].append(bv)
    a = {'bufferView': len(J['bufferViews']) - 1, 'componentType': comp, 'count': len(arr), 'type': typ}
    J['accessors'].append(a)
    return len(J['accessors']) - 1


# ---------------------------------------------------------------- 행렬
def quat_m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(p, q, s):
    M = np.eye(4); M[:3, :3] = quat_m(q) * np.array(s)[None, :]; M[:3, 3] = p; return M


def colmajor(M):
    return [float(v) for v in M.T.reshape(-1)]


# ---------------------------------------------------------------- 가중치: 뼈 캡슐까지 거리 (역거리 거듭제곱, 가까운 4개)
def seg_dist(P, a, b):
    ab = b - a; L2 = max(float(ab @ ab), 1e-12)
    t = np.clip((P - a) @ ab / L2, 0, 1)
    return np.linalg.norm(P - (a[None] + t[:, None] * ab[None]), axis=1)


def cap_weights(P, caps, p=4, delta=.01):
    D = np.stack([np.maximum(seg_dist(P, np.array(a), np.array(b)) - r, 0) for a, b, r in caps], 1)
    W = 1.0 / (D + delta) ** p
    k = min(4, W.shape[1])
    idx = np.argsort(-W, 1)[:, :k]; w = np.take_along_axis(W, idx, 1)
    w /= w.sum(1, keepdims=True)
    w[w < .02] = 0; w /= w.sum(1, keepdims=True)                       # 아주 작은 영향은 버린다 (먼 뼈가 살짝 끌고 가지 않게)
    if k < 4:
        idx = np.concatenate([idx, np.zeros((len(P), 4 - k), int)], 1); w = np.concatenate([w, np.zeros((len(P), 4 - k))], 1)
    return idx, w


def islands(tri, nv):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)), directed=False)
    return lab


# ---------------------------------------------------------------- 캐릭터별 연결표
def chain(R, names, ext=None):
    """관절 이름 사슬 → 캡슐 끝점 (k → k+1, 마지막은 앞 마디 방향으로 ext배 연장)"""
    P = [np.array(R[n]['p']) for n in names]; out = {}
    for k, n in enumerate(names):
        b = P[k + 1] if k + 1 < len(P) else P[k] + (P[k] - P[k - 1]) * (ext if ext is not None else .6)
        out[n] = (P[k], b)
    return out


def spec_vin(R):
    caps = {}
    for limb in ('arm0', 'arm1', 'leg0', 'leg1'):
        for n, (a, b) in chain(R, [f'{limb}_{k}' for k in range(7)], .5).items(): caps[n] = (a, b, .0045)
    rigid = [(r'^Vin_(Body|Label)$', 'spin'),                       # 레코드 몸(라벨 포함)은 달릴 때 레코드처럼 돈다
             (r'^Vin_(Eye|Pupil)0$', 'eye0'), (r'^Vin_(Eye|Pupil)1$', 'eye1'),   # 눈 깜빡임 = 눈 노드 세로 크기 (동공은 눈에 고정)
             (r'^Vin_(Glove|Cuff)0$', 'hand0'), (r'^Vin_(Glove|Cuff)1$', 'hand1'),
             (r'^Vin_Shoe0_', 'shoe0'), (r'^Vin_Shoe1_', 'shoe1'), (r'^Vin_Grommet_', 'disc')]
    skins = [(r'^Vin_Arm0$', [f'arm0_{k}' for k in range(7)]), (r'^Vin_Arm1$', [f'arm1_{k}' for k in range(7)]),
             (r'^Vin_Leg0$', [f'leg0_{k}' for k in range(7)]), (r'^Vin_Leg1$', [f'leg1_{k}' for k in range(7)])]
    return dict(prefix='VIN', root={'oddRig': 'hero', 'character': 'vin', 'height': .24}, rigid=rigid, skins=skins, caps=caps, p=4, delta=.002)


def spec_buddy(R):
    P = lambda n: np.array(R[n]['p'])
    caps = {'body': (np.array([0, .19, -.17]), np.array([0, .245, .085]), .085),
            'neck': (P('neck'), P('head'), .05),
            'head': (np.array([0, .405, .03]), np.array([0, .375, .19]), .07)}
    for i in range(4):
        for n, (a, b) in chain(R, [f'hip{i}', f'knee{i}', f'paw{i}'], None).items(): caps[n] = (a, b, .028)
        a = P(f'paw{i}'); caps[f'paw{i}'] = (a, a + np.array([0, -.012, .035]), .022)
    for n, (a, b) in chain(R, ['tail0', 'tail1', 'tail2', 'tail3'], 1.2).items(): caps[n] = (a, b, .03)
    body_j = ['body', 'neck', 'head'] + [f'{j}{i}' for i in range(4) for j in ('hip', 'knee', 'paw')] + ['tail0', 'tail1', 'tail2', 'tail3']
    rigid = [(r'^Buddy_Eye0$', 'eye0'), (r'^Buddy_Eye1$', 'eye1'), (r'^Buddy_(EyeRim\d|Nose)$', 'head'),
             (r'^Buddy_Ear0$', 'ear0'), (r'^Buddy_Ear1$', 'ear1'),
             (r'^Buddy_(Collar|TieKnot)$', 'neck'), (r'^Buddy_Tie$', 'tie'), (r'^Buddy_(Tag|TagRing)$', 'tag')]
    skins = [(r'^Buddy_Body$', body_j), (r'^Buddy_FurCards$', body_j + ['ear0', 'ear1'])]
    caps['ear0'] = (P('ear0'), P('ear0') + np.array([-.02, -.09, 0]), .02); caps['ear1'] = (P('ear1'), P('ear1') + np.array([.02, -.09, 0]), .02)
    return dict(prefix='BUDDY', root={'oddRig': 'buddy', 'character': 'buddy', 'shoulder': .33}, rigid=rigid, skins=skins, caps=caps, p=4, delta=.006,
                card_islands={'Buddy_FurCards': 'Buddy_Body'}, marker='shoulder')


def spec_bully(R):
    P = lambda n: np.array(R[n]['p'])
    caps = {'pelvis': (np.array([0, .72, 0]), np.array([0, .86, 0]), .11),
            'spine': (np.array([0, .86, 0]), np.array([0, 1.19, 0]), .13),
            'head': (np.array([0, 1.27, .02]), np.array([0, 1.45, .03]), .085)}
    for s in (0, 1):
        for n, (a, b) in chain(R, [f'sho{s}', f'elb{s}', f'hand{s}'], .45).items(): caps[n] = (a, b, .035)
        for n, (a, b) in chain(R, [f'hip{s}', f'knee{s}', f'foot{s}'], None).items(): caps[n] = (a, b, .06)
        f = P(f'foot{s}'); caps[f'foot{s}'] = (f, f + np.array([0, -.05, .1]), .04)
    arms = [f'{j}{s}' for s in (0, 1) for j in ('sho', 'elb', 'hand')]
    legs = [f'{j}{s}' for s in (0, 1) for j in ('hip', 'knee', 'foot')]
    rigid = [(r'^Bully_(Eye\d|Ear\d|Cap|CapButton|CapSnap|CapBrim|HairMass|Hair)$', 'head'),     # 눈알은 머리에 (눈꺼풀이 조형돼 있다 — 게임의 눈 노드 크기 깜빡임을 쓰지 않는다)
             (r'^Bully_Brow0$', 'brow0'), (r'^Bully_Brow1$', 'brow1'),
             (r'^Bully_Hand0$', 'hand0'), (r'^Bully_Hand1$', 'hand1'), (r'^Bully_Band0$', 'elb0'), (r'^Bully_Band1$', 'elb1'),
             (r'^Bully_Shoe0_', 'foot0'), (r'^Bully_Shoe1_', 'foot1'),
             (r'^Bully_(TeeRib|Strap|Buckle|Chain|Pendant)$', 'spine'),
             (r'^Bully_(Guitar\w*|Pickguard|Pickup\d|Bridge|Saddles|Knob\d|Switch|Tuners)$', 'guitar')]
    skins = [(r'^Bully_Head$', ['head', 'spine']), (r'^Bully_Body$', ['pelvis', 'spine', 'head'] + arms + legs),
             (r'^Bully_Tee$', ['pelvis', 'spine', 'sho0', 'sho1']), (r'^Bully_Pants$', ['pelvis'] + legs)]
    # 리뷰 스트랫(bully.py 8절): 기타 로컬 (u 가로 · a 넥 · w 앞) cm, 0.88배 — 게임 기타 노드 로컬(넥 +X · 앞 +Z, 노드 크기 0.88)로
    NF = np.array([0, .14, 1.0]); NF /= np.linalg.norm(NF)
    A_ = np.array([math.cos(math.radians(27)), math.sin(math.radians(27)), 0.0]); A_ -= NF * (A_ @ NF); A_ /= np.linalg.norm(A_)
    U_ = np.cross(NF, A_); U_ /= np.linalg.norm(U_)
    GS = .88; G0 = np.array([-6.5, 77.5, 15.6]) + A_ * (22 * GS)
    C_ = .17                                                         # 넥 방향 자리: 줄 치는 곳(x −0.07) = 미들·브리지 픽업 사이, 왼손(x 0.38 · 0.50) = 넥 · 너트
    Mg = np.eye(4); Mg[0, :3] = A_ / GS; Mg[1, :3] = U_ / GS; Mg[2, :3] = NF / GS
    Mg[:3, 3] = [-(G0 @ A_) / (100 * GS) + .02 + C_, -(G0 @ U_) / (100 * GS), -(G0 @ NF) / (100 * GS)]
    return dict(prefix='BULLY', root={'oddRig': 'bully', 'character': 'bully', 'height': 1.5}, rigid=rigid, skins=skins, caps=caps, p=4, delta=.01,
                local_override={'guitar': Mg}, marker='height')


SPECS = {'vin': spec_vin, 'buddy': spec_buddy, 'bully': spec_bully}


def main(who, src, rigs, dst):
    R = json.load(open(rigs))[who]; S = SPECS[who](R)
    J, bin_ = read_glb(src)
    nodes = J['nodes']; N0 = len(nodes); scene = J['scenes'][J.get('scene', 0)]
    for n in nodes: assert not any(k in n for k in ('translation', 'rotation', 'scale', 'matrix')), '리뷰 GLB 노드는 월드 좌표(변환 없음)여야 한다'
    bind = {k: trs(v['p'], v['q'], v['s']) for k, v in R.items()}
    link_idx = {}

    def link_node(rig):
        if rig not in link_idx:
            M = bind[rig]
            nodes.append({'name': f"{S['prefix']}_{rig}", 'matrix': colmajor(M), 'extras': {'link': rig}, 'children': []})
            link_idx[rig] = len(nodes) - 1
        return link_idx[rig]

    def positions(mi):
        return [acc_read(J, bin_, p_['attributes']['POSITION']).astype(np.float64) for p_ in J['meshes'][mi]['primitives']]

    used, report = set(), []
    # 단단한 부위
    for i in range(N0):
        nm = nodes[i].get('name', '')
        for rx, rig in S['rigid']:
            if re.search(rx, nm):
                li = link_node(rig); nodes[li]['children'].append(i)
                L = S.get('local_override', {}).get(rig)
                nodes[i]['matrix'] = colmajor(L if L is not None else np.linalg.inv(bind[rig]))
                used.add(i); report.append((nm, 'rigid', rig)); break
    # 스킨
    root_children = []
    body_pts = {}
    for i in range(N0):
        if i in used: continue
        nm = nodes[i].get('name', '')
        for rx, joints in S['skins']:
            if not re.search(rx, nm): continue
            caps = [S['caps'][j] for j in joints]
            jn = [link_node(j) for j in joints]
            prims = J['meshes'][nodes[i]['mesh']]['primitives']
            for pi, p_ in enumerate(prims):
                Pv = acc_read(J, bin_, p_['attributes']['POSITION']).astype(np.float64)
                src_body = S.get('card_islands', {}).get(nm)
                if src_body:                                                    # 털 카드: 카드마다 뿌리(몸에 가장 가까운 점)의 가중치를 통째로
                    from scipy.spatial import cKDTree
                    bi = next(k for k in range(N0) if nodes[k].get('name') == src_body)
                    if src_body not in body_pts: body_pts[src_body] = np.concatenate(positions(nodes[bi]['mesh']))
                    tri = acc_read(J, bin_, p_['indices']).reshape(-1, 3).astype(np.int64)
                    lab = islands(tri, len(Pv)); dist, _ = cKDTree(body_pts[src_body]).query(Pv)
                    root = np.zeros(lab.max() + 1, int); best = np.full(lab.max() + 1, 1e9)
                    for v in range(len(Pv)):
                        if dist[v] < best[lab[v]]: best[lab[v]] = dist[v]; root[lab[v]] = v
                    idx, w = cap_weights(Pv[root], caps, S['p'], S['delta']); idx, w = idx[lab], w[lab]
                else:
                    idx, w = cap_weights(Pv, caps, S['p'], S['delta'])
                p_['attributes']['JOINTS_0'] = acc_add(J, bin_, idx, 5121, 'VEC4', 34962)
                p_['attributes']['WEIGHTS_0'] = acc_add(J, bin_, w, 5126, 'VEC4', 34962)
                dom = np.bincount(idx[:, 0], weights=w[:, 0], minlength=len(joints)) / len(Pv)
                report.append((nm + (f'[{pi}]' if len(prims) > 1 else ''), 'skin', ' '.join(f'{j}:{d:.2f}' for j, d in zip(joints, dom) if d > .005)))
            ibm = np.stack([np.linalg.inv(bind[j]).T.reshape(-1) for j in joints])         # 열 우선
            J.setdefault('skins', []).append({'joints': jn, 'inverseBindMatrices': acc_add(J, bin_, ibm, 5126, 'MAT4'), 'name': nm + '_Skin'})
            nodes[i]['skin'] = len(J['skins']) - 1
            root_children.append(i); used.add(i); break
    left = [nodes[i].get('name') for i in range(N0) if i not in used]
    assert not left, f'연결표에 없는 부위: {left}'
    # 표식 (비율 검사): Bully 키 = 머리 · 캡 맨 위, Buddy 어깨 = 등선이 목으로 올라가기 전 가장 높은 곳
    extra_nodes = []
    if S.get('marker') == 'height':
        top = max(float(np.concatenate(positions(nodes[k]['mesh']))[:, 1].max()) for k in range(N0) if re.search(r'^Bully_(Head|Cap|HairMass)$', nodes[k].get('name', '')))
        nodes.append({'name': f"{S['prefix']}_Marker_Height", 'translation': [0, top, 0], 'extras': {'marker': 'height'}}); extra_nodes.append(len(nodes) - 1)
        report.append(('marker', 'height', f'{top * 100:.1f} cm'))
    if S.get('marker') == 'shoulder':
        bi = next(k for k in range(N0) if nodes[k].get('name') == 'Buddy_Body'); Pb = np.concatenate(positions(nodes[bi]['mesh']))
        z0 = float(R['hip0']['p'][2]) - .14                                   # 앞다리 뿌리보다 14 cm 뒤 = 목 덩어리가 올라가기 직전의 등 (기갑)
        m = (np.abs(Pb[:, 0]) < .02) & (np.abs(Pb[:, 2] - z0) < .01)
        sh = float(Pb[m, 1].max())
        nodes.append({'name': f"{S['prefix']}_Marker_Shoulder", 'translation': [0, sh, z0], 'extras': {'marker': 'shoulder'}}); extra_nodes.append(len(nodes) - 1)
        report.append(('marker', 'shoulder', f'{sh * 100:.1f} cm (게임 안 크기 = 리그 루트 배율 적용)'))
    # 루트 = 리그 'root' (게임은 이 노드도 리그 루트 밑으로 옮긴다)
    kids = [li for rig, li in link_idx.items()] + root_children + extra_nodes
    root = {'name': f"{S['prefix']}_root", 'children': kids,
            'extras': dict({'link': 'root', 'unit': 'm', 'note': f"ODD HAUS {S['root']['character']} — 리뷰 후보를 게임 리그에 연결 (tools/blender/game_link.py). 노드 extras.link = 게임 리그 이름"}, **S['root'])}
    nodes.append(root); ri = len(nodes) - 1
    for sk in J.get('skins', []): sk['skeleton'] = ri
    for n in nodes:
        if 'children' in n and not n['children']: del n['children']
    scene['nodes'] = [ri]
    J['asset']['generator'] = (J['asset'].get('generator', '') + ' + ODD HAUS game_link').strip()
    write_glb(dst, J, bin_)
    for r in report: print('  ', *r)
    print('GAME GLB', dst, len(open(dst, 'rb').read()), 'bytes · 리그 노드', len(link_idx), '· 스킨', len(J.get('skins', [])))


if __name__ == '__main__':
    main(*sys.argv[1:5])
