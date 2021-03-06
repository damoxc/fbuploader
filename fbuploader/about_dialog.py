# -*- coding: utf-8 -*-
# fbuploader/about_dialog.py
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

import gtk
import logging
from fbuploader.common import Dialog, signal

log = logging.getLogger(__name__)

class AboutDialog(Dialog):
    
    window_name = 'about_dialog'

    def __init__(self):
        super(AboutDialog, self).__init__()
        log.info('Initializing about dialog.')
        del self.builder
    
    @signal
    def on_about_dialog_delete_event(self, *args):
        self.dialog.hide()
        self.dialog.response(gtk.RESPONSE_CLOSE)
        return True
