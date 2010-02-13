# -*- coding: utf-8 -*-
# fbuploader/new_album_dialog.py
#
# Copyright (C) 2009-2010 Damien Churchill <damoxc@gmail.com>
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

import gtk
import logging

from fbuploader.common import Dialog, signal

log = logging.getLogger(__name__)

class NewAlbumDialog(Dialog):

    window_name = 'new_album_dialog'
    
    def __init__(self, main_window):
        super(NewAlbumDialog, self).__init__(main_window.window)
        self.name = self.builder.get_object('album_name_entry')
        self.location = self.builder.get_object('album_location_entry')
        self.description = self.builder.get_object('album_description_entry')
        del self.builder
        self.facebook = main_window.facebook
        self.refresh_albums = main_window.refresh_photo_albums
    
    def on_delete(self, *args):
        return super(NewAlbumDialog, self).on_delete(*args)
    
    @signal
    def on_new_album_ok_button_clicked(self, *args):
        name = self.name.get_text()
        location = self.location.get_text() or None
        description = self.description.get_text() or None
        self.facebook.photos.createAlbum(name, location, description) \
            .addCallback(self.on_album_created) \
            .addErrback(self.on_album_error)

    def on_album_error(self, err):
        log.exception(err)
        self.dialog.response(gtk.RESPONSE_NO)
        self.dialog.hide()

    def on_album_created(self, album):
        self.refresh_albums()
        self.dialog.response(gtk.RESPONSE_OK)
        self.dialog.hide()
    
    @signal
    def on_new_album_cancel_button_clicked(self, *args):
        self.on_delete()
