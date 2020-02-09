#!/usr/bin/env python3
import json
import os
import random
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv
from requests.compat import urljoin, urlparse
from requests.exceptions import ConnectionError, HTTPError

DEFAULT_CHUNK_SIZE = 1024
FILES_FOLDER = "images"

XKCD_COMICS_URL = "http://xkcd.com/{comic_number}/info.0.json"
XKCD_CURRENT_URL = "https://xkcd.com/info.0.json"

VK_API_VERSION = "5.103"
VK_API_METHODS_BASE_URL = "https://api.vk.com/method/"
VK_MY_COMMUNITY_ID = 166256394


def get_url_filename(url=""):
    """Извлекает имя файла картинки с расширением из урла."""
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


def download_image(url="", img_path="", img_name="", rewrite=True):
    """Функция для скачивания файла изображения
    по заданному url и сохранения по заданному пути."""

    os.makedirs(img_path, exist_ok=True)

    file_name = os.path.join(img_path, img_name)
    path = Path(file_name)

    if not rewrite and path.is_file():
        return

    response = requests.get(
        url=url, stream=True, verify=False
    )
    response.raise_for_status()
    try:
        with open(file_name, 'wb') as file:
            for chunk in response.iter_content(DEFAULT_CHUNK_SIZE):
                file.write(chunk)
                # raise ValueError
    except IOError as error:
        exit("Ошибка записи файла\n{0}\n}".format(error))
    # finally:
        # os.remove(file_name)
    return file_name


def get_wall_upload_url(vk_group_id=None, access_token=""):
    """Получение ссылки для загрузки фото на сервер ВК
    для последующей публикации на стену группы."""
    api_method_name = "photos.getWallUploadServer"

    params = {
        "group_id": vk_group_id,

        "access_token": access_token,
        "v": VK_API_VERSION,
    }
    response = requests.get(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        params=params,
    )
    response.raise_for_status()

    return response.json()["response"]["upload_url"]


def upload_image_vk(img_path="", url=""):
    """Загрузка фото на заданный url. Возвращает данные о загрузке."""
    with open(img_path, "rb") as image_file:
        files = {
            "photo": image_file
        }
        response = requests.post(url=url, files=files)
        response.raise_for_status()
        return response.json()


def save_wall_photo(upload_response=None, access_token=""):
    """Сохранение загруженного фото для публикации на стене.
    Возвращает данные о сохранении."""
    api_method_name = "photos.saveWallPhoto"

    params = {
        "group_id": VK_MY_COMMUNITY_ID,
        "photo": upload_response["photo"],
        "server": upload_response["server"],
        "hash": upload_response["hash"],

        "access_token": access_token,
        "v": VK_API_VERSION,
    }
    response = requests.post(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        data=params,
    )
    response.raise_for_status()
    return response.json()


def post_wall_photo(save_image_response=None, message="", access_token=""):
    """Публикация фото на стене группы."""
    api_method_name = "wall.post"
    resp = save_image_response["response"][0]

    attachment_str = "".join([
        "photo", str(resp["owner_id"]), "_", str(resp["id"])
    ])
    params = {
        "owner_id": -VK_MY_COMMUNITY_ID,
        "from_group": 1,
        "message": message,
        "attachments": attachment_str,
        "group_id": VK_MY_COMMUNITY_ID,

        "access_token": access_token,
        "v": VK_API_VERSION,
    }
    response = requests.post(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        data=params,
    )
    response.raise_for_status()
    return response.json()


def download_random_comics():
    curr_comics_resp = requests.get(
        url=XKCD_CURRENT_URL
    )
    curr_comics_resp.raise_for_status()

    curr_comics_num = curr_comics_resp.json()["num"]
    random_comics_num = random.randint(1, curr_comics_num)

    url = XKCD_COMICS_URL.format(comic_number=random_comics_num)

    resp = requests.get(url=url)
    resp.raise_for_status()
    
    comics_data = resp.json()
    comic_comment = comics_data["alt"]
    img_url = comics_data["img"]
    comic_img_name = get_url_filename(img_url)

    img_path = download_image(
        url=img_url,
        img_path=FILES_FOLDER,
        img_name=comic_img_name
    )

    return {
        "img_path": img_path,
        "comment": comic_comment,
    }


def main():
    access_token = os.getenv("VK_APP_ACCESS_TOKEN")
    try:
        photo_path, message = download_random_comics().values()

        upload_url = get_wall_upload_url(
            vk_group_id=VK_MY_COMMUNITY_ID,
            access_token=access_token
        )
        upload_response_data = upload_image_vk(
            img_path=photo_path, url=upload_url
        )

        save_resp = save_wall_photo(
            upload_response=upload_response_data,
            access_token=access_token
        )
        post_resp = post_wall_photo(
            save_image_response=save_resp,
            message=message,
            access_token=access_token
        )
        os.remove(photo_path)

    except HTTPError as error:
        exit("Невозможно получить данные с сервера:\n{0}\n".format(error))

    except ConnectionError as error:
        exit("Проблема с сетевым соединением:\n{0}\n".format(error))


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    main()
