"""임장 음성메모 → 매물 비교표 + 자금 판정.

사용 예
  python run.py                                   # 질문에 답하며 실행
  python run.py --seed 2 --buyer 무주택           # 대본(완벽한 받아쓰기 가정)으로 실행
  python run.py --transcripts data/transcripts/turbo_noisy_prompt.json --seed 2 --buyer 무주택
  python run.py --method llm ...                  # Claude 추출 (ANTHROPIC_API_KEY 필요, 없으면 캐시 사용)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from imjang import extract_llm, extract_rules
from imjang.finance import BUYER_TYPES, INCOME_BRACKETS, SEED_BRACKETS, evaluate_property
from imjang.regions import classify, normalize_region
from imjang.report import to_html, to_markdown

ROOT = Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8")


def ask(prompt: str, options: dict) -> str:
    print(prompt)
    for k, v in options.items():
        print(f"  {k}) {v[0] if isinstance(v, tuple) else v}")
    while True:
        a = input("> ").strip()
        for k in options:
            if a == str(k):
                return k
        print("목록의 번호/이름을 입력해 주세요.")


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["items"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcripts", default="data/scripts.json", help="받아쓰기 결과 JSON (기본: 대본)")
    ap.add_argument("--method", choices=["rules", "llm", "auto"], default="auto",
                    help="rules=규칙 기반, llm=Claude, auto=키 또는 캐시가 있으면 llm 아니면 rules")
    ap.add_argument("--seed", type=int, choices=list(SEED_BRACKETS), help="시드 구간 번호 1~6")
    ap.add_argument("--buyer", choices=list(BUYER_TYPES), help="무주택 / 생애최초 / 다주택")
    ap.add_argument("--income", type=int, choices=list(INCOME_BRACKETS), default=None, help="연소득 구간 0~5 (0=미입력)")
    ap.add_argument("--out", default="outputs", help="결과 폴더")
    a = ap.parse_args()

    interactive = sys.stdin.isatty()
    if a.seed is None:
        a.seed = int(ask("시드(투자 가능 금액) 구간을 고르세요:", SEED_BRACKETS)) if interactive else 2
    if a.buyer is None:
        a.buyer = ask("주택 보유 상태를 고르세요:", {k: v for k, v in BUYER_TYPES.items()}) if interactive else "무주택"
    if a.income is None:
        a.income = int(ask("연소득 구간 (대출 DSR 추정용, 모르면 0):", INCOME_BRACKETS)) if interactive else 0

    src = ROOT / a.transcripts
    items = load_items(src)
    titles = {i["id"]: i.get("title", i["id"]) for i in load_items(ROOT / "data/scripts.json")}
    cache = ROOT / "outputs" / "cache_llm"
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    props, method_used = [], set()
    for it in items:
        text = it["text"]
        t0 = time.perf_counter()
        p = None
        if a.method in ("llm", "auto"):
            try:
                p = extract_llm.extract(text, cache, use_api=has_key)
            except Exception as ex:  # 네트워크·키 문제 → 규칙 기반으로 대체
                print(f"[{it['id']}] Claude 추출 실패 → 규칙 기반 사용: {ex}")
            if p is None and a.method == "llm":
                print(f"[{it['id']}] API 키도 캐시도 없어 규칙 기반으로 대체합니다.")
        if p is None:
            p = extract_rules.extract(text)
            method_used.add("규칙 기반")
        else:
            method_used.add(f"Claude ({extract_llm.MODEL})")

        reg = normalize_region(p.get("sido"), p.get("sigungu"), p.get("dong"), text)
        p["sido"] = reg["sido"] or p.get("sido")
        zone = classify(reg, text)
        p["_zone"] = zone
        p["_finance"] = evaluate_property(p, zone, a.seed, a.buyer, a.income)
        p["_id"] = it["id"]
        p["_title"] = titles.get(it["id"], it["id"]).split(" — ")[0]
        p["_seconds"] = round(time.perf_counter() - t0 + it.get("stt_seconds", 0), 2)
        p["_stt_seconds"] = it.get("stt_seconds")
        props.append(p)

    settings = {"method": " + ".join(sorted(method_used)), "source": a.transcripts,
                "seed": a.seed, "buyer": a.buyer, "income": a.income}
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    tag = "llm" if any("Claude" in m for m in method_used) else "rules"
    stem = Path(a.transcripts).stem
    (out / f"extracted_{tag}_{stem}.json").write_text(
        json.dumps({"settings": settings, "items": props}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "report.md").write_text(to_markdown(props, settings), encoding="utf-8")
    (out / "report.html").write_text(to_html(props, settings), encoding="utf-8")

    print(f"\n추출: {settings['method']}  |  시드 {SEED_BRACKETS[a.seed][0]} · {a.buyer}")
    for p in props:
        verdicts = " / ".join(f"{s['name']}: {s['verdict']}" for s in p["_finance"]["scenarios"])
        print(f"- {p['_title']:<10} [{p['_zone']['label']}] {verdicts}  ({p['_seconds']}초)")
    print(f"\n저장: {out / 'report.html'}  (브라우저로 열기)\n      {out / 'report.md'}")


if __name__ == "__main__":
    main()
