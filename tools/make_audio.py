"""대본(data/scripts.json) → AI 음성 mp3 (data/audio/clean/) + Colab 업로드용 audio_clean.zip

  pip install edge-tts
  python tools/make_audio.py
"""
import asyncio
import json
import sys
import zipfile
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")


async def main():
    items = json.loads((ROOT / "data/scripts.json").read_text(encoding="utf-8"))["items"]
    out = ROOT / "data/audio/clean"
    out.mkdir(parents=True, exist_ok=True)
    for s in items:
        p = out / f"{s['id']}.mp3"
        await edge_tts.Communicate(s["text"], s["voice"], rate="+10%").save(str(p))
        print("저장:", p)
    with zipfile.ZipFile(ROOT / "audio_clean.zip", "w") as z:
        for s in items:
            z.write(out / f"{s['id']}.mp3", f"{s['id']}.mp3")
    print("저장:", ROOT / "audio_clean.zip")


asyncio.run(main())
