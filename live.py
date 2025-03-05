import json
import time
import base64
import config
import account
import requests
import traceback
from PIL import Image
from io import BytesIO
from logger import logger
from datetime import datetime, timedelta
from dateutil import parser, relativedelta
from message import GroupMsg, TextMsg, Base64ImageMsg, AtAllMsg


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
    

def get_live_info():
    global room_id
    global uname
    
    if uname != "" and room_id != 0:
        return room_id
    
    info = bili_api_get(f"https://api.live.bilibili.com/live_user/v1/Master/info?uid={config.uid}")
    
    uname = info["info"]["uname"]
    room_id = info["room_id"]
    
    if uname == "" or room_id == 0:
        raise Exception("get room id error, check uid first")
    
    logger.warning(f"watching {uname} now")
    return room_id


def get_room_info(id: int) -> RoomInfo:
    content = bili_api_get(f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={id}")
    room_info = RoomInfo(live_status = content["live_status"],
                        title = content["title"],
                        user_cover = content["user_cover"],
                        live_time = content["live_time"])

    return room_info


def get_live_endtime() -> tuple[datetime, bool]:
    now = datetime.now()
    try:
        totalPage = 1
        i = 1
        
        while i <= totalPage:
            data = bili_api_get(f"https://api.live.bilibili.com/xlive/web-ucenter/user/following?page={i}&page_size=9&ignoreRecord=1&hit_ab=true")
            totalPage = data["totalPage"]
            
            lists = data["list"]
            for l in lists:
                if l["roomid"] == room_id:
                    record_live_time = l["record_live_time"]
                    
                    if record_live_time <= 0:
                        logger.warning("get end time from api failed")
                        raise Exception("get end time from api failed")
                    
                    live_end_time = datetime.fromtimestamp(record_live_time)
                    logger.info(f"get live end time from api, end time: {live_end_time}")
                    return live_end_time, True
            time.sleep(1)
            i += 1
        raise Exception("get end time from api failed")
        
    except:
        logger.info(f"get live end time from local, end time: {now}")
        return now, False


def start_living(room_info: RoomInfo):
    msg = GroupMsg()
    msg.appendMsg(TextMsg(f'{uname}开播了\n{"=" * 15}\n{room_info.title}'))
    msg.appendMsg(Base64ImageMsg(get_base64_image(room_info.user_cover)))
    msg.appendMsg(TextMsg(f"https://live.bilibili.com/{room_id}\n"))
    msg.appendMsg(AtAllMsg())
    msg.send()
    

def end_living(live_start: str):
    end, success = get_live_endtime()
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
    if success:
        text = f"{uname}下播了\n直播时长: {live_duration}"
    else:
        text = f"{uname}下播了\n直播时长(估测): {live_duration}"
        
    msg.appendMsg(TextMsg(text))
    msg.send()
    
    return True


def main():
    interval = config.live_interval * 60
    retry_times = 0
    max_retry = 30
    
    get_live_info()
    
    live_status = {
        "living": False,
        "start": ""
    }
    
    try:
        with open("./data/live.json", "r") as f:
            j = json.load(f)
            live_status["living"] = j["living"]
            live_status["start"] = j["start"]
        
    except:
        with open("./data/live.json", "w") as f:
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
                    
                    with open("./data/live.json", "w") as f:
                        json.dump(live_status, f)
                    
                    logger.warning(f"start live at {room_info.live_time}, send notification")

            else:
                if live_status["living"]:
                    live_status["living"] = False
                    
                    with open("./data/live.json", "w") as f:
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


if __name__ == "__main__":
    account.check_login()
    main()
    