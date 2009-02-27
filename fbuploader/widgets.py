# -*- coding: utf-8 -*-
# fbuploader/widgets.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

import os
import gtk
import logging

log = logging.getLogger(__name__)

class PhotoPreview(gtk.EventBox):
    __gtype_name__ = "PhotoPreview"
    
    def __init__(self):
        super(PhotoPreview, self).__init__()
        self.image = gtk.Image()
        self.add(self.image)
        self.pixbuf = None
        self.is_resize = False
        self.filename = None
        self.image.connect("size-allocate", self.on_image_size_allocate)
        self.connect("button-press-event", self.on_button_press_event)
    
    def _scale_image(self, allocation=None):
        allocation = allocation or self.image.get_allocation()
        log.debug("Resizing image (%dx%d)", allocation.width, allocation.height)
        width, height = self.pixbuf.get_width(), self.pixbuf.get_height()
        
        # First stage to resize the picture by the largest dimension
        if width > height:
            log.debug("Image width is bigger")
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        else:
            log.debug("Image height is bigger")
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        
        # Check to ensure that the smaller dimension isn't exceeding the 
        # widgets allocated space.
        if width > allocation.width:
            log.debug("Width still bigger")
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        elif height > allocation.height:
            log.debug("Height still bigger")
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        self.width, self.height = width, height
        return self.pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    
    def on_image_size_allocate(self, *args):
        if self.pixbuf is None: return
        if self.is_resize:
            self.image.set_from_pixbuf(self._scale_image())
            self.is_resize = False
        else:
            self.is_resize = True
    
    def on_button_press_event(self, widget, event):
        allocation = self.image.get_allocation()
        x, y = event.x, event.y
        if allocation.width == self.width:
            y -= int((allocation.height - self.height) / 2.0)
        elif allocation.height == self.height:
            x -= int((allocation.width - self.width) / 2.0)
        x = (x / self.width) * 100
        y = (y / self.height) * 100

    def set_from_file(self, filename):
        self.filename = filename
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        scaled_pixbuf = self._scale_image()
        self.image.set_from_pixbuf(scaled_pixbuf)

class PhotoView(gtk.IconView):
    __gtype_name__ = "PhotoView"
    
    def __init__(self, model=None):
        photo_model = gtk.ListStore(str, str, gtk.gdk.Pixbuf)
        super(PhotoView, self).__init__(photo_model)
        self.set_text_column(1)
        self.set_pixbuf_column(2)
        self.set_item_width(100)
    
    def add_photo(self, filename):
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        if width > height:
            ratio = width / 100.0
            width, height = 100, int(height / ratio)
        else:
            ratio = height / 100.0
            width, height = int(width / ratio), 100

        scaled = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        del width
        del height
        del pixbuf
        name = os.path.basename(filename)
        self.get_model().append((filename, name, scaled))