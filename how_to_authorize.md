给自己的备忘
每次隔很久就忘记微博授权怎么搞，干脆写个备忘算了

1、登录p酱账号，在登录的情况下直接浏览器打开这个接口 
   https://open.weibo.com/wiki/Oauth2/authorize 
   参数直接看文档

2、用刚才回调拿到的 code 调用 
   https://open.weibo.com/wiki/Oauth2/access_token
   这个接口有点搞，参数要以GET的形式拼起来
   access_token?client_id=xxx&client_secret=xxx&...
   但是请求要用post发，post的body不要带任何数据

3、返回的access_token填到config.py里就行了（吧