# Copyright 2011-2013, Vinothan N. Manoharan, Thomas G. Dimiduk,
# Rebecca W. Perry, Jerome Fung, and Ryan McGorty, Anna Wang
#
# This file is part of HoloPy.
#
# HoloPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HoloPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HoloPy.  If not, see <http://www.gnu.org/licenses/>.
"""
Reading and writing of yaml files.

yaml files are structured text files designed to be easy for humans to
read and write but also easy for computers to read.  HoloPy uses them
to store information about experimental conditions and to describe
analysis procedures.

.. moduleauthor:: Tom Dimiduk <tdimiduk@physics.harvard.edu>
"""

import numpy as np
import yaml
from yaml.reader import ReaderError
import re
import inspect
import types

from holopy_object import SerializableMetaclass
from marray import Marray
import marray

def save(outf, obj):
    if isinstance(outf, str):
        outf = open(outf, 'wb')

    outf.write(yaml.dump(obj).encode())
    if isinstance(obj, Marray):
        # yaml saves of large arrays are very slow, so we have numpy save the array
        # parts of Marray objects.  This will mean the file isn't stricktly
        # a valid yaml (or even a valid text file really), but we can still read
        # it, and with the right programs (like linux more) you can still see
        # the text yaml information, and it keeps everything in one file
        outf.write('array: !NpyBinary\n'.encode())
        np.save(outf, obj)


def load(inf):
    if isinstance(inf, str):
        with open(inf, mode='rb') as inf:
            return _load(inf)
    else:
        return _load(inf)

def _load(inf):
    line = inf.readline()
    cls = line.strip(b'{} !\n').decode('utf-8')
    lines = []
    if hasattr(marray, cls) and issubclass(getattr(marray, cls), Marray):
        while not re.search(b'!NpyBinary', line):
            lines.append(line)
            line = inf.readline()
        arr = np.load(inf)
        head = b''.join(lines[1:])
        kwargs = yaml.load(head)
        if kwargs is None:
            kwargs = {} #pragma: nocover
        return getattr(marray, cls)(arr, **kwargs)


    else:
        inf.seek(0)
        obj = yaml.load(inf)
        if isinstance(obj, dict):
            # sometimes yaml doesn't convert strings to floats properly, so we
            # have to check for that.
            for key in obj:
                if isinstance(obj[key], str):
                    try:
                        obj[key] = float(obj[key])
                    except ValueError: #pragma: nocover
                        pass #pragma: nocover

        return obj


def _pickle_method(method):
    func_name = method.__func__.__name__
    obj = method.__self__
    return _unpickle_method, (func_name, obj)

def _unpickle_method(func_name, obj):
    return getattr(obj, func_name)

###################################################################
# Custom Yaml Representers
###################################################################

def complex_constructor(loader, node):
    return complex(node.value)
yaml.add_constructor('!complex', complex_constructor)

def numpy_dtype_loader(loader, node):
    name = loader.construct_scalar(node)
    return np.dtype(name)
yaml.add_constructor('!dtype', numpy_dtype_loader)

def class_loader(loader, node):
    name = loader.construct_scalar(node)
    tok = name.split('.')
    mod = __import__(tok[0])
    for t in tok[1:]:
        mod = mod.__getattribute__(t)
    return mod
yaml.add_constructor('!class', class_loader)

def instancemethod_constructor(loader, node):
    name = loader.construct_scalar(node)
    tok = name.split('of')
    method = tok[0].strip()
    obj = 'dummy: '+ tok[1]
    obj = yaml.load(obj)['dummy']
    return getattr(obj, method)
yaml.add_constructor('!method', instancemethod_constructor)
