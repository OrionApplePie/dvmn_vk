#!/usr/bin/env python3
import os
from pathlib import Path

import requests
from requests.compat import urlparse

DEFAULT_CHUNK_SIZE = 1024
FILES_FOLDER = "images"


def download_image(url="", img_path="", img_name="", rewrite=True):
    """Function for downloading image by given url
    and saving it to given folder."""

    os.makedirs(img_path, exist_ok=True)

    file_name = os.path.join(img_path, img_name)
    path = Path(file_name)

    # если есть опция перезаписи и если уже есть такой файл, то не скачиваем
    if not rewrite and path.is_file():
        return

    response = requests.get(
        url=url, stream=True, verify=False
    )
    response.raise_for_status()

    with open(file_name, 'wb') as file:
        for chunk in response.iter_content(DEFAULT_CHUNK_SIZE):
            file.write(chunk)
    return file_name


def get_url_filename(url=""):
    """Извлекает имя файла картинки с расширением из урла."""
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


def main():
    base_url = "http://xkcd.com/{comic_number}/info.0.json"
    url = base_url.format(comic_number=614)

    r = requests.get(url=url)
    r.raise_for_status()
    r_json = r.json()

    comic_comment = r_json["alt"]
    print(comic_comment)

    img_url = r_json["img"]
    comic_img_name = get_url_filename(img_url)

    img_path = download_image(
        url=img_url,
        img_path=FILES_FOLDER,
        img_name=comic_img_name
    )


if __name__ == "__main__":
    main()
