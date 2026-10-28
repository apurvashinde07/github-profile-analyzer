# GitHub Profile Analyzer

A small Streamlit web app that turns a GitHub username into an automatic,
data-driven summary of that person's public profile.

## What it does and the problem it solves

Judging a developer's public GitHub profile (interests, language mix and
consistency) normally means opening repositories one by one. That is slow and
never gives a combined picture. Enter a username here and the app fetches the
public data through the **official GitHub REST API** (no scraping) and shows:

- Three pages, chosen in the sidebar: **Home** (what the tool does and quick
  examples), **Analyzer** (the analysis) and **About** (project details, users,
  technologies and limitations).
- A profile card and key numbers: repos, followers, total stars, active days in
  the last 90 days, and the year the account was created.
- A pie chart of the language mix across repositories.
- A bar chart of **all** repositories (not only starred ones), with the stars
  written next to every bar, including "0".
- Weekly activity over the last 13 weeks, including weeks with no activity.
- A full, sortable table of all repositories.
- A "Reach" section: followers, following, total stars, total forks and the top
  repositories (GitHub does not share profile views, so these are the public
  popularity numbers).
- A **profile README summary**: the app fetches the user's profile README (the
  repository named like the username) and shows its key lines and the
  technologies it mentions. The summary is extractive: no AI is used.
- A button to download the repository table as a CSV file.
- A button to download a PDF report (key numbers, summary, top repositories and charts).
- A one-sentence summary and a "Learning timeline" chart.
- A simple visual design: logo, icons, gradient header, cards, and a large
  sidebar menu (Home / Analyzer / About). Works on light and dark themes.

> **Important:** this tool measures public activity, language usage and
> consistency. It does **not** measure programming skill.

## Setup and run

Commands use the Windows `py` launcher:

```
py -m pip install -r requirements.txt
py -m streamlit run app.py
py test_analysis.py
```

Works on Python 3.9 to 3.13. The tests need no network and no pytest.

## Light and dark theme

The app supports both themes. Click the three-dot menu at the top right, open
**Settings**, and choose **Light**, **Dark** or **Use system setting**. The
charts have a transparent background, so they match whichever theme is active.

## Optional GitHub token

A token is optional. Without one, GitHub allows 60 requests per hour; with one,
5,000 per hour. To create one:

1. Open GitHub **Settings > Developer settings > Personal access tokens**.
2. Create a token and select **no scopes** (public data does not need any).
3. Paste it into the password field in the app sidebar.

The token is only used in request headers and is held only in session memory.
It is never printed, logged or written to disk.

## About page details

To show your name, college and guide on the About page, fill in
`DEVELOPER_NAME`, `COLLEGE_NAME` and `GUIDE_NAME` at the top of `pages.py`.

## Demo mode

Switch on **Demo mode (sample data)** in the sidebar to see the whole app with
a bundled, fictional profile ("Sample Student"). It makes no network calls.
It exists because the unauthenticated rate limit (60 requests per hour) can run
out during a live demo. Demo mode always works, and a banner says
"SAMPLE DATA - not a real person".

## Project structure

| File | Responsibility |
| --- | --- |
| `github_api.py` | Calls the GitHub REST API; custom errors; rate-limit info |
| `analysis.py` | Pure pandas logic (no Streamlit, no matplotlib) |
| `charts.py` | Matplotlib charts (Agg backend), each returns a Figure |
| `report.py` | Builds the downloadable PDF report (matplotlib only) |
| `sample_data.py` | Fictional data for Demo mode, dated relative to today |
| `app.py` | Streamlit interface: page navigation and the Analyzer page |
| `pages.py` | The Home and About pages (fixed text) |
| `branding.py` | Logo (SVG) and page icon helpers |
| `styles.py` | Page CSS (cards, header, sidebar, buttons) |
| `assets/logo.svg`, `assets/logo.png` | The project logo |
| `test_analysis.py` | Offline tests with PASS/FAIL output |
| `requirements.txt` | requests, pandas, matplotlib, streamlit |

## How it works

1. The user enters a username (or switches on Demo mode) and presses **Analyze**.
2. `github_api.py` calls `GET /users/{username}`, `GET /users/{username}/repos`
   (up to 3 pages), `GET /users/{username}/events/public` (up to 3 pages) and
   `GET /repos/{username}/{username}/readme` (the profile README, if any).
   One analysis uses about 4 to 8 requests. The result is cached for 10 minutes.
3. `analysis.py` turns the raw JSON into a DataFrame, language counts, weekly
   counts, active days and a summary sentence.
4. `charts.py` draws the figures, and `app.py` lays everything out.
5. Errors (unknown user, rate limit, no internet) become friendly messages, never a stack trace.

## Extra

- **Learning timeline:** repos created per year, stacked by primary language.

## Limitations

- The events feed covers only about the last 90 days (roughly 300 events).
- Private repositories are invisible.
- The profile README is found only if a repository named exactly like the username exists.
- Repo size includes data files, so it is only a rough indicator.
- Only each repo's primary language is counted.
- Stars and repo counts do not measure skill.
- Profile views and "used by" counts are not available through the GitHub API.
- Watchers are not shown: the repo list reports the star count as watchers.
- GitHub rate limits apply (60 per hour without a token).
- Up to 300 repositories are analyzed.