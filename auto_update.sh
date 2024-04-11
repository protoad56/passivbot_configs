#!/bin/bash

set -x

TG_TOKEN="6120796421:AAEmms06XosOiABi3L2gc-utFYyNPb79Gnw"
TG_CHAT_ID="6757461113"

ROOT_PATH="/root"
CFG_DIR="${ROOT_PATH}/passivbot_configs"
PASSIVBOT_DIR="${ROOT_PATH}/passivbot/"

GIT_URL="https://github.com/protoad56/passivbot_configs.git"


cd $CFG_DIR


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
fi