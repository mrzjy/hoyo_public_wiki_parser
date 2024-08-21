import asyncio
import datetime
import json
import os
import argparse
import sqlite3

import aiohttp
from bilibili_api import user
from utils.common import map_uid_to_title
from utils.private import credential


"""
Code reference: https://github.com/Starrah/BilibiliGetDynamics
"""

# print("Available uids:")
# print(json.dumps(map_uid_to_title, ensure_ascii=False, indent=4))


parser = argparse.ArgumentParser()
parser.add_argument('--uid', default="401742377", help="uid", choices=list(map_uid_to_title.keys()))
args = parser.parse_args()

u = user.User(uid=int(args.uid), credential=credential)

os.makedirs(".db", exist_ok=True)
db_name = f".db/{map_uid_to_title[args.uid]}.db"
# pic_directory = f".db/{map_uid_to_title[args.uid]}/pics"


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


async def main():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dynamic (
        id INTEGER PRIMARY KEY,
        time INTEGER KEY,
        json TEXT NOT NULL
    )
    ''')

    cursor.execute('SELECT id FROM dynamic')
    existing_dynamic_ids = set([result[0] for result in cursor.fetchall()])
    cursor.execute('SELECT time FROM dynamic')
    previous_times = [result[0] for result in cursor.fetchall()]
    previous_times.sort()
    prev_date = "None"
    if previous_times:
        prev_date = datetime.datetime.fromtimestamp(previous_times[-1]).date()
        print(f"Already stored: {len(existing_dynamic_ids)} dynamics until {prev_date}")

    offset = 0
    count = 0
    early_break = False
    while True:
        if count % 10 == 0:
            print(count)
        try:
            res = await u.get_dynamics(offset)
        except:
            await asyncio.sleep(3)
            res = await u.get_dynamics(offset)
        if res["has_more"] != 1:
            break
        offset = res["next_offset"]
        for card in res["cards"]:
            # if card["desc"]["dynamic_id"] == 884110427985805319:
            #     early_break = True
            #     break
            if card["desc"]["dynamic_id"] in existing_dynamic_ids:
                early_break = True
                break
            cursor.execute(
                'INSERT INTO dynamic (id, time, json) VALUES (?, ?, ?)',
                (card["desc"]['dynamic_id'], card["desc"]["timestamp"], json.dumps(card, ensure_ascii=False))
            )
            conn.commit()
            count += 1
            print(count)
        if early_break:
            print("early break")
            break
        await asyncio.sleep(3)

    print("--------已完成！---------")
    cursor.execute('SELECT time FROM dynamic')
    update_times = [result[0] for result in cursor.fetchall()]
    update_times.sort()
    up_to_date = datetime.datetime.fromtimestamp(update_times[-1]).date()
    print(f"Finished Update: latest dynamic: {prev_date} -> {up_to_date}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
