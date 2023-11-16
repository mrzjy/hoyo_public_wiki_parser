# Genshin Impact Wiki zh

### Steps

All code is in parse_genshin_zh.py

To run it yourself, you should:

1. Specify the cache data directory in line 12 (will crawl necessary htmls and save in local disk, so that the second time you run you won't have to crawl web pages again (unless you want to update))

2. Run the file
~~~
python parse_genshin_zh.py
~~~

3. Obtain the data in data folder

### Known issues
- There are two sections that have not been parsed yet: 家具 and 任务道具
