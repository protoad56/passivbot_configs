#!/root/hawkbot/myenv/bin/python
import time
import requests
from collections import deque
import pyinotify
import os
import re
import threading

# Configuration
LOG_FILE = '/root/hawkbot/logs/hawkbot.log'   # Update with your hawkbot.log path
KEYWORDS = ['WARNING', 'ERROR', 'your_keyword']  # Update with your keywords
TELEGRAM_TOKEN = '7686131500:AAEWuaYOLynEoSyNEJkiOXI5EpNkHDg5dl4'        # Update with your bot's API token
CHAT_ID = '6757461113'                 # Update with your chat ID

class LogMonitor(pyinotify.ProcessEvent):
    def __init__(self, logfile, keywords):
        self.logfile = logfile
        self.keywords = keywords
        self.last_lines = deque(maxlen=5)
        self._open_log_file()
        
    def _open_log_file(self):
        self.file = open(self.logfile, 'r')
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()
        
    def send_telegram_message(self, message):
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'MarkdownV2'
        }
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Telegram send failed: {e}")
        
    def process_IN_MODIFY(self, event):
        self._read_new_lines()
        
    def process_IN_MOVE_SELF(self, event):
        # Log file has been rotated
        self.file.close()
        time.sleep(1)  # Wait a moment for the new file to be created
        self._open_log_file()
        self._read_new_lines()
        
    def _read_new_lines(self):
        self.file.seek(self.position)
        while True:
            line = self.file.readline()
            if not line:
                break
            line = line.rstrip()
            self.last_lines.append(line)
            if any(keyword.lower() in line.lower() for keyword in self.keywords):
                lines_to_send = list(self.last_lines)
                # Highlight keywords in the lines
                lines_to_send = [self._highlight_keywords(l) for l in lines_to_send]
                message = '\n'.join(lines_to_send)
                self.send_telegram_message(message)
                self.last_lines.clear()
        self.position = self.file.tell()

    def _highlight_keywords(self, text):
        # Use MarkdownV2 formatting; escape special characters
        def escape_markdown(text):
            # Escape Markdown special characters
            escape_chars = r'\_*[]()~`>#+-=|{}.!'
            return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

        escaped_text = escape_markdown(text)
        for keyword in self.keywords:
            # Escape the keyword as well
            escaped_keyword = escape_markdown(keyword)
            # Use regex to replace the keyword with its bold version
            pattern = re.compile(re.escape(escaped_keyword), re.IGNORECASE)
            escaped_text = pattern.sub(r'*{}\*'.format(escaped_keyword), escaped_text)
        return escaped_text

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
                    keyword = text[len('/add_keyword'):].strip()
                    if keyword and keyword not in self.keywords:
                        self.keywords.append(keyword)
                        self.send_telegram_message(f"Keyword '{keyword}' added.")
                elif text.startswith('/remove_keyword'):
                    keyword = text[len('/remove_keyword'):].strip()
                    if keyword in self.keywords:
                        self.keywords.remove(keyword)
                        self.send_telegram_message(f"Keyword '{keyword}' removed.")
                elif text.startswith('/list_keywords'):
                    keywords = ', '.join(self.keywords)
                    self.send_telegram_message(f"Current keywords: {keywords}")
                else:
                    self.send_telegram_message("Available commands:\n"
                                               "/add_keyword [keyword]\n"
                                               "/remove_keyword [keyword]\n"
                                               "/list_keywords")

def monitor_log_file():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF

    log_monitor = LogMonitor(LOG_FILE, KEYWORDS)
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
