import os
import urllib
import urllib.error
import urllib.request
import argparse
import numpy as np
from urllib.error import HTTPError
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument('--name', default=None, type=str, required=True,
                    help='x, where manga resides at http://www.mangareader.net/x/')
parser.add_argument('--chapters', default='1-2', type=str, required=True)
parser.add_argument('--out', type=str, help='output directory')

args = parser.parse_args()
print(vars(args))


def write_stream(stream, directory, file_name):
    file_path = os.path.join(directory, file_name)
    file = open(file_path, 'wb')
    file.write(stream)
    file.close()


def get_stream(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    request = urllib.request.Request(url, headers=headers)
    raw_html = urllib.request.urlopen(request)
    return raw_html


def save_image(image_url, output_directory, file_name):
    if os.path.exists(os.path.join(output_directory, file_name)):
        return
    try:
        raw_html = get_stream(image_url)
        write_stream(raw_html.read(), output_directory, file_name)
    except urllib.error.HTTPError as err:
        print('Page not found')


def get_img_urls_for_chapter(url):
    try:
        raw_html = get_stream(url)
        soup = BeautifulSoup(raw_html, 'html.parser')
    except urllib.error.HTTPError as err:
        print('Invalid chapter url')
        return

    page_idx = 1
    img_url_list = list()
    while True:
        page_url = os.path.join(url, str(page_idx))
        soup = None
        try:
            raw_html = get_stream(page_url)
            soup = BeautifulSoup(raw_html, 'html.parser')
        except urllib.error.HTTPError as err:
            print('Reached end of chapter')
            break
        img = soup.find('table', {'class': 'episode-table'}).find_all('img')[0]['src']
        img_url_list.append((page_idx, img))
        page_idx += 1
    return img_url_list


def download_chapter(chapter_url, output_directory):
    img_url_list = get_img_urls_for_chapter(chapter_url)
    for idx, img_url in img_url_list:
        extension='.jpg'
        file_name=str(idx)+extension
        save_image(img_url, output_directory, file_name)

def get_chapters(chapter_str):
    chapters_range = [int(x) for x in chapter_str.split('-')]
    return np.arange(chapters_range[0], chapters_range[1]+1)


if __name__ == '__main__':
    chapters = get_chapters(args.chapters)
    base_url = 'http://www.mangareader.net'
    if not os.path.exists(args.out):
        os.makedirs(args.out)
    for chapter in chapters:
        manga_url = os.path.join(base_url, args.name, str(chapter))
        chapter_directory = os.path.join(args.out, str(chapter))
        if not os.path.exists(chapter_directory):
            os.makedirs(chapter_directory)
        download_chapter(manga_url, chapter_directory)
