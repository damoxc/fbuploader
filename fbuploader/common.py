# -*- coding: utf-8 -*-
# fbuploader/common.py
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
import time
import logging
import threading
import gtk, gtk.glade
import xdg, xdg.BaseDirectory
from pkg_resources import resource_filename

log = logging.getLogger(__name__)

def signal(func):
    func._signal = True
    return func

session = None
def create_new_session():
    return str(int(time.time()))

def get_current_session():
    global session
    if session is None:
        session = create_new_session()
    return session

def get_session_dir(filename=None):
    if False:
        pass
    else:
        folder = os.path.join(xdg.BaseDirectory.save_config_path("fbuploader"),
                              get_current_session())
        if filename:
            return os.path.join(folder, filename)
        else:
            return folder

def set_current_session(session_id):
    global session
    session = session_id

def get_config_dir(filename=None):
    if False:
        pass
    else:
        folder = xdg.BaseDirectory.save_config_path("fbuploader")
        if filename:
            return os.path.join(folder, filename)
        else:
            return folder

_prop = property
def property(fget=None, fset=None, fdel=None, doc=None):
    if fget is not None and fget.func_code.co_argcount == 0:
        keys = 'get', 'set', 'del'
        func_locals = {'doc': fget.__doc__}
        def probeFunc(frame, event, args):
            if event == 'return':
                locals = frame.f_locals
                func_locals.update(dict(('f' + k, locals.get(k)) for k in keys))
                sys.settrace(None)
            return probeFunc
        sys.settrace(probeFunc)
        fget()
        return _prop(**func_locals)
    else:
        return _prop(fget, fset, fdel, doc)

class Events(object):
    
    def __init__(self, *args, **kwargs):
        self.__events = {}
    
    def on(self, event, callback):
        callbacks = self.__events.get(event, [])
        callbacks.append(callback)
        self.__events[event] = callbacks
    
    def fire(self, event, *args):
        callbacks = self.__events.get(event, [])
        for callback in callbacks:
            callback(*args)
    
    def unregister(self, event, callback):
        callbacks = self.__events.get(event, [])
        callbacks.remove(callback)
        self.__events[event] = callbacks

class Thread(threading.Thread, Events):
    def __init__(self):
        super(Thread, self).__init__()
        Events.__init__(self)

class Window(object):

    glade_file = resource_filename("fbuploader", "data/fbuploader.glade")
    icon = resource_filename("fbuploader", "data/fbuploader64.png")
    
    def __init__(self, window_name, icon=None):
        self.tree = gtk.glade.XML(self.glade_file)
        self.window = self.tree.get_widget(window_name)
        icon = icon or self.icon
        self.window.set_icon_from_file(icon)
        self.tree.signal_autoconnect(self.get_signals())
    
    def get_signals(self):
        signals = {}
        for attr in dir(self):
            if attr[0] == "_":
                continue
            try:
                if getattr(getattr(self, attr), "_signal", False):
                    signals[attr] = getattr(self, attr)
            except: pass
        return signals
    
    def show(self):
        self.window.show()
        self.window.show_all()

class Dialog(Window):
    
    def __init__(self, dialog_name, icon=None):
        super(Dialog, self).__init__(dialog_name, icon=icon)
        self.dialog = self.window
        self.dialog.connect("delete-event", self.on_delete)
    
    def on_delete(self, *args):
        self.dialog.response(gtk.RESPONSE_CANCEL)
        self.dialog.hide()
        return True
    
    def run(self):
        return self.dialog.run()

class MessageBox(gtk.MessageDialog):
    def __init__(self, parent=None, flags=0, type=gtk.MESSAGE_INFO,
                 buttons=gtk.BUTTONS_NONE, message_format=None):
        super(MessageBox, self).__init__(parent, flags, type, buttons,
                                         message_format)
        self.set_icon_from_file(resource_filename("fbuploader",
                                                  "data/fbuploader64.png"))

__all__ = [
    # methods
    "signal", "create_new_session", "get_current_session", "get_session_dir",
    "set_current_session", "get_config_dir", "property",
    
    # classes
    "Events", "Window", "Dialog", "MessageBox", "Thread"
]