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

import gtk.glade

def signal(func):
    func._signal = True
    return func

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

class Window(object):

    def __init__(self, glade_file, window_name, icon=None):
        self.tree = gtk.glade.XML(glade_file)
        self.window = self.tree.get_widget(window_name)
        if icon is not None:
            icon = get_icon(icon)
            self.window.set_icon(icon)
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
    
    def __init__(self, glade_file, window_name, icon=None):
        super(Dialog, self).__init__(glade_file, window_name, icon=icon)
        self.dialog = self.window
    
    def run(self):
        return self.dialog.run()