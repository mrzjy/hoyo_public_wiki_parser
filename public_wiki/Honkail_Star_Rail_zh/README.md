# Honkai Star Rail Wiki zh

### Current state

Lots of wiki contents are under construction. So we'll have to wait for them. 

Feel free to open an issue for what you want but does not exist in this repo.

### Requirements

~~~
Python 3.8+
Selenium + chromedriver (only needed for 短信.json)
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

### Known Issues

- There are pages with nested plotFrames that are complex to parse (e.g., 冒险任务.json, 致：黯淡星)
