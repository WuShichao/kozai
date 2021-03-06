#! /usr/bin/env python

'''
kl_period

Calculate the period of a hierarchical triple, either semi-analytically or
by numerically integrating the triple.
'''

# System modules
import json
import time

# Numerical modules
from math import sqrt, cos
import numpy as np
from scipy.integrate import quad

# Other modules from this package
from _kozai_constants import *

def P_out(triple):
  '''Return the outer period of a hierarchical triple in years.'''
  return np.sqrt(triple.a2**3 / (triple.m1 + triple.m2 + triple.m3))

def P_in(triple):
  '''Return the inner period of a hierarchical triple in years.'''
  return np.sqrt(triple.a1**3 / (triple.m1 + triple.m2))

def kl_period_oom(triple):
  '''The usual KL period formula:

  t_KL = P_out^2 / P_in * (1 - e2^2)^(3/2)

  Parameters:
    triple: A Triple object

  Returns:
    P: The period of KL oscillations in years.
  '''

  return (8 / (15 * np.pi) * (1 + triple.m1 / triple.m3) * P_out(triple)**2 
    / P_in(triple) * (1 - triple.e2**2)**(3./2))

def is_librating(triple):
  '''Determine whether the triple is librating or rotating.

  Parameters:
    triple: A Triple object

  Returns:
    True if librating, False if rotating.
  '''

  if triple.CKL > 0:
    return False
  else:
    return True

def depsdh(eps, H, Th):
  '''The derivative of epsilon with respect to H.'''

  return (eps**2 / ((1-eps**2) * (eps**2 - Th) * sqrt(1 - (3*eps**4 +
    eps**2 * (H - 9 * Th - 5) + 15*Th)**2 / (225 * (1-eps**2)**2 * (eps**2 -
    Th)**2))))

def kl_period_norm(Hhat, Th):
  zeta = 20 - Hhat + 24 * Th
  epsmin = 1/6. * sqrt(zeta - sqrt(zeta**2 - 2160 * Th))

  # Check whether the triple is librating or rotating
  if Hhat + 6 * Th - 2 > 0:
    epsmax = 1/6. * sqrt(zeta + sqrt(zeta**2 - 2160 * Th))
  else:
    epsmax = sqrt((Hhat + 6 * Th + 10) / 12.)

  return quad(depsdh, epsmin, epsmax, args=(Hhat, Th), epsabs=1e-13, epsrel=1e-13)[0]

def kl_period(triple):
  '''Calculate the period of KL oscillations semi-analytically.

  Parameters:
    triple: A Triple object

  Returns:
    P: The period in years
  '''

  L1toC2 = (16 * triple.a2 * (1 - triple.e2**2)**(3/2.) / triple.m3 *
    (triple.a2 / triple.a1)**2 * sqrt(triple.m1 * triple.a1) / (2 * np.pi))

  return L1toC2 * kl_period_norm(triple.Hhatquad, triple.Th) / 15

def numeric_kl_period(triple, nperiods=3, tstop=1e6):
  '''Calculate the period of KL oscillations by explicitly integrating the
  secular equations of motion.

  Input:
    triple: A triple class
    n_periods: (optional) The number of KL cycles over which to integrate

  Output:
    The average period of KL oscillations in yr.
  '''

  triple.tstop = tstop
  triple.integrator_setup()

  e_prev2 = 0.
  e_prev  = 0.

  periods = []
  emin_tstart = 0
  emax_tstart = 0

  cpu_starttime = time.time()

  while time.time() - cpu_starttime < triple.cputstop:
    triple._step()

    if len(periods) == 2 * nperiods:
      break
    if e_prev2 < e_prev > triple.e1:
      if emax_tstart > 0:
        periods.append(triple.t - emax_tstart)
      emax_tstart = triple.t
    elif e_prev2 > e_prev < triple.e1:
      if emin_tstart > 0:
        periods.append(triple.t - emin_tstart)
      emin_tstart = triple.t

    e_prev2 = e_prev
    e_prev = triple.e1
  
  return np.mean(periods)
