#!/bin/bash

# Check if the folder argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <folder>"
    exit 1
fi

# Get the folder path from the argument
FOLDER="$1"

# Check if the provided argument is a valid directory
if [ ! -d "$FOLDER" ]; then
    echo "Error: $FOLDER is not a valid directory."
    exit 1
fi

# Iterate through all subfolders of the given folder
for SUBFOLDER in "$FOLDER"/*/; do
    if [ -d "$SUBFOLDER" ]; then
        echo "Processing folder: $SUBFOLDER"
        OUTPUT_FOLDER="${SUBFOLDER/raw/clean}"
        python script/parse.py "$SUBFOLDER" "$OUTPUT_FOLDER" "--force"
    fi
done