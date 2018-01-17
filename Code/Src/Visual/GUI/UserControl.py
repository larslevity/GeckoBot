# -*- coding: utf-8 -*-
"""
Created on Mon May 23 15:15:23 2016

@author: ls

Gtk.Window for user specified paths
"""

from gi.repository import Gtk
# from Src.Visual.GUI.User_control_modes import move
from Src.Visual.GUI.User_control_modes import pwm


# pylint: disable=too-many-locals, too-many-public-methods, unused-argument
# pylint: disable=too-many-statements
class UserControlWindow(Gtk.Window):
    """
    User Control via GUI
    """
    def __init__(self, task, list_of_open_windows, modus='PWM'):
        """
        *Initialize with:*

        Args:
            data (GlobalData Object): the data
            list_of_open_windows (list): that's what it sounds like
        """
        # initialize atrributes
        self.list_of_open_windows = list_of_open_windows
        self.task = task

        # connecting events
        title = 'User Control Window - {}'.format(modus)
        super(UserControlWindow, self).__init__(title=title)
        self.connect('delete_event', self.on_quit_clicked)
        self.connect('key-press-event', self._on_key_down)

        # build the diffrent windows and Frames
        main_box = Gtk.VBox(homogeneous=False, spacing=2)
        self.add(main_box)
        notebook = Gtk.Notebook()
        notebook.set_tab_pos = (Gtk.PositionType.TOP)
        main_box.pack_start(notebook, True, True, 2)

        # dpm spinner and quit button
        hbox = Gtk.HBox(spacing=2, homogeneous=False)
        main_box.pack_start(hbox, False, False, 2)

        box = Gtk.HBox(False, 2)
        label = Gtk.Label('Quit')
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/Cancel.png")
        box.pack_start(image, False, False, 1)
        box.pack_start(label, False, False, 1)
        btn = Gtk.Button()
        btn.add(box)
        btn.connect('clicked', self.on_quit_clicked)
        hbox.pack_end(btn, False, False, 2)

        # create the pages for notebook
#        move_page = move.MovePage(self.data, self.dpm_adjustment)
        if modus == 'PWM':
            page = pwm.PwmPage(self.task)
        elif modus == 'REF':
            page = pwm.ReferencePage(self.task)
        elif modus == 'WALK':
            page = pwm.WalkingPage(self.task)
        else:
            raise NotImplementedError(modus)

#        notebook.append_page(move_page, Gtk.Label('Move'))
        notebook.append_page(page, Gtk.Label(modus))

        # finally show all
        self.show_all()

    def on_quit_clicked(self, widget=None, event=None):
        """
        Destroy the the UserControlWindow and remove it from the list of
        open windows.
        """
        self.list_of_open_windows.remove(self)
        self.destroy()

    def _on_key_down(self, widget, event):
        """
        define what happens if a key is pressed
        """
        key = event.keyval
        if key == ord('q'):
            self.on_quit_clicked()
