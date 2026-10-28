"""Offline tests for the GitHub Profile Analyzer.

Run with:  py test_analysis.py
No pytest and no network are needed. GitHub calls are replaced by mocks.
"""

import sys
from datetime import date, timedelta
from unittest import mock

import requests
from matplotlib.figure import Figure

import analysis
import charts
import github_api
import report
import sample_data

# A fixed "today" and the seven days after it, so every weekday is tested.
FIXED_TODAY = date(2026, 10, 11)
EXPECTED_WEEKLY = [3, 5, 0, 2, 8, 12, 7, 0, 4, 9, 6, 11, 5]


def fake_response(status, data=None, headers=None):
    """Build a fake requests response."""
    response = mock.Mock()
    response.status_code = status
    response.headers = headers or {}
    response.json.return_value = data if data is not None else {}
    return response


def sample_df(include_forks=False):
    """DataFrame built from the bundled sample repos."""
    return analysis.repos_to_dataframe(sample_data.get_sample_repos(), include_forks)


# ---------- analysis checks ----------

def test_forks_excluded_by_default():
    return len(sample_df()) == 14


def test_forks_included_when_requested():
    return len(sample_df(include_forks=True)) == 15


def test_total_stars():
    return analysis.total_stars(sample_df()) == 7


def test_total_stars_empty():
    return analysis.total_stars(analysis.repos_to_dataframe([])) == 0


def test_language_counts_sample():
    counts = analysis.language_counts(sample_df())
    return (counts["Python"] == 6 and counts["JavaScript"] == 3
            and counts["HTML"] == 2 and counts["Java"] == 2 and counts["C++"] == 1)


def test_language_ignores_missing_language():
    repos = [{"name": "a", "language": None}, {"name": "b", "language": "Go"}]
    counts = analysis.language_counts(analysis.repos_to_dataframe(repos))
    return list(counts.index) == ["Go"]


def test_language_other_grouping():
    languages = ["A", "A", "A", "B", "B", "C", "D", "E", "F", "G", "H"]
    repos = [{"name": "r" + str(i), "language": lang} for i, lang in enumerate(languages)]
    counts = analysis.language_counts(analysis.repos_to_dataframe(repos))
    return len(counts) == 7 and counts.index[-1] == "Other" and counts["Other"] == 2


def test_weekly_activity_values():
    for offset in range(7):
        day = FIXED_TODAY + timedelta(days=offset)
        events = sample_data.get_sample_events(today=day)
        if analysis.weekly_activity(events, today=day) != EXPECTED_WEEKLY:
            return False
    return True


def test_weekly_activity_has_13_values_and_zeros():
    weekly = analysis.weekly_activity([], today=FIXED_TODAY)
    return len(weekly) == 13 and weekly == [0] * 13


def test_weekly_activity_empty_weeks_are_zero():
    events = sample_data.get_sample_events(today=FIXED_TODAY)
    weekly = analysis.weekly_activity(events, today=FIXED_TODAY)
    return weekly[2] == 0 and weekly[7] == 0


def test_active_days_sample():
    for offset in range(7):
        day = FIXED_TODAY + timedelta(days=offset)
        events = sample_data.get_sample_events(today=day)
        if analysis.active_days(events, today=day) != 24:
            return False
    return True


def test_active_days_ignores_old_events():
    old_day = FIXED_TODAY - timedelta(days=120)
    events = [
        {"created_at": old_day.isoformat() + "T10:00:00Z"},
        {"created_at": FIXED_TODAY.isoformat() + "T08:00:00Z"},
        {"created_at": FIXED_TODAY.isoformat() + "T09:00:00Z"},
    ]
    return analysis.active_days(events, today=FIXED_TODAY) == 1


def test_summary_sample():
    events = sample_data.get_sample_events(today=FIXED_TODAY)
    weekly = analysis.weekly_activity(events, today=FIXED_TODAY)
    active = analysis.active_days(events, today=FIXED_TODAY)
    text = analysis.build_summary(sample_df(), weekly, active)
    return ("Most used language: Python (6 of 14 repos)." in text
            and "Active on 24 of the last 90 days." in text
            and "Weeks with no activity: 2 (weeks 3 and 8)." in text)


def test_summary_empty_data():
    text = analysis.build_summary(analysis.repos_to_dataframe([]), [0] * 13, 0)
    return isinstance(text, str) and "No public activity" in text and "No language" in text


# ---------- chart checks ----------

def test_language_pie_returns_figure():
    counts = analysis.language_counts(sample_df())
    return isinstance(charts.language_pie(counts), Figure)


def test_weekly_chart_returns_figure_with_13_bars():
    fig = charts.weekly_activity_bar(EXPECTED_WEEKLY)
    return isinstance(fig, Figure) and len(fig.axes[0].patches) == 13


def test_all_repos_chart_shows_zero_star_repos():
    fig = charts.all_repos_bar(sample_df())
    texts = [t.get_text() for t in fig.axes[0].texts]
    return (isinstance(fig, Figure) and len(fig.axes[0].patches) == 14
            and texts.count("\u2605 0") == 10 and "\u2605 3" in texts)


def test_all_repos_chart_star_colors():
    fig = charts.all_repos_bar(sample_df())
    colors = {t.get_text(): t.get_color() for t in fig.axes[0].texts}
    return colors["\u2605 3"] == charts.GOLD and colors["\u2605 0"] == charts.GRAY


def test_all_repos_chart_limits_to_15():
    repos = [{"name": "repo" + str(i), "size": i * 10, "language": "Go"} for i in range(20)]
    fig = charts.all_repos_bar(analysis.repos_to_dataframe(repos))
    texts = [t.get_text() for t in fig.axes[0].texts]
    return len(fig.axes[0].patches) == 15 and "Showing 15 of 20 repos" in texts


def test_charts_handle_empty_data():
    empty = analysis.repos_to_dataframe([])
    figures = [
        charts.language_pie(analysis.language_counts(empty)),
        charts.all_repos_bar(empty),
        charts.weekly_activity_bar([0] * 13),
    ]
    return all(isinstance(fig, Figure) for fig in figures)


# ---------- github_api checks (all mocked) ----------

def test_api_404_is_user_not_found():
    with mock.patch("requests.get", return_value=fake_response(404)):
        try:
            github_api.get_user("nobody")
        except github_api.UserNotFoundError:
            return True
    return False


def test_api_403_with_zero_remaining_is_rate_limit():
    headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1999999999"}
    with mock.patch("requests.get", return_value=fake_response(403, headers=headers)):
        try:
            github_api.get_user("someone")
        except github_api.RateLimitError as error:
            return error.reset_time == 1999999999
    return False


def test_api_403_with_requests_left_is_generic_error():
    headers = {"x-ratelimit-remaining": "42"}
    with mock.patch("requests.get", return_value=fake_response(403, headers=headers)):
        try:
            github_api.get_user("someone")
        except github_api.RateLimitError:
            return False
        except github_api.GitHubAPIError:
            return True
    return False


def test_api_network_failure_is_api_error():
    with mock.patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")):
        try:
            github_api.get_user("someone")
        except github_api.GitHubAPIError as error:
            return error.network_problem is True
    return False


def test_api_success_returns_json_and_rate_info():
    headers = {"x-ratelimit-limit": "60", "x-ratelimit-remaining": "57",
               "x-ratelimit-reset": "1999999999"}
    with mock.patch("requests.get", return_value=fake_response(200, {"login": "x"}, headers)):
        data, rate = github_api.get_user("x")
    return data == {"login": "x"} and rate["remaining"] == 57 and rate["limit"] == 60


def test_api_headers_with_and_without_token():
    with mock.patch("requests.get", return_value=fake_response(200, {})) as fake_get:
        github_api.get_user("x")
        plain = fake_get.call_args.kwargs["headers"]
        github_api.get_user("x", token="abc123")
        with_token = fake_get.call_args.kwargs["headers"]
    return ("Authorization" not in plain
            and with_token["Authorization"] == "Bearer abc123"
            and plain["User-Agent"] == "github-profile-analyzer"
            and plain["Accept"] == "application/vnd.github+json")


def test_api_pagination_stops_after_three_pages():
    full_page = [{"name": "r"}] * 100
    with mock.patch("requests.get", return_value=fake_response(200, full_page)) as fake_get:
        repos, _ = github_api.get_repos("x")
    return fake_get.call_count == 3 and len(repos) == 300


def test_api_pagination_stops_on_short_page():
    with mock.patch("requests.get", return_value=fake_response(200, [{"name": "r"}])) as fake_get:
        repos, _ = github_api.get_events("x")
    return fake_get.call_count == 1 and len(repos) == 1


def test_username_helpers():
    return (github_api.clean_username("  @octocat ") == "octocat"
            and github_api.clean_username("https://github.com/octocat/") == "octocat"
            and github_api.is_valid_username("octocat")
            and not github_api.is_valid_username("bad name/..")
            and not github_api.is_valid_username(""))


def test_rate_limit_minutes():
    error = github_api.RateLimitError(reset_time=1000 + 600)
    return error.minutes_until_reset(now=1000) == 10


# ---------- learning timeline ----------

def test_timeline_totals_match_repo_count():
    timeline = analysis.repos_per_year_by_language(sample_df())
    return int(timeline.values.sum()) == 14 and "Python" in timeline.columns


def test_timeline_chart_returns_figure():
    figures = [
        charts.learning_timeline(analysis.repos_per_year_by_language(sample_df())),
        charts.learning_timeline(analysis.repos_per_year_by_language(analysis.repos_to_dataframe([]))),
    ]
    return all(isinstance(fig, Figure) for fig in figures)


# ---------- reach, top repos, activity types, CSV ----------

def test_reach_summary_sample():
    reach = analysis.reach_summary(sample_data.get_sample_profile(), sample_df())
    return (reach["followers"] == 18 and reach["following"] == 21
            and reach["stars"] == 7 and reach["forks"] == 1)


def test_reach_summary_empty():
    reach = analysis.reach_summary({}, analysis.repos_to_dataframe([]))
    return reach == {"followers": 0, "following": 0, "stars": 0, "forks": 0}


def test_top_repos_order_and_limit():
    top = analysis.top_repos(sample_df())
    return (len(top) == 5
            and list(top["name"][:3]) == ["crop-recommender", "portfolio-site", "price-tracker"]
            and top["stars"].is_monotonic_decreasing)


def test_top_repos_empty():
    return analysis.top_repos(analysis.repos_to_dataframe([])).empty


def test_event_type_counts_sample():
    events = sample_data.get_sample_events(today=FIXED_TODAY)
    counts = analysis.event_type_counts(events)
    return (int(counts.sum()) == len(events) == 72
            and int(counts["Pushes"]) == 18 and int(counts["Pull requests"]) == 18
            and int(counts["Issues"]) == 18)


def test_event_type_counts_groups_unknown_as_other():
    events = [{"type": "PushEvent"}, {"type": "MemberEvent"}, {"type": "PushEvent"}]
    counts = analysis.event_type_counts(events)
    return int(counts["Pushes"]) == 2 and int(counts["Other"]) == 1 and counts.index[-1] == "Other"


def test_event_type_counts_empty():
    return len(analysis.event_type_counts([])) == 0


def test_repos_to_csv_content():
    text = analysis.repos_to_csv(sample_df())
    lines = text.strip().splitlines()
    return (lines[0] == "name,language,stars,forks,size_kb,last_pushed,created,url"
            and len(lines) == 15 and "crop-recommender" in text)


def test_repos_to_csv_empty_has_header_only():
    text = analysis.repos_to_csv(analysis.repos_to_dataframe([]))
    return text.strip() == "name,language,stars,forks,size_kb,last_pushed,created,url"


def test_activity_chart_returns_figure():
    events = sample_data.get_sample_events(today=FIXED_TODAY)
    fig = charts.activity_type_bar(analysis.event_type_counts(events))
    empty = charts.activity_type_bar(analysis.event_type_counts([]))
    return isinstance(fig, Figure) and len(fig.axes[0].patches) == 4 and isinstance(empty, Figure)


# ---------- PDF report ----------

def _report_bytes(df):
    """Build a report for the sample profile and the given repo DataFrame."""
    events = sample_data.get_sample_events(today=FIXED_TODAY)
    weekly = analysis.weekly_activity(events, today=FIXED_TODAY)
    active = analysis.active_days(events, today=FIXED_TODAY)
    summary = analysis.build_summary(df, weekly, active)
    return report.build_pdf_report(sample_data.get_sample_profile(), df, weekly, active, summary)


def _page_count(data):
    """Count the pages of a PDF made by matplotlib."""
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


def test_report_is_a_pdf_with_pages():
    data = _report_bytes(sample_df())
    return isinstance(data, bytes) and data.startswith(b"%PDF") and _page_count(data) == 3


def test_report_works_with_no_repos():
    data = _report_bytes(analysis.repos_to_dataframe([]))
    return data.startswith(b"%PDF") and _page_count(data) == 2


def test_report_works_with_empty_profile():
    empty = analysis.repos_to_dataframe([])
    data = report.build_pdf_report({}, empty, [0] * 13, 0, analysis.build_summary(empty, [0] * 13, 0))
    return data.startswith(b"%PDF")


# ---------- profile README ----------

def test_readme_summary_cleans_markdown():
    summary = analysis.summarize_readme(sample_data.get_sample_readme()["text"])
    joined = " ".join(summary["lines"])
    return (len(summary["lines"]) == 5
            and "http" not in joined and "![" not in joined and "|" not in joined
            and "<" not in joined and "**" not in joined
            and summary["lines"][0] == "Hi, I'm Sample Student")


def test_readme_summary_finds_keywords():
    summary = analysis.summarize_readme(sample_data.get_sample_readme()["text"])
    return all(word in summary["keywords"] for word in ("Python", "JavaScript", "Git"))


def test_readme_keywords_need_whole_words():
    summary = analysis.summarize_readme("I like Django and Gopher stories and Gold coins")
    return "Django" in summary["keywords"] and "Go" not in summary["keywords"]


def test_readme_summary_empty_or_badges_only():
    return (analysis.summarize_readme("") is None
            and analysis.summarize_readme(None) is None
            and analysis.summarize_readme("![badge](https://x.io/a.svg)")["lines"] == [])


def test_api_profile_readme_not_found_is_none():
    with mock.patch("requests.get", return_value=fake_response(404)):
        info, _ = github_api.get_profile_readme("someone")
    return info is None


def test_api_profile_readme_is_decoded():
    import base64
    body = {"encoding": "base64", "html_url": "https://github.com/x/x/blob/main/README.md",
            "content": base64.b64encode("Hello \u2605 world".encode("utf-8")).decode("ascii")}
    with mock.patch("requests.get", return_value=fake_response(200, body)) as fake_get:
        info, _ = github_api.get_profile_readme("x")
    return (info["text"] == "Hello \u2605 world" and info["url"].startswith("https://github.com/")
            and fake_get.call_args.args[0].endswith("/repos/x/x/readme"))


ALL_TESTS = [
    ("forks are excluded by default", test_forks_excluded_by_default),
    ("forks are included when requested", test_forks_included_when_requested),
    ("total stars are summed correctly", test_total_stars),
    ("total stars of empty data is 0", test_total_stars_empty),
    ("language counts match the sample", test_language_counts_sample),
    ("repos without a language are ignored", test_language_ignores_missing_language),
    ("languages beyond the top 6 become Other", test_language_other_grouping),
    ("weekly_activity gives the expected values (all weekdays)", test_weekly_activity_values),
    ("weekly_activity returns 13 zeros for no events", test_weekly_activity_has_13_values_and_zeros),
    ("empty weeks appear as 0", test_weekly_activity_empty_weeks_are_zero),
    ("active_days counts 24 days in the sample (all weekdays)", test_active_days_sample),
    ("active_days ignores events older than 90 days", test_active_days_ignores_old_events),
    ("build_summary works with sample data", test_summary_sample),
    ("build_summary works with empty data", test_summary_empty_data),
    ("language_pie returns a Figure", test_language_pie_returns_figure),
    ("weekly_activity_bar returns a Figure with 13 bars", test_weekly_chart_returns_figure_with_13_bars),
    ("all_repos_bar shows every repo including 0 stars", test_all_repos_chart_shows_zero_star_repos),
    ("all_repos_bar uses gold for stars and gray for 0", test_all_repos_chart_star_colors),
    ("all_repos_bar limits to 15 bars with a note", test_all_repos_chart_limits_to_15),
    ("charts handle empty data", test_charts_handle_empty_data),
    ("HTTP 404 becomes UserNotFoundError", test_api_404_is_user_not_found),
    ("HTTP 403 with 0 remaining becomes RateLimitError", test_api_403_with_zero_remaining_is_rate_limit),
    ("HTTP 403 with requests left is a generic error", test_api_403_with_requests_left_is_generic_error),
    ("network failure becomes GitHubAPIError", test_api_network_failure_is_api_error),
    ("successful call returns JSON and rate info", test_api_success_returns_json_and_rate_info),
    ("headers are correct, token only when given", test_api_headers_with_and_without_token),
    ("pagination stops after 3 pages", test_api_pagination_stops_after_three_pages),
    ("pagination stops on a short page", test_api_pagination_stops_on_short_page),
    ("username helpers work", test_username_helpers),
    ("minutes until reset are calculated", test_rate_limit_minutes),
    ("timeline counts every repo once", test_timeline_totals_match_repo_count),
    ("learning_timeline returns a Figure", test_timeline_chart_returns_figure),
    ("reach summary uses profile and repos", test_reach_summary_sample),
    ("reach summary handles empty data", test_reach_summary_empty),
    ("top repos are ordered by stars and limited to 5", test_top_repos_order_and_limit),
    ("top repos handles no repos", test_top_repos_empty),
    ("event types are counted and add up", test_event_type_counts_sample),
    ("unknown event types become Other", test_event_type_counts_groups_unknown_as_other),
    ("event types handle no events", test_event_type_counts_empty),
    ("CSV has the right header and rows", test_repos_to_csv_content),
    ("CSV of no repos has only the header", test_repos_to_csv_empty_has_header_only),
    ("activity_type_bar returns a Figure", test_activity_chart_returns_figure),
    ("report is a PDF with 3 pages", test_report_is_a_pdf_with_pages),
    ("report works with no repos", test_report_works_with_no_repos),
    ("report works with an empty profile", test_report_works_with_empty_profile),
    ("README summary removes markdown, links and badges", test_readme_summary_cleans_markdown),
    ("README summary finds technology keywords", test_readme_summary_finds_keywords),
    ("README keywords match whole words only", test_readme_keywords_need_whole_words),
    ("README summary handles empty and badge-only text", test_readme_summary_empty_or_badges_only),
    ("missing profile README is None, not an error", test_api_profile_readme_not_found_is_none),
    ("profile README is decoded from base64", test_api_profile_readme_is_decoded),
]


def main():
    """Run every check and print PASS or FAIL for each."""
    passed = 0
    failed = 0
    for name, test_function in ALL_TESTS:
        try:
            ok = test_function()
            detail = ""
        except Exception as error:   # a crash counts as a failure
            ok = False
            detail = " (error: " + repr(error) + ")"
        if ok:
            passed += 1
            print("PASS: " + name)
        else:
            failed += 1
            print("FAIL: " + name + detail)
    print("")
    print(str(passed) + " passed, " + str(failed) + " failed, " + str(passed + failed) + " total")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())