"""Pure data logic for the GitHub Profile Analyzer.

This file uses only pandas and the standard library. It has no Streamlit
and no matplotlib code, so it can be tested without a browser or a network.
"""

import re
from datetime import datetime, timedelta, timezone

import pandas as pd

REPO_COLUMNS = [
    "name", "language", "stars", "forks",
    "size_kb", "last_pushed", "created", "url",
]
TOP_LANGUAGE_LIMIT = 6   # languages beyond the top 6 are grouped as "Other"


def repos_to_dataframe(repos, include_forks=False):
    """Turn the raw repo list from the API into a tidy DataFrame.

    Forked repositories are left out unless include_forks is True.
    """
    rows = []
    for repo in repos:
        if repo.get("fork") and not include_forks:
            continue
        rows.append({
            "name": repo.get("name") or "(unnamed)",
            "language": repo.get("language") or None,
            "stars": int(repo.get("stargazers_count") or 0),
            "forks": int(repo.get("forks_count") or 0),
            "size_kb": int(repo.get("size") or 0),
            "last_pushed": repo.get("pushed_at"),
            "created": repo.get("created_at"),
            "url": repo.get("html_url"),
        })
    df = pd.DataFrame(rows, columns=REPO_COLUMNS)
    df["last_pushed"] = pd.to_datetime(df["last_pushed"], utc=True, errors="coerce")
    df["created"] = pd.to_datetime(df["created"], utc=True, errors="coerce")
    return df


def language_counts(df):
    """Count repos per primary language. Returns a Series, biggest first.

    Repos with no language are ignored. Everything beyond the top 6
    languages is added up under the name "Other".
    """
    if df is None or df.empty:
        return pd.Series(dtype="int64")
    languages = df["language"].dropna()
    if languages.empty:
        return pd.Series(dtype="int64")

    counts = languages.value_counts()
    # Sort by name first, then by count, so ties always come out in the same order.
    counts = counts.sort_index().sort_values(ascending=False, kind="stable")

    if len(counts) > TOP_LANGUAGE_LIMIT:
        top = counts.iloc[:TOP_LANGUAGE_LIMIT]
        other_total = int(counts.iloc[TOP_LANGUAGE_LIMIT:].sum())
        counts = pd.concat([top, pd.Series({"Other": other_total})])

    counts = counts.astype("int64")
    counts.name = "repos"
    return counts


def total_stars(df):
    """Add up the stars of all repos in the DataFrame."""
    if df is None or df.empty:
        return 0
    return int(df["stars"].sum())


def account_year(profile):
    """Return the year the account was created as text, or 'N/A'."""
    created_at = profile.get("created_at") if profile else None
    if created_at and len(created_at) >= 4:
        return created_at[:4]
    return "N/A"


def _today_utc():
    """Return today's date in UTC."""
    return datetime.now(timezone.utc).date()


def _event_date(event):
    """Return the UTC calendar date of an event, or None if it cannot be read."""
    text = event.get("created_at")
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date()


def weekly_activity(events, weeks=13, today=None):
    """Count events per calendar week for the last `weeks` weeks.

    Weeks start on Monday (UTC). The list is ordered oldest week first
    and weeks without events are 0. The last item is the current week.
    """
    if today is None:
        today = _today_utc()
    this_monday = today - timedelta(days=today.weekday())
    first_monday = this_monday - timedelta(weeks=weeks - 1)

    counts = [0] * weeks
    for event in events:
        event_day = _event_date(event)
        if event_day is None:
            continue
        days_since_start = (event_day - first_monday).days
        if 0 <= days_since_start < weeks * 7:
            counts[days_since_start // 7] += 1
    return counts


def active_days(events, days=90, today=None):
    """Count distinct UTC days with at least one event in the last `days` days."""
    if today is None:
        today = _today_utc()
    first_day = today - timedelta(days=days - 1)

    busy_days = set()
    for event in events:
        event_day = _event_date(event)
        if event_day is not None and first_day <= event_day <= today:
            busy_days.add(event_day)
    return len(busy_days)


def _week_list_text(week_numbers):
    """Write week numbers as text, e.g. 'weeks 3 and 8'."""
    labels = [str(number) for number in week_numbers]
    if len(labels) == 1:
        return "week " + labels[0]
    return "weeks " + ", ".join(labels[:-1]) + " and " + labels[-1]


def build_summary(df, weekly, active):
    """Build one readable summary sentence. Works with empty data."""
    parts = []

    counts = language_counts(df)
    if len(counts) == 0:
        parts.append("No language data is available.")
    else:
        total_repos = len(df)
        noun = "repo" if total_repos == 1 else "repos"
        top_name = counts.index[0]
        top_count = int(counts.iloc[0])
        parts.append(
            "Most used language: " + str(top_name) + " ("
            + str(top_count) + " of " + str(total_repos) + " " + noun + ")."
        )

    if active == 0 and sum(weekly) == 0:
        parts.append("No public activity in the last 90 days.")
    else:
        parts.append("Active on " + str(active) + " of the last 90 days.")
        empty_weeks = [i + 1 for i, value in enumerate(weekly) if value == 0]
        text = "Weeks with no activity: " + str(len(empty_weeks))
        if empty_weeks:
            text += " (" + _week_list_text(empty_weeks) + ")"
        parts.append(text + ".")

    return " ".join(parts)


# ---------- Learning timeline ----------


def _timeline_label(language, top_languages):
    """Pick the column name for a repo: its language, 'Other' or 'No language'."""
    if not isinstance(language, str) or not language:
        return "No language"
    if language in top_languages:
        return language
    return "Other"


def repos_per_year_by_language(df):
    """Count repos created per year, split by primary language.

    Returns a DataFrame with one row per year (including years with no
    repos) and one column per language.
    """
    if df is None or df.empty:
        return pd.DataFrame()
    top_languages = [name for name in language_counts(df).index if name != "Other"]

    rows = []
    for _, row in df.iterrows():
        if pd.isna(row["created"]):
            continue
        rows.append({
            "year": int(row["created"].year),
            "language": _timeline_label(row["language"], top_languages),
        })
    if not rows:
        return pd.DataFrame()

    table = pd.crosstab(pd.Series([r["year"] for r in rows], name="year"),
                        pd.Series([r["language"] for r in rows], name="language"))
    all_years = range(int(table.index.min()), int(table.index.max()) + 1)
    table = table.reindex(all_years, fill_value=0)
    # Put the most common languages first.
    order = table.sum().sort_values(ascending=False, kind="stable").index
    return table[list(order)]


# ---------- Reach, top repos, activity types and CSV export ----------

TOP_REPO_LIMIT = 5

# Friendly names for GitHub event types. Anything not listed becomes "Other".
EVENT_LABELS = {
    "PushEvent": "Pushes",
    "PullRequestEvent": "Pull requests",
    "IssuesEvent": "Issues",
    "CreateEvent": "Created (repo, branch or tag)",
    "IssueCommentEvent": "Comments and reviews",
    "PullRequestReviewEvent": "Comments and reviews",
    "PullRequestReviewCommentEvent": "Comments and reviews",
    "CommitCommentEvent": "Comments and reviews",
    "WatchEvent": "Stars given",
    "ForkEvent": "Forks made",
}


def reach_summary(profile, df):
    """Return the public popularity numbers of an account.

    Followers and following come from the profile. Stars and forks are
    added up over the repos in the DataFrame (forks of other people's
    projects are left out unless the user chose to include them).
    """
    profile = profile or {}
    total_forks = 0
    if df is not None and not df.empty:
        total_forks = int(df["forks"].sum())
    return {
        "followers": int(profile.get("followers") or 0),
        "following": int(profile.get("following") or 0),
        "stars": total_stars(df),
        "forks": total_forks,
    }


def top_repos(df, limit=TOP_REPO_LIMIT):
    """Return the most popular repos: most stars first, then most forks."""
    columns = ["name", "language", "stars", "forks"]
    if df is None or df.empty:
        return pd.DataFrame(columns=columns)
    ordered = df.sort_values(["stars", "forks", "name"],
                             ascending=[False, False, True], kind="stable")
    return ordered[columns].head(limit).reset_index(drop=True)


def event_type_counts(events):
    """Count events by activity type. Returns a Series, biggest first.

    Rare or unknown event types are added up under "Other".
    """
    totals = {}
    for event in events:
        label = EVENT_LABELS.get(event.get("type"), "Other")
        totals[label] = totals.get(label, 0) + 1
    if not totals:
        return pd.Series(dtype="int64")
    counts = pd.Series(totals, dtype="int64")
    # Sort by name first so ties always come out in the same order.
    counts = counts.sort_index().sort_values(ascending=False, kind="stable")
    if "Other" in counts.index and len(counts) > 1:
        counts = pd.concat([counts.drop("Other"), counts[["Other"]]])
    counts.name = "events"
    return counts


def repos_to_csv(df):
    """Return the repo table as CSV text (newest push first)."""
    columns = ["name", "language", "stars", "forks", "size_kb",
               "last_pushed", "created", "url"]
    if df is None or df.empty:
        return pd.DataFrame(columns=columns).to_csv(index=False)
    table = df.sort_values("last_pushed", ascending=False)[columns].copy()
    table["language"] = table["language"].fillna("")
    table["last_pushed"] = table["last_pushed"].dt.strftime("%Y-%m-%d").fillna("")
    table["created"] = table["created"].dt.strftime("%Y-%m-%d").fillna("")
    return table.to_csv(index=False)


# ---------- Profile README summary ----------

README_MAX_LINES = 5
README_LINE_LIMIT = 160

# Technology words that are looked for in the README text.
TECH_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP",
    "Ruby", "Kotlin", "Swift", "HTML", "CSS", "SQL", "React", "Angular", "Vue",
    "Node.js", "Django", "Flask", "Spring", "Docker", "Kubernetes", "Git", "Linux",
    "AWS", "Azure", "MongoDB", "MySQL", "PostgreSQL", "TensorFlow", "PyTorch",
    "Pandas", "NumPy", "Machine Learning", "Data Science", "Android", "Flutter",
]

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+")
_MARKERS = re.compile(r"^[\s>#*+\-]+|[*_`~]+")


def _clean_readme_line(line):
    """Remove markdown and HTML from one line and return plain text."""
    line = _IMAGE.sub("", line)
    line = _LINK.sub(r"\1", line)
    line = _HTML_TAG.sub("", line)
    line = _URL.sub("", line)
    line = _MARKERS.sub("", line)
    return " ".join(line.split())


def _keyword_found(text, keyword):
    """Return True if the keyword appears in the text as a whole word."""
    pattern = r"(?<![A-Za-z0-9+#])" + re.escape(keyword) + r"(?![A-Za-z0-9+#])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def summarize_readme(text):
    """Make a short summary of a profile README. No AI is used.

    Returns {"lines": first meaningful lines, "keywords": technologies that
    are mentioned, "words": number of words}, or None if there is no text.
    """
    if not text or not text.strip():
        return None
    body = _HTML_COMMENT.sub("", text)
    body = _CODE_FENCE.sub("", body)

    lines = []
    for raw_line in body.splitlines():
        if "|" in raw_line:      # table rows are mostly badges and layout
            continue
        line = _clean_readme_line(raw_line)
        if len(line) < 8 or len(line.split()) < 2:
            continue
        if line not in lines:
            lines.append(line[:README_LINE_LIMIT].rstrip())
        if len(lines) == README_MAX_LINES:
            break

    plain = _HTML_COMMENT.sub("", text)
    keywords = [word for word in TECH_KEYWORDS if _keyword_found(plain, word)]
    return {"lines": lines, "keywords": keywords, "words": len(plain.split())}