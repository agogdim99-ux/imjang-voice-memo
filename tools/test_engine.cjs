// 앱 엔진(app/engine.js)이 Python 파이프라인과 같은 결과를 내는지 검사한다.
//   python run.py ... (outputs/extracted_rules_*.json 생성) 후
//   node tools/test_engine.cjs
const fs = require("fs"), path = require("path");
const E = require("../app/engine.js");
const ROOT = path.join(__dirname, "..");
const FIELDS = Object.keys(E.empty());
let total = 0, diff = 0;
for (const f of fs.readdirSync(path.join(ROOT, "outputs")).filter(f => /^extracted_rules_.*\.json$/.test(f))) {
  const data = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", f), "utf8"));
  const src = JSON.parse(fs.readFileSync(path.join(ROOT, data.settings.source), "utf8")).items;
  for (const py of data.items) {
    const js = E.analyze(src.find(i => i.id === py._id).text);
    for (const k of FIELDS.concat(["zone"])) {
      total++;
      const a = k === "zone" ? py._zone.zone : py[k], b = k === "zone" ? js.zone.zone : js[k];
      if (JSON.stringify(a ?? null) !== JSON.stringify(b ?? null)) { diff++; console.log(`✗ ${f} ${py._id} ${k}: py=${JSON.stringify(a)} js=${JSON.stringify(b)}`); }
    }
  }
}
console.log(`\n${total - diff}/${total} 칸 일치`);
process.exit(diff ? 1 : 0);
