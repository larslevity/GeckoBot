"""
module for Plotting Area
"""


from gi.repository import Gtk
from matplotlib.figure import Figure as Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg
from numpy import nan
import numpy as np


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
        data = list(self.data.recorded[key]['val'])
        if self.look_at_present:
            val_new = data[-self._bufsize:]
        else:
            start_idx = self.look_at_head - self._bufsize
            start_idx = 0 if start_idx < 0 else start_idx
            val_new = data[start_idx:self.look_at_head]
        return val_new

    def get_vec_data(self, key, angle=0.52, width=5):
        """ data[vec]['val'] = [[x0, y0, x1, y1], ..., [x0, y0, x1, y1]] """
        x0, y0, x1, y1 = (self.data.recorded[key]['val'][-1])
        phi = np.arctan2(y1-y0, x1-x0)
        x2 = x1 - width*np.sin(np.pi/2-phi-angle)
        y2 = y1 - width*np.cos(np.pi/2-phi-angle)
        x3 = x1 - width*np.cos(phi-angle)
        y3 = y1 - width*np.sin(phi-angle)
        return ([x0, x1, x2, x3, x1], [y0, y1, y2, y3, y1])  # x,y,dx,dy


    def update(self, keylist):
        """
        Update the plot
        """

        # adjust number of plots if neccessary
        while len(keylist)+self.nMarkers > self.nartist:
            self.points[self.nartist] = self.axx.plot(nan, nan, '-')[0]
            self.nartist += 1

        # get selection
        mark = []
        vecidx = 0
        for artist, elem in enumerate(keylist):
            if elem[0][:3] == 'vec':  # special treat for vecs
                x, y = self.get_vec_data(elem[0])
                self.vectors[vecidx].set_data(x, y)
                vecidx += 1

            else:
                ord_val = self.getdata(elem[1])
                abs_val = self.getdata(elem[0])
                # update line
                self.points[artist+self.nMarkers].set_data(abs_val, ord_val)
    
                # position artist gets special care -> Marker
                if elem[0][0] == 'x' and elem[1][0] == 'y':  # key = (x?, y?)
                    if elem[0][1] == elem[1][1]:    # (? = ?)
                        artist = int(elem[0][1])  # idx = ?
                        if artist == 8:  # xref - special care
                            artist = 6
                        mark.append(artist)
                        ord_val = [ord_val[-1]]
                        abs_val = [abs_val[-1]]
                        # update line
                        self.points[artist].set_data(abs_val, ord_val)

        nomark = [x for x in range(self.nMarkers) if x not in mark]
        # set all other plots to None
        for artist in (list(range(len(keylist)+self.nMarkers, self.nartist))
                       + nomark):
            self.points[artist].set_data(nan, nan)
        for artist in range(vecidx, self.nVectors):
            self.vectors[artist].set_data(nan, nan)

        # recalc data limits
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
        # print "BufferSize: %s" % self._bufsize

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

    def set_look_at_HEAD(self, state):
        self.check_button.set_active(state)

    def __init__(self, data, toplevel):
        """
        *Initialize with:*

        Args:
            data (GlobalData Object): Source of Data
        """
        super(PlotArea, self).__init__()
        self.toplevel = toplevel
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
        #
        self.BufSizeSpinnBtn = None
        self.AxRatioBtn = None

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
        self.nartist = 16
        self.nMarkers = 7
        # set the first 7 artists as Markers instead of lines
        for artist in range(self.nMarkers):
            self.points[artist] = self.axx.plot(nan, nan, 'ko')[0]
        for artist in range(self.nMarkers, self.nartist):
            self.points[artist] = self.axx.plot(nan, nan, '-')[0]
        
        # init vectors
        self.vectors = {}
        self.nVectors = 1
        for artist in range(self.nVectors):
            self.vectors[artist] = self.axx.plot([nan, nan], [nan, nan],
                        linewidth=5)[0]

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
        image.set_from_file("Src/GUI/pictures/Equal.png")
        self.AxRatioBtn = Gtk.ToggleButton()
        self.AxRatioBtn.add(image)
        self.AxRatioBtn.connect("clicked", self.change_axes_aspect)
        self.AxRatioBtn.set_active(False)
        hbox.pack_start(self.AxRatioBtn, expand=False, fill=False, padding=0)
        # spacer for good looking
        spacer = Gtk.Label()
        hbox.pack_start(spacer, expand=True, fill=True, padding=0)
        # Adjustment for SpinButton:
        adjustment = Gtk.Adjustment(value=30, lower=1, upper=1e5,
                                    step_incr=1, page_incr=-1)
        # create Label
        label = Gtk.Label("Buffer [1]:")
        # pack label to hbox:
        hbox.pack_start(label, expand=False, fill=False, padding=0)
        # create a text enter field for buffer size
        self.BufSizeSpinnBtn = \
            Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        adjustment.connect("value_changed", self.change_buffer_size,
                           self.BufSizeSpinnBtn)
        # pack SpinButton zu hbox
        hbox.pack_start(self.BufSizeSpinnBtn, expand=False, fill=False,
                        padding=1)
