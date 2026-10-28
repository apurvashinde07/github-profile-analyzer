"""Helpers for calling the official GitHub REST API.

This module only uses the requests library and the public REST API.
There is no scraping, no GraphQL and no login flow.

The optional access token is only used to build the request headers.
It is never printed, logged or written to disk.
"""

import base64
import math
import re
import time
from urllib.parse import quote

import requests

BASE_URL = "https://api.github.com"
TIMEOUT_SECONDS = 15
PER_PAGE = 100
MAX_REPO_PAGES = 3    # 3 pages x 100 = at most 300 repositories
MAX_EVENT_PAGES = 3   # the events feed holds about 300 events at most
MAX_README_CHARS = 20000   # a profile README is cut to this length

# GitHub usernames use letters, digits and hyphens and are at most 39 characters.
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,38}$")


class GitHubAPIError(Exception):
    """Base error for any problem while talking to GitHub."""

    def __init__(self, message, network_problem=False):
        super().__init__(message)
        # True when the request never reached GitHub (no internet, timeout).
        self.network_problem = network_problem


class UserNotFoundError(GitHubAPIError):
    """Raised when GitHub answers with HTTP 404."""

    def __init__(self, message="The GitHub user was not found."):
        super().__init__(message)


class RateLimitError(GitHubAPIError):
    """Raised when the hourly request limit is used up."""

    def __init__(self, reset_time=None):
        super().__init__("GitHub's rate limit has been reached.")
        # Unix time (seconds) when the limit resets, or None if unknown.
        self.reset_time = reset_time

    def minutes_until_reset(self, now=None):
        """Return the whole minutes until the limit resets, or None if unknown."""
        if self.reset_time is None:
            return None
        if now is None:
            now = time.time()
        seconds_left = self.reset_time - now
        return max(1, int(math.ceil(seconds_left / 60.0)))


def clean_username(text):
    """Tidy user input: trim spaces, drop a leading @, accept a profile URL."""
    if text is None:
        return ""
    name = text.strip()
    if "github.com/" in name:
        name = name.rstrip("/").split("/")[-1]
    return name.lstrip("@").strip()


def is_valid_username(name):
    """Return True if the name looks like a possible GitHub username."""
    return bool(name) and USERNAME_PATTERN.match(name) is not None


def _build_headers(token=None):
    """Build the request headers. The token is added only when supplied."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-analyzer",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    return headers


def _to_int(value):
    """Convert a header value to int, or return None if it is missing or odd."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_rate_info(response):
    """Read the rate-limit numbers from the response headers."""
    return {
        "limit": _to_int(response.headers.get("x-ratelimit-limit")),
        "remaining": _to_int(response.headers.get("x-ratelimit-remaining")),
        "reset": _to_int(response.headers.get("x-ratelimit-reset")),
    }


def _request(path, token=None, params=None):
    """Send one GET request and return (json_data, rate_info).

    Raises UserNotFoundError, RateLimitError or GitHubAPIError.
    """
    url = BASE_URL + path
    try:
        response = requests.get(
            url,
            headers=_build_headers(token),
            params=params,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException:
        raise GitHubAPIError("Could not reach GitHub.", network_problem=True) from None

    rate_info = _read_rate_info(response)
    status = response.status_code

    if status == 404:
        raise UserNotFoundError()
    if status == 429 or (status == 403 and rate_info["remaining"] == 0):
        raise RateLimitError(rate_info["reset"])
    if status != 200:
        raise GitHubAPIError("GitHub returned HTTP status " + str(status) + ".")

    try:
        data = response.json()
    except ValueError:
        raise GitHubAPIError("GitHub returned data that could not be read.") from None
    return data, rate_info


def _get_pages(path, token, extra_params, max_pages):
    """Fetch a list endpoint page by page, up to max_pages pages."""
    items = []
    rate_info = {"limit": None, "remaining": None, "reset": None}
    for page_number in range(1, max_pages + 1):
        params = dict(extra_params)
        params["per_page"] = PER_PAGE
        params["page"] = page_number
        data, rate_info = _request(path, token, params)
        if not isinstance(data, list):
            raise GitHubAPIError("GitHub returned unexpected data.")
        items.extend(data)
        if len(data) < PER_PAGE:
            break  # this was the last page
    return items, rate_info


def get_user(username, token=None):
    """GET /users/{username}. Returns (profile_dict, rate_info)."""
    return _request("/users/" + quote(username, safe=""), token)


def get_repos(username, token=None):
    """GET /users/{username}/repos (up to 3 pages). Returns (repo_list, rate_info)."""
    path = "/users/" + quote(username, safe="") + "/repos"
    params = {"type": "owner", "sort": "pushed"}
    return _get_pages(path, token, params, MAX_REPO_PAGES)


def get_events(username, token=None):
    """GET /users/{username}/events/public (up to 3 pages). Returns (event_list, rate_info)."""
    path = "/users/" + quote(username, safe="") + "/events/public"
    return _get_pages(path, token, {}, MAX_EVENT_PAGES)


def get_profile_readme(username, token=None):
    """GET /repos/{username}/{username}/readme (the profile README).

    A profile README lives in a repository named exactly like the user.
    Returns ({"text": ..., "url": ...} or None, rate_info). None means the
    user has no profile README, which is normal and not an error.
    """
    name = quote(username, safe="")
    try:
        data, rate_info = _request("/repos/" + name + "/" + name + "/readme", token)
    except UserNotFoundError:
        return None, None
    if not isinstance(data, dict):
        return None, rate_info
    text = ""
    if data.get("encoding") == "base64" and data.get("content"):
        try:
            raw = base64.b64decode(data["content"])
        except (ValueError, TypeError):
            raw = b""
        text = raw.decode("utf-8", errors="replace")[:MAX_README_CHARS]
    return {"text": text, "url": data.get("html_url")}, rate_info