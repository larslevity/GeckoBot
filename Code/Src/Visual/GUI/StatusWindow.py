"""
Created on Wed May 17 13:48:31 2017

@author: ls

Analysis Tool
"""
# pylint: disable= no-name-in-module
from gi.repository import Gtk
from Src.Visual.GUI import UserControl

# For State Buttons
AVAILABLE_STATES = [('Pause', 'PAUSE'),
                    ('Walking', 'REFERENCE_TRACKING'),
                    ('User Reference', 'USER_REFERENCE'),
                    ('Direct Actuator Input', 'USER_CONTROL')]

# For Gecko Representation
parts = [1, 2, 3, 4, 5, 6]

# pylint: disable= too-many-public-methods, unused-argument
class StatusObject(Gtk.Bin):
    """ Analysis Object """

    def __init__(self, data, parent):
        """
        *Initialize with:*
        Args:
            data (GlobalData object): the data you wanna plot
        """
        # Super Init:
        super(StatusObject, self).__init__()

        # DATA:
        self.state_button = {}
        self.gecko_repr = {}  # Dict of Gecko Repr
        self.parent = parent  # the gtk v2 gui main win

        main_box = Gtk.VBox(False, 2)
        self.add(main_box)

        # Buttons
        btns_vbox = Gtk.VBox(False, 0)
        btns_viewport = Gtk.Viewport()
        btns_viewport.add(btns_vbox)
        main_box.pack_start(btns_viewport, True, True, 1)
        self._init_buttons_widget(btns_vbox)

        # Gecko Repr
        repr_hbox = Gtk.HBox(False, 2)
        repr_viewport = Gtk.Viewport()
        repr_viewport.add(repr_hbox)
        main_box.pack_end(repr_viewport, False, False, 1)
        self._init_gecko_repr(repr_hbox, parts)

        self.show_all()

    def _init_buttons_widget(self, box):
        state_vbox = box
##         Overview Table:
#        overview_table = Gtk.Table(columns=2, rows=6, homogeneous=False)
#        state_vbox.pack_end(overview_table, False, False, 2)
#        btns = {'1 Legs': [0, 1, 2, 3],
#                '2 Belly': [4, 5],
#                '3 Feet': [6, 7, 8, 9]}
#        row_idx = 0
#        for cat in sorted(btns.iterkeys()):
#            label = Gtk.Label()
#            label.set_markup(cat)
#            overview_table.attach(label, 0, 1, row_idx, row_idx+1)
#            row_idx += 1
#            col_idx = 0
#            for elem in btns[cat]:
#                btn = Gtk.Button(str(elem))
#                btn.set_name(str(elem))
#                btn.connect('clicked', self.on_btn_clicked)
#                overview_table.attach(btn, col_idx, col_idx + 1,
#                                      row_idx, row_idx+1)
#                col_idx += 1
#                if col_idx == 2:
#                    col_idx = 0
#                    row_idx += 1
#
#        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
#        state_vbox.pack_end(separator, False, False, 5)
        label = Gtk.Label()
        label.set_markup('<big>\tCurrent State</big> ')
        label.set_halign(Gtk.Align.START)
        state_vbox.pack_start(label, False, False, 1)

        radiobtn = None
        for state in AVAILABLE_STATES:
            radiobtn = Gtk.RadioButton.new_from_widget(radiobtn)
            radiobtn.set_label(state[0])
            radiobtn.set_name(state[1])
            radiobtn.connect("toggled", self.on_selected)
            state_vbox.pack_start(radiobtn, False, False, 1)
            self.state_button[state] = radiobtn

    def on_selected(self, widget, data=None):
        if widget.get_active():
            print(widget.get_label()+" is selected")
            self.parent.task.state = widget.get_name()
            # if usercontrol window not open, open it
            in_list = 0
            userControlWindow = None
            for win in self.parent.list_of_open_windows:
                if isinstance(win, UserControl.UserControlWindow):
                    in_list += 1
                    userControlWindow = win
            if in_list:
                userControlWindow.on_quit_clicked()
            if widget.get_name() == 'USER_CONTROL':
                self.parent.list_of_open_windows.append(
                    UserControl.UserControlWindow(self.parent.task,
                        self.parent.list_of_open_windows, 'PWM'))
            if widget.get_name() == 'USER_REFERENCE':
                self.parent.list_of_open_windows.append(
                    UserControl.UserControlWindow(self.parent.task,
                            self.parent.list_of_open_windows, 'REF'))
            if widget.get_name() == 'REFERENCE_TRACKING':
                self.parent.list_of_open_windows.append(
                    UserControl.UserControlWindow(self.parent.task,
                            self.parent.list_of_open_windows, 'WALK'))


    def on_btn_clicked(self, btn):
        print btn.get_name()

    def _init_gecko_repr(self, box, parts):
        """ Put the gecko represention in a box """
        table = Gtk.Table(columns=2, rows=3, homogeneous=False)
        box.pack_start(table, False, False, 2)
        row_idx = 0
        col_idx = 0
        for part in parts:
            image_path = 'Src/Visual/GUI/pictures/'+str(part)+'/000.png'
            image = Gtk.Image()
            image.set_from_file(image_path)
            self.gecko_repr[str(part)] = image
            table.attach(image, col_idx, col_idx+1, row_idx, row_idx+1)
            col_idx += 1
            if col_idx == 2:
                col_idx = 0
                row_idx += 1

    def update_gecko_repr(self, data):
        """ Update the Gecko Representation according to the actual data """
        for part in self.gecko_repr:
            if part in data.recorded:
                #  print data.recorded[part]['val'][-1]
                pressure = int(round(data.recorded[part]['val'][-1]*10)*10)
                p_f = '00' + str(pressure)
                p_f = p_f[-3:]
                image_path = 'Src/Visual/GUI/pictures/'+part+'/'+p_f+'.png'
                self.gecko_repr[part].set_from_file(image_path)

        self.show_all()
        return True
