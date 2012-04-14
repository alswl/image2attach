#!/usr/bin/python
# coding:utf-8

import sys
import os
import unittest

import MoinMoin
try:
    moin_path = MoinMoin.__path__[0] # fix for test
except IndexError:
    raise ImportError
sys.path.append(os.path.join(moin_path, 'support'))

from Image2Attach import Parser

class ParserTest(unittest.TestCase):
    """
    test case:
        run this python file in env that has MoinMoin,
    """

    def test1(self):
        url = u'http://pic002.cnblogs.com/images/2011/125698/2011011817563992.gif'
        html = u'{{%s}}' %url
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:[%s]' %x),
                         u'{{attachment:[%s]}}' %url)

    def test2(self):
        url = u'http://pic002.cnblogs.com/images/2011/125698/2011011817563992.gif'
        html = u'图片 <<BR>>\n{{%s}}' %url
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:[%s]' %x),
                         u'图片 <<BR>>\n{{attachment:[%s]}}' %url)

    def test3(self):
        url = u'http://pic002.cnblogs.com/images/2011/125698/2011011817563992.png'
        html = u'图片 <<BR>> {{%s}}' %url
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:[%s]' %x),
                         u'图片 <<BR>> {{attachment:[%s]}}' %url)

    def test4(self):
        url = u'https://pic002.cnblogs.com/images/2011/125698/2011011817563992.JPG'
        html = u'<<BR>> {{%s}}' %url
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:[%s]' %x),
                         u'<<BR>> {{attachment:[%s]}}' %url)

    def test5(self):
        url = u'https://pic002.cnblogs.com/images/2011/125698/2011011817563992.Jpg'
        html = u'[[http://baidu.com|{{%s}}]]' %url
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:[%s]' %x),
                         u'[[http://baidu.com|{{attachment:[%s]}}]]' %url)

    def test6(self):
        url1 = u'http://pic002.cnblogs.com/images/2011/125698/2011011817563992_.png'
        url2 = u'https://pic002.cnblogs.com/images/2011/125698/2011011817563992.Jpg'
        html = u'[[%s|{{%s}}]]' %(url1, url2)
        #import ipdb; ipdb.set_trace()
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:#%s#' %x),
                         u'[[attachment:#%s#|{{attachment:#%s#}}]]' %(url1, url2))

    def test7(self):
        url = u'https://pic002.cnblogs.com/images/2011/125698/2011011817563992.Jpg'
        html = u"""
来看一个经典的三栏布局：<<BR>> {{%s}} <<BR>> 从内容出发（[[http://lifesinger.org/blog/?p=298|渐进增强]]的核心思想），一份合理的HTML结构如下：
        """.strip() %(url)
        #import ipdb; ipdb.set_trace()
        self.assertEqual(Parser().parse(html, lambda x: 'attachment:#%s#' %x),
                         html.replace(url, 'attachment:#%s#' %url))

if __name__ == '__main__':
    unittest.main()
