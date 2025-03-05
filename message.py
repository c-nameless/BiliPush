import time
import json
import common
import config
import smtplib
import schedule
import requests
from logger import logger
from email.utils import formataddr
from email.mime.text import MIMEText


def fail_mail():
    with common.mutex:
        if common.exit_event.is_set():
            return
        
        try:
            msg = MIMEText("BiliPush发送消息失败, 请检日志确认情况", "plain", "utf-8")
            msg["From"] = formataddr(("BiliPush", config.mail["sender"]), "utf-8")
            msg["To"] = formataddr((None, config.mail["receiver"]), "utf-8")
            msg["Subject"] = "BiliPush 发送失败"

            if config.mail["ssl"]:
                smtp = smtplib.SMTP_SSL(config.mail["server"], config.mail["port"])
            else:
                smtp = smtplib.SMTP(config.mail["server"], config.mail["port"])

            smtp.login(config.mail["sender"], config.mail["password"])
            smtp.sendmail(config.mail["sender"], config.mail["receiver"], msg.as_string())
            smtp.quit()

        except:
            logger.error("send mail failed", exc_info=True)
        
        finally:
            common.exit_event.set()


class PrivateMsg:
    def __init__(self, user_id):
        self.user_id = user_id
        self.message = []


    def appendMsg(self, msg):
        self.message.append(msg)


    def toJson(self):
        message = []
        original = self.message.copy()
        for m in self.message:
            if isinstance(m, dict):
                message.append(m)
            else:
                message.append(m.__dict__)
        self.message = message
        j = json.dumps(self.__dict__)
        self.message = original
        return j
    
    
    def clear(self):
        self.user_id = 0
        self.message.clear()
        
    
    def send(self):
        try:
            if config.auto_schedule:
                schedule.set_can_stop(False)
                start = schedule.start()
                if not start:
                    logger.error("bot start fail, send mail")
                    fail_mail()
                    return

                ready = False

                for i in range(0, 60):
                    if schedule.bot_ready():
                        ready = True
                        break
                    time.sleep(1)

                if not ready:
                    logger.error("bot not ready, send mail")
                    fail_mail()
                    return

            url = f"{config.llonebot}/send_private_msg"

            r = requests.post(url = url, data = self.toJson(), headers = {'Content-Type': 'application/json'})
            if r.status_code != 200:
                raise Exception(f"status code: {r.status_code}, url: {r.url}")

            res = r.json()
            if res["status"] != "ok":
                raise Exception(f"send message failed, error info: {r.text}")

            logger.warning(f"sending success: {r.text}")

        except Exception as e:
            raise e

        finally:
            if config.auto_schedule:
                schedule.set_can_stop(True)

class GroupMsg:
    def __init__(self):
        self.group_id = 0
        self.message = []


    def appendMsg(self, msg):
        self.message.append(msg)


    def toJson(self):
        message = []
        original = self.message.copy()
        for m in self.message:
            if isinstance(m, dict):
                message.append(m)
            else:
                message.append(m.__dict__)
        self.message = message
        j = json.dumps(self.__dict__)
        self.message = original
        return j
    
    
    def clear(self):
        self.group_id = 0
        self.message.clear()
    
    
    def check_at_all(self):
        try:
            url = f"{config.llonebot}/get_group_at_all_remain"
            r = requests.post(url = url, json = {"group_id": self.group_id})
            if r.status_code != 200:
                return False
            
            j = r.json()
            if j["status"] != "ok":
                return False
            
            if j["data"]["can_at_all"] and j["data"][ "remain_at_all_count_for_group"] > 0 and j["data"][ "remain_at_all_count_for_uin"] > 0:
                return True
        
            return False
        
        except:
            return False
        
    
    def send(self):
        try:
            schedule.set_can_stop(False)
            start = schedule.start()
            if not start:
                logger.error("bot start fail, send mail")
                fail_mail()
                return

            ready = False

            for i in range(0, 60):
                if schedule.bot_ready():
                    ready = True
                    break
                time.sleep(1)

            if not ready:
                logger.error("bot not ready, send mail")
                fail_mail()
                return

            url = f"{config.llonebot}/send_group_msg"

            for id in config.groups:
                self.group_id = id
                remove_at_all = False

                for msg in self.message:
                    if isinstance(msg, AtAllMsg) and ((id not in config.at_all) or (not self.check_at_all())):
                        remove_at_all = True
                        self.message.remove(msg)

                r = requests.post(url = url, data = self.toJson(), headers = {'Content-Type': 'application/json'})
                if r.status_code != 200:
                    raise Exception(f"status code: {r.status_code}, url: {r.url}")

                res = r.json()
                if res["status"] != "ok":
                    raise Exception(f"send message failed, error info: {r.text}")

                logger.warning(f"sending success: {r.text}")

                if remove_at_all:
                    self.message.append(AtAllMsg())

                time.sleep(1)

        except Exception as e:
            raise e

        finally:
            if config.auto_schedule:
                schedule.set_can_stop(True)


class TextMsg:
    def __init__(self, text: str):
        self.type = "text"
        self.data = {
            "text": text
        }


class NetworkImageMsg:
    def __init__(self, image: str):
        self.type = "image"
        self.data = {
            "file": image
        }


class Base64ImageMsg:
    def __init__(self, image: bytes | str):
        self.type = "image"
        if isinstance(image, bytes):
            image_data = image.decode()
        else:
            image_data = image
        self.data = {
            "file": "base64://" + image_data
        }


class AtAllMsg:
    def __init__(self):
        self.type = "at"
        self.data = {
            "qq": "all"
        }