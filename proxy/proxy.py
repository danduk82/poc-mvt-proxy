import os
import requests
from flask import Flask, request, Response, jsonify, render_template

app = Flask(__name__)

# Base URL for the backend
BASE_URL = "https://demo.baremaps.com"

# Environment variables for forwarded protocol and host
FORWARDED_PROTO = os.getenv("FORWARDED_PROTO")
FORWARDED_HOST = os.getenv("FORWARDED_HOST")

def get_proxy_url():
    """Determine the proxy URL based on headers or environment variables."""
    proto = request.headers.get("X-Forwarded-Proto", FORWARDED_PROTO) or request.scheme
    host = request.headers.get("X-Forwarded-Host", FORWARDED_HOST) or request.host
    return f"{proto}://{host}"

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Construct the full URL for the backend
    url = f"{BASE_URL}/{path}"

    # Forward headers and data from the client
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    data = request.get_data() if request.method in ['POST', 'PUT'] else None

    # Use the requests library to forward the request
    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=data,
            params=request.args,
            stream=True,  # Stream response for large content
        )
    except requests.exceptions.RequestException as e:
        return Response(f"Error connecting to the backend: {e}", status=502)

    # Rewrite JSON content for specific resources
    if path.endswith(("tiles.json", "style.json", "icons.json")):
        try:
            json_content = response.json()
            proxy_url = get_proxy_url()

            # Rewrite URLs in the JSON payload
            rewritten_content = rewrite_json_urls(json_content, proxy_url)
            return jsonify(rewritten_content), response.status_code
        except ValueError:
            app.logger.error(f"Failed to parse JSON for resource {path}")
            return Response(f"Failed to process JSON response.", status=502)

    # Stream non-JSON responses
    def generate():
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    headers = {key: value for key, value in response.headers.items()}
    return Response(generate(), status=response.status_code, headers=headers)

def rewrite_json_urls(json_content, proxy_url):
    """Recursively rewrite URLs in a JSON payload."""
    if isinstance(json_content, dict):
        return {key: rewrite_json_urls(value, proxy_url) for key, value in json_content.items()}
    elif isinstance(json_content, list):
        return [rewrite_json_urls(item, proxy_url) for item in json_content]
    elif isinstance(json_content, str) and BASE_URL in json_content:
        return json_content.replace(BASE_URL, proxy_url)
    return json_content

@app.route('/map')
def example_map():
    """Serve a dynamic HTML page for a MapLibre example."""
    # Determine the fully qualified URL
    proto = request.headers.get("X-Forwarded-Proto", FORWARDED_PROTO) or request.scheme
    host = request.headers.get("X-Forwarded-Host", FORWARDED_HOST) or request.host
    base_url = f"{proto}://{host}"

    # Pass the fully qualified style.json URL to the template
    style_url = f"{base_url}/style.json"
    return render_template('index.html', style_url=style_url)

if __name__ == '__main__':

    # Run the Flask server
    app.run(host='0.0.0.0', port=8080)
