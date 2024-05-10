#!/bin/bash

# Define source and destination directories
SOURCE_DIR="new"
DEST_DIR="new_USDC"

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Navigate to the source directory
cd "$SOURCE_DIR"

# Loop through all files ending with 'USDT.json'
for file in *USDT.json; do
    # Check if the file exists to avoid errors in case there are no matching files
    if [ -f "$file" ]; then
        # Construct the new filename by replacing 'USDT' with 'USDC'
        new_filename="${file/USDT/USDC}"
        
        # Copy the file to the destination directory with the new filename
        cp "$file" "../$DEST_DIR/$new_filename"
    fi
done

echo "Files have been copied and renamed successfully."