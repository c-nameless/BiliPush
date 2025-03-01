# 关于
简易的B站开播检测、新动态检测、粉丝数和舰长数量统计，并在开播时和新动态发布时将其推送到qq群中

# 用法
## 注意事项
本程序仅在`python 3.12`中测试过，其它python版本不保证兼容性

为防止风控以及B站api的调用需要，需要使用B站APP扫码登录账号

建议在B站关注需要检测的UP主，以获得更准确的直播时长统计

## step0: llonebot
需要使用[llonebot](https://github.com/LLOneBot/LLOneBot)，项目地址: https://github.com/LLOneBot/LLOneBot

## step1: 安装依赖
`pip install -r requirements.txt`

## setp2: 编辑配置
在程序同一目录下创建`data/config.json`，模板如下，根据实际情况修改

```json
{
    "llonebot": "http://127.0.0.1:11451",
    "browser_type": "chrome",
    "browser_path": "./chrome/chrome.exe",
    "driver_path": "./chrome/chromedriver.exe",
    "uid": 114514,
    "admin": 1919810,
    "groups": [111,222,333],
    "at_all": [111],
    "dynamic_interval": 5,
    "live_interval": 1
}
```

参数解释
```
llonebot: llonebot的地址, http
browser_type: 浏览器类型，chrome或firefox，用于获取动态截图
browser_path: 浏览器可执行文件路径
driver_path: 浏览器驱动路径，供selenium使用
uid: 要检测的up主的uid
admin: 管理员qq号，程序异常退出时会向其发送通知
groups: 当检测到开播或新动态时，发送通知的群
at_all: 启用@all的群，需要群管理员权限
dynamic_interval: 动态检测频率，单位分钟
live_interval: 直播检测频率，单位分钟
```

## step3: 运行
`python main.py`或打包成二进制文件运行

