import os
from pathlib import Path

import requests


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
