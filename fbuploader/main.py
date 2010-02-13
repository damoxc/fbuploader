# -*- coding: utf-8 -*-
# fbuploader/main.py
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

import logging
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%H:%M:%S',
    qualname='fbuploader'
)

def main():
    from twisted.internet import gtk2reactor
    reactor = gtk2reactor.install()

    from fbuploader.main_window import MainWindow
    log.info('Starting Main Window')
    main_window = MainWindow()
    main_window.show()

    reactor.run()
