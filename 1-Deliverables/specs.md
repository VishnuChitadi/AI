Wikipedia Chain Finder - Project Specification
Project Overview
Create a web application that finds the shortest chain of Wikipedia article links connecting two articles using bidirectional iterative deepening search.
Technical Stack

Frontend: HTML, CSS, vanilla JavaScript
Backend: Python Flask
External API: Wikipedia MediaWiki Action API

System Architecture
Frontend Components
User Interface:

Two text input fields for start and end article titles
Submit button to initiate search
Loading spinner with "Searching..." status text
Results display area showing the article chain
Error message display area

Input Handling:

Trim whitespace from article titles before submission
Disable submit button while search is in progress
Send POST request to Flask backend API

Results Display:

Show article chain with arrows: Article1 → Article2 → Article3
Display each article as a clickable link to Wikipedia
Show chain length: "Found path in X steps"
Display appropriate error messages when search fails

Backend Components
Flask API Endpoint:
POST /api/search
Request Format:
json{
  "start": "Article Title 1",
  "end": "Article Title 2"
}
Response Format (Success):
json{
  "success": true,
  "path": ["Article1", "Article2", "Article3", "Article4"]
}
Response Format (Failure):
json{
  "success": false,
  "error": "Error message description"
}
```

**HTTP Status Codes:**
- 200: Valid search completed (whether path found or not)
- 400: Bad request (missing parameters, invalid input)
- 500: Server error (API failures, unexpected errors)

## Search Algorithm Specification

### Bidirectional Iterative Deepening Search

**Algorithm Structure:**
1. Initialize two search frontiers: forward (from start) and backward (from end)
2. For each depth d from 0 to max_depth (4):
   - Expand forward search to depth d
   - Expand backward search to depth d
   - Check for intersection between visited sets
   - If intersection found, reconstruct and return path
   - If no intersection, increment d and continue
3. If max_depth reached without finding path, return failure

**Data Structures:**
- `forward_visited = {article_title: parent_article}` - tracks forward search path
- `backward_visited = {article_title: parent_article}` - tracks backward search path
- Frontier queues for BFS-style expansion at each depth level

**Search Style:**
- BFS-style iterative deepening: explore ALL nodes at depth d before moving to d+1
- Check for intersection after completing each depth level in both directions

**Path Reconstruction:**
1. When article appears in both `forward_visited` and `backward_visited`, that's the meeting point
2. Trace backwards from meeting point through `forward_visited` to get start → meeting path
3. Trace backwards from meeting point through `backward_visited` to get end → meeting path
4. Reverse the backward path
5. Concatenate: start → meeting → end

**Search Constraints:**
- Maximum depth: 4 (resulting in maximum chain of 7 articles)
- Timeout: 60 seconds for entire search
- Return failure if either constraint exceeded

## Wikipedia API Integration

**API Endpoint:**
`https://en.wikipedia.org/w/api.php`

**Query Parameters:**
- `action=query`
- `titles=<article_title>`
- `prop=links`
- `pllimit=500` (or max)
- `redirects=1` (automatically follow redirects)
- `format=json`
- `plnamespace=0` (only main article namespace)

**Link Extraction:**
- Only include links with namespace 0 (`ns=0`)
- This filters out Wikipedia:, Help:, Category:, File:, Template:, User:, Talk:, etc.
- Limit to 500 links per page (API default maximum)
- Handle continuation tokens if needed (though 500 limit should suffice)

**Article Validation:**
- Check for `missing` flag in API response to detect non-existent articles
- Let API handle title normalization (capitalization, underscores/spaces)
- Redirects handled automatically with `redirects=1` parameter

**Error Handling:**
- Implement 2-3 retry attempts with exponential backoff for network errors
- Catch and handle API rate limiting
- Return appropriate error messages for timeout or connection failures

## Error Handling

**Article Not Found:**
- Message: "Article '[title]' not found. Please check the spelling."
- HTTP Status: 400

**No Path Found:**
- Message: "No path found within 7 articles. Try different start/end points."
- HTTP Status: 200 (this is a valid search result)

**Search Timeout:**
- Message: "Search timeout - no path found within 60 seconds."
- HTTP Status: 200

**Network/API Errors:**
- Message: "Unable to complete search due to network error. Please try again."
- HTTP Status: 500

**Invalid Request:**
- Message: "Please provide both start and end article titles."
- HTTP Status: 400

## Performance Considerations

- **Single-threaded execution:** No parallel processing required for v1
- **No caching:** Results are not cached in first version
- **Link limit:** Maximum 500 links extracted per article
- **Timeout enforcement:** Hard stop at 60 seconds
- **Memory management:** Track only visited nodes, don't store full article content

## Implementation Notes

**Not Required:**
- Multi-threading or async processing
- Database or persistent storage
- User authentication or session management
- Search history or result caching
- Advanced error recovery or logging

**Reasonable Assumptions:**
- Network connectivity to Wikipedia API is generally reliable
- Users will input valid Wikipedia article titles
- 60-second timeout is sufficient for most searches
- 500 links per article provides adequate coverage
- Disambiguation pages can be treated as regular articles

## File Structure Suggestion
```
project/
├── backend/
│   ├── app.py              # Flask application and API endpoint
│   ├── search.py           # Bidirectional search algorithm
│   ├── wikipedia_api.py    # Wikipedia API interaction
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── style.css           # Styling
│   └── script.js           # Frontend JavaScript
└── README.md               # Project documentation
Testing Recommendations
Test Cases:

Valid article pairs with known short paths
Non-existent article titles
Article pairs with no connection within depth limit
Disambiguation pages as start/end points
Articles with very common/uncommon link structures
Timeout scenarios (distant article pairs)

Example Test Pairs:

"Python (programming language)" → "Philosophy" (should find path)
"Nonexistent Article" → "Philosophy" (should error)
Very obscure article → another very obscure article (may timeout or fail)