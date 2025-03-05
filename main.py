import os
import live
import time
import config
import status
import dynamic
import message
import account
import schedule
import threading
from logger import logger

try:
    os.makedirs("./data", exist_ok=True)
    account.check_login()
    
    live.get_live_info()

    if config.auto_schedule:
        scheduleThread = threading.Thread(target=schedule.main, daemon=True)
        scheduleThread.start()

    liveThread = threading.Thread(target=live.main, daemon=True)
    liveThread.start()

    dynamicThread = threading.Thread(target=dynamic.main, daemon=True)
    dynamicThread.start()
    
    statusThread = threading.Thread(target=status.main, daemon=True)
    statusThread.start()

    while True:
        time.sleep(2)
        if not (liveThread.is_alive() and dynamicThread.is_alive() and statusThread.is_alive()):
            msg = message.PrivateMsg(user_id = config.admin)
            msg.appendMsg(message.TextMsg("子线程异常退出, 检查日志"))
            msg.send()
            raise Exception("sub thread exit unexpected, check log")

        if config.auto_schedule and not scheduleThread.is_alive():
            raise Exception("schedule thread exit unexpected, check log")

except KeyboardInterrupt:
    pass

except:
    logger.error("an error occurred, program exit", exc_info = True)
    os.system("pause")

finally:
    if config.auto_schedule:
        schedule.set_can_stop(True)
        schedule.stop()