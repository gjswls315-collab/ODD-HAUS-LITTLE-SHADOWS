"""v2.9 거실 GLB + 맞춤 가구 GLB → 게임 거실 GLB (텍스처를 다시 압축하지 않고 GLB 수준에서 합친다)

1. 잘라내기: 바꾸는 가구 자리(게임 좌표 상자)에 무게중심이 들어가는 v2.9 삼각형을 뺀다 — 노드 이름(정규식)마다 상자 목록.
   통째로 바꾸는 메시(러그 · 커튼)는 상자를 크게 잡아 전부 뺀다.
2. 붙이기: 맞춤 가구 GLB의 노드 · 메시 · 재질 · 텍스처 · 이미지를 v2.9 루트(ENV_Lounge) 밑에 붙인다 (좌표 = 게임 월드 m).
3. 정리: 장면에서 닿지 않는 메시 · 재질 · 텍스처 · 이미지 · 버퍼를 버린다.
사용: python glb_merge.py <v2.9 거실.glb> <맞춤 가구.glb> <출력.glb>
"""
import sys, json, re
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from game_link import read_glb, write_glb, acc_read, acc_add

INF = 1e9
# 게임 좌표 상자 (x0, y0, z0, x1, y1, z1) — lounge_colliders.json의 가구 자리 + 여유
SOFA = (4.0, -.01, -.62, 6.32, 1.0, .52)
SIDE = (8.18, -.01, -.3, 8.78, 1.0, .3)
SIDE_CABLE = (8.12, -.02, -1.65, 8.8, 1.0, .3)                                  # 램프 → 뒷벽 전선 (상판 위 시작 부분 포함)
ROD = (8.95, 2.28, -1.62, 11.65, 2.46, -1.44)
def frame_box(x, y, w, h):
    return (x - w / 2 - .075, y - h / 2 - .075, -1.63, x + w / 2 + .075, y + h / 2 + .075, -1.38)
FRAMES = [frame_box(*f) for f in ((5.15, 1.5, .78, .52), (7.6, 1.72, .44, .56), (12.6, 1.8, .5, .66))]
ALL = (-INF, -INF, -INF, INF, INF, INF)
CUTS = [
    (r'^Lounge_(Velvet|VelvetDark|Button|Plaid)_Mesh$', [SOFA]),                       # 소파 · 쿠션 · 단추 · 베개
    (r'^Lounge_WalnutDark_Mesh$', [SOFA, SIDE]),                                       # 소파 다리 · 받침 테 / 사이드 테이블 다리 · 선반
    (r'^Lounge_(Walnut|Books|CeramicGreen)_Mesh$', [SIDE]),                            # 사이드 테이블 상판 · 선반 책 · 램프 몸통
    (r'^Lounge_Brass_Mesh$', [SIDE, ROD]),                                             # 램프 놋쇠 · 커튼 봉
    (r'^Lounge_TableLampShade$', [ALL]),
    (r'^Lounge_Cable_Mesh$', [SIDE_CABLE]),                                            # 램프 전선
    (r'^Lounge_Curtain_Mesh$', [ALL]),
    (r'^Lounge_(Gilt|Paintings)_Mesh$', FRAMES),
    (r'^Lounge_(PersianRug|RugFringe)$', [ALL]),
]


def inside(P, b):
    return (P[:, 0] >= b[0]) & (P[:, 0] <= b[3]) & (P[:, 1] >= b[1]) & (P[:, 1] <= b[4]) & (P[:, 2] >= b[2]) & (P[:, 2] <= b[5])


def cut(J, bin_, report):
    for n in J['nodes']:
        if 'mesh' not in n: continue
        boxes = next((bx for rx, bx in CUTS if re.search(rx, n.get('name', ''))), None)
        if not boxes: continue
        assert not any(k in n for k in ('translation', 'rotation', 'scale', 'matrix')), n.get('name')
        mesh = J['meshes'][n['mesh']]; keep_prims = []
        for p in mesh['primitives']:
            P = acc_read(J, bin_, p['attributes']['POSITION']).astype(np.float64)
            I = acc_read(J, bin_, p['indices']).reshape(-1, 3).astype(np.int64) if 'indices' in p else np.arange(len(P)).reshape(-1, 3)
            C = P[I].mean(1); hit = np.zeros(len(I), bool)
            for b in boxes: hit |= inside(C, b)
            report.append((n['name'], int(hit.sum()), len(I)))
            if hit.all(): continue
            if hit.any():
                keep = I[~hit].reshape(-1)
                p['indices'] = acc_add(J, bin_, keep, 5125 if len(P) > 65535 else 5123, 'SCALAR', 34963)
            keep_prims.append(p)
        mesh['primitives'] = keep_prims
        if not keep_prims: del n['mesh']


def append(J, bin_, K, kbin):
    """K(맞춤 가구)의 모든 것을 J 뒤에 붙인다. 반환: K 장면 루트 노드들의 새 번호"""
    off = {k: len(J.get(k, [])) for k in ('bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes')}
    while len(bin_) % 8: bin_.append(0)
    boff = len(bin_); bin_ += kbin
    for bv in K.get('bufferViews', []):
        bv = dict(bv); bv['byteOffset'] = bv.get('byteOffset', 0) + boff; bv['buffer'] = 0; J.setdefault('bufferViews', []).append(bv)
    for a in K.get('accessors', []):
        a = dict(a); a['bufferView'] += off['bufferViews']; J.setdefault('accessors', []).append(a)
    for im in K.get('images', []):
        im = dict(im)
        if 'bufferView' in im: im['bufferView'] += off['bufferViews']
        J.setdefault('images', []).append(im)
    J.setdefault('samplers', []).extend(K.get('samplers', []))
    def fix_tex(t):
        t = json.loads(json.dumps(t))
        if 'source' in t: t['source'] += off['images']
        if 'sampler' in t: t['sampler'] += off['samplers']
        for e in t.get('extensions', {}).values():
            if 'source' in e: e['source'] += off['images']
        return t
    J.setdefault('textures', []).extend(fix_tex(t) for t in K.get('textures', []))
    def fix_texrefs(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'index' and isinstance(v, int) and ('texCoord' in o or k == 'index'): o[k] = v + off['textures']
                else: fix_texrefs(v)
        elif isinstance(o, list):
            for v in o: fix_texrefs(v)
    for m in K.get('materials', []):
        m = json.loads(json.dumps(m)); fix_texrefs(m); J.setdefault('materials', []).append(m)
    for me in K.get('meshes', []):
        me = json.loads(json.dumps(me))
        for p in me['primitives']:
            p['attributes'] = {k: v + off['accessors'] for k, v in p['attributes'].items()}
            if 'indices' in p: p['indices'] += off['accessors']
            if 'material' in p: p['material'] += off['materials']
        J.setdefault('meshes', []).append(me)
    for n in K.get('nodes', []):
        n = json.loads(json.dumps(n))
        if 'mesh' in n: n['mesh'] += off['meshes']
        if 'children' in n: n['children'] = [c + off['nodes'] for c in n['children']]
        J['nodes'].append(n)
    for e in K.get('extensionsUsed', []):
        if e not in J.setdefault('extensionsUsed', []): J['extensionsUsed'].append(e)
    for e in K.get('extensionsRequired', []):
        if e not in J.setdefault('extensionsRequired', []): J['extensionsRequired'].append(e)
    return [i + off['nodes'] for i in K['scenes'][K.get('scene', 0)]['nodes']]


def gc(J, bin_):
    """장면에서 닿는 것만 남기고 번호를 다시 매긴다 + BIN을 다시 채운다."""
    sc = J['scenes'][J.get('scene', 0)]
    nodes_used, stack = [], list(sc['nodes'])
    while stack:
        i = stack.pop()
        if i in nodes_used: continue
        nodes_used.append(i); stack += J['nodes'][i].get('children', [])
    nodes_used.sort(); nmap = {o: k for k, o in enumerate(nodes_used)}
    meshes_used = sorted({J['nodes'][i]['mesh'] for i in nodes_used if 'mesh' in J['nodes'][i]}); mmap = {o: k for k, o in enumerate(meshes_used)}
    acc_used, mat_used = set(), set()
    for mi in meshes_used:
        for p in J['meshes'][mi]['primitives']:
            acc_used |= set(p['attributes'].values())
            if 'indices' in p: acc_used.add(p['indices'])
            if 'material' in p: mat_used.add(p['material'])
    for sk in J.get('skins', []): pass
    tex_used = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'index' and isinstance(v, int): tex_used.add(v)
                else: walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    for mi in mat_used: walk(J['materials'][mi])
    img_used, smp_used = set(), set()
    for ti in tex_used:
        t = J['textures'][ti]
        if 'source' in t: img_used.add(t['source'])
        if 'sampler' in t: smp_used.add(t['sampler'])
        for e in t.get('extensions', {}).values():
            if 'source' in e: img_used.add(e['source'])
    amap = {o: k for k, o in enumerate(sorted(acc_used))}; matmap = {o: k for k, o in enumerate(sorted(mat_used))}
    tmap = {o: k for k, o in enumerate(sorted(tex_used))}; imap = {o: k for k, o in enumerate(sorted(img_used))}; smap = {o: k for k, o in enumerate(sorted(smp_used))}
    bv_used = sorted({J['accessors'][a]['bufferView'] for a in acc_used} | {J['images'][i]['bufferView'] for i in img_used if 'bufferView' in J['images'][i]})
    nb = bytearray(); bvmap = {}; new_bv = []
    for o in bv_used:
        bv = dict(J['bufferViews'][o])
        while len(nb) % 8: nb.append(0)
        s = bv.get('byteOffset', 0); nb += bin_[s:s + bv['byteLength']]
        bv['byteOffset'] = len(nb) - bv['byteLength']; bvmap[o] = len(new_bv); new_bv.append(bv)
    def remap_tex(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'index' and isinstance(v, int): o[k] = tmap[v]
                else: remap_tex(v)
        elif isinstance(o, list):
            for v in o: remap_tex(v)
    J2 = {k: v for k, v in J.items() if k not in ('nodes', 'meshes', 'accessors', 'bufferViews', 'materials', 'textures', 'images', 'samplers', 'scenes')}
    J2['scenes'] = [dict(sc, nodes=[nmap[i] for i in sc['nodes']])]; J2['scene'] = 0
    J2['nodes'] = []
    for i in nodes_used:
        n = dict(J['nodes'][i])
        if 'mesh' in n: n['mesh'] = mmap[n['mesh']]
        if 'children' in n: n['children'] = [nmap[c] for c in n['children'] if c in nmap]
        J2['nodes'].append(n)
    J2['meshes'] = []
    for mi in meshes_used:
        me = json.loads(json.dumps(J['meshes'][mi]))
        for p in me['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
            if 'indices' in p: p['indices'] = amap[p['indices']]
            if 'material' in p: p['material'] = matmap[p['material']]
        J2['meshes'].append(me)
    J2['accessors'] = [dict(J['accessors'][a], bufferView=bvmap[J['accessors'][a]['bufferView']]) for a in sorted(acc_used)]
    J2['bufferViews'] = new_bv
    J2['materials'] = []
    for mi in sorted(mat_used):
        m = json.loads(json.dumps(J['materials'][mi])); remap_tex(m); J2['materials'].append(m)
    J2['textures'] = []
    for ti in sorted(tex_used):
        t = json.loads(json.dumps(J['textures'][ti]))
        if 'source' in t: t['source'] = imap[t['source']]
        if 'sampler' in t: t['sampler'] = smap[t['sampler']]
        for e in t.get('extensions', {}).values():
            if 'source' in e: e['source'] = imap[e['source']]
        J2['textures'].append(t)
    J2['images'] = [dict(J['images'][i], **({'bufferView': bvmap[J['images'][i]['bufferView']]} if 'bufferView' in J['images'][i] else {})) for i in sorted(img_used)]
    J2['samplers'] = [J['samplers'][s] for s in sorted(smp_used)]
    for k in ('textures', 'images', 'samplers', 'materials'):
        if not J2[k]: del J2[k]
    return J2, nb


def main(base, fit, out):
    J, b = read_glb(base); K, kb = read_glb(fit)
    rep = []; cut(J, b, rep)
    for nm, h, t in rep: print(f'  잘라냄 {nm:34s} {h:7d} / {t:7d} 삼각형')
    root = next(i for i, n in enumerate(J['nodes']) if (n.get('extras') or {}).get('oddEnv'))
    J['nodes'][root].setdefault('children', []).extend(append(J, b, K, kb))
    J['nodes'][root]['extras']['note'] = J['nodes'][root]['extras'].get('note', '') + ' / v3.0: 소파 · 사이드 테이블 · 램프 · 커튼 · 금박 액자 3점 · 러그 · 담요 = 리뷰 구역과 같은 조형(tools/blender/lounge_game.py), 충돌 상자 크기 그대로'
    J2, nb = gc(J, b)
    J2['asset']['generator'] = (J2['asset'].get('generator', '') + ' + ODD HAUS glb_merge').strip()
    write_glb(out, J2, nb)
    tris = 0
    for me in J2['meshes']:
        for p in me['primitives']: tris += J2['accessors'][p['indices']]['count'] // 3 if 'indices' in p else J2['accessors'][p['attributes']['POSITION']]['count'] // 3
    print('MERGED', out, len(open(out, 'rb').read()), 'bytes · 삼각형', tris, '· 노드', len(J2['nodes']), '· 이미지', len(J2.get('images', [])))


if __name__ == '__main__':
    main(*sys.argv[1:4])
