# Honkai Star Rail Wiki zh

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
