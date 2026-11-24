"""Estilo único dos gráficos (mesmas cores do app) e função para salvar em img/."""
import matplotlib.pyplot as plt

from src.config import PASTA_IMG

AZUL = "#2563eb"
VERMELHO = "#dc2626"
CINZA = "#94a3b8"
TEXTO = "#334155"


def aplicar_estilo():
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.edgecolor": "#cbd5e1",
        "axes.labelcolor": TEXTO,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#e2e8f0",
        "grid.linewidth": 0.8,
        "xtick.color": TEXTO,
        "ytick.color": TEXTO,
        "legend.frameon": False,
    })


def linha_taxa_base(ax, taxa, horizontal=True):
    """Linha cinza tracejada com a taxa média de avaliações negativas (na legenda)."""
    rotulo = f"média geral ({100 * taxa:.1f}%)"
    if horizontal:
        ax.axhline(100 * taxa, color=CINZA, ls="--", lw=1.2, label=rotulo)
        ax.legend(loc="upper left", fontsize=9)
    else:
        ax.axvline(100 * taxa, color=CINZA, ls="--", lw=1.2, label=rotulo)
        ax.legend(loc="lower right", fontsize=9)


def salvar(fig, nome):
    PASTA_IMG.mkdir(exist_ok=True)
    fig.savefig(PASTA_IMG / nome, bbox_inches="tight", facecolor="white")
