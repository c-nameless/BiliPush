import json
import time
import account
import requests
from logger import logger
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions, ChromeService
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxService
from message import GroupMsg, TextMsg, Base64ImageMsg, NetworkImageMsg, AtAllMsg


id_str = []
browser_type = ""
browser_path = ""
driver_path = ""


def api_get_recent_dynamic(uid: int):
    r = requests.get(f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?host_mid={uid}", headers=account.headers, cookies=account.cookies)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    j = r.json()
    if j["code"] != 0:
        raise Exception(f"api init dynamic failed. response: {r.text}")
    
    return j["data"]


def get_id_str_from_data(data) -> list:
    new_id_str = []
    items = data["items"]
    for item in items:
        new_id_str.append(item["id_str"])
        
    return new_id_str


def check_has_new_dynamic(new_id_str: list):
    res = []
    
    for id in new_id_str:
        if id not in id_str:
            res.append(id)
            
    return res


def get_pic_url_from_dynamic(item):
    pics = []
    try:
        if item["type"] == "DYNAMIC_TYPE_DRAW":
            pic_items = item["modules"]["module_dynamic"]["major"]["draw"]["items"]
            for pic in pic_items:
                pics.append(pic["src"])
    finally:
        return pics


def init_browser():
    if browser_type.lower() == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless")
        options.binary_location=browser_path
        service = ChromeService(executable_path=driver_path)
        driver = Chrome(options=options, service=service)
    else:
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.binary_location=browser_path
        service = FirefoxService(executable_path=driver_path)
        driver = Firefox(options=options, service=service)
    
    driver.implicitly_wait(10)
    return driver


def init(browser_type_arg: str, browser_path_arg: str, driver_arg):
    global browser_type
    global browser_path
    global driver_path
    
    if browser_type_arg.lower() != "chrome" and browser_type_arg.lower() != "firefox":
        raise Exception("unknown browser type")
    
    browser_type = browser_type_arg.lower()
    browser_path = browser_path_arg
    driver_path = driver_arg
    
    init_browser()


def browser_get(id: int):
    driver = init_browser()
    
    driver.get("https://www.bilibili.com")
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.delete_all_cookies()
    
    for key, value in account.cookies.items():
        driver.add_cookie({"name": key, "value": value, "domain":".bilibili.com", "path":"/"})
        
    driver.get(f'https://www.bilibili.com/opus/{id}')

    class_names = ["bili-opus-view", "bili-dyn-item__main"]
    success = False
    dynamic_img = ""
    for name in class_names:
        try:
            dynamic_img = driver.find_element(by=By.CLASS_NAME, value=name).screenshot_as_base64
            success = True
            break
        except:
            logger.error("selenium get dynamic error", exc_info = True)

    if not success:
        driver.save_screenshot("err.png")

    driver.quit()
    return success, dynamic_img


def send_new_dynamic(data):
    msg = GroupMsg()
    for item in data:
        try:
            msg.appendMsg(TextMsg(f'{item["modules"]["module_author"]["name"]}发布了新动态'))
            success, dynamic_pic = browser_get(item["id_str"])
            if not success:
                raise Exception("dynamic screen shoot failed")
            
            msg.appendMsg(Base64ImageMsg(dynamic_pic))
            pics = get_pic_url_from_dynamic(item = item)
            for pic in pics:
                msg.appendMsg(NetworkImageMsg(pic))
            
            msg.appendMsg(TextMsg('https://t.bilibili.com/{item["id_str"]}\n'))
            msg.appendMsg(AtAllMsg())
            
            msg.send()
        
        except:
            logger.error("an error occurred when process new dynamic", exc_info = True)
            
        finally:
            msg.clear()


def run(uid: int, interval: int):
    global id_str
    skip_first = True
    
    while True:
        try:
            data = api_get_recent_dynamic(uid=uid)
            
            if skip_first:
                id_str = get_id_str_from_data(data=data)
                logger.info("dynamic skip first, waiting for next query")
                skip_first = False
                continue
            
            ids = get_id_str_from_data(data=data)
            new_id_str = check_has_new_dynamic(ids)
            if len(new_id_str) <= 0:
                logger.info("dynamic not update yet, waiting for next query")
                continue
            
            id_str = ids
            items = data["items"]
            to_send = []
            for item in items:
                if item["id_str"] in new_id_str:
                    to_send.append(item)
            
            logger.warning("new dynamic update")
            send_new_dynamic(data=to_send)
            
        except:
            logger.error(f"an error occurred, waiting for next query.", exc_info = True)
            
        finally:
            time.sleep(interval)


def main(uid: int, interval_arg:int):
    if interval_arg < 1:
        interval_arg = 1
    
    run(uid = uid, interval = interval_arg * 60)


if __name__ == '__main__':
    import message
    
    config = open("./data/config.json", 'r', encoding="utf-8")
    configJson = json.load(config)
    
    message.init(addr=configJson["llonebot"],group = configJson["groups"] ,at=configJson["at_all"])
    message.check_bot()
    
    account.check_login()
    
    init(configJson["browser_type"],configJson["browser_path"],configJson["driver_path"])

    main(configJson["uid"], configJson["live_interval"])
    