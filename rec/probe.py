import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9333")
        pg = [x for x in b.contexts[0].pages if "account" in x.url][0]
        print(len(b.contexts[0].pages), await pg.evaluate("()=>[screenX,screenY,outerWidth,outerHeight,innerWidth,innerHeight,devicePixelRatio]"))
        for s in ["#root", "#keys", "#bt", "#ba", "#bb", "h1"]:
            print(s, await pg.locator(s).bounding_box())
asyncio.run(main())
