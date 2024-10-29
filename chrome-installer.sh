#!/bin/bash
set -e

VERSION="132.0.6804.0"
PLATFORM="linux64"
chrome_json="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

# Retrieve the JSON data once and store it
json_data=$(curl -s "$chrome_json")

# Get Chrome download URL
latest_chrome_linux_download_url="$(echo "$json_data" | jq -r ".versions[] | select(.version == \"$VERSION\") | .downloads.chrome[] | select(.platform == \"$PLATFORM\") | .url")"

# Get ChromeDriver download URL (note the .downloads.chromedriver path)
latest_chrome_driver_linux_download_url="$(echo "$json_data" | jq -r ".versions[] | select(.version == \"$VERSION\") | .downloads.chromedriver[] | select(.platform == \"$PLATFORM\") | .url")"

# Exit if either URL is empty
if [ -z "$latest_chrome_linux_download_url" ] || [ -z "$latest_chrome_driver_linux_download_url" ]; then
    echo "Error: Could not find download URLs for Chrome version $VERSION"
    exit 1
fi

# Set download paths
download_path_chrome_linux="/opt/chrome-headless-shell-linux.zip"
download_path_chrome_driver_linux="/opt/chrome-driver-linux.zip"

# Download and install Chrome
mkdir -p "/opt/chrome"
echo "Downloading Chrome..."
curl -Lo "$download_path_chrome_linux" "$latest_chrome_linux_download_url"
unzip -q "$download_path_chrome_linux" -d "/opt/chrome"
rm -f "$download_path_chrome_linux"

# Download and install ChromeDriver
mkdir -p "/opt/chrome-driver"
echo "Downloading ChromeDriver..."
curl -Lo "$download_path_chrome_driver_linux" "$latest_chrome_driver_linux_download_url"
unzip -q "$download_path_chrome_driver_linux" -d "/opt/chrome-driver"
rm -f "$download_path_chrome_driver_linux"

echo "Installation complete!"