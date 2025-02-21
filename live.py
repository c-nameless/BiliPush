import json
import time
import account
import base64
import requests
import traceback
from PIL import Image
from io import BytesIO
from logger import logger
from datetime import datetime, timedelta
from dateutil import parser, relativedelta
from message import GroupMsg, TextMsg, Base64ImageMsg, AtAllMsg


max_retry = 30
retry_times = 0
interval = 0
room_id = 0
uname = ""


class RoomInfo:
    def __init__(self, live_status: int, title: str, user_cover: str, live_time: str):
        self.live_status = live_status
        self.title = title
        self.user_cover = user_cover
        self.live_time = live_time


def bili_api_get(url: str):
    r = requests.get(url=url, headers=account.headers, cookies=account.cookies)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    j = r.json()
    if j["code"] != 0:
        raise Exception(f"request failed, raw: {j}, url: {r.url}")
    
    return j["data"]
    

def get_base64_image(url: str):
    if url == "":
        raise Exception("room cover url is empty, retry in 10s")
    
    r = requests.get(url=url, headers=account.headers, cookies=account.cookies)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    img = Image.open(BytesIO(r.content))
    if img.format.lower() != 'webp':
        img.close()
        return base64.b64encode(r.content)
    
    res = BytesIO()
    img.save(res, format="jpeg", quality=100)
    img.close()
    return base64.b64encode(res.getvalue())
    

def get_live_info(uid: int):
    info = bili_api_get(f"https://api.live.bilibili.com/live_user/v1/Master/info?uid={uid}")
    global room_id
    global uname
    uname = info["info"]["uname"]
    room_id = info["room_id"]
    
    if uname == "" or room_id == 0:
        raise Exception("get room id error, check uid first")
    
    return room_id


def get_room_info(id: int) -> RoomInfo:
    content = bili_api_get(f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={id}")
    room_info = RoomInfo(live_status = content["live_status"],
                        title = content["title"],
                        user_cover = content["user_cover"],
                        live_time = content["live_time"])

    return room_info


def get_live_endtime() -> datetime:
    try:
        data = bili_api_get("https://api.live.bilibili.com/xlive/web-ucenter/user/following?page=1&page_size=9&ignoreRecord=1&hit_ab=true")
        lists = data["list"]
        for i in lists:
            if i["roomid"] == room_id:
                record_live_time = i["record_live_time"]
                
                if record_live_time <= 0:
                    logger.warning("get end time from api failed")
                    raise Exception("get end time from api failed")
                
                live_end_time = datetime.fromtimestamp(record_live_time)
                logger.info("get live end time from api")
                return live_end_time
            
    except:
        logger.info("get live end time from local")
        return datetime.now()


def start_living(room_info: RoomInfo):
    msg = GroupMsg()
    msg.appendMsg(TextMsg(f"{uname}开播了\n{"=" * 15}\n{room_info.title}"))
    msg.appendMsg(Base64ImageMsg(get_base64_image(room_info.user_cover)))
    msg.appendMsg(TextMsg(f"https://live.bilibili.com/{room_id}\n"))
    msg.appendMsg(AtAllMsg())
    msg.send()
    

def end_living(live_start: str):
    end = get_live_endtime()
    start = parser.parse(live_start)
    
    if abs(datetime.now() - end) >= timedelta(minutes=5):
        return False
    
    duration = relativedelta.relativedelta(end, start)
    
    live_duration = ""
    if duration.days != 0:
        live_duration += f"{duration.days}天"
    if duration.hours != 0:
        live_duration += f"{duration.hours}小时"
    if duration.minutes != 0:
        live_duration += f"{duration.minutes}分钟"
    
    msg = GroupMsg()    
    msg.appendMsg(TextMsg(f"{uname}下播了\n直播时长: {live_duration}"))
    msg.send()
    
    return True


def run(uid: int):
    global interval
    global retry_times
    get_live_info(uid=uid)
    
    live_status = {
        "living": False,
        "start": ""
    }
    
    try:
        f = open("./data/live.json", "r+")
        j = json.load(f)
        live_status["living"] = j["living"]
        live_status["start"] = j["start"]
        
    except:
        f = open("./data/live.json", "w+")
        json.dump(live_status, f)
    
    while True:
        try:
            room_info = get_room_info(room_id)

            if room_info.live_status == 1:
                if live_status["living"]:
                    logger.info("living, waiting for next query")
                    
                else:
                    
                    try:
                        start_living(room_info)
                    except:
                        retry_times += 1
                        interval = 10
                        if retry_times >= max_retry:
                            interval = 60
                            
                        logger.error(f"send live notification failed, retry in {interval}s.", exc_info=True)
                        continue
                    
                    interval = 60
                    retry_times = 0
                    live_status["living"] = True
                    live_status["start"] = room_info.live_time
                    
                    f.seek(0)
                    f.truncate()
                    json.dump(live_status, f)
                    
                    logger.warning("start live, send notification")

            else:
                if live_status["living"]:
                    live_status["living"] = False
                    
                    f.seek(0)
                    f.truncate()
                    json.dump(live_status, f)
                    
                    send_end = end_living(live_status["start"])
                    
                    if send_end:
                        logger.warning("end live, send notification")
                        
                    else:
                        logger.warning("exceeds 5 minutes, push aborted")
                        
                else:
                    logger.info("not live yet, waiting for next query")

        except:
            traceback.print_exc()
            logger.error(f"An error occurred while query live info, waiting for next query.", exc_info = True)

        finally:
            time.sleep(interval)


def main(uid: int, interval_arg: int):
    if interval_arg < 1:
        interval_arg = 1
    
    global interval
    interval = interval_arg * 60
    
    run(uid = uid)


if __name__ == "__main__":
    import message
    
    config = open("./data/config.json", 'r', encoding="utf-8")
    configJson = json.load(config)
    
    message.init(addr=configJson["llonebot"],group = configJson["groups"] ,at=configJson["at_all"])
    message.check_bot()

    account.check_login()
    main(configJson["uid"], configJson["live_interval"])
    