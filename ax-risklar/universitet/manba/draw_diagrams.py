import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Polygon, FancyBboxPatch

plt.rcParams["font.family"] = "Liberation Serif"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img") + "/"
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, ec, fs=10, fc="white", lw=1.4, color="black", bold=False, gid=None):
    r = Rectangle((x, y), w, h, fill=True, fc=fc, ec=ec, lw=lw)
    r.set_gid(gid)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=color, fontweight="bold" if bold else "normal", gid=gid)


# ---------------- tekshiruv: matnlar bir-birini, chiziqlarni va ramkalarni qoplamasligi ----------------
MARGIN = float(os.environ.get("MARGIN", "0"))  # qo'shimcha bo'sh joy, pt


def check(fig, ax, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    probs = []
    texts = [t for t in ax.texts if t.get_text().strip()]
    tbb = {}
    for t in texts:
        bb = t.get_window_extent(r)
        if t.get_bbox_patch() is not None:  # oq fonli yorliq: fon chegarasi bilan
            pad = t.get_bbox_patch().get_boxstyle().pad * t.get_fontsize() * fig.dpi / 72
            bb = bb.expanded(1, 1).padded(pad)
        tbb[t] = bb.padded(MARGIN * fig.dpi / 72)

    def lbl(t):
        return repr(t.get_text().replace("\n", " ")[:28])

    # matn - matn
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if tbb[a].overlaps(tbb[b]):
                probs.append(f"matn/matn: {lbl(a)} x {lbl(b)}")
    # matn - chiziq (o'z chizig'idan tashqari)
    for t in texts:
        bb = tbb[t]
        for ln in ax.lines:
            if t.get_gid() and ln.get_gid() == t.get_gid():
                continue
            xy = ax.transData.transform(ln.get_xydata())
            for p0, p1 in zip(xy[:-1], xy[1:]):
                s = np.linspace(0, 1, 300)[:, None]
                pts = p0 + (p1 - p0) * s
                inside = ((pts[:, 0] > bb.x0 + 1) & (pts[:, 0] < bb.x1 - 1) &
                          (pts[:, 1] > bb.y0 + 1) & (pts[:, 1] < bb.y1 - 1))
                if inside.any():
                    probs.append(f"matn/chiziq: {lbl(t)}")
                    break
    # matn - shakl chegarasi (ramkadan chiqish ham shu yerda aniqlanadi)
    for t in texts:
        bb = tbb[t]
        for pa in ax.patches:
            path = pa.get_path().transformed(pa.get_transform())
            pts = path.interpolated(60).vertices
            inside = ((pts[:, 0] > bb.x0 + 1) & (pts[:, 0] < bb.x1 - 1) &
                      (pts[:, 1] > bb.y0 + 1) & (pts[:, 1] < bb.y1 - 1))
            if inside.any():
                probs.append(f"matn/shakl: {lbl(t)} (shakl gid={pa.get_gid()})")
            elif pa.get_gid() != t.get_gid() or t.get_gid() is None:
                c = ((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2)
                if path.contains_point(c) and pa.get_gid() is not None and t.get_gid() is not None:
                    probs.append(f"matn begona shakl ichida: {lbl(t)}")
    # matn rasm chegarasidan chiqmasin
    fb = fig.bbox
    axb = ax.get_window_extent(r)
    for t in texts:
        bb = tbb[t]
        if bb.x0 < axb.x0 or bb.x1 > axb.x1 or bb.y0 < axb.y0 or bb.y1 > axb.y1:
            probs.append(f"o'q chegarasidan chiqdi: {lbl(t)}")
    print(f"[{name}] muammolar: {len(probs)}")
    for p_ in probs:
        print("   ", p_)
    return probs


# ---------------- 2.1-rasm: Galstuk-babochka ----------------
def bowtie():
    fig, ax = plt.subplots(figsize=(8.3, 6.6), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 72)
    ax.axis("off")
    green, red = "#70AD47", "#C00000"
    cx, cy = 50, 36
    el = Ellipse((cx, cy), 21, 14, fc="white", ec="#843C0C", lw=1.4)
    el.set_gid("top")
    ax.add_patch(el)
    ax.text(cx, cy, "Xodim hisob\nyozuvining\negallanishi", ha="center",
            va="center", fontsize=9.5, color="#843C0C", fontweight="bold", gid="top")
    ax.text(10, 70, "Sabablar", color="#38761D", fontsize=11, fontweight="bold", ha="center")
    ax.text(89, 70, "Oqibatlar", color=red, fontsize=11, fontweight="bold", ha="center")
    lbl = dict(ha="center", fontsize=7.3, bbox=dict(fc="white", ec="none", pad=0.4))

    def on_line(x0, y0, x1, y1, x):
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    # (y, sabab matni, to'siq yorlig'i, yorliq x, chiziqdan siljish, joylashuv)
    # (y, sabab matni, to'siq yorlig'i, yorliq markazining x koordinatasi)
    # yorliq o'z chizig'ining ustiga (markazi chiziqda) qo'yiladi, qo'shni chiziqlarga tegmaydi
    causes = [
        (63, "Fishing xat orqali\nparolni soxta\nsaytga kiritish", "Pochta filtri (DMARC),\nxodimlarni o'qitish", 30.8),
        (49.5, "Zaif va takroriy\nparollar", "Parol siyosati,\nMFA", 27.5),
        (36, "Umumiy kompyuterda\ntizimdan chiqmaslik,\nparolni saqlash", "Sessiyani avtomatik\nyopish, saqlash taqiqi", 30),
        (22.5, "Kompyuterga\nkeylogger\no'rnatilishi", "Antivirus/EDR,\nUSB cheklovi", 28.4),
        (9, "Telefon orqali\nijtimoiy\nmuhandislik", "Parol so'ralmaydi,\nqo'ng'iroqni tekshirish", 30),
    ]
    for i, (y, c, bar, tx) in enumerate(causes):
        g = f"c{i}"
        box(ax, 1, y - 4.5, 18, 9, c, green, fs=8, gid=f"cb{i}")
        ex, ey = cx - 10.3, cy + (y - cy) * 0.15
        ax.plot([19, ex], [y, ey], color=green, lw=1.2, gid=g)
        mx = 21.8
        my = on_line(19, y, ex, ey, mx)
        ax.add_patch(Rectangle((mx - 0.6, my - 2.3), 1.2, 4.6, fc="#C9A0A0", ec="#7F3F3F", lw=0.8, zorder=3))
        ax.text(tx, on_line(19, y, ex, ey, tx), bar, va="center", gid=g, **lbl)

    cons = [
        (60, "Baholar va davomat\nma'lumotlarining\nsoxtalashtirilishi", "Audit log, ikki\nkishilik tasdiqlash", 69),
        (44, "Talabalar shaxsiy\nma'lumotlarining\nsirqib chiqishi", "RBAC, eksportni\ncheklash", 70),
        (28, "Egallangan pochtadan\nfishing tarqatilishi\n(hujum kengayishi)", "Faollik nazorati,\nhisobni bloklash", 70),
        (12, "Universitet obro'siga\nputur, tekshiruv\nva jarimalar", "Insidentga javob\nrejasi, rasmiy bayonot", 70),
    ]
    for i, (y, c, bar, tx) in enumerate(cons):
        g = f"o{i}"
        box(ax, 79, y - 5, 20, 10, c, red, fs=8, gid=f"ob{i}")
        sx, sy = cx + 10.3, cy + (y - cy) * 0.15
        ax.plot([sx, 79], [sy, y], color=red, lw=1.2, gid=g)
        mx = 77
        my = on_line(sx, sy, 79, y, mx)
        ax.add_patch(Rectangle((mx - 0.6, my - 2.3), 1.2, 4.6, fc="#C9A0A0", ec="#7F3F3F", lw=0.8, zorder=3))
        ax.text(tx, on_line(sx, sy, 79, y, tx), bar, va="center", gid=g, **lbl)

    ax.text(27, 0.6, "Oldini olish to'siqlari", fontsize=8.5, color="#7F3F3F", ha="center", va="bottom",
            style="italic")
    ax.text(72, 0.6, "Oqibatlarni kamaytirish to'siqlari", fontsize=8.5, color="#7F3F3F", va="bottom",
            ha="center", style="italic")
    check(fig, ax, "bowtie")
    fig.savefig(OUT + "bowtie.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# ---------------- 2.2-rasm: Sabab-oqibat (baliq skeleti) ----------------
def fishbone():
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 56)
    ax.axis("off")
    lc = "#7F7F7F"
    y0 = 28
    ax.plot([16, 100], [y0, y0], color="black", lw=1.6)
    d = Polygon([[0, y0], [8, y0 + 8], [16, y0], [8, y0 - 8]], closed=True,
                fc="white", ec="black", lw=1)
    d.set_gid("head")
    ax.add_patch(d)
    ax.text(8, y0, "Hisob yozuvi\negallanishi", ha="center", va="center", fontsize=8.5, gid="head")

    def branch(x_base, up, title, items):
        s = 1 if up else -1
        x_top, y_top = x_base + 14, y0 + s * 24
        ax.plot([x_base, x_top], [y0, y_top], color=lc, lw=1)
        ax.text(x_top + 0.5, y_top + s * 1.4, title, ha="center", va="center", fontsize=9.5,
                fontweight="bold")
        n = len(items)
        for i, t in enumerate(items):
            f = (i + 1) / (n + 1)
            xb = x_base + 14 * f
            yb = y0 + s * 24 * f
            ax.plot([xb, xb + 15], [yb, yb], color=lc, lw=0.8)
            ax.text(xb + 8.6, yb + s * 0.4, t, ha="center", va="bottom" if up else "top", fontsize=7.6)

    branch(20, True, "Odamlar", ["AX bo'yicha bilim\npastligi",
                                 "Fishing xatni\nochish", "Parolni boshqaga\naytish"])
    branch(42, True, "Texnik vositalar", ["Antivirus / EDR\nyo'qligi",
                                          "Eskirgan brauzer\nva OT", "Parolni brauzerda\nsaqlash"])
    branch(64, True, "Tashkiliy jarayonlar", ["AX siyosati\nbajarilmasligi",
                                             "Jurnallar\nko'rilmasligi",
                                             "O'qitish\no'tkazilmasligi"])
    branch(20, False, "Muhit", ["Umumiy (ochiq)\nkompyuterlar", "Ochiq (parolsiz)\nWi-Fi",
                                "Tizimdan\nchiqmaslik"])
    branch(42, False, "Tashqi omillar", ["Soxta (o'xshash)\ndomenlar",
                                         "Ommaviy fishing\nkampaniyalari",
                                         "Sirqib chiqqan\nparollar bazalari"])
    branch(64, False, "Autentifikatsiya", ["Zaif / takroriy\nparollar", "MFA joriy\nqilinmagan",
                                           "Kirish urinishlari\ncheklanmagan"])
    check(fig, ax, "fishbone")
    fig.savefig(OUT + "fishbone.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# ---------------- 2.3-rasm: Sabab-oqibat diagrammasi (nosozlik + hodisalar daraxti) ----------------
def cause_consequence():
    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=200)
    ax.set_xlim(0, 121)
    ax.set_ylim(10, 68)
    ax.axis("off")
    k = dict(color="black", lw=1)

    def gate_or(x, y):
        ax.add_patch(Polygon([[x - 2, y - 1.5], [x, y + 1.5], [x + 2, y - 1.5], [x, y - 0.6]],
                             closed=True, fc="white", ec="black", lw=1))
        ax.text(x + 2.6, y, "YOKI", ha="left", va="center", fontsize=6.8)

    def gate_and(x, y):
        ax.add_patch(FancyBboxPatch((x - 1.8, y - 1.5), 3.6, 3, boxstyle="round,pad=0,rounding_size=1.4",
                                    fc="white", ec="black", lw=1))
        ax.text(x + 2.4, y, "VA", ha="left", va="center", fontsize=6.8)

    nleaf = [0]

    def leaf(x, y, t):
        nleaf[0] += 1
        g = f"leaf{nleaf[0]}"
        e = Ellipse((x, y), 8, 7, fc="white", ec="black", lw=0.9)
        e.set_gid(g)
        ax.add_patch(e)
        ax.text(x, y, t, ha="center", va="center", fontsize=6.6, gid=g)

    # ---- chap tomon: nosozlik daraxti (sabablar)
    box(ax, 6, 52, 22, 7, "Hisob yozuvi egallandi\nP = 0,097 (yiliga)", "black", fs=8.2,
        fc="#FCE4D6", bold=True, gid="top")
    ax.plot([17, 17], [52, 48.5], **k)
    gate_or(17, 47)
    ax.plot([17, 17], [45.5, 43], **k)
    ax.plot([8.5, 25.5], [43, 43], **k)
    ax.plot([17, 17], [43, 40.2], **k)
    leaf(17, 36.7, "Keylogger\n0,02")
    for j, (xc, txt, kids) in enumerate((
            (8.5, "Fishing orqali\nP = 0,05", ((4, "Xat filtrdan\no'tdi  0,2"), (13, "Xodim parolni\nkiritdi  0,25"))),
            (25.5, "Parolni topish\nP = 0,03", ((21.5, "Parol zaif /\ntakroriy  0,3"), (30.5, "Urinishlar\nchegarasiz\n0,1"))))):
        ax.plot([xc, xc], [43, 40.5], **k)
        box(ax, xc - 4.4, 35, 8.8, 5.5, txt, "black", fs=7.4, gid=f"mid{j}")
        ax.plot([xc, xc], [35, 33.3], **k)
        gate_and(xc, 31.8)
        ax.plot([xc, xc], [30.3, 28.5], **k)
        ax.plot([kids[0][0], kids[1][0]], [28.5, 28.5], **k)
        for kx, kt in kids:
            ax.plot([kx, kx], [28.5, 26.5], **k)
            leaf(kx, 23, kt)
    ax.text(17, 14, "Nosozlik daraxti\n(hodisa sabablari)", ha="center", fontsize=9, style="italic")

    # ---- o'ng tomon: hodisalar daraxti (oqibatlar), HA/YO'Q bloklar
    ax.annotate("", xy=(37, 55.5), xytext=(28, 55.5), arrowprops=dict(arrowstyle="->", lw=1.2))

    ncond = [0]

    def cond(x, y, t):
        ncond[0] += 1
        box(ax, x, y - 3, 13, 6, t, "#2F5597", fs=7.4, fc="#DEEBF7", gid=f"cond{ncond[0]}")

    def yn(x, y_from, y_yes, y_no, p_yes, p_no, x_end_yes, x_end_no):
        ax.plot([x, x + 2], [y_from, y_from], **k)
        ax.plot([x + 2, x + 2], [y_no, y_yes], **k)
        ax.plot([x + 2, x_end_yes], [y_yes, y_yes], **k)
        ax.plot([x + 2, x_end_no], [y_no, y_no], **k)
        ax.text(x + 2.6, y_yes + 0.5, f"HA  {p_yes}", fontsize=6.9, color="#38761D", va="bottom")
        ax.text(x + 2.6, y_no - 0.5, f"YO'Q  {p_no}", fontsize=6.9, color="#C00000", va="top")

    cond(37, 55.5, "Begona kirish\nbloklanadimi?")
    yn(50, 55.5, 63, 44, "0,5", "0,5", 102, 59)
    cond(59, 44, "Jurnal 24 soatda\naniqlaydimi?")
    yn(72, 44, 51, 29, "0,7", "0,3", 80.5, 80.5)
    for yb in (51, 29):
        cond(80.5, yb, "Zaxira nusxadan\ntiklanadimi?")
        yn(93.5, yb, yb + 4, yb - 4, "0,9", "0,1", 102, 102)

    outs = [
        (63, "S1: Kirish bloklandi\nP = 0,500", "#E2EFDA"),
        (55, "S2: Tez aniqlandi, tiklandi\nP = 0,315", "#E2EFDA"),
        (47, "S3: Qo'lda tiklash\n(bir necha kun)  P = 0,035", "#FFF2CC"),
        (33, "S4: Kech aniqlandi, sirqish\nP = 0,135", "#FCE4D6"),
        (25, "S5: Halokatli oqibat\nP = 0,015", "#F4B183"),
    ]
    for i, (y, t, c) in enumerate(outs):
        box(ax, 102, y - 2.8, 18.5, 5.6, t, "black", fs=7.2, fc=c, gid=f"s{i}")
    ax.text(76, 14, "Hodisalar daraxti (oqibatlar va ularning ehtimolliklari)", ha="center",
            fontsize=9, style="italic")
    check(fig, ax, "cca")
    fig.savefig(OUT + "cca.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


if __name__ == "__main__":
    bowtie()
    fishbone()
    cause_consequence()
    print("ok")
