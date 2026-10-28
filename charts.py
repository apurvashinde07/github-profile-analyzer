"""Matplotlib charts for the GitHub Profile Analyzer.

Every function returns a matplotlib Figure. The non-interactive Agg
backend is used, so no window is ever opened. All charts use one neutral
palette with a transparent background, so they match both the light and
the dark Streamlit theme.
"""

import matplotlib
matplotlib.use("Agg")  # must be set before any figure is created

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

MAX_BARS = 15

# One palette that reads well on BOTH a light and a dark page. Charts have a
# transparent background, so the page theme shows through. Text uses a
# mid-grey and the series colours are medium tones.
CARD_COLOR = "none"         # transparent chart background
TEXT_COLOR = "#7D8590"      # titles and labels
MUTED_COLOR = "#7D8590"     # ticks, zero stars, notes
GRID_COLOR = "#7D8590"      # axis lines
SLICE_TEXT_COLOR = "#0D1117"  # percentage text drawn on the pie slices

PIE_COLORS = ["#2F81F7", "#E8833A", "#2EA043", "#A371F7", "#F85149", "#1FB6B6"]
OTHER_COLOR = "#6E7681"
NO_LANGUAGE_COLOR = "#8B949E"
BAR_COLOR = "#2F81F7"
WEEK_COLOR = "#2EA043"
GOLD = "#D29922"
GRAY = MUTED_COLOR


def _new_figure(width, height):
    """Create a figure and one axes with a transparent background."""
    fig = Figure(figsize=(width, height), facecolor=CARD_COLOR)
    ax = fig.subplots()
    ax.set_facecolor(CARD_COLOR)
    return fig, ax


def _style_axes(ax, title):
    """Apply neutral colours, a title and clean spines to an axes."""
    ax.set_title(title, color=TEXT_COLOR, fontsize=12, pad=12)
    ax.tick_params(colors=MUTED_COLOR)
    ax.xaxis.label.set_color(MUTED_COLOR)
    ax.yaxis.label.set_color(MUTED_COLOR)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID_COLOR)


def _message_figure(title, message):
    """Make a small figure that only shows a message (used for empty data)."""
    fig, ax = _new_figure(5, 3.5)
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color=MUTED_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=12, pad=12)
    fig.tight_layout()
    return fig


def _percent_label(percent):
    """Show a percentage on a pie slice only if the slice is big enough."""
    if percent < 5:
        return ""
    return "{:.0f}%".format(percent)


def language_pie(counts):
    """Pie chart of primary languages by repo count."""
    title = "Languages (by repo count)"
    if counts is None or len(counts) == 0:
        return _message_figure(title, "No language data")

    labels = [str(name) for name in counts.index]
    values = [int(value) for value in counts.values]
    colors = []
    for position, label in enumerate(labels):
        if label == "Other":
            colors.append(OTHER_COLOR)
        else:
            colors.append(PIE_COLORS[position % len(PIE_COLORS)])

    fig, ax = _new_figure(5, 4.2)
    _wedges, label_texts, percent_texts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct=_percent_label,
        startangle=90,
        counterclock=False,
        wedgeprops={"edgecolor": "none"},
    )
    for text in label_texts:
        text.set_color(TEXT_COLOR)
    for text in percent_texts:
        text.set_color(SLICE_TEXT_COLOR)   # dark text on the coloured slices
        text.set_fontweight("bold")
    ax.set_title(title, color=TEXT_COLOR, fontsize=12, pad=12)
    fig.tight_layout()
    return fig


def all_repos_bar(df):
    """Horizontal bars for all repos (size in KB), with stars written next to each bar."""
    title = "All repos (bar = size in KB, ★ = stars)"
    if df is None or df.empty:
        return _message_figure(title, "No repositories to show")

    total_repos = len(df)
    shown = df.sort_values("size_kb", ascending=False, kind="stable").head(MAX_BARS)

    labels = []
    sizes = []
    stars = []
    for _, row in shown.iterrows():
        language = row["language"]
        if not isinstance(language, str) or not language:
            language = "No language"
        labels.append(str(row["name"]) + "  (" + language + ")")
        sizes.append(int(row["size_kb"]))
        stars.append(int(row["stars"]))

    biggest = max(max(sizes), 1)
    positions = list(range(len(sizes)))

    fig, ax = _new_figure(9, max(3.0, 0.38 * len(sizes) + 1.5))
    ax.barh(positions, sizes, color=BAR_COLOR, height=0.7)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_COLOR)
    ax.invert_yaxis()            # largest repo at the top
    ax.set_xlim(0, biggest * 1.15)  # leave room for the star text

    padding = biggest * 0.012
    for position, size, star_count in zip(positions, sizes, stars):
        color = GOLD if star_count > 0 else GRAY
        ax.text(size + padding, position, "★ " + str(star_count),
                va="center", ha="left", fontsize=9, color=color)

    if total_repos > MAX_BARS:
        note = "Showing " + str(MAX_BARS) + " of " + str(total_repos) + " repos"
        ax.text(0.99, 0.02, note, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=9, color=MUTED_COLOR)

    ax.set_xlabel("Repo size (KB)")
    _style_axes(ax, title)
    fig.tight_layout()
    return fig


def weekly_activity_bar(weekly):
    """Bar chart of events per week. Week 1 is the oldest week."""
    title = "Weekly activity (last 13 weeks)"
    values = [int(value) for value in weekly]
    week_numbers = list(range(1, len(values) + 1))

    fig, ax = _new_figure(6, 4.2)
    ax.bar(week_numbers, values, color=WEEK_COLOR, width=0.7)
    ax.set_xticks(week_numbers)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    if not values or max(values) == 0:
        ax.set_ylim(0, 1)
    ax.set_xlabel("Week (1 = oldest)")
    ax.set_ylabel("Events")
    _style_axes(ax, title)
    fig.tight_layout()
    return fig


def learning_timeline(timeline):
    """Stacked bars: repos created per year, split by primary language."""
    title = "Learning timeline (repos created per year)"
    if timeline is None or timeline.empty:
        return _message_figure(title, "No repositories to show")

    years = [str(year) for year in timeline.index]
    fig, ax = _new_figure(8, 4.2)
    bottoms = [0] * len(years)
    for position, language in enumerate(timeline.columns):
        values = [int(v) for v in timeline[language]]
        if language == "Other":
            color = OTHER_COLOR
        elif language == "No language":
            color = NO_LANGUAGE_COLOR
        else:
            color = PIE_COLORS[position % len(PIE_COLORS)]
        ax.bar(years, values, bottom=bottoms, label=str(language), color=color, width=0.7)
        bottoms = [b + v for b, v in zip(bottoms, values)]

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Year created")
    ax.set_ylabel("Repos")
    legend = ax.legend(title="Language", fontsize=8, loc="upper left",
                       bbox_to_anchor=(1.01, 1), facecolor="none",
                       edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
    legend.get_title().set_color(MUTED_COLOR)
    _style_axes(ax, title)
    fig.tight_layout()
    return fig


def activity_type_bar(counts):
    """Horizontal bars: how many events of each type (pushes, pull requests ...)."""
    title = "What the user does (events by type)"
    if counts is None or len(counts) == 0:
        return _message_figure(title, "No public activity to show")

    labels = [str(name) for name in counts.index]
    values = [int(value) for value in counts.values]
    positions = list(range(len(values)))
    biggest = max(max(values), 1)

    fig, ax = _new_figure(7, max(2.8, 0.45 * len(values) + 1.4))
    ax.barh(positions, values, color=PIE_COLORS[3], height=0.65)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9, color=TEXT_COLOR)
    ax.invert_yaxis()                 # biggest type at the top
    ax.set_xlim(0, biggest * 1.15)    # leave room for the number text
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    for position, value in zip(positions, values):
        ax.text(value + biggest * 0.012, position, str(value),
                va="center", ha="left", fontsize=9, color=MUTED_COLOR)

    ax.set_xlabel("Events")
    _style_axes(ax, title)
    fig.tight_layout()
    return fig