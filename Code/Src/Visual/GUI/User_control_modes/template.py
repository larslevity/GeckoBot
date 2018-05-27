# -*- coding: utf-8 -*-
"""
Created on Mon May 30 03:14:12 2016

@author: ls

Templates for the UserControl Pages
"""

from gi.repository import Gtk


def create_xy_adjustments(data):
    """ Create a x-, and a y-adjustment """
    value = (float(data.limits[0] + data.limits[1]))/2
    x_adjustment = Gtk.Adjustment(value=value,
                                  lower=data.limits[0],
                                  upper=data.limits[1],
                                  step_incr=0.01, page_size=0.01)
    value = (data.limits[2])+1
    y_adjustment = Gtk.Adjustment(value=value,
                                  lower=data.limits[2],
                                  upper=data.limits[3],
                                  step_incr=0.01, page_size=0.01)
    return x_adjustment, y_adjustment


def create_image_button(label, image_path):
    """ Create a labeled button with an image """
    box = Gtk.HBox(False, 2)
    label = Gtk.Label(label)
    image = Gtk.Image()
    image.set_from_file(image_path)
    box.pack_start(image, False, False, 1)
    box.pack_end(label, False, False, 1)
    btn = Gtk.Button()
    btn.add(box)
    return btn


def create_content_box(label, spacer=True):
    """
    Create the frame for a content box
    """
    content_vbox = Gtk.VBox(False, 2)

    text_area = Gtk.Label(label)
    action_area = Gtk.VBox(False, 2)
    justify_area = Gtk.HBox(False, 2)

    content_vbox.pack_start(text_area, False, False, 2)
    if spacer:
        content_vbox.pack_start(action_area, False, False, 2)
        spacer = Gtk.HBox(False, 0)
        content_vbox.pack_start(spacer, expand=True, fill=True, padding=2)
    else:
        content_vbox.pack_start(action_area, True, True, 2)
    content_vbox.pack_start(justify_area, False, False, 2)
    return content_vbox, action_area, justify_area


def create_labeled_spinner(label, adjustment):
    """
    Create a labeled spinner
    """
    box = Gtk.HBox(False, 2)
    spinner = Gtk.SpinButton(adjustment=adjustment,
                             climb_rate=0.01, digits=2)
    gtk_label = Gtk.Label(label)
    box.pack_start(spinner, False, False, 2)
    box.pack_end(gtk_label, False, False, 2)
    return box
