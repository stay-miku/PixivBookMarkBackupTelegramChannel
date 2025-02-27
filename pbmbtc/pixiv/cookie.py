# import requests
import httpx
import json
from lxml import etree
import logging

logger = logging.getLogger("cookie")
logger.setLevel(logging.DEBUG)


# 验证cookie可用性,可用会返回一个包含账号id和账号名的字典,否则抛出Exception
async def cookie_verify(cookie: str):
    header = {
        "cookie": cookie,
        "referer": "https://www.pixiv.net/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/111.0.0.0 Safari/537.36",
        "sec-fetch-dest": "document",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        # "accept-encoding": "gzip, deflate, br",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.pixiv.net/", headers=header)
    if response.status_code != 200:
        raise Exception(f"Cookie verify: Error status code{response.status_code}")
    http = response.content.decode("utf-8")
    content = etree.HTML(http).xpath("//script[@id=\"__NEXT_DATA__\"]/text()")
    preload_state = json.loads(content[0])["props"]["pageProps"]["serverSerializedPreloadedState"]
    user_data = json.loads(preload_state)["userData"]["self"]
    if user_data is None:
        return None
    logger.debug(f"userId: {user_data['id']}, userName: {user_data['pixivId']}")
    return {"userId": user_data["id"], "userName": user_data["pixivId"]}

