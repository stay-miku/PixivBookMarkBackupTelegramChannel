import os
import shutil
from typing import List
from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger("pixiv utils")


def get_image_format(byte_data):
    if byte_data.startswith(b'\x89PNG'):
        return 'png'
    elif byte_data.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif byte_data.startswith(b'\x47\x49'):
        return 'gif'
    elif byte_data.startswith(b'\x42\x4D'):
        return 'bmp'
    elif byte_data.startswith(b'\x00\x00\x01\x00\x01'):
        return 'ico'
    else:
        raise Exception("unknown image file format")


def delete_files_in_folder(folder_path):
    logger.debug(f"delete: {folder_path}")

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def get_tags(meta):
    tag_list = meta["tags"]["tags"]
    tags = {}
    for tag in tag_list:
        if "translation" in tag:
            translation = []
            for t in list(tag["translation"].keys()):
                translation.append(tag["translation"][t])
            tags[tag['tag']] = translation
        else:
            tags[tag['tag']] = ''
    return tags


def crop_image(image_bytes):
    image = Image.open(BytesIO(image_bytes))

    # 对于图像宽高比例超过1:10或10:1的处理            tg限制
    width, height = image.width, image.height
    if width / height >= 10:
        crop_width = 9 * height
        left = (width - crop_width) / 2
        image = image.crop((int(left), 0, int(left + crop_width), height))
    elif height / width >= 10:
        crop_height = 9 * width
        upper = (height - crop_height) / 2
        image = image.crop((0, int(upper), width, int(upper + crop_height)))
    else:
        return image_bytes

    image_format = get_image_format(image_bytes)

    tmp = BytesIO()
    image.save(tmp, image_format)
    return tmp.getvalue()


def compress_image(image_bytes, compression_ratio):
    if compression_ratio >= 1:
        return image_bytes

    image = Image.open(BytesIO(image_bytes))

    image_format = get_image_format(image_bytes)

    # 新大小
    new_width = int(image.width * compression_ratio)
    new_height = int(image.height * compression_ratio)
    resized_image = image.resize((int(new_width), int(new_height)))

    output = BytesIO()
    resized_image.save(output, image_format)
    compressed_bytes = output.getvalue()
    output.close()

    return compressed_bytes


# 压缩gif帧,tg限制api发送文件最大大小为50MB
# 好像没用,但还是留着吧
def compress_frame(frames: List[List], max_size=1024*1024*50) -> List[List]:
    image = Image.open(BytesIO(frames[0][1]))
    if image.width / image.height >= 10 or image.height / image.width >= 10:
        frames = [[i[0], crop_image(i[1])] for i in frames]

    file_size = sum([len(i[1]) for i in frames])

    if not file_size >= max_size:
        return frames

    image = Image.open(BytesIO(frames[0][1]))
    if not image.width + image.height >= 10000:
        return frames

    ratio = min(max_size / file_size, 10000 / (image.width + image.height))

    return [[i[0], compress_image(i[1], ratio)] for i in frames]


def crop_image_2(file_path, crop_size):
    image = Image.open(file_path)

    crop = image.crop(crop_size)

    crop.save(file_path)


def compress_image_2(file_path, rate):
    image = Image.open(file_path)
    new_width = int(image.width * rate)
    new_height = int(image.height * rate)
    resize = image.resize((new_width, new_height))
    resize.save(file_path)


# rate >= 1为检查宽高比例和像素和大小 rate < 1为压缩图像
def compress_frame_2(file_list: List[str], path, rate):
    image = Image.open(os.path.join(path, file_list[0]))
    if rate >= 1 and image.width / image.height >= 10:
        logger.debug(f"compress frame 2: crop frame due to width/height rate > 10")
        crop_width = image.height * 9
        crop = (image.width - crop_width) / 2
        crop_size = (int(crop), 0, int(crop_width + crop), image.height)
        for i in file_list:
            crop_image_2(os.path.join(path, i), crop_size)

    elif rate >= 1 and image.height / image.width >= 10:
        logger.debug(f"compress frame 2: crop frame due to height/width rate > 10")
        crop_height = image.width * 9
        crop = (image.height - crop_height) / 2
        crop_size = (0, int(crop), image.width, int(crop + crop_height))
        for i in file_list:
            crop_image_2(os.path.join(path, i), crop_size)

    if rate >= 1 and image.width + image.height >= 10000:
        r = 10000.0 / (image.width + image.height)

        logger.debug(f"compress frame 2: resize frame due to width + height > 10000, rate: {r}")
        for i in file_list:
            compress_image_2(os.path.join(path, i), r)

    if rate >= 1:
        return
    else:
        logger.debug(f"compress frame 2: resize frame, rate: {rate}")
        for i in file_list:
            compress_image_2(os.path.join(path, i), rate)


