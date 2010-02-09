# -*- coding: utf-8 -*-
# fbuploader/photochooser_dialog.py
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
from pkg_resources import resource_filename
from fbuploader.common import Dialog, signal

log = logging.getLogger(__name__)

class PhotoChooser(Dialog):
    
    window_name = 'photochooser_dialog'

    def __init__(self):
        super(PhotoChooser, self).__init__()
        log.info('Initializing photochooser dialog.')
        del self.builder
        
        # We want to be able to select multiple photos.
        self.dialog.set_select_multiple(True)
        
        # We also only want photos displayed.
        photo_filter = gtk.FileFilter()
        photo_filter.add_mime_type('image/gif')
        photo_filter.add_mime_type('image/jpeg')
        photo_filter.add_mime_type('image/tiff')
        photo_filter.add_mime_type('image/png')
        self.dialog.set_filter(photo_filter)
    
    @signal
    def on_photochooser_dialog_delete_event(self, *args):
        self.dialog.hide()
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    on_photochooser_cancel_button_clicked = on_photochooser_dialog_delete_event
    
    @signal
    def on_photochooser_open_button_clicked(self, *args):
        if len(self.dialog.get_filenames()) == 0:
            return True

        self.dialog.hide()
        self.dialog.response(gtk.RESPONSE_OK)
        return True
    on_photochooser_dialog_file_activated = on_photochooser_open_button_clicked
        
