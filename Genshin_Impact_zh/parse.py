import json
import os
import re
import traceback

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup, element
import urllib.parse


cache_dir = "D:/data/biligame/genshin"


def load_html_by_route(route):
    try:
        filename = "wiki.biligame.com" + route.replace("/", "_") + ".html"
        with open(os.path.join(cache_dir, filename), "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("filename not found", route)
        if route.startswith("/"):
            route = route[1:]
        url = f"https://wiki.biligame.com/{route}"
        html = requests.get(url).text
        save_html(url, html)
    return html


def save_html(page_url, html_content):
    # convert URL into a valid filename
    filename = page_url.replace("http://", "").replace("https://", "").replace("/", "_") + ".html"
    filepath = os.path.join(cache_dir, filename)
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(filepath):
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


def parse_main_page(route="/ys/%E9%A6%96%E9%A1%B5"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    menu_wrap = soup.find('div', class_='menu-wrap wiki-menu-ul-1 clearfix')
    menu_items = menu_wrap.find_all('div', class_='wiki-menu-li-1')

    for menu_item in menu_items:
        title = menu_item.find('a', class_='menu-title')
        print(title.text.strip())
        sub_menu = menu_item.find('div', class_='wiki-menu-ul-2')
        if sub_menu:
            sub_menu_items = sub_menu.find_all('div', class_='wiki-menu-li-2')
            for sub_menu_item in sub_menu_items:
                sub_title = sub_menu_item.find('a', class_='menu-title').text.strip()

                print("\t", sub_title)
                for sub_sub_menu_item in sub_menu_item.find_all('a', class_='menu-title-1'):
                    try:
                        sub_sub_title = sub_sub_menu_item.text.strip()
                        href = sub_sub_menu_item["href"]
                        print("\t\t", sub_sub_title, href)
                    except:
                        continue


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
        table_type = "free"

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
    else:  # freeform
        info = []
        for row in rows:
            line = ""
            nodes = row.find_all(["th", "td"])
            for k, n in enumerate(nodes):
                if k and n.name == "td" and nodes[k-1].name == "th":
                    line += ": "
                content = n.text.replace('\xa0', '')
                content = re.sub("文件:.+\.(jpg|gif|png)", "", content)
                line += f"{content.strip()} "
            info.append(line.strip())

    if isinstance(info, dict):
        info = {k: v for k, v in info.items() if k and v}
    elif isinstance(info, list):
        info = [l for l in info if l]
    return info


def parse_character_list(route="/ys/%E8%A7%92%E8%89%B2"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    tab_contents = soup.find_all(class_="resp-tab-content")
    for tab_content in tab_contents:
        tabs = tab_content.find_all(class_="g C5星")
        tabs += tab_content.find_all(class_="g C4星")
        for tab in tabs:
            title = tab.find(class_="L").text
            link = tab.find_all("a")[-1]["href"]
            if title in results:
                continue
            # parse each character page
            results[title] = parse_character_info(link)
            print(f"{title} {results[title]}")
    return results


def parse_character_info(route):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')

    for h2 in soup.find_all("h2"):
        section = h2.find('span', class_="mw-headline")
        if not section or "立绘" in section.text:
            continue
        title = section["id"].strip()
        info[title] = {}

        if "天赋" in title:
            subsection = section.find_next("div", class_="resp-tabs-container")
            for s in subsection.find_all("div", class_="resp-tab-content"):
                name = s.find('div', class_="r-skill-title-1").text.split("图")[-1].strip()
                content = s.find('div', class_="r-skill-bg-2").get_text().split("描述")[-1]
                info[title][name] = re.sub(r"\s+", " ", content).strip()
            continue
        elif title == "角色相关":
            contents = {}
            headlines = section.find_all_next(['h3'])
            for headline in headlines:
                if headline.text.strip() not in contents:
                    contents[headline.text.strip()] = []
                for sibling in headline.find_next_siblings():
                    # Stop if encounter another headline at the same level or higher
                    if re.match("h\d", sibling.name) and int(sibling.name[1]) <= int(headline.name[1]):
                        break
                    if "原神WIKI导航" in sibling.text:
                        break
                    content = re.sub(r"图*\s+", "", sibling.text.strip())
                    if content:
                        contents[headline.text.strip()].append(content)
            info[title] = contents

        wikitable = section.find_next('table', class_='wikitable')
        if wikitable:
            info[title] = parse_table(wikitable)
    for key, item in info.items():
        if not item:
            print(f"warning: {key} field is empty", info)
    return info


def parse_character_voices(route="/ys/%E8%A7%92%E8%89%B2%E8%AF%AD%E9%9F%B3"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    tab_content = soup.find(class_="resp-tab-content")
    tabs = tab_content.find_all(class_="home-box-tag-1")

    # additional two
    for title, link in [
        ["旅行者语音/荧", "/ys/%E6%97%85%E8%A1%8C%E8%80%85%E8%AF%AD%E9%9F%B3/%E8%8D%A7"],
        ["旅行者语音/空", "/ys/%E6%97%85%E8%A1%8C%E8%80%85%E8%AF%AD%E9%9F%B3/%E7%A9%BA"],
    ]:
        results[title] = parse_voice_page(link)
        print(f"{title} {results[title]}")

    for tab in tabs:
        tab = tab.find("a")
        title, link = tab['title'], tab["href"]
        if "语音" in title:
            results[title] = parse_voice_page(link)
            print(f"{title} {results[title]}")
    return results


def parse_voice_page(route):
    html = load_html_by_route(route)
    if not html:
        return {}
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for table in soup.find_all("tbody")[2:]:
        rows = table.find_all('tr')
        key = table.find_all('tr')[0].text.strip()
        info[key] = {}
        subkeys = [th.text.strip() for th in rows[1].find_all('th')]
        for row in rows[2:]:
            cells = row.find_all('div')
            for s_key, cell in zip(subkeys, cells):
                text = re.sub("\s*</*(div|font).*>\s*", "", cell.prettify())
                text = re.sub(" <br/>", "", text)
                info[key][s_key] = text
    return info


def parse_character_outfits(route="/ys/%E8%A3%85%E6%89%AE"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table")

    results = {}
    for row in table.find_all("tr"):
        try:
            info = row.find("a")
            title, link = info['title'], info["href"]
            get, rarity, sort = row["data-param1"], row["data-param2"], row["data-param3"]
            results[title] = parse_outfit(link, sort)
            addition_map = {
                "来源": get, "稀有度": f"{rarity}星", "类型": sort,
            }
            for key, item in addition_map.items():
                if key not in results[title]:
                    results[title][key] = item
            print(f"{title} {results[title]}")
        except:
            continue
    return results


def parse_outfit(route, sort):
    info = {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    if sort != "衣装":
        wikitable = soup.find('table', class_='wikitable')
        for th in wikitable.find_all('th'):
            td = th.find_next('td')
            if th and th.text.strip() == "稀有度":
                info[th.text.strip()] = td.find('img')["alt"].split(".")[0]
            else:
                if td and "请上传文件" not in td.text:
                    info[th.text.strip()] = re.sub(r"(^图)*\s+", " ", td.text).strip()
    else:
        element = soup.find("span", {"id": "故事"})
        info["故事"] = element.find_next("tbody").text.strip()

    for key, item in info.items():
        if not item:
            del info[key]
    return info


def parse_weapon_list(route="/ys/%E6%AD%A6%E5%99%A8%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for s in soup.find_all("div", class_="g"):
        info = s.find_all('a')[-1]
        title, link = info['title'], info["href"]
        results[title] = parse_weapon(link)
        print(f"{title} {results[title]}")
    return results


def parse_weapon(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}

    brief = soup.find("div", class_="YS-WeaponBrief")
    brief = re.sub(r"\s*\n+\s*", "\n", brief.text).strip()
    info["简介"] = re.sub("\s*///\s*", "\n", brief)

    for key in ["实装版本", "锻造材料", "故事"]:
        span = soup.find("span", {"id": key})
        if span:
            info[key] = span.find_next("div").text.strip()

    rec = soup.find("div", class_="YSCard recommended")
    rec = re.sub(r"\s*\n+\s*", "\n", rec.text).strip()
    clean = ""
    for i, r in enumerate(rec.split("推荐说明")):
        if i % 2 == 1:
            clean += f"{r}\n"
    info["推荐"] = clean.strip()
    return info


def parse_relic_list(route="/ys/%E5%9C%A3%E9%81%97%E7%89%A9%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for s in soup.find_all("div", class_="g"):
        info = s.find_all('a')[-1]
        title, link = info['title'], info["href"]
        results[title] = parse_relic(link)
        print(f"{title} {results[title]}")
    return results


def parse_relic(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}

    brief = soup.find("div", class_="attribute")
    brief = re.sub(r"\s*\n+\s*", "\n", brief.text).strip()
    brief = re.sub(r" +", "\n", brief)
    info["简介"] = re.sub("\s*///\s*", "\n", brief)

    get = soup.find("div", class_="get")
    get = re.sub(r"\s*\n+\s*", "\n", get.text).strip()
    get = re.sub(r" +", "\n", get)
    info["获取方式"] = re.sub("\s*///\s*", "\n", get)

    info["圣遗物故事"] = {}
    parts = [p.text.strip() for p in soup.find_all("div", class_="up")]

    for j, s in enumerate(soup.find_all("div", class_="story")):
        story = s.text.strip()
        story += "\n" + s.find_next("div", class_="item").text.strip()
        info["圣遗物故事"][parts[j]] = story

    info["推荐"] = []
    rec = soup.find("div", class_="recommended")
    for title in rec.find_all("div", class_="title"):
        if title.text.strip() == "推荐角色":
            continue
        item = title.find_next("div", class_="item")
        rec_text = title.text.strip() + "\n" + item.text.strip()
        if rec_text not in info["推荐"]:
            info["推荐"].append(rec_text)

    return info


def parse_npc_list(route="/ys/NPC%E5%9B%BE%E9%89%B4"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    npcs = list(soup.find_all("div", class_="giconCard"))
    for s in tqdm(npcs):
        npc = s.find_all("a")[-1]
        results[npc.text.strip()] = parse_npc(npc["href"])
        print(results[npc.text.strip()])
    return results


def parse_npc(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}

    e = soup.find("div", class_="npcMainRight")
    info["姓名"] = e.find("div", class_="npcName").text.strip()
    info["昵称"] = e.find("div", class_="npcNick").text.strip()
    info["地点"] = e.find("div", class_="npcAddress").text.strip()
    table = e.find("table", class_='npcInfor')
    if table:
        info["信息"] = {}
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            title = tds[0].text.strip()
            content = tds[1].text.strip()
            if title == "对话赠礼":
                try:
                    content = tr.find('a')["title"] + re.sub("\s", "", content)
                except:
                    print()
            info["信息"][title] = content
    npc = soup.find(id="npcTalk")
    info["对话"] = parse_conversation(npc)

    info["待机语音"] = []
    for table in soup.find_all("table", class_="npcStandVoiceList"):
        for tr in table.find_all("tr")[1:]:
            if isinstance(tr, element.NavigableString) or "待机语音" in tr.text:
                continue
            content = tr.find("td").text.strip()
            if content:
                info["待机语音"].append(content)

    info["相关剧情&任务"] = []
    for task in soup.find_all("div", class_="npcTask"):
        info["相关剧情&任务"].append(task.text.strip())
    return info


def parse_plotbox(plotbox):
    plots = []
    for i, plot in enumerate(plotbox.find_all("div", class_="npcPlotSelect")):
        option_beginnings = plot.find_all("div", class_="npcPlot")
        option_contents = plot.find_next_siblings("div")
        try:
            assert len(option_beginnings) == len(option_contents)
            options = {}
            for j, (begin, content) in enumerate(zip(option_beginnings, option_contents)):
                begin = re.sub("Media[:a-zA-Z]+", "", begin.get_text())
                content = re.sub("Media[:a-zA-Z]+", "", content.get_text())
                option = "\n".join([begin, content])
                options[f"对话分支{i+1}-{j+1}"] = option
            plots.append(options)
        except AssertionError:
            if option_contents[0].text.strip() == "":
                plots.append(f"对话选项：" + "".join([f"{k+1}）{b.text.strip()}" for k, b in enumerate(option_beginnings)]))
            else:
                print("warning: error when parsing npc plots")
    return plots


def parse_conversation(soup):
    cur_string_span = ""
    conversation = {}
    for talkbox in soup.find_all("div", class_="npcTalkBox"):
        plotframe = talkbox.find('div', class_='npcPlotFrame')
        title = plotframe.find('div', class_="npcSmallTitle")
        title_str = title.text.strip()
        conversation[title.text.strip()] = []
        for e in title.next_siblings:
            if isinstance(e, element.NavigableString):
                cur_string_span += e if not re.search("[a-zA-Z.]+", e) else ""
            elif e.name != "div":
                cur_string_span += e.get_text() if not re.search("[a-zA-Z.]+", e.get_text()) else ""
            else:
                if cur_string_span.strip():
                    conversation[title_str].append(cur_string_span.strip())
                cur_string_span = ""
                parsed_plot = parse_plotbox(e)
                if parsed_plot:
                    conversation[title_str].append(parsed_plot)
        if cur_string_span.strip():
            conversation[title_str].append(cur_string_span.strip())
    return conversation


def parse_food_list(route="/ys/%E9%A3%9F%E7%89%A9%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    rarity = headers.index("稀有度")
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            if rarity == j:
                cell = cell.find('img')["alt"].split(".")[0]
            else:
                cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)
        name = cells[0]
        if name not in results:
            results[name] = {"basic": {}, "detail": {}}
        for header, cell in zip(headers, cells):
            results[name]["basic"][header] = cell
        link = row.find("a")
        if link:
            detail = parse_food(link["href"])
            results[name]["detail"] = detail
        print(name, results[name])
    return results


def parse_food(route):
    if "index.php" in route:
        return {}
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for headline in soup.find_all("span", class_="mw-headline"):
        headline_str = headline.text.strip()
        info[headline_str] = {}
        table = headline.find_next("table", class_="wikitable")
        if not table:
            continue
        if table.has_attr("style") and "display:none" in table["style"]:
            continue
        for row in table.find_all("tr"):
            try:
                headers = []
                for h in row.find_all("th"):
                    if h.has_attr("style") and "display:none" in h["style"]:
                        continue
                    header = h.text.split("Media")[0].strip()
                    if header:
                        headers.append(header)
                if not headers:
                    continue
                header = " - ".join(headers)
                if header == "稀有度":
                    content = row.find('img')["alt"].split(".")[0]
                else:
                    content = row.find("td").text.strip().replace("\xa0", " ")
                if content and "文件:" not in content and content != "'":
                    info[headline_str][header] = content
            except:
                continue

    if "基本信息" in info and "同类素材" in info['基本信息']:
        del info['基本信息']["同类素材"]
    return info


def parse_material_list(route="/ys/%E6%9D%90%E6%96%99%E5%9B%BE%E9%89%B4"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    materials = soup.find_all('div', class_="ys-iconLarge")
    for material in tqdm(materials):
        try:
            link = material.find("a")
            data = parse_food(link["href"])
            if data:
                results[link["title"]] = data
                print(link["title"], data)
        except:
            print(traceback.format_exc())
    return results


def parse_item_list(route="/ys/%E9%81%93%E5%85%B7%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    rarity = headers.index("稀有度")
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            if rarity == j:
                cell = cell.find('img')["alt"].split(".")[0]
            else:
                cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)
        name = cells[0]
        if name not in results:
            results[name] = {"basic": {}, "detail": {}}
        for header, cell in zip(headers, cells):
            results[name]["basic"][header] = cell
        link = row.find("a")
        if link:
            detail = parse_food(link["href"])
            if detail:
                results[name]["detail"] = detail
        print(results[name])
    return results


def parse_furniture(route="/ys/%E6%91%86%E8%AE%BE%E4%B8%80%E8%A7%88"):
    # todo
    pass


def parse_furniture_suite_list(route="/ys/摆设套装一览"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)
        name = cells[0]
        if name not in results:
            results[name] = {"basic": {}, "detail": {}}
        for header, cell in zip(headers, cells):
            results[name]["basic"][header] = cell
        link = row.find("a")
        if link:
            detail = parse_food(link["href"])
            if detail:
                results[name]["detail"] = detail
        print(results[name])
    return results


def parse_task_item(route="/ys/%E4%BB%BB%E5%8A%A1%E9%81%93%E5%85%B7%E4%B8%80%E8%A7%88"):
    # todo
    pass


def parse_geography_list(route="/ys/%E5%9C%B0%E7%90%86%E5%BF%97"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for area in soup.find('span', class_="mw-headline").find_next("div").find_all('a'):
        title, href = area["title"], area["href"]
        results[title] = parse_geography(href)
        print(results[title])
    return results


def parse_geography(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for box in soup.find_all("div", class_="showOnBox"):
        name = box.find("div", class_="showOn").text.strip()
        desc = box.find("div", class_="showOnText").text.strip()
        info[name] = desc
    return info


def parse_archon_quest_list(route="/ys/%E9%AD%94%E7%A5%9E%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for task in soup.find_all("div", class_="taskIcon"):
        info = task.find("a")
        title, href = info["title"], info["href"]
        results[title] = parse_common_quest(href)
        print(results[title])
    return results


def parse_plot(sibling):
    text = ""
    option_beginnings = sibling.find_all("div", class_="plotOptions")
    option_contents = sibling.find_all("div", class_="content")
    if len(option_contents) >= len(option_beginnings):
        for j, (begin, contents) in enumerate(zip(option_beginnings, option_contents)):
            text += f"剧情选项{j+1}：{begin.text.strip()}\n{contents.text.strip()}\n"
    else:
        for j, option in enumerate(option_beginnings):
            text += f"剧情选项{j+1}：{option.text.strip()}"
        for content in option_contents:
            text += f"{content}\n"
    return text


def parse_common_quest(route, level="h2", add_asterisk=True):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    quest = {}

    for head in soup.find('div', id="mw-content-text").find_all(level):
        if not head.find("span"):
            continue

        title = head.text.strip()
        quest[title] = []
        for node in head.find_next_siblings():
            if node.name == level:
                break
            content = parse_node(node, add_asterisk)
            if content:
                quest[title].append(content)

        quest[title] = "\n".join(quest[title])
        quest[title] = re.sub("(分支对话|动画剧情)", "", quest[title])
        quest[title] = re.sub("\n+", "\n", quest[title])
        quest[title] = re.sub(" ", "", quest[title])
        quest[title] = quest[title].replace("\xa0", "")
        quest[title] = re.sub("请上传文件.+", "", quest[title])
    return quest


def parse_node(node, add_asterisk=False):
    text = ""
    # todo: tabbertab
    if node.name == "div" and not node.has_attr("class"):
        text = node.text.strip()
    elif node.name == "div" and "tabbertab" in node["class"]:
        print()

    elif node.name == "div" and re.search("(plotFrame|plotBox|foldFrame)", str(node["class"])):
        if len(node.find_all("div", "plotBox")) <= 1:
            text = parse_plot(node)
        else:
            for child in node.findChildren(recursive=False):
                content = parse_node(child)
                text += content.strip() + "\n"
    elif node.name == "div" and "foldExplain" in node["class"]:
        return ""
    elif node.name == "h2":
        return f"\n={node.text.strip()}="
    elif node.name == "h3" or node.name == "blockquote" or "color:#b18300" in node.prettify():
        text = ""
        for line in node.text.split("\n"):
            if line.strip():
                if add_asterisk:
                    text += f"*{line.strip()}*\n"
                else:
                    text += f"{line.strip()}\n"
        text = text.strip()
    else:
        text = node.text.strip()

    if re.search("(相关攻略|参考链接|原神WIKI导航)", text):
        return ""
    if re.search("(请上传文件|www\.|文件:|https:|max-width|toclevel|Media)", text):
        return ""
    return text


def parse_legend_quest_list(route="/ys/%E4%BC%A0%E8%AF%B4%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for task in soup.find_all("div", class_="taskIcon"):
        info = task.find("a")
        title, href = info["title"], info["href"]
        if title not in results and re.search("第.+幕", title):
            try:
                data = parse_legend_quest(href)
                if data:
                    results[title] = data
                    print(results[title])
            except:
                continue
    return results


def parse_legend_quest(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for hint in soup.find_all("div", class_="tishi"):
        hint = hint.find("a")
        href, title = hint["href"], hint["title"]
        try:
            info[title] = parse_common_quest(href)
        except:
            print(title, traceback.format_exc())
            continue
    return info


def parse_world_quest_list(route="/ys/%E4%B8%96%E7%95%8C%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    tasks = list(soup.find_all("span", class_="home-an1"))
    for task in tqdm(tasks):
        info = task.find("a")
        title, href = info["title"], info["href"]
        data = parse_world_quest(href)
        if data:
            results[title] = data
            print(results[title])
    return results


def parse_world_quest(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    table = soup.find("table", class_="wikitable")
    if table:
        info["信息"] = parse_table(table)

    story = parse_common_quest(route)
    if story:
        info["剧情"] = story
    return info


def parse_commission_quest_list(route="/ys/%E5%A7%94%E6%89%98%E4%BB%BB%E5%8A%A1"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    output = []
    tasks = list(soup.find_all("div", class_="tishi"))
    for task in tqdm(tasks):
        try:
            info = task.find("a")
            title, href = info["title"], info["href"]
            if re.search("[a-zA-Z]", title):
                continue
            data = parse_common_quest(href)
            if data:
                output.append({"title": title, "content": data})
                print({"title": title, "content": data})
        except:
            print(traceback.format_exc())
    return output


def parse_birthday_email_list(route="/ys/邮件"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')]
    for row in rows[1:]:
        cells = [re.sub(r"(^图)*\s+", " ", cell.get_text()).strip() for cell in row.find_all('td')]
        info = {}
        for header, cell in zip(headers, cells):
            if cell:
                if header == "奖励":
                    cell = cell.split("【")[0]

                info[header] = cell.strip()
            else:
                if header == "发件人" and row["data-param1"]:
                    info[header] = row["data-param1"]
        results.append(info)
    return results


def parse_monster_list(route="/ys/%E6%80%AA%E7%89%A9%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)

        link = row.find("a")
        if "index.php" in link["href"]:
            continue

        name = cells[0]
        if name not in results:
            results[name] = {"basic": {}, "detail": {}}
        for header, cell in zip(headers, cells):
            if cell:
                results[name]["basic"][header] = cell

        data = parse_monster(link["href"])
        if data:
            results[name]["detail"] = data
        print(results[name])
    return results


def parse_monster(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for h2 in soup.find_all('h2', {"id": False, "class": False}):
        title = h2.text.strip()
        # only get textual info
        if title in {"基本信息", "相关攻略", "参考链接", "特别提醒"}:
            continue
        info[title] = {}
        data = []
        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break
            elif sibling.name == "div" and sibling.has_attr("class") and "m-skill-bg" in sibling["class"]:
                skill_name = sibling.find("div", class_="m-skill-title-1").text.strip()
                skill_desc = ""
                for subsection in sibling.find_all("span", class_="m-skill-p"):
                    content = ""
                    for s in subsection.next_siblings:
                        if s.name == "span" and s.has_attr("class"):
                            break
                        if s.text.strip():
                            content += f"{s.text.strip()}"
                    if content.strip():
                        content = f"{subsection.text.strip()}: {content.strip()}"
                        skill_desc += f"{content}\n"
                if skill_name:
                    skill_desc = f"技能名称：{skill_name}\n{skill_desc.strip()}"
                desc = skill_desc
            else:
                desc = sibling.text.strip()
            if not re.search("http", desc) and desc.strip():
                data.append(desc)
        if data:
            if len(data) == 1:
                data = data[0]
            info[title] = data
    return info


def parse_animal_list(route="/ys/%E9%87%8E%E7%94%9F%E7%94%9F%E7%89%A9%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)

        name = cells[0]
        if name not in results:
            results[name] = {}
        for header, cell in zip(headers, cells):
            if cell:
                results[name][header] = cell
        print(results[name])
    return results


def parse_tcg(route="/ys/%E4%B8%83%E5%9C%A3%E5%8F%AC%E5%94%A4"):
    info = parse_common_quest(route)
    return info


def parse_tcg_card_list(route="/ys/%E5%8D%A1%E7%89%8C%E5%9B%BE%E9%89%B4"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    table = soup.find("table", {"id": "CardSelectTr"})
    rows = table.find_all('tr')
    header_row = rows[0]
    headers = [header.text.strip() for header in header_row.find_all('th')][1:]
    for row in tqdm(rows[1:]):
        cells = []
        for j, cell in enumerate(row.find_all('td')[1:]):
            cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
            cells.append(cell)

        link = row.find("a")
        if "index.php" in link["href"]:
            continue

        name = cells[0]
        if name not in results:
            results[name] = {"basic": {}, "detail": {}}
        for header, cell in zip(headers, cells):
            if cell:
                results[name]["basic"][header] = cell

        data = parse_tcg_card(link["href"])
        if data:
            results[name]["detail"] = data
        print(results[name])
    return results


def parse_tcg_card(route):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    data = []
    for row in soup.find_all("div", class_="flex-row"):
        if "cost-box" in row["class"]:
            continue
        if "jiNeng" in row["class"]:
            for tag in row.find_all(class_='cost'):
                tag.decompose()
        data.append(row.text.strip())
    info["详细信息"] = data
    return info


def parse_argot(route="/ys/%E9%BB%91%E8%AF%9D"):
    info = parse_common_quest(route)
    return info


def parse_tips(route="/ys/%E8%BF%87%E5%9C%BA%E6%8F%90%E7%A4%BA"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for table in tqdm(soup.find_all("table", class_="wikitable")):
        title = table.find_previous("span", class_="mw-headline").text.strip()
        results[title] = []
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = []
            for j, cell in enumerate(row.find_all('td')):
                cell = re.sub(r"(^图)*\s+", " ", cell.get_text()).strip()
                cells.append(cell)
            if len(cells) > 3:
                cells = [cells[0], cells[-2]]
            results[title].append("：".join(cells))
    return results


def parse_book_list(route="/ys/%E4%B9%A6%E7%B1%8D%E4%B8%80%E8%A7%88"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for a in soup.find("div", class_="tishi").find_all_next("a")[1:]:
        try:
            href, title = a["href"], a["title"]
            if title in info:
                continue
            info[title] = parse_common_quest(href)
            print(info[title])
        except:
            pass
    return info


def parse_achievement_list(route="/ys/%E6%88%90%E5%B0%B1%E7%B3%BB%E7%BB%9F"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    for a in soup.find_all("div", class_="acBox"):
        a = a.find("a")
        info[a["title"]] = parse_achievement(a["href"])
        print(info[a["title"]])
    return info


def parse_achievement(route):
    info = parse_common_quest(route, level="h2", add_asterisk=False)
    if not info:
        info = parse_common_quest(route, level="h3", add_asterisk=False)
    return info


def parse_library(route="/ys/%E5%8C%97%E9%99%86%E5%9B%BE%E4%B9%A6%E9%A6%86"):
    html = load_html_by_route(route)
    soup = BeautifulSoup(html, 'html.parser')
    results = {}
    for i, menu in enumerate(soup.find_all("div", class_="menu")):
        menu_str = menu.text.strip()
        results[menu_str] = {}
        # parse menu
        if i:
            menu_html = load_html_by_route(menu.find("a")["href"])
            menu_soup = BeautifulSoup(menu_html, 'html.parser')
        else:
            menu_soup = soup
        for sub_menu in menu_soup.find_all("div", class_="ct"):
            sub_menu_str = sub_menu.text.strip()
            href = sub_menu.find("a")["href"]
            if "index.php" in href:
                continue
            data = parse_common_quest(href, add_asterisk=False)
            if not data:
                data = parse_common_quest(sub_menu.find("a")["href"], level="h3", add_asterisk=False)
            if data:
                results[menu_str][sub_menu_str] = data
                print(results[menu_str][sub_menu_str])
    return results


if __name__ == '__main__':
    # parse main page
    # parse_main_page()

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    output_config = {
        "角色图鉴": {
            "角色一览.json": parse_character_list,
            "角色语音.json": parse_character_voices,
            "角色装扮.json": parse_character_outfits,
        },
        "装备图鉴": {
            "武器一览.json": parse_weapon_list,
            "圣遗物一览.json": parse_relic_list,
        },
        "物品一览": {
            "食物一览.json": parse_food_list,
            "材料一览.json": parse_material_list,
            "道具一览.json": parse_item_list,
            "摆设套装一览.json": parse_furniture_suite_list,
        },
        "七圣召唤": {
            "七圣召唤.json": parse_tcg,
            "卡牌一览.json": parse_tcg_card_list,
        },
        "生物志": {
            "怪物一览.json": parse_monster_list,
            "野生生物一览.json": parse_animal_list,
            "地理志一览.json": parse_geography_list,
            "NPC图鉴.json": parse_npc_list,
        },
        "书籍一览": {
            "书籍一览.json": parse_book_list,
        },
        "成就一览": {
            "成就一览.json": parse_achievement_list,
        },
        "任务": {
            "魔神任务.json": parse_archon_quest_list,
            "传说任务.json": parse_legend_quest_list,
            "世界任务.json": parse_world_quest_list,
            "委托任务.json": parse_commission_quest_list,
        },
        "邮件": {
            "生日邮件.json": parse_birthday_email_list,
        },
        "扩展阅读": {
            "北陆图书馆.json": parse_library,
            "过场提示.json": parse_tips,
            "黑话.json": parse_argot,
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
