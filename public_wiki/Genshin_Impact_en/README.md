# Genshin Impact Wiki zh

Status: WIP... (just started)

### Steps

1. Download the latest wiki dump directly from [here](https://genshin-impact.fandom.com/wiki/Special:Statistics)
2. Preprocess the wiki dump file

(Specify the file path in line 12 in preprocess_wiki_xml.py)

~~~
python preprocess_wiki_xml.py
~~~

3. Parse the wiki data

~~~
python parse_character.py
~~~

4. Obtain the data in data folder