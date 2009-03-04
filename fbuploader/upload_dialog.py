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

import os
import gtk
import logging
import threading
from fbuploader.common import Dialog, signal

log = logging.getLogger(__name__)

class PhotoUploader(threading.Thread):

    def __init__(self, facebook, aid, upload_cb, tag_cb):
        super(PhotoUploader, self).__init__()
        self.upload_cb = upload_cb
        self.tag_cb = tag_cb
        self.queue = []
        self.aid = aid
        self.do_upload = facebook.photos.upload
        self.add_tag = facebook.photos.addTag
    
    def run(self):
        while 1:
            if not self.queue: break
            photo, info = self.queue.pop(0)
            log.info("Uploading photo: %s", os.path.basename(photo))
            upload_info = self.do_upload(photo, self.aid, info.get("caption"))
            self.upload_cb(photo)
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
            self.tag_cb(photo)
    
    def upload(self, photo, info):
        self.queue.append((photo, info))

class UploadDialog(Dialog):
    
    def __init__(self, main_window):
        super(UploadDialog, self).__init__("upload_dialog")
        log.info("Initializing upload dialog.")
        self.main_window = main_window
        self.total_progressbar = self.tree.get_widget("upload_total_progressbar")
        self.current_progressbar = self.tree.get_widget("upload_current_progressbar")
    
    def run(self):
        self.dialog.show()
        aid = self.main_window.album["aid"]
        facebook = self.main_window.facebook
        
        uploader = PhotoUploader(facebook, aid, self.on_upload, self.on_tag)
        self.total_photos = len(self.main_window.photos)
        self.complete_photos = 0
        for photo in self.main_window.photos:
            uploader.upload(photo, self.main_window.photo_info[photo])
        uploader.start()
        
    def on_upload(self, photo):
        self.complete_photos += 1
        progress = (self.complete_photos / float(self.total_photos))
        self.total_progressbar.set_fraction(progress)
    
    def on_tag(self, photo):
        pass

    @signal
    def on_upload_dialog_delete_event(self, *args):
        self.dialog.hide()
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    
    @signal
    def on_upload_cancel_button_clicked(self, *args):
        pass