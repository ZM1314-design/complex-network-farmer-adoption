"""plot_style.py

统一的“顶刊风格”绘图样式。

设计目标：
- 适配论文与顶刊排版：清爽、克制、可读性强
- 同时支持中文与英文
- 默认导出 PNG(600dpi) + PDF(矢量)

注意：字体依赖于本机字体库；若缺失会自动回退。
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib as mpl
from matplotlib import font_manager
from pathlib import Path


@dataclass(frozen=True)
class JournalStyle:
    base_fontsize: int = 10
    title_fontsize: int = 11
    label_fontsize: int = 10
    tick_fontsize: int = 9
    legend_fontsize: int = 9
    line_width: float = 1.8
    marker_size: float = 5.0


def apply_journal_style(style: JournalStyle | None = None) -> None:
    """应用顶刊风格 rcParams。

    说明：
    - 本项目内置开源中文字体：assets/fonts/NotoSansCJKsc-Regular.otf
    - 会在运行时动态注册，确保跨机器无缺字。
    """

    if style is None:
        style = JournalStyle()

    # 动态注册内置字体（若文件不存在则自动回退到系统字体）
    font_path = Path(__file__).resolve().parents[1] / 'assets' / 'fonts' / 'NotoSansCJKsc-Regular.otf'
    if font_path.exists():
        try:
            font_manager.fontManager.addfont(str(font_path))
        except Exception:
            # 字体注册失败时保持回退
            pass

    # 检查目标字体是否真的可用（有些环境 addfont 后仍可能不可用）
    noto_available = True
    try:
        font_manager.findfont('Noto Sans CJK SC', fallback_to_default=False)
    except Exception:
        noto_available = False

    mpl.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#111111",
            "xtick.color": "#111111",
            "ytick.color": "#111111",
            "text.color": "#111111",
            "axes.titlesize": style.title_fontsize,
            "axes.labelsize": style.label_fontsize,
            "xtick.labelsize": style.tick_fontsize,
            "ytick.labelsize": style.tick_fontsize,
            "legend.fontsize": style.legend_fontsize,
            "font.size": style.base_fontsize,
            "font.family": "sans-serif",
            "font.sans-serif": (
                [
                    # 内置字体优先（保证跨机器一致）
                    "Noto Sans CJK SC",
                    "Noto Sans CJK",
                ]
                if noto_available
                else []
            )
            + [
                # 系统回退
                "PingFang SC",
                "Heiti SC",
                "STHeiti",
                "Songti SC",
                "STSong",
                "Source Han Sans SC",
                "SimHei",
                # 英文/数字字体
                "Times New Roman",
                "Helvetica",
                "Arial",
                # 最后兜底
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            # 避免缺字时直接报 warning/显示方框的干扰
            "text.usetex": False,
            "axes.grid": False,
            "grid.alpha": 0.2,
            "lines.linewidth": style.line_width,
            "lines.markersize": style.marker_size,
            "legend.frameon": False,
            "legend.handlelength": 1.8,
            "legend.borderaxespad": 0.2,
        }
    )


JOURNAL_PALETTE = {
    "blue": "#1f77b4",
    "orange": "#ff7f0e",
    "green": "#2ca02c",
    "red": "#d62728",
    "purple": "#9467bd",
    "brown": "#8c564b",
    "gray": "#7f7f7f",
    "black": "#111111",
}
