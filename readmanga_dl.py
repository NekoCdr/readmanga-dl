import re
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from os import system
import tkinter
from tkinter import filedialog


def check_status(status_code: int) -> None:
    if status_code != 200:
        print(f'TERMINATED! Server return code {status_code}!')
        system('pause')
        sys.exit(0)


def str_convert(_string) -> str:
    result = re.search(r'[^\'\"]+', _string)
    if result == None:
        return ''
    else:
        return str(result.group(0))


def get_manga_url(input_url: str) -> str:
    allowed_domains = ['readmanga.me', 'www.readmanga.me']

    url = urlparse(input_url)

    if not url.netloc:
        url = urlparse('//'+input_url)

    if not url.netloc in allowed_domains or not url.path:
        print(f'ERROR! {url.geturl()} is not supported!')
        system('pause')
        sys.exit(0)

    path = Path(url.path)

    path_level = len(path.parents)-2
    if path_level > 0:
        path = path.parents[path_level]

    manga_url = 'http://readmanga.me/' + str(path.relative_to('/'))

    return manga_url


def get_manga_data(manga_url: str, headers: dict) -> dict:
    response = requests.get(manga_url, headers=headers)

    check_status(response.status_code)

    page = BeautifulSoup(response.content, 'html.parser')
    manga_name = page.select_one('span.name').text
    
    manga_data = {
        'name': manga_name
    }
    return manga_data


def get_chapter_list(manga_url: str, headers: dict) -> dict:
    response = requests.get(f'{manga_url}/vol1/1', headers=headers)

    check_status(response.status_code)

    page = BeautifulSoup(response.content, 'html.parser')
    chapter_selector = page.select('#chapterSelectorSelect > option')[::-1]

    chapter_list = []
    for option in chapter_selector:
        chapter_data = re.findall(r'/vol(.+)\?', option['value'])[0]
        chapter_data = chapter_data.split('/')
        chapter_name = option.text
        
        chapter_list.append({
            'volume': int(chapter_data[0]),
            'chapter': int(chapter_data[1]),
            'name': chapter_name
        })

    return chapter_list


def get_page_links(manga_url: str, vol: int, chapter: int) -> dict:
    url = f'{manga_url}/vol{vol}/{chapter}'
    response = requests.get(url, headers=headers)

    check_status(response.status_code)

    first_page = BeautifulSoup(response.content, 'html.parser')
    script_block = first_page.select('.pageBlock.container.reader-bottom > script[type="text/javascript"]')[0].text
    regexp_result = re.findall(r'rm_h.init\( \[\[(.+)\]\].+\);', script_block)[0]
    page_data_list = regexp_result.split('],[')

    page_links = []
    for page in page_data_list:
        t = [str_convert(_string) for _string in page.split(',')]
        page_links.append(str(t[1] + t[0] + t[2]))

    return page_links


system('title *** Readmanga Downloader ***')

manga_input_url = input('Please, enter manga url: ')
target_path = Path().resolve().joinpath('downloaded manga') # default path, unless otherwise specified

print('Please, select target folder:')

root = tkinter.Tk()
root.withdraw()
selected_path = filedialog.askdirectory()

if selected_path:
    target_path = Path(selected_path).resolve()

manga_url = get_manga_url(manga_input_url)

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
}

manga_data = get_manga_data(manga_url, headers)

chapter_list = get_chapter_list(manga_url, headers)

manga_path = Path(target_path).resolve().joinpath(manga_data['name'])
manga_path.mkdir(parents=True, exist_ok=True)
manga_path = manga_path.resolve()

for chapter_data in chapter_list:
    vol = chapter_data['volume']
    chapter = chapter_data['chapter']

    page_links = get_page_links(manga_url, vol, chapter)

    chapter_path = manga_path.joinpath(f'{vol:02d}/{chapter:02d}')
    chapter_path.mkdir(parents=True, exist_ok=True)
    chapter_path = chapter_path.resolve()

    print(f'*** Started download chapter {vol} - {chapter} ***')

    cl = len(page_links)
    i = 1
    for image_url in page_links:
        print(f'Getting chapter pages [{i}/{cl}]...')
        img_response = requests.get(image_url, headers=headers)

        image_path = chapter_path.joinpath(f'{i:02d}.jpg')

        check_status(img_response.status_code)
        
        with open(str(image_path), 'wb') as image_file:
            image_file.write(img_response.content)
            image_file.close()

        i += 1

    print(f'Chapter {vol} - {chapter} download successfully.\n')

print('All chapters downloaded!')
print(f'Download path: {str(manga_path)}')

system('pause')
