# telegram-bot-asf
[![PyPI](https://img.shields.io/badge/Python-3.6-blue.svg?style=flat-square)](https://pypi.python.org/pypi/ASF-IPC)
[![ASF](https://img.shields.io/badge/ASF-4.0.3.0%20supported-orange.svg?style=flat-square)](https://github.com/JustArchi/ArchiSteamFarm)

使用telegram bot管理ASF  
参考[ASF_IPC](https://github.com/deluxghost/ASF_IPC)，[deluxghost/telegram-asf](https://github.com/deluxghost/telegram-asf)，[BenZinaDaze/tg_asf_bot](https://github.com/BenZinaDaze/tg_asf_bot)  

# 准备
1,安装python3.6  
2,创建telegram bot,获取token  
3,下载代码，使用git clone或在github页面下载
```shell
git clone https://github.com/zhongfly/telegram-bot-asf.git  
```
4,如使用socks代理，按注释修改requirments  
5,安装依赖
```shell
pip install -r requirements.txt  
```
6,修改配置文件tgbot.toml  
7,运行telegram-asf.py（使用默认配置文件路径）  
```shell
python3 telegram-asf.py
```

# 说明
1，可自定义配置文件路径，启动时使用命令
```shell
python3 telegram-asf.py YOUR_CONFIG.toml  
```
2，配置文件格式说明：
```ini
[telegram]
token = "987654321:XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
# 多位管理员用逗号隔开，例如[123456789,987654321,4564649]
admin = [123456789]
# socks5代理如下示例；http代理则类似填入"http://127.0.0.1:3128"；不使用代理则留空，只保留引号""
proxy =  "socks5h://127.0.0.1:1080/"

[ipc]
address = "http://127.0.0.1:1242/"
# 无密码则留空，只保留引号""
password = "123"
```
3，使用redeem或addlicense命令时会检查输入的格式是否正确


# 使用
方法1，直接发送ASF的command命令给bot，bot将回复结果。  
  
方法2，发送 /start 命令给bot，进入按键交互，按提示即可管理asf（注，若2min未回复bot，bot将自动取消操作，同时你也可以发送 /cancel 来手动取消）  
