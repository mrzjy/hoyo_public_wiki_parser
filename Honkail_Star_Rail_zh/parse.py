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
    elif rows[-1].find_all("th") and rows[-1].find_all("td"):
        table_type = "header_left"
    elif not table.find_all("th") and table.find_all("td"):
        table_type = "no_header"
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
            row_info = {k: v for k, v in row_info.items() if k and v}
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
            if not tr.find("td"):
                continue
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
    elif table_type == "no_header":
        info = [td.text.strip() for td in table.find_all("td")]
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


def parse_lightcone_list(route="sr/%E5%85%89%E9%94%A5%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all("tr")
    for row in rows[1:]:
        node = row.find("a")
        if node["title"] in results:
            continue
        data = parse_lightcone(node["href"])
        if data:
            results[node["title"]] = data
        print(node["title"], data)
    return results


def parse_lightcone(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    basic_info = soup.find("table", class_="wikitable")
    info["基础信息"] = parse_table(basic_info)
    for h2 in soup.find_all("h2"):
        section = h2.find('span', class_="mw-headline")
        if not section or "立绘" in section.text:
            continue
        title = section["id"].strip()
        if title in {"光锥故事", "推荐角色"}:
            wikitable = section.find_next('table', class_='wikitable')
            if wikitable:
                info[title] = parse_table(wikitable)
    info = {k: v for k, v in info.items() if k and v}
    return info


def parse_relic_list(route="/sr/%E9%81%97%E5%99%A8%E7%AD%9B%E9%80%89"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all("tr")
    for row in rows[1:]:
        node = row.find("a")
        if node["title"] in results:
            continue
        data = parse_relic(node["href"])
        if data:
            results[node["title"]] = data
        print(node["title"], data)
    return results


def parse_relic(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    basic_info = soup.find("table", class_="wikitable")
    info["基本信息"] = parse_table(basic_info)
    for h2 in soup.find_all("h2"):
        section = h2.find('span', class_="mw-headline")
        if not section or "立绘" in section.text:
            continue
        title = section["id"].strip()
        if title == "遗器来历":
            info[title] = {}
            section = section.find_next("div", class_="main-line-wrap")
            subtitles = [li.text.strip() for li in section.find("ul").find_all("li")]
            contents = section.find_all("div", class_="resp-tab-content")
            for t, c in zip(subtitles, contents):
                info[title][t] = c.text.strip()

        elif title in {"光锥故事", "推荐角色"}:
            wikitable = section.find_next('table', class_='wikitable')
            if wikitable:
                info[title] = parse_table(wikitable)
    info = {k: v for k, v in info.items() if k and v}
    return info


def parse_trailblaze_mission_list(route="/sr/%E5%BC%80%E6%8B%93%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for h2 in soup.find_all("h2")[2:]:
        chapter = h2.text.strip()
        results[chapter] = {}
        for node in h2.next_siblings:
            if node.name == "div" and "drop-down-wrap" in node["class"]:
                mission = node.find("div", class_="title").text.strip().replace("展开/折叠", "")
                results[chapter][mission] = {}
                for subnode in node.find("div", class_="wrap-content").find_all("a"):
                    title = subnode["title"]
                    data = parse_mission_page(subnode["href"])
                    if data:
                        results[chapter][mission][title] = data
                        print(data)
            if node.name == "h2":
                break
    return results


def parse_mission_page(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    basic_info = soup.find("table", class_="wikitable")
    if basic_info:
        info["基本信息"] = parse_table(basic_info)

    # irrelevant tags:
    for tag in soup.find_all("div", class_=["resourceLoader", "foldExplain"]):
        tag.decompose()

    for h2 in soup.find_all("h2"):
        section = h2.find('span', class_="mw-headline")
        if not section or "立绘" in section.text:
            continue
        title = section["id"].strip()
        info[title] = []
        if title == "任务相关":
            for node in h2.find_next_siblings():
                if node.text.strip():
                    if node.name == "h3":
                        info[title].append(f"={node.text.strip()}=")
                    elif node.name == "ul":
                        content = "\n".join([f"- {li}" for li in node.text.strip().split("\n")])
                        info[title].append(content)
                    else:
                        info[title].append(f"{node.text.strip()}")
            info[title] = "\n".join(info[title])
        elif title == "剧情内容":
            info[title] = parse_common_quest(h2, mode="next_sibling")
    return info


def parse_plot(node):
    text = ""
    option_beginnings = node.find_all("div", class_="plotOptions")
    option_contents = node.find_all("div", class_="content")
    if len(option_contents) >= len(option_beginnings):
        for j, (begin, content) in enumerate(zip(option_beginnings, option_contents)):
            if content.find("div", class_="NM-Container"):
                sender = content.find("div", class_="SenderName")
                message = sender.find_next("div").text.strip()
                content = f"{sender.text.strip()}：{message}\n"
                text += f"剧情选项{j + 1}：{content}\n"
            else:
                content = content.text.strip()
                text += f"剧情选项{j+1}：{begin.text.strip()}\n{content}\n"
    elif option_contents:
        if option_contents[0].find("div", class_="NM-Container"):
            for j, content in enumerate(option_contents):
                if content.find("div", class_="NM-Container"):
                    sender = content.find("div", class_="SenderName")
                    message = sender.find_next("div").text.strip()
                    text += f"剧情选项{j + 1}：{sender.text.strip()}：{message}\n"
        else:
            for j, option in enumerate(option_beginnings):
                text += f"剧情选项{j + 1}：{option.text.strip()}"
            for content in option_contents:
                text += f"{content}\n"
    return text


def parse_common_quest(node, mode="children"):
    if not node:
        return ""
    text = []
    if mode == "children":
        nodes = node.children
    elif mode == "next_sibling":
        nodes = node.find_next_siblings()
    else:
        raise NotImplementedError
    for node in nodes:
        if node.text.strip():
            if node.name == "h3":
                text.append(f"={node.text.strip()}=")
            elif node.name == "ul":
                text.append(node.text.strip())
            elif node.name == "dl" and node.find("span", {"style": "color:#f29e38"}):
                text.append(f"*{node.text.strip()}*")
            elif node.name == "div" and ("MessageFromMe" in node["class"] or "MessageToMe" in node["class"]):
                sender = node.find("div", class_="SenderName")
                message = sender.find_next("div").text.strip()
                text.append(f"{sender.text.strip()}：{message}\n")
            elif node.name == "div" and "tabber" in node["class"]:
                tab_title = node.find("div", class_="tabbertab")["title"]
                content = parse_common_quest(node)
                if content:
                    if isinstance(content, list):
                        content = "\n".join(content)
                    content = f"剧情分支：{tab_title}\n{content}"
                    text.append(content)
            elif node.name == "div" and "foldFrame" in node["class"]:
                content = node.find("div", class_="foldTitle").text.strip()
                text.append(f"*{content}*")
                fold_content = node.find("div", class_="foldContent")
                if not fold_content.find("div", class_="plotFrame"):
                    text.append(fold_content.text.strip())
                else:
                    content = parse_common_quest(fold_content)
                    if content:
                        if isinstance(content, list):
                            content = "\n".join(content)
                        text.append(content)
            elif node.name == "div" and "plotFrame" in node["class"]:
                content = parse_plot(node)
                if content:
                    text.append(content.strip())
            else:
                text.append(f"{node.text.strip()}")
    text = "\n".join(text)
    text = re.sub(" {2,}", " ", text)
    text = text.replace(" ", "")
    return text


def parse_companion_mission_list(route="/sr/%E5%90%8C%E8%A1%8C%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for h2 in soup.find_all("h2")[2:]:
        chapter = h2.text.strip()
        results[chapter] = {}
        unique_title = set()
        for node in h2.next_siblings:
            if node.name == "div" and "drop-down-wrap" in node["class"]:
                mission = node.find("div", class_="title").text.strip().replace("展开/折叠", "")
                results[chapter][mission] = {}
                for subnode in node.find("div", class_="wrap-content").find_all("a"):
                    title = subnode["title"]
                    if title in unique_title:
                        continue
                    unique_title.add(title)
                    data = parse_mission_page(subnode["href"])
                    if data:
                        results[chapter][mission][title] = data
                        print(chapter, mission, data)
            if node.name == "h2":
                break
    return results


if __name__ == '__main__':
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    output_config = {
        "角色图鉴": {
            "角色一览.json": parse_character_list,
            "角色语音.json": parse_character_voice_list,
        },
        "装备图鉴": {
            "光锥一览.json": parse_lightcone_list,
            "装备一览.json": parse_relic_list,
        },
        "任务": {
            "开拓任务.json": parse_trailblaze_mission_list,
            "同行任务.json": parse_companion_mission_list,
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
