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
import time
import urllib
import logging
import facebook
import tempfile
import gtk.glade
import threading
import cPickle as pickle

from fbuploader.common import *
from fbuploader.friends_dialog import FriendsDialog
from fbuploader.photochooser_dialog import PhotoChooser
from fbuploader.upload_dialog import UploadDialog
from fbuploader.widgets import PhotoView, PhotoPreview

log = logging.getLogger(__name__)

FB_API_KEY = "a7b58c2702d421a270df42cfff9f4007"
FB_SECRET_KEY = "a01ccd6ae703d353a701ea49f63b7667"

class Autosave(threading.Thread):
    def __init__(self, callback, interval=30):
        super(Autosave, self).__init__()
        self.callback = callback
        self.interval = interval
        self.do_abort = False
    
    def abort(self):
        self.do_abort = True
    
    def run(self):
        while not self.do_abort:
            self.callback()
            time.sleep(self.interval)

class AlbumDownloader(threading.Thread):
    def __init__(self, facebook, callback):
        super(AlbumDownloader, self).__init__()
        self.facebook = facebook
        self.callback = callback
    
    def run(self):
        log.info("Downloading photo albums")
        self.callback(self.facebook.photos.getAlbums())

class FriendsDownloader(threading.Thread):
    def __init__(self, facebook, callback):
        super(FriendsDownloader, self).__init__()
        self.facebook = facebook
        self.callback = callback
    
    def run(self):
        log.info("Downloading friend information")
        friends = {}
        uids = self.facebook.friends.get()
        uids.append(self.facebook.uid)
        for friend in self.facebook.users.getInfo(uids):
            friends[friend["name"]] = friend["uid"]
            friends[friend["uid"]] = friend["name"]
        log.debug("Running FriendsDownloader callback")
        self.callback(friends)

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
            log.info("Album has no cover photo")
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

class PhotoAdder(Thread):
    def __init__(self, photos_view):
        super(PhotoAdder, self).__init__()
        self.photos_view = photos_view
        self.photos = []
    
    def add(self, photo):
        self.photos.append(photo)
    
    def run(self):
        for photo in self.photos:
            filename, width, height = self.photos_view.add_photo(photo)
            self.fire("photo-added", filename, width, height)


class MainWindow(Window):

    def __init__(self):
        log.info("Initializing Main Window")
        super(MainWindow, self).__init__("main_window")
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
        self.preview_image.on("tag-event", self.on_photo_tag)
        
        # Initialize the fb_session variable
        self.fb_session = None
        
        # Initialize the photo_chooser variable that will contain the
        # filechooser dialog.
        self.photo_chooser = None
        
        # Initialize the photos list and photo_info dictionary used to store 
        # the order and information (width/height/caption/tags) for the photos
        self.photos = []
        self.photo_info = {}
        
        # Initialize the friends_chooser variable that will contain the
        # friends chooser dialog.
        self.friends_chooser = None
        
        # Initialize the upload_dialog variable that will contain the
        # upload dialog later.
        self.upload_dialog = None
    
    def check_sessions(self):
        sessions = []
        for item in os.listdir(get_config_dir()):
            if os.path.isdir(os.path.join(get_config_dir(), item)):
                sessions.append(item)
        return sessions
    
    def clear_photo_albums(self):
        albums = self.albums[:]
        for album in albums:
            self.albums.remove(album)
            self.albums_combobox.remove_text(0)
        
    def get_signals(self):
        signals = super(MainWindow, self).get_signals()
        signals["on_main_window_event_after"] = self.quit
        signals["on_quit_menuitem_activate"] = self.quit
        signals["on_main_window_destroy"] = self.quit
        return signals
    
    def load(self, session):
        log.info("Loading session %s", session)
        try:
            set_current_session(session)
            path = get_session_dir("data")
            if not os.path.exists(path):
                log.error("Session data doesn't exist")
                return
            session = pickle.load(open(path, "rb"))
        except:
            log.error("Unable to load session %d", session)
            return

        self.photos = session.get("photos")
        self.photo_info = session.get("photo_info")
        self.fb_session = session.get("fb_session")
        
        if self.fb_session["expires"] <= time.time():
            self.login()
        else:
            self.facebook.session_key = self.fb_session["session_key"]
            self.facebook.secret = FB_SECRET_KEY
            self.facebook.uid = self.fb_session["uid"]
        
        for photo in self.photos:
            info = self.photo_info[photo]
            size = (info["width"], info["height"])
            self.photos_view.load_photo(photo, size=size)
    
    def login(self):
        logged_in = MessageBox(buttons=gtk.BUTTONS_OK)
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
        else:
            log.error("Login failed")
    
    def save(self):
        session = {
            "photos": self.photos,
            "photo_info": self.photo_info,
            "fb_session": self.fb_session
        }
        try:
            path = get_session_dir("data")
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            pickle.dump(session, open(path, "wb"))
        except:
            log.error("Unable to save session info")
    
    def set_form_sensitive(self, sensitive=True):
        action = sensitive and "Enabling" or "Disabling"
        log.info("%s album form", action)
        self.albums_combobox.set_sensitive(sensitive)
        self.album_cover.set_sensitive(sensitive)
        self.album_name.set_sensitive(sensitive)
        self.album_description.set_sensitive(sensitive)
        self.album_location.set_sensitive(sensitive)
    
    def set_tags(self, tags):
        names = []
        for tag in tags:
            if type(tag[0]) is int:
                names.append(self.friends[tag[0]])
            else:
                names.append(tag[0])
        self.tags_entry.set_text("; ".join(names))
    
    def quit(self, *args):
        log.info("Shutting down main window")
        if self.photo_chooser is not None:
            self.photo_chooser.dialog.hide()
        if self.friends_chooser is not None:
            self.friends_chooser.dialog.hide()
        try:
            gtk.main_quit()
        except RuntimeError: pass
        
    ## Properties ##
    @property
    def album(self):
        try:
            return self.albums[self.albums_combobox.get_active()]
        except:
            return None

    ## Event Handlers ##
    def on_got_albums(self, albums):
        self.clear_photo_albums()
        for album in albums:
            self.albums.append(album)
            self.albums_combobox.append_text("%s (%d Photos)" % (album["name"],
                                                                 album["size"]))
        self.albums_combobox.set_active(0)
        self.set_form_sensitive(True)
    
    def on_got_friends(self, friends):
        self.friends = friends
    
    def on_got_albumcover(self, path):
        self.album_cover.set_from_file(path)
    
    def on_autosave(self):
        log.info("Autosaving session data")
        self.save()
    
    @signal
    def on_main_window_show(self, e):
        old_sessions = self.check_sessions()
        if old_sessions:
            self.load(old_sessions[0])
        else:
            create_new_session()
            self.login()
        AlbumDownloader(self.facebook, self.on_got_albums).start()
        FriendsDownloader(self.facebook, self.on_got_friends).start()
        Autosave(self.on_autosave).start()
    
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

        def on_photo_added(filename, width, height):
            self.photos.append(filename)
            self.photo_info[filename] = {
                "width": width,
                "height": height
            }

        adder = PhotoAdder(self.photos_view)
        adder.on("photo-added", on_photo_added)
        for filename in self.photo_chooser.dialog.get_filenames():
            adder.add(filename)
        adder.start()
    
    @signal
    def on_photos_view_selection_changed(self, *args):
        selected = self.photos_view.get_selected_items()
        if not selected:
            return

        # If there was a previous image, save the value in the caption field
        if self.preview_image.filename is not None:
            info = self.photo_info.get(self.preview_image.filename, {})
            info["caption"] = self.caption_entry.get_text()
            self.photo_info[self.preview_image.filename] = info
        
        selected = selected[0]
        model = self.photos_view.get_model()
        filename = model[selected][0]
        
        info = self.photo_info.get(filename, {})        
        self.preview_image.set_from_file(filename)
        self.caption_entry.set_text(info.get("caption", ""))
        self.set_tags(info.get("tags", []))
        return True
    
    @signal
    def on_photo_tag(self, x, y, event):
        x, y = int(round(x)), int(round(y))
        if self.friends_chooser is None:
            self.friends_chooser = FriendsDialog(self.facebook.uid,
                                                 self.friends)
        self.friends_chooser.dialog.set_position(gtk.WIN_POS_MOUSE)
        if self.friends_chooser.run() != gtk.RESPONSE_OK:
            return True
        uid, name = self.friends_chooser.uid, self.friends_chooser.name
        
        info = self.photo_info.get(self.preview_image.filename, {})
        tags = info.get("tags", [])
        tags.append((uid, name, x, y))
        info["tags"] = tags
        self.set_tags(tags)
        self.photo_info[self.preview_image.filename] = info
    
    @signal
    def on_upload_button_clicked(self, *args):
        are_you_sure = MessageBox(buttons=gtk.BUTTONS_YES_NO)
        are_you_sure.set_markup("Are you sure you wish to upload?")
        response = are_you_sure.run()
        are_you_sure.hide()
        if response != gtk.RESPONSE_YES:
            return
        
        if self.upload_dialog is None:
            self.upload_dialog = UploadDialog(self)
        self.upload_dialog.run()