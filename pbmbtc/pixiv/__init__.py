from .cookie import cookie_verify
from .download import ugoira_download, image_download
from .metadata import get_ugoira_meta, get_pages, get_illust_meta
from .bookmarks import get_bookmarks
from .user_illusts import get_user_illusts
from .utils import compress_frame_2, get_tags, get_image_format, delete_files_in_folder
from typing import List, Dict
import os
from io import BytesIO
import subprocess
from zipfile import ZipFile
import logging
import math

logger = logging.getLogger("pixiv")


# 获取ugoira的zip打包文件 文件名 控制参数
def get_ugoira(pid, u_cookie) -> Dict:
    logger.debug(f"ugoira: pid: {pid}")
    ugoira_meta = get_ugoira_meta(pid, u_cookie)
    ugoira = ugoira_download(ugoira_meta["originalSrc"])
    file_name = ugoira_meta["originalSrc"].rsplit("/", 1)[1]

    return {"file": ugoira, "file_name": file_name, "meta": ugoira_meta}


# tmp_path内不要存放任何有价值文件
# tmp_path不要用/结尾
def get_ugoira_gif(file: bytes, meta, tmp_path, max_size=1024*1024*50) -> bytes:
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
    result = subprocess.run(f"ffmpeg -framerate {gif_fps} -i {tmp_path}/%0{gif_frame_name_length}d.{gif_frame_extension} -vf \"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse\" {os.path.join(tmp_path, gif_file_name)}"
                            , stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    if result.returncode != 0:
        raise Exception(f"stdout: {result.stdout.decode('utf-8')}\n--------------------------\nstderr: {result.stderr.decode('utf-8')}")

    with open(os.path.join(tmp_path, gif_file_name), "rb") as f:
        gif = f.read()

    if len(gif) >= max_size:
        logger.debug(f"ugoira gif: gif size > max_size, gif size: {len(gif)}, max_size: {max_size}")
        rate = math.sqrt(max_size / len(gif)) * 0.95            # 计算压缩图像的比例
        del gif
        compress_frame_2(frames_name, tmp_path, rate)
        os.remove(os.path.join(tmp_path, gif_file_name))

        logger.debug("ugoira gif: regenerate gif...")

        # 重新生成
        result = subprocess.run(
            f"ffmpeg -framerate {gif_fps} -i {tmp_path}/%0{gif_frame_name_length}d.{gif_frame_extension} -vf \"split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse\" {os.path.join(tmp_path, gif_file_name)}"
            , stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        if result.returncode != 0:
            raise Exception(
                f"stdout: {result.stdout.decode('utf-8')}\n--------------------------\nstderr: {result.stderr.decode('utf-8')}")

        with open(os.path.join(tmp_path, gif_file_name), "rb") as f:
            gif = f.read()

    logger.debug(f"ugoira gif: return, gif size: {len(gif)}")
    return gif


def get_illust(pid, u_cookie) -> List[Dict]:
    logger.debug(f"illust: pid: {pid}")

    pages = get_pages(pid, u_cookie)

    logger.debug(f"illust: pages: {len(pages)}")

    # 保存所有图片
    illust = []
    for page in pages:
        url = page["urls"]["original"]
        file = image_download(url)
        file_name = url.rsplit("/", 1)[1]
        illust.append({"file_name": file_name, "file": file})

    return illust


def get_manga(pid, u_cookie) -> List[Dict]:
    logger.debug("manga: get manga")
    return get_illust(pid, u_cookie)


def get_novel() -> List[bytes]:
    pass


def get_work() -> List[bytes]:
    pass

