# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 14:45:29 2017

@author: ls
"""


from gi.repository import Gtk


# pylint: disable=too-many-locals, too-many-public-methods, unused-argument
# pylint: disable=too-many-statements
class SettingsWindow(Gtk.Window):
    """
    User Settings via GUI
    """
    def __init__(self, list_of_open_windows, toplevel):
        """
        *Initialize with:*

        Args:
            list_of_open_windows (list): that's what it sounds like
        """
        # initialize atrributes
        self.list_of_open_windows = list_of_open_windows
        self.toplevel = toplevel

        # connecting events
        title = 'Settings'
        super(SettingsWindow, self).__init__(title=title)
        self.connect('delete_event', self.on_quit_clicked)
        self.connect('key-press-event', self._on_key_down)

        main_box = Gtk.VBox(homogeneous=False, spacing=2)
        self.add(main_box)

        notebook = Gtk.Notebook()
        notebook.set_tab_pos = (Gtk.PositionType.TOP)
        main_box.pack_start(notebook, False, False, 2)

        page = PIDSettingPage(self.toplevel)
        notebook.append_page(page, Gtk.Label('PID Settings'))

        ABSpage = AbsoluteValuePage(self.toplevel)
        notebook.append_page(ABSpage, Gtk.Label('Absolute Value Settings'))

        # quit button
        hbox = Gtk.HBox(spacing=2, homogeneous=False)
        main_box.pack_end(hbox, False, False, 2)

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


class AbsoluteValuePage(Gtk.Bin):
    def __init__(self, toplevel):
        super(AbsoluteValuePage, self).__init__()
        self.toplevel = toplevel

        main_box = Gtk.HBox(False, 2)
        self.add(main_box)

        self.entry = [None]*3
        table = Gtk.Table(3, 4, False)
        main_box.pack_start(table, False, False, 2)

        for i, e in enumerate([('Maximal Absolute Pressure', '[bar]', self.set_maxpressure, self.toplevel.task.maxpressure, .05, 10, 2),
                               ('Maximal Control Output', '[10V]', self.set_maxctrout, self.toplevel.task.maxctrout, 0, 1, 2),
                               ('Pseudo Sampling Rate', '[sec]', self.set_tsampling, self.toplevel.task.tsampling, 0, 1, 3)]):
            label_text, unit, handler, default_val, lower, upper, digits = e
            label = Gtk.Label(label_text)
            unit_label = Gtk.Label(unit)
            self.entry[i] = EntryWidget(None, default_val, lower, upper, digits)
            btn = Gtk.Button('Set')
            btn.connect('clicked', handler, i)
            table.attach(label, 0, 1, i, i+1)
            table.attach(self.entry[i], 1, 2, i, i+1)
            table.attach(unit_label, 2, 3, i, i+1)
            table.attach(btn, 3, 4, i, i+1)

        self.show_all()

    def set_maxpressure(self, widget, idx):
        val = self.entry[idx].get_value()
        self.toplevel.task.maxpressure = val
        self.toplevel.task.set_maxpressure = True

    def set_maxctrout(self, widget, idx):
        val = self.entry[idx].get_value()
        self.toplevel.task.maxctrout = val
        self.toplevel.task.set_maxctrout = True

    def set_tsampling(self, widget, idx):
        val = self.entry[idx].get_value()
        self.toplevel.task.tsampling = val
        self.toplevel.task.set_tsampling = True


class PIDSettingPage(Gtk.Bin):

    def __init__(self, toplevel):
        super(PIDSettingPage, self).__init__()
        self.toplevel = toplevel
        # Creates a list containing 6 lists, each of 3 items, all set to None
        w, h = 3, len(self.toplevel.task.PID_Params)
        self.entry = [[None for x in range(w)] for y in range(h)]

        # build the diffrent windows and Frames
        main_box = Gtk.VBox(homogeneous=False, spacing=2)
        self.add(main_box)

        for idx in range(h):
            hbox = Gtk.HBox(False, 1)
            main_box.pack_start(hbox, False, False, 1)
            label = Gtk.Label('Ctr {}:'.format(idx))
            hbox.pack_start(label, False, False, 6)

            for j, gain in enumerate(['P', 'I', 'D']):
                default = self.toplevel.task.PID_Params[idx][j]
                entry = EntryWidget(gain, default)
                hbox.pack_start(entry, False, False, 6)
                self.entry[idx][j] = entry

            btn = Gtk.Button('Set')
            btn.connect('clicked', self.on_set_clicked, idx)
            hbox.pack_start(btn, False, False, 4)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            main_box.pack_start(separator, False, False, 1)

        # finally show all
        self.show_all()

    def on_set_clicked(self, widget, ctr_id):
        P, I, D = [self.entry[ctr_id][j].get_value() for j in range(3)]
        self.toplevel.task.PID_Params[ctr_id] = [P, I, D]
        self.toplevel.task.set_PID[ctr_id] = True
        print 'PID Ctr ', ctr_id, 'is set to', P, I, D


class EntryWidget(Gtk.Bin):
    def __init__(self, label, default, lower=0, upper=100, digits=2):
        super(EntryWidget, self).__init__()

        mainbox = Gtk.HBox(False, 2)
        self.add(mainbox)

        label = Gtk.Label(label)
        mainbox.pack_start(label, False, False, 1)

        self.adjustment = Gtk.Adjustment(value=default, lower=lower,
                                         upper=upper, step_incr=1./10**digits)
        spinner = Gtk.SpinButton(adjustment=self.adjustment, climb_rate=1./10**digits,
                                 digits=digits, numeric=True)
        mainbox.pack_start(spinner, False, False, 1)

        self.show_all()

    def on_editable_toggled(self, button):
        value = button.get_active()
        self.entry.set_editable(value)

    def get_value(self):
        value = self.adjustment.get_value()
        return value
