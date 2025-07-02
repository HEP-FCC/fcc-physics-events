#!/bin/bash

# ==============================================================================
# Batch Upload FCC JSON Dictionaries to API
#
# Description:
#   This script finds all `.json` files in a specified directory and uploads
#   each one to the FCC Physics Events API endpoint for processing.
#
# Usage:
#   ./scripts/upload_jsons.sh /path/to/your/json_folder
#
# Prerequisites:
#   - `curl` must be installed.
#   - The FastAPI application must be running.
# ==============================================================================

# --- Configuration ---
# Set the target API endpoint.
# Make sure your FastAPI app is running and accessible at this address.
API_ENDPOINT="http://localhost:8000/upload-fcc-dict/"

# --- Helper Functions ---
# A helper function for logging messages with a timestamp.
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] - $1"
}

# --- Pre-flight Checks ---
# Check if the 'curl' command is available.
if ! command -v curl &> /dev/null; then
  log "ERROR: 'curl' command is not installed. Please install it to continue."
  exit 1
fi

# Check if a directory path was provided as an argument.
if [ -z "$1" ]; then
  log "ERROR: No directory specified."
  log "Usage: $0 /path/to/your/json_folder"
  exit 1
fi

# Store the provided directory path.
SOURCE_DIR="$1"

# Check if the provided path is actually a directory.
if [ ! -d "$SOURCE_DIR" ]; then
  log "ERROR: The path '$SOURCE_DIR' is not a valid directory."
  exit 1
fi


# --- Main Logic ---
log "Starting batch upload from directory: $SOURCE_DIR"
log "Target API endpoint: $API_ENDPOINT"
echo "--------------------------------------------------"

# Find all files ending with .json (case-insensitive) in the source directory.
# The `-print0` and `while read -d ''` combination handles filenames with spaces.
find "$SOURCE_DIR" -type f -iname "*.json" -print0 | while IFS= read -r -d '' json_file; do
#   log "Uploading file: '$json_file'"

  # Use curl to upload the file.
  # -X POST: Specifies the HTTP POST method.
  # -F "file=@$json_file;type=application/json": Creates a multipart/form-data request.
  #   This is what FastAPI's `UploadFile` expects. 'file' is the name of the field.
  # -s: Silent mode to suppress progress meter.
  # -w "\nHTTP Status: %{http_code}\n": Prints the HTTP status code after the request.
  response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST -F "file=@$json_file;type=application/json" "$API_ENDPOINT")

  # Extract the body and status code from the response
  http_body=$(echo "$response" | sed '$d')
  http_status=$(echo "$response" | tail -n1 | cut -d: -f2)

  if [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
    log "SUCCESS: Server responded with status $http_status."
    log "Response: $http_body"
  else
    log "FAILURE: Server responded with status $http_status."
    log "Response: $http_body"
  fi
  echo "--------------------------------------------------"
done

log "Batch upload complete."

