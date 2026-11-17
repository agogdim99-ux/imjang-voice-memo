"""받아쓰기 결과 + 항목표를 넣어 Colab 노트북(colab/02_LLM_항목추출.ipynb)을 만든다.

  python tools/build_notebook2.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from imjang.extract_llm import SYSTEM  # noqa: E402  (Claude와 같은 지시문을 쓴다)
from imjang.schema import FIELDS, LIST_FIELDS  # noqa: E402

CONDITIONS = ["scripts", "turbo_noisy_prompt", "small_noisy_noprompt"]


def load(cond):
    p = ROOT / ("data/scripts.json" if cond == "scripts" else f"data/transcripts/{cond}.json")
    return [{"id": i["id"], "text": i["text"]} for i in json.loads(p.read_text(encoding="utf-8"))["items"]]


TEXTS = {c: load(c) for c in CONDITIONS}
KEYS = [(k, t) for k, _, _, t in FIELDS] + [(k, "array of string") for k, _ in LIST_FIELDS]
key_desc = "\n".join(f'- "{k}": {t} 또는 null' if "array" not in t else f'- "{k}": 문자열 목록 (없으면 [])' for k, t in KEYS)
PROMPT_SYSTEM = SYSTEM + "\n\n출력 형식: 아래 키를 모두 가진 JSON 객체 하나만 출력한다. 설명·코드블록 없이 JSON만.\n" + key_desc


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.strip("\n")}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src.strip("\n")}


cells = [
    md("""
# 임장 음성메모 PoC — ③ 오픈소스 LLM으로 항목 추출 (규칙 기반과 비교)

받아쓴 글에서 항목표를 뽑는 일을 **Qwen2.5-7B-Instruct**(공개 LLM, 한국어 가능)로 해 본다.
유료 API 없이 Colab 무료 T4 GPU에서 4비트로 줄여(양자화) 실행한다.

- 입력: 대본 원문 / turbo+소음+힌트 / small+소음+힌트없음 받아쓰기 (각 5건)
- 지시문: Claude 추출기와 **같은 지시문**(`imjang/extract_llm.py`의 SYSTEM)
- 출력: 항목표 JSON → 저장소 `data/llm_extracted/` → `python run.py --method qwen` 으로 채점

**실행 전**: `런타임 → 런타임 유형 변경 → T4 GPU` 후 위에서부터 ▶ (모델 내려받기 포함 약 15분)
"""),
    code("""
!pip -q install -U transformers accelerate bitsandbytes
import torch; print("GPU:", torch.cuda.is_available())
"""),
    code("SYSTEM = " + json.dumps(PROMPT_SYSTEM, ensure_ascii=False) + "\nTEXTS = " + json.dumps(TEXTS, ensure_ascii=False, indent=1)),
    code("""
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
MODEL = "Qwen/Qwen2.5-7B-Instruct"
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(
    MODEL, device_map="auto",
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4"))
print("로드 완료")
"""),
    code("""
import json, re, time

def extract(text):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "받아쓴 임장 메모:\\n\\n" + text}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    enc = {k: v.to(model.device) for k, v in enc.items()}
    out = model.generate(**enc, max_new_tokens=700, do_sample=False)   # 매번 같은 결과(재현성)
    raw = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"\\{[\\s\\S]*\\}", raw)
    try:
        return json.loads(m.group(0)), raw
    except Exception:
        return None, raw

RESULTS = {}
for cond, items in TEXTS.items():
    RESULTS[cond] = {}
    for it in items:
        t0 = time.time()
        data, raw = extract(it["text"])
        sec = round(time.time() - t0, 1)
        RESULTS[cond][it["id"]] = {"data": data, "seconds": sec, "raw": None if data else raw}
        print(f"{cond:<22} {it['id']}  {sec:>5}초  {'OK' if data else 'JSON 실패'}")
"""),
    md("## 결과 출력 (Claude Code가 이 출력을 읽어 저장소에 넣는다)"),
    code("""
print("<<<LLM_JSON>>>" + json.dumps({"model": MODEL, "results": RESULTS}, ensure_ascii=False) + "<<<END>>>")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "02_LLM_항목추출.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("저장:", out)
