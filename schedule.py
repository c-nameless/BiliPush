import time
import config
import requests
import threading
import subprocess
from logger import logger
from datetime import datetime


qq: None | subprocess.Popen = None
mutex = threading.Lock()
skip = False
can_stop = False


def process_is_alive():
    if qq is None:
        return False

    return qq.poll() is None


def check_can_stop():
    with mutex:
        return process_is_alive() and can_stop


def set_can_stop(can: bool):
    with mutex:
        global can_stop
        global skip
        if not can:
            skip = True
        can_stop = can


def start():
    with mutex:
        if process_is_alive():
            return True

        global qq
        try:
            logger.warning("starting qq now")
            qq = subprocess.Popen(args=config.qq_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        except:
            qq = None
            logger.error("start qq failed", exc_info=True)
            return False


def stop():
    with mutex:
        if not process_is_alive():
            return True

        global qq
        try:
            qq.kill()
            for i in range(0, 30):
                if qq.poll() is not None:
                    qq = None
                    logger.info("stop qq success")
                    return True
                time.sleep(1)

            raise Exception("stop qq failed")

        except Exception as e:
            logger.error(e, exc_info=True)
            return False


def bot_ready():
    try:
        r = requests.post(url=f"{config.llonebot}/get_status")
        if r.status_code != 200:
            return False

        res = r.json()
        if res["status"] != "ok":
            return False

        return True

    except:
        return False


def main():
    logger.warning("auto schedule start")
    global skip
    while True:
        logger.info("check qq can stop or not")

        if check_can_stop():
            if skip:
                skip = False
                logger.info("can stop, but skip")
                time.sleep(300)
                continue

            hour = datetime.now().hour

            if config.start_hour > config.stop_hour:
                if config.stop_hour <= hour < config.start_hour:
                    stop()

            if config.start_hour < config.stop_hour:
                if hour >= config.stop_hour or hour < config.start_hour:
                    stop()

        time.sleep(300)


if __name__ == "__main__":
    main()