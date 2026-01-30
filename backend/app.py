"""Flask application and API endpoint."""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from search import find_path
from wikipedia_api import ArticleNotFoundError, WikipediaAPIError

# Get the frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS)."""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route('/api/search', methods=['POST'])
def search():
    """Search for a path between two Wikipedia articles.

    Request JSON:
        {
            "start": "Article Title 1",
            "end": "Article Title 2"
        }

    Response JSON (success):
        {
            "success": true,
            "path": ["Article1", "Article2", "Article3"]
        }

    Response JSON (failure):
        {
            "success": false,
            "error": "Error message description"
        }
    """
    # Check for JSON body
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Request must be JSON"
        }), 400

    data = request.get_json()

    # Validate required parameters
    start = data.get('start')
    end = data.get('end')

    if not start or not end:
        return jsonify({
            "success": False,
            "error": "Please provide both start and end article titles."
        }), 400

    # Trim whitespace
    start = start.strip()
    end = end.strip()

    if not start or not end:
        return jsonify({
            "success": False,
            "error": "Please provide both start and end article titles."
        }), 400

    # Perform search
    try:
        result = find_path(start, end)

        if result["success"]:
            return jsonify(result), 200
        else:
            # Check if it's an article not found error (400) or no path found (200)
            error_msg = result.get("error", "")
            if "not found" in error_msg.lower():
                return jsonify(result), 400
            else:
                # No path found or timeout - valid search result
                return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Unable to complete search due to network error. Please try again."
        }), 500


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        "success": False,
        "error": "An unexpected error occurred. Please try again."
    }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found."
    }), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
