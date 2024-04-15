#!/bin/bash

set -x

TG_TOKEN="6120796421:AAEmms06XosOiABi3L2gc-utFYyNPb79Gnw"
TG_CHAT_ID="6757461113"

ROOT_PATH="/root"
CFG_DIR="${ROOT_PATH}/passivbot_configs"
PASSIVBOT_DIR="${ROOT_PATH}/passivbot"

GIT_URL="https://github.com/protoad56/passivbot_configs.git"

# Define the source folder and the destination folder
source_folder="${ROOT_PATH}/passivbot_configs/optimized"
destination_folder="${ROOT_PATH}/passivbot/configs/live/forager/live"  

# Define the path to the lock file
lock_file="${PASSIVBOT_DIR}/configs/forager/forager_lock.json"

cd $CFG_DIR

# Function to check if a file is locked
is_locked() {
    jq -r --arg filename "$1" '.files[] | select(.filename == $filename)' "$lock_file" | grep -q .
}


# Function to send message to Telegram
send_telegram_message() {
    local message="$1"
        curl -s --data "text=${message}" \
                --data "reply_markup=${keyboard}" \
                --data "chat_id=$TG_CHAT_ID" \
                --data "parse_mode=markdown" \
                "https://api.telegram.org/bot${TG_TOKEN}/sendMessage"
}

# Function to copy files based on newer timestamp
copy_if_newer() {
    src_file="$1"
    dest_file="$2"
    if [ -f "$dest_file" ]; then
        # Compare file modification times
        if [ "$src_file" -nt "$dest_file" ]; then
            if ! is_locked "$(basename "$src_file")"; then
                cp "$src_file" "$dest_file"
                message="Copied updated file: $(basename "$src_file")"
                echo "$message"
                send_telegram_message "$message"
            else
                message="Skipping locked file: $(basename "$src_file")"
                echo "$message"
                send_telegram_message "$message"
            fi
        fi
    else
        if ! is_locked "$(basename "$src_file")"; then
            cp "$src_file" "$dest_file"
            message="Copied new file: $(basename "$src_file")"
            echo "$message"
            send_telegram_message "$message"
        else
            message="Skipping locked file: $(basename "$src_file")"
            echo "$message"
            send_telegram_message "$message"
        fi
    fi
}


# Get current commit
current_commit=$(git rev-parse --short HEAD)

# Pull latest changes
git checkout main
git pull origin main
    

latest_commit=$(git rev-parse --short HEAD)

if [ "$latest_commit" != "$current_commit" ]; then
        message="Current config is updated to commit: *${latest_commit}*"
        message+="%0A%0A"
        message+="Config has been re-loaded, no actions are required."
        

                # Compose buttons for showing git changes and backtesting results
        keyboard="{\"inline_keyboard\":[[{\"text\":\"Changes\", \"url\":\"${GIT_URL}/commit/${latest_commit}\"}]]}"
        
                # # Send the message
        curl -s --data "text=${message}" \
                --data "reply_markup=${keyboard}" \
                --data "chat_id=$TG_CHAT_ID" \
                --data "parse_mode=markdown" \
                "https://api.telegram.org/bot${TG_TOKEN}/sendMessage"

        # Iterate over files in the source folder
        for file in "$source_folder"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                dest_file_path="$destination_folder/$filename"
                copy_if_newer "$file" "$dest_file_path"
            fi
        done

        # Special case to copy backtest_result.csv to a specific location with a new name
        if [ -f "backtest_result.csv" ]; then
            copy_if_newer "backtest_result.csv" "$PASSIVBOT_DIR/att_backtest_result.csv"
        fi


fi