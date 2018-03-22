# -*- coding: utf-8 -*-
"""
Created on Wed May 25 17:32:33 2016

@author: ls
"""

from gi.repository import Gtk
from Src.Visual.GUI.User_control_modes import template


# pylint: disable=too-many-public-methods, unused-argument, too-many-locals
class PwmPage(Gtk.Bin):
    """
    Initialize the PWM-Screen

    Returns:
        (Gtk.Box): The PWM-Page
    """

    def __init__(self, task):
        # Attr
        self.task = task
        self.pwm_adjustment = {}
        # Super Init
        super(PwmPage, self).__init__()

        text = 'Enter PWM manually. \
            But be careful - you could cause extensive damage!'
        pwm_vbox, action_area, justify_area =\
            template.create_content_box(text, False)
        self.add(pwm_vbox)

        # Action Area - pwm adjusments and dvalve states
        mainhbox = Gtk.HBox(False, 2)
        vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(vbox, True, True, 2)
        action_area.pack_start(mainhbox, expand=True, fill=True, padding=2)

        # Fill the pwm area
        for name in sorted(self.task.pwm.iterkeys()):
            hbox = Gtk.HBox(False, 2)
            self.pwm_adjustment[name] =\
                Gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1,
                               page_size=1)
            pwm_spinner = Gtk.SpinButton(adjustment=self.pwm_adjustment[name],
                                         climb_rate=5, digits=0)
            self.pwm_adjustment[name].connect('value_changed', self._set_pwm)
            pwm_scroller = Gtk.HScrollbar(adjustment=self.pwm_adjustment[name])
            pwm_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/"+name+".png"
            pwm_image.set_from_file(imgpath)
            # pack the hbox
            hbox.pack_start(pwm_image, expand=False, fill=False, padding=2)
            hbox.pack_start(pwm_spinner, expand=False, fill=False, padding=2)
            hbox.pack_start(pwm_scroller, expand=True, fill=True, padding=2)
            vbox.pack_start(hbox, expand=True, fill=True, padding=2)
        # fill the dvalve area
        dvalve_vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(dvalve_vbox, expand=False, fill=False, padding=2)
        for name in sorted(self.task.dvalve_state.iterkeys()):
            btn_box = Gtk.HBox(False, 2)    # for the toggle btn
            label = Gtk.Label(name)
            dvalve_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/f"+name+".png"
            dvalve_image.set_from_file(imgpath)
            btn_box.pack_start(dvalve_image, False, False, 1)
            btn_box.pack_start(label, False, False, 1)
            toggle_button = Gtk.ToggleButton()
            toggle_button.add(btn_box)
            toggle_button.connect('toggled', self._set_state, name)
            dvalve_vbox.pack_start(
                toggle_button, expand=False, fill=False, padding=2)

        # Justify Area
        set_pwm_zero_btn = Gtk.Button('Set PWM to 0')
        set_pwm_zero_btn.connect('clicked', self._on_set_pwm_zero_btn_clicked)
        justify_area.pack_start(set_pwm_zero_btn, False, False, 2)

        self._on_set_pwm_zero_btn_clicked()

    def _set_state(self, btn, name):
        """
        Set the task.dvalve_state to the temporary state of the btn
        """
        self.task.dvalve_state[name] = int(btn.get_active())
#        print('Dvalve', name, 'was turned', btn.get_active())

    def _set_pwm(self, widget=None, event=None):
        """
        Set the task.pwm to the temporary pwm adjustments
        """
        for name in self.pwm_adjustment:
            self.task.pwm[name] = self.pwm_adjustment[name].get_value()

    def _on_set_pwm_zero_btn_clicked(self, widget=None, event=None):
        """
        Set the pwm adjustments to zeros and call self.set_pwm()
        """
        for name in self.pwm_adjustment:
            self.pwm_adjustment[name].set_value(0.)
        self._set_pwm()


class ReferencePage(Gtk.Bin):
    """
    Initialize the Reference-Screen

    Returns:
        (Gtk.Box): The Reference-Page
    """

    def __init__(self, task):
        # Attr
        self.task = task
        self.pwm_adjustment = {}
        # Super Init
        super(ReferencePage, self).__init__()

        text = 'Enter Reference manually. \
            But be careful - you could cause extensive damage!'
        pwm_vbox, action_area, justify_area =\
            template.create_content_box(text, False)
        self.add(pwm_vbox)

        # Action Area - pwm adjusments and dvalve states
        mainhbox = Gtk.HBox(False, 2)
        vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(vbox, True, True, 2)
        action_area.pack_start(mainhbox, expand=True, fill=True, padding=2)

        # Fill the pwm area
        for name in sorted(self.task.pwm.iterkeys()):
            hbox = Gtk.HBox(False, 2)
            self.pwm_adjustment[name] =\
                Gtk.Adjustment(value=0, lower=0, upper=1, step_incr=.01,
                               page_size=.01)
            pwm_spinner = Gtk.SpinButton(adjustment=self.pwm_adjustment[name],
                                         climb_rate=.01, digits=2)
            self.pwm_adjustment[name].connect('value_changed', self._set_pwm)
            pwm_scroller = Gtk.HScrollbar(adjustment=self.pwm_adjustment[name])
            pwm_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/"+name+".png"
            pwm_image.set_from_file(imgpath)
            # pack the hbox
            hbox.pack_start(pwm_image, expand=False, fill=False, padding=2)
            hbox.pack_start(pwm_spinner, expand=False, fill=False, padding=2)
            hbox.pack_start(pwm_scroller, expand=True, fill=True, padding=2)
            vbox.pack_start(hbox, expand=True, fill=True, padding=2)
        # fill the dvalve area
        dvalve_vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(dvalve_vbox, expand=False, fill=False, padding=2)
        for name in sorted(self.task.dvalve_state.iterkeys()):
            btn_box = Gtk.HBox(False, 2)    # for the toggle btn
            label = Gtk.Label(name)
            dvalve_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/f"+name+".png"
            dvalve_image.set_from_file(imgpath)
            btn_box.pack_start(dvalve_image, False, False, 1)
            btn_box.pack_start(label, False, False, 1)
            toggle_button = Gtk.ToggleButton()
            toggle_button.add(btn_box)
            toggle_button.connect('toggled', self._set_state, name)
            dvalve_vbox.pack_start(
                toggle_button, expand=False, fill=False, padding=2)

        # Justify Area
        set_pwm_zero_btn = Gtk.Button('Set Reference to Zero')
        set_pwm_zero_btn.connect('clicked', self._on_set_pwm_zero_btn_clicked)
        justify_area.pack_start(set_pwm_zero_btn, False, False, 2)

        self._on_set_pwm_zero_btn_clicked()

    def _set_state(self, btn, name):
        """
        Set the task.dvalve_state to the temporary state of the btn
        """
        self.task.dvalve_state[name] = int(btn.get_active())
#        print('Dvalve', name, 'was turned', btn.get_active())

    def _set_pwm(self, widget=None, event=None):
        """
        Set the task.pwm to the temporary pwm adjustments
        """
        for name in self.pwm_adjustment:
            self.task.ref[name] = self.pwm_adjustment[name].get_value()

    def _on_set_pwm_zero_btn_clicked(self, widget=None, event=None):
        """
        Set the pwm adjustments to zeros and call self.set_pwm()
        """
        for name in self.pwm_adjustment:
            self.pwm_adjustment[name].set_value(0)
        self._set_pwm()


class WalkingPage(Gtk.Bin):
    """
    Initialize the Walking-Screen

    Returns:
        (Gtk.Box): The Walking-Page
    """

    def __init__(self, task):
        # Attr
        self.task = task
        self.entry = {}
        self.pattern = self.task.pattern
        print('default pattern:', self.pattern)
        # Super Init
        super(WalkingPage, self).__init__()

        text = 'Enter Pattern manually.'
        pwm_vbox, action_area, justify_area =\
            template.create_content_box(text, False)
        self.add(pwm_vbox)

        # Action Area - pwm adjusments and dvalve states
        mainhbox = Gtk.HBox(False, 2)
        vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(vbox, True, True, 2)
        action_area.pack_start(mainhbox, expand=True, fill=True, padding=2)

#         Fill the pwm area
        idx = 0
        for name in sorted(self.task.pwm.iterkeys()):
            hbox = Gtk.HBox(False, 2)
            self.entry[name] = Gtk.Entry()
            text = ''
            for p in self.pattern:
                text = text + str(p[idx]) + ', '
            text = text[:-2]
            self.entry[name].set_text(text)
            pwm_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/"+name+".png"
            pwm_image.set_from_file(imgpath)
            # pack the hbox
            hbox.pack_start(pwm_image, expand=False, fill=False, padding=2)
            hbox.pack_start(self.entry[name], expand=False,
                            fill=False, padding=2)
            vbox.pack_start(hbox, expand=True, fill=True, padding=2)
            idx += 1
#         fill the dvalve area
        for name in sorted(self.task.dvalve_state.iterkeys()):
            btn_box = Gtk.HBox(False, 2)    # for the toggle btn
            self.entry['f'+name] = Gtk.Entry()
            text = ''
            for p in self.pattern:
                text = text + str(p[idx]) + ', '
            text = text[:-2]
            self.entry['f'+name].set_text(text)

            dvalve_image = Gtk.Image()
            imgpath = "Src/Visual/GUI/pictures/User_Control/f"+name+".png"
            dvalve_image.set_from_file(imgpath)
            btn_box.pack_start(dvalve_image, False, False, 2)
            btn_box.pack_start(self.entry['f'+name], False, False, 2)
            vbox.pack_start(btn_box, expand=False, fill=False, padding=2)
            idx += 1
        # fill tsampling area
        tmin_box = Gtk.HBox(False, 2)
        self.entry['tmin'] = Gtk.Entry()
        text = ''
        for p in self.pattern:
            text = text + str(p[idx]) + ', '
        text = text[:-2]
        self.entry['tmin'].set_text(text)
        tmin_label = Gtk.Label('Minimum Process Time:')
        tmin_box.pack_start(tmin_label, False, False, 2)
        tmin_box.pack_start(self.entry['tmin'], False, False, 2)
        vbox.pack_start(tmin_box, False, False, 2)

        del idx

        # Justify Area
        status_vbox = Gtk.VBox(False, 2)
        mainhbox.pack_start(status_vbox, False, False, 2)
        lbl = Gtk.Label()
        lbl.set_markup('<big>\tCurrent Pattern</big> ')
        self.status_label = Gtk.Label()
        self._refresh_label()
        status_vbox.pack_start(lbl, False, False, 2)
        status_vbox.pack_start(self.status_label, False, False, 2)

        set_pattern_btn = Gtk.Button('Set Pattern')
        set_pattern_btn.connect('clicked', self._on_set_pattern_btn_clicked)
        justify_area.pack_start(set_pattern_btn, False, False, 2)

        start_walking_btn = Gtk.Button('START Walking')
        start_walking_btn.connect('clicked', self._on_start_walking_btn)
        justify_area.pack_start(start_walking_btn, False, False, 2)

        stop_walking_btn = Gtk.Button('STOP Walking')
        stop_walking_btn.connect('clicked', self._on_stop_walking_btn)
        justify_area.pack_start(stop_walking_btn, False, False, 2)

        self._get_pattern()
        self._refresh_label()

    def _on_stop_walking_btn(self, widget):
        # send task to BBB
        self.task.walking_state = False
        self.task.set_walking_state = True

    def _on_start_walking_btn(self, widget):
        # send task to BBB
        self.task.walking_state = True
        self.task.set_walking_state = True

    def _refresh_label(self):
        str_pattern = ''
        for elem in self.pattern:
            str_pattern = str_pattern + str(elem)+'\n'
        self.status_label.set_markup(str_pattern)
        self.show_all()

    def _get_pattern(self):
        pattern = [[None for i in range(11)] for i in range(
            len(self.entry['1'].get_text().split()))]
        for idx, name in enumerate(sorted(self.entry.iterkeys())):
            text = self.entry[name].get_text()
            text_split = text.split(',')
            try:
                for pose, split in enumerate(text_split):
                    if name[0] == 'f':
                        ref = str2bool(split)
                    else:
                        ref = float(split)
                    # print 'pose', pose, idx, 'ref:', ref
                    pattern[pose][idx] = ref
            except ValueError as msg:
                print msg
        l_p = [len(pp) for pp in pattern]
        if l_p.count(l_p[0]) == len(l_p):
            self.pattern = pattern
        else:
            print 'single items should have the same length..'

    def _on_set_pattern_btn_clicked(self, widget):
        self._get_pattern()
        self._refresh_label()
        # send pattern to BBB
        self.task.pattern = self.pattern
        self.task.set_pattern = True


def str2bool(v):
    return v.lower() in ("yes", "true", " true", "1", " 1")
