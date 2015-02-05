#!/usr/bin/python
# This Python file uses the following encoding: utf-8

from BeautifulSoup import BeautifulSoup
from multiprocessing import Pool
import time, datetime
import re
import requests
import sys

sys.dont_write_bytecode = True

class _GetPad(object):
    _URL = 'https://etherpad.openmarket.com'

    def __init__(self, auth):
        (self._user, self._pword) = auth

    def __call__(self, pad, revision=None):
        revision_no = "latest" if revision is None else "rev.%s" % revision
        page = requests.get("%s/ep/pad/view/%s/%s" % (self._URL, pad, revision_no), auth=(self._user, self._pword))
        soup = BeautifulSoup(page.text, convertEntities=BeautifulSoup.HTML_ENTITIES)
        text_time = soup.find("div", {'id': 'timer'}).text

        ugly_javascript = filter(lambda x: "CDATA" in x.text, soup.findAll("script"))[0].text
        revision_number = int(re.findall(r'"totalRevs":(\d+)\D', ugly_javascript)[0])

        pad_text = "\n".join(map(lambda x: x.text, soup.find("div", {'id': 'padcontent'}).findAll("div")))
        return (pad, datetime.datetime(*time.strptime(text_time, '%m/%d/%Y %H:%M:%S')[:6]), pad_text, revision_number)

class Etherpad(object):
    _URL = 'https://etherpad.openmarket.com'

    def __init__(self, auth, concurrent=10):
        (self._user, self._pword) = auth
        self._concurrent = concurrent

    def list_pads_by_hashtag(self, hashtag):
        page = requests.get("%s/ep/search?query=%s" % (self._URL, hashtag), auth=(self._user, self._pword))
        soup = BeautifulSoup(page.text)
        pads = map(lambda x: x.text, filter(lambda x: x is not None, map(lambda x: x.find("a"), soup.find("div", {'id': 'editorcontainer'}).findAll("dt"))))
        return pads

    def get_pads(self, pad_list):
        pool = Pool(self._concurrent)
        updates = pool.map(_GetPad((self._user, self._pword)), pad_list)
        pool.terminate()
        return updates

     

def main():
    e = Etherpad(('your_username', 'your_password'))
    for (pad, updated, text, revision_number) in e.get_update_times(e.list_pads_by_hashtag('test')):
        print "%s %s" % (pad, updated.strftime('%Y-%m-%d %H:%M:%S'))
        print text

if __name__ =='__main__':main()

