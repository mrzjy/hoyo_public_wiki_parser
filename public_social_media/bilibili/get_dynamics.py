import asyncio
import datetime
import json
import os
import argparse
import aiohttp
from bilibili_api import user
from utils.common import map_uid_to_title


"""
Code reference: https://github.com/Starrah/BilibiliGetDynamics
"""

print("Available uids:")
print(json.dumps(map_uid_to_title, ensure_ascii=False, indent=4))


parser = argparse.ArgumentParser()
parser.add_argument('--uid', default="27534330", help="uid", choices=list(map_uid_to_title.keys()))
parser.add_argument('--no_download', action="store_true", help="同时下载动态中的图片")
parser.add_argument('--full_json', action="store_true", help="输出动态完整数据")
args = parser.parse_args()
args.no_download = True
args.full_json = True

u = user.User(uid=int(args.uid))

cache_dir = f".cache/{map_uid_to_title[args.uid]}"
directory = f"data/{map_uid_to_title[args.uid]}"
pic_directory = f"{directory}/pics"


async def fetch(session: aiohttp.ClientSession, url: str, path: str):
    try:
        async with session.get(url) as resp:
            with open(path, 'wb') as fd:
                while 1:
                    chunk = await resp.content.read(1024)  # 每次获取1024字节
                    if not chunk:
                        break
                    fd.write(chunk)
        # print("downloaded " + url)
    except:
        print("failed " + url)


def copyKeys(src, keys):
    res = {}
    for k in keys:
        if k in src:
            res[k] = src[k]
    return res


def getItem(input):
    if "item" in input:
        return getItem(input["item"])
    if "videos" in input:
        return getVideoItem(input)
    else:
        return getNormal(input)


def getNormal(input):
    res = copyKeys(input, ['description', 'pictures', 'content'])
    if "pictures" in res:
        res["pictures"] = [pic["img_src"] for pic in res["pictures"]]
    return res


def getVideoItem(input):
    res = copyKeys(input, ['title', 'desc', 'dynamic', 'short_link', 'stat', 'tname'])
    res["av"] = input["aid"]
    res["pictures"] = [input["pic"]]
    return res


def cardToObj(input):
    res = {
        "dynamic_id": input["desc"]["dynamic_id"],
        "timestamp": input["desc"]["timestamp"],
        "type": input["desc"]["type"],
        "item": getItem(input["card"])
    }
    if "origin" in input["card"]:
        originObj = json.loads(input["card"]["origin"])
        res["origin"] = getItem(originObj)
        if "user" in originObj and "name" in originObj["user"]:
            res["origin_user"] = originObj["user"]["name"]
    return res


async def main():
    os.makedirs(directory, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    existing_dynamic_ids = set()
    if os.path.exists(f"{directory}/dynamics.jsonl"):
        with open(f'{directory}/dynamics.jsonl', "r", encoding="UTF-8") as f:
            for line in f:
                dynamic = json.loads(line)
                existing_dynamic_ids.add(dynamic["desc"]["dynamic_id"])

    with open(f'{cache_dir}/dynamics.jsonl', "w", encoding="UTF-8") as f:
        offset = 0
        count = 0
        if not args.no_download:
            os.makedirs("pics", exist_ok=True)
        early_break = False
        while True:
            if count % 10 == 0:
                print(count)
            res = await u.get_dynamics(offset)
            if res["has_more"] != 1:
                break
            offset = res["next_offset"]
            for card in res["cards"]:
                cardObj = cardToObj(card)
                if not args.no_download:
                    tasks = []
                    async with aiohttp.ClientSession() as session:
                        if "pictures" in cardObj["item"]:
                            for pic_url in cardObj["item"]["pictures"]:
                                task = fetch(session, pic_url, os.path.join(pic_directory, os.path.basename(pic_url)))
                                tasks.append(task)
                            await asyncio.gather(*tasks)
                data = cardObj if not args.full_json else card
                if data["desc"]["dynamic_id"] in existing_dynamic_ids:
                    early_break = True
                    break
                print(json.dumps(data, ensure_ascii=False), file=f)
                count += 1
                print(count)
            if early_break:
                print("early break")
                break
            await asyncio.sleep(1)
    print()
    print("--------已完成！---------")


def update_merge():
    if os.path.exists(f"{cache_dir}/dynamics.jsonl"):
        with open(f'{cache_dir}/dynamics.jsonl', "r", encoding="UTF-8") as f:
            new_dynamics = [json.loads(line) for line in f]
    else:
        print(f"No new dynamics found in {cache_dir}/dynamics.jsonl. No need to merge.")
        return

    existing_dynamics = []
    existing_dynamic_ids = set()
    if os.path.exists(f"{directory}/dynamics.jsonl"):
        with open(f'{directory}/dynamics.jsonl', "r", encoding="UTF-8") as f:
            for line in f:
                dynamic = json.loads(line)
                existing_dynamics.append(dynamic)
                existing_dynamic_ids.add(dynamic["desc"]["dynamic_id"])

    update_dynamics = existing_dynamics
    for new_dynamic in new_dynamics:
        if new_dynamic["desc"]["dynamic_id"] not in existing_dynamic_ids:
            update_dynamics.insert(0, new_dynamic)
    with open(f'{directory}/dynamics.jsonl', "w", encoding="UTF-8") as f:
        for dynamic in update_dynamics:
            print(json.dumps(dynamic, ensure_ascii=False), file=f)
    print(f"--------{directory}/dynamics.jsonl 已更新！---------")

    newest_dynamic = update_dynamics[0]
    date = datetime.datetime.fromtimestamp(newest_dynamic["desc"]["timestamp"]).date()

    print(f"{len(existing_dynamics)} dynamics -> {len(update_dynamics)} dynamics")
    print(f"up tp date: {date}")
    os.remove(f"{cache_dir}/dynamics.jsonl")


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
    update_merge()
