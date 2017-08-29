import time
import json
import re
from pprint import pprint
import datetime
import os
import shutil
import concurrent.futures

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import requests
from bs4 import BeautifulSoup
from django.db import IntegrityError


from .models import User, Media, Hashtag


DIRNAME_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'app', 'images')
BROWSER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'browser', 'chromedriver')
print(BROWSER_PATH)
MAX_WORKERS = 25


class ScrapingHelper:
    def __init__(self, url):
        self.url = url
        self.wd = None
        self.create_wd()

    def create_wd(self):
        self.wd = webdriver.Firefox()
        self.wd.implicitly_wait(5)
        self.wd.get(self.url)

    def destroy_wd(self):
        self.wd.close()

    def scrap(self):
        medias = []
        print('Dowloading...')
        self.scroll_page(scroll=10)
        bsObj = BeautifulSoup(self.wd.page_source, 'lxml')
        for element in bsObj.find('article').find('div', {'class': '_cmdpi'}).find_all('a'):
            l = 'https://www.instagram.com' + element['href'][:element['href'].rfind('/')]
            media = Media(link=l)
            if 'Video' in str(element):
                media.type = 'v'
            else:
                media.type = 'i'
            medias.append(media)
            # print(media)
        medias = self.download_many(medias)
        for media in medias:
            hashtags = media.hashtags_[:]
            try:
                media.author.save()
            except IntegrityError as error:
                media.author = User.objects.get(user_id=media.author.user_id)

            try:
                media.save()
            except Exception as error:
                print(error)
            media = Media.objects.get(media_id=media.media_id)

            for h in hashtags:
                try:
                    h.save()
                except IntegrityError:
                    h = Hashtag.objects.get(text=h.text)
                media.hashtags.add(h)
            media.save()
        return medias

    def scroll_page(self, scroll=0):
        for _ in range(0, scroll):
            page_height = self.wd.find_element_by_tag_name('article').size['height']
            try:
                self.wd.find_element_by_link_text('Load more').click()
            except NoSuchElementException:
                pass
            for __ in range(5):
                self.wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                #print(wd.find_element_by_tag_name('article').size['height'])
                time.sleep(0.3)
            if page_height == self.wd.find_element_by_tag_name('article').size['height']:
                break

    def download_many(self, medias):
        new_medias = []
        # for m in medias:
        #     new_medias.append(self.download_one(m))

        workers = min(MAX_WORKERS, len(medias))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_media = {executor.submit(self.download_one, media): media for media in medias}
            for future in concurrent.futures.as_completed(future_to_media):
                try:
                    data = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (future_to_media[future], exc))
                    raise
                else:
                    new_medias.append(data)
                    # print(data)
        return new_medias

    def download_one(self, media):
        r = requests.get('http://api.instagram.com/oembed?callback=&url='+media.link)
        if r.status_code != 200:
            print('BAD CONNECTION', media.link)
            return media
        data = json.loads(r.text)
        #pprint(data)
        author = User(user_id=str(data['author_id']), username=data['author_name'])
        media.author = author
        media.media_id = data['media_id']
        media.hashtags_ = self.get_hashtags_from_title(data['title'])

        datetime_pattern = re.compile(r"datetime=.(.+?).>")
        date = datetime_pattern.findall(data['html'].replace('\n', ' '))[0]
        media.created_date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S+00:00')

        if media.type == 'i':
            media.url = data['thumbnail_url']
            media.filepath = media.media_id+'.jpg'
        else:
            media.filepath = media.media_id + '.mp4'

        if not os.path.exists(os.path.join(DIRNAME_IMAGES, media.media_id)):
            media = self.download_media(media)
        return media

    @staticmethod
    def download_media(media):
        if media.type == 'i':
            r = requests.get(media.url, stream=True)
        else:
            r = requests.get(media.link)
            url_video_pattern = re.compile(r"https:.+?\.mp4")
            media.url = url_video_pattern.findall(r.text)[0]
            r = requests.get(media.url, stream=True)
        if r.status_code == 200:
            if not os.path.exists(os.path.join(DIRNAME_IMAGES, media.filepath+ media.url[-4:])):
                with open(os.path.join(DIRNAME_IMAGES, media.filepath+ media.url[-4:]), 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        return media

    @staticmethod
    def get_hashtags_from_title(title):
        hashtag_pattern = re.compile(r'#(.*?) ')
        return [Hashtag(text=hashtag) for hashtag in set(hashtag_pattern.findall(title+' '))]  # set() without copies hashtags
