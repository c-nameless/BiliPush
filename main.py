import os
import json
import live
import time
import status
import dynamic
import message
import account
import requests
import threading
from logger import logger

try:
    os.makedirs("./data", exist_ok=True)
    account.check_login()
    
    config = open("./data/config.json", 'r', encoding="utf-8")
    configJson = json.load(config)
    
    r = requests.get(f'https://api.live.bilibili.com/live_user/v1/Master/info?uid={configJson["uid"]}', headers=account.headers, cookies=account.cookies)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    j = r.json()
    if j["code"] != 0:
        raise Exception(f"request failed, raw: {j}, url: {r.url}")
    
    uname = j["data"]["info"]["uname"]
    if uname == "":
        raise Exception("get user info failed, check uid")
    
    message.init(addr=configJson["llonebot"],group = configJson["groups"],at=configJson["at_all"])
    dynamic.init(browser_type_arg=configJson["browser_type"],browser_path_arg=configJson["browser_path"],driver_arg=configJson["driver_path"])
    
    message.check_bot()
    
    liveThread = threading.Thread(target=live.main, args=(configJson["uid"], configJson["live_interval"]), daemon=True)
    liveThread.start()

    dynamicThread = threading.Thread(target=dynamic.main, args=(configJson["uid"], configJson["dynamic_interval"]), daemon=True)
    dynamicThread.start()
    
    
    statusThread = threading.Thread(target=status.main, args=(configJson["uid"],), daemon=True)
    statusThread.start()
    
    logger.warning(f"launched, watching {uname} now")
    while True:
        time.sleep(2)
        if not (liveThread.is_alive() and dynamicThread.is_alive() and statusThread.is_alive()):
            msg = message.PrivateMsg(user_id = configJson["admin"])
            msg.appendMsg(message.TextMsg("子线程异常退出, 检查日志"))
            msg.send()
            raise Exception("sub thread exit unexpected, check log")

except KeyboardInterrupt:
    pass

except:
    logger.error("an error occurred, program exit", exc_info = True)
    os.system("pause")