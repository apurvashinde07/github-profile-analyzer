"""Streamlit web interface for the GitHub Profile Analyzer.

Run with:  py -m streamlit run app.py
"""

import re

import pandas as pd
import streamlit as st

import analysis
import branding
import charts
import github_api
import pages
import report
import sample_data
from github_api import GitHubAPIError, RateLimitError, UserNotFoundError
from styles import PAGE_STYLE

DISCLAIMER = (
    "This tool measures public activity, language usage and consistency, "
    "not programming skill."
)
EVENTS_NOTE = (
    "Activity comes from GitHub's public events feed, which only covers about "
    "the last 90 days (roughly 300 events at most)."
)

st.set_page_config(
    page_title="GitHub Profile Analyzer",
    page_icon=branding.page_icon(),
    layout="wide",
)

@st.cache_data(ttl=600, show_spinner="Fetching data from GitHub...")
def fetch_github_data(username, _token):
    """Fetch profile, repos, events and README. Cached for 10 minutes per username.

    The leading underscore on _token tells Streamlit not to use it in the
    cache key, so the token is never part of what gets stored.
    """
    profile, _ = github_api.get_user(username, _token)
    repos, _ = github_api.get_repos(username, _token)
    events, rate_info = github_api.get_events(username, _token)
    # The profile README is optional. Any problem here must not break the page.
    try:
        readme, readme_rate = github_api.get_profile_readme(username, _token)
    except GitHubAPIError:
        readme, readme_rate = None, None
    if readme_rate and readme_rate.get("remaining") is not None:
        rate_info = readme_rate
    return {"user": profile, "repos": repos, "events": events,
            "readme": readme, "rate": rate_info}


def draw_sidebar():
    """Draw the sidebar widgets and return what the user chose."""
    st.sidebar.header("\u2699\ufe0f Settings")
    username = st.sidebar.text_input(
        "GitHub username", key="username", placeholder="e.g. octocat"
    )
    token = st.sidebar.text_input(
        "GitHub token (optional)",
        type="password",
        key="token",
        help=(
            "Optional. Raises the request limit from 60 to 5,000 per hour. "
            "No scopes are needed for public data."
        ),
    )
    include_forks = st.sidebar.checkbox("Include forked repos", value=False, key="include_forks")
    demo_mode = st.sidebar.checkbox("Demo mode (sample data)", value=False, key="demo_mode")
    analyze_clicked = st.sidebar.button("Analyze", key="analyze")
    st.sidebar.caption(DISCLAIMER)
    return {
        "username": username,
        "token": token.strip() if token else None,
        "include_forks": include_forks,
        "demo_mode": demo_mode,
        "analyze_clicked": analyze_clicked,
    }


def load_data(demo_mode, target, token):
    """Return the data dictionary, or None after showing a friendly error."""
    if demo_mode:
        # Demo mode never touches the network.
        return {
            "user": sample_data.get_sample_profile(),
            "repos": sample_data.get_sample_repos(),
            "events": sample_data.get_sample_events(),
            "readme": sample_data.get_sample_readme(),
            "rate": None,
        }

    try:
        return fetch_github_data(target.lower(), token or None)
    except UserNotFoundError:
        st.error("User '" + target + "' was not found on GitHub.")
    except RateLimitError as error:
        minutes = error.minutes_until_reset()
        if minutes is None:
            wait_text = "within an hour"
        elif minutes == 1:
            wait_text = "in about 1 minute"
        else:
            wait_text = "in about " + str(minutes) + " minutes"
        st.error(
            "GitHub's rate limit has been reached. It resets " + wait_text
            + ". Add an optional token in the sidebar, or switch on Demo mode."
        )
    except GitHubAPIError as error:
        if error.network_problem:
            st.error("Could not reach GitHub. Please check your internet connection.")
        else:
            st.error("GitHub sent an unexpected answer (" + str(error) + "). Please try again later.")
    except Exception:
        st.error("Something unexpected went wrong while loading the data. Please try again.")
    return None


def show_profile_card(profile):
    """Show avatar, name, login, bio and a link to the profile."""
    login = profile.get("login") or ""
    name = profile.get("name") or login
    avatar_column, text_column = st.columns([1, 6])
    with avatar_column:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=100)
    with text_column:
        st.subheader(name)
        st.caption("@" + login)
        bio = profile.get("bio")
        if bio:
            st.write(bio.replace("$", "\\$"))
        if profile.get("html_url"):
            st.markdown("[View profile on GitHub](" + profile["html_url"] + ")")


def _escape_markdown(text):
    """Put a backslash before every markdown character so the text shows as plain text."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~$<&])", r"\\\1", text)


def show_readme_summary(readme):
    """Show a short summary of the user's profile README, if there is one."""
    st.subheader("\U0001F4DD Profile README")
    text = (readme or {}).get("text") or ""
    if not text.strip():
        st.info(
            "This user has no profile README. A profile README is a file in a "
            "repository that has exactly the same name as the username."
        )
        return

    summary = analysis.summarize_readme(text)
    if not summary["lines"]:
        st.info("The profile README has no readable text (it may only contain images and badges).")
    for line in summary["lines"]:
        st.markdown("- " + _escape_markdown(line))
    if summary["keywords"]:
        chips = "".join('<span class="chip">' + word + "</span>" for word in summary["keywords"])
        # The words come from a fixed list in analysis.py, not from GitHub.
        st.markdown("**Technologies mentioned:** " + chips, unsafe_allow_html=True)

    note = ("Short summary: the first lines of the README without images, links and "
            "badges. No AI is used. The README has " + str(summary["words"]) + " words.")
    st.caption(note)
    url = readme.get("url") or ""
    if url.startswith("https://github.com/"):
        st.markdown("[Open the full README on GitHub](" + url + ")")


def show_metrics(profile, df, active):
    """Show the row of metric tiles (followers and stars are in the Reach section)."""
    columns = st.columns(3)
    columns[0].metric("\U0001F4E6 Repos", len(df))
    columns[1].metric("\U0001F525 Active days (last 90)", active)
    columns[2].metric("\U0001F4C5 Member since", analysis.account_year(profile))


def build_table(df):
    """Build the display table of all repos, newest push first."""
    ordered = df.sort_values("last_pushed", ascending=False)
    return pd.DataFrame({
        "Name": ordered["name"],
        "Language": ordered["language"].fillna("(No language)"),
        "Stars": ordered["stars"],
        "Forks": ordered["forks"],
        "Size (KB)": ordered["size_kb"],
        "Last pushed": ordered["last_pushed"].dt.strftime("%Y-%m-%d").fillna("-"),
    })


def show_reach(profile, df):
    """Show the Reach section: public popularity numbers and top repos."""
    st.subheader("\U0001F4CA Reach")
    reach = analysis.reach_summary(profile, df)
    columns = st.columns(4)
    columns[0].metric("\U0001F465 Followers", reach["followers"])
    columns[1].metric("\U0001F91D Following", reach["following"])
    columns[2].metric("\u2B50 Total stars", reach["stars"])
    columns[3].metric("\U0001F374 Total forks", reach["forks"])
    st.caption(
        "GitHub does not share how many people viewed a profile, so reach is "
        "shown with followers, stars and forks. Stars and forks are added up "
        "over the repositories listed below."
    )
    top = analysis.top_repos(df)
    if top.empty:
        return
    st.markdown("**\U0001F3C6 Top repositories (most stars first)**")
    table = pd.DataFrame({
        "Name": top["name"],
        "Language": top["language"].fillna("(No language)"),
        "Stars": top["stars"],
        "Forks": top["forks"],
    })
    st.dataframe(table, hide_index=True)


def show_overview(df, weekly, active):
    """Show charts, summary and the table of all repos."""
    left, right = st.columns(2)
    with left:
        if df.empty:
            st.info("This user has no public repositories.")
        else:
            st.pyplot(charts.language_pie(analysis.language_counts(df)))
    with right:
        st.pyplot(charts.weekly_activity_bar(weekly))
        if active == 0:
            st.info("No public activity in the last 90 days.")
        st.caption(EVENTS_NOTE)

    if not df.empty:
        st.pyplot(charts.all_repos_bar(df))

    st.markdown("**Summary:** " + analysis.build_summary(df, weekly, active))

    if not df.empty:
        st.subheader("\U0001F4C1 All repositories")
        st.dataframe(build_table(df), hide_index=True)
        st.download_button(
            "\u2B07\ufe0f Download repositories as CSV",
            data=analysis.repos_to_csv(df),
            file_name="repositories.csv",
            mime="text/csv",
        )

        st.subheader("\U0001F552 Learning timeline")
        timeline = analysis.repos_per_year_by_language(df)
        st.pyplot(charts.learning_timeline(timeline))


@st.cache_data(max_entries=5, show_spinner=False)
def make_report(profile, df, weekly, active, summary):
    """Build the PDF once and reuse it, because building takes about 2 seconds."""
    return report.build_pdf_report(profile, df, weekly, active, summary)


def show_report_download(profile, df, weekly, active):
    """Show a button that downloads the whole profile summary as a PDF."""
    st.subheader("\U0001F4C4 Report")
    summary = analysis.build_summary(df, weekly, active)
    pdf_bytes = make_report(profile, df, weekly, active, summary)
    login = profile.get("login") or "profile"
    st.download_button(
        "\u2B07\ufe0f Download profile report (PDF)",
        data=pdf_bytes,
        file_name="github-report-" + login + ".pdf",
        mime="application/pdf",
    )


def show_footer(rate, demo_mode):
    """Show the remaining API requests and the disclaimer."""
    if demo_mode:
        st.caption("Demo mode: no requests were made to GitHub.")
    elif rate and rate.get("remaining") is not None:
        text = "GitHub API requests remaining this hour: " + str(rate["remaining"])
        if rate.get("limit") is not None:
            text += " of " + str(rate["limit"])
        st.caption(text + " (as of the last request).")
    st.caption(DISCLAIMER)


def show_dashboard(data, include_forks, demo_mode):
    """Show everything for one analysed profile."""
    profile = data["user"]
    df = analysis.repos_to_dataframe(data["repos"], include_forks)
    weekly = analysis.weekly_activity(data["events"])
    active = analysis.active_days(data["events"])

    show_profile_card(profile)
    show_readme_summary(data.get("readme"))
    show_metrics(profile, df, active)
    show_reach(profile, df)
    show_overview(df, weekly, active)
    show_report_download(profile, df, weekly, active)
    show_footer(data["rate"], demo_mode)


PAGES = ["Home", "Analyzer", "About"]
PAGE_ICONS = {"Home": "\U0001F3E0", "Analyzer": "\U0001F50D", "About": "\u2139\ufe0f"}


def draw_navigation():
    """Draw the logo and the page selector at the top of the sidebar."""
    st.sidebar.markdown(
        '<div class="side-brand">' + branding.logo_html(46)
        + "<div><b>Profile Analyzer</b><br><small>Public GitHub insights</small></div></div>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="nav-title">Go to</div>', unsafe_allow_html=True)
    st.session_state.setdefault("page", "Home")
    st.sidebar.radio(
        "Go to",
        PAGES,
        key="page",
        format_func=lambda name: PAGE_ICONS[name] + "  " + name,
        label_visibility="collapsed",
    )
    return st.session_state["page"]


def run_analyzer():
    """Show the Analyzer page: sidebar settings, then the result of the analysis."""
    options = draw_sidebar()

    if options["demo_mode"]:
        st.warning("SAMPLE DATA - not a real person")
        data = load_data(True, "", None)
        show_dashboard(data, options["include_forks"], True)
        return

    if options["analyze_clicked"]:
        st.session_state["target"] = github_api.clean_username(options["username"])
    target = st.session_state.get("target")

    if target is None:
        st.info(
            "Enter a GitHub username in the sidebar and press Analyze, "
            "or switch on Demo mode to see sample data."
        )
        return
    if target == "":
        st.warning("Please enter a GitHub username in the sidebar.")
        return
    if not github_api.is_valid_username(target):
        st.error("'" + target + "' is not a valid GitHub username.")
        return

    data = load_data(False, target, options["token"])
    if data is None:
        return
    show_dashboard(data, options["include_forks"], False)


def main():
    """Show the header, then the page chosen in the sidebar."""
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero">' + branding.logo_html(76)
        + "<div><h1>GitHub Profile Analyzer</h1>"
        "<p>Enter a GitHub username to get a data-driven summary of that "
        "person's public profile.</p>"
        '<span class="chip">Official GitHub REST API</span>'
        '<span class="chip">No scraping</span>'
        '<span class="chip">Light and dark theme</span>'
        '<span class="chip">PDF and CSV reports</span></div></div>',
        unsafe_allow_html=True,
    )
    page = draw_navigation()

    if page == "Home":
        pages.keep_settings()
        pages.show_home()
    elif page == "About":
        pages.keep_settings()
        pages.show_about()
    else:
        run_analyzer()


main()