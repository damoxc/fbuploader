# -*- coding: utf-8 -*-
# fbuploader/main_window.py
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
import urllib
import logging
import facebook
import tempfile
import gtk.glade
import threading
from pkg_resources import resource_filename
from fbuploader.common import Window, signal
from fbuploader.photochooser_dialog import PhotoChooser
from fbuploader.widgets import PhotoView, PhotoPreview

log = logging.getLogger(__name__)

FB_API_KEY = "a7b58c2702d421a270df42cfff9f4007"
FB_SECRET_KEY = "a01ccd6ae703d353a701ea49f63b7667"

class AlbumDownloader(threading.Thread):
    def __init__(self, facebook, callback):
        super(AlbumDownloader, self).__init__()
        self.facebook = facebook
        self.callback = callback
    
    def run(self):
        log.info("Downloading photo albums")
        self.callback(self.facebook.photos.getAlbums())

class AlbumCoverDownloader(threading.Thread):
    def __init__(self, facebook, album, callback):
        super(AlbumCoverDownloader, self).__init__()
        self.facebook = facebook
        self.album = album
        self.callback = callback

    def run(self):
        if "cover_file" in self.album:
            self.callback(self.album["cover_file"])
            return

        log.info("Retreiving album cover photo")
        cover_photo = self.facebook.photos.get(pids=self.album["cover_pid"])
        if cover_photo:
            cover_photo = cover_photo[0]
        else:
            log.warning("Album has no cover photo")
            return

        data_dir = os.path.join(tempfile.gettempdir(), "fbuploader")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        path = os.path.join(data_dir, os.path.basename(cover_photo["src"]))
        if not os.path.exists(path):
            log.info("Downloading album cover photo")
            urllib.urlretrieve(cover_photo["src"], path)
            
        self.album["cover_file"] = path
        self.callback(path)

class MainWindow(Window):

    def __init__(self):
        log.info("Initializing Main Window")
        glade_file = resource_filename("fbuploader", "glade/fbuploader.glade")
        super(MainWindow, self).__init__(glade_file, "main_window")
        self.facebook = facebook.Facebook(FB_API_KEY, FB_SECRET_KEY)
        self.albums = []
        
        # Get widgets from the tree
        self.albums_combobox = self.tree.get_widget("albums_combobox")
        self.album_cover = self.tree.get_widget("albumcover_image")
        self.album_name = self.tree.get_widget("albumname_entry")
        self.album_description = self.tree.get_widget("albumdescription_entry")
        self.album_location = self.tree.get_widget("albumlocation_entry")
        
        self.preview_image = self.tree.get_widget("preview_image")
        self.caption_entry = self.tree.get_widget("caption_entry")
        self.tags_entry = self.tree.get_widget("tags_entry")
        
        # Remove the first item in the combobox (left there so glade autocreates
        # a store)
        self.albums_combobox.remove_text(0)
        
        # Disable the album form, we don't want it active until we have data.
        self.set_form_sensitive(False)
        
        # Add in the photos view widget
        self.photos_view = PhotoView()
        self.tree.get_widget("photos_scrolled").add(self.photos_view)
        self.photos_view.connect("selection-changed", self.on_photos_view_selection_changed)
        
        # Add in the preview photo image widget
        self.preview_image = PhotoPreview()
        self.tree.get_widget("preview_viewport").add(self.preview_image)
        
        # Initialize the photo_chooser variable that will contain the
        # filechooser dialog.
        self.photo_chooser = None
        
        # Initialize the photo_info dictionary used to store the captions
        # and tags for the photos.
        self.photo_info = {}
    
    def set_form_sensitive(self, sensitive=True):
        action = sensitive and "Enabling" or "Disabling"
        log.info("%s album form", action)
        self.albums_combobox.set_sensitive(sensitive)
        self.album_cover.set_sensitive(sensitive)
        self.album_name.set_sensitive(sensitive)
        self.album_description.set_sensitive(sensitive)
        self.album_location.set_sensitive(sensitive)
        
    def get_signals(self):
        signals = super(MainWindow, self).get_signals()
        signals["on_main_window_event_after"] = self.quit
        signals["on_quit_menuitem_activate"] = self.quit
        signals["on_main_window_destroy"] = self.quit
        return signals
    
    def quit(self, *args):
        log.info("Shutting down main window")
        if self.photo_chooser is not None:
            self.photo_chooser.dialog.hide()
        try:
            gtk.main_quit()
        except RuntimeError: pass
    
    def clear_photo_albums(self):
        albums = self.albums[:]
        for album in albums:
            self.albums.remove(album)
            self.albums_combobox.remove_text(0)
    
    def get_album_by_name(self, name):
        for album in self.albums:
            if album["name"] == name:
                return album
    
    def on_got_albums(self, albums):
        self.clear_photo_albums()
        for album in albums:
            self.albums.append(album)
            self.albums_combobox.append_text("%s (%d Photos)" % (album["name"],
                                                                 album["size"]))
        self.set_form_sensitive(True)
    
    def on_got_albumcover(self, path):
        self.album_cover.set_from_file(path)
    
    @signal
    def on_main_window_show(self, e):
        self.set_form_sensitive(True)
        return
        logged_in = gtk.MessageDialog(buttons=gtk.BUTTONS_OK)
        logged_in.set_markup("Press OK once you have logged in.")
        self.fb_token = self.facebook.auth.createToken()
        self.facebook.login()
        log.info("Logging in to Facebook")
        if logged_in.run() == gtk.RESPONSE_OK:
            logged_in.destroy()
            try:
                self.fb_session = self.facebook.auth.getSession()
            except Exception, e:
                log.error("Login failed")
            else:
                log.info("Successfully logged in")
                AlbumDownloader(self.facebook, self.on_got_albums).start()
        else:
            log.error("Login failed")
    
    @signal
    def on_albums_combobox_changed(self, e):
        index = self.albums_combobox.get_active()
        if not self.albums:
            return
        self.album_cover.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
        album = self.albums[index]
        self.album_name.set_text(album["name"])
        self.album_description.set_text(album["description"])
        self.album_location.set_text(album["location"])
        AlbumCoverDownloader(self.facebook, album, self.on_got_albumcover).start()

    ## DND Stuff ##
    @signal
    def on_photos_iconview_drag_drop(self, iconview, context, x, y, time):
        context.finish(True, False, time)
        return True
    
    @signal
    def on_photos_iconview_drag_data_received(self, iconview, context, x, y,
                                              selection, info, time):
        print selection.data
        return True

    @signal
    def on_photos_iconview_drag_motion(self, iconview, context, x, y, time):
        context.drag_status(gtk.gdk.ACTION_COPY, time)
        return True

    @signal
    def on_photochoose_button_clicked(self, button):
        if self.photo_chooser is None: self.photo_chooser = PhotoChooser()
        if self.photo_chooser.run() != gtk.RESPONSE_OK:
            return True

        for filename in self.photo_chooser.dialog.get_filenames():
            self.photos_view.add_photo(filename)
    
    @signal
    def on_photos_view_selection_changed(self, *args):
        selected = self.photos_view.get_selected_items()[0]
        model = self.photos_view.get_model()
        filename = model[selected][0]
        assert isinstance(self.preview_image, gtk.Image)
        self.preview_image
        self.preview_image.set_from_file(filename)
        return True