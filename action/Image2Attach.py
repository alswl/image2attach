#!/usr/bin/python
# coding:utf-8

"""
    MoinMoin Extention: image2attach v0.0.3
    Descption: Save page's images to attachments
    @author: alswl <http://log4d.com>
    @date: 2011-12-31
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
        _ = self.request.getText
        if self.process_success > 0:
            PageEditor(self.request, self.pagename)._write_file(
                self.text,
                comment=_(
                    'save images to attachment: %d successful, %d faild' \
                    %(self.process_success, self.process_fail)
                    ),
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
        if transclude != None and \
           not transclude.strip().startswith('{{attachment:') and \
           self.image_url_re.search(transclude) != None:
                url = self.image_url_re.search(transclude).group(0)
                return line.replace(url, self.process_image_url(url))
        else:
            return line

    def process_link(self, line, groups):
        """[[link|{{image}}]]"""
        target = groups.get('link_target', '')
        desc = groups.get('link_desc', '') or ''

        # process image in link
        match = WikiParser.scan_re.match(desc.strip())
        if match != None:
            for type, hit in match.groupdict().items():
                if hit is not None and type == 'transclude':
                    attach_desc = self.process_transclude(desc,
                                                          match.groupdict())
                    line = line.replace(desc, attach_desc)

        # process target which url contains .jpg/.gif/.png
        if os.path.splitext(target)[1].lower() in \
           ['.' + x for x in self.image_extenstions] and \
           target[:10] != 'attachment':
            line = line.replace(
                target,
                self.process_image_url(target)
                )
        return line

    def process_image_url(self, url):
        "download image and replace image url"""
        try:
            #url = self.image_url_re.findall(transclude)[0]
            image = self.fetchImage(url)
            self.process_success += 1
            url = url.replace('%20', '') # fix '%20' -> ' ' bug
            return 'attachment:' + self.addAttachment(url, image)
        except Exception, e:
            self.process_fail += 1
            return url

    def fetchImage(self, url):
        """save image to local"""
        try:
            handler = urllib2.urlopen(url.encode('utf-8'))
            return handler.read()
        except Exception, e:
            logging.error(u'get %s failed' %url)
            raise e

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

class Parser(object):
    """Transform the wiki where has image"""

    image_url_rule = r'https?://[^|^}]+' # image url's regex rule
    image_url_re = re.compile(image_url_rule, re.VERBOSE | re.UNICODE)
    image_extenstions = ['jpg', 'gif', 'png']

    def __init__(self):
        pass

    def parse(self, raw, callback):
        text = ''
        for line in WikiParser.eol_re.split(raw):
            text += self.process_line(line, callback) + '\n'
        return text[:-1]

    def process_line(self, line, callback):
        """process each line in wiki text"""
        results = []
        # save the indent
        indent = WikiParser.indent_re.match(line).group(0) or ''
        lastpos = 0 # absolute position within line

        while lastpos <= len(line):
            parser_scan_re = re.compile(
                WikiParser.parser_scan_rule % re.escape(WikiParser.parser_unique),
                re.VERBOSE|re.UNICODE
            )
            scan_re = None and parser_scan_re or WikiParser.scan_re
            match = scan_re.search(line, lastpos)
            if match != None:
                for type, hit in match.groupdict().items():
                    # only process the type may contain images
                    if hit is not None:
                        #if type in ('transclude', 'link'):
                        if type == 'transclude':
                            results.append(self.process_transclude(
                                line[lastpos:match.end()],
                                match.groupdict(),
                                callback
                            ))
                        elif type == 'link':
                            results.append(self.process_link(
                                line[lastpos:match.end()],
                                match.groupdict(),
                                callback))
                        elif type in ('transclude_target', 'link_target',
                                      'link_desc'):
                            continue
                        else:
                            results.append(line[lastpos:match.end()])
                            break
                lastpos = match.end()
            else:
                results.append(line[lastpos:])
                break

        return indent + ''.join(results)

    def process_transclude(self, line, groups, callback):
        """# {{http://xxx/xxx.jpg}}"""
        transclude = groups.get('transclude', '')
        if transclude != None \
           and not transclude.strip().startswith('{{attachment:') \
           and self.image_url_re.search(transclude) != None:
            url = self.image_url_re.search(transclude).group(0)
            line = line.replace(url, callback(url))
        return line

    def process_link(self, line, groups, callback):
        """[[link|{{image}}]]"""
        target = groups.get('link_target', '')
        desc = groups.get('link_desc', '') or ''

        # process image in link
        match = WikiParser.scan_re.match(desc.strip())
        if match != None:
            for type, hit in match.groupdict().items():
                if hit is not None and type == 'transclude':
                    attach_desc = self.process_transclude(desc,
                                                          match.groupdict(),
                                                          callback)
                    line = line.replace(desc, attach_desc)

        # process target which url contains .jpg/.gif/.png
        if os.path.splitext(target)[1].lower() in \
           ['.' + x for x in self.image_extenstions] and \
           target[:10] != 'attachment':
            line = line.replace(target, callback(target))
        return line

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
