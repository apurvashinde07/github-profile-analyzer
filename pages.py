"""The Home and About pages of the GitHub Profile Analyzer.

These pages only show fixed text. No data from GitHub is placed inside the
HTML, so nothing from outside can change the page markup.
"""

import streamlit as st

# Fill these in to show your details on the About page. Empty values are hidden.
DEVELOPER_NAME = ""
COLLEGE_NAME = ""
GUIDE_NAME = ""

PROJECT_NAME = "GitHub Profile Analyzer"
DOMAIN = "Data Analysis & Visualization (API Integration)"
SUBDOMAIN = "Developer Profile Analytics"

# Settings that live in the sidebar of the Analyzer page.
SETTING_KEYS = ("username", "token", "include_forks", "demo_mode")

SAMPLE_USERNAMES = ("octocat", "torvalds", "gaearon")

FEATURE_CARDS = [
    ("\U0001F464", "Profile summary",
     "Name, bio, repositories, active days and the year the account was created."),
    ("\U0001F4DD", "Profile README",
     "A short summary of the profile README: key lines and the technologies it mentions."),
    ("\U0001F4E3", "Reach",
     "Followers, following, total stars and forks, and the top repositories."),
    ("\U0001F9E9", "Language mix",
     "A pie chart of the primary language of every repository."),
    ("\U0001F4E6", "All repositories",
     "Every repository in one chart and a full table, even those with zero stars."),
    ("\U0001F4C8", "Weekly activity",
     "The last 13 weeks, including the weeks with no activity."),
    ("\U0001F4C4", "Reports",
     "Download the repository table as CSV or the whole profile as a PDF report."),
]

STEPS = [
    "Open the Analyzer page and type a GitHub username.",
    "The app asks the official GitHub REST API for the profile, repositories and recent activity.",
    "The data is analysed with pandas and drawn as charts with matplotlib.",
    "Read the summary, or download the CSV and PDF report.",
]

USERS = [
    ("Recruiters and HR", "Get a quick picture of a candidate's languages and consistency."),
    ("Teachers and mentors", "See whether a student works regularly and which languages they use."),
    ("Students and freshers", "Check their own profile and find what is missing."),
    ("Team leads and organizers", "Compare language mix and activity when forming a team."),
    ("Open-source community", "See how much reach and collaboration an account has."),
]

TECHNOLOGIES = [
    ("requests", "Calls the official GitHub REST API"),
    ("pandas", "Cleans the data and calculates the numbers"),
    ("matplotlib", "Draws the charts and builds the PDF report"),
    ("streamlit", "The web interface"),
]

LIMITATIONS = [
    "This tool measures public activity, language usage and consistency. It does not measure programming skill.",
    "GitHub does not share profile views, so reach is shown with followers, stars and forks.",
    "The activity feed covers only about the last 90 days (roughly 300 events).",
    "Private repositories are invisible.",
    "The profile README is found only if the user has a repository with the same name as the username.",
    "Only the primary language of each repository is counted.",
    "GitHub allows 60 requests per hour without a token and 5,000 with one.",
]


def keep_settings():
    """Keep the Analyzer settings alive while another page is open.

    Streamlit forgets the value of a widget that is not drawn on the page, so
    each saved value is written back to itself.
    """
    for key in SETTING_KEYS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def _go_to_analyzer():
    """Button callback: open the Analyzer page."""
    st.session_state["page"] = "Analyzer"


def _try_demo():
    """Button callback: open the Analyzer page in Demo mode."""
    st.session_state["demo_mode"] = True
    _go_to_analyzer()


def _try_username(name):
    """Button callback: analyse a sample username."""
    st.session_state["username"] = name
    st.session_state["target"] = name
    st.session_state["demo_mode"] = False
    _go_to_analyzer()


def _card(icon, title, text):
    """Show one small card. All texts are fixed strings from this file."""
    st.markdown(
        '<div class="card"><div class="icon">' + icon + "</div><h4>" + title
        + "</h4><p>" + text + "</p></div>",
        unsafe_allow_html=True,
    )


def show_home():
    """Show the Home page."""
    st.subheader("\u2728 What it does")
    st.write(
        "Judging a developer's GitHub profile usually means opening repositories "
        "one by one. Enter a username here and get one combined, data-driven "
        "picture of that person's public profile."
    )

    for start in range(0, len(FEATURE_CARDS), 3):
        columns = st.columns(3)
        for column, (icon, title, text) in zip(columns, FEATURE_CARDS[start:start + 3]):
            with column:
                _card(icon, title, text)

    st.subheader("\U0001F6E0\uFE0F How it works")
    for number, step in enumerate(STEPS, start=1):
        st.write(str(number) + ". " + step)

    st.subheader("\U0001F680 Try it now")
    st.button("\U0001F50D Start analyzing", on_click=_go_to_analyzer, key="home_start")
    st.write("Or pick an example. Demo mode needs no internet.")
    columns = st.columns(1 + len(SAMPLE_USERNAMES))
    columns[0].button("\U0001F9EA Demo mode", on_click=_try_demo, key="home_demo")
    for column, name in zip(columns[1:], SAMPLE_USERNAMES):
        column.button(name, on_click=_try_username, args=(name,), key="home_user_" + name)
    st.caption(
        "Each live analysis uses about 4 to 8 of GitHub's 60 free requests per hour."
    )


def show_about():
    """Show the About page."""
    st.subheader("\U0001F4CB Project details")
    details = [("Project", PROJECT_NAME), ("Domain", DOMAIN), ("Subdomain", SUBDOMAIN)]
    if DEVELOPER_NAME:
        details.append(("Developer", DEVELOPER_NAME))
    if COLLEGE_NAME:
        details.append(("College", COLLEGE_NAME))
    if GUIDE_NAME:
        details.append(("Guide", GUIDE_NAME))
    for label, value in details:
        st.write("**" + label + ":** " + value)

    st.subheader("\U0001F9E0 The problem it solves")
    st.write(
        "Judging a developer's public GitHub profile (interests, language mix and "
        "consistency) means opening repositories one by one. That is slow and never "
        "gives a combined picture. This tool turns a username into an automatic, "
        "data-driven summary."
    )

    st.subheader("\U0001F465 Who is it for?")
    for who, why in USERS:
        st.write("- **" + who + ":** " + why)

    st.subheader("\U0001F9F0 Technologies")
    for name, use in TECHNOLOGIES:
        st.write("- **" + name + ":** " + use)

    st.subheader("\U0001F50C Data sources")
    st.write(
        "Only the official GitHub REST API is used (no scraping): the user "
        "profile, the list of repositories, the public events feed and the profile README."
    )

    st.subheader("\u26A0\uFE0F Limitations")
    for line in LIMITATIONS:
        st.write("- " + line)