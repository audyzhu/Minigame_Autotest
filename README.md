# Minigame_Autotest
基于Laya引擎的自动化测试工具 注入miniAutoTest.js进去相关小游戏，即可录制回放点击操作，实现基本自动化测试

## SDK



## Server  
  由于微信连接的限制，只支持https和websocket，所以这边使用的是websocket，需要安装一下开源的服务器，python很方便的一个websocket库，不过不支持WSS，只支持WS。
  安装方法：  
`pip install git+https://github.com/Pithikos/python-websocket-server`   
`pip install websocket-server`  
`可以直接拷贝websocket-server.py到你项目对应运行目录`  
