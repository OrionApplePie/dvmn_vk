#!/usr/bin/env python3
import os
import json
from pathlib import Path

import requests
from requests.compat import urlparse, urljoin

from dotenv import find_dotenv, load_dotenv

DEFAULT_CHUNK_SIZE = 1024
FILES_FOLDER = "images"

VK_API_VERSION = "5.103"
VK_API_METHODS_BASE_URL = "https://api.vk.com/method/"


def implicit_flow():
    client_id = os.getenv("VK_CLIENT_ID")

    auth_url = "https://oauth.vk.com/authorize"
    params = {
        "client_id": client_id,
        # "redirect_uri": "",
        "display": "page",
        "scope": "photos,groups,wall,offline",
        "response_type": "token",
        "v": "5.103",
    }

    response = requests.get(
        url=auth_url,
        params=params
    )
    print(response.url)


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

    # with open("comm_data.txt", "w") as out_file:
    #     json.dump(comm_response.json(), out_file)

    print(comm_response.url)
    # print(comm_response.json())


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

    implicit_flow()

    get_comm_vk()


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    main()
