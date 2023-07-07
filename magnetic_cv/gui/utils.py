# -*- coding: utf-8 -*-

"""General functions that can be used in more than one widget."""

import os.path as _path

_basepath = _path.dirname(_path.abspath(__file__))


def get_icon_path(icon_name):
    """Get the icon file path."""
    img_path = _path.join(
        _path.join(_path.dirname(_basepath), 'resources'), 'img')
    icon_path = _path.join(img_path, '{0:s}.png'.format(icon_name))
    return icon_path


def get_ui_file(widget):
    """Get the ui file path."""
    if isinstance(widget, type):
        basename = '{0:s}.ui'.format(widget.__name__.lower())
    else:
        basename = '{0:s}.ui'.format(widget.__class__.__name__.lower())
    uifile = _path.join(_basepath, _path.join('ui', basename))
    return uifile
