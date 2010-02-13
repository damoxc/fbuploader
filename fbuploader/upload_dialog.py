# -*- coding: utf-8 -*-
# fbuploader/upload_dialog.py
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

import os
import gtk
import gobject
import logging

from math import ceil
from pkg_resources import resource_filename
from fbuploader.common import Dialog, signal, json

log = logging.getLogger(__name__)

def format_tag(tag):
    tag_dict = {'x': float(tag[1]), 'y': float(tag[2])}
    if type(tag[0]) is int:
        tag_dict['tag_uid'] = tag[0]
    else:
        tag_dict['tag_text'] = tag[0]
    return tag_dict

class PhotoUploader(gobject.GObject):

    __gtype_name__ = 'PhotoUploader'

    def __init__(self, facebook, aid):
        super(PhotoUploader, self).__init__()
        self.queue = []
        self.aid = aid
        self.fb_upload = facebook.photos.upload
        self.fb_add_tag = facebook.photos.addTag
        self.running = True

    def abort(self):
        """
        Cancel the running upload.
        """
        self.running = False

    def add_photo(self, photo, info):
        """
        Adds a photo to the upload queue.

        :param photo: x
        :type photo: the photos name
        """
        self.queue.append((photo, info))

    def _do_upload(self, photo, info, attempt=0, *args):
        log.debug('do_upload(%r, %r, %r, attempt=%r, %r)', self, photo, info, attempt, args)
        log.info('Uploading photo: %s', os.path.basename(photo))
        
        self.emit('before-upload', photo)

        def cb_upload(count, chunk_size, total_size):
            self.emit('upload', photo, count, chunk_size, total_size)
            
        self.fb_upload(photo, self.aid, info.get('caption'), callback=cb_upload) \
            .addCallback(self._on_photo_uploaded, photo, info) \
            .addErrback(self._on_upload_error, photo, info, attempt)

    def _on_upload_error(self, err, photo, info, attempt):
        log.error('Unable to upload photo to aid: %s' % self.aid)
        log.exception(e)
        # Check to see if we should retry or give up.
        if attempt >= 2:
            log.error('Failed uploading 3 times, giving up')
        else:
            gobject.idle_add(self._do_upload, photo, info, attempt + 1)

    def _on_photo_uploaded(self, result, photo, info):
        pid = str(result['pid'])
        gobject.idle_add(self._do_tagging, photo, info, pid)
    
    def _do_tagging(self, photo, info, pid, attempt=0):
        tags = map(format_tag, info.get('tags', []))

        # There are no valid tags in the tag info
        if not tags:
            self.emit('after-upload', photo)
            gobject.idle_add(self._upload)
            return

        tags = json.dumps(tags)
        log.info('Tagging photo: %s', os.path.basename(photo))
        self.emit('before-tag', photo)
        log.debug('Running add_tag(%r, %r)', pid, tags)
        self.add_tag(pid, tags=tags) \
            .addCallback(self._on_tag_complete, photo) \
            .addErrback(self._on_tag_error, pid, attempt)

    def on_tag_error(self, err, pid, attempt):
        log.error('Unable to tag photo with pid: %s' % pid)
        log.exception(e)

        # Check to see if we should retry or give up.
        if attempt >= 2:
            log.error('Failed tagging 3 times, giving up')
        else:
            gobject.idle_add(self._do_tagging, photo, info, pid,
                attempt + 1)

    def on_tag_complete(self, res, photo):
        self.emit('after-tag', photo)
        self.emit('after-upload', photo)
        gobject.idle_add(self._upload)

    def start_upload(self):
        """
        Starts the upload.
        """
        gobject.idle_add(self._upload)

    def _upload(self):
        """
        Upload the next photo in the queue.
        """
        # we've been told to abort so we should probably do so
        if not self.running:
            return

        # all the photos have been uploaded so lets return
        if not self.queue:
            return

        # pop the photo info from the queue and start the upload
        photo, info = self.queue.pop(0)
        gobject.idle_add(self._do_upload, photo, info)

gobject.signal_new('before-upload', PhotoUploader,  gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new('upload', PhotoUploader,  gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE, ((gobject.TYPE_PYOBJECT,)*4))
gobject.signal_new('after-upload', PhotoUploader,  gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new('before-tag', PhotoUploader,  gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new('after-tag', PhotoUploader,  gobject.SIGNAL_RUN_LAST,
    gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

class UploadDialog(Dialog):
    
    window_name = 'upload_dialog'
    
    def __init__(self, main_window):
        super(UploadDialog, self).__init__()
        log.info('Initializing upload dialog.')
        self.main_window = main_window
        self.image = self.builder.get_object('upload_image')
        self.image.set_from_file(resource_filename('fbuploader',
                                                   'data/fbuploader64.png'))
        self.total = self.builder.get_object('upload_total')
        self.total_progressbar = self.builder.get_object('upload_total_progressbar')
        self.current = self.builder.get_object('upload_current')
        self.current_progressbar = self.builder.get_object('upload_current_progressbar')
    
    def run(self):
        aid = self.main_window.album['aid']
        facebook = self.main_window.facebook
        
        # Set up the photo uploader
        self.uploader = PhotoUploader(facebook, aid)
        self.uploader.connect('before-upload', self.on_before_upload)
        self.uploader.connect('upload', self.on_upload)
        self.uploader.connect('after-upload', self.on_after_upload)
        self.uploader.connect('before-tag', self.on_before_tag)
        self.uploader.connect('after-tag', self.on_after_tag)
        
        self.total_photos = len(self.main_window.photos)
        self.complete_photos = 0
        self.total.set_text('0/%d' % self.total_photos)
        for photo in self.main_window.photos:
            self.uploader.add_photo(photo, self.main_window.photo_info[photo])
        self.uploader.start_upload()

        response = self.dialog.run()
        self.dialog.hide()
        
        # Tidy up for the next run
        self.total.set_text('')
        self.total_progressbar.set_fraction(0)
        self.current_progressbar.set_fraction(0)
        self.current.set_text('')
        return response
    
    def on_before_upload(self, uploader, photo):
        text = '%s (Uploading 0%%)' % os.path.basename(photo)
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
        self.dialog.queue_draw()
        gtk.main_iteration()
    
    def on_upload(self, uploader, photo, count, chunk_size, total_size):
        progress = count / ceil(total_size / float(chunk_size))
        name = os.path.basename(photo)
        text = '%s (Uploading %.0f%%)' % (name, progress*100)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        log.debug("Setting current progressbar to '%f'", round(progress, 2))
        self.current_progressbar.set_fraction(progress)
        self.dialog.queue_draw()
        gtk.main_iteration()
        
    def on_after_upload(self, uploader, photo):
        self.complete_photos += 1
        progress = (self.complete_photos / float(self.total_photos))
        text = '%s (Uploading 100%%)' % os.path.basename(photo)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        log.debug("Setting total progressbar to '%f'", progress)
        self.total_progressbar.set_fraction(progress)
        self.total.set_text('%d/%d' % (self.complete_photos, self.total_photos))
        self.image.set_from_file(resource_filename('fbuploader',
                                                   'data/fbuploader64.png'))
        
        self.dialog.queue_draw()
        gtk.main_iteration()
        if self.complete_photos == self.total_photos:
            self.dialog.response(gtk.RESPONSE_OK)
    
    def on_before_tag(self, uploader, photo):
        text = '%s (Tagging)' % os.path.basename(photo)
        log.debug("Setting current label to '%s'", text)
        self.current.set_text(text)
        self.dialog.queue_draw()
        gtk.main_iteration()
    
    def on_after_tag(self, uploader, photo):
        log.debug("Setting current label to ''")
        self.current.set_text('')
        self.dialog.queue_draw()
        gtk.main_iteration()

    @signal
    def on_upload_dialog_delete_event(self, *args):
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    
    @signal
    def on_upload_cancel_button_clicked(self, *args):
        self.uploader.abort()
        self.dialog.response(gtk.RESPONSE_CANCEL)
