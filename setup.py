# -*- coding: utf-8 -*-
# setup.py
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

from setuptools import setup, find_packages

setup(name='FBUploader',
      version='0.1',
      license='GPLv3',
      description='Facebook photo uploader',
      long_description='''''',
      author='Damien Churchill',
      author_email='damoxc@gmail.com',
      packages=['fbuploader'],
      package_data={'fbuploader': ['data/*']},
      entry_points = """
      [console_scripts]
      fbuploader = fbuploader.main:main
      """
)
