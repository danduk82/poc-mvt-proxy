import os
import requests
from flask import Flask, request, Response, jsonify, render_template

app = Flask(__name__)

# Base URL for the backend
BASE_URLS = {
    "baremaps-com": "https://demo.baremaps.com",
    "baremaps-apache-org": "https://baremaps.apache.org",
    
    }

# Environment variables for forwarded protocol and host
FORWARDED_PROTO = os.getenv("FORWARDED_PROTO")
FORWARDED_HOST = os.getenv("FORWARDED_HOST")

def get_proxy_url():
    """Determine the proxy URL based on headers or environment variables."""
    proto = request.headers.get("X-Forwarded-Proto", FORWARDED_PROTO) or request.scheme
    host = request.headers.get("X-Forwarded-Host", FORWARDED_HOST) or request.host
    return f"{proto}://{host}"

def get_baremaps_url(path):
    # Construct the full URL for the backend
    if path.endswith((".mvt")):
        base_url = BASE_URLS.get("baremaps-com")
    else:
        base_url = BASE_URLS.get("baremaps-apache-org")    
    url = f"{base_url}/{path}"
    return url

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    url = get_baremaps_url(path)
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
    if path.endswith((".json")):
        try:
            json_content = response.json()
            proxy_url = get_proxy_url()

            # Rewrite URLs in the JSON payload
            rewritten_content = rewrite_json_urls(json_content, proxy_url, path)
            return jsonify(rewritten_content), response.status_code
        except ValueError:
            app.logger.error(f"Failed to parse JSON for resource {path}")
            return Response(f"Failed to process JSON response.", status=502)
    # Handle Protobuf tiles (.mvt)
    elif path.endswith(".mvt"):
        # Read the raw content
        response_content = response.content

        # Remove "Content-Encoding: gzip" if the content is not actually gzipped
        if response.headers.get("Content-Encoding") == "gzip":
            if not response_content.startswith(b"\x1f\x8b"):  # Check for gzip magic numbers
                response.headers.pop("Content-Encoding", None)

        # Ensure no "Transfer-Encoding: chunked" is sent if the content is not chunked
        response.headers.pop("Transfer-Encoding", None)

        return Response(
            response_content,
            status=response.status_code,
            headers={key: value for key, value in response.headers.items()},
            content_type=response.headers.get('Content-Type')
        )
    
    # Stream non-JSON responses
    def generate():
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    # Forward headers for non-MVT responses
    headers = {key: value for key, value in response.headers.items()}
    headers.pop("Transfer-Encoding", None)  # Avoid sending invalid chunked headers
    return Response(generate(), status=response.status_code, headers=headers)


def rewrite_json_urls(json_content, proxy_url, path):
    """Recursively rewrite URLs in a JSON payload."""
    if isinstance(json_content, dict):
        return {key: rewrite_json_urls(value, proxy_url, path) for key, value in json_content.items()}
    elif isinstance(json_content, list):
        return [rewrite_json_urls(item, proxy_url, path) for item in json_content]
    elif isinstance(json_content, str) and get_baremaps_url(path) in json_content:
        return json_content.replace(get_baremaps_url(path), proxy_url)
    return json_content

def get_base_url():
    """Helper function to determine the fully qualified base URL."""
    proto = request.headers.get("X-Forwarded-Proto", FORWARDED_PROTO) or request.scheme
    host = request.headers.get("X-Forwarded-Host", FORWARDED_HOST) or request.host
    return f"{proto}://{host}"

def render_map(template_name, style_filename):
    """Helper function to render a map with the given style."""
    base_url = get_base_url()
    style_url = f"{base_url}/{style_filename}"
    return render_template(template_name, style_url=style_url)

@app.route('/default')
def default_map():
    """Serve the default map"""
    return render_map('index.html', 'mapStyles/default.json')

@app.route('/light')
def light_map():
    """Serve the light map."""
    return render_map('index.html', 'mapStyles/light.json')

@app.route('/dark')
def dark_map():
    """Serve the dark map."""
    return render_map('index.html', 'mapStyles/dark.json')

if __name__ == '__main__':

    # Run the Flask server
    app.run(host='0.0.0.0', port=8080)
