#!/root/hawkbot/myenv/bin/python
import time
import requests
from collections import deque
import pyinotify
import os

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
        payload = {'chat_id': CHAT_ID, 'text': message}
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
            if any(keyword in line for keyword in self.keywords):
                lines_to_send = list(self.last_lines)
                message = '\n'.join(lines_to_send)
                self.send_telegram_message(message)
                self.last_lines.clear()
        self.position = self.file.tell()

def monitor_log_file():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF

    log_monitor = LogMonitor(LOG_FILE, KEYWORDS)
    notifier = pyinotify.Notifier(wm, log_monitor)
    wm.add_watch(LOG_FILE, mask)

    try:
        notifier.loop()
    except KeyboardInterrupt:
        notifier.stop()
        log_monitor.file.close()

if __name__ == "__main__":
    monitor_log_file()
