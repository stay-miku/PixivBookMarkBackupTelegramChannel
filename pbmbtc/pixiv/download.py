# import requests
import httpx
import copy
import logging

logger = logging.getLogger("download")
logger.setLevel(logging.DEBUG)


header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) C"
                  "hrome/111.0.0.0 Safari/537.36",
    "referer": "https://www.pixiv.net/",
    "sec-fetch-dest": "image",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    # "accept-encoding": "gzip, deflate, br",
    "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

timeout = httpx.Timeout(timeout=60)


# 图片的bytes,需自行根据链接判断图片格式
async def image_download(url: str) -> bytes:
    logger.debug(f"image download: url: {url}")
    # 不管怎么样把看起来比较有用的都塞进去~
    h = copy.deepcopy(header)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=h, timeout=timeout)
    if response.status_code != 200:
        raise Exception(f"Image download: Error status code: {response.status_code}")

    return response.content


# 按理返回的是一个压缩包,需要后续处理
async def ugoira_download(url: str) -> bytes:
    logger.debug(f"ugoira download: url: {url}")

    h = copy.deepcopy(header)
    h["origin"] = "https://www.pixiv.net"
    h["sec-fetch-dest"] = "empty"
    h["accept"] = "*/*"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=h, timeout=timeout)
    if response.status_code != 200:
        raise Exception(f"Download ugoira: Error status code: {response.status_code}")

    return response.content

