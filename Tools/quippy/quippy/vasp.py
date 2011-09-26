# HQ XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# HQ X
# HQ X   quippy: Python interface to QUIP atomistic simulation library
# HQ X
# HQ X   Copyright James Kermode 2010
# HQ X
# HQ X   These portions of the source code are released under the GNU General
# HQ X   Public License, version 2, http://www.gnu.org/copyleft/gpl.html
# HQ X
# HQ X   If you would like to license the source code under different terms,
# HQ X   please contact James Kermode, james.kermode@gmail.com
# HQ X
# HQ X   When using this software, please cite the following reference:
# HQ X
# HQ X   http://www.jrkermode.co.uk/quippy
# HQ X
# HQ XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

from quippy.atoms import Atoms, atoms_reader, AtomsReaders, AtomsWriters
from quippy.farray import fzeros,frange
from StringIO import StringIO
import sys, string, os, operator, itertools, logging, glob, re

import numpy as np
import time, os, itertools, sys
import re

@atoms_reader('vasp')
@atoms_reader('POSCAR')
def VASPReader(poscar, outcar=None, species=None):
   """Read a configuration from a VASP POSCAR file.

   Following POSCAR, optionally also read a trajectory from an OUTCAR file."""
   
   p = open(poscar, 'r')
   comment = p.readline().rstrip()
   l = p.readline().strip(); lc_factor=np.real(l)
   l = p.readline().strip(); a1 = np.real(l.split())
   l = p.readline().strip(); a2 = np.real(l.split())
   l = p.readline().strip(); a3 = np.real(l.split())
   l = p.readline().strip(); at_species = l.split()
   try:
      ns = [ int(n) for n in at_species ]
      no_species = True
   except:
      no_species = False

   have_species = True
   if (no_species):
      for i in range(len(ns)):
         if (species is not None):
            species_cli = species.split()
            at_species[i] = species_cli[i-1]
         else:
            have_species = False
            at_species[i] = ("%d" % (i+1))
   else:
      l = p.readline().strip();
      ns = [ int(n) for n in l.split() ]

   l=p.readline().strip()
   if (re.compile("^\s*s", re.IGNORECASE).match(l)):
      dyn_type = l
      coord_type = p.readline().strip();
   else:
      coord_type = l

   n=0
   for i in range(len(ns)):
      n += ns[i]

   lat = fzeros( (3,3) )
   lat[:,1] = a1[0:3]
   lat[:,2] = a2[0:3]
   lat[:,3] = a3[0:3]

   at = Atoms(n=n, lattice=lat)
   at.params['VASP_Comment'] = comment

   coord_direct=re.compile("^\s*d", re.IGNORECASE).match(coord_type);

   ii = 1
   for ti in range(len(ns)):
      for i in range(ns[ti]):
         l = p.readline().strip(); pos = np.array(l.split()[0:3], float); 
	 if (coord_direct):
	    at.pos[:,ii] = np.dot(at.lattice[:,:],pos[:])
	 else:
	    at.pos[:,ii] = pos[:]
         at.species[:,ii] = at_species[ti]
         ii += 1

   if (have_species):
      at.set_zs()
   else:
      at.Z[:] = [ int("".join(n)) for n in at.species[:] ]

   yield at

   at_cur = at.copy()
   lat_cur = at_cur.lattice.copy()
   at_i = -1
   lat_i = -1

   if outcar is not None:
      p = open(outcar, 'r')
      for lr in p:
         l=lr.rstrip()
         if (lat_i >= 1 and lat_i <= 3):
            lat_cur[:,lat_i] = [ float(r) for r in l.replace("-"," -").split()[0:3] ]
            lat_i += 1
         if (at_i >= 1 and at_i <= at_cur.n):
            at_cur.pos[:,at_i] = [ float(r) for r in l.replace("-"," -").split()[0:3] ]
            at_i += 1
         if (l.find("TOTAL-FORCE (eV/Angst)") >= 0):
            at_i=1
            p.next()
         if (l.find("direct lattice vectors") >= 0):
            lat_i=1
         if (at_i == at_cur.n):
            at_cur.set_lattice(lat_cur, False)
            for i in frange(at_cur.n):
               dr = at_cur.diff_min_image(i, at.pos[:,i])
               at_cur.pos[:,i] = at.pos[:,i] - dr
            yield at_cur


class VASPWriter(object): 
    def __init__(self, pos=None, species_map={'O':1, 'Si':2}):
	if pos == 'stdout':
		pos = sys.stdout 
	
	self.pos = pos
	self.species_map = species_map

	if isinstance(self.pos, str): self.pos = open(self.pos, 'w')

    def write(self, at):
        self.pos.write('System\n')# % (self.step_name, self.it))

#Lattice
        self.pos.write('%20.10f\n' % 1.0)
        for i in (1,2,3):
            L = at.lattice[:,i].copy()
            self.pos.write('%20.10f%20.10f%20.10f\n' % (L[1], L[2], L[3]))

#Count and print the atomic species sorted according to map_species
        nat = [0]*len(self.species_map.keys())
        sorted_species = [' ']*len(self.species_map.keys())

        for i,key in enumerate(sorted(self.species_map, key=self.species_map.get)):
                sorted_species[i] = key
		nat[i] = ( at.species[:].stripstrings()==key ).count() 
        self.pos.write(' '.join([str(n) for n in nat])+'\n')

        self.pos.write('Selective Dynamics\n')
        self.pos.write('Cartesian\n')

#Positions
        for j in range(len(sorted_species)):
              for i in frange(at.n):
                  if str(at.species[i].stripstrings()) == sorted_species[j] :
                  	p = at.pos[:,i].copy()
                  	self.pos.write('%20.10f%20.10f%20.10f T  T  T\n' % (p[1], p[2], p[3]))


AtomsWriters['vasp'] = VASPWriter
