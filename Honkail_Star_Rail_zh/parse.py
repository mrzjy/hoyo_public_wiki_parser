import json
import os
import re
import traceback

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup, element
import urllib.parse


cache_dir = "D:/data/biligame/starrail"
#current_dir = os.getcwd()
#cache_dir = current_dir + "/starrail"


def load_html_by_route(route, force_update=False):
    try:
        assert not force_update
        filename = "wiki.biligame.com" + route.replace("/", "_") + ".html"
        with open(os.path.join(cache_dir, filename), "r", encoding="utf-8") as f:
            html = f.read()
    except (FileNotFoundError, AssertionError):
        print("filename not found", route)
        if route.startswith("/"):
            route = route[1:]
        url = f"https://wiki.biligame.com/{route}"
        html = requests.get(url).text
        save_html(url, html, force_update)
    return html


def save_html(page_url, html_content, force_update=False):
    # convert URL into a valid filename
    filename = page_url.replace("http://", "").replace("https://", "").replace("/", "_") + ".html"
    filepath = os.path.join(cache_dir, filename)
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(filepath) or force_update:
        try:
            with open(filepath, 'w', encoding="utf-8") as f:
                f.write(html_content)
            print(filename, " saved.")
        except OSError:
            filename = urllib.parse.unquote(filename)
            filepath = os.path.join(cache_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding="utf-8") as f:
                    f.write(html_content)
                print(filename, " saved.")
        except:
            print(traceback.format_exc())


def parse_table(table):
    rows = table.find_all('tr')
    if len(rows[0].find_all("th")) > 1 and not rows[0].find_all("td"):
        table_type = "header_top"
    elif len(table.find_all("th")) == len(table.find_all("td")):
        table_type = "header_cell_equal"
    elif rows[0].find_all("th") and rows[0].find_all("td"):
        table_type = "header_left"
    else:
        raise NotImplementedError

    if table_type == "header_top":
        headers = [header.text.strip() for header in rows[0].find_all('th')]
        info = []
        for row in rows[1:]:
            row_info = {}
            for header, cell in zip(headers, row.find_all('td')):
                if not header:
                    continue
                if header == "稀有度":
                    row_info[header] = cell.find('img')["alt"].split(".")[0]
                else:
                    row_info[header] = re.sub(r"(^图)*\s+", " ", cell.text).strip()
            info.append(row_info)
    elif table_type == "header_cell_equal":
        info = {}
        for header, cell in zip(table.find_all("th"), table.find_all("td")):
            header = header.text.strip()
            if header == "稀有度":
                info[header] = cell.find('img')["alt"].split(".")[0]
            else:
                info[header] = re.sub(r"(^图)*\s+", " ", cell.text).strip()
    elif table_type == "header_left":
        info = {}
        for tr in table.find_all('tr'):
            headers = []
            for h in tr.find_all('th'):
                if h.has_attr("style") and "display:none" in h["style"]:
                    continue
                header = h.text.split("Media")[0].strip()
                headers.append(header)
            if not headers:
                continue
            header = " - ".join([h for h in headers if h])

            if header == "稀有度":
                content = tr.find('img')["alt"].split(".")[0]
            else:
                content = tr.find("td").text.strip().replace("\xa0", " ")
            if not content or "文件:" in content or content == "'":
                continue
            info[header] = content
    else:
        raise NotImplementedError

    if isinstance(info, dict):
        info = {k: v for k, v in info.items() if k and v}
    elif isinstance(info, list):
        info = [l for l in info if l]
    return info


def parse_character_list(route="/sr/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"):
    html = load_html_by_route(route, force_update=True)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for character in soup.find("div", {"id": "CardSelectTr"}).find_all("div", class_="visible-xs"):
        node = character.find("a")
        data = parse_character_info(node["href"])
        if data:
            results[node["title"]] = data
        print(node["title"], data)
    return results


def parse_character_info(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')

    quote = soup.find("div", {"style": "font-size: 18px;font-weight: bold;"})
    if quote:
        info["quote"] = quote.text.strip()

    basic_info = soup.find("table", class_="wikitable")
    info["基础信息"] = parse_table(basic_info)
    short_intro = basic_info.find_next("table", class_="wikitable")
    info["简介"] = short_intro.text.strip()
    for h2 in soup.find_all("h2"):
        section = h2.find('span', class_="mw-headline")
        if not section or "立绘" in section.text:
            continue
        title = section["id"].strip()
        if title == "角色相关":
            info[title] = [{"官方介绍": section.find_next("center").text.strip()}]
            for table in section.find_all_next('table', class_='wikitable'):
                data = parse_table(table)
                if data:
                    info[title].append(data)
        if title in {"角色故事", "角色晋阶材料", "其它信息", "角色搭配推荐"}:
            wikitable = section.find_next('table', class_='wikitable')
            if wikitable:
                info[title] = parse_table(wikitable)
    info = {k: v for k, v in info.items() if k and v}
    return info


def parse_character_voice_list(route="/sr/%E8%A7%92%E8%89%B2%E8%AF%AD%E9%9F%B3"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for character in soup.find_all("div", class_="ping0"):
        node = character.find("a")
        if node["title"] in results:
            continue
        data = parse_character_voice(node["href"])
        if data:
            results[node["title"]] = data
        print(node["title"], data)
    return results


def parse_character_voice(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all("table", class_="wikitable")[2:]:
        rows = table.find_all("tr")
        title = rows[0].text.strip()
        content = rows[-1].text.strip()
        info[title] = content
    return info


if __name__ == '__main__':
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    output_config = {
        "角色图鉴": {
            # "角色一览.json": parse_character_list,
            "角色语音.json": parse_character_voice_list,
        }
    }

    for dirname, parser_funcs in output_config.items():
        dirpath = os.path.join(output_dir, dirname)
        os.makedirs(dirpath, exist_ok=True)

        for filename, parser_func in parser_funcs.items():
            output = parser_func()
            filepath = os.path.join(dirpath, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
