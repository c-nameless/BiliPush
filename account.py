import os
import io
import json
import qrcode
import requests
from PIL import Image


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

cookies = {}

def get_qrcode():
    r = requests.get("https://passport.bilibili.com/x/passport-login/web/qrcode/generate", headers=headers)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
        
    j = r.json()
    if j["code"] != 0:
        raise RuntimeError(f"get qrcode failed. response: {r.text}")
    return j["data"]["url"], j["data"]["qrcode_key"]


def get_cookies(key: str):
    r = requests.get(f"https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={key}", headers=headers)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    cookie = requests.utils.dict_from_cookiejar(r.cookies)
    set_cookies(data=cookie)
    
    j = json.dumps(cookie)
    with open("./data/cookies.json", "w", encoding="utf-8") as f:
        f.write(j)
    
    
def set_cookies(data):
    global cookies
    cookies = data


def login():
    url, key = get_qrcode()
    code = qrcode.QRCode()
    code.add_data(url)
    if os.name.lower() == "nt":
        i = code.make_image(fill_color="black", back_color="white")
        data = io.BytesIO()
        i.save(data)
        img = Image.open(data)
        img.show()
    else:
        code.print_tty()
    print("scan the qrcode and press enter")
    input()
    get_cookies(key=key)


def check_login():
    cookie = {}
    try:
        with open("./data/cookies.json", "r") as f:
            cookie = json.load(f)
    except:
        pass
        
    r = requests.get("https://account.bilibili.com/site/getCoin", headers=headers, cookies=cookie)
    if r.status_code != 200:
        raise Exception(f"status code: {r.status_code}, url: {r.url}")
    
    j = r.json()
    if j["code"] != 0:
        login()
    else:
        set_cookies(data=cookie)


if __name__ == "__main__":
    login()