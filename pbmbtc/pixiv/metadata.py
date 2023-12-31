# import requests
import httpx
import json
import copy
import logging

logger = logging.getLogger("metadata")
logger.setLevel(logging.DEBUG)


# 通用header
header = {
    "cookie": "",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
    "referer": "",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    # "accept-encoding": "gzip, deflate, br, zstd",
    "accept": "application/json"
}

referer = "https://www.pixiv.net/artworks/{}"


# 获取动图数据
async def get_ugoira_meta(pid: str, cookie: str):
    logger.debug(f"ugoira meta: pid: {pid}")

    h = copy.deepcopy(header)
    h["cookie"] = cookie
    h["referer"] = referer.format(pid)

    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.pixiv.net/ajax/illust/{}/ugoira_meta".format(pid), headers=h)
    if response.status_code != 200:
        raise Exception(f"Get ugoira meta: Error status code: {response.status_code}")
    json_data = json.loads(response.content.decode("utf-8"))
    if json_data["error"]:
        raise Exception("Get ugoira meta: " + json_data["message"])

    return json_data["body"]


# 获取作品数据
async def get_illust_meta(pid: str, cookie: str):
    logger.debug(f"illust meta: pid: {pid}")

    h = copy.deepcopy(header)
    h["cookie"] = cookie
    h["referer"] = referer.format(pid)

    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.pixiv.net/ajax/illust/" + pid, headers=h)
    if response.status_code != 200:
        raise Exception(f"Get illust meta: Error status code: {response.status_code}")
    json_data = json.loads(response.content.decode("utf-8"))
    if json_data["error"]:
        raise Exception("Get illust meta: " + json_data["message"])

    return json_data["body"]


async def get_pages(pid: str, cookie: str):
    logger.debug(f"pages meta(for illust): pid: {pid}")

    h = copy.deepcopy(header)
    h["referer"] = referer.format(pid)
    h["cookie"] = cookie

    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.pixiv.net/ajax/illust/{}/pages".format(pid), headers=h)
    if response.status_code != 200:
        raise Exception(f"Get page: Error status code: {response.status_code}")
    pages_json = json.loads(response.content.decode("utf-8"))
    if pages_json["error"]:
        raise Exception("Get page: " + pages_json["message"])

    return pages_json["body"]


