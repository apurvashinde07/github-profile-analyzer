"""Builds the downloadable PDF profile report.

The report is made with matplotlib only (no extra library). It has a summary
page with the key numbers and the top repositories, followed by the charts.
This file has no Streamlit code, so it can be tested without a browser.
"""

import io
import textwrap
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")  # must be set before any figure is created

import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

import analysis
import charts

PAGE_WIDTH = 8.27     # A4 width in inches
PAGE_HEIGHT = 11.69   # A4 height in inches
IMAGE_WIDTH = 5.2     # width of each chart on the page, in inches
MARGIN_TOP = 0.7
GAP = 0.35
TEXT_COLOR = "#222222"
MUTED_COLOR = "#666666"
ACCENT_COLOR = "#2F81F7"
DISCLAIMER = ("This report measures public activity, language usage and consistency, "
              "not programming skill.")
EVENTS_NOTE = ("Activity comes from GitHub's public events feed, which only covers "
               "about the last 90 days (roughly 300 events at most).")


def _new_page():
    """Create an empty A4 page with a white background."""
    return Figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT), facecolor="white")


def _wrap(text, width):
    """Wrap text into a list of lines."""
    return textwrap.wrap(text or "", width=width) or [""]


def _summary_page(profile, df, active, summary):
    """Build page 1: name, key numbers, summary sentence and top repositories."""
    profile = profile or {}
    login = profile.get("login") or ""
    name = profile.get("name") or login or "Unknown user"
    reach = analysis.reach_summary(profile, df)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    fig = _new_page()
    y = 0.95

    def put(text, size=11, color=TEXT_COLOR, weight="normal", gap=0.028):
        """Write one line of text and move the cursor down."""
        nonlocal y
        fig.text(0.09, y, text, fontsize=size, color=color, fontweight=weight, va="top")
        y -= gap

    put("GitHub Profile Report", size=22, weight="bold", color=ACCENT_COLOR, gap=0.045)
    put(name, size=16, weight="bold", gap=0.03)
    put("@" + login, size=11, color=MUTED_COLOR, gap=0.026)
    for line in _wrap(profile.get("bio"), 80):
        put(line, size=10, color=MUTED_COLOR, gap=0.022)
    put("Generated on " + today + " (UTC)", size=9, color=MUTED_COLOR, gap=0.04)

    put("Key numbers", size=13, weight="bold", gap=0.034)
    numbers = [
        ("Repositories", len(df)),
        ("Followers", reach["followers"]),
        ("Following", reach["following"]),
        ("Total stars", reach["stars"]),
        ("Total forks", reach["forks"]),
        ("Active days (last 90)", active),
        ("Member since", analysis.account_year(profile)),
    ]
    for label, value in numbers:
        fig.text(0.09, y, label, fontsize=11, color=MUTED_COLOR, va="top")
        fig.text(0.42, y, str(value), fontsize=11, color=TEXT_COLOR,
                 fontweight="bold", va="top")
        y -= 0.026
    y -= 0.016

    put("Summary", size=13, weight="bold", gap=0.034)
    for line in _wrap(summary, 85):
        put(line, size=10.5, gap=0.024)
    y -= 0.018

    top = analysis.top_repos(df)
    put("Top repositories (most stars first)", size=13, weight="bold", gap=0.034)
    if top.empty:
        put("No public repositories.", size=10.5, color=MUTED_COLOR)
    else:
        fig.text(0.09, y, "Name", fontsize=10, color=MUTED_COLOR, va="top")
        fig.text(0.50, y, "Language", fontsize=10, color=MUTED_COLOR, va="top")
        fig.text(0.74, y, "Stars", fontsize=10, color=MUTED_COLOR, va="top")
        fig.text(0.84, y, "Forks", fontsize=10, color=MUTED_COLOR, va="top")
        y -= 0.026
        for _, row in top.iterrows():
            language = row["language"] if isinstance(row["language"], str) else "(No language)"
            fig.text(0.09, y, str(row["name"])[:34], fontsize=10.5, va="top", color=TEXT_COLOR)
            fig.text(0.50, y, language, fontsize=10.5, va="top", color=TEXT_COLOR)
            fig.text(0.74, y, str(row["stars"]), fontsize=10.5, va="top", color=TEXT_COLOR)
            fig.text(0.84, y, str(row["forks"]), fontsize=10.5, va="top", color=TEXT_COLOR)
            y -= 0.024

    fig.text(0.09, 0.07, DISCLAIMER, fontsize=8.5, color=MUTED_COLOR, va="top")
    fig.text(0.09, 0.05, EVENTS_NOTE, fontsize=8.5, color=MUTED_COLOR, va="top")
    return fig


def _chart_image(fig):
    """Draw a chart figure to an image array on a white background."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, facecolor="white", bbox_inches="tight")
    buffer.seek(0)
    return mpimg.imread(buffer)


def _chart_pages(images):
    """Place chart images on A4 pages from top to bottom. Returns a list of figures."""
    pages = []
    page = None
    y_top = 0.0   # distance from the top of the page, in inches
    for image in images:
        height = IMAGE_WIDTH * image.shape[0] / image.shape[1]
        if page is None or y_top + height > PAGE_HEIGHT - MARGIN_TOP:
            page = _new_page()
            pages.append(page)
            y_top = MARGIN_TOP
        left = (PAGE_WIDTH - IMAGE_WIDTH) / 2 / PAGE_WIDTH
        bottom = (PAGE_HEIGHT - y_top - height) / PAGE_HEIGHT
        ax = page.add_axes([left, bottom, IMAGE_WIDTH / PAGE_WIDTH, height / PAGE_HEIGHT])
        ax.imshow(image)
        ax.axis("off")
        y_top += height + GAP
    return pages


def build_pdf_report(profile, df, weekly, active, summary):
    """Return the profile report as PDF bytes.

    profile: profile dict from GitHub, df: repo DataFrame, weekly: 13 weekly
    counts, active: active days, summary: the one-sentence summary text.
    """
    chart_figures = []
    if df is not None and not df.empty:
        chart_figures.append(charts.language_pie(analysis.language_counts(df)))
    chart_figures.append(charts.weekly_activity_bar(weekly))
    if df is not None and not df.empty:
        chart_figures.append(charts.all_repos_bar(df))
        chart_figures.append(charts.learning_timeline(analysis.repos_per_year_by_language(df)))

    images = [_chart_image(fig) for fig in chart_figures]
    pages = [_summary_page(profile, df, active, summary)] + _chart_pages(images)

    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        for page in pages:
            pdf.savefig(page, facecolor="white")
    return buffer.getvalue()