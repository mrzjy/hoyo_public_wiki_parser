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

- Get or Update posts (dynamics) from Hoyoverse's official accounts

~~~
# cd to this sub-directory
cd public_social_media/bilibili

# run script (.bat is for running in Windows)
./scripts/update_dynamics.bat
~~~

The scripts tries to download all posts/dynamics up to date in data/{game} folder, resulting in a dynamics.jsonl file.

The second time you run the script, it will only download new posts that does not exist in your previous dynamics.jsonl, and store them in .cache folder. Then it'll merge the existing and new ones, thus finish the updating process.

- Get or Update comments (WIP)