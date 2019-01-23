# -*- coding: utf-8 -*-
"""
Main Window
"""

import gi
from gi.repository import Gtk
# pylint: disable=no-name-in-module
from gi.repository import GLib

from Src.Visual.GUI import AnalysisWindow
from Src.Visual.GUI import MenuToolbar


gi.require_version('Gtk', '3.0')


# pylint: disable=too-many-public-methods, unused-argument
# pylint: disable=too-many-instance-attributes
class GeckoBotGUI(Gtk.Window):
    """ The Main Window of PaintBot GUI """

    def run(self):
        """ Add timeout which update the PlotWindow every ._interval seconds
        and starts the Gtk.main() loop """
        self.is_running = True
        GLib.timeout_add(self._interval,
                         self.analyse_win.plot_win.update,
                         self.analyse_win.select_win.keylist)
        Gtk.main()

    def _on_key_down_main_win(self, widget, event):
        """
        define what happens if a key is pressed
        """
        pass
#        key = event.keyval
#        if key == ord("q"):
#            self.do_delete_event(widget=None)

    # pylint: disable=arguments-differ
    def do_delete_event(self, widget, force=False):
        """ Override the default handler for the delete-event signal
        Ask if user is sure of deleting the main_window"""
        # Show our message dialog
        if force:
            response = Gtk.ResponseType.OK
        else:
            dialog = Gtk.MessageDialog(transient_for=self,
                                       modal=True,
                                       buttons=Gtk.ButtonsType.OK_CANCEL)
            dialog.props.text = 'Are you sure you want to quit?'
            response = dialog.run()
            dialog.destroy()

        # We only terminate when the user presses the OK button
        if response == Gtk.ResponseType.OK:
            print 'Terminating...'
            for window in self.list_of_open_windows:
                window.destroy()
            self.destroy()
            Gtk.main_quit()
            self.is_running = False
            return False

        # Otherwise we keep the application open
        return True

    def __init__(self, data, sampleinterval=.2):
        """
        *Initialize with:*
        Args:
            data (object): the data which is visualized and manipulated
            sampleinterval (Optional float): timesteps to update the plot
        """
        # Super Init:
        Gtk.Window.__init__(self, title="GeckoBot GUI")
        self.connect('delete-event', Gtk.main_quit)
        self.connect("key-press-event", self._on_key_down_main_win)
        self.set_default_size(600, 400)

        # init GUIData
        self.data = data
        self.is_running = False

        # interval for GLib argument
        self._interval = int(sampleinterval*1000)
        self.list_of_open_windows = [self]

        # #### Fill Window ####
        main_box = Gtk.VBox(False, 2)
        self.add(main_box)

        # Dropdown Menu
        self.dropdown_menu = Gtk.HBox(False, 4)
        main_box.pack_start(self.dropdown_menu, expand=False,
                            fill=False, padding=2)
        self._init_menu_toolbar_box()

        # Box for all below Menu
        main_hbox = Gtk.HBox(homogeneous=False, spacing=2)
        main_box.pack_start(main_hbox, expand=True, fill=True, padding=2)
        # Status Window
#        self.status_win = StatusWindow.StatusObject(self.data, self)
#        main_hbox.pack_start(self.status_win, False, False, 1)
        # Analysis Window
        self.analyse_win = AnalysisWindow.AnalysisObject(self.data)
        self.analyse_win.size_request()
        main_hbox.pack_start(self.analyse_win, True, True, 1)

        self.show_all()

    def _init_menu_toolbar_box(self):
        """ dropdown menu for advanced features """
        menubox = MenuToolbar.MenuToolbarWindow(toplevel=self)
        self.dropdown_menu.pack_start(menubox, expand=False,
                                      fill=False, padding=2)
