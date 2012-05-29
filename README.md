# Image2Attach #

## What's this ##

Image2Attach is a extension for [MoinMoin](http://moinmo.in).
It can create a page action to save images from web to page's attachments.

## Requirment ##

* MoinMoin 1.9 (I only test in this version.)

## Install ##

* copy action/Image2Attach.py to data/plugin/action/
* restart python server

## Usage ##

Go into a page, click `more action` - `Image2Attach` .
It will take a while to fetch the images,
after that it will save the image to attachments and replace the
image's link with attachment's link.
Finnally it will commit a change with message
`internet image save to attachment` to wiki.

Enjoy it, any bugs can report to
[Issue Report](https://github.com/alswl/image2attach/issues).

## Support ##

You can get some develop infomation in
[Image2attach - Log4D](http://log4d.com/tag/image2attach)

## Licence ##

Distributed under the [GPL v2](http://www.gnu.org/licenses/gpl-2.0.htmwl)

// vim: set ft=markdown:
