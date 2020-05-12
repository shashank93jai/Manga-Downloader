import os
import urllib
import urllib.error
import urllib.request
import argparse
import numpy as np
from image_scraper.utils import ImageScraper
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from image_scraper.progressbar import ProgressBar, Percentage, Bar, RotatingMarker, ETA, FileTransferSpeed
from image_scraper.utils import ImageScraper, download_worker_fn
from image_scraper.exceptions import DirectoryAccessError, DirectoryCreateError, PageLoadError
from concurrent.futures import ThreadPoolExecutor
import threading
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--name', default=None, type=str, required=True,
                    help='x, where manga resides at http://www.mangareader.net/x/')
parser.add_argument('--chapters', default='1-2', type=str, required=True)
parser.add_argument('--out', type=str, help='output directory')
parser.add_argument('--downloader', type=str, default='serial')

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


def save_image(image_url, output_directory, filename):
    if os.path.exists(os.path.join(output_directory, filename)):
        return
    try:
        raw_html = get_stream(image_url)
        write_stream(raw_html.read(), output_directory, filename)
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
            break
        img = soup.find('table', {'class': 'episode-table'}).find_all('img')[0]['src']
        img_url_list.append((page_idx, img))
        page_idx += 1
    return img_url_list

def get_chapters(chapter_str):
    chapters_range = [int(x) for x in chapter_str.split('-')]
    return np.arange(chapters_range[0], chapters_range[1]+1)

def serial_download(img_info):
    for sub_dir, filename, img_url in img_info:
        extension='.'+img_url.split('/')[-1]
        filename=filename+extension
        save_image(img_url, os.path.join(args.out, sub_dir), filename)

def multi_threaded_download(img_info):
    scraper = ImageScraper()
    scraper.download_path = args.out
    scraper.set_img_list(img_info)
    scraper.process_download_path()

    status_flags = {'count': 0, 'percent': 0.0, 'failed': 0, 'under_min_or_over_max_filesize': 0}
    widgets = ['Progress: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()
    pool = ThreadPoolExecutor(max_workers=scraper.nthreads)
    status_lock = threading.Lock()
    for img_info in scraper.images:
        if status_flags['count'] == scraper.no_to_download:
            break
        pool.submit(download_worker_fn, scraper, img_info, pbar, status_flags, status_lock)
        status_flags['count'] += 1
    pool.shutdown(wait=True)
    pbar.finish()
    print("\nDone!\nDownloaded {0} images\nFailed: {1}\n".format(
        status_flags['count'] - status_flags['failed'] - status_flags['under_min_or_over_max_filesize'],
        status_flags['failed']))

if __name__ == '__main__':
    chapters = get_chapters(args.chapters)
    base_url = 'http://www.mangareader.net'
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    img_info = list()
    for chapter in chapters:
        manga_url = os.path.join(base_url, args.name, str(chapter))
        chapter_directory = os.path.join(args.out, str(chapter))
        if not os.path.exists(chapter_directory):
            os.makedirs(chapter_directory)

        img_list_for_chapter = get_img_urls_for_chapter(manga_url)
        img_info_for_chapter = [(str(chapter), str(idx), url) for idx, url in img_list_for_chapter] #(chapter_directory_name, filename, image url to download)
        img_info.extend(img_info_for_chapter)

    if args.downloader == 'serial':
        serial_download(img_info)
    elif args.downloader == 'multi-thread':
        multi_threaded_download(img_info)
    else:
        print('Invalid --downloader option')



