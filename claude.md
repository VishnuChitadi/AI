Core Requirements

Web app that finds Wikipedia article chains connecting start article to end article
Frontend:

HTML/CSS/vanilla JavaScript (no frameworks)
Two input boxes for start/end article titles
Submit button, loading indicator, results display area


Backend:

Python Flask
API endpoint to receive start/end from frontend
Return the path or error messages


Wikipedia API:

Use Wikimedia API to fetch Wikipedia pages dynamically
Parse content to extract links from each page
Only follow main article namespace links (no admin pages, discussions, images, etc.)
Note: Dynamic fetching is slower than pre-computed database but necessary for this project


Algorithm:

Bidirectional iterative deepening search
Two searches: one from start, one from end
They meet in the middle
Requires ability to work backwards from goal


Search constraints:

Max depth: 4 (produces chain of max 7 articles)
Cut off and return failure if limit exceeded
60-second timeout


Performance:

Limit to 500 links per page
No caching in v1
Single-threaded execution


Other:

Handle errors (article not found, no path, network issues)
Display results as clickable Wikipedia links
Make other reasonable implementation choices as needed