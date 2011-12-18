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
        self.image_urls = []
        self.images = {}
        self.process_success = 0
        self.process_fail = 0

    def execute(self):
        self.getImageUrls()
        self.fetchImages()
        #logging.info(self.images)
        logging.info('****************************')
        logging.info(self.images.keys())
        self.addAttachment()
        logging.info(self.image_urls)

    def getImageUrls(self):
        """match all internet image url from raw"""
        transcludes = []
        for line in self.page.get_raw_body().splitlines():
            line = line.strip()
            match = WikiParser.scan_re.match(line)
            if match != None:
                transclude = match.groupdict().get('transclude', '')
                #logging.info('transclude')
                #logging.info(transclude )
                if transclude != None and transclude.find('attachment') < 0:
                    # not attachment image ye
                    transcludes.append(transclude)
        # remove the {{ and }}
        self.image_urls = [self.image_url_re.findall(x)[0] for x in transcludes]

    def fetchImages(self):
        """save image to local"""
        for url in self.image_urls:
            try:
                handler = urllib2.urlopen(url)
                self.images[url] = handler.read()
            except:
                self.process_fail += 1

    def addAttachment(self):
        """add image to attachment"""
        for name, image in self.images.items():
            AttachFile.add_attachment(
                self.request,
                self.pagename,
                name,
                image,
                )

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
