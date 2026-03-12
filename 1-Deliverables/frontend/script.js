// Frontend JavaScript for Wikipedia Chain Finder

const API_URL = '/api/search';

// DOM elements
const form = document.getElementById('search-form');
const startInput = document.getElementById('start');
const endInput = document.getElementById('end');
const submitBtn = document.getElementById('submit-btn');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const resultsDiv = document.getElementById('results');
const pathLengthP = document.getElementById('path-length');
const pathDisplayDiv = document.getElementById('path-display');

// Form submission handler
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Get and trim input values
    const start = startInput.value.trim();
    const end = endInput.value.trim();

    // Validate inputs
    if (!start || !end) {
        showError('Please enter both start and end article titles.');
        return;
    }

    // Start search
    setLoading(true);
    hideError();
    hideResults();

    try {
        // Set a 90-second timeout to allow for server's 60-second search timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000);

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ start, end }),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        const data = await response.json();

        if (data.success) {
            showResults(data.path);
        } else {
            showError(data.error || 'An error occurred. Please try again.');
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            showError('Search timed out. Try articles that are more closely related.');
        } else {
            showError('Network error. Please check your connection and try again.');
        }
    } finally {
        setLoading(false);
    }
});

// Set loading state
function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        loadingDiv.classList.remove('hidden');
    } else {
        submitBtn.disabled = false;
        loadingDiv.classList.add('hidden');
    }
}

// Show error message
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

// Hide error message
function hideError() {
    errorDiv.classList.add('hidden');
}

// Show results
function showResults(path) {
    // Calculate steps (path length - 1)
    const steps = path.length - 1;
    pathLengthP.textContent = `Found path in ${steps} step${steps !== 1 ? 's' : ''} (${path.length} articles)`;

    // Build path display
    pathDisplayDiv.innerHTML = '';

    path.forEach((article, index) => {
        // Create article link
        const link = document.createElement('a');
        link.href = `https://en.wikipedia.org/wiki/${encodeURIComponent(article.replace(/ /g, '_'))}`;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.className = 'article-link';
        link.textContent = article;
        pathDisplayDiv.appendChild(link);

        // Add arrow between articles (except after last one)
        if (index < path.length - 1) {
            const arrow = document.createElement('span');
            arrow.className = 'arrow';
            arrow.textContent = '\u2192'; // → arrow
            pathDisplayDiv.appendChild(arrow);
        }
    });

    resultsDiv.classList.remove('hidden');
}

// Hide results
function hideResults() {
    resultsDiv.classList.add('hidden');
}
