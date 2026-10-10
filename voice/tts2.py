import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, sys, subprocess
sys.path.insert(0, f'{ROOT}/voice')
import edge_tts
from lines import LINES
VOICE = "en-US-AndrewMultilingualNeural"
D = f"{ROOT}/voice/"
async def one(k, text):
    c = edge_tts.Communicate(text, VOICE, rate="+6%", boundary="WordBoundary")
    words, audio = [], b""
    async for ch in c.stream():
        if ch["type"] == "audio": audio += ch["data"]
        elif ch["type"] == "WordBoundary": words.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])
    assert len(audio) > 2000 and words
    open(D + k + ".mp3", "wb").write(audio)
    d = float(subprocess.check_output(["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0", D + k + ".mp3"]))
    return {"text": text, "dur": d, "words": words}
async def main():
    old = json.load(open(D + "voice.json"))
    out = {}
    for k, t in LINES:
        ok = k in old and old[k]["text"] == t and os.path.exists(D + k + ".mp3") and os.path.getsize(D + k + ".mp3") > 2000
        if ok: out[k] = old[k]; continue
        for attempt in range(6):
            try:
                out[k] = await one(k, t); print("gen", k, round(out[k]["dur"], 2), flush=True); break
            except Exception as e:
                print("retry", k, attempt, type(e).__name__, str(e)[:80], flush=True); await asyncio.sleep(4 + attempt * 6)
        else:
            print("FAILED", k); 
        json.dump({**old, **out}, open(D + "voice.partial.json", "w"), indent=1)
    missing = [k for k, _ in LINES if k not in out]
    if missing: print("MISSING", missing); sys.exit(1)
    json.dump(out, open(D + "voice.json", "w"), indent=1)
    print("total", round(sum(v["dur"] for v in out.values()), 1))
asyncio.run(main())
