# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 20:08:18 2018

For the Tbas install the prerelease from github:
pip install dash-core-components==0.13.0-rc4


@author: ls
"""
from __future__ import print_function

import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from collections import deque
import time
import os
import flask
import __builtin__
import sys
import threading
import traceback

from termcolor import colored
from Src.Communication import pickler
from Src.Controller import controller as ctrlib


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


class WebserverThread(threading.Thread):
    def __init__(self, cargo):
        """ """
        print('Initialize server ...')
        threading.Thread.__init__(self)
        self.cargo = cargo
        self.uiVars = UI_Vars()
        pattern = cargo.wcomm.pattern
        PATTusr = [
         [0.00, 0.00, 0.00, 0.0, 0.25, 0.00, False, True, True, False, 5.0],
         [0.00, 0.00, 0.00, 0.0, 0.25, 0.00, True, True, True, True, 2.0],
         [0.00, 0.00, 0.00, 0.0, 0.25, 0.00, True, False, False, True, 1.0],
         [0.00, 0.0, 0.0, 0.00, 0.00, 0.25, True, False, False, True, 5.0],
         [0.00, 0.0, 0.0, 0.00, 0.00, 0.25, True, True, True, True, 2.0],
         [0.00, 0.0, 0.0, 0.00, 0.00, 0.25, False, True, True, False, 1.0]]
        self.uiVars.append_ptrn('default', pattern)
        self.uiVars.append_ptrn('own-ptrn', PATTusr)
        self.app = make_app(self.uiVars)

    def run(self):
        """ run the Webserver """
        try:
            self.app.run_server(host='0.0.0.0', port=5000, debug=True)
        finally:
            print('\n--caught exception! in Webserver Thread--\n')
            print("Unexpected error:\n", sys.exc_info()[0])
            print(sys.exc_info()[1])
            traceback.print_tb(sys.exc_info()[2])
            print('\nBreaking the communication loop ...')

            print('Exit the communication Thread ...')
            self.cargo.state = 'EXIT'

        print('Webserver Thread is done ...')

    def get_tasks(self):
        data_in_raw = self.connection.recv(4096)
        data_in_list = pickler.unpickle_data(data_in_raw)

        for data_in in data_in_list:
            if 'update' in data_in:
                self.send_back([self.cargo.rec, self.cargo.rec_u,
                                self.cargo.rec_r])

            if 'valve_meta_info' in data_in:
                valve_data = []
                for valve in self.cargo.valve:
                    valve_data.append(valve.name)
                PID_gains = []
                for c in self.cargo.controller:
                    PID_gains.append([c.Kp, c.Ti, c.Td])
                self.send_back([valve_data,
                                self.cargo.maxpressure,
                                self.cargo.maxctrout,
                                self.cargo.sampling_time,
                                PID_gains,
                                self.cargo.wcomm.pattern])

            if 'dvalve_meta_info' in data_in:
                dvalve_data = []
                for dvalve in self.cargo.dvalve:
                    dvalve_data.append(dvalve.name)
                self.send_back(dvalve_data)

            if 'change_state' in data_in:
                candidates = ['PAUSE', 'REFERENCE_TRACKING', 'EXIT',
                              'USER_CONTROL', 'USER_REFERENCE']
                new_state = None
                for candidate in candidates:
                    if candidate in data_in:
                        new_state = candidate
                        print('recieved task to change state to:', new_state)
                if new_state:
                    self.cargo.state = new_state
                    while not self.cargo.actual_state == new_state:
                        time.sleep(self.cargo.sampling_time)
                self.send_back(new_state)

            if 'set_valve' in data_in:
                valve_data = data_in[1]
                for key in valve_data:
                    self.cargo.pwm_task[key] = valve_data[key]

            if 'set_ref' in data_in:
                ref_data = data_in[1]
                for key in ref_data:
                    self.cargo.ref_task[key] = ref_data[key]

            if 'set_dvalve' in data_in:
                dvalve_data = data_in[1]
                for key in dvalve_data:
                    self.cargo.dvalve_task[key] = dvalve_data[key]

            if 'set_pidgain' in data_in:
                idx = data_in[1]
                gain_data = data_in[2]
                if isinstance(self.cargo.controller[idx],
                              ctrlib.PidController):
                    self.cargo.controller[idx].set_gain(gain_data)
                else:
                    raise NotImplementedError(
                        "Controller", self.cargo.controller[idx],
                        "doesn't support gain setting at runtime")
                c = self.cargo.controller[idx]
                gain = [c.Kp, c.Ti, c.Td]
                self.send_back(gain)

            if 'set_maxpressure' in data_in:
                maxpressure = data_in[1]
                if 10 > maxpressure > 0:
                    self.cargo.maxpressure = maxpressure
                    for sensor in self.cargo.sens:
                        sensor.set_maxpressure(maxpressure)
                self.send_back(self.cargo.maxpressure)

            if 'set_maxctrout' in data_in:
                maxctrout = data_in[1]
                if 1. > maxctrout > 0.:
                    self.cargo.maxctrout = maxctrout
                    for ctr in self.cargo.controller:
                        ctr.set_maxoutput(maxctrout)
                self.send_back(self.cargo.maxctrout)

            if 'set_tsampling' in data_in:
                tsampling = data_in[1]
                if 1. > tsampling > 0.:
                    self.cargo.sampling_time = tsampling
                self.send_back(self.cargo.sampling_time)

            if 'set_pattern' in data_in:
                pattern = data_in[1]
                self.cargo.wcomm.pattern = pattern
                self.send_back(self.cargo.wcomm.pattern)

            if 'set_walking' in data_in:
                state = data_in[1]
                self.cargo.wcomm.confirm = state
                self.send_back(self.cargo.wcomm.confirm)


def flat_list(l):
    return [item for sublist in l for item in sublist]


# -----------------------------------------------------------------------------
# Initialize
# -----------------------------------------------------------------------------

class UI_Vars(object):
    def __init__(self):
        self.n_sliders = 6
        self.n_btns = 4
        self.max_len = 10
        self.ptrnctr_dic = {}
        self.pwm_values = {
            str(i): deque([0]*self.max_len, maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.ref_values = {
            str(i): deque([0]*self.max_len, maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.mes_values = {
            str(i): deque([0]*self.max_len, maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.timestamp = {
            str(i): deque(range(self.max_len), maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.timestamp['start'] = time.time()
        self.ref_timestamp = {
            str(i): deque(range(self.max_len), maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.ref_timestamp['start'] = time.time()
        self.mes_timestamp = {
            str(i): deque(range(self.max_len), maxlen=self.max_len)
            for i in range(self.n_sliders)}
        self.ref_timestamp['start'] = time.time()
        self.d_ref_values = {
            str(i): 0 for i in range(self.n_btns)}
        self.minus_clicks = {
                str(i): 0 for i in range(self.n_sliders)}
        self.plus_clicks = {
                str(i): 0 for i in range(self.n_sliders)}
        self.minus_clicks_ref = {
                str(i): 0 for i in range(self.n_sliders)}
        self.plus_clicks_ref = {
                str(i): 0 for i in range(self.n_sliders)}

    def append_ptrn(self, key, data):
        self.ptrnctr_dic[key] = self.generate_ptrn_dict(data)

    def get_ptrn_keys(self):
        return sorted(self.ptrnctr_dic[self.ptrnctr_dic.keys()[0]].iterkeys())

    def get_ptrn_dic(self, key):
        return self.ptrnctr_dic[key]

    def get_ptrn_data(self, key):
        return self.generate_pattern(**self.ptrnctr_dic[key])

    def append_pwm(self, idx, pwm):
        self.pwm_values[str(idx)].append(pwm)
        self.timestamp[str(idx)].append(time.time()-self.timestamp['start'])

    def append_mes(self, idx, mes):
        self.mes_values[str(idx)].append(mes)
        self.mes_timestamp[str(idx)].append(
            time.time()-self.mes_timestamp['start'])

    def append_ref(self, idx, ref):
        self.ref_values[str(idx)].append(ref)
        self.ref_timestamp[str(idx)].append(
            time.time()-self.ref_timestamp['start'])

    def set_d_ref(self, idx, dref):
        self.d_ref_values[idx] = dref

    def get_pwm(self, idx):
        idx = str(idx)
        return (list(self.pwm_values[idx]), list(self.timestamp[idx]))

    def get_ref(self, idx):
        idx = str(idx)
        return (list(self.ref_values[idx]), list(self.ref_timestamp[idx]))

    def get_mes(self, idx):
        idx = str(idx)
        return (list(self.mes_values[idx]), list(self.mes_timestamp[idx]))

    def get_dref(self, idx):
        return self.d_ref_values[idx]

    def generate_ptrn_dict(self, data):
        return {
            'ptrn_t_move': data[0][-1],
            'ptrn_t_fix': data[1][-1],
            'ptrn_t_defix': data[2][-1],
            'ptrn_p_0': data[3][0],
            'ptrn_p_01': data[0][0],
            'ptrn_p_1': data[0][1],
            'ptrn_p_11': data[3][1],
            'ptrn_p_2': data[0][2],
            'ptrn_p_21': data[3][2],
            'ptrn_p_3': data[3][3],
            'ptrn_p_31': data[0][3],
            'ptrn_p_4': data[3][4],
            'ptrn_p_41': data[0][4],
            'ptrn_p_5': data[0][5],
            'ptrn_p_51': data[3][5]}

    def generate_pattern(self, ptrn_t_move, ptrn_t_fix, ptrn_t_defix, ptrn_p_0,
                         ptrn_p_01, ptrn_p_1, ptrn_p_11, ptrn_p_2, ptrn_p_21,
                         ptrn_p_3, ptrn_p_31, ptrn_p_4, ptrn_p_41, ptrn_p_5,
                         ptrn_p_51):
        data = [
            [ptrn_p_01, ptrn_p_1, ptrn_p_2, ptrn_p_31, ptrn_p_41, ptrn_p_5,
             False, True, True, False, ptrn_t_move],
            [ptrn_p_01, ptrn_p_1, ptrn_p_2, ptrn_p_31, ptrn_p_41, ptrn_p_5,
             True, True, True, True, ptrn_t_fix],
            [ptrn_p_01, ptrn_p_1, ptrn_p_2, ptrn_p_31, ptrn_p_41, ptrn_p_5,
             True, False, False, True, ptrn_t_defix],
            [ptrn_p_0, ptrn_p_11, ptrn_p_21, ptrn_p_3, ptrn_p_4, ptrn_p_51,
             True, False, False, True, ptrn_t_move],
            [ptrn_p_0, ptrn_p_11, ptrn_p_21, ptrn_p_3, ptrn_p_4, ptrn_p_51,
             True, True, True, True, ptrn_t_fix],
            [ptrn_p_0, ptrn_p_11, ptrn_p_21, ptrn_p_3, ptrn_p_4, ptrn_p_51,
             False, True, True, False, ptrn_t_defix]]
        return data


def make_app(uiVars):

    app = dash.Dash()
    app.scripts.config.serve_locally = True
    app.config['suppress_callback_exceptions'] = True

    # -------------------------------------------------------------------------
    # CSS Stylesheets
    # -------------------------------------------------------------------------

    # Add a static image route that serves images from desktop
    # Be *very* careful here - you don't want to serve arbitrary files
    # from your computer or server
    css_directory = os.getcwd()
    stylesheets = ['style.css']
    static_css_route = '/static/'

    @app.server.route('{}<stylesheet>'.format(static_css_route))
    def serve_stylesheet(stylesheet):
        if stylesheet not in stylesheets:
            raise Exception(
                '"{}" is excluded from the allowed static files'.format(
                    stylesheet
                )
            )
        return flask.send_from_directory(css_directory, stylesheet)

    for stylesheet in stylesheets:
        app.css.append_css({"external_url": "/static/{}".format(stylesheet)})

    # app.css.append_css({
    #    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
    # })

    # -------------------------------------------------------------------------
    # PWM CONTROL - Html layout
    # -------------------------------------------------------------------------

    lbls = [[html.Label('0', id='ref-label-{}'.format(i))
             ] for i in range(uiVars.n_sliders)]

    btns = [[
            html.Button(id='-ref-btn-{}'.format(i), children='-'),
            html.Button(id='+ref-btn-{}'.format(i), children='+')
            ] for i in range(uiVars.n_sliders)]

    sldrs = [[
            dcc.Slider(id='ref-slider-{}'.format(i),
                       min=0,
                       max=100,
                       value=0,
                       marks={str(j): str(j) for j in range(0, 101, 10)}
                       )
            ] for i in range(uiVars.n_sliders)]

    sliders = flat_list(
                [[html.Div([
                    html.Div(lbls[i], className="one column"),
                    html.Div(btns[i], className="four columns"),
                    html.Div(sldrs[i], className="seven columns"),
                    ], className="row")
                  ] for i in range(uiVars.n_sliders)])

    dlbls = [[html.Button(children='F{}'.format(i),
                          id='d-ref-btn-{}'.format(i))
              ] for i in range(uiVars.n_btns)]

    dsldrs = [[dcc.Slider(id='d-ref-slider-{}'.format(i),
                          min=0,
                          max=1,
                          value=0,
                          marks={j: str(bool(j)) for j in range(2)}
                          )
               ] for i in range(uiVars.n_btns)]

    dsliders = flat_list(
                [[html.Div([
                    html.Div(dlbls[i], className="six columns"),
                    html.Div(dsldrs[i], className="six columns")
                    ], className="row")
                  ] for i in range(uiVars.n_btns)])

    refctr = html.Div([
            html.H1('Pressure Control'),
            html.Div([
                html.Div(sliders, className='eight columns'),
                html.Div(dsliders, className='three columns')
            ], className='row')
        ])

    # -------------------------------------------------------------------------
    # PWM CONTROL - Html layout
    # -------------------------------------------------------------------------
    lbls = [[html.Label('0', id='pwm-label-{}'.format(i))
             ] for i in range(uiVars.n_sliders)]

    btns = [[
            html.Button(id='--btn-{}'.format(i), children='-'),
            html.Button(id='+-btn-{}'.format(i), children='+')
            ] for i in range(uiVars.n_sliders)]

    sldrs = [[
            dcc.Slider(id='pwm-slider-{}'.format(i),
                       min=0,
                       max=100,
                       value=0,
                       marks={str(j): str(j) for j in range(0, 101, 10)}
                       )
            ] for i in range(uiVars.n_sliders)]

    sliders = flat_list(
                [[html.Div([
                    html.Div(lbls[i], className="one column"),
                    html.Div(btns[i], className="four columns"),
                    html.Div(sldrs[i], className="seven columns"),
                    ], className="row")
                  ] for i in range(uiVars.n_sliders)])

    dlbls = [[html.Button(children='F{}'.format(i), id='d-btn-{}'.format(i))
              ] for i in range(uiVars.n_btns)]

    dsldrs = [[dcc.Slider(id='d-slider-{}'.format(i),
                          min=0,
                          max=1,
                          value=0,
                          marks={j: str(bool(j)) for j in range(2)}
                          )
               ] for i in range(uiVars.n_btns)]

    dsliders = flat_list(
                [[html.Div([
                    html.Div(dlbls[i], className="six columns"),
                    html.Div(dsldrs[i], className="six columns")
                    ], className="row")
                  ] for i in range(uiVars.n_btns)])

    pwmctr = html.Div([
            html.H1('PWM Control'),
            html.Div([
                html.Div(sliders, className='eight columns'),
                html.Div(dsliders, className='three columns')
            ], className='row')
        ])

    # -------------------------------------------------------------------------
    # Pattern CONTROL - Html tab Layout
    # -------------------------------------------------------------------------

    ptrn_inputs_t = [
        ['{}{} :'.format(key.split('_')[1], key.split('_')[2][:3]),
         dcc.Input(id=key, type='number', min=0,
                   max=100 if key.split('_')[1] == 'p' else 1000,
                   value=uiVars.get_ptrn_dic('own-ptrn')[key]*100,
                   style={'width': 65})]
        for key in uiVars.get_ptrn_keys()]
    ptrn_inputs = [html.Div([
            html.Div(item[0], className='five columns'),
            html.Div(item[1], className='seven columns')
        ], className='row') for item in ptrn_inputs_t]

    pttrnctr = html.Div([
        html.H1('Walking'),
        html.Div(dcc.Dropdown(
            id='ptrn-dropdown',
            options=[{'label': key, 'value': key}
                     for key in uiVars.ptrnctr_dic],
            value=uiVars.ptrnctr_dic.keys()[0]
            ), className='row'),
        html.Div([html.Button(id='ptrn-start', children='Start'),
                  html.Button(id='ptrn-stop', children='Stop')
                  ], className='row'),
        html.Div([
            html.Div(id='ptrn-scope', className='eight columns'),
            html.Div([
                html.Div([
                    html.Div(
                        ptrn_inputs[:8], className='six columns'),
                    html.Div(flat_list([
                        ptrn_inputs[8:],
                        [html.Div([
                            html.Button(id='ptrn-submit-btn',
                                        children='Submit')
                            ], className='row')]
                    ]), className='six columns'),
                ], className='row')
            ], className='four columns')
        ], className='row')
    ])

    # -------------------------------------------------------------------------
    # Pressure CONTROL - Html Tab Layout
    # -------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    # Overall - Html Layout
    # -----------------------------------------------------------------------------

    app.layout = html.Div(flat_list([
        [html.Div([
            html.Div(dcc.Graph(id='pressure-ref-graph', animate=True),
                     className="six columns"),
            html.Div(dcc.Graph(id='live-graph', animate=True),
                     className="six columns")
            ], className='row'),
         dcc.Interval(id='graph-update', interval=1000)],
        [dcc.Tabs(
            tabs=[
                {'label': i[1], 'value': i[0]} for i in
                [('PAUSE', 'Pause'),
                 ('REFERENCE_TRACKING', 'Walking'),
                 ('USER_CONTROL', 'PWM Ctr'),
                 ('USER_REFERENCE', 'Prsr Ctr'),
                 ('EXIT', 'Quit')]
            ],
            value='PAUSE',
            id='tabs'),
         html.Div(id='tab-output')]
    ]), style={
        'width': '90%',
        'fontFamily': 'Sans-Serif',
        'margin-left': 'auto',
        'margin-right': 'auto'
    })

    # -------------------------------------------------------------------------
    # Callbacks - Tabs Content
    # -------------------------------------------------------------------------

    @app.callback(Output('tab-output', 'children'), [Input('tabs', 'value')])
    def display_content(value):
        if value == 'REFERENCE_TRACKING':
            return pttrnctr
        elif value == 'USER_CONTROL':
            return pwmctr
        elif value == 'USER_REFERENCE':
            return refctr
        elif value == 'PAUSE':
            return html.H1('PAUSE')
        elif value == 'EXIT':
            return 'Not Implemented'
        else:
            return 'Not Implemented'

    # -------------------------------------------------------------------------
    # Callbacks - PWM CTR
    # -------------------------------------------------------------------------

    for i in range(uiVars.n_sliders):
        @app.callback(Output('pwm-label-{}'.format(i), 'children'),
                      [Input('pwm-slider-{}'.format(i), 'value')])
        def slider_callback(val, idx=i):
            if uiVars.get_pwm(idx)[0][-1] != val:
                uiVars.append_pwm(idx, val)
            return str(val)

        @app.callback(Output('pwm-slider-{}'.format(i), 'value'),
                      [Input('--btn-{}'.format(i), 'n_clicks'),
                       Input('+-btn-{}'.format(i), 'n_clicks')])
        def slider_update(minus, plus, idx=i):
            val = uiVars.get_pwm(idx)[0][-1]
            if minus > uiVars.minus_clicks[str(idx)]:
                uiVars.minus_clicks[str(idx)] += 1
                if val - 1 >= 0:
                    val -= 1
            if plus > uiVars.plus_clicks[str(idx)]:
                uiVars.plus_clicks[str(idx)] += 1
                if val + 1 <= 100:
                    val += 1
            return val

    for i in range(uiVars.n_btns):
        @app.callback(Output('d-slider-{}'.format(i), 'value'),
                      [Input('d-btn-{}'.format(i), 'n_clicks')])
        def d_btn_callback(event, idx=i):
            if event:
                state = event % 2
            else:
                state = 0
            uiVars.set_d_ref(idx, state)
            return state

    # -------------------------------------------------------------------------
    # Callbacks - REF CTR
    # -------------------------------------------------------------------------

    for i in range(uiVars.n_sliders):
        @app.callback(Output('ref-label-{}'.format(i), 'children'),
                      [Input('ref-slider-{}'.format(i), 'value')])
        def ref_slider_callback(val, idx=i):
            if uiVars.get_ref(idx)[0][-1] != val:
                uiVars.append_ref(idx, val)
            return str(val)

        @app.callback(Output('ref-slider-{}'.format(i), 'value'),
                      [Input('-ref-btn-{}'.format(i), 'n_clicks'),
                       Input('+ref-btn-{}'.format(i), 'n_clicks')])
        def ref_slider_update(minus, plus, idx=i):
            val = uiVars.get_ref(idx)[0][-1]
            if minus > uiVars.minus_clicks_ref[str(idx)]:
                uiVars.minus_clicks_ref[str(idx)] += 1
                if val - 1 >= 0:
                    val -= 1
            if plus > uiVars.plus_clicks_ref[str(idx)]:
                uiVars.plus_clicks_ref[str(idx)] += 1
                if val + 1 <= 100:
                    val += 1
            return val

    for i in range(uiVars.n_btns):
        @app.callback(Output('d-ref-slider-{}'.format(i), 'value'),
                      [Input('d-ref-btn-{}'.format(i), 'n_clicks')])
        def d_ref_btn_callback(event, idx=i):
            if event:
                state = event % 2
            else:
                state = 0
            uiVars.set_d_ref(idx, state)
            return state
    # -------------------------------------------------------------------------
    # Callbacks - Ptrn
    # -------------------------------------------------------------------------

    @app.callback(Output('ptrn-scope', 'children'),
                  inputs=[Input('ptrn-dropdown', 'value'),
                          Input('ptrn-submit-btn', 'n_clicks')],
                  state=[State(key, 'value')
                         for key in uiVars.get_ptrn_keys()])
    def update_ptrn_graph(dropdown_val, submit, *args):
        global ptrnctr_dic
        if dropdown_val == 'own-ptrn':
            uiVars.ptrnctr_dic['own-ptrn'] = {
                key: min(abs(float(args[idx])), 100)*.01
                if key.split('_')[1] == 'p' else abs(float(args[idx]))*.01
                for idx, key in enumerate(uiVars.get_ptrn_keys())}
        traces = []
        ptrn = uiVars.get_ptrn_data(dropdown_val)

        for key in uiVars.pwm_values:
            y = [p[int(key)] for p in ptrn]
            t_m, t_a, t_d = (uiVars.ptrnctr_dic[dropdown_val]['ptrn_t_move'],
                             uiVars.ptrnctr_dic[dropdown_val]['ptrn_t_fix'],
                             uiVars.ptrnctr_dic[dropdown_val]['ptrn_t_defix'])
            x = [0, t_m, t_m+t_a, t_m+t_a+t_d, 2*t_m+t_a+t_d, 2*t_m+2*t_a+t_d]
            data = go.Scatter(
                x=x,
                y=y,
                name=key,
                mode='lines+markers')
            traces.append(data)

        ptrn_lbls_t = [
            ['{}{} : '.format(key.split('_')[1], key.split('_')[2]),
             html.Label(children=uiVars.ptrnctr_dic[dropdown_val][key])]
            for key in uiVars.get_ptrn_keys()]
        ptrn_lbls = [html.Div([
                html.Div(item[0], className='six columns'),
                html.Div(item[1], className='six columns')
                ], className='row') for item in ptrn_lbls_t]

        figure = {
                'data': traces,
                'layout': go.Layout(
                    xaxis={'range': [0, 2*t_m+2*t_a+t_d]},
                    yaxis={'range': [0, 1]},
                    margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                    height=300
                    )
            }
        return [html.Div(ptrn_lbls, className='three columns'),
                html.Div([
                    html.Div([
                        dcc.Graph(id='ptrn-graph',
                                  figure=figure, config={'staticPlot': True})
                        ], className='nine columns')
                    ])]

    # -------------------------------------------------------------------------
    # Callbacks - Main
    # -------------------------------------------------------------------------
    @app.callback(Output('live-graph', 'figure'),
                  events=[Event('graph-update', 'interval')])
    def update_graph():
        traces = []
        minis = []
        maxis = []
        for key in uiVars.pwm_values:
            y, x = uiVars.get_pwm(key)
            minis.append(min(x))
            maxis.append(max(x))
            data = go.Scatter(
                x=x,
                y=y,
                name='PWM {}'.format(key),
                mode='lines+markers')
            traces.append(data)
        return {
            'data': traces,
            'layout': go.Layout(
                xaxis={'range': [min(minis), max(maxis)]},
                yaxis={'range': [0, 100]},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10}
            )
        }

    @app.callback(Output('pressure-ref-graph', 'figure'),
                  events=[Event('graph-update', 'interval')])
    def update_ref_graph():
        traces = []
        minis = []
        maxis = []
        for key in uiVars.ref_values:
            y, x = uiVars.get_ref(key)
            minis.append(min(x))
            maxis.append(max(x))
            data = go.Scatter(
                x=x,
                y=y,
                name='Ref {}'.format(key),
                mode='lines+markers')
            traces.append(data)
        for key in uiVars.mes_values:
            y, x = uiVars.get_mes(key)
            minis.append(min(x))
            maxis.append(max(x))
            data = go.Scatter(
                x=x,
                y=y,
                name='Mes {}'.format(key),
                mode='lines+markers')
            traces.append(data)
        return {
            'data': traces,
            'layout': go.Layout(
                xaxis={'range': [min(minis), max(maxis)]},
                yaxis={'range': [0, 100]},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10}
            )
        }
    return app
