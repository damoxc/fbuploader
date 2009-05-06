# -*- coding: utf-8 -*-
# fbuploader/imaging.py
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

import gtk.gdk

# Python Imaging Library imports
from PIL import Image
from PIL.ExifTags import TAGS

# Exif Orientation Tag Meaning
# Value   0th Row      0th Column
#   1     top          left side
#   2     top          right side
#   3     bottom       right side
#   4     bottom       left side
#   5     left side    top
#   6     right side   top
#   7     right side   bottom
#   8     left side    bottom

ORIENTATION = {
    #1: 0,
    3: 180,
    6: 270,
    8: 90
}

def autoprepare(filename):
    """
    Prepares an image for upload, resizing it to the maximum image size and
    rotating it according to the EXIF info.
    
    :param filename: str, The path of the image
    :returns: the prepared image
    :rtype: Image
    """
    image = scale(filename)
    return autorotate_image(image)

def autoprepare_image(image):
    """
    Prepares an image for upload, resizing it to the maximum image size and
    rotating it according to the EXIF info.
    
    :param image: Image, The image to rotate
    :returns: the prepared image
    :rtype: Image
    """
    scale_image(image)
    return autorotate_image(image)

def autorotate(filename):
    """
    Rotates an image automatically according to the EXIF data.
    
    :param filename: str, The path of the image
    :returns: the rotated image
    :rtype: Image
    """
    image = Image.open(filename)
    return autorotate_image(image)

def autorotate_image(image):
    """
    Rotates an image automatically according to the EXIF data.
    
    :param image: Image, The image to rotate
    :returns: the rotated image
    :rtype: Image
    """
    exif = get_exif_from_image(image)
    orientation = exif.get('Orientation', 1)
    
    if orientation not in ORIENTATION:
        # We don't need to do anything for this as it's a normal image
        return
    return image.rotate(ORIENTATION[orientation])

def get_exif(filename):
    """
    Retrieves the EXIF info for an image.
    
    :param filename: str, The path of the image
    :returns: Dictionary containing the EXIF info.
    :rtype dict:
    """
    image = Image.open(filename)
    return get_exif_from_image(image)

def get_exif_from_image(image):
    """
    Retrieves the EXIF info from a PIL image.
    
    :param image: Image, the PIL image.
    :returns: a dictionary containing the EXIF info.
    :rtype dict:
    """
    ret = {}
    for tag, value in image._getexif().iteritems():
        decoded = TAGS.get(tag, tag)
        ret[decoded] = value
    return ret

def scale(filename, size=(604, 1024), filter=Image.ANTIALIAS):
    """
    Scales the image to the specified size.
    
    :param filename: str, the filename of the image
    :param size: tuple, the width and height to scale to
    :param filter: int, one of the PIL scale constants to use as the filter
    """
    image = Image.open(filename)
    image.thumbnail(size, filter)
    return image

def scale_image(image, size=(604, 1024), filter=Image.ANTIALIAS):
    """
    Scales the image to the specified size.
    
    :param filename: str, the filename of the image
    :param size: tuple, the width and height to scale to
    :param filter: int, one of the PIL scale constants to use as the filter
    """
    image.thumbnail(size, filter)
    return image

def scale_pixbuf(pixbuf, width, height):
    """
    Method to assist creating thumbnails from an already open pixbuf, that
    keeps the correct aspect ratio.
    
    :param pixbuf: gtk.gdk.Pixbuf, The pixbuf you wish to scale
    :param width: int, The maximum width to scale to
    :param height: int, The maximum height to scale to
    """
    _width = pixbuf.get_width()
    _height = pixbuf.get_height()
    
    if _width <= width or _height <= height:
        # We don't need to do a resize
        return pixbuf
    
    # First stage to resize the picture by the largest dimension
    if _width > _height:
        ratio = _width / float(width)
        _width, _height = width, int(_height / ratio)
    else:
        ratio = _height / float(height)
        _width, _height = int(_width / ratio), height
    
    # Second stage to ensure that the smaller dimension isn't exceeding the
    # maximum.
    if _width > width:
        ratio = _width / float(width)
        _width, _height = width, int(_height / ratio)
    elif _height > height:
        ratio = _height / float(height)
        _width, _height = int(_width / ratio), height
    return pixbuf.scale_simple(_width, _height, gtk.gdk.INTERP_BILINEAR)