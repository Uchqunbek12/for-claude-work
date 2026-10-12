import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Liberation Serif"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


# ---------------- 1.2-rasm: ALE choralargacha / choralardan keyin ("B" universiteti) ----------------
def ale_chart():
    risks = ["R1", "R2", "R3", "R4", "R5", "R6"]
    before = [200, 336, 180, 135, 600, 90]
    after = [16, 84, 18, 13.5, 108, 10.8]
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
    ax.set_ylim(0, 700)
    ax.yaxis.grid(True, color="#d9d9d9", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=9, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12))
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "ale.png"))
    plt.close(fig)


ale_chart()
print("ok")
