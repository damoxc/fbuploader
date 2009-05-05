# -*- coding: utf-8 -*-
# fbuploader/widgets.py
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
import cairo
import gobject
import logging
from pkg_resources import resource_filename
from fbuploader.common import EventThread, get_session_dir

log = logging.getLogger(__name__)

def scale_image(pixbuf, max_width=None, max_height=None):
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    
    if width <= max_width or height <= max_height:
        # We don't need to do a resize
        return pixbuf
    
    # First stage to resize the picture by the largest dimension
    if width > height:
        ratio = width / float(max_width)
        width, height = max_width, int(height / ratio)
    else:
        ratio = height / float(max_height)
        width, height = int(width / ratio), max_height
    
    # Second stage to ensure that the smaller dimension isn't exceeding the
    # maximum.
    if width > max_width:
        ratio = width / float(max_width)
        width, height = max_width, int(height / ratio)
    elif height > max_height:
        ratio = height / float(max_height)
        width, height = int(width / ratio), max_height
    return pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)

loading_image = gtk.gdk.pixbuf_new_from_file(resource_filename(
    'fbuploader', 'data/fbuploader64.png'))

class PhotoPreview(gtk.Viewport):
    __gtype_name__ = 'PhotoPreview'
    
    def __init__(self):
        super(PhotoPreview, self).__init__()
        self.set_shadow_type(gtk.SHADOW_NONE)
        
        self.image = gtk.Image()
        self.add(self.image)
        
        self.pixbuf = None
        self.is_resize = False
        self.filename = None
        
        self.connect('size-allocate', self.on_image_size_allocate)
        self.connect('button-press-event', self.on_button_press_event)

    def _scale_image(self, allocation=None):
        allocation = allocation or self.image.get_allocation()
        log.debug('Resizing image')
        log.debug('Allocated size (%dx%d)', allocation.width, allocation.height)
        width, height = self.pixbuf.get_width(), self.pixbuf.get_height()
        log.debug('Image size (%dx%d)', width, height)
        
        # First stage to resize the picture by the largest dimension
        if width > height:
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        else:
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        
        log.debug('Scaled size run 1 (%dx%d)', width, height)
        # Check to ensure that the smaller dimension isn't exceeding the 
        # widgets allocated space.
        if width > allocation.width:
            ratio = width / float(allocation.width)
            width, height = allocation.width, int(height / ratio)
        elif height > allocation.height:
            ratio = height / float(allocation.height)
            width, height = int(width / ratio), allocation.height
        log.debug('Scaled size run 2 (%dx%d)', width, height)
        self.width, self.height = width, height
        return self.pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
    
    def clear_tag(self):
        """
        Clears any displayed tags on the photo
        """
        scaled_pixbuf = self._scale_image()
        self.image.set_from_pixbuf(scaled_pixbuf)

    def display_tag(self, name, x, y):
        """
        Display a tag on the photo.
        
        :param name: str, The name to display alongside the tag.
        :param x: int, The percentage to the tag, x dimension.
        :param y: int, The percentage to the tag, y dimension.
        """
        
        log.debug('Display tag (%r, %r, %r)', name, x, y)
        ctx = self.image.window.cairo_create()
        allocation = self.image.get_allocation()
        
        if allocation.width == self.width:
            ctx.translate(0, (allocation.height - self.height) / 2.0)
        elif allocation.height == self.height:
            ctx.translate((allocation.width - self.width) / 2.0, 0)

        x = (self.width / 100.0) * x
        y = (self.height / 100.0) * y
        
        # Draw the frame
        ctx.set_source_rgba(0.1, 0.1, 0.1, 0.8)
        ctx.set_line_width(max(ctx.device_to_user_distance(4.5, 4.5)))
        ctx.rectangle(x - 40, y - 40, 80, 80)
        ctx.stroke()
        
        # If there's no name we don't need to draw the label.
        if not name:
            return
        
        # Set up the text
        ctx.set_font_size(10)
        ctx.select_font_face("Bitstream Vera Sans", cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_BOLD)
        x1, y1, width, height, x2, y2 = ctx.text_extents(name)
        
        # Draw the background
        ctx.set_source_rgba(0, 0, 0, 0.8)
        ctx.rectangle(x - (width / 2.0) - 5, y - 63, width + 10, height + 10)
        ctx.fill()
        
        # Draw the text
        ctx.move_to(x - (width / 2.0), y - 50)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.show_text(name)
    
    def set_from_file(self, filename):
        """
        Set the photo to display in the preview.
        
        :param filename: str, The filename of the photo to load.
        """
        self.filename = filename
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        scaled_pixbuf = self._scale_image()
        self.image.set_from_pixbuf(scaled_pixbuf)
        self.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))
    
    ## Event Handlers
    def on_image_size_allocate(self, *args):
        allocation = self.get_allocation()
        if self.pixbuf is None: return
        if self.is_resize:
            self.image.set_from_pixbuf(self._scale_image())
            self.is_resize = False
        else:
            self.is_resize = True
    
    def on_button_press_event(self, widget, event):
        if not hasattr(self, 'width'): return
        allocation = self.image.get_allocation()
        x, y = event.x, event.y
        if allocation.width == self.width:
            y -= int((allocation.height - self.height) / 2.0)
        elif allocation.height == self.height:
            x -= int((allocation.width - self.width) / 2.0)
        x = (x / self.width) * 100
        y = (y / self.height) * 100
        self.emit('tag-event', x, y, event)

# Add an event for when the photo is "tagged" (clicked)
gobject.signal_new('tag-event', PhotoPreview, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE, ((gobject.TYPE_PYOBJECT,)*3))

class PhotoAdder(EventThread):
    """
    This class handles adding photos to the PhotoView. We want this to be 
    threaded.
    """
    def __init__(self, photos_view, filename, load_only=False):
        super(PhotoAdder, self).__init__()
        self.model = photos_view.get_model()
        self.queue_resize = photos_view.queue_resize
        
        self.load_only = load_only
        self.filename = filename
    
    def add(self, filename):
        name = os.path.basename(filename)
        return self.model.append((filename, name, loading_image))
    
    def resize(self, filename):
        # Load the photo from the specified file
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        
        # Get the widget and height of the photo, we may need to do some
        # scaling!
        width, height = pixbuf.get_width(), pixbuf.get_height()
        
        if width > 604:
            # We need to resize the photo to the largest that facebook accepts,
            # there is zero point in working with anything larger.
            ratio = width / 604.0
            width = 604
            height = int(height / ratio)
            pixbuf = pixbuf.scale_simple(width, height,
                                         gtk.gdk.INTERP_BILINEAR)

        # Save the possibly scaled pixbuf in the session directory
        filename = get_session_dir(os.path.basename(filename))
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        pixbuf.save(filename, 'jpeg', {'quality': '95'})
        self.fire('photo-added', filename, width, height)
        return pixbuf, filename, (width, height)
    
    def load(self, tree_iter, filename=None, pixbuf=None, size=None):
        # Use the filename passed in if there is one
        if filename:
            self.model.set_value(tree_iter, 0, filename)
        else:
            filename = self.model.get_value(tree_iter, 0)
        
        # Load the photo from the specified file or use the passed in pixbuf
        pixbuf = pixbuf or gtk.gdk.pixbuf_new_from_file(filename)
        
        log.debug('Scaling')
        scaled = scale_image(pixbuf, 100, 100)
        self.model.set_value(tree_iter, 2, scaled)
        log.debug('Resizing')
        self.queue_resize()
        del pixbuf, scaled
    
    def run(self):
        tree_iter = self.add(self.filename)
        filename = None
        pixbuf = None
        size = None
        if not self.load_only:
            filename = self.model.get_value(tree_iter, 0)
            pixbuf, filename, size = self.resize(filename)
        self.load(tree_iter, filename, pixbuf, size)

class QueuedPhotoAdder(PhotoAdder):
    def __init__(self, photos_view, load_only=False):
        super(QueuedPhotoAdder, self).__init__(photos_view, None, load_only)
        self.running = False
        self.__queue = []
    
    def queue(self, *args):
        self.__queue.extend(args)
    
    def run(self):
        tree_iters = map(self.add, self.__queue)
        for tree_iter in tree_iters:
            filename = None
            pixbuf = None
            size = None
            if not self.load_only:
                filename = self.model.get_value(tree_iter, 0)
                pixbuf, filename, size = self.resize(filename)
            self.load(tree_iter, filename, pixbuf, size)

class PhotoView(gtk.IconView):
    __gtype_name__ = 'PhotoView'
    
    def __init__(self, model=None):
        photo_model = gtk.ListStore(str, str, gtk.gdk.Pixbuf)
        super(PhotoView, self).__init__(photo_model)
        self.set_text_column(1)
        self.set_pixbuf_column(2)
        self.set_item_width(120)
        self.photos = {}
        self.connect('key-press-event', self.on_key_press_event)
    
    def add_photo(self, filename):
        log.debug('Adding photo')
        PhotoAdder(self, filename).start()
    
    def add_photo_by_uri(self, uri):
        if uri.startswith('file://'):
            self.add_photo(uri[7:])
    
    def add_photos(self, filenames):
        log.debug('Adding photos')
        queued_adder = QueuedPhotoAdder(self)
        queued_adder.on('photo-added', self.on_photo_added)
        queued_adder.queue(*filenames)
        queued_adder.start()
    
    def add_photos_by_uri(self, uris):
        log.debug('Adding photos by uri')
        filenames = [uri[7:] for uri in uris if uri.startswith('file://')]
        self.add_photos(filenames)

    def load_photo(self, filename):
        log.debug('Loading photo')
        PhotoAdder(self, filename, True).start()
    
    def load_photos(self, filenames):
        log.debug('Loading photos')
        queued_adder = QueuedPhotoAdder(self, True)
        queued_adder.queue(*filenames)
        queued_adder.start()
    
    def reload_photo(self, filename):
        log.debug('Reloading photo')
        model = self.get_model()
        for photo in model:
            if photo[0] != filename:
                continue
            pixbuf = gtk.gdk.pixbuf_new_from_file(filename)        
            photo[2] = scale_image(pixbuf, 100, 100)
            self.queue_resize()
    
    def on_photo_added(self, filename, width, height):
        self.emit('photo-added', filename, width, height)
    
    def on_key_press_event(self, iconview, event, *args):
        if event.keyval != 65535:
            return
        selection = self.get_selected_items()
        if not selection:
            return
        
        tree_iter = self.get_model().get_iter(selection[0])
        filename = self.get_model().get(tree_iter, 0)[0]
        self.get_model().remove(tree_iter)
        self.select_path(selection[0])
        self.emit('photo-deleted', filename)

gobject.signal_new('photo-added', PhotoView,
    gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
    (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT,))
gobject.signal_new('photo-deleted', PhotoView,
    gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
    (gobject.TYPE_PYOBJECT,))
        
class TagLabel(gtk.EventBox):
    
    __gtype_name__ = 'TagLabel'
    
    def __init__(self, text, uid, x, y):
        super(TagLabel, self).__init__()
        self.__uid = uid
        self.__x = x
        self.__y = y
        self.__text = text
        
        self.__label = gtk.Label()
        self.add(self.__label)
        
        self.set_tag(text)
        self.connect('enter-notify-event', self.on_enter_notify_event)
        self.connect('leave-notify-event', self.on_leave_notify_event)
    
    def set_tag(self, text, underline=False):
        if underline:
            markup = '<span foreground="blue"><u>%s</u></span>' % text
        else:
            markup = '<span foreground="blue">%s</span>' % text
        log.debug('Setting markup to: %r', markup)
        self.__label.set_markup(markup)
    
    @property
    def label(self):
        return self.__label
    
    @property
    def text(self):
        return self.__text
    
    @property
    def uid(self):
        return self.__uid
    
    @property
    def x(self):
        return self.__x
    
    @property
    def y(self):
        return self.__y
    
    def on_enter_notify_event(self, widget, event):
        self.set_tag(self.__text, True)
        self.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
        self.emit('enter')
    
    def on_leave_notify_event(self, widget, event):
        self.set_tag(self.__text)
        self.emit('leave')

gobject.signal_new('enter', TagLabel,
    gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
    [])
gobject.signal_new('leave', TagLabel,
    gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
    [])