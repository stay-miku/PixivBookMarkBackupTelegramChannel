from .cookie import *
from .download import *
from .metadata import *
from .bookmarks import *
from .user_illusts import *
from typing import List, Dict
import imageio
from io import BytesIO
from zipfile import ZipFile


def get_ugoira(pid, u_cookie) -> Dict:
    ugoira_meta = get_ugoira_meta(pid, u_cookie)
    ugoira = ugoira_download(ugoira_meta["originalSrc"])
    file_name = ugoira_meta["originalSrc"].rsplit("/", 1)[1]

    return {"file": ugoira, "file_name": file_name, "meta": ugoira_meta}


def get_ugoira_gif(file: bytes, meta) -> bytes:
    zip_buffer = BytesIO(file)

    with ZipFile(zip_buffer, "r") as f:
        images_list = f.namelist()
        images_list = sorted(images_list, key=lambda x: int(x.split(".", 1)[0]))

        images = [f.read(i) for i in images_list]

    frames = [imageio.v2.imread(BytesIO(i)) for i in images]
    output = BytesIO()

    imageio.v2.mimsave(output, frames, format='GIF', fps=1000.0 / meta['frames'][0]['delay'], loop=0)

    return output.getvalue()


def get_illust(pid, u_cookie) -> List[Dict]:
    pages = get_pages(pid, u_cookie)

    # 保存所有图片
    illust = []
    for page in pages:
        url = page["urls"]["original"]
        file = image_download(url)
        file_name = url.rsplit("/", 1)[1]
        illust.append({"file_name": file_name, "file": file})

    return illust


def get_manga(pid, u_cookie) -> List[Dict]:
    return get_illust(pid, u_cookie)


def get_novel() -> List[bytes]:
    pass


def get_work() -> List[bytes]:
    pass

