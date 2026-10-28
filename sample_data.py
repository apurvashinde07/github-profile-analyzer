"""Bundled fictional data for Demo mode.

Nothing in this file is a real person. All dates are calculated from
today's date, so the charts are never empty and no network is needed.
"""

from datetime import datetime, timedelta, timezone

SAMPLE_LOGIN = "sample-student"

# One row per repository:
# (name, language, stars, forks, size_kb, created_days_ago, pushed_days_ago,
#  description, topics, license, homepage, is_fork)
REPO_ROWS = [
    ("crop-recommender", "Python", 3, 1, 920, 980, 40,
     "Suggests crops from soil and weather data", ["machine-learning", "agriculture"],
     "mit", "", False),
    ("portfolio-site", "HTML", 2, 0, 310, 700, 12,
     "My personal portfolio website", ["portfolio", "html", "css"],
     None, "https://sample-student.example.com", False),
    ("dsa-practice", "Java", 0, 0, 150, 850, 25,
     "Data structures practice problems", [], None, "", False),
    ("price-tracker", "Python", 1, 0, 85, 520, 60,
     "Tracks product prices over time", ["web", "python"], "mit", "", False),
    ("chat-ui", "JavaScript", 0, 0, 68, 400, 90,
     "Simple chat interface", [], None, "", False),
    ("voice-assistant", "Python", 1, 0, 64, 600, 130,
     "Basic voice assistant", ["python"], None, "", False),
    ("weather-app", "JavaScript", 0, 0, 53, 450, 150,
     "Weather lookup app", [], None, "", False),
    ("todo-app", "JavaScript", 0, 0, 40, 300, 200,
     "", [], None, "", False),
    ("sorting-visualizer", "C++", 0, 0, 33, 750, 260,
     "Visualises sorting algorithms", [], None, "", False),
    ("bank-system", "Python", 0, 0, 27, 1000, 320,
     "", [], None, "", False),
    ("quiz-game", "Python", 0, 0, 20, 900, 380,
     "Console quiz game", [], None, "", False),
    ("login-page", "HTML", 0, 0, 16, 560, 420,
     "", [], None, "", False),
    ("calculator", "Java", 0, 0, 9, 1050, 500,
     "Basic calculator", [], None, "", False),
    ("notes-cli", "Python", 0, 0, 7, 150, 20,
     "Command line notes tool", ["cli"], "mit", "", False),
    # A forked repo, so the "Include forked repos" checkbox has an effect.
    ("open-source-fork", "Python", 0, 0, 2400, 200, 180,
     "Fork used for practising pull requests", [], "mit", "", True),
]

# Events per week, oldest week first. Weeks 3 and 8 are fully inactive.
WEEKLY_PATTERN = [3, 5, 0, 2, 8, 12, 7, 0, 4, 9, 6, 11, 5]
# Number of different days with activity in each week (adds up to 24).
ACTIVE_DAYS_PATTERN = [2, 2, 0, 1, 3, 3, 2, 0, 2, 3, 2, 3, 1]
DAY_OFFSETS = [2, 3, 4]   # days after Monday used for events
EVENT_TYPES = ["PushEvent", "CreateEvent", "IssuesEvent", "PullRequestEvent"]


def _iso(moment):
    """Format a datetime the way the GitHub API does."""
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_sample_profile(now=None):
    """Return a fictional profile in the same shape as GET /users/{name}."""
    if now is None:
        now = datetime.now(timezone.utc)
    return {
        "login": SAMPLE_LOGIN,
        "name": "Sample Student",
        "bio": "CS student | Python | learning web dev",
        "followers": 18,
        "following": 21,
        "public_repos": len(REPO_ROWS),
        "created_at": _iso(now - timedelta(days=1100)),
        "avatar_url": None,   # no image, so Demo mode needs no network
        "html_url": None,
    }


def get_sample_repos(now=None):
    """Return fictional repositories in the same shape as the repos endpoint."""
    if now is None:
        now = datetime.now(timezone.utc)
    repos = []
    for row in REPO_ROWS:
        (name, language, stars, forks, size_kb, created_ago, pushed_ago,
         description, topics, license_key, homepage, is_fork) = row
        license_info = None
        if license_key:
            license_info = {"key": license_key, "name": license_key.upper() + " License"}
        repos.append({
            "name": name,
            "language": language,
            "stargazers_count": stars,
            "forks_count": forks,
            "size": size_kb,
            "fork": is_fork,
            "pushed_at": _iso(now - timedelta(days=pushed_ago)),
            "created_at": _iso(now - timedelta(days=created_ago)),
            "description": description or None,
            "html_url": "https://example.com/" + SAMPLE_LOGIN + "/" + name,
            "topics": list(topics),
            "license": license_info,
            "homepage": homepage or None,
        })
    return repos


def get_sample_events(today=None):
    """Return fictional events spread over the last 13 weeks.

    Events are placed relative to today (UTC). Weeks 3 and 8 have no events.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()
    this_monday = today - timedelta(days=today.weekday())

    events = []
    event_number = 0
    for week_index in range(13):
        count = WEEKLY_PATTERN[week_index]
        if count == 0:
            continue
        monday = this_monday - timedelta(weeks=12 - week_index)
        if week_index == 12:
            offsets = [0]   # the current week: use Monday so it is never in the future
        else:
            offsets = DAY_OFFSETS[:ACTIVE_DAYS_PATTERN[week_index]]

        per_day = count // len(offsets)
        extra = count % len(offsets)
        for position, offset in enumerate(offsets):
            events_today = per_day + (1 if position < extra else 0)
            day = monday + timedelta(days=offset)
            for i in range(events_today):
                moment = datetime(day.year, day.month, day.day, 8 + i, 0, 0)
                event_number += 1
                events.append({
                    "id": str(event_number),
                    "type": EVENT_TYPES[event_number % len(EVENT_TYPES)],
                    "created_at": _iso(moment),
                    "repo": {"name": SAMPLE_LOGIN + "/sample-repo"},
                })
    return events


SAMPLE_README = """<!-- sample profile README (fictional) -->
<h1 align="center">Hi, I'm Sample Student</h1>
![visitors](https://example.com/badge.svg)

## About me
- I am a computer science student who loves building small tools with **Python**.
- I am currently learning web development with HTML, CSS and JavaScript.
- Ask me about data structures, machine learning basics and Git.

| Stats | Badges |
| --- | --- |
| ![stats](https://example.com/stats.svg) | ![top](https://example.com/top.svg) |

[Portfolio](https://sample-student.example.com)
"""


def get_sample_readme():
    """Return a fictional profile README in the same shape as the real one."""
    return {"text": SAMPLE_README, "url": None}