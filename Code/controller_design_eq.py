# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 20:01:28 2017

@author: ls
"""

from sympy import symbols
import sympy as sym
from sympy import init_printing

init_printing()

z, Kp, Ti, Td, gam, Ts, a0, a1, a2, b0, b1, b2 = \
    symbols('z Kp Ti Td gam Ts a0 a1 a2 b0 b1 b2')

y0, y1, y2, e0, e1, e2 = symbols('y0 y1 y2 e0 e1 e2')

s = 2/Ts*(z-1)/(z+1)


C = Kp*(1 + 1/(Ti*s) + (Td*s)/(1+gam*Td*s))
C = sym.simplify(C)

C1 = Kp*((2*Ti/Ts*(z-1)+z+1)*(z+1+gam*2*Td/Ts*(z-1))+2*Td/Ts*(z-1)*2*Ti/Ts*(z-1)) / \
    (2*Ti/Ts*(z-1)*(z+1+gam*2*Td/Ts*(z-1)))

print('\n\nSymbolic Calculated Controller')
sym.pretty_print(sym.simplify(C))

print('\n\nRearrange s.t. powers of z are visible')
C = sym.cancel(C, z)
sym.pretty_print(C)

print('\n\nExtract Coefficients of the diffrents powers')
nominator, denominator = sym.fraction(sym.cancel(C, z))

print('\nNominator:')
sym.pretty_print(sym.collect(nominator, z))
b = []
nominator = sym.collect(nominator, z)
for i in range(3):
    b.append(nominator.coeff(z, 2-i))
    print('\nCoeff b['+str(i)+']:')
    sym.pretty_print(b[i])


print('\nDenominator:')
sym.pretty_print(denominator)
a = []
denominator = sym.collect(denominator, z)
for i in range(3):
    a.append(denominator.coeff(z, 2-i))
    print('\nCoeff a['+str(i)+']:')
    sym.pretty_print(a[i])


print('\n\nSubstitue Coefficients:')
C = C.subs(b[0], b0)
C = C.subs(b[1], b1)
C = C.subs(b[2], b2)
C = C.subs(a[0], a0)
C = C.subs(a[1], a1)
C = C.subs(a[2], a2)
sym.pretty_print(C)


print('\n\nCalculate real Values:')
Kp_real = .6
Ti_real = .5
Td_real = .33
gam_real = .1
Ts_real = 0.01

k0 = a[2]/a[0]
k1 = a[1]/a[0]
k2 = b[2]/a[0]
k3 = b[1]/a[0]
k4 = b[0]/a[0]

print('\nk0=')
sym.pretty_print(k0)
print(k0)
print('\nk1=')
sym.pretty_print(k1)
print(k1)
print('\nk2=')
sym.pretty_print(k2)
print(k2)
print('\nk3=')
sym.pretty_print(k3)
print(k3)
print('\nk4=')
sym.pretty_print(k4)
print(k4)


k0 = k0.subs(Kp, Kp_real)
k0 = k0.subs(Ti, Ti_real)
k0 = k0.subs(Td, Td_real)
k0 = k0.subs(Ts, Ts_real)
k0 = k0.subs(gam, gam_real)

k1 = k1.subs(Kp, Kp_real)
k1 = k1.subs(Ti, Ti_real)
k1 = k1.subs(Td, Td_real)
k1 = k1.subs(Ts, Ts_real)
k1 = k1.subs(gam, gam_real)

k2 = k2.subs(Kp, Kp_real)
k2 = k2.subs(Ti, Ti_real)
k2 = k2.subs(Td, Td_real)
k2 = k2.subs(Ts, Ts_real)
k2 = k2.subs(gam, gam_real)

k3 = k3.subs(Kp, Kp_real)
k3 = k3.subs(Ti, Ti_real)
k3 = k3.subs(Td, Td_real)
k3 = k3.subs(Ts, Ts_real)
k3 = k3.subs(gam, gam_real)

k4 = k4.subs(Kp, Kp_real)
k4 = k4.subs(Ti, Ti_real)
k4 = k4.subs(Td, Td_real)
k4 = k4.subs(Ts, Ts_real)
k4 = k4.subs(gam, gam_real)

y = -k0*y2 - k1*y1 + k2*e2 + k3*e1 + k4*e0
sym.pretty_print(y)


