# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 14:11:47 2017

@author: ls
"""

#Version Check
import sys
if sys.version_info > (3, 0):
    print("Warning! Must be using Python 2")

import control
import matplotlib.pyplot as plt
import numpy as np
from matplotlib2tikz import save as tikz_save
from Src.Controller import controller as ctrlib
from Src.Management import save



"""
Signals #################################################
"""

# Time
ts = 0.01   # [sec] sampling time
T = 6      # [sec] Simulation time

t = [i*ts for i in range(0, int(T/ts))]     # time vector

# Signal
u = [np.sin(time*2*np.pi*2)**2 for time in t]
u[int(T/ts/2):] = [0 for i in u[int(T/ts/2):]]

R = 1.2
r = [R for i in t]
r[int(2*T/ts/4):] = [0 for i in r[int(2*T/ts/4):]]
r[:int(T/ts/3)] = [R*7./10 for i in r[:int(T/ts/3)]]
r[:10] = [0 for i in r[:10]]


"""
System Settings #################################################
"""
# System
# a1 = [.1, 0]
# b1 = [1.]

K0 = 3
a1 = [1., 0]
b1 = [K0]
sys_tf1 = control.tf(b1, a1)
G = sys_tf1
Gss = control.tf2ss(G)
if Gss.isctime():
    Gss = Gss.sample(ts, method='bilinear')


def set_stateG():
    return [[0]]
stateG = set_stateG()

# Controller
Kp = 1.3
Ti = .55
Td = .2
gam = 0.1
Ctr = ctrlib.PidController([Kp, Ti, Td], ts, 1)
Ctr_unlim = ctrlib.PidController([Kp, Ti, Td], ts, 100)
Ctr_lim = ctrlib.PidController_WindUp([Kp, Ti, Td], ts, 1)

Ctr_sympy = ctrlib.PidController_SymPy([Kp, Ti, Td], ts, 1)
# Ti = Kp/Ki
# Td = Kd/Kp

a = [gam*Ti*Td, Ti, 0]
b = [(1+gam)*Kp*Ti*Td, Kp*Ti+gam*Kp*Td, Kp]
C = control.tf(b, a)
Css = control.tf2ss(C)
if Css.isctime():
    Css = Css.sample(ts, method='bilinear')


def set_stateC():
    return [[0], [0]]
stateC = set_stateC()

# Closed Loop
CL = control.feedback(C*G, 1, -1)
CL = (1+G*C)**(-1)*G*C

"""
Test Simulation #################################################
"""
# Test Simulation
tout, yout, _ = control.forced_response(G, t, u)
y_out_ss = [0]
for i in range(len(t)-1):
    # simulate:
    state_next = (Gss.A*stateG + Gss.B*u[i])
    yout_tmp = (Gss.C*state_next + Gss.D*u[i])
    # store
    y_out_ss.append(float(yout_tmp))
    stateG = state_next


#plt.figure()
#plt.title('Test Simulation Result - control tk')
#plt.plot(tout, yout)
#plt.hold(True)
#plt.plot(t, u)
#
#plt.figure()
#plt.title('Test Simulation Result - selfmade')
#plt.plot(t, y_out_ss)
#plt.hold(True)
#plt.plot(t, u)

"""
Real Simulation #################################################
"""

# Simulation of Unlimited system with STD PID
tout_cl, yout_cl, xout_cl = control.forced_response(CL, t, r)
uout_cl = [0]
eout_cl = [0]
yout_cl = [0]
stateC = set_stateC()
stateG = set_stateG()
for i in range(len(t)-1):
    # simulate Controller:
    uout = Ctr_unlim.output(r[i], yout_cl[i])
    # store
    uout_cl.append(float(uout))

    # simulate Plant:
    state_next = (Gss.A*stateG + Gss.B*uout_cl[-1])
    yout = (Gss.C*state_next + Gss.D*uout_cl[-1])
    # store
    yout_cl.append(float(yout))
    stateG = state_next
    eout_cl.append(r[i]-yout_cl[-1])


# Simulation of limited PID
u_ss = [0]
e_ss = [0]
y_ss = [0]
stateC = set_stateC()
stateG = set_stateG()
for i in range(len(t)-1):
    # simulate Controller:
    uout = Ctr_lim.output(r[i], y_ss[i])
    # store
    u_ss.append(float(uout))

    # simulate Plant:
    state_next = (Gss.A*stateG + Gss.B*u_ss[-1])
    yout = (Gss.C*state_next + Gss.D*u_ss[-1])
    # store
    y_ss.append(float(yout))
    stateG = state_next
    e_ss.append(r[i]-y_ss[-1])

# Simulation of Anti-Windup PID
u_ss_2 = [0]
e_ss_2 = [0]
y_ss_2 = [0]
stateG = set_stateG()
for i in range(len(t)-1):
    # simulate Controller:
    uout = Ctr.output(r[i], y_ss_2[i])
    # store
    u_ss_2.append(float(uout))

    # simulate Plant:
    state_next = (Gss.A*stateG + Gss.B*u_ss_2[-1])
    yout = (Gss.C*state_next + Gss.D*u_ss_2[-1])
    # store
    y_ss_2.append(float(yout))
    stateG = state_next
    e_ss_2.append(r[i]-y_ss_2[-1])


# Simulation of SymPy optimized Controller
u_sym = [0]
e_sym = [0]
y_sym = [0]
stateG = set_stateG()
for i in range(len(t)-1):
    # simulate Controller:
    uout = Ctr_sympy.output(r[i], y_sym[i])
    # store
    u_sym.append(float(uout))

    # simulate Plant:
    state_next = (Gss.A*stateG + Gss.B*u_sym[-1])
    yout = (Gss.C*state_next + Gss.D*u_sym[-1])
    # store
    y_sym.append(float(yout))
    stateG = state_next
    e_sym.append(r[i]-y_ss_2[-1])


"""
Plotting #################################################
"""

plt.figure()
plt.title('Simulation Result: Kp:'+str(Kp)+' Ti:'+str(Ti)+' Td:'+str(Td))
ax1 = plt.subplot(211)
# plt.ylabel(str(G))
yout_cl = [i/R for i in yout_cl]
plt.plot(t, yout_cl, 'b--', label='Unlimited')
y_ss = [i/R for i in y_ss]
plt.plot(t, y_ss, 'r-', label='Limited')
y_ss_2 = [i/R for i in y_ss_2]
plt.plot(t, y_ss_2, 'g-', label='AntiWindUp')
# y_sym = [i/R for i in y_sym]
# plt.plot(t, y_sym, 'b-', label='SymPy PID')
r = [i/R for i in r]
plt.plot(t, r, ':', label='Reference')
plt.ylabel('System Output')


# plt.plot(t, uout_cl, 'b:', label='unlimited_sys sim')
# plt.plot(t, u_ss, 'r:', label='std PID')
# plt.plot(t, u_ss_2, 'g:', label='anti_windup PID')

plt.grid()
plt.legend()

plt.subplot(212, sharex=ax1)

plt.plot(t, uout_cl, 'b--', label='Unlimited')
plt.plot(t, u_ss, 'r-', label='Limited')
plt.plot(t, u_ss_2, 'g-', label='AntiWindUp')
# plt.plot(t, u_sym, 'b-', label='SymPy PID')
plt.xlabel('Time [sec]')
plt.ylabel('Controller Output')
plt.ylim(-1.5, 1.5)

plt.legend()
plt.grid()

filename = 'TikZ-Out/Simulation_results.tex'
tikz_save(filename, figureheight='6cm', figurewidth='12cm')
save.insert_tex_header(filename)


# print('Controller BodePlot')
# plt.figure()
# control.bode_plot(C)
# control.bode_plot(G)
# control.bode_plot(CL)

plt.show()
