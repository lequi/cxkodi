#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin,xbmcaddon, xbmc
import urlfetch
from BeautifulSoup import BeautifulSoup
import json
import re
import fptplay

plugin = Plugin()
__settings__ = xbmcaddon.Addon(id='plugin.video.fptplay')
crawurl = 'https://fptplay.net/livetv'

def getAllChannels():
    cns = []
    #cns.extend(getEvents(crawurl))
    cns.extend(getChannels(crawurl))
    return cns

def getEvents(url):
    cns = []
    result = None
    result = urlfetch.fetch(
        url,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })
    if result.status_code != 200 :
        plugin.log.error('Something wrong when get list fpt play event !')
        return None
    soup = BeautifulSoup(result.content, convertEntities=BeautifulSoup.HTML_ENTITIES)

    item = soup.find('ul', {'class' : 'slider_event'})
    if item == None :
        return None
    itemlinks = item.findAll('a')
    if itemlinks == None :
        return None
    for item in itemlinks:
        title = item.get('title')
        link = item.get('href')
        img = item.find('img')
        imgthumbnail = ''
        if img != None :
            imgthumbnail = img.get('src')
        if not imgthumbnail :
            continue
        cn = {
                'label': title,
                'path': plugin.url_for('plays', id = link),
                'thumbnail':imgthumbnail,
                'is_playable': True
            }
        if cn not in cns :
            cns.append(cn)
    return cns

def getChannels(url):
    cns = []
    result = None
    result = urlfetch.fetch(
        url,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })
    if result.status_code != 200 :
        plugin.log.error('Something wrong when get list fpt play channel !')
        return None
    soup = BeautifulSoup(result.content, convertEntities=BeautifulSoup.HTML_ENTITIES)

    items = soup.findAll('div', {'class' : 'hover01'})
    for item in items:

        ac = item.find('a', {'class' : 'tv_channel '})

        if ac == None :
            ac = item.find('a', {'class' : 'tv_channel active'})
            if ac == None :
                continue

        lock = item.find('img', {'class' : 'lock'})

        if lock != None :
            continue

        dataref = ac.get('data-href')

        if dataref == None :
            continue

        img = ac.find('img', {'class' : 'img-responsive'})

        imgthumbnail = ''

        if img != None :
            imgthumbnail = img.get('data-original')

        if not dataref.startswith(crawurl) :
            continue

        channelid = dataref[27:]

        if not channelid :
            continue

        title = channelid
        cn = {
                'label': title,
                'path': plugin.url_for('plays', id = channelid),
                'thumbnail':imgthumbnail,
                'is_playable': True
            }
        cns.append(cn)
    return cns

def getLink(id = None):

    if id.startswith('https://') :
        #is event
        id = getChannelIdFromEventLink(id)
    if id == None :
        return None


    #get cookie & csrf
    result = urlfetch.fetch(
        crawurl,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })

    #plugin.log.error(result.content)

    m = re.search(r"name=\"_token\" content=\"(.+)\"",result.content)

    if m == None :
        return None
    csrf = m.group(1)
    cookie='laravel_session=' + result.cookies.get('laravel_session') + ";"

    result = urlfetch.post(
        'https://fptplay.net/show/getlinklivetv',
        data={"id": id,
            "quality": __settings__.getSetting('quality'),
            "mobile": "web",
			"type" : "newchannel"
            },
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
                'X-Requested-With':'XMLHttpRequest',
                'Referer':'https://fptplay.net/livetv',
                'x-csrf-token': csrf,
                'cookie':cookie
                }
        )

    if result.status_code != 200 :
        plugin.log.error("Can't get link for id " + id)
        return None

    info = json.loads(result.content)
    plugin.log.error(info)

    return info['stream']

def startChannel():
    channelid = __settings__.getSetting('start_channelid')
    link = getLink(channelid)
    xbmc.Player().play(link)

def getChannelIdFromEventLink(url = None) :
    if url == None :
        return None
    result = None
    result = urlfetch.fetch(
        url,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })
    if result.status_code != 200 :
        plugin.log.error('Something wrong when get content of event link !')
        return None
    m = re.search(r"var id = '([^']+)';",result.content)
    if m == None :
        return None
    return m.group(1)

@plugin.route('/')
def index():
    cns = getAllChannels()
    return cns

@plugin.route('/plays/<id>')
def plays(id):
    link = getLink(id)
    plugin.log.info("Playing : " + link)
    plugin.set_resolved_url(link)

@plugin.route('/resolve/<uri>')
def resolve(uri):
    plugin.log.info("Resolve : " + uri)
    s_link = fptplay.getLink(uri,__settings__.getSetting('quality'))
    plugin.log.info("Return url : " + s_link)
    if s_link == None :
        return None 
    plugin.set_resolved_url(s_link)


if __name__ == '__main__':
    plugin.run()
