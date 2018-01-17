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
    def find_default_keylist(self, modus='m'):
        """ Look in Recorder and check what data is worth to plot """
        keylist = []
        keylist_u = []
        keylist_r = []
        for el in sorted(self.data.recorded.iterkeys()):
            if len(el.split('_')) == 1:
                if len(el.split('u')) == 2 and len(el.split('u')[0]) == 0:
                    if el+'_t' in self.data.recorded:
                        keylist_u.append((el+'_t', el))
                elif len(el.split('r')) == 2 and len(el.split('r')[0]) == 0:
                    if el+'_t' in self.data.recorded:
                        keylist_r.append((el+'_t', el))
                elif el+'_t' in self.data.recorded:
                    keylist.append((el+'_t', el))
        if modus == 'm':
            return keylist
        elif modus == 'u':
            return keylist_u
        elif modus == 'r':
            return keylist_r

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
        for key in keylist_to_append:
            if self.selection(key[0], key[1], True) not in self._selected:
                if self.selection(key[0], key[1], False) not in self._selected:
                    self._selected.append(self.selection(key[0], key[1], True))
        self._refresh_display_box()

    def delete_keylist(self, widget):
        for idx  in range(len(self._selected)):
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
        # key list of (abs,ord)-tuple with only visible selections
        self.keylist = []
        m = self.find_default_keylist()
        # construct a named tuple containing all selections
        self.selection = namedtuple('selection', 'abszisse ordinate visible')
        # store for all selections
        self._selected = []

        # FRAME of Selection Area
        # add main vbox
        self.main_vbox = Gtk.VBox(homogeneous=False, spacing=3)
        self.add(self.main_vbox)
        # Buttons to simplify selection filling
        btns_viewport = Gtk.Viewport()
        btns_hbox = Gtk.HBox(True, 2)
        self.main_vbox.pack_start(btns_viewport, False, False, 2)
        btns_viewport.add(btns_hbox)
        m_btn = Gtk.Button('m')
        m_btn.connect("clicked", self.keylist_append, 'm')
        btns_hbox.pack_start(m_btn, False, False, 2)
        u_btn = Gtk.Button('u')
        u_btn.connect("clicked", self.keylist_append, 'u')
        btns_hbox.pack_start(u_btn, False, False, 2)
        r_btn = Gtk.Button('r')
        r_btn.connect("clicked", self.keylist_append, 'r')
        btns_hbox.pack_start(r_btn, False, False, 2)
        del_btn = Gtk.Button()
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/delete.gif")
        del_btn.add(image)
        del_btn.connect("clicked", self.delete_keylist)
        btns_hbox.pack_start(del_btn, False, False, 2)
        # create display VBox in a scrolled window
        self.list_selection = Gtk.Viewport()
        self.main_vbox.pack_start(self.list_selection, True, True, 1)
        self.display_vbox = Gtk.VBox(homogeneous=True, spacing=1)
        self.list_selection.add(self.display_vbox)
        self.vis_btn = {}
        # create select HBox
        select_view = Gtk.Viewport()
        self.select_hbox = Gtk.HBox(homogeneous=True, spacing=1)
        self.main_vbox.pack_start(select_view, False, False, 1)
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
            self.select_hbox.pack_start(vbox, True, False, 0)
            # create label and pack it to select_hbox:
            label = Gtk.Label()
            label.set_markup('<b>{}</b>'.format(axis))
            vbox.pack_start(label, True, False, 0)
            # create a vertical box in a scrolled win within the select_hbox
            scrolled_win = Gtk.ScrolledWindow()
            scrolled_win.set_min_content_width(100)
            scrolled_win.set_min_content_height(100)
            vbox.pack_start(scrolled_win, True, False, 0)
            # another vbox
            vbox = Gtk.VBox(homogeneous=True, spacing=1)
            # Put the vbox in the scrolled Window which is in the select_hbox
            scrolled_win.add_with_viewport(vbox)
            # create a Button for each key in data.recorded
            for key in sorted(self.data.recorded.iterkeys()):
                button = Gtk.Button(key)
                # connect Button
                button.connect("clicked", self.push_axis_to_display_clicked,
                               key, axis)
                # Put button into vbox
                vbox.pack_start(button, expand=True, fill=True, padding=2)
            self.show_all()

    def _refresh_display_box(self):
        """
        refresh the display screen
        """
        # remove all widget from self.display_vbox, i.e. destroy and create new
        self.list_selection.remove(self.list_selection.get_child())
        self.display_vbox = Gtk.VBox(homogeneous=True, spacing=1)
        self.list_selection.add(self.display_vbox)
        self.vis_btn = {}

        for idx, selection in enumerate(self._selected):
            # create HBox
            hbox = Gtk.HBox(homogeneous=False, spacing=2)
            # put the hbox into the display_vbox
            self.display_vbox.pack_start(hbox, True, False, 1)
            # #### Label Ordinate ####
            label_abs = Gtk.Label(selection.abszisse)
            label_abs.set_width_chars(10)
            hbox.pack_start(label_abs, expand=True, fill=False, padding=1)
            # #### Label Ordinate ####
            label_ord = Gtk.Label(selection.ordinate)
            label_ord.set_width_chars(1)
            hbox.pack_start(label_ord, expand=True, fill=False, padding=1)
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
            hbox.pack_start(self.vis_btn[idx], True, False, 1)
            # #### Delete Button ####
            # create image
            image = Gtk.Image()
            image.set_from_file("Src/Visual/GUI/pictures/delete.gif")
            # a button to contain the image widget
            button = Gtk.Button()
            button.add(image)
            button.connect("clicked", self.delete_selection_btn_clicked, idx)
            hbox.pack_start(button, expand=True, fill=False, padding=1)
        self.show_all()
