#!/root/hawkbot/myenv/bin/python
import time
import requests
from collections import deque
import pyinotify
import os
import re
import threading
import html
import socket


# Configuration
LOG_FILE = '/root/hawkbot/logs/hawkbot.log'   # Update with your hawkbot.log path
# Map keywords to their corresponding emojis
KEYWORDS = {
    'ERROR': '🔴',    # Red circle for ERROR
    'WARNING': '🟡',  # Yellow circle for WARNING
    'multi_autoreduce_plugin':'🥹',
    'hedge_plugin':'😤'
}

IGNORE_KEYWORDS = ['dca_plugin','Order is rejected']  # Keywords to ignore
TELEGRAM_TOKEN = '7686131500:AAEWuaYOLynEoSyNEJkiOXI5EpNkHDg5dl4'        # Update with your bot's API token
CHAT_ID = '6757461113'                 # Update with your chat ID
SERVER_NAME = socket.gethostname()

class LogMonitor(pyinotify.ProcessEvent):
    def __init__(self, logfile, keywords, ignore_keywords):
        self.logfile = logfile
        self.keywords = keywords  # Now a dictionary
        self.ignore_keywords = ignore_keywords
        self.last_lines = deque(maxlen=5)
        self._open_log_file()
                
    def _open_log_file(self):
        self.file = open(self.logfile, 'r')
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()
                
    def send_telegram_message(self, message):
        # Escape the server name
        escaped_server_name = html.escape(SERVER_NAME)
        # Include server name at the top
        full_message = f"<b>Server:</b> {escaped_server_name}\n\n{message}"
        # Print the message for debugging
        print(f"Sending message: {full_message}")
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': full_message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = response.json().get('description', 'No description')
            print(f"Telegram send failed: {e}\nError: {error_message}\nMessage: {full_message}")
        except requests.exceptions.RequestException as e:
            print(f"Telegram send failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def process_IN_MODIFY(self, event):
        self._read_new_lines()
                
    def process_IN_MOVE_SELF(self, event):
        # Log file has been rotated
        self.file.close()
        time.sleep(1)  # Wait a moment for the new file to be created
        self._open_log_file()
        self._read_new_lines()
  
    def _highlight_keywords(self, text):
        # Escape the text for HTML
        escaped_text = html.escape(text)

        # For each keyword, replace it with the highlighted version
        for keyword, emoji in self.keywords.items():
            # Escape the keyword for use in regex
            escaped_keyword = re.escape(keyword)
            # Create a regex pattern for case-insensitive matching and capture the matched text
            pattern = re.compile(f'({escaped_keyword})', re.IGNORECASE)
            # Replacement function to preserve the original case of the matched keyword
            def repl(match):
                matched_text = match.group(1)
                return f"{emoji} <b>{matched_text}</b>"
            # Perform the replacement
            escaped_text = pattern.sub(repl, escaped_text)
        return escaped_text

    def _read_new_lines(self):
        self.file.seek(self.position)
        while True:
            line = self.file.readline()
            if not line:
                break
            line = line.rstrip()
            self.last_lines.append(line)
            # Check if the line contains any of the alert keywords
            if any(keyword.lower() in line.lower() for keyword in self.keywords):
                # Check if the line contains any of the ignore keywords
                if any(ignore_keyword.lower() in line.lower() for ignore_keyword in self.ignore_keywords):
                    # Skip this line and continue
                    continue
                else:
                    # Line contains alert keyword and does not contain ignore keyword
                    lines_to_send = list(self.last_lines)
                    # Highlight keywords in the lines
                    lines_to_send = [self._highlight_keywords(l) for l in lines_to_send]
                    message = '\n'.join(lines_to_send)
                    self.send_telegram_message(message)
                    self.last_lines.clear()
        self.position = self.file.tell()

    def fetch_and_process_updates(self):
        offset = None
        while True:
            url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates'
            params = {'timeout': 100, 'offset': offset}
            try:
                response = requests.get(url, params=params)
                result = response.json()
                if result['ok']:
                    for update in result['result']:
                        offset = update['update_id'] + 1
                        if 'message' in update:
                            self.process_message(update['message'])
            except Exception as e:
                print(f"Error fetching updates: {e}")
            time.sleep(1)

    def process_message(self, message):
        if 'text' in message and 'chat' in message:
            chat_id = message['chat']['id']
            text = message['text'].strip()
            if str(chat_id) == CHAT_ID:
                if text.startswith('/add_keyword'):
                    parts = text[len('/add_keyword'):].strip().split()
                    if len(parts) >= 1:
                        keyword = parts[0]
                        emoji = parts[1] if len(parts) > 1 else '🔹'  # Default emoji
                        if keyword not in self.keywords:
                            self.keywords[keyword] = emoji
                            self.send_telegram_message(f"Keyword '{keyword}' added with emoji '{emoji}'.")
                        else:
                            self.send_telegram_message(f"Keyword '{keyword}' already exists.")
                    else:
                        self.send_telegram_message("Usage: /add_keyword [keyword] [emoji]")
                elif text.startswith('/remove_keyword'):
                    keyword = text[len('/remove_keyword'):].strip()
                    if keyword in self.keywords:
                        del self.keywords[keyword]
                        self.send_telegram_message(f"Keyword '{keyword}' removed.")
                    else:
                        self.send_telegram_message(f"Keyword '{keyword}' not found.")
                elif text.startswith('/list_keywords'):
                    if self.keywords:
                        keywords = ', '.join([f"{emoji} {kw}" for kw, emoji in self.keywords.items()])
                        self.send_telegram_message(f"Current keywords: {keywords}")
                    else:
                        self.send_telegram_message("No keywords set.")
                elif text.startswith('/add_ignore'):
                    keyword = text[len('/add_ignore'):].strip()
                    if keyword and keyword not in self.ignore_keywords:
                        self.ignore_keywords.append(keyword)
                        self.send_telegram_message(f"Ignore keyword '{keyword}' added.")
                    else:
                        self.send_telegram_message(f"Ignore keyword '{keyword}' already exists or invalid.")
                elif text.startswith('/remove_ignore'):
                    keyword = text[len('/remove_ignore'):].strip()
                    if keyword in self.ignore_keywords:
                        self.ignore_keywords.remove(keyword)
                        self.send_telegram_message(f"Ignore keyword '{keyword}' removed.")
                    else:
                        self.send_telegram_message(f"Ignore keyword '{keyword}' not found.")
                elif text.startswith('/list_ignores'):
                    if self.ignore_keywords:
                        keywords = ', '.join(self.ignore_keywords)
                        self.send_telegram_message(f"Current ignore keywords: {keywords}")
                    else:
                        self.send_telegram_message("No ignore keywords set.")
                else:
                    self.send_telegram_message(
                        "Available commands:\n"
                        "/add_keyword [keyword] [emoji]\n"
                        "/remove_keyword [keyword]\n"
                        "/list_keywords\n"
                        "/add_ignore [keyword]\n"
                        "/remove_ignore [keyword]\n"
                        "/list_ignores"
                    )

def monitor_log_file():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF

    log_monitor = LogMonitor(LOG_FILE, KEYWORDS, IGNORE_KEYWORDS)
    notifier = pyinotify.Notifier(wm, log_monitor)
    wm.add_watch(LOG_FILE, mask)

    # Start the message handling in a separate thread
    message_thread = threading.Thread(target=log_monitor.fetch_and_process_updates)
    message_thread.daemon = True
    message_thread.start()

    try:
        notifier.loop()
    except KeyboardInterrupt:
        notifier.stop()
        log_monitor.file.close()

if __name__ == "__main__":
    monitor_log_file()
