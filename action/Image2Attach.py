#!/usr/bin/python
# coding:utf-8

"""
    MoinMoin Extention: image2attach v0.0.1
    Descption: Save page's images to attachments
    @author: alswl <http://log4d.com>
    @date: 2011-12-17
    @license: GNU GPL, see COPYING for details.
"""

import urllib2
import re

from MoinMoin import log
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.action import AttachFile
from MoinMoin import wikiutil
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

logging = log.getLogger(__name__)

class Image2Attach:
    image_url_rule = r'https?://[^|^}]+' # image url's regex rule
    image_url_re = re.compile(image_url_rule, re.VERBOSE | re.UNICODE)

    def __init__(self, pagename, request):
        self.pagename = pagename
        self.request = request
        self.page = Page(request, pagename)

    def execute(self):
        logging.info('****************************')
        self.getImageUrls()

    def getImageUrls(self):
        """match all internet image url from raw"""
        transcludes = []
        for line in self.page.get_raw_body().splitlines():
            line = line.strip()
            match = WikiParser.scan_re.match(line)
            if match != None:
               transclude = match.groupdict().get('transclude', '')
               if transclude != None and transclude.find('attachment') < 0:
                   transcludes.append(transclude)
        self.images = [self.image_url_re.findall(x) for x in transcludes]
        logging.info(self.images)

    def fetchImages(self):
        """save image to local"""
        pass

    def addAttachment(self):
        """add image to attachment"""
        pass

    def replaceImages(self):
        """edit the raw, replace image url with attachment url"""
        files = AttachFile._get_files(self.request, self.pagename)
        attach_dir = AttachFile.getAttachDir(self.request, self.pagename)

        newtext = ''
        #PageEditor(self.request, self.pagename).saveText(newtext, 0) #XXX 0
        pass

def execute(pagename, request):
    """
    save images to attachments
    """
    #TODO add auth control
    _ = request.getText
    page = Page(request, pagename)
    Image2Attach(pagename, request).execute()
    request.theme.add_msg(_("images all saved"), "info")
    page.send_page()
