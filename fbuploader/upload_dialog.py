# -*- coding: utf-8 -*-
# fbuploader/upload_dialog.py
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

import gtk
import logging
import threading
from fbuploader.common import Dialog, signal

log = logging.getLogger(__name__)

class UploadDialog(Dialog):
    
    def __init__(self, main_window):
        super(UploadDialog, self).__init__("upload_dialog")
        log.info("Initializing upload dialog.")
        self.main_window = main_window
        self.do_upload = self.main_window.facebook.photos.upload
        self.add_tag = self.main_window.facebook.photos.addTag
        self.aid = self.main_window.album["aid"]
    
    def run(self):
        for photo in self.main_window.photos:
            self.upload_photo(photo)
    
    def upload_photo(self, photo):
        info = self.main_window.photo_info[photo]
        log.info("Uploading photo: %s", photo)
        upload_info = self.do_upload(photo, self.aid, info.get("caption"))
        pid = upload_info["pid"]
        def format_tag(tag):
            tag_dict = {"x": tag[1], "y": tag[2]}
            if type(tag[0]) is int:
                tag_dict["tag_uid"] = tag[0]
            else:
                tag_dict["tag_text"] = tag[0]
        tags = map(format_tag, info.get("tags", []))
        log.info("Tagging photo: %s", photo)
        if tags:
            self.add_tag(pid, tags=tags)

    @signal
    def on_upload_dialog_delete_event(self, *args):
        self.dialog.hide()
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    
    @signal
    def on_upload_cancel_button_clicked(self, *args):
        pass