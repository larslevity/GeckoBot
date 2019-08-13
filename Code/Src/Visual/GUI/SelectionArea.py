"""
Selection Area class
"""

from collections import namedtuple
from gi.repository import Gtk


# pylint: disable=too-many-instance-attributes, unused-argument
# pylint: disable=too-many-public-methods, too-many-branches
class SelectionArea(Gtk.Bin):
    """
    Selection Area with the atrribute keylist containing tuple of (abs, ord)
    which somebody selected to plot in the Plotting Area
    """
    def find_default_keylist(self, modus='p'):
        """ Look in Recorder and check what data is worth to plot """
        keylist = []
        if modus == 'pos':
            recorded_data = sorted(self.data.recorded.iterkeys())
            for idx in range(6) + [8]:
                if 'x{}'.format(idx) in recorded_data:
                    if 'y{}'.format(idx) in recorded_data:
                        keylist.append(('x{}'.format(idx), 'y{}'.format(idx)))
        else:
            for el in sorted(self.data.recorded.iterkeys()):
                if len(el.split('_')) == 1:
                    if (len(el.split(modus)) == 2 and
                       len(el.split(modus)[0]) == 0):
                        if 'time' in self.data.recorded:
                            keylist.append(('time', el))

        return keylist

    def set_keylist(self, desired_keylist):
        """
        Set keylist manually

        Args:
            desired_keylist (list): List of tuples of the desired plots
        """
        self._selected = []
        for key in desired_keylist:
            self._selected.append(self.selection(key[0], key[1], True))
        self._refresh_display_box()

    def keylist_append(self, widget, modus):
        """
        Append a keylist manually to the self.selection

        Args:
            keylist_to_append (list): List of tuples of the desired plots
        """
        keylist_to_append = self.find_default_keylist(modus)
        idx = []
        for key in keylist_to_append:
            if self.selection(key[0], key[1], True) not in self._selected:
                if self.selection(key[0], key[1], False) not in self._selected:
                    self._selected.append(self.selection(key[0], key[1], True))
                else:
                    idx.append(self._selected.index(
                        self.selection(key[0], key[1], False)))
            else:
                idx.append(self._selected.index(
                    self.selection(key[0], key[1], True)))
        if len(idx) == len(keylist_to_append):
            for i in sorted(idx, reverse=True):
                self.delete_selection_btn_clicked(None, i)

        self._refresh_display_box()

    def delete_keylist(self, widget):
        for idx in range(len(self._selected)):
            self.vis_btn[idx].set_active(False)
        self._selected = []
        self._refresh_display_box()

#        self._selected = []
#        self._refresh_display_box()

    def push_axis_to_display_clicked(self, widget, key, axis):
        """
        Push key in Table
        """
        free_idx = None
        already_inserted = False
        if axis is "abszisse":
            # find free index:
            for idx, selection in enumerate(self._selected):
                if selection.abszisse is None:
                    free_idx = idx
                    break
            # check if new_tuple alread exist:
            if free_idx is not None:
                new_tuple = (key, self._selected[free_idx].ordinate)
                for idx, selection in enumerate(self._selected):
                    if new_tuple == (selection.abszisse, selection.ordinate):
                        already_inserted = True
                        break
                # insert if all is valid
                if not already_inserted and self._check_valid(free_idx, key):
                    self._selected[free_idx] =\
                        self.selection(key, self._selected[free_idx].ordinate,
                                       True)
            else:
                self._selected.append(self.selection(key, None, False))
        # same for ordinate
        if axis is "ordinate":
            # find free index:
            for idx, selection in enumerate(self._selected):
                if selection.ordinate is None:
                    free_idx = idx
                    break
            # check if new_tuple alread exist:
            if free_idx is not None:
                new_tuple = (self._selected[free_idx].abszisse, key)
                for idx, selection in enumerate(self._selected):
                    if new_tuple == (selection.abszisse, selection.ordinate):
                        already_inserted = True
                        break
                # insert if all is valid
                if not already_inserted and self._check_valid(free_idx, key):
                    self._selected[free_idx] =\
                        self.selection(self._selected[free_idx].abszisse, key,
                                       True)
            else:
                self._selected.append(self.selection(None, key, False))

        if already_inserted:
            print '(%s, %s) is already inserted' % new_tuple
        else:
            self._refresh_display_box()

    def _check_valid(self, idx, key):
        """ Check wether the length of a pair is the same """
        # check if the tuple will be complete
        abszisse = self._selected[idx].abszisse
        ordinate = self._selected[idx].ordinate
        print abszisse, ordinate
        if abszisse is None:
            abszisse = key
        elif ordinate is None:
            ordinate = key
        else:
            return 'Error'

        # check if same length
        len_abs = self.data.recorded[abszisse]['len']
        len_ord = self.data.recorded[ordinate]['len']
        print len_abs, len_ord
        if len_abs == len_ord:
            return True
        else:
            print 'tuple is not same length'
            return False

    def delete_selection_btn_clicked(self, widget, idx):
        """
        Remove selction for the given idx
        """
        self.vis_btn[idx].set_active(False)
        del self._selected[idx]
        self._refresh_display_box()
        print "Row %s is deleted" % idx

    def visible_selection_btn_clicked(self, widget, idx):
        """
        Enable or Disable the visibility of plot with this idx
        """
        # get labels:
        abszisse = self._selected[idx].abszisse
        ordinate = self._selected[idx].ordinate
        # check if labels are valid
        if abszisse in self.data.recorded and ordinate in self.data.recorded:
            # ON or OFF?
            if widget.get_active():
                # Already appended?
                if (abszisse, ordinate) not in self.keylist:
                    self.keylist.append((abszisse, ordinate))
#                    print "(%s, %s) is in keylist" % (abszisse, ordinate)
                    self._selected[idx] = self.selection(abszisse, ordinate,
                                                         True)
            # OFF -> rm from list and delete plot
            else:
                if (abszisse, ordinate) in self.keylist:
                    self.keylist.remove((abszisse, ordinate))
                    print "(%s, %s) is removed from keylist" % (abszisse,
                                                                ordinate)
                self._selected[idx] = self.selection(abszisse, ordinate, False)
        # Not valid: set to inactive
        else:
            widget.set_active(False)

    def __init__(self, data):
        """
        *Initialize with:*

        Args:
            data (GlobalData Object): the source of the data
        """
        # super init:
        super(SelectionArea, self).__init__()

        # Global Data
        self.data = data
        self.choices = [key for key in sorted(self.data.recorded.iterkeys())]
        # key list of (abs,ord)-tuple with only visible selections
        self.keylist = []
        m = self.find_default_keylist()
        # construct a named tuple containing all selections
        self.selection = namedtuple('selection', 'abszisse ordinate visible')
        # store for all selections
        self._selected = []

        # FRAME of Selection Area
        # first add hbox
        self.main_hbox = Gtk.HBox(homogeneous=False, spacing=3)
        self.add(self.main_hbox)

        # add main vbox
        self.main_vbox = Gtk.VBox(homogeneous=False, spacing=3)
        self.main_hbox.pack_start(self.main_vbox, True, True, 1)
        # ##### BTNS View #############################################
        # Buttons to simplify selection filling
        btns_viewport = Gtk.Viewport()
        btns_vbox = Gtk.VBox(True, 1)
        btns_hbox1 = Gtk.HBox(True, 1)
        btns_hbox2 = Gtk.HBox(True, 1)
        btns_vbox.pack_start(btns_hbox1, False, False, 0)
        btns_vbox.pack_start(btns_hbox2, False, False, 0)
        self.main_vbox.pack_start(btns_viewport, False, False, 2)
        btns_viewport.add(btns_vbox)
        # p btn
        p_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/pressure.png")
        p_btn.add(image)
        p_btn.connect("clicked", self.keylist_append, 'p')
        btns_hbox1.pack_start(p_btn, False, False, 2)
        # u btn
        u_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/motor_input.png")
        u_btn.add(image)
        u_btn.connect("clicked", self.keylist_append, 'u')
        btns_hbox1.pack_start(u_btn, False, False, 2)
        # r btn
        r_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/reference.png")
        r_btn.add(image)
        r_btn.connect("clicked", self.keylist_append, 'r')
        btns_hbox1.pack_start(r_btn, False, False, 2)
        # del btn
        del_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/delete.png")
        del_btn.add(image)
        del_btn.connect("clicked", self.delete_keylist)
        btns_hbox1.pack_start(del_btn, False, False, 2)
        # alpha btn
        alpha_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/alpha_IMG.png")
        alpha_btn.add(image)
        alpha_btn.connect("clicked", self.keylist_append, 'a')
        btns_hbox2.pack_start(alpha_btn, False, False, 2)
        # epsilon btn
        eps_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/epsilon.png")
        eps_btn.add(image)
        eps_btn.connect("clicked", self.keylist_append, 'e')
        btns_hbox2.pack_start(eps_btn, False, False, 2)
        # pos btn
        pos_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/pos_feet.png")
        pos_btn.add(image)
        pos_btn.connect("clicked", self.keylist_append, 'pos')
        btns_hbox2.pack_start(pos_btn, False, False, 2)
        # fixation btn
        fix_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/fixation.png")
        fix_btn.add(image)
        fix_btn.connect("clicked", self.keylist_append, 'f')
        btns_hbox2.pack_start(fix_btn, False, False, 2)

        # ### Selected - View #############################################
        # create display VBox in a scrolled window
        s_view = Gtk.Viewport()
        vbox = Gtk.VBox(homogeneous=False, spacing=1)
        self.main_vbox.pack_start(s_view, True, True, 0)
        s_view.add(vbox)
        page_size = Gtk.Adjustment(lower=10, page_size=100)
        scrolled_win = Gtk.ScrolledWindow(page_size)
        scrolled_win.set_min_content_width(200)
        scrolled_win.set_min_content_height(100)
        vbox.pack_start(scrolled_win, True, True, 0)
        # another vbox
        vbox = Gtk.VBox(homogeneous=False, spacing=1)
        # Put the vbox in the scrolled Window which is in the select_hbox
        scrolled_win.add_with_viewport(vbox)
        self.list_selection = Gtk.Viewport()
#        self.main_vbox.pack_start(self.list_selection, False, False, 1)
        vbox.pack_start(self.list_selection, False, False, 1)
        self.display_vbox = Gtk.VBox(homogeneous=False, spacing=1)
        self.list_selection.add(self.display_vbox)
        self.vis_btn = {}

        # ### Selection - View #############################################
        # create select HBox
        select_view = Gtk.Viewport()
        self.select_hbox = Gtk.HBox(homogeneous=True, spacing=1)
        self.main_hbox.pack_start(select_view, True, True, 1)
        select_view.add(self.select_hbox)
        # init the Window:
        self._init_select_hbox()
        self.set_keylist(m)

        self.show_all()

    def _init_select_hbox(self):
        """
        Build the frame of the Select-HBox, where teh select-buttons live in.
        """
        # remove all children
        for child in self.select_hbox.get_children():
            self.select_hbox.remove(child)
        # fill the hbox again
        for axis in ["abszisse", "ordinate"]:
            # create vbox
            vbox = Gtk.VBox(homogeneous=False, spacing=1)
            self.select_hbox.pack_start(vbox, False, False, 0)
            # create label and pack it to select_hbox:
            label = Gtk.Label()
            label.set_markup('<b>{}</b>'.format(axis[:3]))
            vbox.pack_start(label, False, False, 7)
            # create a vertical box in a scrolled win within the select_hbox
            page_size = Gtk.Adjustment(lower=10, page_size=100)
            scrolled_win = Gtk.ScrolledWindow(page_size)
            scrolled_win.set_min_content_width(80)
            scrolled_win.set_min_content_height(100)
            vbox.pack_start(scrolled_win, True, True, 0)
            # another vbox
            vbox = Gtk.VBox(homogeneous=False, spacing=1)
            # Put the vbox in the scrolled Window which is in the select_hbox
            scrolled_win.add_with_viewport(vbox)
            # create a Button for each key in data.recorded
            for key in sorted(self.data.recorded.iterkeys()):
                button = Gtk.Button(key)
                # connect Button
                button.connect("clicked", self.push_axis_to_display_clicked,
                               key, axis)
                button.set_property("height-request", 37.7)
                # Put button into vbox
                vbox.pack_start(button, expand=False, fill=False, padding=1)
            self.show_all()

    def _refresh_display_box(self):
        """
        refresh the display screen
        """
        # remove all widget from self.display_vbox, i.e. destroy and create new
        self.list_selection.remove(self.list_selection.get_child())
        self.display_vbox = Gtk.VBox(homogeneous=False, spacing=1)
        self.list_selection.add(self.display_vbox)
        self.vis_btn = {}

        for idx, selection in enumerate(self._selected):
            # create HBox
            hbox = Gtk.HBox(homogeneous=False, spacing=2)
            # put the hbox into the display_vbox
            self.display_vbox.pack_start(hbox, False, False, 1)
            # #### Label Ordinate ####
            label_abs = Gtk.Label(selection.abszisse)
            label_abs.set_width_chars(10)
            hbox.pack_start(label_abs, expand=False, fill=False, padding=1)
            # #### Label Ordinate ####
            label_ord = Gtk.Label(selection.ordinate)
            label_ord.set_width_chars(1)
            hbox.pack_start(label_ord, expand=False, fill=False, padding=1)
            # #### Delete Button ####
            # create image
            image = Gtk.Image()
            image.set_from_file("Src/Visual/GUI/pictures/delete.gif")
            # a button to contain the image widget
            button = Gtk.Button()
            button.add(image)
            button.connect("clicked", self.delete_selection_btn_clicked, idx)
            hbox.pack_end(button, expand=False, fill=False, padding=1)
            # #### Visible Button ####
            # create image
            image = Gtk.Image()
            image.set_from_file("Src/Visual/GUI/pictures/visible.png")
            # a button to contain the image widget
            self.vis_btn[idx] = Gtk.ToggleButton()
            self.vis_btn[idx].add(image)
            self.vis_btn[idx].connect("clicked",
                                      self.visible_selection_btn_clicked, idx)
            self.vis_btn[idx].set_active(selection.visible)
            hbox.pack_end(self.vis_btn[idx], False, False, 1)

        self.show_all()
