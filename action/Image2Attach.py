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
        self.images = {} # image binay files {filename: content}
        self.images_fetched = [] # images successful fetched
        self.process_success = 0 # count of process successful
        self.process_fail = 0 # count of process failed

    def execute(self):
        self.getImageUrls()
        self.fetchImages()
        #logging.info('****************************')
        #logging.info(self.images)
        self.addAttachment()
        result = self.replaceImages()
        if self.process_success > 0:
            PageEditor(self.request, self.pagename)._write_file(
                result,
                comment=u'internet image save to attachment',
                )

    def getImageUrls(self):
        """match all internet image url from raw"""
        transcludes = []
        for line in WikiParser.eol_re.split(self.page.get_raw_body()):
            line = line.strip()
            match = WikiParser.scan_re.match(line)
            if match != None:
                transclude = match.groupdict().get('transclude', '')
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
            if not AttachFile.exists(self.request,
                                     self.pagename,
                                     wikiutil.taintfilename(name)):
                AttachFile.add_attachment(self.request,
                                          self.pagename,
                                          name,
                                          image)

    def replaceImages(self):
        """edit the raw, replace image url with attachment url"""

        result = ''
        for line in WikiParser.eol_re.split(self.page.get_raw_body()):
            # save the ident
            indent = WikiParser.indent_re.match(line).group(0)
            result += indent + self.replaceImageLine(line.strip())
        logging.info('****************************')
        logging.info(result)
        return result

    def replaceImageLine(self, line):
        """replace one line image url with attachment, else will return"""
        match = WikiParser.scan_re.match(line)
        if match != None:
            transclude = match.groupdict().get('transclude', '')
            if transclude != None and transclude.find('attachment') < 0:
                url = self.image_url_re.findall(transclude)[0]
                line = line.replace(url, 'attachment:' + wikiutil.taintfilename(url))
                self.process_success += 1
        return line + '\n'

def execute(pagename, request):
    """
    save images to attachments
    """
    #TODO add auth control
    _ = request.getText
    page = Page(request, pagename)
    image2attach = Image2Attach(pagename, request)
    image2attach.execute()
    request.theme.add_msg(
        _(
            "%d images saved successful, %d images saved failed" % (
                image2attach.process_success,
                image2attach.process_fail,
            )
        ),
        "info"
        )
    page.send_page()
