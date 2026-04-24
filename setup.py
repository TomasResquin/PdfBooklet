#!/usr/bin/python3

#
# PdfBooklet 3.1.2 - GTK+ based utility to create booklets and other layouts 
# from PDF documents.
# Copyright (C) 2008-2012 GAF Software
# <https://sourceforge.net/projects/pdfbooklet>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import os
import re
import glob
import webbrowser


try :
    from setuptools import setup
    print ("installation with setuptools")
except :
    from distutils.core import setup

import sys



sys.prefix = '/usr'


data_files=[('/usr/share/pdfbooklet/data', glob.glob('pdfbooklet/data/*.*')),
            ('/usr/share/pdfbooklet/documentation', glob.glob('./documentation/*.*')),          
            ('/usr/share/applications', ['pdfbooklet/data/pdfbooklet.desktop']),
            ('/usr/share/locale/fr/LC_MESSAGES', glob.glob('locale/fr/LC_MESSAGES/*.*')),
            ('/usr/share/pixmaps', ['pdfbooklet/data/pdfbooklet.png']),
            ('/usr/share/icons/hicolor/48x48/apps', ['pdfbooklet/data/pdfbooklet.png'])]


setup(name='pdfbooklet',
      version='3.1.6',
      author='GAF Software',
      author_email='Averell7 at sourceforge dot net',
      maintainer='Tomas Julian Resquin',
      maintainer_email='tomasjulianresquin at proton dot me',
      description='A simple application for creating booklets and other layouts from PDF files',
      url='https://github.com/TomasResquin/PdfBooklet',
      license='GNU GPL-3',
      scripts=['bin/pdfbooklet'],
      packages=['pdfbooklet', 'pdfbooklet.pdfarranger', 'pdfbooklet.pdfarranger.utils'],
      data_files=data_files,
      #requires=['python-poppler'],          # for distutils
      #install_requires=['python-poppler']   # for setuptools  should work but does not. We can use setup.cfg instead
     )
