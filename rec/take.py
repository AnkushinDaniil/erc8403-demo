import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, sys, time, subprocess
sys.path.insert(0, f'{ROOT}/wallet')
import w, mc
from playwright.async_api import async_playwright
G = f"{ROOT}/rec/gate/"
V = json.load(open(f"{ROOT}/voice/voice.json"))
EV = {"cam": [], "cur": [], "hl": [], "beats": {}, "cmd": {}, "roots": [], "notes": []}
ALICE = dict(cx=527, cy=298, z=1.06, focus=[20, 20, 1014, 556])
THIEF = dict(cx=527, cy=824.5, z=1.06, focus=[20, 596, 1014, 457])
BROW = dict(cx=1499, cy=293.5, z=1.09, focus=[1054, 20, 890, 547])
LOG = dict(cx=1495, cy=720, z=1.2, focus=[1054, 587, 882, 266])
OVER = dict(cx=982, cy=536, z=0.55, focus=None)
GREEN, RED, AMBER, BLUE = [100, 211, 86], [90, 90, 255], [34, 153, 210], [255, 180, 61]
T0 = 0
now = lambda: time.time() - T0
def cam(v, dur=0.8): EV["cam"].append(dict(t=now(), dur=dur, **v))
CUR = [982.0, 536.0]
def glide(x, y, dur=0.7):
    EV["cur"].append({"t0": now(), "t1": now() + dur, "x0": CUR[0], "y0": CUR[1], "x1": x, "y1": y}); CUR[0], CUR[1] = x, y
def cell(term, row, col):
    oy = 20 if term == "a" else 596
    return 34 + col * 17, oy + 14 + row * 33
def hl_term(term, row, c0, c1, color, dur, point=True, delay=0.0):
    x, y = cell(term, row, c0)
    EV["hl"].append({"t0": now() + delay, "t1": now() + delay + dur, "x": x - 6, "y": y - 1, "w": (c1 - c0) * 17 + 12, "h": 35, "c": color})
    if point: glide(x + (c1 - c0) * 17 + 26, y + 24, 0.6)
def hl_box(bb, color, dur, pad=8, point=True, side=False):
    x, y = 1054 + bb["x"], 110 + bb["y"]
    EV["hl"].append({"t0": now(), "t1": now() + dur, "x": x - pad, "y": y - pad, "w": bb["width"] + 2 * pad, "h": bb["height"] + 2 * pad, "c": color})
    if point and side: glide(x + bb["width"] + pad + 16, y + bb["height"] * 0.5 - 34, 0.6)
    elif point: glide(x + bb["width"] * 0.55, y + bb["height"] + 22, 0.6)
def word(line, text, nth=0):
    ws = [x for x in V[line]["words"] if x[2].strip(".,:").lower() == text.lower()]
    assert ws, (line, text)
    return ws[nth][0]
async def until(t_abs):
    d = t_abs - now()
    if d > 0: await asyncio.sleep(d)
def fire(g):
    open(G + g, "w").close(); EV["cmd"][g] = {"start": now()}
async def wait_cmd(g, timeout=15):
    t = time.time()
    while not os.path.exists(G + g + ".done"):
        if "typed" not in EV["cmd"][g] and os.path.exists(G + g + ".typed"): EV["cmd"][g]["typed"] = now()
        if time.time() - t > timeout: raise SystemExit("timeout " + g)
        await asyncio.sleep(0.02)
    EV["cmd"][g].setdefault("typed", now()); EV["cmd"][g]["done"] = now()
    print("CMD %s start %.2f typed %.2f done %.2f" % (g, EV["cmd"][g]["start"], EV["cmd"][g]["typed"], EV["cmd"][g]["done"]), flush=True)
def root_note(tag):
    r = w.chain_root().hex(); EV["roots"].append({"t": now(), "tag": tag, "root": r, "keys": [w.NAMES_BY_ADDR.get(a, "?") for _, a in w.chain_records()]})
    return r
async def main():
    global T0
    w.NAMES_BY_ADDR = {w.addr_of(n): n for n in w.DEVICES}
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:9333")
        pg = [x for x in b.contexts[0].pages if "account" in x.url][0]
        await pg.reload(); await asyncio.sleep(1.5)
        BB = {s: await pg.locator(s).bounding_box() for s in ["#root", "#keys", "#bt", "#ba", "#bb"]}
        await pg.evaluate("()=>sync(0)"); await asyncio.sleep(0.6)
        await pg.evaluate("()=>sync(1)")
        T0 = time.time()
        EV["cam"].append(dict(t=0, dur=0.01, **OVER))
        root_note("genesis")
        thief0 = w.balance(w.THIEF)
        t = 0.6
        def beat(name):
            EV["beats"][name] = now(); print("BEAT %-3s %.2f" % (name, now()), flush=True); return now()

        await until(t); b0 = beat("l1")
        cam(ALICE, 0.9)
        await until(b0 + 0.5); fire("a1"); await wait_cmd("a1")
        hl_term("a", 3, 10, 34, BLUE, 2.2)
        await until(b0 + word("l1", "chain") - 0.5)
        cam(BROW, 0.8); await asyncio.sleep(0.8)
        hl_box(BB["#root"], AMBER, 2.4)
        await until(b0 + V["l1"]["dur"] + 0.5)

        b0 = beat("l2"); cam(ALICE, 0.8)
        await until(b0 + 0.25); fire("a2"); await wait_cmd("a2"); root_note("add")
        hl_term("a", 7, 0, 38, GREEN, 1.6, delay=0.0)
        await asyncio.sleep(0.9)
        cam(BROW, 0.7); await asyncio.sleep(0.75)
        BBk = await pg.locator("#keys").bounding_box()
        hl_box(BBk, GREEN, 2.2)
        await until(max(b0 + V["l2"]["dur"] + 0.4, now() + 2.0))

        b0 = beat("l3"); cam(ALICE, 0.8)
        await until(b0 + 0.3); fire("a3"); await wait_cmd("a3")
        hl_term("a", 1, 0, 36, GREEN, 2.2)
        await until(max(b0 + V["l3"]["dur"] + 0.4, now() + 1.6))

        b0 = beat("l4")
        await until(b0 + word("l4", "From") - 0.4); fire("a4"); await wait_cmd("a4"); root_note("revoke")
        hl_term("a", 4, 0, 42, GREEN, 1.6)
        await asyncio.sleep(0.9)
        cam(BROW, 0.7); await asyncio.sleep(0.75)
        BBk = await pg.locator("#keys").bounding_box()
        hl_box(BBk, AMBER, 2.2)
        await until(max(b0 + V["l4"]["dur"] + 0.4, now() + 2.0))

        async def attack(line, g, refuse_word, nth, rows_reason, bal_row):
            b0 = beat(line); cam(THIEF, 0.9)
            await until(b0 + word(line, refuse_word, nth) - 2.35); fire(g); await wait_cmd(g)
            assert w.balance(w.THIEF) == thief0, "thief got funds"
            hl_term("t", 3, 0, 24, RED, 3.2)
            for r in rows_reason: EV["hl"].append({"t0": now() + 0.5, "t1": now() + 3.2, "x": cell("t", r, 0)[0] - 6, "y": cell("t", r, 0)[1] - 1, "w": 40 * 17 + 12, "h": 35, "c": RED})
            return b0
        b0 = await attack("l5", "t1", "refuses", 0, [4, 5], 6)
        await asyncio.sleep(1.5)
        cam(LOG, 0.7); await asyncio.sleep(0.75)
        EV["hl"].append({"t0": now(), "t1": now() + 2.0, "x": 1054 + 6, "y": 587 + 12 + 22 - 2, "w": 870, "h": 22 * 4 + 4, "c": RED}); glide(1054 + 700, 587 + 140, 0.6)
        await until(max(b0 + V["l5"]["dur"] + 0.4, now() + 2.0))

        b0 = await attack("l6", "t2", "Refused", 0, [4, 5], 6)
        await until(max(b0 + V["l6"]["dur"] + 0.4, now() + 1.8))

        b0 = await attack("l7", "t3", "Refused", 0, [4], 5)
        await until(b0 + word("l7", "signature", 1) - 0.3)
        cam(BROW, 0.7); await asyncio.sleep(0.75)
        hl_box(BB["#bt"], GREEN, 2.4)
        await until(max(b0 + V["l7"]["dur"] + 0.4, now() + 2.2))

        b0 = beat("l8"); cam(ALICE, 0.8)
        await until(b0 + word("l8", "loses") - 0.2); fire("a5"); await wait_cmd("a5")
        hl_term("a", 0, 9, 28, AMBER, 1.6)
        await until(b0 + word("l8", "No") - 1.3); fire("a6"); await wait_cmd("a6")
        hl_term("a", 2, 0, 44, RED, 2.0)
        await until(max(b0 + V["l8"]["dur"] + 0.4, now() + 1.5))

        b0 = beat("l9")
        await until(b0 + 0.15); fire("a7"); await wait_cmd("a7"); EV["notes"].append(["recovered", now()])
        hl_term("a", 5, 10, 27, BLUE, 2.4, point=False); hl_term("a", 6, 10, 27, BLUE, 2.4)
        await until(max(b0 + word("l9", "she") - 1.9, now() + 1.3)); fire("a8"); await wait_cmd("a8")
        hl_term("a", 9, 0, 36, GREEN, 2.2)
        await until(max(b0 + V["l9"]["dur"] + 0.6, now() + 2.0))
        TWO = []
        def two_note(tag):
            mc.on("two")
            q = {"t": now(), "tag": tag, "sv": mc.imported(w.ALICE), "dy": mc.imported(mc.DAILY), "bob": w.balance(w.BOB) / 1e18, "thief": w.balance(w.THIEF) / 1e18, "svb": w.balance(w.ALICE) / 1e18, "dyb": w.balance(mc.DAILY) / 1e18}
            mc.on("home"); q["home"] = int(w.rpc("eth_blockNumber", [])['result'], 16); q["root"] = w.chain_root().hex()
            TWO.append(q); print("TWO", q, flush=True)
        b0 = beat("m1"); cam(BROW, 0.9)
        await asyncio.sleep(0.45); await pg.goto("http://127.0.0.1:8700/two"); await asyncio.sleep(0.9)
        EV["nav"] = now()
        B2 = {s: await pg.locator(s).bounding_box() for s in ["#sv", "#dy", "#svh", "#dyh", "#btc"]}
        two_note("start")
        await until(b0 + word("m1", "keys") - 0.2)
        hl_box(B2["#svh"], AMBER, 2.8, pad=3, point=False); hl_box(B2["#dyh"], AMBER, 2.8, pad=3, side=True)
        await until(b0 + V["m1"]["dur"] + 0.4)

        b0 = beat("m2"); cam(ALICE, 0.8)
        await until(b0 + 0.3); fire("b1"); await wait_cmd("b1", 30); two_note("relay1")
        hl_term("a", 1, 0, 44, BLUE, 2.0)
        await until(max(b0 + word("m2", "accounts") - 0.3, now() + 1.2))
        hl_term("a", 2, 0, 50, GREEN, 2.2, point=False); hl_term("a", 3, 0, 50, GREEN, 2.2)
        await asyncio.sleep(1.5); cam(BROW, 0.7); await asyncio.sleep(0.75)
        B3 = {s: await pg.locator(s).bounding_box() for s in ["#svh", "#dyh"]}
        hl_box(B3["#svh"], GREEN, 2.0, pad=3, point=False); hl_box(B3["#dyh"], GREEN, 2.0, pad=3, side=True)
        await until(max(b0 + V["m2"]["dur"] + 0.4, now() + 1.8))

        b0 = beat("m3"); cam(ALICE, 0.8)
        await until(b0 + 0.2); fire("b2"); await wait_cmd("b2", 30); two_note("pay")
        hl_term("a", 5, 0, 47, GREEN, 2.2)
        await until(max(b0 + V["m3"]["dur"] + 0.4, now() + 1.8))

        b0 = beat("m4")
        await until(b0 + word("m4", "Alice") - 0.6); fire("b3"); await wait_cmd("b3", 30); root_note("revoke2")
        hl_term("a", 2, 0, 42, GREEN, 1.6)
        await asyncio.sleep(0.6); fire("b4"); await wait_cmd("b4", 30); two_note("relay2")
        hl_term("a", 5, 0, 50, GREEN, 2.0, point=False); hl_term("a", 6, 0, 50, GREEN, 2.0)
        await asyncio.sleep(1.2); cam(BROW, 0.7); await asyncio.sleep(0.75)
        B3 = {s: await pg.locator(s).bounding_box() for s in ["#svh", "#dyh"]}
        hl_box(B3["#svh"], GREEN, 2.0, pad=3, point=False); hl_box(B3["#dyh"], GREEN, 2.0, pad=3, side=True)
        await until(max(b0 + V["m4"]["dur"] + 0.4, now() + 2.0))

        async def attack2(line, g, key, lead, verdict, rows, color=RED, vw=24, rw=40):
            b0 = beat(line); cam(THIEF, 0.9)
            await until(b0 + word(line, key) - lead); fire(g); await wait_cmd(g, 30); two_note(g)
            hl_term("t", verdict, 0, vw, color, 3.2)
            for r in rows: EV["hl"].append({"t0": now() + 0.5, "t1": now() + 3.2, "x": cell("t", r, 0)[0] - 6, "y": cell("t", r, 0)[1] - 1, "w": rw * 17 + 12, "h": 35, "c": color})
            return b0
        b0 = await attack2("m5", "u1", "refuses", 2.9, 2, [3, 4], rw=31)
        await until(max(b0 + V["m5"]["dur"] + 0.4, now() + 2.2))
        b0 = await attack2("m6", "u2", "refused", 2.9, 3, [4, 5])
        await until(max(b0 + V["m6"]["dur"] + 0.4, now() + 2.2))
        b0 = await attack2("m7", "u3", "works", 2.9, 3, [4], AMBER, vw=36, rw=24)
        await asyncio.sleep(1.6); cam(BROW, 0.7); await asyncio.sleep(0.75)
        hl_box(B2["#btc"], RED, 2.4)
        await until(max(b0 + V["m7"]["dur"] + 0.4, now() + 2.4))

        cam(ALICE, 0.8); EV["notes"].append(["wait", now()])
        await asyncio.sleep(0.3); fire("b5"); await wait_cmd("b5", 90); two_note("relay3")
        hl_term("a", 1, 0, 46, AMBER, 2.4)
        b0 = beat("m8")
        await until(b0 + word("m8", "dead") - 2.9); cam(THIEF, 0.8); fire("u4"); await wait_cmd("u4", 30); two_note("u4")
        hl_term("t", 3, 0, 24, RED, 3.0)
        for r in (4, 5): EV["hl"].append({"t0": now() + 0.5, "t1": now() + 3.0, "x": cell("t", r, 0)[0] - 6, "y": cell("t", r, 0)[1] - 1, "w": 40 * 17 + 12, "h": 35, "c": RED})
        await until(max(b0 + V["m8"]["dur"] + 0.6, now() + 2.4))
        cam(OVER, 1.0); glide(982, 536, 0.9)
        await asyncio.sleep(1.2)
        EV["two"] = TWO; EV["window"] = mc.WINDOW
        EV["end"] = now(); mc.on("two"); EV["thief_two"] = w.balance(w.THIEF); mc.on("home"); EV["thief_balance"] = w.balance(w.THIEF); EV["final_root"] = w.chain_root().hex()
        json.dump(EV, open(f"{ROOT}/rec/events.json", "w"), indent=1)
        print("END %.2f thief %d" % (EV["end"], EV["thief_balance"]))
asyncio.run(main())
