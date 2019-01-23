# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 22:59:10 2016

@author: ls

related to :
http://python-gtk-3-tutorial.readthedocs.io/en/latest/menus.html
"""
from time import strftime
import gi
from gi.repository import Gtk
from Src.Visual.GUI import save
from Src.Visual.GUI import SettingsWindow

gi.require_version('Gtk', '3.0')


#UI_INFO = """
#<ui>
#  <menubar name='MenuBar'>
#    <menu action='FileMenu'>
#      <menu action='FileLoad'>
#        <menuitem action='FileLoadBuffer' />
#        <menuitem action='FileLoadPwmBuffer' />
#        <menuitem action='FileLoadRecorded' />
#      </menu>
#      <menu action='FileSave'>
#        <menuitem action='FileSaveRecordedAsTikz' />
#        <menuitem action='FileSaveBuffer' />
#        <menuitem action='FileSavePwmBuffer' />
#      </menu>
#      <separator />
#      <menuitem action='FileQuit' />
#    </menu>
#    <menu action='EditMenu'>
#      <menuitem action='EditEstimate' />
#      <menuitem action='EditPaste' />
#      <menuitem action='EditSomething' />
#    </menu>
#    <menu action='SettingsMenu'>
#      <menuitem action='SettingsSettings'/>
#    </menu>
#  </menubar>
#  <toolbar name='ToolBar'>
#    <toolitem action='FileLoadBuffer' />
#    <toolitem action='FileLoadPwmBuffer' />
#    <toolitem action='FileSaveRecordedAsTikz' />
#    <toolitem action='EditEstimate' />
#    <toolitem action='FileQuit' />
#  </toolbar>
#</ui>
#"""

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menu action='FileSave'>
        <menuitem action='FileSaveRecordedAsTikz' />
      </menu>
      <separator />
      <menuitem action='FileQuit' />
    </menu>
    <menu action='EditMenu'>
      <menuitem action='EditPaste' />
      <menuitem action='EditSomething' />
    </menu>
    <menu action='SettingsMenu'>
      <menuitem action='SettingsSettings'/>
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem action='FileSaveRecordedAsTikz' />
    <toolitem action='SettingsSettings' />
    <toolitem action='FileQuit' />
  </toolbar>
</ui>
"""


class MenuToolbarWindow(Gtk.Bin):
    """ A Bin Object which creates a Menu and a Toolbar """

    def __init__(self, toplevel):
        super(MenuToolbarWindow, self).__init__()
        self.data = toplevel.data
        self.toplevel = toplevel
        self.list_of_open_windows = self.toplevel.list_of_open_windows

        action_group = Gtk.ActionGroup("my_actions")

        self.add_file_menu_actions(action_group)
        self.add_edit_menu_actions(action_group)
        self.add_settings_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(menubar, False, False, 0)

        toolbar = uimanager.get_widget("/ToolBar")
        box.pack_start(toolbar, False, False, 0)

        self.popup = uimanager.get_widget("/PopupMenu")

        self.add(box)

    def add_file_menu_actions(self, action_group):
        """ menu action are generated """
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)

        # Load
        action_fileloadmenu = Gtk.Action("FileLoad", "Load", None, None)
        action_group.add_action(action_fileloadmenu)

#        action_new = Gtk.Action("FileLoadRecorded", "Recorder",
#                                "Load a reference from .h5", Gtk.STOCK_OPEN)
#        action_new.connect("activate", self.on_load_clicked)
#        action_group.add_action_with_accel(action_new, '<control><shift>R')
#
#        action_new = Gtk.Action("FileLoadBuffer", "Buffer",
#                                "Load a reference from .h5", Gtk.STOCK_OPEN)
#        action_new.connect("activate", self.on_load_clicked)
#        action_group.add_action_with_accel(action_new, '<control><shift>B')
#
#        action_new = Gtk.Action("FileLoadPwmBuffer", "Pwm Buffer",
#                                "Load a Pwm-Signal from .h5", Gtk.STOCK_OPEN)
#        action_new.connect("activate", self.on_load_clicked)
#        action_group.add_action_with_accel(action_new, '<control><shift>P')

        # Save
        action_filesavemenu = Gtk.Action("FileSave", "Save", None, None)
        action_group.add_action(action_filesavemenu)

        action_new = Gtk.Action("FileSaveRecordedAsTikz", "Recorder as Tikz",
                                "Save current Plot as TikZ-Picture",
                                Gtk.STOCK_SAVE)
        action_new.connect("activate", self.on_save_clicked)
        action_group.add_action_with_accel(action_new, '<control>S')

#        action_new = Gtk.Action("FileSaveBuffer", "Buffer",
#                                "Save the current Buffer to .h5",
#                                Gtk.STOCK_OPEN)
#        action_new.connect("activate", self.on_save_clicked)
#        action_group.add_action_with_accel(action_new, None)
#
#        action_new = Gtk.Action("FileSavePwmBuffer", "Pwm Buffer",
#                                "Save the current Pwm Buffer to .h5",
#                                Gtk.STOCK_OPEN)
#        action_new.connect("activate", self.on_save_clicked)
#        action_group.add_action_with_accel(action_new, None)

        # Quit
        action_filequit = Gtk.Action("FileQuit", None,
                                     'Exit the entire program', Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.toplevel.do_delete_event)
        action_group.add_action_with_accel(action_filequit,
                                           '<control><shift>Q')

    def add_edit_menu_actions(self, action_group):
        """ add items in the edit menu, key configuration and handlers. """
        action_group.add_actions([
            ("EditMenu", None, "Edit"),
#            ("EditEstimate", None, 'Estimate',
#             None, 'Parameter Estimation of the System',
#             self.on_menu_edit),
            ("EditPaste", Gtk.STOCK_PASTE, None, None, None,
             self.on_menu_edit),
            ("EditSomething", None, "Something", "<control><alt>S", None,
             self.on_menu_edit)
        ])

    def add_settings_menu_actions(self, action_group):
        """ add items in the settings menu, key configuration and handlers. """

        action_settingsmenu = Gtk.Action("SettingsMenu", "Settings", None, None)
        action_group.add_action(action_settingsmenu)

        action_new = Gtk.Action("SettingsSettings", "Settings",
                                "Tune System-Parameter",
                                Gtk.STOCK_PROPERTIES)
        action_new.connect("activate", self.on_menu_settings)
        action_group.add_action(action_new)

#        action_group.add_actions([
#            ("SettingsMenu", None, "Settings"),
#            ("SettingsSettings", None, 'System Settings', None, 'Tune System-Parameter', self.on_menu_settings)
#        ])
        
#        action_group.add_action(Gtk.Action("SettingsMenu", "Settings", None,
#                                           None))
#
#        action_group.add_radio_actions([
#            ("ChoiceOne", None, "One", None, None, 1),
#            ("ChoiceTwo", None, "Two", None, None, 2)
#        ], 1, self.on_menu_choices_changed)
#
#        three = Gtk.ToggleAction("ChoiceThree", "Three", None, None)
#        three.connect("toggled", self.on_menu_choices_toggled)
#        action_group.add_action(three)

    def create_ui_manager(self):
        """ This is something magic..."""
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.toplevel.add_accel_group(accelgroup)
        return uimanager

    def on_menu_edit(self, widget):
        """ starts the stimation state """
        print "Menu item " + widget.get_name() + " was selected"
        if widget.get_name() == 'EditEstimate':
            if self.data.flag['PAUSE'] is True:
                self.data.flag['ESTIMATE'] = True
            else:
                print 'Only possile in PAUSE state...'

    def on_menu_settings(self, widget):
        print "Menu item " + widget.get_name() + " was selected"
        if widget.get_name() == "SettingsSettings":
            inlist = False
            for window in self.list_of_open_windows:
                if isinstance(window, SettingsWindow.SettingsWindow):
                    inlist = True
            if not inlist:
                self.list_of_open_windows.append(
                    SettingsWindow.SettingsWindow(self.list_of_open_windows,
                                                  self.toplevel))

    def on_load_clicked(self, widget):
        """ Load an trajectory from somewhere
        """
        target = widget.get_name()
        filename = self._select_file('open', target)
        if filename:
            data = save.load_data(self.data, filename)
            if target == 'FileLoadBuffer':
                self.data.buffer = data
            elif target == 'FileLoadPwmBuffer':
                self.data.motor_input_buffer = data
            elif target == 'FileLoadRecorded':
                self.data.recorded = data

    def on_save_clicked(self, widget):
        """ Save the current state to .h5 """
        target = widget.get_name()
        filename = self._select_file('save', target)
        if filename:
            if target == "FileSaveRecordedAsTikz":
                save.save_current_plot_as_tikz(self.toplevel, filename)
#            elif target == 'FileSaveBuffer':
#                save.save_buffer_data(self.data, filename)
#            elif target == 'FileSavePwmBuffer':
#                save.save_motor_input_buffer_data(self.data, filename)

    def _select_file(self, action, target):
        """ starts the user dialog to select a file """
        if action == "open":
            gtk_action = Gtk.FileChooserAction.OPEN
        elif action == "save":
            gtk_action = Gtk.FileChooserAction.SAVE
        dialog = Gtk.FileChooserDialog("Please choose a file", self.toplevel,
                                       gtk_action,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        if action == "save":
            dialog.set_current_name(target+strftime("%Y_%m_%d__%H_%M")+'.tex')
        dialog = add_filters(dialog)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        else:
            filename = None
        dialog.destroy()
        return filename


def add_filters(dialog):
    """ data filter for hdf5 format """
    filter_tex = Gtk.FileFilter()
    filter_tex.set_name("*.tex")
    filter_tex.add_pattern("*.tex")
    dialog.add_filter(filter_tex)

    filter_h5 = Gtk.FileFilter()
    filter_h5.set_name("*.h5")
    filter_h5.add_pattern("*.h5")
    dialog.add_filter(filter_h5)

    filter_any = Gtk.FileFilter()
    filter_any.set_name("Any files")
    filter_any.add_pattern("*")
    dialog.add_filter(filter_any)
    return dialog
