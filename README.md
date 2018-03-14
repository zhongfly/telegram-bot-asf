# telegram-bot-asf
使用telegram bot管理ASF  
基于[ASF_IPC](https://github.com/deluxghost/ASF_IPC)  
参考[deluxghost/telegram-asf](https://github.com/deluxghost/telegram-asf)，[BenZinaDaze/tg_asf_bot](https://github.com/BenZinaDaze/tg_asf_bot)  

# 准备
1,安装python3.6  
2,创建telegram bot,获取token  
3,git clone https://github.com/zhongfly/telegram-bot-asf.git  
4,如使用socks代理，按注释修改requirments  
5,安装依赖 pip install -r requirements.txt  
6,在telegram-asf.py中按注释修改token，admin，ipc_address，ipc_password，use_proxy，proxy  
7,运行telegram-asf.py  

# 使用
方法1，直接发送ASF的command命令给bot，bot会回复结果。  
![直接发送命令（以status为例）](https://i.loli.net/2018/03/14/5aa8bfaa0f17f.jpg)  
  
方法2，发送 /start 命令给bot，进入按键交互，按提示即可管理asf（注，若2min未回复bot，bot将自动取消操作，同时你也可以发送 /cancel 来手动取消）  
![选择命令](https://i.loli.net/2018/03/14/5aa8bf6f49069.jpg)  
![选择bot](https://i.loli.net/2018/03/14/5aa8bf6f4131a.jpg)  
![发送KEY或取消](https://i.loli.net/2018/03/14/5aa8bf6f4ea21.jpg)  
