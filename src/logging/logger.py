import os
import logging
from datetime import datetime

LOG_DIR_PATH = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR_PATH, exist_ok=True)

LOG_FILE = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR_PATH, LOG_FILE)


class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"))
        self.logger.addHandler(logging.StreamHandler())
    
    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)


logger = Logger()