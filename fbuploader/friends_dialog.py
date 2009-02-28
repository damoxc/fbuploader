# -*- coding: utf-8 -*-
# fbuploader/friends_dialog.py
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

from pkg_resources import resource_filename
from fbuploader.common import Dialog, Events, signal

class FriendsDialog(Dialog, Events):
    
    def __init__(self, user_uid, friends):
        glade_file = resource_filename("fbuploader", "glade/fbuploader.glade")
        Events.__init__(self)
        super(FriendsDialog, self).__init__(glade_file, "friends_dialog")
        
        # Set up the list of friends names and uids
        friends.sort(lambda x, y: cmp(x["name"], y["name"]))
        self.friends = friends
        self.user_uid = user_uid
        self.__recent_friends = {}

        # Get the required widgets as variables
        self.friend_entry = self.tree.get_widget("friend_entry")
        self.all_friends = self.tree.get_widget("allfriends_treeview")
        self.all_friends_expander = self.tree.get_widget("allfriends_expander")
        self.recent_friends = self.tree.get_widget("recentfriends_treeview")

        # Set up the friends treeviews
        for treeview in (self.all_friends, self.recent_friends):
            treeview.set_model(gtk.ListStore(int, str))
            renderer = gtk.CellRendererText()
            column = gtk.TreeViewColumn("Friends", renderer)
            column.add_attribute(renderer, "text", 1)
            treeview.append_column(column)
            treeview.set_headers_visible(False)
        self.filter_friends()
        
    
    def filter_friends(self, filter_text=""):
        # Add all the friends to the all friends treeview.
        model = self.all_friends.get_model()
        model.clear()
        count = 0
        for friend in self.friends:
            if friend["uid"] == self.user_uid:
                self.add_recent_friend(friend["name"], friend["uid"])
            if friend["name"].startswith(filter_text):
                model.append((friend["uid"], friend["name"]))
                count += 1
        return count
    
    def add_recent_friend(self, name, uid=-1):
        if name not in self.__recent_friends:
            self.__recent_friends[name] = uid
            model = self.recent_friends.get_model()
            model.append((uid, name))
    
    def run(self):
        self.uid, self.name = None, None
        self.dialog.set_position(gtk.WIN_POS_MOUSE)
        self.friend_entry.grab_focus()
        response = self.dialog.run()
        
        # Begin tidy up so dialog will be fresh for the next run
        self.friend_entry.set_text("")
        self.filter_friends()
        if self.all_friends_expander.get_expanded():
            self.all_friends_expander.set_expanded(False)
        
        # Finally hide the dialog, we want to do this every run regardless of
        # response.
        self.dialog.hide()
        return response
    
    @signal
    def on_friends_ok_button_clicked(self, *args):
        pass
    
    @signal
    def on_friends_cancel_button_clicked(self, *args):
        self.dialog.response(gtk.RESPONSE_CANCEL)
        return True
    on_friends_dialog_delete_event = on_friends_cancel_button_clicked 
    
    @signal
    def on_friend_entry_changed(self, *args):
        if not self.all_friends_expander.get_expanded():
            self.all_friends_expander.set_expanded(True)
        if self.filter_friends(self.friend_entry.get_text()) == 1:
            self.friend_entry.set_text(self.all_friends.get_model()[0][1])
            selection = self.all_friends.get_selection()
            selection.select_path((0,))
            self.all_friends.grab_focus()
    
    @signal
    def on_allfriends_treeview_row_activated(self, allfriends, path, column):
        model = allfriends.get_model()
        self.uid, self.name = model.get(model.get_iter(path), 0, 1)
        self.add_recent_friend(self.name, self.uid)
        self.dialog.response(gtk.RESPONSE_OK)
    on_recentfriends_treeview_row_activated = on_allfriends_treeview_row_activated
        