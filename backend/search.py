"""Search algorithm for finding Wikipedia article paths."""

import time

from wikipedia_api import get_article_links, get_article_backlinks, validate_article, ArticleNotFoundError, WikipediaAPIError


def find_path(start, end, max_depth=4, timeout=60):
    """Find the shortest path between two Wikipedia articles.

    Uses bidirectional BFS to find the shortest chain of links connecting two articles.
    Searches from both start and end simultaneously for better performance.

    Args:
        start: Starting article title
        end: Target article title
        max_depth: Maximum search depth (default 4)
        timeout: Maximum search time in seconds (default 60)

    Returns:
        dict with keys:
            - success: bool indicating if path was found
            - path: list of article titles from start to end (if found)
            - error: error message (if not found)
    """
    start_time = time.time()

    # Validate and normalize article titles
    try:
        start = validate_article(start)
        end = validate_article(end)
    except ArticleNotFoundError as e:
        return {"success": False, "error": str(e)}
    except WikipediaAPIError as e:
        return {"success": False, "error": "Unable to complete search due to network error. Please try again."}

    # Edge case: start equals end
    if start == end:
        return {"success": True, "path": [start]}

    def check_timeout():
        return time.time() - start_time > timeout

    def build_path(forward_parent, backward_parent, meeting_point):
        """Build complete path by combining forward and backward paths."""
        # Build forward path: start -> meeting_point
        forward_path = []
        current = meeting_point
        while current is not None:
            forward_path.append(current)
            current = forward_parent.get(current)
        forward_path.reverse()

        # Build backward path: meeting_point -> end
        backward_path = []
        current = backward_parent.get(meeting_point)
        while current is not None:
            backward_path.append(current)
            current = backward_parent.get(current)

        return forward_path + backward_path

    # Bidirectional BFS
    # forward_parent[article] = the article that links to this one (from start)
    # backward_parent[article] = the article this links to (toward end)
    forward_parent = {start: None}
    backward_parent = {end: None}
    forward_frontier = [start]
    backward_frontier = [end]

    for depth in range(max_depth + 1):
        if check_timeout():
            return {
                "success": False,
                "error": "Search timeout - no path found within 60 seconds."
            }

        if not forward_frontier and not backward_frontier:
            break

        # Expand the smaller frontier for efficiency
        if forward_frontier and (not backward_frontier or len(forward_frontier) <= len(backward_frontier)):
            # Expand forward frontier
            next_frontier = []

            for current in forward_frontier:
                if check_timeout():
                    return {
                        "success": False,
                        "error": "Search timeout - no path found within 60 seconds."
                    }

                try:
                    links = get_article_links(current)
                except (ArticleNotFoundError, WikipediaAPIError):
                    continue

                for link in links:
                    # Check if we've found an intersection with backward search
                    if link in backward_parent:
                        forward_parent[link] = current
                        return {"success": True, "path": build_path(forward_parent, backward_parent, link)}

                    if link not in forward_parent:
                        forward_parent[link] = current
                        next_frontier.append(link)

            forward_frontier = next_frontier

        else:
            # Expand backward frontier
            next_frontier = []

            for current in backward_frontier:
                if check_timeout():
                    return {
                        "success": False,
                        "error": "Search timeout - no path found within 60 seconds."
                    }

                try:
                    backlinks = get_article_backlinks(current)
                except WikipediaAPIError:
                    continue

                for link in backlinks:
                    # Check if we've found an intersection with forward search
                    if link in forward_parent:
                        backward_parent[link] = current
                        return {"success": True, "path": build_path(forward_parent, backward_parent, link)}

                    if link not in backward_parent:
                        backward_parent[link] = current
                        next_frontier.append(link)

            backward_frontier = next_frontier

    # Max depth reached without finding path
    return {
        "success": False,
        "error": "No path found within 7 articles. Try different start/end points."
    }
