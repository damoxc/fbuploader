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
from fbuploader.common import Events, get_session_dir

log = logging.getLogger(__name__)

def scale_image(pixbuf, width=None, height=None):
    if width is None and height is None:
        raise Exception("Neither height nor width has been specified")
    
    cur_width = pixbuf.get_width()
    cur_height = pixbuf.get_height()
    
    if cur_width >= width or cur_height >= height:
        # We need to do a resize
        pass

class PhotoPreview(Events, gtk.EventBox):
    __gtype_name__ = "PhotoPreview"
    
    def __init__(self):
        super(PhotoPreview, self).__init__()
        gtk.EventBox.__init__(self)
        self.image = gtk.Image()
        self.add(self.image)
        self.pixbuf = None
        self.is_resize = False
        self.filename = None
        self.image.connect("size-allocate", self.on_image_size_allocate)
        self.connect("button-press-event", self.on_button_press_event)
    
    def _scale_image(self, allocation=None):
        allocation = allocation or self.image.get_allocation()
        log.debug("Resizing image")
        log.debug("Allocated size (%dx%d)", allocation.width, allocation.height)
        width, height = self.pixbuf.get_width(), self.pixbuf.get_height()
        log.debug("Image size (%dx%d)", width, height)
        
        # First stage to resize the picture by the largest dimension
        if width > height:
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        else:
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        
        log.debug("Scaled size run 1 (%dx%d)", width, height)
        # Check to ensure that the smaller dimension isn't exceeding the 
        # widgets allocated space.
        if width > allocation.width:
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        elif height > allocation.height:
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        log.debug("Scaled size run 2 (%dx%d)", width, height)
        self.width, self.height = width, height
        return self.pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    
    def on_image_size_allocate(self, *args):
        allocation = self.get_allocation()
        """if self.pixbuf is None: return
        if self.is_resize:
            self.image.set_from_pixbuf(self._scale_image())
            self.is_resize = False
        else:
            self.is_resize = True"""
    
    def on_button_press_event(self, widget, event):
        if not hasattr(self, "width"): return
        allocation = self.image.get_allocation()
        x, y = event.x, event.y
        if allocation.width == self.width:
            y -= int((allocation.height - self.height) / 2.0)
        elif allocation.height == self.height:
            x -= int((allocation.width - self.width) / 2.0)
        x = (x / self.width) * 100
        y = (y / self.height) * 100
        self.fire("tag-event", x, y, event)

    def set_from_file(self, filename):
        self.filename = filename
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        scaled_pixbuf = self._scale_image()
        self.image.set_from_pixbuf(scaled_pixbuf)
        self.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))

class PhotoView(gtk.IconView):
    __gtype_name__ = "PhotoView"
    
    def __init__(self, model=None):
        photo_model = gtk.ListStore(str, str, gtk.gdk.Pixbuf)
        super(PhotoView, self).__init__(photo_model)
        self.set_text_column(1)
        self.set_pixbuf_column(2)
        self.set_item_width(100)
    
    def add_photo(self, filename):
        # Load the photo from the specified file
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        
        # Get the widget and height of the photo, we may need to do some
        # scaling!
        width, height = pixbuf.get_width(), pixbuf.get_height()
        
        if width > 604:
            # We need to resize the photo to the largest that facebook accepts,
            # there is zero point in working with anything larger.
            ratio = width / 604.0
            width = 604
            height = int(height / ratio)
            pixbuf = pixbuf.scale_simple(width, height,
                                         gtk.gdk.INTERP_BILINEAR)
        
        # Save the possibly scaled pixbuf in the session directory
        filename = get_session_dir(os.path.basename(filename))
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        pixbuf.save(filename, "jpeg", {"quality": "79"})
        self.load_photo(filename, pixbuf, (width, height))        
        return filename, width, height

    def load_photo(self, filename, pixbuf=None, size=None):
        # Load the photo from the specified file or use the passed in pixbuf
        pixbuf = pixbuf or gtk.gdk.pixbuf_new_from_file(filename)
        
        if size is not None:
            width, height = size
        else:
            width, height = pixbuf.get_width(), pixbuf.get_height()
        
        # Scale the image to produce a thumbnail
        if width > height:
            ratio = width / 100.0
            width, height = 100, int(height / ratio)
        else:
            ratio = height / 100.0
            width, height = int(width / ratio), 100

        scaled = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_HYPER)
        del pixbuf
        name = os.path.basename(filename)
        self.get_model().append((filename, name, scaled))
        self.queue_resize()