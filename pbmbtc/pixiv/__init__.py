from .cookie import cookie_verify
from .download import ugoira_download, image_download
from .metadata import get_ugoira_meta, get_pages, get_illust_meta
from .bookmarks import get_bookmarks
from .user_illusts import get_user_illusts
from .utils import compress_frame_2, get_tags, get_image_format, delete_files_in_folder
from typing import List, Dict
import os
from io import BytesIO
from zipfile import ZipFile
import logging
import math
import asyncio
import aiofiles

# 其实对于get请求和ffmpeg生成gif应该定义为协程的,但是...能跑就行,有机会再改改
# 没有协程的问题只在于在更新和备份时bot会无响应)
# 并不打算使用协程提高api请求速率,并发太高怕被ban

logger = logging.getLogger("pixiv")


# 获取ugoira的zip打包文件 文件名 控制参数
async def get_ugoira(pid, u_cookie) -> Dict:
    logger.debug(f"ugoira: pid: {pid}")
    ugoira_meta = await get_ugoira_meta(pid, u_cookie)
    ugoira = await ugoira_download(ugoira_meta["originalSrc"])
    file_name = ugoira_meta["originalSrc"].rsplit("/", 1)[-1]

    return {"file": ugoira, "file_name": file_name, "meta": ugoira_meta}


# tmp_path内不要存放任何有价值文件
# tmp_path不要用/结尾
async def get_ugoira_gif(file: bytes, meta, tmp_path, max_size=1024 * 1024 * 50) -> bytes:
    logger.debug(f"ugoira gif")
    # imageio方案放弃,生成gif动图大小比ffmpeg大且帧率无法完全控制
    # zip_buffer = BytesIO(file)
    #
    # with ZipFile(zip_buffer, "r") as f:
    #     images_list = f.namelist()
    #     images_list = sorted(images_list, key=lambda x: int(x.split(".", 1)[0]))
    #
    #     images = [f.read(i) for i in images_list]
    #
    # frames = [imageio.v2.imread(BytesIO(i)) for i in images]
    # output = BytesIO()
    #
    # imageio.v2.mimsave(output, frames, format='GIF', duration=meta['frames'][0]['delay'] / 1000.0, loop=0)
    #
    # return output.getvalue()

    # 创建文件夹及清理tmp_path
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    delete_files_in_folder(tmp_path)

    zip_file = BytesIO(file)

    # 解压
    with ZipFile(zip_file, "r") as f:
        frames_name = f.namelist()
        f.extractall(tmp_path)
        logger.debug(f"ugoira gif: unzip, file size: {len(frames_name)}")

    # 对宽高限制和比例限制进行判断
    compress_frame_2(frames_name, tmp_path, 1)

    # gif参数
    gif_fps = 1000 / meta["frames"][0]["delay"]
    gif_file_name = "tmp.gif"
    gif_frame_extension = meta["frames"][0]["file"].rsplit(".", 1)[1]
    gif_frame_name_length = len(meta["frames"][0]["file"].split(".", 1)[0])

    logger.debug(f"ugoira gif: fps: {gif_fps}, extension: {gif_frame_extension}, name_length: {gif_frame_name_length}")

    # ffmpeg生成gif
    process = await asyncio.create_subprocess_shell(
        f"ffmpeg -framerate {gif_fps} -i {tmp_path}/%0{gif_frame_name_length}d.{gif_frame_extension} -vf \"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse\" {os.path.join(tmp_path, gif_file_name)}"
        , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(
            f"stdout: {stdout.decode('utf-8')}\n--------------------------\nstderr: {stderr.decode('utf-8')}")

    async with aiofiles.open(os.path.join(tmp_path, gif_file_name), "rb") as f:
        gif = await f.read()

    # 压缩
    if len(gif) >= max_size:
        logger.debug(f"ugoira gif: gif size > max_size, gif size: {len(gif)}, max_size: {max_size}")
        rate = math.sqrt(max_size / len(gif)) * 0.95  # 计算压缩图像的比例
        del gif
        compress_frame_2(frames_name, tmp_path, rate)
        os.remove(os.path.join(tmp_path, gif_file_name))

        logger.debug("ugoira gif: regenerate gif...")

        # 重新生成
        process = await asyncio.create_subprocess_shell(
            f"ffmpeg -framerate {gif_fps} -i {tmp_path}/%0{gif_frame_name_length}d.{gif_frame_extension} -vf \"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse\" {os.path.join(tmp_path, gif_file_name)}"
            , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(
                f"stdout: {stdout.decode('utf-8')}\n--------------------------\nstderr: {stderr.decode('utf-8')}")

        async with aiofiles.open(os.path.join(tmp_path, gif_file_name), "rb") as f:
            gif = await f.read()

    logger.debug(f"ugoira gif: return, gif size: {len(gif)}")
    return gif


# 不仅可以用于插画和漫画 也可以用于动图,可以作为动图预览
async def get_illust(pid, u_cookie) -> List[Dict]:
    logger.debug(f"illust: pid: {pid}")

    pages = await get_pages(pid, u_cookie)

    logger.debug(f"illust: pages: {len(pages)}")

    # 保存所有图片
    illust = []
    for page in pages:
        url = page["urls"]["original"]
        file = await image_download(url)
        file_name = url.rsplit("/", 1)[-1]
        illust.append({"file_name": file_name, "file": file})

    return illust


async def get_manga(pid, u_cookie) -> List[Dict]:
    logger.debug("manga: get manga")
    return await get_illust(pid, u_cookie)


def get_novel() -> List[bytes]:
    pass
