"""LLM(Claude) 추출기 — ANTHROPIC_API_KEY 가 있을 때만 쓴다.

구조화 출력(JSON Schema)으로 항목표 모양을 강제하므로, 모델이 표 밖의 내용을 만들거나
형식을 깨뜨리지 못한다. 한 번 뽑은 결과는 outputs/cache_llm/ 에 저장해서,
키가 없는 사람도 같은 결과로 재현할 수 있다.
"""
import hashlib
import json
from pathlib import Path

from .schema import json_schema

MODEL = "claude-opus-5-5"

SYSTEM = """너는 부동산 임장(현장 방문) 음성메모를 정리하는 도우미다.
받아쓴 글에서 주어진 항목표에 맞춰 값을 뽑아라.

규칙
- 말에 실제로 나온 값만 적는다. 나오지 않은 항목은 반드시 null (빈 목록은 []). 추측 금지.
- 금액은 '만원' 단위 정수: 7억 2천 → 72000, 18만원 → 18, 5천만원 → 5000.
- 관리비(mgmt_fee)는 만원 단위 숫자.
- 말하는 사람이 값을 고쳐 말하면("아 아니다 ~") 마지막 값을 쓰고, 그 사실을 uncertain 에 적는다.
- '~쯤', '~정도라던데', '모르겠다'처럼 불확실한 말은 값을 적되 uncertain 에도 적는다.
  단, 숫자를 전혀 말하지 않았으면 null.
- sido 는 '서울특별시' / '인천광역시' / '경기도' 중 하나로 적는다(말에 시·군·구만 나와도 추론 가능).
- sigungu 는 '부천시 원미구', '성남시 분당구', '영등포구'처럼 적는다.
- chopuma(초품아): '초품아' 또는 길을 건너지 않고 단지 안/바로 옆 초등학교면 true, 길을 건너야 하면 false, 언급 없으면 null.
- seller_loan_exists: 매도인 융자(근저당)가 있다고 하면 true, 없다고 하면 false, 언급 없으면 null.
- defects: 누수·균열·곰팡이·파손·수리 필요 등 하자를 짧은 문장으로. 없으면 [].
- 받아쓰기 오류로 보이는 단어는 문맥상 명백할 때만 바로잡는다."""


def _cache_path(text: str, cache_dir: Path) -> Path:
    h = hashlib.sha256((MODEL + SYSTEM + text).encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"{h}.json"


def extract(text: str, cache_dir: Path, use_api: bool = True) -> dict | None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cp = _cache_path(text, cache_dir)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))
    if not use_api:
        return None

    import anthropic  # 키가 있을 때만 필요

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"받아쓴 임장 메모:\n\n{text}"}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": json_schema()}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"모델이 응답을 거절함: {response.stop_details}")
    raw = next(b.text for b in response.content if b.type == "text")
    data = json.loads(raw)
    cp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
