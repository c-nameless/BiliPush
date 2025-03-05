import os
import live
import time
import common
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
        time.sleep(5)
        if common.exit_event.is_set():
            logger.warning("waiting for all threads to exit")
            
            while liveThread.is_alive() or dynamicThread.is_alive() or statusThread.is_alive():
                time.sleep(1)

            while config.auto_schedule and scheduleThread.is_alive():
                time.sleep(1)
                
            break
        
        else:
            if not (liveThread.is_alive() and dynamicThread.is_alive() and statusThread.is_alive()):
                msg = message.PrivateMsg(user_id = config.admin)
                msg.appendMsg(message.TextMsg("子线程异常退出, 检查日志"))
                msg.send()
                common.exit_event.set()

            if config.auto_schedule and not scheduleThread.is_alive():
                common.exit_event.set()

except KeyboardInterrupt:
    pass

except:
    logger.error("an error occurred, program exit", exc_info = True)
    os.system("pause")

finally:
    if config.auto_schedule:
        schedule.force_stop()