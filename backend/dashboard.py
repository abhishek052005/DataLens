import matplotlib

matplotlib.use("Agg")

import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

BG = "#0b1120"
CARD_BG = "#111c2f"
CARD_BORDER = "#24334b"
TEXT = "#eef3fc"
TEXT_MUTED = "#91a0b8"
GRID = "#26354c"
ACCENT = ["#7c83ff", "#37c7a2", "#41a5ff", "#f4b860",
          "#ed7294", "#9d86ff", "#4bc5d5", "#b2d878"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "figure.facecolor": BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": CARD_BORDER,
    "axes.labelcolor": TEXT_MUTED,
    "xtick.color": TEXT_MUTED,
    "ytick.color": TEXT_MUTED,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "text.color": TEXT,
    "axes.titlecolor": TEXT,
})


def render_dashboard(
    dashboard_data: dict,
    filename: str = "",
    output_path: str = "outputs/dashboard.png",
) -> Path:
    """Render a dashboard image without requiring a desktop or GUI backend."""
    charts = dashboard_data.get("charts", [])
    kpis = dashboard_data.get("kpis", [])
    columns = 2
    chart_rows = max(1, math.ceil(len(charts) / columns))
    has_insights = bool(dashboard_data.get("insights"))

    figure_height = 3.2 + chart_rows * 4.25 + (0.65 if has_insights else 0)
    fig = plt.figure(figsize=(16, figure_height), facecolor=BG)
    row_count = 2 + chart_rows + int(has_insights)
    height_ratios = [0.55, 1.15] + [4] * chart_rows
    if has_insights:
        height_ratios.append(0.65)

    grid = fig.add_gridspec(
        row_count,
        columns,
        height_ratios=height_ratios,
        hspace=0.5,
        wspace=0.2,
        left=0.045,
        right=0.955,
        top=0.965,
        bottom=0.04,
    )

    header = fig.add_subplot(grid[0, :])
    header.axis("off")
    header.text(0, 0.62, "AI DATA DASHBOARD", fontsize=17, weight="bold",
                color=TEXT, transform=header.transAxes)
    details = [
        filename,
        f"{dashboard_data.get('row_count', 0):,} rows",
        datetime.now().strftime("%d %b %Y, %H:%M"),
    ]
    header.text(0, 0.12, "  /  ".join(value for value in details if value),
                fontsize=9, color=TEXT_MUTED, transform=header.transAxes)
    header.plot([0, 1], [-0.08, -0.08], color=CARD_BORDER, linewidth=1,
                transform=header.transAxes, clip_on=False)

    kpi_axis = fig.add_subplot(grid[1, :])
    _draw_kpis(kpi_axis, kpis)

    for index, chart in enumerate(charts):
        row = index // columns + 2
        column = index % columns
        chart_type = chart.get("type")
        ax = fig.add_subplot(grid[row, column], projection="polar" if chart_type == "radar" else None)
        _style_axis(ax)
        _plot_chart(ax, chart, color_idx=index)

    for index in range(len(charts), chart_rows * columns):
        ax = fig.add_subplot(grid[index // columns + 2, index % columns])
        ax.axis("off")

    if has_insights:
        footer = fig.add_subplot(grid[-1, :])
        footer.axis("off")
        footer.text(0, 0.72, "AI INSIGHTS", fontsize=8, weight="bold", color=ACCENT[0])
        footer.text(
            0,
            0.22,
            "  •  ".join(str(item) for item in dashboard_data["insights"][:3]),
            fontsize=9,
            color=TEXT_MUTED,
            wrap=True,
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(output_file, dpi=160, bbox_inches="tight", facecolor=BG)
    finally:
        plt.close(fig)
    return output_file


def _draw_kpis(ax, kpis: list[dict]) -> None:
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    count = max(len(kpis), 1)
    gap = 0.014
    width = (0.99 - gap * (count - 1)) / count

    if not kpis:
        ax.text(0.02, 0.5, "No KPI metrics were selected.", color=TEXT_MUTED, va="center")
        return

    for index, kpi in enumerate(kpis):
        x = index * (width + gap)
        card = FancyBboxPatch(
            (x, 0.08),
            width,
            0.84,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor=CARD_BG,
            edgecolor=CARD_BORDER,
            linewidth=0.9,
        )
        ax.add_patch(card)
        accent = ACCENT[index % len(ACCENT)]
        ax.add_patch(FancyBboxPatch(
            (x + 0.025, 0.2), 0.008, 0.58,
            boxstyle="round,pad=0.002",
            facecolor=accent,
            edgecolor="none",
        ))
        ax.text(x + 0.06, 0.7, str(kpi.get("label", "Metric")),
                fontsize=9, color=TEXT_MUTED, va="center")
        ax.text(x + 0.06, 0.43, _format_kpi(kpi),
                fontsize=17, weight="bold", color=TEXT, va="center")
        ax.text(x + 0.06, 0.22, f"{kpi.get('column', '')}  /  {kpi.get('agg', '')}",
                fontsize=8, color=TEXT_MUTED, va="center")


def _format_kpi(kpi: dict) -> str:
    value = kpi.get("value", 0)
    number = float(value)
    if kpi.get("format") == "percent":
        return f"{number:,.1f}%"
    if kpi.get("format") == "currency":
        return f"₹{number:,.0f}"
    return f"{number:,.0f}" if number.is_integer() else f"{number:,.2f}"


def _style_axis(ax) -> None:
    ax.set_facecolor(CARD_BG)
    if ax.name == "polar":
        ax.spines["polar"].set_color(CARD_BORDER)
        ax.grid(color=GRID, linewidth=0.7)
        ax.tick_params(colors=TEXT_MUTED, labelsize=8)
        return

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", labelsize=8, length=0, pad=7)
    ax.set_axisbelow(True)


def _plot_chart(ax, chart: dict, color_idx: int = 0) -> None:
    data = chart["data"]
    x = chart.get("x", "")
    y = chart.get("y", "")
    chart_type = chart["type"]
    color = ACCENT[color_idx % len(ACCENT)]
    title = chart.get("title") or f"{y} by {x}"
    ax.set_title(title, fontsize=12, weight="bold", color=TEXT, loc="left", pad=20)
    if chart.get("insight"):
        ax.text(0, 1.015, chart["insight"], transform=ax.transAxes,
                fontsize=8, color=TEXT_MUTED, style="italic", va="bottom")

    if chart_type in {"line", "area"}:
        if isinstance(data, pd.DataFrame):
            series = list(data.columns[:3])
            positions = np.arange(len(data))
            for index, name in enumerate(series):
                values = data[name].to_numpy()
                line_color = ACCENT[index % len(ACCENT)]
                ax.plot(positions, values, color=line_color,
                        linewidth=2.2, marker="o", markersize=4, label=str(name))
                if chart_type == "area":
                    ax.fill_between(positions, values, color=line_color, alpha=0.1)
            if len(series) > 1:
                _legend(ax)
        else:
            values = data.to_numpy()
            positions = np.arange(len(data))
            ax.plot(positions, values, color=color, linewidth=2.4,
                    marker="o", markersize=4)
            if chart_type == "area":
                ax.fill_between(positions, values, color=color, alpha=0.16)
        ax.set_xticks(np.arange(len(data)), data.index.astype(str))
        ax.set_ylabel(y)
        ax.grid(axis="y", alpha=0.8)
        _category_ticks(ax)

    elif chart_type == "bar":
        values = data.nlargest(12) if len(data) > 12 else data
        bars = ax.bar(values.index.astype(str), values.to_numpy(),
                      color=color, width=0.68, edgecolor="none", zorder=3)
        if len(bars):
            bars[int(np.argmax(values.to_numpy()))].set_color(ACCENT[1])
            ax.bar_label(bars, labels=[_compact(value) for value in values.to_numpy()],
                         padding=3, fontsize=8, color=TEXT_MUTED)
        ax.set_ylabel(y)
        ax.grid(axis="y", alpha=0.8)
        _category_ticks(ax)

    elif chart_type == "stacked_bar":
        if isinstance(data, pd.DataFrame):
            bottom = np.zeros(len(data))
            for index, name in enumerate(data.columns[:5]):
                values = data[name].to_numpy()
                ax.bar(data.index.astype(str), values, bottom=bottom,
                       color=ACCENT[index % len(ACCENT)], width=0.68,
                       edgecolor=CARD_BG, linewidth=0.4, label=str(name), zorder=3)
                bottom += values
            _legend(ax, columns=min(4, len(data.columns)))
        ax.set_ylabel(y)
        ax.grid(axis="y", alpha=0.8)
        _category_ticks(ax)

    elif chart_type == "pie":
        colors = [ACCENT[index % len(ACCENT)] for index in range(len(data))]
        ax.pie(
            data.to_numpy(),
            startangle=90,
            colors=colors,
            counterclock=False,
            wedgeprops={"width": 0.36, "edgecolor": CARD_BG, "linewidth": 2},
            autopct=lambda pct: f"{pct:.0f}%" if pct >= 5 else "",
            pctdistance=0.82,
            textprops={"fontsize": 8, "weight": "bold", "color": TEXT},
        )
        ax.text(0, 0.06, _compact(data.sum()), ha="center", va="center",
                fontsize=15, weight="bold", color=TEXT)
        ax.text(0, -0.19, "TOTAL", ha="center", va="center",
                fontsize=7, color=TEXT_MUTED)
        ax.legend(data.index.astype(str), loc="center left", bbox_to_anchor=(0.98, 0.5),
                  frameon=False, labelcolor=TEXT_MUTED, fontsize=8)

    elif chart_type == "scatter":
        if isinstance(data, pd.DataFrame):
            ax.scatter(data[x], data[y], alpha=0.68, s=34, color=color,
                       edgecolors=CARD_BG, linewidths=0.5, zorder=3)
            if len(data) > 1 and data[x].nunique() > 1:
                slope, intercept = np.polyfit(data[x], data[y], 1)
                trend_x = np.linspace(data[x].min(), data[x].max(), 80)
                ax.plot(trend_x, slope * trend_x + intercept, color=ACCENT[3],
                        linewidth=1.5, linestyle="--", alpha=0.9)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.grid(alpha=0.7)

    elif chart_type == "histogram":
        values = pd.to_numeric(data, errors="coerce").dropna()
        ax.hist(values, bins=min(24, max(8, int(np.sqrt(len(values))))),
                color=color, alpha=0.88, edgecolor=CARD_BG, linewidth=1)
        ax.set_xlabel(x or y)
        ax.set_ylabel("Records")
        ax.grid(axis="y", alpha=0.8)

    elif chart_type == "radar":
        values = data.iloc[:12]
        labels = values.index.astype(str).tolist()
        if labels:
            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
            radii = values.to_numpy(dtype=float)
            ax.plot(np.r_[angles, angles[0]], np.r_[radii, radii[0]],
                    color=color, linewidth=2.2)
            ax.fill(np.r_[angles, angles[0]], np.r_[radii, radii[0]],
                    color=color, alpha=0.2)
            ax.set_xticks(angles, labels)
            ax.set_ylim(bottom=0)
            maximum = float(np.max(radii))
            if maximum > 0:
                radial_ticks = np.linspace(maximum / 4, maximum, 4)
                ax.set_yticks(radial_ticks)
                ax.set_yticklabels([_compact(value) for value in radial_ticks], fontsize=7)
            ax.set_rlabel_position(45)
        ax.grid(color=GRID, linewidth=0.7)

    elif chart_type == "composed":
        if isinstance(data, pd.DataFrame) and data.shape[1] > 1:
            categories = data.index.astype(str)
            bars = ax.bar(categories, data[y].to_numpy(), color=color,
                          alpha=0.8, width=0.62, label=y, zorder=3)
            ax.set_ylabel(y)
            secondary = ax.twinx()
            secondary.set_facecolor("none")
            secondary.spines["right"].set_visible(False)
            secondary.tick_params(axis="y", labelsize=8, colors=TEXT_MUTED, length=0)
            secondary.plot(categories, data[chart["y2"]].to_numpy(),
                           color=ACCENT[3], marker="o", linewidth=2.2, label=chart["y2"])
            secondary.set_ylabel(chart["y2"], color=TEXT_MUTED)
            _legend(ax, handles=[bars, secondary.lines[0]],
                    labels=[y, chart["y2"]])
        else:
            values = data.nlargest(12) if len(data) > 12 else data
            bars = ax.bar(values.index.astype(str), values.to_numpy(),
                          color=color, width=0.68, edgecolor="none", zorder=3)
            if len(bars):
                ax.bar_label(bars, padding=3, fontsize=8, color=TEXT_MUTED)
            ax.set_ylabel(y)
        ax.grid(axis="y", alpha=0.8)
        _category_ticks(ax)

    elif chart_type == "box":
        groups = [data.loc[data[x] == value, y].to_numpy() for value in data[x].unique()[:12]]
        labels = data[x].drop_duplicates().astype(str).head(12).tolist()
        boxes = ax.boxplot(groups, tick_labels=labels, patch_artist=True,
                           medianprops={"color": TEXT, "linewidth": 1.8},
                           whiskerprops={"color": TEXT_MUTED},
                           capprops={"color": TEXT_MUTED},
                           flierprops={"marker": ".", "markersize": 3,
                                       "markerfacecolor": color, "markeredgecolor": "none"})
        for index, patch in enumerate(boxes["boxes"]):
            patch.set_facecolor(ACCENT[index % len(ACCENT)])
            patch.set_alpha(0.65)
        ax.set_ylabel(y)
        ax.grid(axis="y", alpha=0.8)
        _category_ticks(ax)


def _category_ticks(ax) -> None:
    ax.tick_params(axis="x", labelrotation=25)
    for label in ax.get_xticklabels():
        label.set_ha("right")


def _legend(ax, handles=None, labels=None, columns: int = 1) -> None:
    options = {
        "loc": "upper left",
        "frameon": False,
        "labelcolor": TEXT_MUTED,
        "fontsize": 8,
        "ncol": columns,
    }
    if handles is not None:
        ax.legend(handles, labels, **options)
    else:
        ax.legend(**options)


def _compact(value: float) -> str:
    number = float(value)
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(number) >= threshold:
            return f"{number / threshold:.1f}{suffix}"
    return f"{number:,.0f}" if number.is_integer() else f"{number:,.1f}"
