"""Wikipedia API interaction module."""

import time
import requests

BASE_URL = "https://en.wikipedia.org/w/api.php"
MAX_RETRIES = 3
RETRY_DELAY = 1  # Initial delay in seconds
USER_AGENT = "WikipediaChainFinder/1.0 (Educational Project)"


class WikipediaAPIError(Exception):
    """Custom exception for Wikipedia API errors."""
    pass


class ArticleNotFoundError(WikipediaAPIError):
    """Raised when an article does not exist."""
    pass


def _make_request(params, retries=MAX_RETRIES):
    """Make a request to the Wikipedia API with retry logic.

    Args:
        params: Dictionary of query parameters
        retries: Number of retry attempts remaining

    Returns:
        JSON response from the API

    Raises:
        WikipediaAPIError: If the request fails after all retries
    """
    params["format"] = "json"

    headers = {"User-Agent": USER_AGENT}

    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                # Exponential backoff
                delay = RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                raise WikipediaAPIError(f"Network error after {retries} attempts: {e}")

    raise WikipediaAPIError("Request failed")


def validate_article(title):
    """Check if an article exists and return its normalized title.

    Args:
        title: The article title to validate

    Returns:
        The normalized article title

    Raises:
        ArticleNotFoundError: If the article does not exist
        WikipediaAPIError: If there's an API error
    """
    params = {
        "action": "query",
        "titles": title,
        "redirects": 1,
    }

    data = _make_request(params)

    pages = data.get("query", {}).get("pages", {})

    # No pages returned means article doesn't exist
    if not pages:
        raise ArticleNotFoundError(f"Article '{title}' not found. Please check the spelling.")

    for page_id, page_info in pages.items():
        if page_id == "-1" or "missing" in page_info:
            raise ArticleNotFoundError(f"Article '{title}' not found. Please check the spelling.")

        # Return the normalized/canonical title
        return page_info.get("title", title)

    raise WikipediaAPIError("Unexpected API response format")


def get_article_links(title):
    """Fetch all links from an article (namespace 0 only).

    Args:
        title: The article title to get links from

    Returns:
        List of article titles that this article links to

    Raises:
        ArticleNotFoundError: If the article does not exist
        WikipediaAPIError: If there's an API error
    """
    links = []
    continue_token = None

    while True:
        params = {
            "action": "query",
            "titles": title,
            "prop": "links",
            "pllimit": "max",
            "plnamespace": 0,
            "redirects": 1,
        }

        if continue_token:
            params["plcontinue"] = continue_token

        data = _make_request(params)

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_info in pages.items():
            if page_id == "-1" or "missing" in page_info:
                raise ArticleNotFoundError(f"Article '{title}' not found. Please check the spelling.")

            page_links = page_info.get("links", [])
            for link in page_links:
                # Only include namespace 0 (main articles)
                if link.get("ns", -1) == 0:
                    links.append(link["title"])

        # Check for continuation
        if "continue" in data:
            continue_token = data["continue"].get("plcontinue")
        else:
            break

        # Safety limit: stop after collecting 500 links
        if len(links) >= 500:
            break

    return links


def get_article_backlinks(title):
    """Fetch articles that link TO a given article (namespace 0 only).

    Args:
        title: The article title to get backlinks for

    Returns:
        List of article titles that link to this article

    Raises:
        WikipediaAPIError: If there's an API error
    """
    backlinks = []
    continue_token = None

    while True:
        params = {
            "action": "query",
            "list": "backlinks",
            "bltitle": title,
            "bllimit": "max",
            "blnamespace": 0,
        }

        if continue_token:
            params["blcontinue"] = continue_token

        data = _make_request(params)

        bl_list = data.get("query", {}).get("backlinks", [])
        for bl in bl_list:
            if bl.get("ns", -1) == 0:
                backlinks.append(bl["title"])

        # Check for continuation
        if "continue" in data:
            continue_token = data["continue"].get("blcontinue")
        else:
            break

        # Safety limit: stop after collecting 500 backlinks
        if len(backlinks) >= 500:
            break

    return backlinks
