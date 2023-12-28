# BiliBili

This directory parses Hoyoverse-related social media content from BiliBili, such as posts, comments, etc.

### Supported Account
| Game               | Account Name                                        |
|--------------------|-----------------------------------------------------|
| Genshin Impact     | [原神](https://space.bilibili.com/401742377)          |
| Honkai: Star Rail  | [崩坏星穹铁道](https://space.bilibili.com/1340190821/)    |
| Honkai Impact 3rd  | [崩坏3第一偶像爱酱](https://space.bilibili.com/27534330/)   |
| Honkai Academy 2nd | [崩坏学园2-灵依娘desu](https://space.bilibili.com/133934/) |
| Tears of themis    | [未定事件簿](https://space.bilibili.com/436175352/)      |

### Steps

- Fill your credential info by creating a "private.py" in the utils folder

~~~private.py
from bilibili_api import Credential

credential = Credential(
    sessdata="your_sessdata",
    bili_jct="your_bili_jct",
    buvid3="your buvid3",
)
~~~

Please refer to [this manual](https://nemo2011.github.io/bilibili-api/#/get-credential) to find your corresponding information 

1. Get or Update posts (dynamics) from Hoyoverse's official accounts

~~~
# cd to this sub-directory
cd public_social_media/bilibili

# run script (.bat is for running in Windows)
./scripts/update_dynamics.bat
~~~

The scripts tries to download all posts/dynamics up to date in data/{game} folder, resulting in a dynamics.jsonl file.

The second time you run the script, it will only download new posts that does not exist in your previous dynamics.jsonl, and store them in .cache folder. Then it'll merge the existing and new ones, thus finish the updating process.

2. Get or Update raw comments (WIP)

(Note that some posts have disabled comment section)

3. Process and generate final comment session data

Here's an example of what it'll look like (Please see [sample.json](data/sample.json) for a full sample)

~~~
{
    "replies": [
        {
            "replies": null,
            "content": "西班牙风格可能会在纳塔那边看到",
            "role": "user_13",
            "like": 42
        },
        {
            "replies": null,
            "content": "西班牙响板",
            "role": "user_14",
            "sex": "男",
            "like": 22
        },
        {
            "replies": null,
            "content": "枫丹包括西班牙哦",
            "role": "user_15",
            "like": 11
        }
    ],
    "content": "南欧的音乐风格，有意大利黑手党的感觉，伊比利亚半岛风情音乐!",
    "role": "user_12",
    "like": 1922
}
~~~

- Anonymization

We do not want to retain any specific user account info (e.g., names), so we simply mask most user names in the structured data, including the "role" field and "回复 @some_name :" reply pattern, for example:

~~~
{"replies": null, "content": "比起衣服，帝君更希望璃月人民幸福安康，包括你，亲爱的旅行者⊙ω⊙", "role": "user_1008", "like": 2}
~~~

The "user_1008" is a masked user name replacing the real user name.

However, be aware that there are still "@some_name" content in the data, where some users are specifically mentioned. for example:

> @原神 老米呀老米，明年可就 ...

> 这个up @some_name 已经发了三个私服爆料视频 ...

For now, we leave such content as is.