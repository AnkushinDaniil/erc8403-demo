import json, math, subprocess, sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

raw, out, evf = sys.argv[1], sys.argv[2], sys.argv[3]
banddir = sys.argv[4] if len(sys.argv) > 4 else None
BOFF = int(sys.argv[5]) if len(sys.argv) > 5 else 0
EV = json.load(open(evf))
for n, q in enumerate(EV["cur"]):
    if q["x1"] > 1040: continue
    g = [h for h in EV["hl"] if q["t0"] - 0.1 <= h["t0"] <= q["t0"] + 0.8 and h["x"] < 1040]
    if not g: continue
    q["x1"] = min(996, max(h["x"] + h["w"] for h in g) + 14)
    q["y1"] = (min(h["y"] for h in g) + max(h["y"] + h["h"] for h in g)) / 2 - 6
    if n + 1 < len(EV["cur"]): EV["cur"][n + 1]["x0"], EV["cur"][n + 1]["y0"] = q["x1"], q["y1"]
W, H, FPS = 1920, 1200, 30
VW, VH = 1964, 1073
OW, SH = 1080, 600
BH = 480
WP = (92, 66, 46)
END = EV["end"]
PANES = [((0, 0, 1014, 556), (20, 20)), ((0, 620, 1014, 457), (20, 596)), ((1030, 0, 890, 90), (1054, 20)), ((1030, 143, 890, 457), (1054, 110)), ((1030, 640, 882, 266), (1054, 587))]
RECTS = [(20, 20, 1014, 556), (20, 596, 1014, 457), (1054, 20, 890, 547), (1054, 587, 882, 266)]

def base():
    im = Image.new("RGB", (VW, VH), (46, 66, 92))
    sh = Image.new("L", (VW, VH), 0)
    d = ImageDraw.Draw(sh)
    for x, y, w, h in RECTS: d.rectangle([x - 2, y + 6, x + w + 2, y + h + 14], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im = Image.composite(Image.new("RGB", (VW, VH), (14, 20, 30)), im, sh)
    return np.array(im)[:, :, ::-1].copy()
BASE = base()

def cursor_img(s=2.1):
    k = 4
    pts = [(0, 0), (0, 17), (4, 13.2), (7, 20), (9.6, 18.9), (6.7, 12.3), (12, 12.3)]
    pad = 6
    im = Image.new("RGBA", (int((12 + 2 * pad) * s * k), int((20 + 2 * pad) * s * k)), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    P = [((x + pad) * s * k, (y + pad) * s * k) for x, y in pts]
    ImageDraw.Draw(sh).polygon([(x + 1.2 * s * k, y + 1.8 * s * k) for x, y in P], fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(1.6 * s * k))
    d = ImageDraw.Draw(im)
    d.polygon(P, fill=(255, 255, 255, 255))
    d.line(P + [P[0]], fill=(255, 255, 255, 255), width=int(2.2 * s * k), joint="curve")
    d.polygon(P, fill=(20, 20, 20, 255))
    im = Image.alpha_composite(sh, im).resize((im.size[0] // k, im.size[1] // k), Image.LANCZOS)
    a = np.array(im).astype(np.float32)
    return a[:, :, [2, 1, 0]], a[:, :, 3:4] / 255.0, int(pad * s)
CUR, CURA, CPAD = cursor_img()

def ease(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def cam_at(t):
    c0 = EV["cam"][0]
    s = [c0["cx"], c0["cy"], math.log(c0["z"]), 0.0, 0, 0, VW, VH]
    for k in EV["cam"][1:]:
        if t <= k["t"]: break
        e = ease((t - k["t"]) / k["dur"])
        f = k["focus"]
        d0, r0 = s[3], s[4:8]
        s = [a + (b - a) * e for a, b in zip(s[:3], [k["cx"], k["cy"], math.log(k["z"])])]
        if f and d0 > 0.01 and f != r0: s += [abs(1 - 2 * e)] + (r0 if e < 0.5 else f)
        elif f: s += [d0 + (1 - d0) * e] + f
        else: s += [d0 * (1 - e)] + r0
    return s
def cur_at(t):
    segs = EV["cur"]
    if not segs or t < segs[0]["t0"]: return (segs[0]["x0"], segs[0]["y0"]) if segs else (982, 536)
    g = [q for q in segs if q["t0"] <= t][-1]
    e = ease((t - g["t0"]) / max(0.01, g["t1"] - g["t0"]))
    return g["x0"] + (g["x1"] - g["x0"]) * e, g["y0"] + (g["y1"] - g["y0"]) * e

dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", raw, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
OH = SH + (BH if banddir else 0)
enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-an", out], stdin=subprocess.PIPE)
f0, i, written, seen_dark = None, -1, 0, False
virt = np.empty((VH, VW, 3), np.uint8)
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    i += 1
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    if f0 is None:
        m = fr[588, 1908].mean()
        if m < 60: seen_dark = True
        elif m > 128 and seen_dark: f0 = i
        else: continue
        if f0 is None: continue
    t = (i - f0) / FPS
    if t > END: break
    virt[:] = BASE
    for (x, y, w, h), (vx, vy) in PANES: virt[vy:vy + h, vx:vx + w] = fr[y:y + h, x:x + w]
    virt[110 + 457 - 26:110 + 457, 1054 + 890 - 26:1054 + 890] = (23, 17, 13)
    cx, cy, lz, fd, fx, fy, fw, fh = cam_at(t)
    z = math.exp(lz)
    src, zz, ccx, ccy = virt, z, cx, cy
    if z < 0.78:
        src = cv2.resize(virt, (VW // 2, VH // 2), interpolation=cv2.INTER_AREA)
        zz, ccx, ccy = z * 2, cx / 2, cy / 2
    M = np.float32([[zz, 0, OW / 2 - ccx * zz], [0, zz, SH / 2 - ccy * zz]])
    scr = cv2.warpAffine(src, M, (OW, SH), flags=cv2.INTER_LINEAR if zz <= 1.01 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=WP)
    tx = lambda x: (x - cx) * z + OW / 2
    ty = lambda y: (y - cy) * z + SH / 2
    if fd > 0.01:
        x0, y0, x1, y1 = [int(round(v)) for v in (tx(fx), ty(fy), tx(fx + fw), ty(fy + fh))]
        dim = (scr.astype(np.float32) * (1 - 0.55 * fd)).astype(np.uint8)
        x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(OW, x1), min(SH, y1)
        if x1c > x0c and y1c > y0c: dim[y0c:y1c, x0c:x1c] = scr[y0c:y1c, x0c:x1c]
        scr = dim
    for q in EV.get("hl", []):
        if q["t0"] <= t <= q["t1"]:
            a = min(1.0, (t - q["t0"]) / 0.25, (q["t1"] - t) / 0.25)
            x0, y0, x1, y1 = [int(round(v)) for v in (tx(q["x"]), ty(q["y"]), tx(q["x"] + q["w"]), ty(q["y"] + q["h"]))]
            ov = scr.copy(); cv2.rectangle(ov, (x0, y0), (x1, y1), q["c"], -1, cv2.LINE_AA)
            scr = cv2.addWeighted(ov, 0.18 * a, scr, 1 - 0.18 * a, 0)
            ov = scr.copy(); cv2.rectangle(ov, (x0, y0), (x1, y1), q["c"], 3, cv2.LINE_AA)
            scr = cv2.addWeighted(ov, a, scr, 1 - a, 0)
    px, py = cur_at(t)
    ox, oy = tx(px), ty(py)
    hx, hy = int(round(ox)) - CPAD, int(round(oy)) - CPAD
    ch, cw = CUR.shape[:2]
    a0, b0 = max(0, hy), max(0, hx)
    a1, b1 = min(SH, hy + ch), min(OW, hx + cw)
    if a1 > a0 and b1 > b0:
        ca = CURA[a0 - hy:a1 - hy, b0 - hx:b1 - hx]
        scr[a0:a1, b0:b1] = (scr[a0:a1, b0:b1] * (1 - ca) + CUR[a0 - hy:a1 - hy, b0 - hx:b1 - hx] * ca).astype(np.uint8)
    if banddir:
        band = cv2.imread(os.path.join(banddir, "%05d.jpg" % (written + BOFF)))
        if band is None: break
        frame = np.vstack([band[:120], scr, band[720:]])
    else:
        frame = scr
    enc.stdin.write(frame.tobytes())
    written += 1
enc.stdin.close(); enc.wait(); dec.kill()
print("sync frame", f0, "written", written, "dur %.2f" % (written / FPS))
