"""추출 결과를 정답표(data/ground_truth.json)와 비교해 정확도를 낸다.

  python evaluate.py outputs/extracted_rules_scripts.json [다른 결과 파일 ...]

정답 규칙: 정답이 null(녹음에 없음)이면 추출도 비어 있어야 정답 → '확인 필요' 표시 검증.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent
GT = json.loads((ROOT / "data/ground_truth.json").read_text(encoding="utf-8"))["items"]

LABELS = {
    "sido": "시·도", "sigungu": "시·군·구", "dong": "동", "sale_price": "매매가", "jeonse_price": "전세가",
    "area_pyeong": "평형", "built_year": "연식", "households": "세대수", "mgmt_fee": "관리비",
    "parking_class": "주차(1대 기준)", "elevator": "엘리베이터", "station_walk_min": "역 도보(분)",
    "chopuma": "초품아", "seller_loan_exists": "융자 유무", "defects_mentioned": "하자 언급",
}


def predicted(p: dict, key: str):
    if key == "parking_class":
        v = p.get("parking_per_household")
        return None if v is None else ("1대 이상" if v >= 1 else "1대 미만")
    if key == "defects_mentioned":
        return bool(p.get("defects"))
    return p.get(key)


def correct(key: str, gt, pred) -> bool:
    if key == "sigungu":
        return pred is not None and all(tok in pred for tok in gt)
    if gt is None:
        return pred is None
    if pred is None:
        return False
    if isinstance(gt, (int, float)) and not isinstance(gt, bool):
        try:
            return abs(float(pred) - gt) < 1e-6
        except (TypeError, ValueError):
            return False
    return pred == gt


def score(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows, total, ok = [], 0, 0
    null_total = null_ok = 0
    for p in data["items"]:
        gt = GT.get(p["_id"])
        if not gt:
            continue
        for key, g in gt.items():
            pr = predicted(p, key)
            c = correct(key, g, pr)
            total += 1
            ok += c
            if g is None or (key == "defects_mentioned" and g is False):
                null_total += 1
                null_ok += c
            if not c:
                rows.append((p["_id"], LABELS[key], g, pr))
    secs = [p.get("_seconds") for p in data["items"] if p.get("_seconds") is not None]
    return {"file": path.name, "method": data["settings"]["method"], "source": data["settings"]["source"],
            "total": total, "ok": ok, "acc": ok / total if total else 0,
            "null_total": null_total, "null_ok": null_ok, "errors": rows,
            "avg_seconds": sum(secs) / len(secs) if secs else None}


def main():
    paths = [Path(x) for x in sys.argv[1:]] or sorted((ROOT / "outputs").glob("extracted_*.json"))
    results = [score(p) for p in paths]
    md = ["# 항목 추출 정확도\n",
          "정답표: `data/ground_truth.json` (매물 5건 × 15항목 = 75칸). 녹음에 없는 항목은 '확인 필요'로 비워야 정답.\n",
          "| 결과 파일 | 추출 | 받아쓰기 입력 | 정확도 | 누락 표시(확인 필요) 정확도 | 1건 평균 처리 시간 |",
          "|---|---|---|---|---|---|"]
    for r in results:
        t = f"{r['avg_seconds']:.1f}초" if r["avg_seconds"] is not None else "—"
        md.append(f"| {r['file']} | {r['method']} | `{r['source']}` | **{r['ok']}/{r['total']} ({r['acc']:.0%})** "
                  f"| {r['null_ok']}/{r['null_total']} | {t} |")
    for r in results:
        md.append(f"\n## 틀린 칸 — {r['file']}\n")
        if not r["errors"]:
            md.append("없음")
            continue
        md += ["| 매물 | 항목 | 정답 | 추출값 |", "|---|---|---|---|"]
        md += [f"| {i} | {k} | {g} | {p} |" for i, k, g, p in r["errors"]]
    out = ROOT / "outputs" / "evaluation.md"
    out.write_text("\n".join(md), encoding="utf-8")
    for r in results:
        print(f"{r['file']:<45} {r['ok']}/{r['total']} = {r['acc']:.0%}   (누락 표시 {r['null_ok']}/{r['null_total']})")
    print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
