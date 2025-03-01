import json
import live
import time
import sqlite3
import traceback
from logger import logger


table = "status"
conn = sqlite3.connect('./data/status.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        follower INTEGER DEFAULT 0,
        captain INTEGER DEFAULT 0
    )
''')
conn.commit()


def get_follower_num(uid: int):
    data = live.bili_api_get(f"https://api.bilibili.com/x/relation/stat?vmid={uid}")
    return data["follower"]



def get_captain_num(uid: int):
    room_id = live.room_id
    if room_id == 0:
        room_id = live.get_live_info(uid)
        
    data = live.bili_api_get(f"https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topListNew?roomid={room_id}&page=1&ruid={uid}&page_size=20&typ=5&platform=web")
    return data["info"]["num"]


def save_to_db(uid: int, timestamp: int, follower: int, captain: int):
    cursor.execute(f"INSERT INTO {table} (uid, timestamp, follower, captain) values ({uid}, {timestamp}, {follower}, {captain})")
    conn.commit()
    logger.info("follower or captain num change, save statistics into db")


def run(uid: int):
    follower_old = -1
    captain_old = -1
    
    res = cursor.execute(f"SELECT MAX(timestamp) FROM {table}").fetchone()
    if isinstance(res, tuple) and res[0] is not None:
        t = res[0]
        sub = abs(int(time.time()) - t)
        if sub <= 60:
            logger.info("less than 1min, skip")
            time.sleep(sub)
    
    res = cursor.execute(f"SELECT follower, captain FROM {table} WHERE id = (SELECT MAX(id) FROM {table})").fetchone()
    if res is not None:
        follower_old, captain_old = res
    
    logger.info("start watching follower and captain num")
    while True:
        timestamp = int(time.time())
        m = time.localtime(timestamp).tm_min

        if m % 5 != 0:
            time.sleep(0.256)
            continue
        
        try:
            follower = get_follower_num(uid=uid)
            captain = get_captain_num(uid=uid)
            
            if follower_old == -1 and captain_old == -1:
                follower_old = follower
                captain_old = captain
                save_to_db(uid=uid, timestamp=timestamp, follower=follower, captain=captain)
                continue
            
            if follower_old != follower or captain_old != captain:
                logger.info(f"follower or captain num change")
                logger.info(f"before: follower: {follower_old}, captain: {captain_old}")
                logger.info(f"now: follower: {follower}, captain: {captain}")
                follower_old = follower
                captain_old = captain
                save_to_db(uid=uid, timestamp=timestamp, follower=follower, captain=captain)
                continue
            
            
        except:
            traceback.print_exc()
            logger.error(f"An error occurred while query statistics info, waiting for next query.", exc_info = True)
            
        finally:
            time.sleep(200)
            

def main(uid: int):
    try:
        cursor.execute(f"SELECT timestamp FROM {table} ORDER BY timestamp DESC LIMIT 1")
        run(uid=uid)
        
    except:
        traceback.print_exc()
        logger.error("db operation failed", exc_info=True)
        
    finally:
        conn.commit()
        conn.close()


if __name__ == '__main__':
    import os
    import account
    
    os.makedirs("./data", exist_ok=True)
    
    config = open("./data/config.json", 'r', encoding="utf-8")
    configJson = json.load(config)
    
    account.check_login()

    main(configJson["uid"])