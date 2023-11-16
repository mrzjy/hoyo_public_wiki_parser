import json
import re
import pandas as pd
import wikitextparser as wtp


df = pd.read_excel("html_entities.xlsx")
map_html_codes_to_symbol = {
    row["Entity Name"]: row["Symbol"] if not pd.isna(row["Symbol"]) else "" for _, row in df.iterrows()
}


def text_normalization(content: str) -> str:
    # replace all html entities
    for entity in re.findall("&[a-zA-Z0-9]+;", content):
        if entity in map_html_codes_to_symbol:
            content = content.replace(entity, map_html_codes_to_symbol[entity])
    # remove html tags
    content = re.sub(r"\s*<br />\s*", " ", content)
    content = re.sub(r"<[^>]+>", "", content)

    return content


def find_page_by_title(title: str, pages: list[dict]) -> dict:
    for page in pages:
        if page["title"] == title:
            return page
    return {}


def remove_wikitext_format(string: str) -> str:
    # in case there is nested templates
    while re.search(r"\{\{[^}]+}}", string):
        string = re.sub(r"\{\{[^}]+}}", "", string)
    while re.search(r"\[\[[^}]+]]", string):
        string = re.sub(r"\[\[[^]]+]]", "", string)
    while re.search(r"<!--[^>]+-->", string):
        string = re.sub(r"<!--[^>]+-->", "", string)

    string = re.sub(r"\'\'\'*", "", string)
    return string.strip()


def get_character_infobox(character_name: str, page: dict) -> dict[str, dict]:
    parsed = wtp.parse(page["content"])
    for template in parsed.templates:
        if "Character Infobox" in template.name:
            return parse_character_infobox(template)
    return None


def parse_character_infobox(template) -> dict[str, str]:
    character_info = {}
    for argument in template.arguments:
        if argument.name.strip() == "quality":
            character_info["quality"] = argument.value.strip()
        elif argument.name.strip() == "weapon":
            character_info["weapon"] = argument.value.strip()
        elif argument.name.strip() == "element":
            character_info["element"] = argument.value.strip()
        elif argument.name.strip() == "birthday":
            character_info["birthday"] = argument.value.strip()
        elif argument.name.strip() == "constellation":
            character_info["constellation"] = argument.value.strip()
        elif argument.name.strip() == "region":
            character_info["region"] = argument.value.strip()
        elif "affiliation" in argument.name:
            character_info[argument.name.strip()] = argument.value.strip()
        elif argument.name.strip() == "dish":
            character_info["dish"] = argument.value.strip()
        elif argument.name.strip() == "namecard":
            character_info["namecard"] = argument.value.strip()
        elif "title" in argument.name:
            character_info[argument.name.strip()] = argument.value.strip()
    output = {k: remove_wikitext_format(v) for k, v in character_info.items()}
    return {k: v for k, v in output.items() if v}


def get_character_lore(character_name, page: dict) -> dict[str, dict]:
    lore_dict = {}
    parsed = wtp.parse(page["content"])
    for i, section in enumerate(parsed.sections):
        # quote
        if i == 0:
            for template in section.templates:
                if template.name.strip().lower() == "quote":
                    for argument in template.arguments:
                        lore_dict["quote"] = remove_wikitext_format(argument.value.strip())
                        break
        # personality
        if section.title == "Personality":
            content = section.contents
            for template in section.templates:
                if template.name.strip().lower() == "quote":
                    content = content.replace(template.string, template.arguments[0].value)
                    break

            # TOdo: youtube ref ...
            lore_dict["Personality"] = remove_wikitext_format(content)

        # appearance

        # story

        # trivial
    assert len(lore_dict["quote"])
    assert len(lore_dict["Personality"])
    return lore_dict


def parse_dialogue_paragraph(character_name, paragraph, add_speaker=True):
    """In wikitext format,
        the colon (:) is used to indent text and create nested lists.
        The semicolon (;) is used to create a definition list in wikitext format.
    """
    clean_paragraph = ""
    for line in paragraph.strip().split("\n"):
        m = re.match(r"^(?P<colon>[:;]+)\s*(?P<content>.+)$", line.strip())
        if m:
            colon, content = m["colon"], m["content"].strip()
            if colon == ";":
                clean_line = content
            else:
                indent = "\t" * (colon.count(":") - 1) + "- "
                if add_speaker:
                    clean_line = indent + f"{character_name}: {content}"
                else:
                    clean_line = indent + f"{content}"
            clean_paragraph += f"{clean_line}\n"
    return clean_paragraph


def clean_idle_quotes(character_name, raw_content):
    paragraph = remove_wikitext_format(raw_content)
    clean_paragraph = parse_dialogue_paragraph(character_name, paragraph)
    return clean_paragraph


def clean_companion_dialogue(character_name, raw_content):
    paragraph = re.sub(r"(\'\'\'|<[^>]+>)", "", raw_content)
    paragraph = re.sub(r"\{\{DIcon.*}}:*\s*", "Traveler: ", paragraph)
    paragraph = re.sub(r"\(Traveler\)", "Traveler", paragraph)
    paragraph = remove_wikitext_format(paragraph)
    clean_paragraph = parse_dialogue_paragraph(character_name, paragraph, add_speaker=False)
    return clean_paragraph


def get_character_voice_overs(character_name: str, page: dict) -> dict[str, dict]:
    voice_overs_dict = {"Story": {}, "Combat VO": {}}
    tmp_map_vo_id_to_intent = {}
    parsed = wtp.parse(page["content"])
    possible_kwargs = {"name": character_name, "character": character_name}
    for template in parsed.templates:
        # there are 2 parts of Voice-Overs
        if "VO/Story" in template.name.strip():
            for argument in template.arguments:
                if argument.name.strip().endswith("_title"):
                    title = argument.name.strip().split("_title")[0]
                    tmp_map_vo_id_to_intent[title] = argument.value
                elif argument.name.strip().endswith("_tx"):
                    title = argument.name.strip().split("_tx")[0]
                    intention = tmp_map_vo_id_to_intent[title].strip().format(**possible_kwargs)
                    intention = remove_wikitext_format(intention)
                    value = remove_wikitext_format(argument.value.strip().format(**possible_kwargs))
                    voice_overs_dict["Story"][intention] = value
        elif template.name.strip() == "Combat VO":
            for argument in template.arguments:
                if argument.name.strip().endswith("tx"):
                    title = argument.name.strip().split("_tx")[0].strip().format(**possible_kwargs)
                    title = remove_wikitext_format(title)
                    value = remove_wikitext_format(argument.value.strip().format(**possible_kwargs))
                    voice_overs_dict["Combat VO"][title] = value
    return voice_overs_dict


def get_character_companion_dialogue(character_name: str, page: dict) -> dict[str, str]:
    companion_dict = {"Idle Quotes": "", "Dialogue": "", "Special Dialogue": {}}
    parsed = wtp.parse(page["content"])
    for section in parsed.sections:
        if section.title == "Idle Quotes":
            companion_dict["Idle Quotes"] = clean_idle_quotes(character_name, section.contents)
        elif section.title == "Dialogue":
            companion_dict["Dialogue"] = clean_companion_dialogue(character_name, section.contents)
        elif section.title == "Special Dialogue":
            # we'll use the nested parsed structure
            for sub_section in section.sections:
                # avoid endless loop
                if sub_section.title is None or sub_section.title == section.title:
                    continue
                companion_dict["Special Dialogue"][sub_section.title] = clean_companion_dialogue(character_name, sub_section.contents)
    return companion_dict


if __name__ == '__main__':
    map_character_to_info = {}
    pages = []
    with open(".cache/raw_data.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            if page["content"] is None:
                continue
            page["content"] = text_normalization(page["content"])
            pages.append(page)

            # find all playable characters
            # todo: better place to find all characters? (tried "playable character" page, but no info is provided in that page ...)
            if page["title"].endswith("/Companion"):
                if re.search("^#redirect \[\[[^]]+/companion]]", page["content"].lower()):
                    continue
                character_name = page["title"].split("/Companion")[0]
                if character_name in {"Companion", "Paimon"}:
                    continue
                map_character_to_info[character_name] = {}

    # get all character info
    for character_name in map_character_to_info:
        # get infobox
        relevant_page = find_page_by_title(f"{character_name}", pages)
        assert relevant_page
        map_character_to_info[character_name]["infobox"] = get_character_infobox(character_name, relevant_page)

        # get character lore
        relevant_page = find_page_by_title(f"{character_name}/Lore", pages)
        assert relevant_page
        map_character_to_info[character_name]["lore"] = get_character_lore(character_name, relevant_page)

        # get voice overs
        relevant_page = find_page_by_title(f"{character_name}/Voice-Overs", pages)
        assert relevant_page
        map_character_to_info[character_name]["voice_overs"] = get_character_voice_overs(character_name, relevant_page)

        # get companion voice
        relevant_page = find_page_by_title(f"{character_name}/Companion", pages)
        assert relevant_page
        map_character_to_info[character_name]["companion"] = get_character_companion_dialogue(character_name, relevant_page)

    with open("data/character.json", "w", encoding="utf-8") as f:
        json.dump(map_character_to_info, f, ensure_ascii=False, indent=4)
