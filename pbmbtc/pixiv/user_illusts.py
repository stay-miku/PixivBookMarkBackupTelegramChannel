import requests
import json
import logging

logger = logging.getLogger("user_illust")
logger.setLevel(logging.DEBUG)


def get_user_illusts(pid: str, cookie: str):
    logger.debug(f"pid: {pid}")

    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "referer": "https://www.pixiv.net/users/{}/artworks".format(pid),
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "cookie": cookie
    }

    url = "https://www.pixiv.net/ajax/user/{}/profile/all?lang=zh".format(pid)

    response = requests.get(url, headers=header)
    if response.status_code != 200:
        raise Exception(f"Get user illusts: Error status code: {response.status_code}")
    response_json = json.loads(response.content.decode("utf-8"))
    r = []
    if response_json["error"]:
        raise Exception("Get page: " + response_json["message"])
    # 当对应的类型没有作品时,其为list,否则为dict
    if isinstance(response_json["body"]["illusts"], dict):
        r += list(response_json["body"]["illusts"].keys())
    if isinstance(response_json["body"]["manga"], dict):
        r += list(response_json["body"]["manga"].keys())

    return r
