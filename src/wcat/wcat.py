#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import os
import sys
import getpass
import urllib
import requests
import html2text
from optparse import OptionParser
from etherpad import Etherpad

sys.dont_write_bytecode = True

class Wcat:

  def __init__(self, auth=None):
    if auth is None and ('WCAT_USER' in os.environ and 'WCAT_PASS' in os.environ):
      auth = (os.environ['WCAT_USER'], os.environ['WCAT_PASS'])
    self._auth = auth
      
  def _get_interactive_auth(self, prompt=None):
    if prompt is not None:
      print prompt
    else:
      print 'Please enter your auth credentials.'

    username = raw_input('username:')
    password = getpass.getpass('password:')
    return (username, password)

  def _get_auth(self, prompt=None):
    if self._auth is None:
      return self.get_interactive_auth(prompt)
    else:
      return self._auth

  def get_page(self, url):
    if not url.lower().startswith('http://') and not url.lower().startswith('https://'):
      # Maybe it's a file!
      return open(url, 'r').read()
    else:
      try:
        page = requests.get(url, verify=False)
      except requests.ConnectionError, e:
        raise Exception("Fatal connection failure: %s" % e.message)

      if page.status_code == 200 and page.url.startswith('https://cas.openmarket.com/login'):
        (username, password) = self._get_auth(prompt='CAS login required')
        data = {'username': username, 'password': password}
        try:
          page = requests.post(page.url, data=data)
        except requests.ConnectionError, e:
          raise Exception('Failed on logging into CAS: %s' % e.message)
      elif page.status_code == 200 and page.url.startswith('https://wiki.openmarket.com/login'):
        (username, password) = self._get_auth(prompt='OM Wiki login required')
        data = {'os_username': username, 'os_password': password, 'os_destination': urllib.unquote_plus(page.url.split('os_destination=')[1].split('&')[0])}
        login_url = 'https://wiki.openmarket.com/dologin.action'
        try:
          page = requests.post(login_url, data=data)
        except requests.ConnectionError, e:
          raise Exception('Failed on logging into OM Wiki: %s' % e.message)
      elif page.status_code == 401:
        (username, password) = self._get_auth(prompt='HTTP basic auth required')
        try:
          page = requests.get(url, auth=(username, password), verify=False)
        except requests.ConnectionError, e:
          raise Exception(e.message)
    return page.text

  def get_text(self, url):
    if 'etherpad.openmarket' in url or 'etherpad.mxtelecom' in url:
      auth = self._get_auth(prompt='HTTP basic auth required')
      etherpad = Etherpad(auth)
      updates = etherpad.get_pads([url.split('/')[-1]])
      text = updates[0][2]
      return text
    else:
      return html2text.html2text(self.get_page(url))      

