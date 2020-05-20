# -*- coding: utf-8 -*-
"""
Main Window
"""

import gi
from gi.repository import Gtk
# pylint: disable=no-name-in-module
from gi.repository import GLib, Gio

try:
    from Src.GUI import AnalysisWindow
    from Src.GUI import MenuToolbar
except ImportError:
    import AnalysisWindow
    import MenuToolbar

gi.require_version('Gtk', '3.0')



class GeckoBotGUI(Gtk.Application):
    def __init__(self, rec, task, tsampling=.2, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.GeckoBotGUI.app",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
            **kwargs
        )
        self.connect("activate", self.do_activate)
        self.is_running = True
        self.main_win = None
        self.ctr = None
        self.rec = rec
        self.task = task
        
        self.list_of_open_windows = []
        self._interval = int(tsampling*1000)

    def do_activate(self, *args):
        if not self.main_win:
            self.main_win = MainWin(self.rec, toplevel=self,
                                    title='GeckoBotGUI', application=self)
            self.list_of_open_windows.append(self.main_win)
            GLib.timeout_add(self._interval,
                             self.main_win.analyse_win.plot_win.update,
                             self.main_win.analyse_win.select_win.keylist)
        if not self.ctr:  # control window
            self.ctr = CtrWin(self.task, 
                              title="GeckoBot Control Window",
                              application=self)
            self.list_of_open_windows.append(self.ctr)

    
    def do_startup(self):
        Gtk.Application.do_startup(self)        
        # a new simpleaction - for the application
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)


    def refresh_selection(self, mode='pos', setlist=True):
        if self.main_win:
            self.main_win.analyse_win.select_win._init_select_hbox()
            self.main_win.analyse_win.select_win.find_default_keylist(mode, setlist)

    def on_quit(self, action=None, force=None):
        print('main quit..')
#        self.main_win.destroy()
#        Gtk.main_quit()
        if self.main_win:
            self.main_win.do_delete_event(force=True)
        if self.ctr:
            self.ctr.destroy() 
        self.quit()
        self.is_running = False


class CtrWin(Gtk.ApplicationWindow):
    def _on_key_down_main_win(self, widget, event):
        key = event.keyval

        if key == 97:  # 65361  # (a):
            self._btn_clicked('manual', 'LEFT')
        if key == 100:  # 65363: (d)
            self._btn_clicked('manual', 'RIGHT')
        if key == 119:  #65362:  # (w)
            self._btn_clicked('manual', 'UP')
        if key == 115:  # 65364: (s)
            self._btn_clicked('manual', 'DOWN')

    def __init__(self, task, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.connect("key-press-event", self._on_key_down_main_win)
        self.set_default_size(250, 110)

        # init GUIData
        self.task = task
        self.is_running = False

        # #### Fill Window ####
        main_box = Gtk.HBox(False, 2)
        self.add(main_box)
        arrow_box = Gtk.VBox(False, 2)
        main_box.pack_start(arrow_box, False, False, 1)
        btn_hbox1 = Gtk.HBox(False, 2)
        btn_hbox2 = Gtk.HBox(False, 2)
        btn_hbox3 = Gtk.HBox(False, 2)

        image = Gtk.Arrow(0)
        up_btn = Gtk.Button()
        up_btn.add(image)
        up_btn.connect('clicked', self._btn_clicked, 'UP')
        
        image = Gtk.Arrow(2)
        left_btn = Gtk.Button()
        left_btn.add(image)
        left_btn.connect('clicked', self._btn_clicked, 'LEFT')
        
        image = Gtk.Arrow(3)
        right_btn = Gtk.Button()
        right_btn.add(image)
        right_btn.connect('clicked', self._btn_clicked, 'RIGHT')
        
        image = Gtk.Arrow(1)
        down_btn = Gtk.Button()
        down_btn.add(image)
        down_btn.connect('clicked', self._btn_clicked, 'DOWN')
        
        btn_hbox1.pack_start(up_btn, True, False, 1)
        btn_hbox2.pack_start(left_btn, True, False, 1)
        btn_hbox2.pack_start(right_btn, True, False, 1)
        btn_hbox3.pack_start(down_btn, True, False, 1)
        arrow_box.pack_start(btn_hbox1, True, False, 1)
        arrow_box.pack_start(btn_hbox2, True, False, 1)
        arrow_box.pack_start(btn_hbox3, True, False, 1)
        
        # q1:
        q_box = Gtk.VBox(False, 2)
        main_box.pack_start(q_box, True, False, 1)
        adjustment = Gtk.Adjustment(value=0, lower=-90, upper=90,
                                    step_incr=5, page_incr=-5)
        label = Gtk.Label("forward velocity")
        q_box.pack_start(label, expand=False, fill=False, padding=0)
        self.q1spinner = \
            Gtk.SpinButton(adjustment=adjustment, climb_rate=5, digits=0)
        adjustment.connect("value_changed", self._spinner_changed,
                           ('q1', self.q1spinner))
        # pack SpinButton zu hbox
        q_box.pack_start(self.q1spinner, expand=False, fill=False,
                        padding=1)
        
        adjustment = Gtk.Adjustment(value=0, lower=-.5, upper=.5,
                                    step_incr=.05, page_incr=-.05)
        label = Gtk.Label("rotational velocity")
        q_box.pack_start(label, expand=False, fill=False, padding=0)
        self.q2spinner = \
            Gtk.SpinButton(adjustment=adjustment, climb_rate=.05, digits=2)
        adjustment.connect("value_changed", self._spinner_changed,
                           ('q2', self.q2spinner))
        # pack SpinButton zu hbox
        q_box.pack_start(self.q2spinner, expand=False, fill=False,
                        padding=1)


        self.show_all()

    def _spinner_changed(self, widget, arg):
        name, spin = arg
        val = spin.get_value()
        self.task.task['q'][int(name[-1])-1] = val

    def _btn_clicked(self, widget=None, name=None):
        """
        Set the pwm adjustments to zeros and call self.set_pwm()
        """
        incr = 10
        print('cam moved')
        if name == 'LEFT':
            self.task.pan(incr)
        if name == 'RIGHT':
            self.task.pan(-incr)
        if name == 'UP':
            self.task.tilt(-incr)
        if name == 'DOWN':
            self.task.tilt(incr)


class MainWin(Gtk.ApplicationWindow):
    """ The Main Window of GeckoBot GUI """

    def _on_key_down_main_win(self, widget, event):
        """
        define what happens if a key is pressed
        """
        key = event.keyval
        if key == ord("q"):
            self.do_delete_event()

    def __init__(self, data, toplevel, *args, **kwargs):
        """
        *Initialize with:*
        Args:
            data (object): the data which is visualized and manipulated
            sampleinterval (Optional float): timesteps to update the plot
        """
        # Super Init:
        super().__init__(*args, **kwargs)
        self.parent = toplevel
        self.connect("key-press-event", self._on_key_down_main_win)
        self.connect("delete-event", self.do_delete_event)
        self.set_default_size(600, 400)
        
        # init GUIData
        self.data = data

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
        # Analysis Window
        self.analyse_win = AnalysisWindow.AnalysisObject(self.data,
                                                         toplevel=self)
        self.analyse_win.size_request()
        main_hbox.pack_start(self.analyse_win, True, True, 1)

        self.show_all()

    def _init_menu_toolbar_box(self):
        """ dropdown menu for advanced features """
        menubox = MenuToolbar.MenuToolbarWindow(toplevel=self)
        self.dropdown_menu.pack_start(menubox, expand=False,
                                      fill=False, padding=2)

    def do_delete_event(self, widget=None, force=False):
        if not force:
            d = Gtk.MessageDialog(transient_for=self,
                                  modal=True,
                                  buttons=Gtk.ButtonsType.OK_CANCEL)
            d.props.text = 'Are you sure you want to quit?'
            response = d.run()
            d.destroy()
        else:
            response = Gtk.ResponseType.OK

        # We only terminate when the user presses the OK button
        if response == Gtk.ResponseType.OK:
            self.destroy()
            if self.parent.ctr:
                self.parent.ctr.destroy()
            self.parent.is_running = False
            return False

        # Otherwise we keep the application open
        return True


if __name__ == "__main__":
    import datamanagement
    rec = datamanagement.GUIRecorder()
    rec.append({'x': [1,2,3,4,5]})
    app = GeckoBotGUI(rec)
    app.run()
