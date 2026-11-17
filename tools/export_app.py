"""파이프라인 결과 → 집노트 웹앱 데이터(app/data.js)

  python run.py --transcripts data/transcripts/turbo_noisy_prompt.json --seed 2 --buyer 무주택 --income 0 --method rules
  python tools/export_app.py            # 기본: outputs/extracted_rules_turbo_noisy_prompt.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
src = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "outputs/extracted_rules_turbo_noisy_prompt.json")
data = json.loads(src.read_text(encoding="utf-8"))
transcripts = {i["id"]: i for i in json.loads((ROOT / data["settings"]["source"]).read_text(encoding="utf-8"))["items"]}

KEEP = ["sido", "sigungu", "dong", "complex_name", "property_type", "sale_price", "jeonse_price", "wolse_deposit", "wolse_monthly",
        "seller_loan_exists", "seller_loan_amount", "area_pyeong", "built_year", "floor", "facing", "households",
        "mgmt_fee", "parking_per_household", "elevator", "mgmt_office", "station_name", "station_walk_min",
        "elementary", "chopuma", "middle_high", "commercial", "defects", "uncertain"]

APP_SAMPLES = {"s1"}   # 앱에는 샘플 1건만 보여준다 (검증용 데이터 5건은 그대로)
props = []
for p in data["items"]:
    if p["_id"] not in APP_SAMPLES:
        continue
    z = p["_zone"]
    t = transcripts.get(p["_id"], {})
    props.append({
        "id": p["_id"],
        "title": p["_title"],
        **{k: p.get(k) for k in KEEP},
        "zone": {k: z[k] for k in ("zone", "label", "gap_allowed", "regulated", "reason", "caution")},
        "transcript": t.get("text"),
        "audio": f"../data/audio/clean/{p['_id']}.mp3",
        "seconds": p.get("_seconds"),
    })

out = {"source": data["settings"]["source"], "method": data["settings"]["method"], "properties": props}
dst = ROOT / "app" / "data.js"
dst.parent.mkdir(exist_ok=True)
dst.write_text("// tools/export_app.py 로 생성 — 직접 고치지 마세요\nwindow.ZIPNOTE_DATA = "
               + json.dumps(out, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print("저장:", dst, f"({len(props)}건)")
