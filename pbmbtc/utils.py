from PIL import Image
import io
import math
import logging
import time
import traceback
from typing import Callable, Dict, List
import asyncio

logger = logging.getLogger("utils")


# 和pixiv/utils里的一模一样
def get_image_format(byte_data):
    if byte_data.startswith(b'\x89PNG'):
        return 'png'
    elif byte_data.startswith(b'\xff\xd8'):
        return 'jpg'
    elif byte_data.startswith(b'\x47\x49'):
        return 'gif'
    elif byte_data.startswith(b'\x42\x4D'):
        return 'bmp'
    elif byte_data.startswith(b'\x00\x00\x01\x00\x01'):
        return 'ico'
    else:
        raise Exception("unknown image file format")


# 与pixiv/utils里的不一样
def compress_image(image_bytes, max_size=1024*1024*10):
    logger.debug(f"compress image: max_size: {max_size}")
    image = Image.open(io.BytesIO(image_bytes))

    image_format = get_image_format(image_bytes)

    # 对于图像宽高比例超过1:10或10:1的处理            tg限制
    width, height = image.width, image.height
    crop = False
    if width / height >= 10:
        logger.debug(f"compress image: crop: width: {width}, height: {height}")
        crop_width = 9 * height
        left = (width - crop_width) / 2
        image = image.crop((int(left), 0, int(left + crop_width), height))
        crop = True
    elif height / width >= 10:
        logger.debug(f"compress image: crop: width: {width}, height: {height}")
        crop_height = 9 * width
        upper = (height - crop_height) / 2
        image = image.crop((0, int(upper), width, int(upper + crop_height)))
        crop = True

    # 图片是否大于最大大小                            tg限制
    if len(image_bytes) >= max_size:
        compression_ratio = math.sqrt(max_size / len(image_bytes)) * 0.95
    # 图片是否大于最大宽高和                           tg限制
    elif (image.width + image.height) >= 10000:
        compression_ratio = 10000 / (image.width + image.height)
    else:
        logger.debug("don't need compress")
        if not crop:
            return image_bytes, False
        else:
            tmp = io.BytesIO()
            image.save(tmp, image_format)
            return tmp.getvalue(), False

    logger.debug(f"compress image: compress rate: {compression_ratio}")
    # 新大小
    new_width = int(image.width * compression_ratio)
    new_height = int(image.height * compression_ratio)
    resized_image = image.resize((int(new_width), int(new_height)))

    output = io.BytesIO()
    resized_image.save(output, image_format)
    compressed_bytes = output.getvalue()
    output.close()

    logger.debug(f"compress image: new image size: {len(compressed_bytes)}")

    # 防止一次压缩无法满足限制(当然一般情况没问题)
    return compressed_bytes, len(compressed_bytes) >= max_size or resized_image.height + resized_image.width >= 10000


def compress_image_if_needed(image_bytes, max_size=1024*1024*10):
    result = True
    while result:
        logger.debug("compress if need")
        image_bytes, result = compress_image(image_bytes, max_size)

    return image_bytes


async def retry(func: Callable, retry_max_attempts: int, retry_delay: int, **kwargs):
    attempt = 1
    while attempt <= retry_max_attempts:
        try:
            result = await func(**kwargs)
            return result
        except Exception as e:
            traceback.print_exception(e)
            logger.warning(f"An exception occurred while running {func.__name__}: {e}, retry after {retry_delay}, retry: {attempt}, max_attempts: {retry_max_attempts}")
            attempt += 1
            await asyncio.sleep(retry_delay)

    raise Exception(
        f"Attempting to run {func.__name__} exceeded the maximum number of retries: {retry_max_attempts}")


def format_tags(tags: Dict[str, List]):
    t = []
    for key in list(tags.keys()):
        t.append(key + '=>' + '=>'.join(tags[key]))

    return '\n'.join(t)

