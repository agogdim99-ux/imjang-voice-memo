"""오픈소스 LLM(Qwen2.5-7B) 추출 결과 읽기.

모델은 Colab GPU에서 돌리고(colab/02_LLM_항목추출.ipynb), 결과 JSON을
data/llm_extracted/qwen.json 에 저장해 둔다. 여기서는 그 결과를 항목표 모양으로 정리만 한다.
"""
import json
from pathlib import Path

from .schema import FIELDS, LIST_FIELDS, empty

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "llm_extracted" / "qwen.json"
TYPES = {k: t for k, _, _, t in FIELDS}


def _coerce(key, v):
    if v is None or v == "" or v == "null":
        return None
    t = TYPES.get(key)
    try:
        if t == "integer":
            return int(float(str(v).replace(",", "")))
        if t == "number":
            return float(str(v).replace(",", ""))
        if t == "boolean":
            return v if isinstance(v, bool) else str(v).lower() in ("true", "있음", "yes")
        if t == "string":
            return str(v)
    except ValueError:
        return None
    return v


def model_name() -> str:
    return json.loads(PATH.read_text(encoding="utf-8")).get("model", "Qwen")


def extract(cond: str, item_id: str) -> dict | None:
    if not PATH.exists():
        return None
    res = json.loads(PATH.read_text(encoding="utf-8"))["results"].get(cond, {}).get(item_id)
    if not res or not res.get("data"):
        return None
    raw = res["data"]
    d = empty()
    for k, *_ in FIELDS:
        d[k] = _coerce(k, raw.get(k))
    for k, _ in LIST_FIELDS:
        v = raw.get(k) or []
        d[k] = [str(x) for x in v] if isinstance(v, list) else [str(v)]
    d["_llm_seconds"] = res.get("seconds")
    return d
