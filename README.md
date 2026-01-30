

# Wikipedia Chain Finder

A web application that finds the shortest chain of Wikipedia article links connecting two articles.

## Features

- Search for paths between any two Wikipedia articles
- Visual display of the article chain with clickable links
- Handles edge cases (same article, non-existent articles, timeouts)
- Responsive design for mobile and desktop

## Tech Stack

- **Frontend**: HTML, CSS, vanilla JavaScript
- **Backend**: Python Flask
- **API**: Wikipedia MediaWiki Action API

## Project Structure

```
project/
├── backend/
│   ├── app.py              # Flask application and API endpoint
│   ├── search.py           # BFS search algorithm
│   ├── wikipedia_api.py    # Wikipedia API interaction
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── style.css           # Styling
│   └── script.js           # Frontend JavaScript
├── plan.md                 # Implementation plan
└── README.md               # This file
```

## Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m backend.app
   ```

4. **Open in browser**
   ```
   http://localhost:5000
   ```

## API

### POST /api/search

Find a path between two Wikipedia articles.

**Request:**
```json
{
  "start": "Article Title 1",
  "end": "Article Title 2"
}
```

**Response (success):**
```json
{
  "success": true,
  "path": ["Article1", "Article2", "Article3"]
}
```

**Response (failure):**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Constraints

- Maximum search depth: 4 levels
- Maximum path length: 7 articles
- Search timeout: 60 seconds
- Links per article: up to 500

## Examples

| Start | End | Typical Result |
|-------|-----|----------------|
| Python (programming language) | Programming language | 2 articles (direct link) |
| Albert Einstein | Physics | 3 articles |
| Philosophy | Philosophy | 1 article (same) |
