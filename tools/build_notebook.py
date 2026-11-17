"""data/scripts.json 을 넣어 Colab 노트북(colab/01_음성생성_받아쓰기.ipynb)을 만든다.
대본을 고치면 이 스크립트를 다시 실행하면 된다:  python tools/build_notebook.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = sys.argv[1] if len(sys.argv) > 1 else "OWNER/imjang-voice-memo"   # GitHub 사용자/저장소
scripts = json.loads((ROOT / "data/scripts.json").read_text(encoding="utf-8"))["items"]


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.strip("\n")}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src.strip("\n")}


cells = [
    md("""
# 임장 음성메모 PoC — ① 샘플 음성 만들기 + ② 받아쓰기(STT)

**이 노트북이 하는 일**
1. 대본 5개를 AI 목소리(edge-tts)로 읽힌 샘플 녹음(`audio_clean.zip`)을 올린다 → 개인 목소리 없이 누구나 같은 데이터로 재현 가능
2. 현장처럼 **소음을 섞은 버전**도 만든다 (실제 임장은 바람·차 소리가 있다)
3. Whisper 모델 2종 × 깨끗/소음 × 용어 힌트 유무 = 8가지로 받아쓰고 **글자 오류율(CER)·시간**을 비교한다
4. 받아쓴 결과(JSON)를 내려받는다 → 저장소 `data/transcripts/` 폴더에 넣으면 끝

**실행 전**: 메뉴 `런타임 → 런타임 유형 변경 → T4 GPU` 선택 후, 위에서부터 ▶ 를 차례로 누르세요. (전체 약 10분)
"""),
    code("""
!pip -q install openai-whisper jiwer
import torch; print("GPU 사용 가능:", torch.cuda.is_available())
"""),
    md("## 1. 대본 (저장소의 `data/scripts.json` 과 같은 내용)"),
    code("SCRIPTS = " + json.dumps(scripts, ensure_ascii=False, indent=1) + "\nfor s in SCRIPTS: print(s['id'], s['title'])"),
    md("""
## 2. AI 목소리 샘플 올리기
음성은 edge-tts(신경망 TTS)로 미리 만들어 두었다 (`data/audio/clean/`, 남·여 목소리 번갈아, 말 속도 +10%).
Colab에서 edge-tts 서버 연결이 막히는 경우가 있어서, 만들어 둔 파일을 올리는 방식으로 바꿨다.

▶ 를 누르면 GitHub 저장소에서 **`audio_clean.zip`** 을 자동으로 내려받는다. (실패하면 파일 선택 버튼이 나온다 → 저장소의 `audio_clean.zip` 선택)
"""),
    code(f"""
import os, zipfile, urllib.request
os.makedirs("audio/clean", exist_ok=True)
URL = "https://raw.githubusercontent.com/{REPO}/main/audio_clean.zip"
try:
    urllib.request.urlretrieve(URL, "audio_clean.zip"); names = ["audio_clean.zip"]
    print("GitHub에서 받음:", URL)
except Exception as e:
    print("자동 다운로드 실패 → 직접 올려 주세요:", e)
    from google.colab import files
    names = list(files.upload())
for name in names:
    with zipfile.ZipFile(name) as z:
        for m in z.namelist():
            if m.endswith(".mp3"):
                open(f"audio/clean/{{os.path.basename(m)}}", "wb").write(z.read(m))
missing = [s["id"] for s in SCRIPTS if not os.path.exists(f"audio/clean/{{s['id']}}.mp3")]
print("올라온 파일:", sorted(os.listdir("audio/clean")))
print("빠진 파일:", missing or "없음 ✅")
"""),
    md("""
## 3. 현장 소음 섞기
도로 소음과 비슷한 낮은 주파수 잡음(브라운 노이즈)과 바람 같은 잡음을 섞는다. 신호 대 잡음비(SNR) 10dB = 말소리가 소음보다 약 3배 큰 정도.
"""),
    code("""
import numpy as np, subprocess, soundfile as sf
os.makedirs("audio/noisy", exist_ok=True)
rng = np.random.default_rng(42)          # 시드 고정 → 누가 돌려도 같은 소음

def load16k(p):
    wav = p.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", "16000", wav], check=True)
    return sf.read(wav)[0]

def street_noise(n):
    brown = np.cumsum(rng.standard_normal(n)); brown -= np.convolve(brown, np.ones(4000)/4000, "same")
    wind = rng.standard_normal(n) * (0.5 + 0.5*np.sin(np.linspace(0, 20, n)))
    x = brown/np.std(brown) + 0.4*wind/np.std(wind)
    return x/np.std(x)

SNR_DB = 10
for s in SCRIPTS:
    y = load16k(f"audio/clean/{s['id']}.mp3")
    noise = street_noise(len(y)) * np.std(y) / (10 ** (SNR_DB/20))
    out = np.clip(y + noise, -1, 1)
    sf.write(f"audio/noisy/{s['id']}.wav", out, 16000)
    print("저장:", f"audio/noisy/{s['id']}.wav")
"""),
    code("""
from IPython.display import Audio, display
print("깨끗한 버전"); display(Audio("audio/clean/s1.mp3"))
print("소음 버전");   display(Audio("audio/noisy/s1.wav"))
"""),
    md("""
## 4. Whisper로 받아쓰기 — 8가지 조건 비교
| 비교 축 | 후보 |
|---|---|
| 모델 크기 | `small`(2.4억 파라미터, 빠름) vs `turbo`(large-v3-turbo, 8억, 정확) |
| 음성 | 깨끗 vs 소음 |
| 용어 힌트(initial_prompt) | 없음 vs 부동산 용어 목록 |

**용어 힌트**는 Whisper에 "이런 단어가 나올 수 있다"고 미리 알려주는 설정(하이퍼파라미터)이다. 샘플 지명은 넣지 않고 일반 부동산 용어만 넣어 공정하게 비교한다.
"""),
    code("""
import whisper, time, json, re, jiwer
PROMPT = "부동산 임장 메모입니다. 매매가, 전세가, 월세, 평형, 연식, 세대수, 세대당 주차, 엘리베이터, 관리비, 융자, 역세권, 초품아, 누수, 곰팡이."

def norm(t):  # 띄어쓰기·문장부호 차이는 오류로 세지 않는다
    return re.sub(r"[\\s.,!?…~'\\"]", "", t)

os.makedirs("transcripts", exist_ok=True)
rows = []
for model_name in ["small", "turbo"]:
    model = whisper.load_model(model_name)
    for audio in ["clean", "noisy"]:
        for use_prompt in [False, True]:
            tag = f"{model_name}_{audio}_{'prompt' if use_prompt else 'noprompt'}"
            items = []
            for s in SCRIPTS:
                path = f"audio/{audio}/{s['id']}." + ("mp3" if audio == "clean" else "wav")
                t0 = time.time()
                r = model.transcribe(path, language="ko", initial_prompt=PROMPT if use_prompt else None,
                                     temperature=0, fp16=torch.cuda.is_available())
                sec = round(time.time() - t0, 2)
                cer = jiwer.cer(norm(s["text"]), norm(r["text"]))
                items.append({"id": s["id"], "text": r["text"].strip(), "stt_seconds": sec, "cer": round(cer, 4)})
            json.dump({"model": model_name, "audio": audio, "prompt": use_prompt, "items": items},
                      open(f"transcripts/{tag}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            avg_cer = sum(i["cer"] for i in items)/len(items); avg_sec = sum(i["stt_seconds"] for i in items)/len(items)
            rows.append({"조건": tag, "모델": model_name, "음성": audio, "용어힌트": use_prompt,
                         "평균 CER": round(avg_cer, 4), "1건 평균 시간(초)": round(avg_sec, 2)})
            print(f"{tag:<26} CER {avg_cer:.2%}  {avg_sec:.1f}초/건")
    del model; torch.cuda.empty_cache()
"""),
    code("""
import pandas as pd
df = pd.DataFrame(rows).sort_values("평균 CER")
df.to_csv("transcripts/stt_results.csv", index=False, encoding="utf-8-sig")
df
"""),
    md("## 5. 받아쓴 문장 눈으로 비교 (가장 어려운 조건: 소음 + 힌트 없음)"),
    code("""
for tag in ["small_noisy_noprompt", "turbo_noisy_prompt"]:
    d = json.load(open(f"transcripts/{tag}.json", encoding="utf-8"))
    print(f"\\n===== {tag} =====")
    for it in d["items"]:
        print(f"[{it['id']}] CER {it['cer']:.1%}\\n  {it['text']}")
"""),
    md("""
## 6. 내려받기
`imjang_stt_results.zip` 이 내려받아진다. 압축을 풀어
- `transcripts/*.json`, `stt_results.csv` → 저장소 `data/transcripts/`
- `audio/` → 저장소 `data/audio/`
에 넣고, Claude Code에 "받아쓰기 결과 넣었어"라고 말하면 된다.
"""),
    md("### 6-1. 받아쓰기 결과를 화면에도 출력 (다운로드가 막힐 때 복사해서 쓴다)"),
    code("""
import glob
bundle = {os.path.basename(p): json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob("transcripts/*.json"))}
print("<<<RESULTS_JSON>>>" + json.dumps(bundle, ensure_ascii=False) + "<<<END>>>")
print("<<<CSV>>>" + open("transcripts/stt_results.csv", encoding="utf-8-sig").read() + "<<<END>>>")
"""),
    md("### 6-2. zip 내려받기"),
    code("""
!zip -qr imjang_stt_results.zip transcripts audio
from google.colab import files
files.download("imjang_stt_results.zip")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "colab" / "01_음성생성_받아쓰기.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("저장:", out)
