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

class PhotoPreview(gtk.Image):
    __gtype_name__ = "PhotoPreview"

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