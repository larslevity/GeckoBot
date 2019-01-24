"""
module for Plotting Area
"""


from gi.repository import Gtk
from matplotlib.figure import Figure as Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg
from numpy import nan


# pylint: disable=too-many-instance-attributes, unused-argument
# pylint: disable=too-many-public-methods
class PlotArea(Gtk.Bin):
    """
    Gtk object with single child
    for the plotting area
    """

    def getdata(self, key):
        """
        Define here were the data comes from

        Args:
            key (str): keyword which data
        """
        if self.look_at_present:
            val_new = self.data.recorded[key]['val'][-self._bufsize:]
        else:
            start_idx = self.look_at_head - self._bufsize
            val_new =\
                self.data.recorded[key]['val'][start_idx:self.look_at_head]
        return val_new

    def update(self, keylist):
        """
        Update the plot
        """
        # update upper boarder of lookat_head
        maxidx = self.data.max_idx
        self.adj_scroll_hist.set_upper(maxidx)
        # update value
        if self.look_at_present:
            self.adj_scroll_hist.set_value(maxidx)
        # increase number of plots if neccessary
        while len(keylist) > self.nartist:
            self.points[self.nartist] = self.axx.plot(nan, nan, '-')[0]
            self.nartist += 1
        # get selection
        for artist, elem in enumerate(keylist):
            ord_val = self.getdata(elem[1])
            abs_val = self.getdata(elem[0])
            # update line
            self.points[artist].set_data(abs_val, ord_val)
        # set all other plots to None
        for artist in range(len(keylist), self.nartist):
            self.points[artist].set_data(nan, nan)

        # scaling stuff
        self.axx.relim()
        self.axx.autoscale_view(tight=None, scalex=True, scaley=True)
        # draw the thing
        self.canvas.draw()
        # return True for GLib to continue
        return True

    def change_buffer_size(self, widget, spin):
        """
        Change the BufferSize to the value of SpinButton
        """
        timewindow = spin.get_value_as_int()
        self._bufsize = int(timewindow)
        print "BufferSize: %s" % self._bufsize

    def change_look_at_hist(self, widget, event=None):
        """
        Set the Head of 'look_at' to the current index of the Widget
        """
        self.look_at_head = int(widget.get_value())

    def look_at_present_callback(self, widget):
        """ Set the bool 'look_at_present' to the value of widget """
        self.look_at_present = widget.get_active()

    def change_axes_aspect(self, widget):
        """ Change axes aspect either to 'equal' or 'auto'
        """
        if widget.get_active():
            self.axx.set_aspect('equal')
        else:
            self.axx.set_aspect('auto')

    def __init__(self, data):
        """
        *Initialize with:*

        Args:
            data (GlobalData Object): Source of Data
        """
        super(PlotArea, self).__init__()

        # GlobalData
        self.data = data
        # look_at_head: index-_bufsize:index -> the data you gonna display
        self.look_at_head = 0
        # look at present?
        self.look_at_present = True
        # number of points in buffer
        self._bufsize = int(100)
        # scrol Window Adjustments
        self.adj_scroll_hist = None
        self.axisequal = False

        # MPL:
        # create figure
        self.figure = Figure()
        # create axes
        self.axx = self.figure.add_subplot(111)
        # set grid
        self.axx.grid(True)
        # set equal scale
        self.axx.set_aspect('auto')
        # set dynamic canvas to GTK3AGG backend
        self.canvas = FigureCanvasGTK3Agg(self.figure)
        # init plots
        self.points = {}
        self.nartist = 10
        for artist in range(self.nartist):
            self.points[artist] = self.axx.plot(nan, nan, '-')[0]

        # GTK:
        vbox = Gtk.VBox(False, 3)
        self.add(vbox)
        # Get PlotWindow and connect to figure
        self.plot_win = Gtk.Viewport()
        self.plot_win.add(self.canvas)

        self.buffer_win = Gtk.Viewport()
        vbox.pack_start(self.plot_win, True, True, 0)
        vbox.pack_start(self.buffer_win, False, True, 1)
        self._init_buffer_box()

        # ######
        # finally show
        self.canvas.show()
        self.show_all()

    def _init_buffer_box(self):
        """ Build the frame of the Box with Look_at and BufferSize adjustments
        """
        # create another vbox
        vbox = Gtk.VBox(homogeneous=False, spacing=1)
        # Put the hbox in the Buffer Window
        self.buffer_win.add(vbox)
        # create hbox
        hbox = Gtk.HBox(homogeneous=False, spacing=1)
        # put hbox into vbox
        vbox.pack_start(hbox, expand=True, fill=True, padding=1)
        # ToggleButton for equal AxisButton
        image = Gtk.Image()
        image.set_from_file("Src/Visual/GUI/pictures/Equal.png")
        toggle_btn = Gtk.ToggleButton()
        toggle_btn.add(image)
        toggle_btn.connect("clicked", self.change_axes_aspect)
        toggle_btn.set_active(False)
        hbox.pack_start(toggle_btn, expand=False, fill=False, padding=0)
        # spacer for good looking
        spacer = Gtk.Label()
        hbox.pack_start(spacer, expand=True, fill=True, padding=0)
        # Adjustment for SpinButton:
        adjustment = Gtk.Adjustment(value=30, lower=1, upper=1e5,
                                    step_incr=1, page_incr=-1)
        # create Label
        label = Gtk.Label("Time Window [sec]:")
        # pack label to hbox:
        hbox.pack_start(label, expand=False, fill=False, padding=0)
        # create a text enter field for buffer size
        button = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        adjustment.connect("value_changed", self.change_buffer_size, button)
        # pack SpinButton zu hbox
        hbox.pack_start(button, expand=False, fill=False, padding=1)

        # #### ScrollBar
        hbox = Gtk.HBox(homogeneous=False, spacing=1)
        vbox.pack_start(hbox, expand=True, fill=False, padding=1)
        self.adj_scroll_hist = Gtk.Adjustment(value=0, lower=0,
                                              upper=self.look_at_head,
                                              step_incr=10, page_size=1)
        scroll_button = Gtk.HScrollbar(adjustment=self.adj_scroll_hist)
        self.adj_scroll_hist.connect("value_changed", self.change_look_at_hist,
                                     scroll_button)
        label = Gtk.Label("Look at:")
        hbox.pack_start(label, expand=False, fill=False, padding=1)
        hbox.pack_start(scroll_button, expand=True, fill=True, padding=1)
        check_button = Gtk.CheckButton("Present")
        check_button.connect("clicked", self.look_at_present_callback)
        check_button.set_active(True)
        hbox.pack_start(check_button, expand=False, fill=False, padding=1)
        spinner = Gtk.SpinButton(adjustment=self.adj_scroll_hist, climb_rate=1,
                                 digits=0)
        hbox.pack_start(spinner, expand=False, fill=False, padding=1)
