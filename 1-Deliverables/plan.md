# Wikipedia Chain Finder - Implementation Plan

## Overview
This plan outlines the step-by-step implementation of a web application that finds the shortest chain of Wikipedia article links connecting two articles using bidirectional iterative deepening search.

---

## Phase 1: Project Setup and Structure

### Objectives
- Create the project directory structure
- Set up Python virtual environment
- Install required dependencies
- Create placeholder files

### Implementation Steps

1. **Create directory structure**
   ```
   project/
   ├── backend/
   │   ├── app.py
   │   ├── search.py
   │   ├── wikipedia_api.py
   │   └── requirements.txt
   ├── frontend/
   │   ├── index.html
   │   ├── style.css
   │   └── script.js
   └── README.md
   ```

2. **Create requirements.txt with dependencies**
   - Flask
   - requests

3. **Set up Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r backend/requirements.txt
   ```

4. **Create placeholder files with basic structure**

### Testing Criteria for Phase 1
- [ ] All directories exist with correct structure
- [ ] Virtual environment activates successfully
- [ ] All dependencies install without errors
- [ ] `python -c "import flask; import requests"` runs without errors

---

## Phase 2: Wikipedia API Integration

### Objectives
- Implement Wikipedia API client
- Handle article validation
- Extract links from articles
- Implement error handling and retries

### Implementation Steps

1. **Create `wikipedia_api.py` with core functions**
   - `validate_article(title)` - Check if article exists, return normalized title
   - `get_article_links(title)` - Fetch all links from an article (namespace 0 only)

2. **Implement API request handling**
   - Base URL: `https://en.wikipedia.org/w/api.php`
   - Query parameters: action, titles, prop, pllimit, redirects, format, plnamespace
   - Handle continuation tokens for pagination (if needed)

3. **Implement retry logic**
   - 2-3 retry attempts with exponential backoff
   - Handle network errors and rate limiting

4. **Implement error handling**
   - Detect missing articles via `missing` flag
   - Handle API response parsing errors
   - Return meaningful error messages

### Testing Criteria for Phase 2
- [ ] `validate_article("Python (programming language)")` returns normalized title
- [ ] `validate_article("Nonexistent Article XYZ123")` returns appropriate error
- [ ] `get_article_links("Python (programming language)")` returns list of article titles
- [ ] All returned links are namespace 0 (no "Wikipedia:", "Category:", etc.)
- [ ] Redirect handling works: `validate_article("Python programming")` resolves correctly
- [ ] Network error retry logic works (can test by temporarily blocking network)
- [ ] API returns maximum 500 links per article

### Manual Test Commands
```python
from wikipedia_api import validate_article, get_article_links

# Test 1: Valid article
print(validate_article("Python (programming language)"))

# Test 2: Invalid article
print(validate_article("ThisArticleDoesNotExist12345"))

# Test 3: Get links
links = get_article_links("Python (programming language)")
print(f"Found {len(links)} links")
print(links[:10])  # Print first 10
```

---

## Phase 3: Search Algorithm Implementation

### Objectives
- Implement forward BFS search
- Implement path reconstruction
- Add timeout enforcement
- Handle edge cases

### Implementation Steps

1. **Create `search.py` with core algorithm**
   - `find_path(start, end, max_depth=4, timeout=60)` - Main entry point

2. **Implement forward BFS search**
   - Initialize frontier with start article
   - Track visited nodes with parent pointers: `{article: parent}`
   - Expand frontier level by level
   - Check if any link reaches the end article

3. **Implement path reconstruction**
   - When end is found, trace back through parent pointers to start
   - Reverse to get path from start to end

4. **Implement constraints**
   - Maximum depth: 4 (max chain of 7 articles)
   - Timeout: 60 seconds hard stop
   - Return appropriate status for each case

5. **Handle edge cases**
   - Start equals end (return single-element path)
   - Start links directly to end (depth 1)
   - No path exists within constraints

### Implementation Note
**Changed from bidirectional to forward-only BFS.** Wikipedia links are directed (one-way), so expanding "backward" from the end article actually follows links *away* from end, not *toward* it. This made path reconstruction invalid. Forward-only BFS always produces valid paths where each article actually links to the next.

### Testing Criteria for Phase 3
- [ ] Same article as start and end returns `[article]`
- [ ] Known connected articles return valid path
- [ ] Path is actually valid (each article links to the next)
- [ ] Search respects max_depth limit
- [ ] Search respects timeout limit
- [ ] Returns failure status when no path found
- [ ] Path reconstruction produces correct order: start → ... → end

### Manual Test Commands
```python
from search import find_path

# Test 1: Same article
result = find_path("Python (programming language)", "Python (programming language)")
print(result)  # Should return path of length 1

# Test 2: Known short path
result = find_path("Python (programming language)", "Programming language")
print(result)  # Should find path

# Test 3: Verify path validity
path = result["path"]
for i in range(len(path) - 1):
    links = get_article_links(path[i])
    assert path[i+1] in links, f"{path[i]} does not link to {path[i+1]}"
print("Path verified!")
```

---

## Phase 4: Flask Backend API

### Objectives
- Create Flask application
- Implement POST /api/search endpoint
- Add request validation
- Implement proper error responses

### Implementation Steps

1. **Create `app.py` with Flask application**
   - Initialize Flask app
   - Configure CORS for frontend access
   - Set up error handlers

2. **Implement `/api/search` endpoint**
   - Accept POST requests with JSON body
   - Extract and validate `start` and `end` parameters
   - Call search algorithm
   - Return appropriate JSON response

3. **Implement request validation**
   - Check for missing parameters
   - Trim whitespace from titles
   - Validate articles exist before searching

4. **Implement response formatting**
   - Success: `{"success": true, "path": [...]}`
   - Failure: `{"success": false, "error": "..."}`
   - Correct HTTP status codes (200, 400, 500)

5. **Add Flask-CORS for cross-origin requests**

### Testing Criteria for Phase 4
- [ ] Server starts without errors on `python app.py`
- [ ] POST /api/search with valid articles returns path
- [ ] POST /api/search with missing parameters returns 400
- [ ] POST /api/search with invalid article returns 400 with descriptive error
- [ ] POST /api/search with no path found returns 200 with success=false
- [ ] Response JSON format matches specification
- [ ] CORS headers present in response

### Manual Test Commands
```bash
# Start server
cd backend && python app.py

# Test 1: Valid search (in another terminal)
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"start": "Python (programming language)", "end": "Programming language"}'

# Test 2: Missing parameters
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"start": "Python"}'

# Test 3: Invalid article
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"start": "NonexistentArticle12345", "end": "Philosophy"}'
```

---

## Phase 5: Frontend Implementation

### Objectives
- Create HTML structure
- Style with CSS
- Implement JavaScript functionality
- Connect to backend API

### Implementation Steps

1. **Create `index.html`**
   - Two text input fields for start and end articles
   - Submit button
   - Loading spinner area
   - Results display area
   - Error message area

2. **Create `style.css`**
   - Clean, centered layout
   - Input field styling
   - Button styling (normal, hover, disabled states)
   - Loading spinner animation
   - Results chain styling with arrows
   - Error message styling (red/warning)
   - Responsive design for mobile

3. **Create `script.js`**
   - Form submission handler
   - Input validation (trim whitespace)
   - Disable button during search
   - Show/hide loading spinner
   - Fetch POST to backend API
   - Display results as clickable links
   - Display error messages
   - Handle network errors

4. **Implement results display**
   - Article chain with arrows: Article1 → Article2 → Article3
   - Each article as clickable link to Wikipedia
   - Chain length display: "Found path in X steps"

### Testing Criteria for Phase 5
- [ ] Page loads without JavaScript errors
- [ ] Both input fields accept text
- [ ] Submit button triggers search
- [ ] Button disables during search
- [ ] Loading spinner appears during search
- [ ] Valid search displays article chain with arrows
- [ ] Articles are clickable links to Wikipedia
- [ ] Chain length is displayed correctly
- [ ] Invalid article shows error message
- [ ] Network error shows appropriate message
- [ ] Empty input fields show validation error
- [ ] Page is usable on mobile viewport

### Manual Test Checklist
1. Open index.html in browser (served via Flask)
2. Enter "Python (programming language)" and "Philosophy"
3. Click Submit
4. Verify loading spinner appears
5. Verify results display with clickable links
6. Click an article link - verify it opens Wikipedia
7. Test with invalid article name
8. Test with empty fields
9. Test on mobile viewport (browser dev tools)

---

## Phase 6: Integration and Final Testing

### Objectives
- Integrate all components
- Serve frontend from Flask
- End-to-end testing
- Edge case testing
- Performance verification

### Implementation Steps

1. **Configure Flask to serve frontend**
   - Serve static files from frontend directory
   - Serve index.html at root route

2. **End-to-end integration**
   - Verify all components work together
   - Test complete user flow

3. **Edge case testing**
   - Test all error scenarios
   - Test boundary conditions

4. **Documentation**
   - Update README.md with setup and usage instructions

### Testing Criteria for Phase 6

#### Functional Tests
- [ ] Application starts with single command
- [ ] Frontend loads at http://localhost:5000
- [ ] Complete search flow works end-to-end
- [ ] All error messages display correctly in UI

#### Edge Case Tests
- [ ] Same article for start and end
- [ ] Articles that are directly linked (1 step)
- [ ] Articles requiring maximum depth
- [ ] Non-existent start article
- [ ] Non-existent end article
- [ ] Both articles non-existent
- [ ] Whitespace in article names (should be trimmed)
- [ ] Special characters in article names
- [ ] Disambiguation pages as inputs

#### Performance Tests
- [ ] Typical search completes in < 30 seconds
- [ ] Timeout triggers correctly at 60 seconds
- [ ] No memory leaks during multiple searches
- [ ] Application remains responsive during search

### Final Test Pairs
| Start | End | Expected Result |
|-------|-----|-----------------|
| "Python (programming language)" | "Philosophy" | Path found |
| "Python (programming language)" | "Programming language" | Short path (likely 1-2 steps) |
| "Albert Einstein" | "Physics" | Path found |
| "NonexistentArticle12345" | "Philosophy" | Error: article not found |
| "Philosophy" | "Philosophy" | Path of length 1 |
| "  Python  " | "Philosophy" | Works (whitespace trimmed) |

---

## Summary

| Phase | Description | Key Deliverable |
|-------|-------------|-----------------|
| 1 | Project Setup | Working development environment |
| 2 | Wikipedia API | Reliable article validation and link extraction |
| 3 | Search Algorithm | Forward BFS with path reconstruction |
| 4 | Flask Backend | REST API endpoint with proper error handling |
| 5 | Frontend | User interface with results display |
| 6 | Integration | Complete working application |

Each phase must pass all its testing criteria before proceeding to the next phase. This ensures incremental progress with verified functionality at each step.
