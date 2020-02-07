#!/usr/bin/env python3
import json
import os
import random
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv
from requests.compat import urljoin, urlparse

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


def get_comm_vk():
    """Returns a list of the communities to which a user belongs using VK API."""
    api_method_name = "groups.get"
    access_token = os.getenv("VK_APP_ACCESS_TOKEN")

    params = {
        "extended": 1,
        "access_token": access_token,
        "v": "5.103",
    }
    comm_response = requests.get(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        params=params,
    )

    print(comm_response.json())


def get_wall_upload_url(vk_group_id=None):
    """Получение ссылки для загрузки фото на сервер ВК
    для последующей публикации на стену группы."""
    api_method_name = "photos.getWallUploadServer"
    access_token = os.getenv("VK_APP_ACCESS_TOKEN")

    params = {
        "group_id": vk_group_id,

        "access_token": access_token,
        "v": "5.103",
    }
    response = requests.get(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        params=params,
    )

    return response.json()["response"]["upload_url"]


def upload_image_vk(img="", url=""):
    """Загрузка фото на заданный урл."""
    with open(img, "rb") as image_file:
        files = {
            "photo": image_file
        }
        response = requests.post(url=url, files=files)
        response.raise_for_status()
        return response.json()


def save_wall_photo(upload_response=None):
    """Сохранение фото для публикации на стене."""
    api_method_name = "photos.saveWallPhoto"
    access_token = os.getenv("VK_APP_ACCESS_TOKEN")

    params = {
        "group_id": VK_MY_COMMUNITY_ID,
        "photo": upload_response["photo"],
        "server": upload_response["server"],
        "hash": upload_response["hash"],
        "caption": "test caption",
        "access_token": access_token,
        "v": "5.103",
    }
    response = requests.post(
        url=urljoin(VK_API_METHODS_BASE_URL, api_method_name),
        data=params,
    )
    response.raise_for_status()
    return response.json()


def post_wall_photo(save_image_response=None, message=""):
    """Публикация фото на стене группы."""
    api_method_name = "wall.post"
    access_token = os.getenv("VK_APP_ACCESS_TOKEN")
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
        "v": "5.103",
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
    
    resp_json = resp.json()
    comic_comment = resp_json["alt"]
    img_url = resp_json["img"]
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
    photo_path, message = download_random_comics().values()

    upload_url = get_wall_upload_url(vk_group_id=VK_MY_COMMUNITY_ID)
    print(f"upload url --> {upload_url}\n")

    upload_resp = upload_image_vk(photo_path, upload_url)
    print(f"upload response --> {upload_resp}\n")

    save_resp = save_wall_photo(upload_response=upload_resp)
    print(f"save photo vk group album response --> {save_resp}\n")

    post_resp = post_wall_photo(
        save_image_response=save_resp, message=message
    )
    print(post_resp)


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    main()
