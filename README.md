# 关于
简易的B站开播检测、新动态检测、粉丝数和舰长数量统计，并在开播时和新动态发布时将其推送到qq群中

# 用法
## 注意事项
本程序仅在`python 3.12`中测试过，其它python版本不保证兼容性

为防止风控以及B站api的调用需要，需要使用B站APP扫码登录账号

建议在B站关注需要检测的UP主，以获得更准确的直播时长统计

若将`auto_schedule`设置为`true`，请在qq中将自动登录选项开启。同时，确保在本程序启动前***退出所有***qq客户端

若将`auto_schedule`设置为`true`，`qq_path`与`mail`对象相关属性必填，反之则不必填写

若自动启停客户端失败，会发送邮件通知

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
    "qq_path": "/opt/QQ/qq",
    "auto_schedule": false,
    "stop_hour": 0,
    "start_hour": 7,
    "uid": 114514,
    "admin": 1919810,
    "groups": [111,222,333],
    "at_all": [111],
    "dynamic_interval": 5,
    "live_interval": 1,
    "mail": {
        "sender": "114514@qq.com",
        "receiver": "1919810@qq.com",
        "password": "password",
        "server": "smtp.qq.com",
        "port": 465,
        "ssl": true
    }
}
```

参数解释
```
llonebot: llonebot的地址, http
browser_type: 浏览器类型，chrome或firefox，用于获取动态截图
browser_path: 浏览器可执行文件路径
driver_path: 浏览器驱动路径，供selenium使用
qq_path: 安装了llonebot的qq客户端可执行文件路径
auto_schedule: 是否启用自动启停
stop_hour: 在该时间(小时，24小时格式)后，若在一定时间后无消息发送，退出qq
start_hour: 在该时间(小时，24小时格式)后，不再自动退出qq
uid: 要检测的up主的uid
admin: 管理员qq号，程序异常退出时会向其发送通知
groups: 当检测到开播或新动态时，发送通知的群
at_all: 启用@all的群，需要群管理员权限
dynamic_interval: 动态检测频率，单位分钟
live_interval: 直播检测频率，单位分钟
mail: 邮件对象，包含发送邮件所使用的变量
mail["sender"]: 发送者邮箱，可以与接收者邮箱一致
mail["receiver"]: 接收者邮箱，可以与发送者邮箱一致
mail["password"]: 发送者邮箱的密码，部分邮箱需要单独的认证码
mail["server"]: smtp服务器地址
mail["port"]: smtp服务器端口
mail["ssl"]: 是否启用ssl
```

## step3: 运行
`python main.py`或打包成二进制文件运行

