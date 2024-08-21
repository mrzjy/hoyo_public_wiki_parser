import argparse
import asyncio
import json
import random
import sqlite3
import traceback

from bilibili_api.comment import OrderType, CommentResourceType, get_comments
from tqdm import tqdm
from bilibili_api import settings
from utils.private import credential
from utils.common import map_uid_to_title


# add proxy if you have
# settings.proxy = "http://localhost:10809"

MAX_PAGE_NUM = 10

parser = argparse.ArgumentParser()
parser.add_argument('--uid', default="401742377", help="uid", choices=list(map_uid_to_title.keys()))
args = parser.parse_args()

db_name = f".db/{map_uid_to_title[args.uid]}.db"
directory = f"data/{map_uid_to_title[args.uid]}"


async def main():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
CREATE TABLE IF NOT EXISTS comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    d_id INTEGER KEY,
    c_id INTEGER KEY,
    json TEXT NOT NULL
)
''')
    print("reading previous comments...")
    cursor.execute('SELECT d_id FROM comment')
    dynamics_already_parsed = set([result[0] for result in cursor.fetchall()])
    cursor.execute('SELECT id, json FROM dynamic')
    all_dynamics = cursor.fetchall()
    dynamics_to_be_parsed = [d[1] for d in all_dynamics if d[0] not in dynamics_already_parsed]

    for i, dynamic in enumerate(dynamics_to_be_parsed):
        dynamic = json.loads(dynamic)
        dynamic_id = dynamic["desc"]["dynamic_id"]
        comments = []
        # 当前已获取数量
        count = 0
        oid = dynamic_id
        type_ = CommentResourceType.DYNAMIC
        max_page_num = MAX_PAGE_NUM
        if dynamic["desc"].get("bvid"):
            oid = dynamic["card"]["aid"]
            type_ = CommentResourceType.VIDEO
            max_page_num = MAX_PAGE_NUM * 2
        pbar = tqdm(range(1, max_page_num+1), position=0, leave=True)
        for page in pbar:
            # 获取评论
            try:
                res = await get_comments(
                    oid=oid,
                    type_=type_,
                    page_index=page,
                    order=OrderType.LIKE,
                    credential=credential,
                )
                # 存储评论
                if res['page']['size'] == 0:
                    break
                comments.extend(res["replies"])
            except:
                try:
                    res = await get_comments(
                        oid=dynamic["desc"]["rid"],
                        type_=CommentResourceType.DYNAMIC_DRAW,
                        page_index=page,
                        order=OrderType.LIKE,
                        credential=credential,
                    )
                    # 存储评论
                    if res['page']['size'] == 0:
                        break
                    comments.extend(res["replies"])
                except:
                    print(traceback.format_exc())
                    print(f"failed dynamic_id: {dynamic_id}")
                    break

            for comment in comments:
                cursor.execute(
                    'INSERT INTO comment (d_id, c_id, json) VALUES (?, ?, ?)',
                    (dynamic_id, comment["rpid"], json.dumps(comment))
                )
            conn.commit()

            pbar.set_description(desc=f"{i}/{len(dynamics_to_be_parsed)}")
            pbar.set_postfix(n_comments=len(comments))

            try:
                # 增加已获取数量
                count += res['page']['size']
                if count >= res['page']['count']:
                    # 当前已获取数量已达到评论总数，跳出循环
                    break
            except:
                print(traceback.format_exc())
                break
            await asyncio.sleep(random.random() * 2.5)
    print("--------已完成！---------")


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
