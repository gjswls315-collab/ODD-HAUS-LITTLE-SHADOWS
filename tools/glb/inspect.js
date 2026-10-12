// GLB 내용 요약: node inspect.js file.glb
const fs = require('fs'); const b = fs.readFileSync(process.argv[2]);
const jl = b.readUInt32LE(12), J = JSON.parse(b.slice(20, 20 + jl).toString());
const bv = J.bufferViews || [], acc = J.accessors || [];
const sizeOf = i => (bv[i] ? bv[i].byteLength : 0);
let geo = 0, anim = 0, img = 0, skin = 0;
for (const m of J.meshes || []) for (const p of m.primitives) { for (const k in p.attributes) geo += sizeOf(acc[p.attributes[k]].bufferView); if (p.indices !== undefined) geo += sizeOf(acc[p.indices].bufferView); }
for (const a of J.animations || []) for (const s of a.samplers) { anim += sizeOf(acc[s.input].bufferView) + sizeOf(acc[s.output].bufferView); }
for (const im of J.images || []) img += sizeOf(im.bufferView);
for (const s of J.skins || []) skin += sizeOf(acc[s.inverseBindMatrices].bufferView);
console.log(JSON.stringify({ bytes: b.length, geometryKB: Math.round(geo / 1024), animKB: Math.round(anim / 1024), imagesKB: Math.round(img / 1024), skinKB: Math.round(skin / 1024), nodes: (J.nodes || []).length, meshes: (J.meshes || []).length, materials: (J.materials || []).length, images: (J.images || []).map(i => i.mimeType + ':' + Math.round(sizeOf(i.bufferView) / 1024) + 'KB'), animations: (J.animations || []).map(a => a.name), extensions: J.extensionsUsed, rootExtras: (J.nodes || []).filter(n => n.extras && n.extras.oddRig).map(n => n.extras) }, null, 1));
