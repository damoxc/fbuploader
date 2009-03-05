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
from math import ceil
from pkg_resources import resource_filename
from fbuploader.common import Dialog, Thread, signal

try:
    import json as simplejson
except:
    import simplejson
    

log = logging.getLogger(__name__)

class PhotoUploader(Thread):

    def __init__(self, facebook, aid):
        super(PhotoUploader, self).__init__()
        self.queue = []
        self.aid = aid
        self.do_upload = facebook.photos.upload
        self.add_tag = facebook.photos.addTag
        self.running = True
    
    def abort(self):
        self.running = False
    
    def run(self):
        while self.running:
            if not self.queue: break
            photo, info = self.queue.pop(0)
            name = os.path.basename(photo)
            log.info("Uploading photo: %s", name)
            
            self.fire("before-upload", photo)
            def cb_upload(count, chunk_size, total_size):
                self.fire("upload", photo, count, chunk_size, total_size)
            upload_info = self.do_upload(photo, self.aid, info.get("caption"),
                                         callback=cb_upload)
            
            pid = str(upload_info["pid"])
            def format_tag(tag):
                tag_dict = {"x": float(tag[1]), "y": float(tag[2])}
                if type(tag[0]) is int:
                    tag_dict["tag_uid"] = tag[0]
                else:
                    tag_dict["tag_text"] = tag[0]
                return tag_dict
            tags = map(format_tag, info.get("tags", []))
            if tags:
                tags = simplejson.dumps(tags)
                log.info("Tagging photo: %s", name)
                self.fire("before-tag", photo)
                log.debug("Running add_tag(%r, %r)", pid, tags)
                self.add_tag(pid, tags=tags)
                self.fire("after-tag", photo)
            
            self.fire("after-upload", photo)
    
    def upload(self, photo, info):
        self.queue.append((photo, info))

class UploadDialog(Dialog):
    
    def __init__(self, main_window):
        super(UploadDialog, self).__init__("upload_dialog")
        log.info("Initializing upload dialog.")
        self.main_window = main_window
        self.image = self.tree.get_widget("upload_image")
        self.image.set_from_file(resource_filename("fbuploader",
                                                   "data/fbuploader64.png"))
        self.total = self.tree.get_widget("upload_total")
        self.total_progressbar = self.tree.get_widget("upload_total_progressbar")
        self.current = self.tree.get_widget("upload_current")
        self.current_progressbar = self.tree.get_widget("upload_current_progressbar")
    
    def run(self):
        aid = self.main_window.album["aid"]
        facebook = self.main_window.facebook
        
        # Set up the photo uploader
        self.uploader = PhotoUploader(facebook, aid)
        self.uploader.on("before-upload", self.on_before_upload)
        self.uploader.on("upload", self.on_upload)
        self.uploader.on("after-upload", self.on_after_upload)
        self.uploader.on("before-tag", self.on_before_tag)
        self.uploader.on("after-tag", self.on_after_tag)
        
        self.total_photos = len(self.main_window.photos)
        self.complete_photos = 0
        self.total.set_text("0/%d" % self.total_photos)
        for photo in self.main_window.photos:
            self.uploader.upload(photo, self.main_window.photo_info[photo])
        self.uploader.start()

        response = self.dialog.run()
        self.dialog.hide()
        
        # Tidy up for the next run
        self.total.set_text("")
        self.total_progressbar.set_fraction(0)
        self.current_progressbar.set_fraction(0)
        self.current.set_text("")
        return response
    
    def on_before_upload(self, photo):
        text = "%s (Uploading 0%%)" % os.path.basename(photo)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        
        # Set a thumbnail of the current image
        pixbuf = gtk.gdk.pixbuf_new_from_file(photo)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        
        # Scale the image to produce a thumbnail
        if width > height:
            ratio = width / 128.0
            width, height = 128, int(height / ratio)
        else:
            ratio = height / 128.0
            width, height = int(width / ratio), 128

        pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_HYPER)
        
        self.image.set_from_pixbuf(pixbuf)
        self.current_progressbar.set_fraction(0)
    
    def on_upload(self, photo, count, chunk_size, total_size):
        progress = count / ceil(total_size / float(chunk_size))
        name = os.path.basename(photo)
        text = "%s (Uploading %.0f%%)" % (name, progress*100)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        log.debug("Setting current progressbar to '%f'", round(progress, 2))
        self.current_progressbar.set_fraction(progress)
        
    def on_after_upload(self, photo):
        self.complete_photos += 1
        progress = (self.complete_photos / float(self.total_photos))
        text = "%s (Uploading 100%%)" % os.path.basename(photo)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        log.debug("Setting total progressbar to '%f'", progress)
        self.total_progressbar.set_fraction(progress)
        self.total.set_text("%d/%d" % (self.complete_photos, self.total_photos))
        self.image.set_from_file(resource_filename("fbuploader",
                                                   "data/fbuploader64.png"))
        
        if self.complete_photos == self.total_photos:
            self.dialog.response(gtk.RESPONSE_OK)
    
    def on_before_tag(self, photo):
        text = "%s (Tagging)" % os.path.basename(photo)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
    
    def on_after_tag(self, photo):
        log.debug("Setting current label to ''")
        self.current.set_text("")

    @signal
    def on_upload_dialog_delete_event(self, *args):
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    
    @signal
    def on_upload_cancel_button_clicked(self, *args):
        self.uploader.abort()
        self.dialog.response(gtk.RESPONSE_CANCEL)