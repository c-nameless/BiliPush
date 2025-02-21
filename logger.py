import os
import logging
import logging.handlers

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s - %(funcName)s at line %(lineno)d in %(filename)s')

os.makedirs("./data/logs", exist_ok=True)

handler = logging.handlers.TimedRotatingFileHandler(filename = "./data/logs/bilipush.log", encoding = "utf-8", when="d", interval=1, backupCount = 3, )
handler.setLevel(logging.WARNING)
handler.setFormatter(formatter)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console)