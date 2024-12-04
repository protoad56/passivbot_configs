
# Function to create a Tmux session and run a command
create_tmux_session() {
    session_name=$1
    command_to_run=$2

    # Check if the session already exists, create if it doesn't
    tmux has-session -t "$session_name" 2>/dev/null

    if [ $? != 0 ]; then
        tmux new-session -d -s "$session_name" "$command_to_run"
        echo "Starting $session_name"
        send_telegram_message "6757461113" "Starting $session_name" "6951567916:AAETarfcLbySoCkI6zYPSZj09Pu3kALmlUw"
    else
        echo "Session $session_name already exists."
    fi
}

systemctl start chrony
systemctl enable chrony
sleep 5
create_tmux_session "hyper_main" "cd /root/passivbot_multi/ && source myenv/bin/activate && python3 passivbot_multi.py configs/live/hyperliquid_forager_mode_live.hjson"
sleep 60
create_tmux_session "doge" "cd /root/passivbot_multi/ && source myenv/bin/activate && python3 passivbot.py binance_02 DOGEUSDT ../passivbot/configs/live/clock_0days.json -lw 2.5 -lm n -sm gs"
sleep 60
# create_tmux_session "doge_max" "cd /root/passivbot_multi/ && source myenv/bin/activate && python3 passivbot.py binance_03 INJUSDT ../passivbot_configs/clock/INJUSDT.json -lw 2.0 -sw 1.0 -lm n -sm gs"
# sleep 60
# create_tmux_session "multi" "cd /root/passivbot_multi/ && source myenv/bin/activate && python3 forager_improved_multi_prototype.py configs/forager/config_multi_live.hjson"
create_tmux_session "hawk" "cd /root/hawkbot/ && source myenv/bin/activate && python3 trade.py -a binance_forager -c ../passivbot_configs/hawk/dynamic-lin.json"
sleep 60
create_tmux_session "hyper_attcrypto" "cd /root/passivbot_v7 && source venv/bin/activate && cd passivbot-rust && maturin develop --release && cd .. && python3 src/main.py ../passivbot_configs/v7/template-att-multi.json -u hyperliquid_01 -lnp 10"
sleep 60
# create_tmux_session "hyper_v7" "cd /root/passivbot_v7 && source venv/bin/activate && cd passivbot-rust && maturin develop --release && cd .. && python3 src/main.py ../passivbot_configs/v7/2024-09-19T20_22_20_8_coins_7316a4a7.json"
# sleep 60
cd /root/exchanges_dashboard2/
docker-compose up -d


# Function to send a Telegram message
send_telegram_message() {
    chat_id=$1
    message=$2
    token=$3

    url="https://api.telegram.org/bot$token/sendMessage"
    curl -s -X POST $url -d chat_id=$chat_id -d text="$message"
}

# Sending a message to Telegram to indicate the server has restarted and scripts are running
send_telegram_message "6757461113" "Restart server completed and scripts are running." "6951567916:AAETarfcLbySoCkI6zYPSZj09Pu3kALmlUw"

# Print completion
echo "All tasks completed. Notification sent to Telegram."