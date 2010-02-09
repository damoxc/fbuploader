# -*- coding: utf-8 -*-
# fbuploader/main_window.py
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
import re
import gtk
import time
import urllib
import gobject
import gtk.gdk
import logging
import facebook

from fbuploader import imaging
from fbuploader.common import *
from fbuploader.about_dialog import AboutDialog
from fbuploader.friends_dialog import FriendsDialog
from fbuploader.new_album_dialog import NewAlbumDialog
from fbuploader.photochooser_dialog import PhotoChooser
from fbuploader.upload_dialog import UploadDialog
from fbuploader.widgets import PhotoView, PhotoPreview, TagLabel

log = logging.getLogger(__name__)

FB_API_KEY = 'a7b58c2702d421a270df42cfff9f4007'
FB_SECRET_KEY = 'a01ccd6ae703d353a701ea49f63b7667'

cover_re = re.compile('(\d+)\{([\w_]+)\}.jpg')

class MainWindow(Window):

    window_name = 'main_window'
    
    def __init__(self):
        log.info('Initializing Main Window')
        super(MainWindow, self).__init__()
        self.facebook = facebook.Facebook(FB_API_KEY, FB_SECRET_KEY)
        self.albums = []
        self.friends = {}
        
        # Get widgets from the builder
        self.albums_combobox = self.builder.get_object('albums_combobox')
        self.album_cover = self.builder.get_object('albumcover_image')
        self.album_name = self.builder.get_object('albumname_entry')
        self.album_description = self.builder.get_object('albumdescription_entry')
        self.album_location = self.builder.get_object('albumlocation_entry')
        
        self.preview_image = self.builder.get_object('preview_image')
        self.caption_entry = self.builder.get_object('caption_entry')
        self.tags_hbox = self.builder.get_object('tags_hbox')
        
        # Remove the first item in the combobox, for some reason GtkBuilder
        # adds a blank item which we don't want there.
        self.albums_combobox.remove_text(0)
        
        # Add in the photos view widget
        self.photos_view = PhotoView()
        self.photos_view.connect('photo-added', self.on_photos_view_add_photo)
        self.photos_view.connect('photo-deleted', self.on_photos_view_delete_photo)
        self.builder.get_object('photos_scrolled').add(self.photos_view)
        self.photos_view.connect('selection-changed', self.on_photos_view_selection_changed)
        
        self.photos_view.drag_dest_set(gtk.DEST_DEFAULT_ALL,
            [('text/uri-list', 0, 0)], gtk.gdk.ACTION_COPY)
        self.photos_view.connect('drag-data-received',
            self.on_photos_view_drag_data_received)
        
        # Add in the preview photo image widget
        self.preview_image = PhotoPreview()
        self.builder.get_object('preview_vbox').pack_start(self.preview_image)
        self.preview_image.connect('tag-event', self.on_photo_tag)
        
        # Disable the UI, we don't want it active until we have data.
        self.set_sensitive(False)
        
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
        
        # Initialize the new_album_dialog variable that will contain the
        # new album dialog later.
        self.new_album_dialog = None
        
        # Create a holder for the AboutDialog but don't create it just yet.
        self.about_dialog = None
    
    def check_sessions(self):
        sessions = []
        if not os.path.exists(get_config_dir('sessions')):
            return
        for item in os.listdir(get_config_dir('sessions')):
            if os.path.isdir(os.path.join(get_config_dir('sessions'), item)):
                sessions.append(item)
        return sessions
    
    def clear_photo_albums(self):
        """
        Removes all the photo albums from the combobox and the albums array.
        """
        albums = self.albums[:]
        for album in albums:
            self.albums.remove(album)
            self.albums_combobox.remove_text(0)
    
    def clear_tags(self):
        """
        Removes the tag widgets from the tag HBox widget.
        """
        for child in self.tags_hbox.get_children():
            self.tags_hbox.remove(child)
    
    def get_friends(self):
        gobject.idle_add(self._get_friends)
    
    def _get_friends(self):
        log.info('Downloading friends')
        uids = self.facebook.friends.get()
        uids.append(self.facebook.uid)
        
        self.friends.clear()
        log.info('Downloading friend information')
        for friend in self.facebook.users.getInfo(uids):
            self.friends[friend['name']] = friend['uid']
            self.friends[friend['uid']] = friend['name']
    
    def get_photo_albums(self):
        gobject.idle_add(self._get_photo_albums)
    
    def _get_photo_albums(self):
        albums = self.facebook.photos.getAlbums()
        self.clear_photo_albums()
        for album in albums:
            self.albums.append(album)
            self.albums_combobox.append_text('%s (%d Photos)' % (album['name'],
                                                                 album['size']))
        self.albums_combobox.set_active(0)
        self.set_sensitive(True)
        
    def get_signals(self):
        signals = super(MainWindow, self).get_signals()
        signals['on_main_window_event_after'] = self.quit
        signals['on_quit_menuitem_activate'] = self.quit
        signals['on_main_window_destroy'] = self.quit
        return signals
    
    def load(self, session):
        if not session:
            return False
        
        log.info('Loading session %s', session)
        try:
            set_current_session(session)
            path = get_session_dir('data')
            if not os.path.exists(path):
                log.error("Session data doesn't exist")
                return False
            session = json.load(open(path, 'rb'))
        except:
            log.error('Unable to load session %s', session)
            return False

        self.photos = session.get('photos')
        self.photo_info = session.get('photo_info')
        self.fb_session = session.get('fb_session')
        
        if self.fb_session['expires'] <= time.time():
            self.login()
        else:
            self.facebook.session_key = self.fb_session['session_key']
            self.facebook.uid = self.fb_session['uid']
            try:
                self.facebook.friends.areFriends(self.facebook.uid, 12345)
            except Exception, e:
                self.login()
        self.photos_view.load_photos(self.photos)
    
    def login(self):
        logged_in = MessageBox(buttons=gtk.BUTTONS_OK)
        logged_in.set_markup('Press OK once you have logged in.')
        self.fb_token = self.facebook.auth.createToken()
        self.facebook.login()
        log.info('Logging in to Facebook')
        if logged_in.run() == gtk.RESPONSE_OK:
            logged_in.destroy()
            try:
                self.fb_session = self.facebook.auth.getSession()
            except Exception, e:
                log.error('Login failed')
            else:
                log.info('Successfully logged in')
        else:
            log.error('Login failed')
    
    def save(self):
        session = {
            'photos': self.photos,
            'photo_info': self.photo_info,
            'fb_session': self.fb_session
        }
        try:
            path = get_session_dir('data')
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            json.dump(session, open(path, 'wb'))
        except:
            log.error('Unable to save session info')
        
    def set_album_cover(self, album):
        gobject.idle_add(self._set_album_cover, album)
    
    def _set_album_cover(self, album):
        data_dir = get_config_dir('covers')
        for cover in os.listdir(data_dir):
            match = cover_re.match(cover)
            if not match:
                continue
            
            if album['aid'] != match.group(1) or album['cover_pid'] != match.group(2):
                # Either the photo has been changed or it's for the wrong album
                continue
            
            path = get_config_dir(os.path.join('covers', cover))
            self.album_cover.set_from_file(path)
            return

        self.update_cover(album)
    
    def set_sensitive(self, sensitive=True):
        action = sensitive and 'Enabling' or 'Disabling'
        log.info('%s user interface', action)
        
        # Photos stuff
        self.photos_view.set_sensitive(sensitive)
        self.preview_image.set_sensitive(sensitive)
        
        # Album Form
        self.albums_combobox.set_sensitive(sensitive)
        self.album_cover.set_sensitive(sensitive)
        self.album_name.set_sensitive(sensitive)
        self.album_description.set_sensitive(sensitive)
        self.album_location.set_sensitive(sensitive)
    
    def set_tags(self, tags):
        self.clear_tags()

        for tag in tags:
            tag, x, y = tag
            if type(tag) is int:
                label = self.friends[tag]
                uid = tag
            else:
                label = tag
                uid = -1

            button = TagLabel(label, uid, x, y)
            button.connect('enter', self.on_tag_enter)
            button.connect('leave', self.on_tag_leave)
            self.tags_hbox.pack_start(button, False, False)
        self.tags_hbox.show_all()
    
    def start_autosave(self):
        gobject.timeout_add(30000, self._autosave)
    
    def _autosave(self):
        log.info('Autosaving session data')
        self.save()
        gobject.timeout_add(30000, self._autosave)
    
    def quit(self, *args):
        log.info('Shutting down main window')
        if self.photo_chooser is not None:
            self.photo_chooser.dialog.hide()
        if self.friends_chooser is not None:
            self.friends_chooser.dialog.hide()
        try:
            gtk.main_quit()
        except RuntimeError: pass
    
    def update_cover(self, album):
        gobject.idle_add(self._update_cover, album)
    
    def _update_cover(self, album):
        cover_photo = self.facebook.photos.get(pids=album['cover_pid'])
        
        if not cover_photo:
            log.info('Album has no cover photo')
            return
        
        cover_photo = cover_photo[0]
        
        data_dir = get_config_dir('covers')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        filename = '%s{%s}.jpg' % (album['aid'], album['cover_pid'])
        log.info('Downloading album cover photo')
        
        path = os.path.join(data_dir, filename)
        urllib.urlretrieve(cover_photo['src'], path)
        self.album_cover.set_from_file(path)
        
    ## Properties ##
    @property
    def album(self):
        try:
            return self.albums[self.albums_combobox.get_active()]
        except:
            return None

    ## Event Handlers ##
    def on_tag_enter(self, widget):
        self.preview_image.display_tag(widget.text, widget.x, widget.y)
    
    def on_tag_leave(self, widget):
        self.preview_image.clear_tag()

    @signal
    def on_main_window_show(self, e):
        old_sessions = self.check_sessions()
        if not self.load(old_sessions and old_sessions[0] or None):
            create_new_session()
            self.login()

        self.get_photo_albums()
        self.get_friends()
        self.start_autosave()
    
    ## Menu Handlers
    @signal
    def on_newalbum_menuitem_activate(self, *args):
        if self.new_album_dialog is None:
            self.new_album_dialog = NewAlbumDialog(self)
        response = self.new_album_dialog.run()
    
    @signal
    def on_refreshalbums_menuitem_activate(self, *args):
        self.refresh_photo_albums()
    
    @signal
    def on_about_menuitem_activate(self, e):
        def on_delete_event(dialog, *args):
            dialog.hide()
            return True
        self.about_dialog = self.about_dialog or AboutDialog()
        self.about_dialog.run()
        self.about_dialog.hide()
    
    @signal
    def on_albums_combobox_changed(self, e):
        index = self.albums_combobox.get_active()
        if not self.albums:
            return
        self.album_cover.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
        album = self.albums[index]
        self.album_name.set_text(album['name'])
        self.album_description.set_text(album['description'])
        self.album_location.set_text(album['location'])
        self.set_album_cover(album)

    ## DND Stuff ##
    @signal
    def on_photos_iconview_drag_drop(self, iconview, context, x, y, time):
        context.finish(True, False, time)
        return True
    
    @signal
    def on_photos_view_drag_data_received(self, iconview, context, x, y,
                                              selection, info, time):
        uris = [uri for uri in selection.data.split('\r\n')[:-1]]
        self.photos_view.add_photos_by_uri(uris)
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

        self.photos_view.add_photos(self.photo_chooser.dialog.get_filenames())
    
    @signal
    def on_photos_view_selection_changed(self, *args):
        selected = self.photos_view.get_selected_items()
        if not selected:
            self.preview_image.clear()
            self.caption_entry.set_text('')
            self.clear_tags()
            return

        # If there was a previous image, save the value in the caption field
        if self.preview_image.filename is not None:
            info = self.photo_info.get(self.preview_image.filename, {})
            info['caption'] = self.caption_entry.get_text()
            self.photo_info[self.preview_image.filename] = info
        
        selected = selected[0]
        model = self.photos_view.get_model()
        filename = model[selected][0]
        
        info = self.photo_info.get(filename, {})      
        self.preview_image.set_from_file(filename)
        self.caption_entry.set_text(info.get('caption', ''))
        self.set_tags(info.get('tags', []))
        return True
    
    @signal
    def on_photos_view_add_photo(self, photoview, filename, width, height):
        log.info('Adding photo %s', os.path.basename(filename))
        log.debug('Full: %s', filename)
        self.photos.append(filename)
        self.photo_info[filename] = {
            'width': width,
            'height': height
        }
    
    @signal
    def on_photos_view_delete_photo(self, photoview, photo):
        self.photos.remove(photo)
        del self.photo_info[photo]
    
    @signal
    def on_rotate_left_button_clicked(self, *args):
        imaging.rotate(self.preview_image.filename, 90)
        self.preview_image.set_from_file(self.preview_image.filename)
        self.photos_view.reload_photo(self.preview_image.filename)
        self.photos_view.queue_resize()
    
    @signal
    def on_rotate_right_button_clicked(self, *args):
        imaging.rotate(self.preview_image.filename, 270)
        self.preview_image.set_from_file(self.preview_image.filename)
        self.photos_view.reload_photo(self.preview_image.filename)
        self.photos_view.queue_resize()
    
    @signal
    def on_photo_tag(self, widget, x, y, event):
        x, y = int(round(x)), int(round(y))
        self.preview_image.display_tag('', x, y)
        if self.friends_chooser is None:
            self.friends_chooser = FriendsDialog(self.facebook.uid,
                                                 self.friends)
        self.friends_chooser.dialog.set_position(gtk.WIN_POS_MOUSE)
        
        if self.friends_chooser.run() != gtk.RESPONSE_OK:
            self.preview_image.clear_tag()
            return True
        
        if self.friends_chooser.uid == -1:
            value = self.friends_chooser.name
        else:
            value = self.friends_chooser.uid
        
        info = self.photo_info.get(self.preview_image.filename, {})
        tags = info.get('tags', [])
        tags.append((value, x, y))
        info['tags'] = tags
        self.set_tags(tags)
        self.photo_info[self.preview_image.filename] = info
        self.preview_image.clear_tag()
    
    @signal
    def on_upload_button_clicked(self, *args):
        are_you_sure = MessageBox(buttons=gtk.BUTTONS_YES_NO)
        are_you_sure.set_markup('Are you sure you wish to upload?')
        response = are_you_sure.run()
        are_you_sure.hide()
        if response != gtk.RESPONSE_YES:
            return
        
        if self.upload_dialog is None:
            self.upload_dialog = UploadDialog(self)
        self.upload_dialog.run()
