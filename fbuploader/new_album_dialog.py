# -*- coding: utf-8 -*-
# fbuploader/new_album_dialog.py
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

import logging

from fbuploader.common import Dialog

log = logging.getLogger(__name__)

class NewAlbumDialog(Dialog):
    def __init__(self, main_window):
        super(NewAlbumDialog, self).__init__("new_album_dialog")
        self.main_window = main_window
    
    def on_delete(self, *args):
        return super(NewAlbumDialog, self).on_delete(*args)