﻿# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
try:    import json
except: import simplejson as json
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class MeteoPLApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'http://www.meteo.pl/'
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.COOKIE_FILE = GetCookieDir('iklubnet.cookie')
        
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        
    def getPage(self, url, params={}, post_data=None):
        sts, data = self.cm.getPage(url, params, post_data)
        if sts:
            enc = self.cm.ph.getSearchGroups(data, 'charset=([^"]+?)"')[0]
            try:
                data = data.decode(enc).encode('utf-8')
            except Exception:
                pass
        return sts, data
        
    def getList(self, cItem):
        printDBG("MeteoPLApi.getChannelsList")
        channelsTab = []
        initList = cItem.get('init_list', True)
        if initList:
            sts, data = self.getPage(self.getFullUrl('um/php/gpp/search.php'))
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, '<select name=woj', '</select>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'option', '<', withMarkers=True)
            for item in data:
                cat = self.cm.ph.getSearchGroups(item, 'value=([^\s^>]+?)[\s>]')[0].replace('"', '').replace("'", "")
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '>([^<]+?)<')[0]).strip()
                params = dict(cItem)
                params.update({'init_list':False, 'meteo_cat':'woj', 'woj':cat, 'url':self.getFullUrl('um/php/gpp/next.php'), 'title':title})
                channelsTab.append(params)
        else:
            cat = cItem.get('meteo_cat', '')
            if 'woj' == cat:
                sts, data = self.getPage(cItem['url'], post_data={'woj':cItem['woj'], 'litera':''})
                if not sts: return []
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>', withMarkers=True, caseSensitive=False)
                for item in data:
                    mgram = self.cm.ph.getDataBeetwenMarkers(item, 'show_mgram(', ')', False)[1].strip()
                    if mgram == '': continue
                    title  = self.cleanHtmlStr(item)
                    params = dict(cItem)
                    params.update({'type':'picture', 'title':title, 'meteo_cat':True, 'url':self.getFullUrl('um/php/meteorogram_id_um.php?ntype=0u&id=' + mgram)})
                    channelsTab.append(params)
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("MeteoPLApi.getVideoLink")
        urlsTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        printDBG("===================================")
        printDBG(data)
        printDBG("===================================")
        
        fcstdate = self.cm.ph.getSearchGroups(data, '''var\s*fcstdate\s*=\s*['"]([^'^"]+?)['"]''')[0]
        ntype = self.cm.ph.getSearchGroups(data, '''var\s*ntype\s*=\s*['"]([^'^"]+?)['"]''')[0]
        lang = self.cm.ph.getSearchGroups(data, '''var\s*lang\s*=\s*['"]([^'^"]+?)['"]''')[0]
        id = self.cm.ph.getSearchGroups(data, '''var\s*id\s*=\s*['"]([^'^"]+?)['"]''')[0]
        act_x = self.cm.ph.getSearchGroups(data, '''var\s*act_x\s*=([^;]+?);''')[0].strip()
        act_y = self.cm.ph.getSearchGroups(data, '''var\s*act_y\s*=([^;]+?);''')[0].strip()
        urlsTab.append({'name':'mgram', 'url':self.getFullUrl('um/metco/mgram_pict.php?ntype=%s&fdate=%s&row=%s&col=%s&lang=%s' % (ntype, fcstdate, act_y, act_x, lang))})
        
        return urlsTab