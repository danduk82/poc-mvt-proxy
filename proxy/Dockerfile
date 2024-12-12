# FROM openresty/openresty:latest

# # Copy custom Nginx configuration
# COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf

# # Expose the port the proxy listens on
# EXPOSE 8080

# # Start OpenResty
# CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]


FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/* \
    && pip install flask requests

# Copy the application code
COPY proxy.py /app/proxy.py
COPY templates/ /app/templates/

# Set the working directory
WORKDIR /app

# Expose the application port
EXPOSE 8080

# Set environment variables for the proxy (replace with actual proxy URL)
ENV http_proxy=http://squid:3128
ENV https_proxy=http://squid:3128

# Run the application
CMD ["python3", "proxy.py"]
