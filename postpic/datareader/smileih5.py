#
# This file is part of postpic.
#
# postpic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# postpic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with postpic. If not, see <http://www.gnu.org/licenses/>.
#
# Stephan Kuschel, 2023
# Carolin Goll, 2023

from __future__ import absolute_import, division, print_function, unicode_literals

from .openPMDh5 import OpenPMDreader
from . import Simulationreader_ifc
from .. import helper
import os.path
import h5py
import glob
import numpy as np
from .. import helper
from ..helper_fft import fft
import re

__all__ = ['SmileiReader', 'SmileiSeries']


def _generateh5indexfile(indexfile, fnames):
    '''
    Creates a h5 index file called indexfile containing external links to all h5
    datasets which are in in the h5 filelist fnames. This is fast as datasets
    will only be externally linked within the new indexfile.
    Therefore the indexfile will also be small in size.

    Will throw an error, if any of the h5 files contain a dataset under the same name.
    '''
    if os.path.isfile(indexfile):
        # indexfile already exists. do not recreate
        return

    dirname = os.path.dirname(fnames[0])
    indexfile = os.path.join(dirname, indexfile)

    def visitf(key):
        # key is a string
        # only link if key points to a dataset. Do not link groups
        if isinstance(hf[key], h5py._hl.dataset.Dataset):
            ih[key] = h5py.ExternalLink(fname, key)

    with h5py.File(indexfile, 'w') as ih:
        for fname in fnames:
            with h5py.File(fname, 'r') as hf:
                hf.visit(visitf)


def _getindexfile(path):
    '''
    Returns the name of the index file after the file has been
    generated (File generation only if it doesnt exist)
    '''
    indexfile = os.path.join(path, '.postpic-smilei-index.h5')
    if not os.path.isfile(indexfile):
        # find all h5 files
        h5files = glob.glob(os.path.join(path, '*.h5'))
        print('generating index file "{}" from the following'
              'h5 files: {}'.format(indexfile, h5files))
        _generateh5indexfile(indexfile, h5files)
    return indexfile

class SmileiReader(OpenPMDreader):
    '''
    The Smilei reader can read  a single h5 file or combine the information of
    all h5 files in the same directory.
    Use either
    `simreader = SmileiReader('path/to/simulation/fields0.h5', 1000)`,
    where 1000 points to iteration 1000 of the simulation.
    or use
    `simreader = SmileiReader('path/to/simulation/', 1000)`
    to combine all h5 files in this directory.
    Internally the second command will create a new file called
    `.postpic-smilei-index.h5` which contains external links to all
    datasets in this directory.

    Args:
      h5file : String
        A String containing the relative Path to the h5 files of the simulation
        or the path to a single h5 file.
        Hidden files starting with `.` will be ignored.

      iteration : Integer
        An integer indicating the iteration to be loaded. Default is None, leading
        to the first iteration found in the h5file to be loaded.
    '''

    def __init__(self, h5file, iteration=None):
        # The class given to super is the OpenPMDreader class, not the SmileiReader class.
        # This is on purpose to NOT run the `OpenPMDreader.__init__`.
        super(OpenPMDreader, self).__init__(h5file)
        # Smilei uses multiple h5 files and also the iteration encoding differs from openPMD.
        if os.path.isfile(h5file):
            self._h5 = h5py.File(h5file, 'r')
        elif os.path.isdir(h5file):
            indexfile = _getindexfile(h5file)
            self._h5 = h5py.File(indexfile, 'r')
        else:
            raise IOError('"{}" is neither a h5 file nor a directory'
                          'containing h5 files'.format(h5file))

        if iteration is None:
            self._iteration = int(list(self._h5['data'].keys())[0])
        elif iteration not in [int(i) for i in list(self._h5['data'].keys())]:
            raise IOError("Iteration {} is in valid".format(iteration))
        else:
            self._iteration = int(iteration)
        
        self._data = self._h5['/data/{:010d}/'.format(self._iteration)]
        self.attrs = self._data.attrs

    #To return the number of AM modes and Field names in the dump.
    def getAMmodes(self):    
        strings=np.array(self._data)
        mask =  np.array(["_mode_" in s for s in strings])
        arr=strings[mask]
        max_suffix = float('-inf')
        max_suffix_string = None
        prefix_list=[]

        for i in arr:
            prefix, suffix = i.split('_mode_')
            suffix_int = int(suffix)
            if suffix_int > max_suffix:
                max_suffix = suffix_int
                max_suffix_string = i
            prefix_list.append(prefix)

        availModes=[i for i in range(0,int(max_suffix_string[-1])+1)]
        return [prefix_list, int(max_suffix_string[-1])+1, availModes]
    
    @staticmethod
    def _modeexpansion_naiv(rawdata, theta=0, M=None):
        '''
        converts to radial data using `modeexpansion`, possibly for multiple
        theta at once.
        '''
        if np.asarray(theta).shape is ():
            # single theta
            theta = [theta]
        # multiple theta
        #data = np.asarray([SmileiReader._modeexpansion_naiv_single(rawdata, theta=t)
        #                   for t in theta])
        # switch from (theta, r, z) to (r, theta, z)
        
        Nt=len(theta)
        (Nm, Nr, Nx) = rawdata.shape
        F_total = np.zeros((Nt,Nr,Nx))                       
        mode =[m for m in range(0,Nm)]

        if M is not None:
            if Nm ==1 and M not in SmileiReader.getAMmodes[-1]:
                raise IOError('Mode {} not available in dump'.format(M))

        for t in theta:
            index=theta.index(t)
            if M is None:
                for m in mode:
                    F_total[index] += np.real(rawdata[m])*np.cos(m*t)+np.imag(rawdata[m])*np.sin(m*t)
            else:
                F_total[index] += np.real(rawdata[0])*np.cos(M*t)+np.imag(rawdata[0])*np.sin(M*t)
        #F_total = F_total.swapaxes(0, 1)
        return F_total
    
    def getComplex(self, key,theta=0):
        
        array_list=[]
        modes=self.getAMmodes()[-1]
        for mode in modes:

            field_name = key+"_mode_"+str(mode)
            field_array = np.array(self._data[field_name])*(self._data[field_name].attrs['unitSI'])
            field_array_shape = field_array.shape
            reshaped_array = field_array.reshape(field_array_shape[0], field_array_shape[1]//2, 2)
            complex_array = reshaped_array[:, :, 0] + 1j * reshaped_array[:, :, 1]
            array_list.append(complex_array)
        
        mod_complex_data= np.stack(array_list,axis=0)                    #Modified array of shape (Nmodes, Nx, Nr)
        #mod_complex_data = np.transpose(mod_complex_data, (0, 2, 1))     #Modified array of shape (Nmodes, Nr, Nx)
        return SmileiReader._modeexpansion_naiv(rawdata=mod_complex_data,theta=theta)
    
    def data(self, key, **kwargs):
        '''
        should work with any key, that contains data, thus on every hdf5.Dataset,
        but not on hdf5.Group. Will extract the data, convert it to SI and return it
        as a numpy array. Constant records will be detected and converted to
        a numpy array containing a single value only.
        '''
        field_pattern=re.compile(r'^{}.*_mode_'.format(key))
        match = [True if re.match(field_pattern, s) else False for s in list(self._data)]

        if True in match:
            return self.getComplex(key=key, **kwargs)
        else:
            record = self._data[key]
        
        if "value" in record.attrs:
            # constant data (a single int or float)
            ret = np.float64(record.attrs['value']) * record.attrs['unitSI']
        else:
            # array data
            ret = np.float64(record[()]) * record.attrs['unitSI']
        return ret
        
    def _keyE(self, component, **kwargs):
        # Smilei deviates from openPMD standard: Ex instead of E/x
        axsuffix = {0: 'x', 1: 'y', 2: 'z', 90: 'r', 91: 't'}[helper.axesidentify[component]]
        return 'E{}'.format(axsuffix)

    def _keyB(self, component, **kwargs):
        # Smilei deviates from openPMD standard: Bx instead of B/x
        axsuffix = {0: 'x', 1: 'y', 2: 'z', 90: 'r', 91: 't'}[helper.axesidentify[component]]
        return 'B{}'.format(axsuffix)

    def _simgridkeys(self):
        # Smilei deviates from openPMD standard: Ex instead of E/x
        return ['Ex', 'Ey', 'Ez','Er','El','Et',
                'Bx', 'By', 'Bz','Br','Bl','Bt',
                'Jx','Jy','Jz','Jr','Jl','Jt','Rho']

    def getderived(self):
        '''
        return all other fields dumped, except E and B.
        '''
        ret = []
        self['.'].visit(ret.append)
        # TODO: remove E and B fields and particles from list
        ret.sort()
        return ret

    def __str__(self):
        return '<SmileiReader at "{}" at iteration {:d}>'.format(self.dumpidentifier,
                                                                 self.timestep())
    
    # override inherited method to count points after mode expansion
    def gridoffset(self, key, axis):
        axid = helper.axesidentify[axis]
        if axid == 91:  # theta
            return 0
        else:
            # r, theta, z
            axidremap = {90: 0, 2: 1}[axid]
            return super(SmileiReader, self).gridoffset(key, axidremap)

    # override inherited method to count points after mode expansion
    def gridspacing(self, key, axis):
        axid = helper.axesidentify[axis]
        if axid == 91:  # theta
            return 2 * np.pi / self.gridpoints(key, axis)
        else:
            # r, theta, z
            axidremap = {90: 0, 2: 1}[axid]
            return super(SmileiReader, self).gridspacing(key, axidremap)
    
    # override inherited method to count points after mode expansion
    def gridpoints(self, key, axis):
        axid = helper.axesidentify[axis]
        axid =int(axid/90)
        (Nx, Nr) = self._data[key].shape
        Nr=Nr/2
        return (Nx,Nr)[axid]


class SmileiSeries(Simulationreader_ifc):
    '''
    Reads a time series of dumps from a given directory.

    Point this to the directory and you will get all dumps,
    but possibly containing different data.
    `simreader = SmileiSeries('path/to/simulation/')`

    Alternatively point this to a single file and you will only get
    the iterations which are present in that file:
    `simreader = SmileiSeries('path/to/simulation/Fields0.h5')`
    '''

    def __init__(self, h5file, dumpreadercls=SmileiReader, **kwargs):
        super(SmileiSeries, self).__init__(h5file, **kwargs)
        self.dumpreadercls = dumpreadercls
        self.h5file = h5file
        self.path = os.path.basename(h5file)
        if os.path.isfile(h5file):
            with h5py.File(h5file, 'r') as h5:
                self._dumpkeys = list(h5['data'].keys())
        elif os.path.isdir(h5file):
            indexfile = _getindexfile(h5file)
            self._h5 = h5py.File(indexfile, 'r')
            with h5py.File(indexfile, 'r') as h5:
                self._dumpkeys = list(h5['data'].keys())
        else:
            raise IOError('{} does not exist.'.format(h5file))

    def _getDumpreader(self, n):
        '''
        Do not use this method. It will be called by __getitem__.
        Use __getitem__ instead.
        '''
        return self.dumpreadercls(self.h5file, self._dumpkeys[n])

    def __len__(self):
        return len(self._dumpkeys)

    def __str__(self):
        return '<SmileiSeries based on "{}">'.format(self.simidentifier)
