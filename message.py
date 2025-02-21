import time
import json
import requests
from logger import logger

llonebot = ""
groups = []
at_all = []


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
        url = f"{llonebot}/send_private_msg"

        r = requests.post(url = url, data = self.toJson(), headers = {'Content-Type': 'application/json'})
        if r.status_code != 200:
            raise Exception(f"status code: {r.status_code}, url: {r.url}")
        
        res = r.json()
        if res["status"] != "ok":
            raise Exception(f"send message failed, error info: {r.text}")
        
        logger.warning(f"sending success: {r.text}")


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
            url = f"{llonebot}/get_group_at_all_remain"
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
        url = f"{llonebot}/send_group_msg"
        
        for id in groups:
            self.group_id = id
            remove_at_all = False

            for msg in self.message:
                if isinstance(msg, AtAllMsg) and ((id not in at_all) or (not self.check_at_all())):
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


def init(addr: str, group: list, at: list):
    global llonebot
    global groups
    global at_all
    llonebot = addr
    groups = group
    at_all = at


def check_bot():
    if llonebot == "":
        raise Exception("llonebot addr not set")
    
    r = requests.post(url = f"{llonebot}/get_status")
    if r.status_code != 200:
        raise Exception("Get bot status failed, check url")
    
    res = r.json()
    if res["status"] != "ok":
        raise Exception(f"Bot status abnormal, info: {r.text}")