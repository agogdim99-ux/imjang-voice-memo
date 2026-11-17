# colab/02_LLM_항목추출.ipynb 의 추출·출력 단계. (노트북 안에서 model, tok, SYSTEM, TEXTS 가 준비된 뒤 실행)
import json, re, time


def extract(text):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "받아쓴 임장 메모:\n\n" + text}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    enc = {k: v.to(model.device) for k, v in enc.items()}
    out = model.generate(**enc, max_new_tokens=700, do_sample=False)   # 매번 같은 결과(재현성)
    raw = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"\{[\s\S]*\}", raw)
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
        print(f"{cond:<22} {it['id']}  {sec:>5}초  {'OK' if data else 'JSON 실패'}", flush=True)

print("<<<LLM_JSON>>>" + json.dumps({"model": MODEL, "results": RESULTS}, ensure_ascii=False) + "<<<END>>>")
