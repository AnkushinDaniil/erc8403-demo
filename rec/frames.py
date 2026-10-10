import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, sys
from playwright.async_api import async_playwright
TL = json.load(open(f'{ROOT}/rec/timeline.json'))
out = sys.argv[1]
times = [float(x) for x in sys.argv[3:]] if sys.argv[2] == "at" else None
a, b = (0, 0) if times else (int(sys.argv[2]), int(sys.argv[3]))
os.makedirs(out, exist_ok=True)
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=os.environ.get("CHROME"), headless=True, args=["--no-sandbox", "--headless=new"])
        pg = await br.new_page(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"file://{ROOT}/web/stage.html")
        await pg.evaluate("tl=>init(tl)", TL)
        if times:
            for t in times:
                await pg.evaluate("t=>render(t)", t)
                await pg.screenshot(path=f"{out}/t{t:07.2f}.jpg", type="jpeg", quality=92)
        else:
            for i in range(a, b):
                await pg.evaluate("t=>render(t)", i / 30)
                await pg.screenshot(path=f"{out}/{i:05d}.jpg", type="jpeg", quality=95)
        print("done", a, b, "errors", errs[:3])
        await br.close()
asyncio.run(main())
