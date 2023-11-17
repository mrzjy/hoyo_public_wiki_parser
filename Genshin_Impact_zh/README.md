# Genshin Impact Wiki zh

### Data structure

~~~
data/
├── 七圣召唤
│   ├── 七圣召唤.json
│   └── 卡牌一览.json
├── 书籍一览
│   └── 书籍一览.json
├── 任务
│   ├── 世界任务.json
│   ├── 传说任务.json
│   ├── 委托任务.json
│   └── 魔神任务.json
├── 成就一览
│   └── 成就一览.json
├── 扩展阅读
│   ├── 北陆图书馆.json
│   ├── 过场提示.json
│   └── 黑话.json
├── 物品一览
│   ├── 摆设套装一览.json
│   ├── 材料一览.json
│   ├── 道具一览.json
│   └── 食物一览.json
├── 生物志
│   ├── NPC图鉴.json
│   ├── 地理志一览.json
│   ├── 怪物一览.json
│   └── 野生生物一览.json
├── 装备图鉴
│   ├── 圣遗物一览.json
│   └── 武器一览.json
├── 角色图鉴
│   ├── 角色一览.json
│   ├── 角色装扮.json
│   └── 角色语音.json
└── 邮件
    └── 生日邮件.json
~~~

### Steps

All code is in parse.py

To run it yourself, you should:

1. Specify the cache data directory in line 12 (will crawl necessary htmls and save in local disk, so that the second time you run you won't have to crawl web pages again (unless you want to update))

2. Run the file
~~~
python parse.py
~~~

3. Obtain the data in data folder

### Known issues
- There are two sections that have not been parsed yet: 家具 and 任务道具
