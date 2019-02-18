"""
skill Grimms stories
Copyright (C) 2018  Andreas Lorensen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.parse import match_one
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message

import requests
from bs4 import BeautifulSoup
import time


class GrimmsTales(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.is_reading = False
        self.lang_url = {'da': 'https://www.grimmstories.com/da/grimm_eventyr/',
                         'de': 'https://www.grimmstories.com/de/grimm_maerchen/',
                         'en': 'https://www.grimmstories.com/en/grimm_fairy-tales/',
                         'es': 'https://www.grimmstories.com/es/grimm_cuentos/',
                         'fr': 'https://www.grimmstories.com/fr/grimm_contes/',
                         'it': 'https://www.grimmstories.com/it/grimm_fiabe/',
                         'nl': 'https://www.grimmstories.com/nl/grimm_sprookjes/'}
        self.url = self.lang_url[self.lang[:2]]
        self.add_event('storytelling', self.handle_storytelling)
        self.add_event('storytelling.'+self.name, self.handle_storytelling_read)
        self.index = self.get_index(self.url + "list")

    def handle_storytelling_read(self, message):
        story = message.data.get("story")
        self.log.info('reading ' + story)
        result = match_one(story, list(self.index.keys()))
        self.log.info(result)
        self.tell_story(self.index.get(result[0]), 0)

    def handle_storytelling(self, message):
        self.log.info('skill called')
        self.bus.emit(Message("storytelling.register", {"register": 'register'}))
        story = message.data.get("story")
        result = match_one(story, list(self.index.keys()))
        if result[1] < 0.1:
            return
        else:
            self.log.info('sendig to messagebs')
            self.bus.emit(Message("storytelling.response",
                                      {'confidence': result[1],
                                       'skill': self.name,
                                       'title': result[0]}))

    def tell_story(self, url, bookmark):
        self.is_reading = True
        story = self.get_story(url)
        self.speak_dialog('title_by_author', data={'title': story[0], 'subtitle': story[1]})
        time.sleep(1)
        self.log.info(url)
        lines = story[2].split('\n\n')
        for line in lines[bookmark:]:
            self.settings['bookmark'] += 1
            time.sleep(.5)
            if self.is_reading is False:
                break
            sentenses = line.split('. ')
            for sentens in sentenses:
                if self.is_reading is False:
                    break
                else:
                    wait_while_speaking()
                    self.speak(sentens, wait=True)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['bookmark'] = 0
            self.settings['story'] = None
            # time.sleep(2)
            # self.speak_dialog('from_GrimmsTales')

    def stop(self):
        self.log.info('stop is called')
        if self.is_reading is True:
            self.is_reading = False
            return True
        else:
            return False

    def get_soup(self, url):
        try:
            r = requests.get(url)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")
            return soup
        except Exception as SockException:
            self.log.error(SockException)

    def get_story(self, url):
        soup = self.get_soup(url)
        title = [a.text.strip() for a in soup.findAll("h1", {'itemprop': ['name']})][0]
        genre = [a.text.strip() for a in soup.findAll("span", {'itemprop': ['genre']})][0]
        title = title.replace(genre, '')
        subtitle = [a.text.strip() for a in soup.find_all('span', {'itemprop': ['headline']})][0]
        story = [a.text.strip() for a in soup.find_all('div', {'itemprop':['text']})][0]
        return title, subtitle, story

    def get_index(self, url):
        soup = self.get_soup(url)
        index = {}
        for link in soup.find_all("a"):
            index.update({link.text: link.get("href")})
        return index


def create_skill():
    return GrimmsTales()
