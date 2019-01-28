# -*- coding: utf-8 -*-
"""
Analysis Tool
"""
# pylint: disable= no-name-in-module
from gi.repository import Gtk
from Src.Visual.GUI import PlotArea
from Src.Visual.GUI import SelectionArea


# pylint: disable= too-many-public-methods, unused-argument
class AnalysisObject(Gtk.Bin):
    """ Analysis Object """

    def __init__(self, data, toplevel):
        """
        *Initialize with:*
        Args:
            data (GlobalData object): the data you wanna plot
        """
        # Super Init:
        super(AnalysisObject, self).__init__()

        # DATA:
        # Init Global Data
        self.data = data

        # #### Fill Buffer Window ####
        hbox = Gtk.HBox(False, 2)
        self.add(hbox)
        self.plot_win = PlotArea.PlotArea(self.data, toplevel=toplevel)
        self.select_win = SelectionArea.SelectionArea(self.data)
        hbox.pack_start(self.plot_win, True, True, 2)
        hbox.pack_start(self.select_win, False, False, 2)

        self.show_all()
