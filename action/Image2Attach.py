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
import os

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
        self.text = ''
        self.image_extenstions = ['jpg', 'gif', 'png']

    def process(self):
        for line in WikiParser.eol_re.split(self.page.get_raw_body()):
            self.process_line(line)
        self.write_file()

    def write_file(self):
        """scommit changes"""
        if self.process_success > 0:
            PageEditor(self.request, self.pagename)._write_file(
                self.text,
                comment=u'internet image save to attachment',
                )

    def process_line(self, line):
        """process each line in wiki text"""
        # save the ident
        indent = WikiParser.indent_re.match(line).group(0)
        if indent == None:
            indent = '' ## FIXME bad smell
        match = WikiParser.scan_re.match(line.strip())
        if match != None:
            for type, hit in match.groupdict().items():
                # only process the type may contain images
                if hit is not None:
                    if type == 'transclude':
                        line = self.process_transclude(line, match.groupdict())
                    elif type == 'link':
                        line = self.process_link(line, match.groupdict())
        self.text += indent + line + '\n'

    def process_transclude(self, line, groups):
        """# {{http://xxx/xxx.jpg}}"""
        transclude = groups.get('transclude', '')
        if transclude != None and transclude.find('attachment') < 0:
            try:
                url = self.image_url_re.findall(transclude)[0]
                image = self.fetchImage(url)
                attachment_name = self.addAttachment(url, image)
                self.process_success += 1
            except:
                self.process_fail += 1
                return line
            return line.replace(url,
                                'attachment:' + attachment_name)
            # remove the {{ and }}
            #self.image_urls = [self.image_url_re.findall(x)[0] for x in transcludes]
        else:
            return line

    def process_link(self, line, groups):
        """[[link|{{image}}]]"""
        target = groups.get('link_target', '')
        desc = groups.get('link_desc', '') or ''
        #params = groups.get('link_params', u'') or u''
        match = WikiParser.scan_re.match(desc.strip())
        if match != None:
            for type, hit in match.groupdict().items():
                if hit is not None and type == 'transclude':
                    attach_desc = self.process_transclude(desc,
                                                          match.groupdict())
                    line = line.replace(desc, attach_desc)
                    if os.path.splitext(target)[1].lower() in \
                       ['.' + x for x in self.image_extenstions] and \
                       target[:10] != 'attachment':
                        line = line.replace(
                            target,
                            self.process_image_url(target)
                            )
                        self.process_success += 1
        return line

    def process_image_url(self, transclude):
        "download image and replace image url"""
        logging.info('transclude')
        logging.info(transclude)
        url = self.image_url_re.findall(transclude)[0]
        image = self.fetchImage(url)
        return 'attachment:' + self.addAttachment(url, image)

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

    def fetchImage(self, url):
        """save image to local"""
        try:
            handler = urllib2.urlopen(url)
            return handler.read()
        except Exception, e:
            raise e # TODO add extract exception
        #finally:
            #handler.close()

    def addAttachment(self, name, content):
        """add image to attachment"""
        if os.path.splitext(name)[1].lower() not in \
           ['.' + x for x in self.image_extenstions]:
            name += '.jpg' # if the url didn't contain a image extention
        AttachFile.add_attachment(self.request,
                                  self.pagename,
                                  name,
                                  content,
                                  True)
        return wikiutil.taintfilename(name)

    def replaceImages(self):
        """edit the raw, replace image url with attachment url"""

        result = ''
        for line in WikiParser.eol_re.split(self.page.get_raw_body()):
            # save the ident
            indent = WikiParser.indent_re.match(line).group(0)
            result += indent + self.replaceImageLine(line.strip())
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
    image2attach.process()
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
