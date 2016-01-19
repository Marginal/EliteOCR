#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Usage:
    python -OO setup-win.py py2exe
"""

from setuptools import setup
import os
from os import rmdir, unlink
from os.path import dirname, exists, isdir, islink, isfile, join
from glob import glob
import platform
import re
import shutil
import sys
from tempfile import gettempdir

import numpy	# pull in dependencies


if sys.platform != 'win32':
    raise AssertionError("This script is for building on Windows")
elif platform.architecture()[0] != '32bit':
    raise AssertionError('Assumes a Python built for 32bit')
elif __debug__:
    raise AssertionError("Run with `python -OO setup-win.py py2exe`")
else:
    import py2exe

# Patch py2exe extension loader to work with gevent
import py2exe.build_exe
py2exe.build_exe.LOADER = """
def __load():
    imp = __import__("imp")
    os = __import__("os")
    sys = __import__("sys")
    try:
        dirname = os.path.dirname(__loader__.archive)
    except NameError:
        dirname = sys.prefix
    path = os.path.join(dirname, '%s')
    mod = imp.load_dynamic(__name__, path)
__load()
del __load
"""

# Build a qt.conf file
qt_conf = join(gettempdir(), 'qt.conf')
f = open(qt_conf, 'wt')
f.write('[Paths]\nPlugins = qt_plugins\n')
f.close()



APPNAME = 'EliteOCR'

# Build directory
DIST='dist.win32'
if DIST and len(DIST)>1 and isdir(DIST):
    shutil.rmtree(DIST)

WIXPATH = r'C:\Program Files (x86)\WiX Toolset v3.9\bin'

VERSION = re.search(r'^appversion\s*=\s*"(.+)"', file('EliteOCR.py').read(), re.MULTILINE).group(1)

DATA_FILES = [('', [qt_conf]),	# http://doc.qt.io/qt-4.8/qt-conf.html
              ('help', glob('help/*.html')),
              ('plugins/TD_Export', ['plugins/TD_Export/TD_Export.py']),
              ('qt_plugins/imageformats', [join(dirname(sys.executable), 'Lib/site-packages/PyQt4/plugins/imageformats/qgif4.dll'), join(dirname(sys.executable), 'Lib/site-packages/PyQt4/plugins/imageformats/qico4.dll')]),
              ('translations', glob('translations/*.qm')),
              ('', ['base_training_data.pck', 'letters.xml', 'numbers.xml', 'station.xml', 'commodities.json',
                    '%s.VisualElementsManifest.xml' % APPNAME]),
              ('', glob('WinSparkle.*')),
]

OPTIONS = {'dist_dir': DIST,
           'optimize': 2,
           'includes': ['PyQt4.QtNetwork', 'lxml._elementpath'],
           'excludes': ['PIL', 'setuptools', 'simplejson', 'Tkinter', 'distutils'],
           'dll_excludes': ['MSVFW32.dll', 'AVIFIL32.dll', 'MSACM32.dll', 'MPR.dll', 'AVICAP32.dll', 'API-MS-Win-Core-LocalRegistry-L1-1-0.dll']
}

setup(
    name = APPNAME,
    version = VERSION,
    windows = [ {'dest_base': APPNAME,
                 'script': 'EliteOCR.py',
                 'icon_resources': [(0, 'icon.ico')],
                 'copyright': u'© 2014 Sebastian Kaminski',
                 'name': APPNAME,		# WinSparkle - matches what QSettings stores
                 'company_name': 'seeebek',	#   ditto
                 'other_resources': [(24, 1, open(APPNAME+'.manifest').read())],
             } ],
    console = [ {'dest_base': 'EliteOCRcmd',
                 'script': 'EliteOCR.py',
                 'copyright': u'© 2014 Sebastian Kaminski',
                 'name': APPNAME,
                 'company_name': 'seeebek',
             } ],

    data_files=DATA_FILES,
    options = {'py2exe': OPTIONS},
    setup_requires=['py2exe'],
)


# Package
PKG = '%s_win_%s.msi' % (APPNAME, VERSION)
os.system(r'"%s\candle.exe" -out %s\ %s.wxs' % (WIXPATH, DIST, APPNAME))
if exists('%s/%s.wixobj' % (DIST, APPNAME)):
    os.system(r'"%s\light.exe" -sacl -spdb -sw1076 %s\%s.wixobj -out %s' % (WIXPATH, DIST, APPNAME, PKG))
