import live
import time
import common
import config
import sqlite3
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


def get_follower_num():
    data = live.bili_api_get(f"https://api.bilibili.com/x/relation/stat?vmid={config.uid}")
    return data["follower"]



def get_captain_num():
    room_id = live.room_id
    if room_id == 0:
        room_id = live.get_live_info()
        
    data = live.bili_api_get(f"https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topListNew?roomid={room_id}&page=1&ruid={config.uid}&page_size=20&typ=5&platform=web")
    return data["info"]["num"]


def save_to_db(timestamp: int, follower: int, captain: int):
    cursor.execute(f"INSERT INTO {table} (uid, timestamp, follower, captain) values ({config.uid}, {timestamp}, {follower}, {captain})")
    conn.commit()
    logger.info("follower or captain num change, save statistics into db")


def main():
    follower_old = -1
    captain_old = -1
    
    res = cursor.execute(f"SELECT MAX(timestamp) FROM {table}").fetchone()
    if isinstance(res, tuple) and res[0] is not None:
        t = res[0]
        sub = abs(int(time.time()) - t)
        if sub <= 60:
            logger.info("less than 1min, skip")
            time.sleep(sub)
    
    res = cursor.execute(f"SELECT follower, captain FROM {table} WHERE id = (SELECT MAX(id) FROM {table} WHERE uid = {config.uid})").fetchone()
    if res is not None:
        follower_old, captain_old = res
    
    logger.info("start watching follower and captain num")
    while not common.exit_event.is_set():
        timestamp = int(time.time())
        m = time.localtime(timestamp).tm_min

        if m % 5 != 0:
            time.sleep(0.256)
            continue
        
        try:
            follower = get_follower_num()
            captain = get_captain_num()
            
            if follower_old == -1 and captain_old == -1:
                follower_old = follower
                captain_old = captain
                save_to_db(timestamp=timestamp, follower=follower, captain=captain)
                continue
            
            if follower_old != follower or captain_old != captain:
                logger.info(f"follower or captain num change")
                logger.info(f"before: follower: {follower_old}, captain: {captain_old}")
                logger.info(f"now: follower: {follower}, captain: {captain}")
                follower_old = follower
                captain_old = captain
                save_to_db(timestamp=timestamp, follower=follower, captain=captain)
                continue
            
            
        except:
            logger.error(f"An error occurred while query statistics info, waiting for next query.", exc_info = True)
            
        finally:
            time.sleep(200)


if __name__ == '__main__':
    import os
    import account
    os.makedirs("./data", exist_ok=True)
    account.check_login()
    main()