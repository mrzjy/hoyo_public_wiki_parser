import json

import mwxml
from mwxml.errors import MalformedXML

"""
fix the error in the lines below, before running the script:
xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 23871045, column 4
"""

# specify the data path here
file_path = "D:/data/fandom_wiki/gensinimpact_pages_current.xml/gensinimpact_pages_current.xml"

raw_data = []

import xml.etree.ElementTree as ET


def strip_tag_name(t):
    t = elem.tag
    idx = k = t.rfind("}")
    if idx != -1:
        t = t[idx + 1:]
    return t


if __name__ == '__main__':
    events = ("start", "end")

    title = None
    ns = ""
    for event, elem in ET.iterparse(file_path, events=events):
        tname = strip_tag_name(elem.tag)

        if event == 'end':
            if tname == 'title':
                title = elem.text
            if tname == "ns":
                ns = elem.text
            elif tname == 'text':
                content = elem.text
                if ns == "0":  # only namespace = "0" is what we need
                    raw_data.append(
                        {
                            "title": title,
                            "content": content,
                        }
                    )

                    if len(raw_data) % 500 == 0:
                        print(len(raw_data))

    with open(".cache/raw_data.jsonl", "w", encoding="utf-8") as f:
        for d in raw_data:
            print(json.dumps(d, ensure_ascii=False), file=f)
