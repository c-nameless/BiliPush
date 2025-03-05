import json

with open("./data/config.json", "r") as f:
    j = json.load(f)

llonebot: str = j["llonebot"]
if llonebot == "":
    raise Exception("llonebot addr not set")

if llonebot.endswith("/"):
    llonebot = llonebot.removesuffix("/")
    
browser_type: str = j["browser_type"]
if browser_type == "":
    raise Exception("browser_type not set")

browser_path: str = j["browser_path"]
if browser_path == "":
    raise Exception("browser_path not set")

driver_path: str = j["driver_path"]
if driver_path == "":
    raise Exception("driver_path not set")

auto_schedule: bool = j["auto_schedule"]
if auto_schedule:
    qq_path: str = j["qq_path"]
    if qq_path == "":
        raise Exception("qq_path not set")
    
    mail = j["mail"]

start_hour: int = j["start_hour"]
stop_hour: int = j["stop_hour"]
if start_hour == stop_hour:
    raise Exception("start_hour same with stop_hour, exit")

if stop_hour >= 24  or stop_hour < 0:
    raise Exception("stop_hour out of range. 0-23")

if start_hour >= 24 or start_hour < 0:
    raise Exception("start_hour out of range. 0-23")

uid: int = j["uid"]
if uid <= 0:
    raise Exception("uid out of range")

admin: int = j["admin"]
if admin <= 0:
    raise Exception("admin out of range")

groups: list[int] = j["groups"]
for g in groups:
    if g <= 0:
        raise Exception("group_id out of range")

at_all: list[int] = j["at_all"]
for a in at_all:
    if a <= 0:
        raise Exception("at_all_id out of range")

dynamic_interval: int = j["dynamic_interval"]
if dynamic_interval < 1:
    dynamic_interval = 1
    
live_interval: int = j["live_interval"]
if live_interval < 1:
    live_interval = 1
