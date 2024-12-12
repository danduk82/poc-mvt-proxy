import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

# Base URL of the backend server
BACKEND_URL = "https://demo.baremaps.com"

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(path):
    # Construct the full URL for the backend
    url = f"{BACKEND_URL}/{path}"

    # Forward the client's request headers
    headers = {key: value for key, value in request.headers if key != "Host"}

    # Forward the client's request body (if any)
    body = request.get_data()

    # Use the requests library to forward the request
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=body,
            params=request.args,
            timeout=10,  # Timeout in seconds
        )
    except requests.RequestException as e:
        return Response(f"Error connecting to backend: {e}", status=502)

    # Return the backend response to the client
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    response_headers = {
        key: value for key, value in resp.headers.items() if key.lower() not in excluded_headers
    }
    return Response(resp.content, resp.status_code, headers=response_headers)


if __name__ == "__main__":
    # Ensure the proxy is configured via environment variables
    http_proxy = os.getenv("http_proxy")
    https_proxy = os.getenv("https_proxy")

    if not http_proxy or not https_proxy:
        print("Warning: Proxy environment variables are not set.")
    
    # Run the web server
    app.run(host="0.0.0.0", port=8080)
