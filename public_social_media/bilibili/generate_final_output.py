import argparse
import json
import os
import re
import sqlite3
import traceback
from multiprocessing import Pool

from tqdm import tqdm
from utils.common import map_uid_to_title

user_reply_pattern = re.compile(r"回复 @[^:]+ :")

parser = argparse.ArgumentParser()
parser.add_argument('--uid', default="1636034895", help="uid", choices=list(map_uid_to_title.keys()))
parser.add_argument('--min_like', default=100, type=int, help="min_likes")
parser.add_argument(
    "--output_json",
    action="store_true",
    help="whether to output in json, by default will output in db for updating convenience",
)
parser.add_argument(
    "--recreate",
    action="store_true",
    help="whether to recreate the output table in db",
)
args = parser.parse_args()
db_name = f".db/{map_uid_to_title[args.uid]}.db"
directory = f"data/{map_uid_to_title[args.uid]}"
os.makedirs(directory, exist_ok=True)

conn = sqlite3.connect(db_name)
cursor = conn.cursor()


def process_replies(nested_dict, mask_mid=None):
    if mask_mid is None:
        mask_mid = {}

    if isinstance(nested_dict, dict):
        mid = nested_dict.get("mid")
        if "replies" in nested_dict:
            if mid not in mask_mid:
                mask_mid[mid] = f"user_{len(mask_mid)}"
            content = nested_dict.get("content", {}).get("message", "")
            content = user_reply_pattern.sub("", content)
            like = nested_dict.get("like", 0)
            if like < args.min_like:
                return None
            d = {
                "content": content,
                "role": mask_mid[mid],
                "like": like,
            }
            if nested_dict.get("member", {}).get("sex") != "保密":
                d["sex"] = nested_dict["member"]["sex"]
            replies = process_replies(nested_dict["replies"], mask_mid)
            if replies:
                d["replies"] = replies
            if "pictures" in nested_dict:
                d["image"] = nested_dict["picture"]["img_src"]
            return d
        else:
            return {}
    elif isinstance(nested_dict, list):
        return [process_replies(item, mask_mid) for item in nested_dict if item]
    else:
        return nested_dict


def clean_up_dynamic(data):
    del data["desc"]["user_profile"]
    desc_keys = list(data["desc"].keys())
    for k in desc_keys:
        if str(data["desc"][k]) == "0":
            del data["desc"][k]
    return data


def query_comment(dynamic_id):
    query = "SELECT json FROM dynamic WHERE id = ?"
    cursor.execute(query, (dynamic_id,))
    dynamic = cursor.fetchone()
    if not dynamic:
        return None, None
    try:
        dynamic = json.loads(dynamic[0])
    except:
        print(traceback.format_exc())
        return None, None

    query = "SELECT json FROM comment WHERE d_id = ?"
    cursor.execute(query, (dynamic_id,))
    comments = [json.loads(row[0]) for row in cursor.fetchall()]
    return dynamic_id, dynamic, comments


def check_id_exists(id):
    # Execute a SELECT query to check if the ID exists
    cursor.execute("SELECT COUNT(*) FROM output WHERE dynamic_id = ?", (id,))
    result = cursor.fetchone()[0]
    # Return True if the ID exists, False otherwise
    return result > 0


def clean_up_comments(comments):
    new_comments = []
    for c in comments:
        if c:
            if c["like"] <= args.min_like:
                continue
            c["replies"] = [r for r in c.get("replies", []) if r and r["like"] >= args.min_like]
            new_comments.append(c)
    return new_comments


if __name__ == '__main__':
    if args.output_json:
        num_replies = 0
        cursor.execute("SELECT * FROM output")
        with open(f"{directory}/comments.jsonl", "w", encoding="utf-8") as f:
            for out in sorted(cursor.fetchall(), key=lambda x: x):
                _, dynamic, comments = out
                dynamic = json.loads(dynamic)
                comments = json.loads(comments)
                if dynamic is None or comments is None:
                    continue
                output_dict = {"dynamic": clean_up_dynamic(dynamic), "comments": clean_up_comments(comments)}
                num_replies += json.dumps(output_dict["comments"], ensure_ascii=False).count("content")
                print(json.dumps(output_dict, ensure_ascii=False), file=f)
            print("num_replies:", num_replies)
            exit()

    if args.recreate:
        cursor.execute("DROP TABLE IF EXISTS output")

    cursor.execute('''CREATE TABLE IF NOT EXISTS output (
dynamic_id INTEGER PRIMARY KEY AUTOINCREMENT,
dynamic TEXT NOT NULL,
comments TEXT NOT NULL
)''')

    mask_mid = {}
    num_comments = 0
    cursor.execute('SELECT d_id FROM comment')
    dynamic_ids = list(set(cursor.fetchall()))
    pbar = tqdm(dynamic_ids, desc="Writing comments")
    batch = []
    for dynamic_id in pbar:
        dynamic_id = dynamic_id[0]
        if check_id_exists(dynamic_id):
            continue
        batch.append(dynamic_id)
        if len(batch) >= 48 or dynamic_id == dynamic_ids[-1]:
            pool = Pool(8)
            batch_comments = pool.map(
                query_comment, batch
            )
            processed = pool.starmap(
                process_replies,
                [[b[-1], mask_mid] for b in batch_comments]
            )
            num_comments += sum([len(c) for c in processed if c])
            inserts = [[b[0], json.dumps(b[1]), json.dumps(p)] for b, p in zip(batch_comments, processed)]

            cursor.executemany(
                'INSERT INTO output (dynamic_id, dynamic, comments) VALUES (?, ?, ?)',
                inserts
            )
            conn.commit()
            batch = []
    pbar.close()

    print(f"Statistics:\nnum comment sessions: {num_comments}")
