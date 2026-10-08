import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Polygon, FancyBboxPatch

plt.rcParams["font.family"] = "Liberation Serif"
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img") + "/"


def box(ax, x, y, w, h, text, ec, fs=10, fc="white", lw=1.4, color="black", bold=False):
    ax.add_patch(Rectangle((x, y), w, h, fill=True, fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=color, fontweight="bold" if bold else "normal", wrap=True)


# ---------------- 1.2-rasm: ALE oldin / keyin ----------------
def ale_chart():
    risks = ["R1", "R2", "R3", "R4", "R5", "R6"]
    before = [560, 270, 576, 570, 120, 19.5]
    after = [28, 45, 96, 114, 30, 1.95]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    x = range(len(risks))
    b1 = ax.bar([i - 0.2 for i in x], before, 0.4, color="#4472C4", label="Choralargacha ALE")
    b2 = ax.bar([i + 0.2 for i in x], after, 0.4, color="#ED7D31", label="Choralardan keyin ALE")
    for bars in (b1, b2):
        for r in bars:
            v = r.get_height()
            ax.text(r.get_x() + r.get_width() / 2, v + 8, f"{v:g}".replace(".", ","),
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(risks, fontsize=10)
    ax.set_ylabel("mln so'm / yil", fontsize=10)
    ax.set_ylim(0, 650)
    ax.yaxis.grid(True, color="#d9d9d9", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=9, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12))
    fig.tight_layout()
    fig.savefig(OUT + "ale.png")
    plt.close(fig)


# ---------------- 2.1-rasm: Galstuk-babochka ----------------
def bowtie():
    fig, ax = plt.subplots(figsize=(8.3, 6.6), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 72)
    ax.axis("off")
    green, red = "#70AD47", "#C00000"
    cx, cy = 50, 36
    ax.add_patch(Ellipse((cx, cy), 21, 14, fc="white", ec="#843C0C", lw=1.4))
    ax.text(cx, cy, "Bank serverlariga\nransomware\ntushishi", ha="center",
            va="center", fontsize=9.5, color="#843C0C", fontweight="bold")
    ax.text(10, 70, "Sabablar", color="#38761D", fontsize=11, fontweight="bold", ha="center")
    ax.text(89, 70, "Oqibatlar", color=red, fontsize=11, fontweight="bold", ha="center")
    lbl = dict(ha="center", va="bottom", fontsize=7.3,
               bbox=dict(fc="white", ec="none", pad=0.4))

    def on_line(x0, y0, x1, y1, x):
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    causes = [
        (63, "Fishing xat orqali\nzararli ilovaning\nochilishi", "Pochta filtri (sandbox),\nxodimlarni o'qitish"),
        (49.5, "OT va dasturlarning\nyangilanmaganligi\n(RDP zaifligi)", "Patch-menejment, RDP ni\nVPN orqasiga yopish"),
        (36, "Zaif va takroriy\nparollar", "Parol siyosati, MFA"),
        (22.5, "Zararlangan USB\nfleshkadan\nfoydalanish", "USB portlarni cheklash,\navtomatik skanerlash"),
        (9, "Litsenziyasiz /\nnoma'lum dasturlarni\no'rnatish", "Admin huquqlarini\ncheklash, whitelisting"),
    ]
    for y, c, bar in causes:
        box(ax, 1, y - 4.5, 18, 9, c, green, fs=8)
        ex, ey = cx - 10.3, cy + (y - cy) * 0.15
        ax.plot([19, ex], [y, ey], color=green, lw=1.2)
        mx = 21.8
        my = on_line(19, y, ex, ey, mx)
        ax.add_patch(Rectangle((mx - 0.6, my - 2.3), 1.2, 4.6, fc="#C9A0A0", ec="#7F3F3F", lw=0.8, zorder=3))
        tx = 31.5
        ax.text(tx, on_line(19, y, ex, ey, tx) + 0.9, bar, **lbl)

    cons = [
        (60, "Avtomatlashtirilgan bank\ntizimi (ABS) to'xtashi,\nxizmatlarning uzilishi", "Zaxira server,\nuzluksizlik (BCP) rejasi"),
        (44, "Mijozlar va operatsiyalar\nma'lumotlarining\nyo'qolishi", "Offline zaxira nusxadan\n(3-2-1) tiklash"),
        (28, "Ma'lumotlarning sirqib\nchiqishi va tovlamachilik\n(double extortion)", "Bazalarni shifrlash,\nDLP tizimi"),
        (12, "Moliyaviy zarar, jarima\nva bank obro'sining\ntushishi", "Insidentga javob rejasi,\nsug'urta, PR-bayonot"),
    ]
    for y, c, bar in cons:
        box(ax, 79, y - 5, 20, 10, c, red, fs=8)
        sx, sy = cx + 10.3, cy + (y - cy) * 0.15
        ax.plot([sx, 79], [sy, y], color=red, lw=1.2)
        mx = 77
        my = on_line(sx, sy, 79, y, mx)
        ax.add_patch(Rectangle((mx - 0.6, my - 2.3), 1.2, 4.6, fc="#C9A0A0", ec="#7F3F3F", lw=0.8, zorder=3))
        tx = 67
        ax.text(tx, on_line(sx, sy, 79, y, tx) + 0.9, bar, **lbl)

    ax.text(27, 0.3, "Oldini olish to'siqlari", fontsize=8.5, color="#7F3F3F", ha="center",
            style="italic")
    ax.text(72, 0.3, "Oqibatlarni kamaytirish to'siqlari", fontsize=8.5, color="#7F3F3F",
            ha="center", style="italic")
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
    ax.add_patch(Polygon([[0, y0], [8, y0 + 8], [16, y0], [8, y0 - 8]], closed=True,
                         fc="white", ec="black", lw=1))
    ax.text(8, y0, "Ransomware\nhujumi", ha="center", va="center", fontsize=8.5)

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
                                 "Fishing xatni\nochish", "Parolni boshqalarga\naytish"])
    branch(42, True, "Dasturiy ta'minot", ["Yangilanmagan OT\nva ilovalar",
                                           "Antivirus / EDR\nyo'qligi", "Litsenziyasiz\ndasturlar"])
    branch(64, True, "Jarayonlar (boshqaruv)", ["AX siyosati\nbajarilmasligi",
                                               "Muntazam audit\no'tkazilmasligi",
                                               "Insident rejasi\nyo'qligi"])
    branch(20, False, "Infratuzilma", ["Segmentatsiya\nyo'q", "RDP port internetga\nochiq",
                                       "Zaxira nusxa\nshu tarmoqda"])
    branch(42, False, "Tashqi omillar", ["Kontragentdan\nzararlangan fayl",
                                         "Yangi (0-day)\nzaifliklar", "Maqsadli\nhujumlar"])
    branch(64, False, "Kirish nazorati", ["Zaif / takroriy\nparollar", "MFA joriy\nqilinmagan",
                                          "Ortiqcha admin\nhuquqlari"])
    fig.savefig(OUT + "fishbone.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# ---------------- 2.3-rasm: Sabab-oqibat diagrammasi (nosozlik + hodisalar daraxti) ----------------
def cause_consequence():
    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=200)
    ax.set_xlim(0, 120)
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

    def leaf(x, y, t):
        ax.add_patch(Ellipse((x, y), 8, 7, fc="white", ec="black", lw=0.9))
        ax.text(x, y, t, ha="center", va="center", fontsize=6.6)

    # ---- chap tomon: nosozlik daraxti (sabablar)
    box(ax, 6, 52, 22, 7, "Ransomware ishga tushdi\nP = 0,088 (yiliga)", "black", fs=8.2,
        fc="#FCE4D6", bold=True)
    ax.plot([17, 17], [52, 48.5], **k)
    gate_or(17, 47)
    ax.plot([17, 17], [45.5, 43], **k)
    ax.plot([8.5, 25.5], [43, 43], **k)
    ax.plot([17, 17], [43, 40.2], **k)
    leaf(17, 36.7, "Zararlangan\nUSB  0,01")
    for xc, txt, kids in ((8.5, "Fishing orqali\nP = 0,03", ((4, "Xat filtrdan\no'tdi  0,1"), (13, "Xodim faylni\nochdi  0,3"))),
                          (25.5, "RDP zaifligi\nP = 0,05", ((21.5, "RDP ochiq\n0,2"), (30.5, "Patch yo'q\n0,25")))):
        ax.plot([xc, xc], [43, 40.5], **k)
        box(ax, xc - 4.4, 35, 8.8, 5.5, txt, "black", fs=7.4)
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

    def cond(x, y, t):
        box(ax, x, y - 3, 13, 6, t, "#2F5597", fs=7.4, fc="#DEEBF7")

    def yn(x, y_from, y_yes, y_no, p_yes, p_no, x_end_yes, x_end_no):
        ax.plot([x, x + 2], [y_from, y_from], **k)
        ax.plot([x + 2, x + 2], [y_no, y_yes], **k)
        ax.plot([x + 2, x_end_yes], [y_yes, y_yes], **k)
        ax.plot([x + 2, x_end_no], [y_no, y_no], **k)
        ax.text(x + 2.6, y_yes + 0.5, f"HA  {p_yes}", fontsize=6.9, color="#38761D", va="bottom")
        ax.text(x + 2.6, y_no - 0.5, f"YO'Q  {p_no}", fontsize=6.9, color="#C00000", va="top")

    cond(37, 55.5, "EDR/antivirus\nhujumni bloklaydimi?")
    yn(50, 55.5, 63, 44, "0,7", "0,3", 101, 59)
    cond(59, 44, "Segmentatsiya\ntarqalishni to'xtatadimi?")
    yn(72, 44, 51, 29, "0,6", "0,4", 80, 80)
    for yb in (51, 29):
        cond(80, yb, "Offline zaxira\nnusxa yaroqlimi?")
        yn(93, yb, yb + 4, yb - 4, "0,8", "0,2", 101, 101)

    outs = [
        (63, "S1: Hujum to'xtatildi\nP = 0,700", "#E2EFDA"),
        (55, "S2: 1 segment, tez tiklash\nP = 0,144", "#E2EFDA"),
        (47, "S3: Segment ma'lumoti\nyo'qoldi  P = 0,036", "#FFF2CC"),
        (33, "S4: Butun tarmoq, 2-3 kun\nP = 0,096", "#FCE4D6"),
        (25, "S5: Halokatli oqibat\nP = 0,024", "#F4B183"),
    ]
    for y, t, c in outs:
        box(ax, 101, y - 2.8, 19, 5.6, t, "black", fs=7.2, fc=c)
    ax.text(76, 14, "Hodisalar daraxti (oqibatlar va ularning ehtimolliklari)", ha="center",
            fontsize=9, style="italic")
    fig.savefig(OUT + "cca.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


ale_chart()
bowtie()
fishbone()
cause_consequence()
print("ok")
