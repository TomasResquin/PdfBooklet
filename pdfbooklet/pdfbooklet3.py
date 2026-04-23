#!/usr/bin/python3
# -*- coding: utf8 -*-

from __future__ import print_function
from __future__ import unicode_literals

# 3.1.5f : fixed incorrect crop when changing output size (set cropbox=mediabox before merge)
# 3.1.4e : small bugfix
# version 3.1.6 : Migration to pypdf v3+ and integration of PdfArranger

# version 3.1.4c : fixed horizontal scrollbar, optimized zoom, fixed multiprocessing pool error, implemented thumbnail caching
# version 3.1.4b : fixed PDFShuffler on Python3, added "Reset" button to PDFShuffler, change app icon
# version 3.1.4a : fixed missing online documentation function and "Autoscale" checkbox check, reverted changes made to the autoScaleAndRotate function
# version 3.1.4 : new icon
# version 3.1.3 : fixes issues about most recently used directories
# version 3.1.2 : bug fix : autoscale didn't work for a mix of portrait / landscape pages.
# version 3.1.1 : workaround for a bug appeared in Ubuntu 19 (see the OnDraw function)
# version 3.1
# fix a serious bug which prevented auto-scale to work.

# version 3.0.6, 09/05/2018
# Bug fixes
# Better Linux support
# No longer uses a temporary file, preview data now in memory

# version 3.0.5, 30 / 07 / 2017
# German Translation added

# version 3.0.4
# New feature : add page numbers (still experimental)
# Gui : dotted line in the middle of a booklet - Still to be improved
# No longer uses the tempfiles/preview.pdf temporary file.
# this is now handled in Memory. Bugs to fix on that feature.
# To understand the reason for which we have used new_from_bytes and not new_from_data, see here :
# https://stackoverflow.com/questions/45838863/gio-memoryinputstream-does-not-free-memory-when-closed
# Fix bug for display of red rectangles when the output page is rotated 90° or 270°

PB_version = "3.1.6"
# it integrates the changes of the file which have 3.1.5 as reference. 
# Next version should be 3.2.0


"""

website : pdfbooklet.sourceforge.net

This software is a computer program whose purpose is to manipulate pdf files.

This software is governed by the CeCILL license under French law and
abiding by the rules of distribution of free software.  You can  use,
modify and/ or redistribute the software under the terms of the CeCILL
license as circulated by CEA, CNRS and INRIA at the following URL
"http://www.cecill.info".

As a counterpart to the access to the source code and  rights to copy,
modify and redistribute granted by the license, users are provided only
with a limited warranty  and the software's author,  the holder of the
economic rights,  and the successive licensors  have only  limited
liability.

In this respect, the user's attention is drawn to the risks associated
with loading,  using,  modifying and/or developing or reproducing the
software by the user in light of its specific status of free software,
that may mean  that it is complicated to manipulate,  and  that  also
therefore means  that it is reserved for developers  and  experienced
professionals having in-depth computer knowledge. Users are therefore
encouraged to load and test the software's suitability as regards their
requirements in conditions enabling the security of their systems and/or
data to be ensured and,  more generally, to use and operate it in the
same conditions as regards security.

The fact that you are presently reading this means that you have had
knowledge of the CeCILL license and that you accept its terms.

==========================================================================
"""


"""
TODO : enregistrer un projet  dans un répertoire avec caractères unicode
vérifier menuAdd

selection_s : L'usage de cette variable serait à vérifier. Est-ce que cela ne crée pas de la confusion ?
Pourquoi ne pas utiliser directement config["options"]["pageSelection"] qu'elle remplace ? Un peu plus long, mais plus facile à déboguer.
Problème surtout à mettre au point :
    Supposons une liste de fichiers ouverts dans lesquels on a fait une sélection.
    Si on ouvre le gestionnaire de fichier a ajoute un fichier à la liste, la sélection est remise à zéro.
    Ce n'est pas bon, il faudrait seulement ajouter les pages du nouveau fichier.
    C'est assez compliqué à gérer si des fichiers ont été supprimés. Une routine de comparaison
    avant et après avoir ouvert le gesionnaire devrait faire le travail.

TODO :

Autoscale : Distinguer les options : pour les pages et global ? Pas sûr que ce soit utile.
Quand un répertoire est sélectionné, avertir
quand on ouvre un fichier, et puis ensuite un projet qui a plusieurs fichiers, pdfshuffler n'est pas bien mis à jour
popumenu rotate : les valeurs de la fenêtre transformations ne sont pas mises à jour.

bugs
fichier ini : ouvrir un fichier, ouvrir le fichier ini correspondant. Ne rien changer, fermer,
le fichier ini est mis à jour à un moment quelconque et souvent toutes les transformations sont remises à zéro.
Dans la même manipulation , quand on ouvre, il arrive que les modifications d'une page soient conservées
et pas celle de l'autre page (en cahier)

slow mode : si la première feuille est faite entièrement de pages blanches générées (par exemple 2 pour
        pages blanches au début dans une configuraiton à deux pages),
        line 4285, in createNewPdf
        pages[i - 1].append(dataz)
        IndexError: list index out of range

petits défauts

quand on clique sur les boutons de global rotation, double update du preview (problème des boutons radio)

améliorations
Le tooltip pour le nom de fichier pourrait afficher les valeurs réelles que donneront les différents paramètres

"""



"""
    EXPLANATIONS OF THE WORKFLOW

    The structure of the program is easy to understand.
    Everything runs around the "config" dictionary which defines how the source pdf files
    must be placed in the output file.
    The content of this dictionary may be viewd at any time by the command "Save project"
    which builds an ini file from this dictionary.

    The program has two parts :
            1) The PdfRenderer class : It receives the config dictionary,
                and from its content builds the output file, applying the necessary
                transormations to the source pages. These transformations, in Pdf,
                are always handled byt transformation matrices. See Pdf specifications
                for details.
            2) The gui, whose only purpose is to build the config dictionary in an easy way.

    Workflow :
        1) Normal process is : - the gui creates and updates the config dict.
                               - When the Go button is pressed, the config dictionary
                                 is sent to PdfRenderer which builds the output file
        2) Preview process : To create the preview, a similar process is used.
                               - the config dictionary is sent to PdfRenderer, with an
                                 additional parameter which indicates a page number
                               - PdfRenderer creates a pdf file in memory which contains a single page.
                               - This page is displayed in the gui by Poppler.

    Inside config, the pages are named in two different ways :
        - Absolute : 2:25 designates a single page, page 25 of the second file.
        - Positional : 2,1 (line, column) designates any page which is placed
          on line 2, column 1

    What renders things complicated is that pdf counts pages from the bottom
    left, starting by 0, which is not user friendly. So the program has to convert
    data in a readable format.

    Another complication is that Pdf defines the center of rotation at the lower left corner,
    which is not user friendly. The rotate function handles this and shifts the image to create
    a centered rotation.

    Transformations

    1) When the user clicks on the preview, the selectPage function is launched.
       a) From the mouse coordinates, it determines the page clicked, and builds a page identifier
       which is a list of six values :
           - row and column (Pdf format)
           - file number and page number
           - row and column if the output page is rotated
       then it updates the selected pages list.
       b) it launchs area_expose to update the display
       c) it extracts from config the transformations already defined for this page
          and fills in the gtkEntry widgets which contains the transformations

    2) When the user changes a value in these widgets, the transformationApply function is launched.
       It reads the values in the gui and updates the config dictionary
       Then it launchs the preview function which will update the preview



    HOWTO

    to add a parameter, three steps are necessary :
        1) add the code which will use the parameter
        2) add a control in Glade
        3) add a line in makeinifile to write the parameter in the project file
        4) add a line in setupGui to setup the gui from the ini file.


"""

"""
Ubuntu 2016 - dépendences

python3-gi
python3-gi-cairo
gir1.2-gtk-3.0
gir1.2-poppler-0.18

Installation de pyinstaller

sudo pip3 install pyinstaller
le paquet python-dev est aussi nécessaire (mais pip le trouve)


"""

import time, math, string, os, sys, re, shutil, site
#print(sys.version)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try :
    import configparser     # Python 3
    from configparser import ConfigParser, RawConfigParser
except :
    from ConfigParser import ConfigParser, RawConfigParser
import io
from collections import defaultdict, OrderedDict
import subprocess
from subprocess import Popen, PIPE
from ctypes import *
import threading
import tempfile, io
import copy
import webbrowser
##import urllib
##from urllib.parse import urlparse
##from urllib.request import urljoin


from optparse import OptionParser
import traceback


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Poppler', '0.18')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Poppler
from gi.repository import Pango
from gi.repository import Gio, GLib
from gi.repository import cairo


Gtk.rc_parse("./gtkrc")

from pdfbooklet.pypdf import PdfReader, PdfWriter, PageObject, Transformation
import pdfbooklet.pypdf.generic as generic
from pdfbooklet.pypdf.generic import DecodedStreamObject, ArrayObject, NameObject, DictionaryObject, StreamObject, NumberObject, IndirectObject, RectangleObject
import re

def mergePage3(self, data):
    """
    Clean merge method using pypdf's native Transformation class.
    
    Accepts a list of items where each item is either:
    - A tuple: (PageObject, Transformation) - page with its complete transformation
    - A PageObject: merged without transformation (identity)
    
    For legacy compatibility, also accepts the old format with strings:
    - "q\n", "Q\n" - ignored (graphics state)
    - "a b c d e f cm\n" - transformation matrix (accumulated)
    - PageObject - merged with accumulated transformation
    """
    import re
    
    # Check if we're using the new structured format or legacy format
    if data and isinstance(data[0], tuple):
        # New format: list of (page, transformation) tuples
        for item in data:
            if isinstance(item, tuple) and len(item) == 2:
                page, transform = item
                
                # Set a VERY LARGE cropbox to disable pypdf clipping
                original_cropbox = page.get("/CropBox")
                large_cropbox = RectangleObject([-10000, -10000, 10000, 10000])
                page[NameObject("/CropBox")] = large_cropbox
                
                try:
                    self.merge_transformed_page(page, transform)
                finally:
                    # Restore original cropbox
                    if original_cropbox is not None:
                        page[NameObject("/CropBox")] = original_cropbox
                    elif "/CropBox" in page:
                        del page["/CropBox"]
        return
    
    # Legacy format: strings and PageObjects
    accumulated_ctm = Transformation()
    base_ctm = Transformation()
    inside_graphics_state = False
    
    for item in data:
        if isinstance(item, (str, bytes)):
            if isinstance(item, str):
                text_item = item
            else:
                text_item = item.decode("latin1")
            
            if text_item.strip() == 'q':
                if not inside_graphics_state:
                    base_ctm = accumulated_ctm
                inside_graphics_state = True
                continue
            
            if text_item.strip() == 'Q':
                inside_graphics_state = False
                continue
            
            # Extract cm commands
            for cm_match in re.finditer(r'([\d.,\-]+)\s+([\d.,\-]+)\s+([\d.,\-]+)\s+([\d.,\-]+)\s+([\d.,\-]+)\s+([\d.,\-]+)\s+cm', text_item):
                try:
                    a = float(cm_match.group(1).replace(',', '.'))
                    b = float(cm_match.group(2).replace(',', '.'))
                    c = float(cm_match.group(3).replace(',', '.'))
                    d = float(cm_match.group(4).replace(',', '.'))
                    e = float(cm_match.group(5).replace(',', '.'))
                    f = float(cm_match.group(6).replace(',', '.'))
                    
                    new_tr = Transformation((a, b, c, d, e, f))
                    accumulated_ctm = accumulated_ctm.transform(new_tr)
                except (ValueError, IndexError):
                    pass
        else:
            # PageObject
            page = item
            ctm_tuple = accumulated_ctm.ctm
            
            # Disable pypdf clipping
            original_cropbox = page.get("/CropBox")
            large_cropbox = RectangleObject([-10000, -10000, 10000, 10000])
            page[NameObject("/CropBox")] = large_cropbox
            
            try:
                is_identity = (abs(ctm_tuple[0] - 1) < 0.001 and 
                               abs(ctm_tuple[1]) < 0.001 and 
                               abs(ctm_tuple[2]) < 0.001 and 
                               abs(ctm_tuple[3] - 1) < 0.001 and 
                               abs(ctm_tuple[4]) < 0.001 and 
                               abs(ctm_tuple[5]) < 0.001)
                
                if not is_identity:
                    self.merge_transformed_page(page, ctm_tuple)
                else:
                    self.merge_page(page)
            finally:
                if original_cropbox is not None:
                    page[NameObject("/CropBox")] = original_cropbox
                elif "/CropBox" in page:
                    del page["/CropBox"]
            
            accumulated_ctm = base_ctm


def calculate_page_transform(page, row, column, ref_width, ref_height, 
                              output_width, output_height, output_scale, 
                              columns_i, rows_i, rotate_to_fit=True):
    """
    Calculate the complete transformation for a page using pypdf's Transformation class.
    
    This function builds a single transformation matrix that:
    1. Optionally rotates the page to match reference orientation
    2. Scales the page to fit within the reference cell
    3. Centers the page within its cell
    4. Positions the page at the correct cell location
    5. Scales everything to fit the output page
    6. Centers the scaled content on the output page
    
    Args:
        page: The source PageObject
        row: Row position (0-indexed, 0 is bottom)
        column: Column position (0-indexed)
        ref_width: Reference cell width (input page width)
        ref_height: Reference cell height (input page height)
        output_width: Output page width
        output_height: Output page height
        output_scale: Scale factor to fit content on output (1.0 = no scaling)
        columns_i: Number of columns in layout
        rows_i: Number of rows in layout
        rotate_to_fit: Whether to rotate page to match reference orientation
        
    Returns:
        A Transformation object representing the complete transformation
    """
    import math
    
    # Get page dimensions
    # Handle implicit rotation via /Rotate attribute
    source_rotation = 0
    if "/Rotate" in page:
        source_rotation = int(page["/Rotate"])
        
    orig_width = float(page.mediabox.width)
    orig_height = float(page.mediabox.height)
    
    # Adjust dimensions based on rotation
    if source_rotation in [90, -270]:
        page_width, page_height = orig_height, orig_width
    elif source_rotation in [270, -90]:
        page_width, page_height = orig_height, orig_width
    else: # 0, 180
        page_width, page_height = orig_width, orig_height
    
    # Determine orientations
    ref_landscape = ref_width > ref_height
    page_landscape = page_width > page_height
    
    rotation = 0
    if rotate_to_fit and ref_landscape != page_landscape:
        rotation = 270  # Rotate 270 degrees (or -90) relative to current orientation
        # After rotation, swap dimensions
        page_width, page_height = page_height, page_width
    
    # Calculate scale to fit page in reference cell
    scale_w = ref_width / page_width
    scale_h = ref_height / page_height
    page_scale = min(scale_w, scale_h)
    
    # Calculate centering within the reference cell
    scaled_page_width = page_width * page_scale
    scaled_page_height = page_height * page_scale
    h_center_in_cell = (ref_width - scaled_page_width) / 2
    v_center_in_cell = (ref_height - scaled_page_height) / 2
    
    # Cell position in reference coordinates
    cell_x = column * ref_width
    cell_y = row * ref_height
    
    # Calculate output centering
    total_content_width = ref_width * columns_i * output_scale
    total_content_height = ref_height * rows_i * output_scale
    h_center_output = (output_width - total_content_width) / 2
    v_center_output = (output_height - total_content_height) / 2
    
    # Build the transformation chain
    transform = Transformation()
    
    # Step 0: Apply source page rotation (from /Rotate or imposition)
    # This aligns the coordinate system to be "upright" relative to the visual page
    if source_rotation != 0:
        transform = transform.rotate(source_rotation)
        if source_rotation == 90 or source_rotation == -270:
            transform = transform.translate(tx=orig_height, ty=0)
        elif source_rotation == 180 or source_rotation == -180:
            transform = transform.translate(tx=orig_width, ty=orig_height)
        elif source_rotation == 270 or source_rotation == -90:
            transform = transform.translate(tx=0, ty=orig_width)
            
    # Step 1: Logical Rotation (rotate_to_fit)
    if rotation != 0:
        transform = transform.rotate(rotation)
        # Rotation handling:
        # When rotating 90/270 degrees, dimensions are swapped.
        # We need to translate the page back into the positive quadrant (0,0 to W,H).
        # 
        # For 270 degree rotation (equivalent to -90):
        # x' = y, y' = -x
        # The page rotates down into negative Y.
        # We must translate by the original width (which is the new height).
        transform = transform.translate(tx=0, ty=page_height)
    
    # Step 2: Scale page to fit in reference cell
    transform = transform.scale(sx=page_scale, sy=page_scale)
    
    # Step 3: Center page within reference cell
    transform = transform.translate(tx=h_center_in_cell, ty=v_center_in_cell)
    
    # Step 4: Position at cell location (in reference coordinates)
    transform = transform.translate(tx=cell_x, ty=cell_y)
    
    # Step 5: Scale everything to fit output page
    if output_scale != 1.0:
        # Scale around origin - this scales both content and positions
        transform = transform.scale(sx=output_scale, sy=output_scale)
    
    # Step 6: Center on output page
    if h_center_output > 0.001 or v_center_output > 0.001:
        transform = transform.translate(tx=h_center_output, ty=v_center_output)
    
    return transform


PageObject.mergePage3 = mergePage3

# from pdfbooklet import *
from pdfbooklet.files_chooser import Chooser

import gettext
import locale

try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    pass

locale_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'share', 'locale')
if not os.path.exists(locale_dir):
    locale_dir = '/usr/share/locale'
gettext.install('pdfbooklet', locale_dir)

debug_b = 0



def join_list(my_list, separator) :
    mydata = ""
    if isinstance(my_list, list) :
        for s in my_list :
            mydata += s + separator
    elif isinstance(my_list, dict) :
        for s in my_list :
            try :
                item1 = unicode2(my_list[s])
            except :
                item1 = str(my_list[s])
            mydata += item1 + separator
    crop = len(separator) * -1
    mydata = mydata[0:crop]
    return mydata

def get_value(dictionary, key, default = 0) :

    if not key in dictionary :
        dictionary[key] = default
        return default
    else :
        return dictionary[key]


def unicode2(string, dummy = "") :

    if isinstance(string, str):
        return string
    
    if isinstance(string, bytes):
        try :
            return string.decode("utf_8")
        except :
            try :
    #               print string, " est ecrit en cp1252"
                return string.decode("cp1252")
            except :
                return str(string)       # Is this the good option ? Return False or an empty string ?
                #return "inconnu"
    return str(string)

def printExcept() :
    a,b,c = sys.exc_info()
    for d in traceback.format_exception(a,b,c) :
        print(d, end=' ')

def bool_test(value) :
    if isinstance(value, str) :
        try :
            value = int(value)
        except :
            if value.strip().lower() == "true" :
                return True
            else :
                return False

    return bool(value)

def alert(message, type = 0) :

        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING,
                                     Gtk.ButtonsType.CLOSE , message)
        dialog.run()
        dialog.destroy()

def showwarning(title, message) :
    """
      GTK_MESSAGE_INFO,
      GTK_MESSAGE_WARNING,
      GTK_MESSAGE_QUESTION,
      GTK_MESSAGE_ERROR,
      GTK_MESSAGE_OTHER
    """

    resetTransform_b = False

    dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL , Gtk.MessageType.WARNING,
                                 Gtk.ButtonsType.CLOSE , title)

    dialog.format_secondary_text(message)
    if "transformWindow" in app.arw :
        app.arw["transformWindow"].set_keep_above(False)
        resetTransform_b = True
    dialog.set_keep_above(True)
    dialog.run()
    dialog.destroy()
    if resetTransform_b == True :
        app.arw["transformWindow"].set_keep_above(True)


def askyesno(title, string) :


    dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL , Gtk.MessageType.QUESTION,
                               Gtk.ButtonsType.NONE, title)
    dialog.add_button(Gtk.STOCK_YES, True)
    dialog.add_button(Gtk.STOCK_NO, False)
    dialog.format_secondary_text(string)
    dialog.set_keep_above(True)
    rep = dialog.run()
    dialog.destroy()
    return rep

def ask_text(parent, message, default=''):
    """
    Display a dialog with a text entry.
    Returns the text, or None if canceled.
    """
    d = Gtk.MessageDialog(parent,
                          Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                          Gtk.MessageType.QUESTION,
                          Gtk.ButtonsType.OK_CANCEL,
                          message)
    entry = Gtk.Entry()
    entry.set_text(default)
    entry.show()
    d.vbox.pack_end(entry, True, True, 0)
    entry.connect('activate', lambda _: d.response(Gtk.ResponseType.OK))
    d.set_default_response(Gtk.ResponseType.OK)

    r = d.run()
    text = entry.get_text()
    if sys.version_info[0] == 2 :
        text = text.decode('utf8')
    d.destroy()
    if r == Gtk.ResponseType.OK:
        return text
    else:
        return None




class myConfigParser() :
    def __init__(self) :
        pass

    def read(self,
            iniFile_s,
             encoding = "utf8",
             comments = False) :
        # ----
        # read ini file and creates a dictionary
        # @param iniFile_s : ini file path
        # @param comments : if True, comments are included in the config. Otherwise they are skipped
        # @return : True if successful, False otherwise


        myconfig = OrderedDict()
        if not os.path.isfile(iniFile_s) :
            return False

        try :                       # if pdfbooklet.cfg is invalid, don't block the program
            if sys.version_info[0] == 3 :
                fileIni = open(iniFile_s, "r", encoding = "utf8")
            else :
                fileIni = open(iniFile_s, "r")
            # If BOM present, skip the first three bytes
            isBOM_s = fileIni.read(3)
            if isBOM_s == chr(239) + chr(187) + chr(191) :  # There is a BOM, skips it
                pass
            else :
                fileIni.seek(0)                          # No BOM, come back to beginning of file

        except :
            myconfig = OrderedDict()
            myconfig["mru"] = OrderedDict()
            myconfig["mru2"] = OrderedDict()
            myconfig["options"] = OrderedDict()
            return myconfig

        section_s = ""
        while True :
            record_s = fileIni.readline()
            if record_s == "" :                     # end of file
                break
            # format line : strip and replace possible \ by /
            record_s = record_s.strip()
            if sys.version_info[0] == 2 :
                record_s = record_s.decode("utf8")
            record_s = record_s.replace("\\", "/")      # TODO : or better : formatPath()
            # If the  line is a section
            if record_s[0:1] == "[" and record_s[-1:] == "]" :      # section
                section_s = record_s[1:-1]
                myconfig[section_s] = OrderedDict()
            else :
                # Skip useless lines
                if section_s == "" :            # comment in the beginning of the file
                    continue
                if len(record_s) == 0 :         # empty line
                    continue
                if record_s[0:1] == "#" :       # comment
                    comment_b = True
                else :
                    comment_b = False
                if comments == False :          # Skip comments
                    if comment_b == True :
                        continue


                # otherwise, store data in section
                # TODO : comments
                record_data = record_s.split("=")
                if len(record_data) > 1 :
                    key = record_data[0].strip()
                    linedata = record_data[1].strip()
                    if linedata == "False" :
                        linedata = False
                    if linedata == "True" :
                        linedata = True
                    myconfig[section_s][key] = linedata
        return myconfig

    def write(self, myconfig, filename) :
        if sys.version_info[0] == 3 :
            iniFile = open(filename, "w", encoding = "utf8")
        else :
            iniFile = open(filename, "w")
        for a in myconfig :
            iniFile.write("[" + a + "]\n")
            for b in myconfig[a] :
                value = myconfig[a][b]
                if value == True :
                    value = '1'
                elif value == False :
                    value = '0'
                data1 = (b + " = " + value + "\n").encode("utf8")  # En python 3 cette ligne convertit en bytes !!!
                data1 = (b + " = " + value + "\n")
                iniFile.write(data1)
            iniFile.write("\n")
        iniFile.close()
        return True

class TxtOnly :
    def __init__(self,
                render,
                pdfList = None,
                pageSelection = None):

        global config, rows_i, columns_i, step_i, sections, output, input1, adobe_l, inputFiles_a, inputFile_a
        global numfolio, prependPages, appendPages, ref_page, selection, PSSelection
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, mediabox_l
        global ouputFile, optionsDict, selectedIndex_a, selected_page, deletedIndex_a, app
        global arw
##        elib_intl.install("pdfbooklet", "share/locale")

        if None != pdfList :
            inputFiles_a = pdfList
            self.loadPdfFiles()
        else :
            inputFiles_a = {}
            inputFile_a = {}
        self.render = render
        self.permissions_i = -1     # all permissions
        self.password_s = ""
        rows_i = 1
        columns_i = 2
        urx_i = 200
        ury_i = 200
        optionsDict = {}
        adobe_l = 0.3527

        self.radioSize = 1
        self.radioDisp = 1
        self.repeat = 0
        self.booklet = 1
        self.righttoleft = 0
        self.delete_rectangle = []

    def openProject2(self, filename_u) :
        # Called by OpenProject and OpenMru (in case the selected item was a project)
        global config, openedProject_u, preview_b, project_b

        if os.path.isfile(filename_u):
            openedProject_u = filename_u
##            self.arw["window1"].set_title(u"Pdf-Booklet  [ " + PB_version + " ] - " + filename_u)
            preview_b = False
            project_b = True
            self.parseIniFile(filename_u)
            preview_b = True
            project_b = False
            return True


    def readNumEntry(self, entry, widget_s = "") :

        if isinstance(entry, int) :
            return float(entry)
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if value == "" : value = 0
        try :
            value = float(value)
        except :
            showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
            return None

        return value


    def readmmEntry(self, entry, widget_s = "", default = 0) :
        global adobe_l

        value = ""
        if isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if (value == "") :
            value = default
        else :
            try :
                value = float(value) / adobe_l
            except :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        return value

    def readPercentEntry(self, entry, widget_s = "") :

        value = ""
        if sys.version_info[0] == 2 and isinstance(entry, unicode) :
                value = entry
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if (value == "") :
            value = 100
        else :
            value.replace("%", "")
            try :
                value = float(value) / 100
                if value < 0 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be > 0. Aborting \n") % widget_s)
                    return None
            except :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        return value

    def readIntEntry(self, entry, widget_s = "", type_i = 0, default = 0) :
        # type = 0 : accepts all values >= 0
        # type = 1 : accepts all values > 0
        # type = -1 : accepts any integer, positive or negative
        # type = 2 : optional. Don't warn if missing, but warn if invalid (not integer)

        value = ""
        if isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")


        try :
            value = int(value)
            if type_i == 0 :
                if value < 0 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be >= 0. Aborting \n") % widget_s)
                    return None
            elif type_i == 1 :
                if value < 1 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be > 0. Aborting \n") % widget_s)
                    return None
        except :
            if value == "" :
                if type_i == 2 :
                    pass
                else :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                    return None
            else :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        if value == "" :
            return default
        elif value == 0 and default > 0 :
            return default
        return value

    def readBoolean(self, entry) :

        value = ""

        if isinstance(entry, str) :
            if entry.strip().lower() == "true" :
                value = True
            elif entry.strip() == "1" :
                value = True
            else :
                value = False
        elif isinstance(entry, bool) :
            return entry
        else :
            value = entry.get_text()
        try :
            if int(value) < 1 :
                return False
            else :
                return True
        except :
            return False


    def parseIniFile(self, inifile = "") :

        global config, rows_i, columns_i, step_i, cells_i, input1, adobe_l
        global numfolio, prependPages, appendPages, ref_page, selection
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, inputFile, inputFiles_a
        global startup_b


        config = parser.read(inifile)


        # migration to 2.4 format : copy xxxx1 values to xxxx and delete xxxx1
        for section in config :
            for option in config[section] :
                if option in["htranslate1", "vtranslate1", "scale1", "rotate1", "xscale1", "yscale1"] :  # Clean no longer used data
                    if option[:-1] in config[section] :
                        config[section][option[:-1]] = config[section][option]
                        del config[section][option]



        # store in dictionary
        self.pagesTr = config
        if not "options" in config :
            config["options"] = OrderedDict()

        for section in config :
            if not section in self.pagesTr :
                self.pagesTr[section] = OrderedDict()

        # inputs

        if startup_b == 0 :
            if "options" in config:
                if "inputs" in config["options"] :


                    temp1 = config["options"]["inputs"]
                    inputFiles_a = {}
                    for filename in temp1.split("|") :
                        if os.path.isfile(filename) :
                            pdfFile = PdfReader(open(filename, "rb"))
                            numpages = len(pdfFile.pages)
                            path, shortFileName = os.path.split(filename)
                            i = len(inputFiles_a)
                            inputFiles_a[i + 1] = filename

                    self.loadPdfFiles()
                    if "pageselection" in config["options"] :
                            self.selection_s = config["options"]["pageselection"]



        # variables
        if "options" in config:
            if "booklet" in config["options"] :
                self.booklet = int(config["options"]["booklet"])


        # multi-line entries

        if "options" in config:
            if "userLayout" in config["options"] :
                layout_s = config["options"]["userLayout"]
                config["options"]["userLayout"] = layout_s.replace("/", "\n")
                (a,b,c,d) = self.parse_user_layout(layout_s)
                self.imposition = a



    def setOption(self, option, default = "") :
        if option in config["options"] :
            result = config["options"][option]
        else :
            result = default
        if isinstance(default, int) :
            try :
                return int(result)
            except :
                return default
    def parse_user_layout(self, layout_s) :

            if layout_s.strip() == "" :
                return ([], 0 , 0 , [])

            layout_s = layout_s.replace("/", "\n")
            lines = layout_s.split("\n")
            imposition = []
            lines2 = []
            for line in lines :
                if line.strip() == "" :     # correct errors : ignore blank lines
                    continue
                if line[0:1] == "#" :       # ignore comments
                    continue
                if line[0:4] == "====" :    # New sheet
                    imposition.append(lines2)
                    lines2 = []
                else :
                    lines2.append(line)
            if len(lines2) > 0 :
                imposition.append(lines2)

            numrows = len(lines2)
            cols = lines2[0].split(",")
            numcols = 0
            for a in cols :
                if a.strip() != "" :
                    numcols += 1

            imposition2 = []
            for lines2 in imposition :
                pages = []
                for line in lines2 :
                    line = line.split(",")
                    for a in line :
                        if a.strip() != "" :         # correct errors : ignore trailing comma
                            pages.append(a.strip())
                imposition2.append(pages)
            self.imposition = imposition2

            return (imposition2, numrows, numcols, pages)

    def loadPdfFiles(self) :
        global inputFile_a, inputFiles_a, pagesIndex_a, refPageSize_a

        i = 1
        inputFile_a = {}
        inputFile_details = {}
        for key in inputFiles_a :
            val = inputFiles_a[key]
            if os.path.isfile(val) :
                inputFile_a[val] = PdfReader(open(val, "rb"))
                inputFile_details[val] = {}
                if inputFile_a[val].is_encrypted :
                    inputFile_details[val]["encrypt"] = True
                    # if not hasattr(inputFile_a[val], "_decryption_key") :   # if not already decrypted
                    # TODO: _decryption_key check might not be needed or different in pypdf
                    # pypdf usually handles decryption state differently. For now commenting out to avoid AttributeError if property changed.
                    # Checking if is_encrypted should be enough for now.
                    password = ask_text(None, _("Please, enter the password for this file"))
                    if password != None :
                        password = password.encode("utf8")
                        inputFile_a[val].decrypt(password)     # Encrypted file
                        if key == 1 :           # we get permissions and password from the first file
                            # FIXME: getPermissions does not exist in pypdf v3+
                            # (a,b,self.permissions_i) = inputFile_a[val].getPermissions()
                            self.permissions_i = 0 # Default/Placeholder
                            self.password_s = password
                    inputFile_details[val]["password"] = password
                selectedIndex_a = {}
                deletedIndex_a = {}

                i += 1



    def output_page_size(self, radiosize, ref_file = 1, ref_page = 0, logdata = 1) :


        global config, rows_i, columns_i, sections, output, adobe_l, inputFiles_a, inputFile_a
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, mediabox_l, outputScale, refPageSize_a

        # Ouput page size
        if ref_file in inputFiles_a :
            fileName = inputFiles_a[ref_file]
            fileName = unicode2(fileName)
            try :
                page0 = inputFile_a[fileName].pages[ref_page]
            except :
                print(_("The reference page is invalid. We use the first page"))
                page0 = inputFile_a[fileName].pages[0]

            llx_i=page0.mediabox.left
            lly_i=page0.mediabox.bottom
            urx_i=page0.mediabox.right
            ury_i=page0.mediabox.top

            urx_i=float(urx_i) - float(llx_i)
            ury_i=float(ury_i) - float(lly_i)

            refPageSize_a = [urx_i, ury_i]
        else :
            alert(_("Reference page invalid, there is no file n°" + str(ref_file)))
            return False


        #££self.print2 (_("Size of source file =    %s mm x %s mm ") % (int(urx_i * adobe_l), int(ury_i * adobe_l)), 1)

        oWidth_i = urx_i * columns_i
        oHeight_i = ury_i * rows_i

        if radiosize == 1 :
            mediabox_l = [oWidth_i, oHeight_i, columns_i, rows_i]
        elif radiosize == 2 :                         # size = no change
            if oWidth_i < oHeight_i :                           # set orientation
                mediabox_l = [urx_i, ury_i, columns_i, rows_i]
            else :
                mediabox_l = [ury_i, urx_i, columns_i, rows_i]

            # calculate  the scale factor
            deltaW = mediabox_l[0] / oWidth_i
            deltaH = mediabox_l[1] / oHeight_i
            if deltaW < deltaH :
                outputScale = deltaW
            else :
                outputScale = deltaH


        elif radiosize == 3 :         # user defined

                customX = self.readNumEntry(app.arw["outputWidth"], _("Width"))
                if customX == None : return False
                customY = self.readNumEntry(app.arw["outputHeight"], _("Height"))
                if customY == None : return False


                mediabox_l = [ customX * (1 / adobe_l), customY * (1 / adobe_l), columns_i, rows_i]


                # calculate  the scale factor
                deltaW = mediabox_l[0] / oWidth_i
                deltaH = mediabox_l[1] / oHeight_i
                if deltaW < deltaH :
                    outputScale = deltaW
                else :
                    outputScale = deltaH


        outputUrx_i = mediabox_l[0]
        outputUry_i = mediabox_l[1]

        app.arw["info_fichier_sortie"].set_text(_("%s mm x %s mm ") % (int(outputUrx_i * adobe_l), int(outputUry_i * adobe_l)))



class dummy:
    def __init__(self) :

        self.pagesTr = {}
        self.arw = {}


class gtkGui(TxtOnly):
    # parameters :
    # render is an instance of pdfRenderer
    # pdfList is a dictionary of path of pdf files : { 1:"...", 2:"...", ... }
    # pageSelection is a list of pages in the form : ["w:x", ... , "y:z"]
    def __init__(self,
                    render,
                    pdfList = None,
                    pageSelection = None):

        TxtOnly.__init__(self, render, pdfList, pageSelection)

        global config, rows_i, columns_i, step_i, sections, output, input1, adobe_l, inputFiles_a, inputFile_a
        global numfolio, prependPages, appendPages, ref_page, selection, PSSelection
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, mediabox_l
        global ouputFile, optionsDict, selectedIndex_a, selected_page, selected_pages_a, selectedeletedIndex_a, app
        if None != pdfList :
            inputFiles_a = pdfList
            ini.loadPdfFiles()
        else :
            inputFiles_a = {}
            inputFile_a = {}
        self.permissions_i = -1     # all permissions
        self.password_s = ""
        rows_i = 1
        columns_i = 2
        step_i = 1
        urx_i = 200
        ury_i = 200
        optionsDict = {}
        adobe_l = 0.3527


        areaAllocationH_i = 400
        areaAllocationW_i = 400
        self.freeze_b = False
        self.preview_scale = 1
        self.dev1 = ""  # for development needs

        selectedIndex_a = {}
        selected_page = None
        selected_pages_a = []
        deletedIndex_a = {}


        app = self
        self.render = render
        self.ar_pages = []
        self.ar_layout = []
        self.previewPage = 0
        self.clipboard= {}
        self.arranger_view = None
        self.imposition = []

        self.initdrag = []
        self.enddrag = []

        self.backup = []
        self.backup_index = 0
        self.backup_command = True
        self.myselectedpage = "" # Initialize to avoid AttributeError in OnDraw


        self.widgets = Gtk.Builder()
        #self.widgets.set_translation_domain('pdfbooklet')
        self.widgets.add_from_file(sfp2('data/pdfbooklet3.glade'))
        arWidgets = self.widgets.get_objects()
        self.arw = {}
        for z in arWidgets :
            try :
                name = Gtk.Buildable.get_name(z)
                self.arw[name]= z
                z.set_name(name)
            except :
                pass


        #autoconnect signals for self functions
        self.widgets.connect_signals(self)
        self.arw["drawingarea1"].connect('draw', self.OnDraw)

        self.autoscale = self.arw["autoscale"]
        self.area = self.arw["drawingarea1"]
        self.settings = self.arw["settings"]
        self.overwrite = self.arw["overwrite"]
        self.noCompress = self.arw["noCompress"]
        self.slowmode = self.arw["slowMode"]
        self.righttoleft = self.arw["righttoleft"]
        self.status = self.arw["status"]


        self.window1 = self.arw["window1"]
        self.window1.show_all()
        self.window1.set_title("Pdf-Booklet  [ " + PB_version + " ]")
        try:
            self.window1.set_icon_from_file(sfp2('data/pdfbooklet.ico'))
        except Exception as e:
            print("Could not load icon:", e)
        self.window1.connect("destroy", self.close_application)

        """
        To change the cursor :
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.window1.get_window().set_cursor(watch_cursor)

##        display =  self.window1.get_display()
##        watch_cursor = Gdk.Cursor.new_from_name(display, "default")

        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        watch_cursor = Gdk.Cursor(Gdk.CursorType.CROSS)
        self.window1.get_window().set_cursor(watch_cursor)
        """

        self.mru_items = {}
        self.menuAdd()

        self.selection_s = ""

        # Global transformations
        self.Vtranslate1 = self.arw["vtranslate1"]
        self.scale1 = self.arw["scale1"]
        self.rotation1 = self.arw["rotation1"]
        self.thispage = self.arw["thispage"]
        self.evenpages = self.arw["evenpages"]
        self.oddpages = self.arw["oddpages"]



        self.area.show()
        self.pagesTr = {}

# ############ Setup drag motion for drawingarea1 ##############


        # setup drag
##        targets = Gtk.TargetList.new([])
##        targets.add_text_targets(0)
##
##        self.area.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [],
##            Gdk.DragAction.COPY)
##        self.area.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
##        self.area.drag_source_set_target_list(targets)
##        self.area.drag_dest_set_target_list(targets)

        # self.area is connected to drag_motion in glade
        
        # Initialize outputSizeDropdown sensitivity
        if "radiosize3" in self.arw and "outputSizeDropdown" in self.arw:
             self.arw["outputSizeDropdown"].set_sensitive(self.arw["radiosize3"].get_active())
             self.arw["outputSizeDropdown"].set_active_id("preset_placeholder")
             
        self.updating_from_dropdown = False




# ##################### Themes [disabled] #################################


        menu_themes = Gtk.Menu()
        mem_menu_name = ""
        # Get the list of gtkrc-xxx files in "data", extract the name, and add items to menu
        themes_dict = {}

        themes_dir = os.path.join(prog_path_u, "share/themes")
        if os.path.isdir(themes_dir) :


            for a in os.listdir(themes_dir) :   # TODO ££
                        rcpath = os.path.join(prog_path_u,a)
                        themes_dict[a] = rcpath
            themes_list = themes_dict.keys()
    ##        themes_list.sort()

            # Extract similar short names to build submenus
            mem_short_name = ""
            submenus = []
            for menu_name in themes_list :
                short_name = menu_name.split("-")[0]
                if short_name == mem_short_name :
                    if short_name not in submenus :
                        submenus.append(short_name)
                mem_short_name = short_name

            # Build first level menu
            sub_dict = {}
            to_del = []
            keys = themes_dict.keys()
    ##        keys.sort()
            for menu_name in submenus :
                if len(menu_name.strip()) == 0 :
                    continue
                sub_dict[menu_name] = Gtk.MenuItem(menu_name)
                menu_themes.append(sub_dict[menu_name])
                sub_dict[menu_name].show()


                submenu = Gtk.Menu()
                submenu.show()
                for key in keys :
                    rcpath = themes_dict[key]
                    short_name = key.split("-")[0]
                    if short_name == menu_name :
                        commandes = Gtk.MenuItem(key)
                        submenu.append(commandes)
                        commandes.connect("activate", self.change_theme, rcpath, key)
                        commandes.show()
                        to_del.append(key)

                sub_dict[menu_name].set_submenu(submenu)

            # delete used keys and add the remaining to main menu

            for key in to_del :
                del themes_dict[key]
            keys = themes_dict.keys()
    ##        keys.sort()

            for menu_name in keys :
                if len(menu_name.strip()) == 0 :
                    continue
                rcpath = themes_dict[menu_name]
                commandes = Gtk.MenuItem(menu_name)
                menu_themes.append(commandes)
                commandes.connect("activate", self.change_theme, rcpath, menu_name)
                commandes.show()

            #self.arw["themes"].set_submenu(menu_themes)
            aaa = 1


    def change_theme(self, widget, path, theme) :

        try:
            settings_location = os.path.join(site.getsitepackages()[1], "gnome/etc/gtk-3.0/settings.ini")
        except :
            settings_location = os.path.join(prog_path_u, "etc/gtk-3.0/settings.ini")
        f1 = open(settings_location, "w")
        f1.write("[Settings]\n")
        f1.write("gtk-theme-name = " + theme)
        f1.close()
        alert(_("You must restart the program to apply the new theme."))






    # this small function returns the type of a widget
    def widget_type(self, widget) :
        try :
            z = widget.class_path()
            z2 = z.split(".")[-1]
            return z2
        except:
            return False


    def gtk_delete(self, source=None, event=None):
        Gtk.main_quit()

    def close_application(self, widget, event=None, mydata=None):
        """Termination"""
        if self.arranger_view != None :
            self.arranger_view.close_application("")
            self.arranger_view = None

        if Gtk.main_level():
            self.arw["window1"].destroy()
            Gtk.main_quit()
            Gdk.threads_leave()

        #os._exit(0)
        return False

    def file_manager(self,widget):
        global inputFiles_a
        mrudir = self.read_mru2("manager")
        if mrudir == "" :
            mrudir = prog_path_u
        self.chooser = Chooser(inputFiles_a, share_path_u, mrudir)
        inputFiles_a = self.chooser.inputFiles_a
        if len(inputFiles_a) == 0 :
            return
        # add file(s) to most recently used
        self.mru(inputFiles_a, "manager")
        self.chooser.chooser.destroy()
        self.chooser = None
        if self.arranger_view:
            self.arranger_view.model.clear()
            self.arranger_view.pdfqueue = []
            self.arranger_view.nfile = 0
            for key in inputFiles_a :
                self.arranger_view.add_pdf_pages(inputFiles_a[key])
            # TODO : N'est à faire que si la liste des fichiers a changé
            self.arranger_view.rendering_thread.pdfqueue = self.arranger_view.pdfqueue

        ini.loadPdfFiles()
        app.selection_s = ""

        self.previewUpdate()


    def FormatPath (
            self,
            path,
            typePath = 0) :
        # Replaces // and \\ by /, but preserves the initial // necessary in urls on a network

        if path[0:2] == "//" or path[0:2] == ["\\"] :
            prefix_s = "//"
            path = path[2:]
        else :
            prefix_s = ""

        if typePath == 1 :
            path = path.replace(":", "")
            prefix_s = ""
        path = path.replace("\\", "/")
        path = path.replace("//", "/")
        return(prefix_s + path)




    def openProject(self, widget, name = "") :
        global config, openedProject_u, preview_b, project_b



        old_dir = self.read_mru2("project")

        gtk_chooser = Gtk.FileChooserDialog(title=_('Import...'),
                                        action=Gtk.FileChooserAction.OPEN,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                  Gtk.ResponseType.CANCEL,
                                                  Gtk.STOCK_OPEN,
                                                  Gtk.ResponseType.OK))
        gtk_chooser.set_current_folder(old_dir)
        gtk_chooser.set_select_multiple(False)

        filter_all = Gtk.FileFilter()
        filter_all.set_name(_('All files'))
        filter_all.add_pattern('*')
        gtk_chooser.add_filter(filter_all)

        filter_ini = Gtk.FileFilter()
        filter_ini.set_name(_('INI files'))
        filter_ini.add_pattern('*.ini')
        gtk_chooser.add_filter(filter_ini)
        gtk_chooser.set_filter(filter_ini)

        response = gtk_chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = gtk_chooser.get_filename()
            filename_u = unicode2(filename, "utf-8")
            self.mru(filename, "project")
            ini.openProject2(filename_u)
            ini.loadPdfFiles()
            self.setupGui()
            self.arw["previewEntry"].set_text("1")
            self.previewUpdate()

##        elif response == Gtk.RESPONSE_CANCEL:
##            print(_('Closed, no files selected'))
        gtk_chooser.destroy()

    def openMru(self, widget) :
        global config, openedProject_u, preview_b, project_b
        global inputFiles_a

        widget_name = widget.get_name()
        filenames_list_s = self.mru_items[widget_name][1]

        # are we opening a project file ?
        filename_u = unicode2(filenames_list_s[0], "utf-8")
        extension_s = os.path.splitext(filename_u)[1]
        if extension_s == ".ini" :
            ini.openProject2(filename_u)
            self.selection_s = config["options"]["pageSelection"]
            ini.loadPdfFiles()
            self.setupGui()
            self.arw["previewEntry"].set_text("1")
            self.previewUpdate()
            return
        else :
            ini.parseIniFile(sfp3("pdfbooklet.cfg"))     # reset transformations
            self.setupGui(sfp3("pdfbooklet.cfg"))

        inputFiles_a = {}

        for filename_s in filenames_list_s :
            filename_u = unicode2(filename_s, "utf-8")
            extension_s = os.path.splitext(filename_u)[1]
            i = len(inputFiles_a)
            inputFiles_a[i + 1] = filename_u


        ini.loadPdfFiles()
        app.selection_s = ""
        self.previewUpdate()


        if self.arranger_view:
            self.arranger_view.model.clear()
            self.arranger_view.pdfqueue = []
            self.arranger_view.nfile = 0
            self.arranger_view.npage = 0
            for key in inputFiles_a :
                self.arranger_view.add_pdf_pages(inputFiles_a[key])
            # TODO : N'est à faire que si la liste des fichiers a changé
            self.arranger_view.rendering_thread.pdfqueue = self.arranger_view.pdfqueue
            #for row in self.arranger_view.model:
            #        row[6] = False






    def saveProject(self, widget) :
        global openedProject_u

        if openedProject_u :
            self.saveProjectAs("", openedProject_u)
        else :
            self.saveProjectAs("")


    def saveProjectAs(self, widget, filename_u = "") :
        global config, openedProject_u

        if filename_u == "" :

            old_dir = self.read_mru2("project")

            gtk_chooser = Gtk.FileChooserDialog(title=_('Save project...'),
                                            action=Gtk.FileChooserAction.SAVE,
                                            buttons=(Gtk.STOCK_CANCEL,
                                                      Gtk.ResponseType.CANCEL,
                                                      Gtk.STOCK_SAVE,
                                                      Gtk.ResponseType.ACCEPT))
            gtk_chooser.set_do_overwrite_confirmation(True)
            gtk_chooser.set_current_folder(old_dir)
            gtk_chooser.set_current_name("untitled document")
            # or chooser.set_filename("untitled document")

            response = gtk_chooser.run()

            if response == Gtk.ResponseType.CANCEL:
##                print(_('Closed, no files selected'))
                gtk_chooser.destroy()
                return

            elif response == Gtk.ResponseType.ACCEPT:
                filename = gtk_chooser.get_filename()
                filename_u = unicode2(filename, "utf-8")
                if filename_u[-4:] != ".ini" :
                    filename_u += ".ini"
                gtk_chooser.destroy()
                self.mru(filename_u, "project")            # TODO : why filename_u here and filename in another call ?



        openedProject_u = filename_u

        for section in self.pagesTr :
            if not section in config :
                config[section] = self.pagesTr[section]



        # update with last selections in the gui
        # perhaps we could also update first pagesTr
        self.makeIniFile()
##        for section in out_a :
##            config[section] = out_a[section]


        #config.write(iniFile)
        self.write_ordered_config(filename_u)

    def write_ordered_config(self, filename_u) :
        global config

        if sys.version_info[0] == 3 :
            iniFile = open(filename_u, "w", encoding = "utf8")
        else :
            iniFile = open(filename_u, "w")

        # store data in an ordered dictionary
        out_a = OrderedDict()
        sections_list = list(config.keys())
        for section1 in["options", "mru", "mru2", "output"] :
            if section1 in config :
                out_a[section1] = OrderedDict()
                for option in config[section1] :
                    value = config[section1][option]
                    if value == 'False' :
                        value = False
                    elif value == 'True' :
                        value = True

                    out_a[section1][option] = value
                sections_list.remove(section1)

        sections_list.sort()
        for section1 in sections_list :
            out_a[section1] = OrderedDict()
            for option in config[section1] :
                    value = config[section1][option]
                    if value == 'False' :
                        value = False
                    elif value == 'True' :
                        value = True
                    out_a[section1][option] = value

        # write data
        for section2 in out_a :
            iniFile.write("[" + section2 + "]\n")
            for option2 in out_a[section2] :
                iniFile.write(option2 + " = " + str(out_a[section2][option2]) + "\n")

        iniFile.close()




    def mru(self, filenames_a, dir_type) :
        # "mru" section is used for the most recent used files, which appear below the file menu
        # "mru2" section is used for the most recent dirs opened with the file/open menu
        #      dir_type indicates the type of directory : for files manager, or for projects.
        mrudir = ""
        if isinstance(filenames_a, dict) :
            filenames = join_list(filenames_a, "|")
            filenames = filenames.replace("\\", "/")
            if 1 in filenames_a :
                mrudir = os.path.split(filenames_a[1])[0]
        else :
            filenames = filenames_a
            mrudir = os.path.split(filenames_a)[0]

        if os.path.isfile(sfp3("pdfbooklet.cfg")) :
            configtemp = parser.read(sfp3("pdfbooklet.cfg"))
        else:
            configtemp = OrderedDict()

        if not "mru" in configtemp :
            configtemp["mru"] = {}
        if not "mru2" in configtemp :
            configtemp["mru2"] = {}

        # cancel if already present
        temp_a = []
        for index in ["mru1", "mru2", "mru3", "mru4"] :
            if index in configtemp["mru"] :
                if filenames == configtemp["mru"][index] :
                    return


        # shift mru
        if "mru3" in configtemp["mru"] :
            configtemp["mru"]["mru4"] = configtemp["mru"]["mru3"]
        if "mru2" in configtemp["mru"] :
            configtemp["mru"]["mru3"] = configtemp["mru"]["mru2"]
        if "mru1" in configtemp["mru"] :
            configtemp["mru"]["mru2"] = configtemp["mru"]["mru1"]
        # set the new value
        configtemp["mru"]["mru1"] = filenames
        configtemp["mru2"][dir_type] = mrudir
##        f = open(sfp3("pdfbooklet.cfg"),"w")
##        configtemp.write(f)
##        f.close()
        parser.write(configtemp, sfp3("pdfbooklet.cfg"))
        configtemp = None
        self.menuAdd()


    def mru_python2(self, filenames_a) :

        mrudir = ""
        if isinstance(filenames_a, dict) :              # several files selected
            filenames = join_list(filenames_a, "|")
            if 1 in filenames_a :                       # At least one file
                mrudir = os.path.split(filenames_a[1])[0]
        else :
            filenames = filenames_a
            mrudir = os.path.split(filenames_a)[0]

        #filenames = filenames.encode('utf-8')

        configtemp = parser.read(sfp3("pdfbooklet.cfg"))

        if configtemp.has_section("mru") == False :
            configtemp.add_section("mru")
        if configtemp.has_section("mru2") == False :
            configtemp.add_section("mru2")

        # cancel if already present
        temp_a = []
        for index in ["mru1", "mru2", "mru3", "mru4"] :
            if configtemp.has_option("mru",index) :
                if filenames == configtemp.get("mru",index) :
                    return

        try :
            # shift mru
            if configtemp.has_option("mru","mru3") :
                configtemp.set("mru","mru4",configtemp.get("mru","mru3"))
            if configtemp.has_option("mru","mru2") :
                configtemp.set("mru","mru3",configtemp.get("mru","mru2"))
            if configtemp.has_option("mru","mru1") :
                configtemp.set("mru","mru2",configtemp.get("mru","mru1"))
            # set the new value
##            filenames_s = filenames.encode("utf-8")
##            mrudir_s = mrudir.encode("utf-8")

            configtemp.set("mru","mru1",filenames)
            configtemp.set("mru2","mru2",mrudir)
            f = open(sfp3("pdfbooklet.cfg"),"w", encoding = "utf8")
            configtemp.write(f)
            f.close()
            configtemp = None
            self.menuAdd()
        except :
            printExcept()
            alert("problem in mru (line 700)")



    def read_mru2(self, key) :

        if os.path.isfile(sfp3("pdfbooklet.cfg")) :
            configtemp = parser.read(sfp3("pdfbooklet.cfg"))

            mru_dir = ""
            if "mru2" in configtemp :
                if key in configtemp["mru2"] :
                    mru_dir = configtemp["mru2"][key]

            configtemp = None
            return mru_dir

    def read_mru2_python2(self) :

        if os.path.isfile(sfp3("pdfbooklet.cfg")) :
            configtemp = parser.read(sfp3("pdfbooklet.cfg"))

            try :
                mru_dir = configtemp.get("mru2","mru2")
            except :
                mru_dir = ""

            configtemp = None
            return mru_dir

    def write_mru2(self, key, filename_u) :

        if os.path.isfile(sfp3("pdfbooklet.cfg")) :
            configtemp = parser.read(sfp3("pdfbooklet.cfg"))

        if not "mru2" in configtemp :
            configtemp["mru2"] = OrderedDict()

        (path_u, file_u) = os.path.split(filename_u)
        configtemp["mru2"][key] = path_u
        parser.write(configtemp, sfp3("pdfbooklet.cfg"))


    def menuAdd(self) :
        # Called by function mru, adds an entry to the menu


        configtemp = parser.read(sfp3("pdfbooklet.cfg"))
        if configtemp == False :
            return

        if "mru" in configtemp :
            for item in ["mru1", "mru2", "mru3", "mru4"] :
                if item in configtemp["mru"] :
                    filepath_list_s = configtemp["mru"][item]
                    filepath_list = filepath_list_s.split("|")
                    temp1 = []
                    for filepath_s in filepath_list :
                        filepath_s = self.FormatPath(filepath_s)
                        path_s,filename_s = os.path.split(filepath_s)
                        temp1 += [filename_s]
                    menu_entry_s = join_list(temp1, ", ")
                    if len(menu_entry_s) > 40 :
                        menu_entry_s = menu_entry_s[0:40] + "..."

                    self.mru_items[item] = [menu_entry_s, filepath_list]        # contains real path, used to open files
                    self.arw[item].set_label(menu_entry_s)                      # displayed menu text





    def pdfBooklet_doc(self, widget) :

        filename = _("Pdf-Booklet_User's_Guide.pdf")
        userGuide_s = "documentation/" + filename

        if 'linux' in sys.platform :
            # Try to find the file in standard locations
            paths_to_check = [
                os.path.join("/usr/share/pdfbooklet/documentation", filename),
                os.path.join("documentation", filename),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documentation", filename))
            ]
            
            found_path = None
            for path in paths_to_check:
                if os.path.exists(path):
                    found_path = path
                    break
            
            if found_path:
                userGuide_s = found_path
                
            subprocess.call(["xdg-open", userGuide_s])
        else:
            os.startfile(sfp(userGuide_s))


    def pdfBooklet_online_doc(self, widget) :
        webbrowser.open("https://pdfbooklet.sourceforge.io/wordpress/guide/")


    def popup_rotate(self, widget):
        # Called by popup menu (right clic on preview)
        global selected_page, rows_i


        # We get the value from the widget name (the 3 menu options use the same function)
        wname = widget.get_name()
        match = re.match("rotate(\d*)", wname)
        value = match.group(1)

        # Code below is just an adaptation of function "transormationsApply"
        if selected_page == None :
            showwarning(_("No selection"), _("There is no selected page. \nPlease select a page first. "))
            return
        # selected_page 4 and 5 contain the correct page reference, including the global rotation.
        humanReadableRow_i = rows_i - selected_page[4]
        Id = str(str(humanReadableRow_i) + "," + str(selected_page[5] + 1))

        pageId = str(selected_page[2]) + ":" + str(selected_page[3])

##        # if transformation is for this page only, use page ref instead of position ref
##        if self.thispage.get_active() == 1 :
##            Id = pageId

        if (Id in config) == False :
            config[Id] = {}
            config[Id]["htranslate"] = '0'
            config[Id]["vtranslate"] = '0'
            config[Id]["scale"] = '100'
            config[Id]["xscale"] = '100'
            config[Id]["yscale"] = '100'
            config[Id]["vflip"] = False
            config[Id]["hflip"] = False





        config[Id]["rotate"] = str(value)

        self.preview(self.previewPage, 0)



    def __________________INI_FILE() :
        pass


    def saveDefaults(self, dummy) :

        out_a = self.makeIniFile()
        iniFile = open(sfp3("pdfbooklet.cfg"), "w")
        for a in out_a :
            if not a in ["mru", "mru2", "options"] :
                continue
            iniFile.write("[" + a + "]\n")
            for b in out_a[a] :
                value = out_a[a][b]
                if value == True :
                    value = '1'
                elif value == False :
                    value = '0'
                iniFile.write(b + " = " + value + "\n")
            iniFile.write("\n")
        iniFile.close()

    def readNumEntry(self, entry, widget_s = "") :

        if sys.version_info[0] == 2 and isinstance(entry, unicode) :
                value = entry
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if value == "" : value = 0
        try :
            value = float(value)
        except :
            showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
            return None

        return value


    def readmmEntry(self, entry, widget_s = "", default = 0) :
        global adobe_l

        value = ""
        if sys.version_info[0] == 2 and isinstance(entry, unicode) :
                value = entry
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if (value == "") :
            value = default
        else :
            try :
                value = float(value) / adobe_l
            except :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        return value

    def readPercentEntry(self, entry, widget_s = "") :

        value = ""
        if sys.version_info[0] == 2 and isinstance(entry, unicode) :
                value = entry
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")
        if (value == "") :
            value = 100
        else :
            value.replace("%", "")
            try :
                value = float(value) / 100
                if value < 0 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be > 0. Aborting \n") % widget_s)
                    return None
            except :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        return value

    def readIntEntry(self, entry, widget_s = "", type_i = 0, default = "") :
        # type = 0 : accepts all values >= 0
        # type = 1 : accepts all values > 0
        # type = -1 : accepts any integer, positive or negative
        # type = 2 : optional. Don't warn if missing, but warn if invalid (not integer)

        value = ""
        if isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        value = value.replace(",", ".")


        try :
            value = int(value)
            if type_i == 0 :
                if value < 0 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be >= 0. Aborting \n") % widget_s)
                    return None
            elif type_i == 1 :
                if value < 1 :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be > 0. Aborting \n") % widget_s)
                    return None
        except :
            if value == "" :
                if type_i == 2 :
                    pass
                else :
                    showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                    return None
            else :
                showwarning(_("Invalid data"), _("Invalid data for %s - must be numeric. Aborting \n") % widget_s)
                return None
        if value == "" :
            return default
        return value

    def readBoolean(self, entry) :

        value = ""
        if sys.version_info[0] == 2 :
            if isinstance(entry, unicode) :
                value = entry
        elif isinstance(entry, str) :
            value = entry
        else :
            value = entry.get_text()
        try :
            if int(value) < 1 :
                return False
            else :
                return True
        except :
            showwarning(_("Invalid data"), _("Invalid data for %s - must be 0 or 1. Aborting \n") % widget_s)






    def readGui(self, logdata = 1) :

        global config, rows_i, columns_i, step_i, sections, output, input1, input2, adobe_l, inputFiles_a, inputFile_a
        global numfolio, prependPages, appendPages, ref_page, selection
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, mediabox_l, outputScale, refPageSize_a

        if self.freeze_b == True :
            return

        # Read the gui and update the config dictionary
        self.makeIniFile()

        outputFile = config["options"]["output"]
        outputScale = 1

        rows_i = self.readIntEntry(self.arw["entry11"], _("rows"), 1)
        #if rows_i == None : return False
        columns_i = self.readIntEntry(self.arw["entry12"], _("columns"), 1)
        #if columns_i == None : return False
        if (rows_i < 1) :
                rows_i = 1
        if (columns_i < 1) :
                columns_i = 1


        if ini.repeat == 1 :
            step_i = self.readIntEntry(self.arw["entry15"], _("step"), 1)
            if step_i == None : return False
            if (step_i < 1) :
                step_i = 1
        else :
            step_i = rows_i * columns_i



        numfolio = self.readIntEntry(self.arw["entry13"], _("folios"))
        prependPages = self.readIntEntry(self.arw["entry32"], _("Leading blank pages"))
        if prependPages == None : return False
        appendPages = self.readIntEntry(self.arw["entry33"], _("Trailing blank pages"))
        if appendPages == None : return False
        selection = self.selection_s


        if self.arw["radiosize1"].get_active() == 1 :
            radiosize = 1
        elif self.arw["radiosize2"].get_active() == 1 :
            radiosize = 2
        if self.arw["radiosize3"].get_active() == 1 :
            radiosize = 3

        referencePage = config["options"]["referencePage"]
        if referencePage.strip() == "" or referencePage == "0" :
            referencePage = "1"
        temp1 = referencePage.split(":")
        try :
            if len(temp1) == 2 :
                ref_file = int(temp1[0])
                ref_page = int(temp1[1])
            else :
                ref_file = 1
                ref_page = int(temp1[0])
        except :
            alert(_("Invalid value for reference page, please correct and try again"))
            return False
        if ref_page > 0 :
            system_ref_page = ref_page - 1          # system numbering start from 0 and not 1
        ini.output_page_size(radiosize, ref_file, system_ref_page, logdata)

        return True



    def setOption(self, option, widget, section = "options") :
        global config

        if section in config :
            if option in config[section] :
                value = config[section][option]
                z = widget.class_path()[1]
                z2 = z.split(".")
                z3 = z2[-1]
                if z3 == "GtkSpinButton" :
                    mydata = value
                    mydata = mydata.replace(",",".")
                    if mydata.strip() != "" :
                        widget.set_value(float(mydata))
                elif z3 == "GtkTextView" :
                    widget.get_buffer().set_text(value)
                elif z3 == "GtkCheckButton" :
                    try :
                        value = int(value)
                    except :
                        pass
                    if bool_test(value) == True :
                        widget.set_active(True)

                else :
                    widget.set_text(value)




    def setupGui(self, inifile = "") :

        global config, rows_i, columns_i, step_i, cells_i, input1, adobe_l
        global numfolio, prependPages, appendPages, ref_page, selection
        global numPages, pagesSel, llx_i, lly_i, urx_i, ury_i, inputFile, inputFiles_a
        global startup_b


        self.freeze_b = True            # prevent update of the display, which would trigger readGui and corrupt the data

        # set radio buttons

        if "presets" in config["options"] :
            temp1 = config["options"]["presets"]
            self.arw[temp1].set_active(True)

        if "size" in config["options"] :
            temp1 = config["options"]["size"]
            self.arw[temp1].set_active(True)

        if "presetOrientation" in config["options"] :
            temp1 = config["options"]["presetOrientation"]
            self.arw[temp1].set_active(True)

        if "globalRotation"  in config["options"] :
            temp1 = config["options"]["globalRotation"]
            self.arw[temp1].set_active(True)


        self.setOption("rows", self.arw["entry11"])
        self.setOption("columns", self.arw["entry12"])
        self.setOption("step", self.arw["entry15"])
        self.setOption("numfolio", self.arw["entry13"])
        self.setOption("prependPages", self.arw["entry32"])
        self.setOption("appendPages", self.arw["entry33"])
        self.setOption("referencePage", self.arw["entry31"])
        self.setOption("creep", self.arw["creep"])
        self.setOption("output", self.arw["entry2"])
        self.setOption("width", self.arw["outputWidth"])
        self.setOption("height", self.arw["outputHeight"])
        self.setOption("userLayout", self.arw["user_layout"])

        self.setOption("htranslate", self.arw["htranslate2"], "output")
        self.setOption("vtranslate", self.arw["vtranslate2"], "output")
        self.setOption("scale", self.arw["scale2"], "output")
        self.setOption("rotate", self.arw["rotation2"], "output")
        self.setOption("xscale", self.arw["xscale2"], "output")
        self.setOption("yscale", self.arw["yscale2"], "output")
        self.setOption("vflip", self.arw["vflip2"], "output")
        self.setOption("hflip", self.arw["hflip2"], "output")

        self.setOption("font_size", self.arw["numbers_font_size"], "page_numbers")
        self.setOption("start_from", self.arw["numbers_start_from"], "page_numbers")
        self.setOption("bottom_margin", self.arw["numbers_bottom_margin"], "page_numbers")


        # set check boxes

        if "advanced"  in config["options"] :
            if config.getint("options", "advanced") == 1 : self.advanced.set_active(1)
            else : self.advanced.set_active(0)
            self.guiAdvanced()
        if "autoscale"  in config["options"] :
            if bool_test(config["options"]["autoscale"]) == True :
                self.autoscale.set_active(1)
            else :
                self.autoscale.set_active(0)
        if "autoRotate"  in config["options"] :
            if int(config["options"]["autoRotate"]) == 1 : self.autorotate.set_active(1)
            else : self.autorotate.set_active(0)

        if "showPdf"  in config["options"] :
            if bool_test(config["options"]["showPdf"]) == True : self.arw["show"].set_active(1)
            else : self.arw["show"].set_active(0)
        if "saveSettings"  in config["options"] :
            if bool_test(config["options"]["saveSettings"]) == True : self.settings.set_active(1)
            else : self.settings.set_active(0)

        if "noCompress"  in config["options"] :
            if bool_test(config["options"]["noCompress"]) == True : self.noCompress.set_active(1)
            else : self.noCompress.set_active(0)
        if "overwrite"  in config["options"] :
            if bool_test(config["options"]["overwrite"]) == True : self.overwrite.set_active(1)
            else : self.overwrite.set_active(0)

        if "righttoleft"  in config["options"] :
            if bool_test(config["options"]["righttoleft"]) == True : self.righttoleft.set_active(1)
            else : self.righttoleft.set_active(0)
        if "slowmode"  in config["options"] :
            if bool_test(config["options"]["slowmode"]) == True : self.slowmode.set_active(1)
            else : self.slowmode.set_active(0)

        if "page_numbers" in config :
            if "page_numbers"  in config["page_numbers"] :
                if bool_test(config["page_numbers"]["page_numbers"]) == True :
                    self.arw["page_numbers"].set_active(1)
                else :
                    self.arw["page_numbers"].set_active(0)

        # set TextView

        buf = self.arw["textview1"].get_buffer()
        if "userLayout" in config["options"] :
            buf.set_text(config["options"]["userLayout"])


        self.freeze_b = False


    def makeIniFile(self, inifile = "") :
        # Reads the gui and updates config dictionary

        global config, rows_i, columns_i, step_i, cells_i, input1, adobe_l
        global numfolio, prependPages, appendPages, ref_page, selection
        global numPages, pagesSel, inputFile
        global out_a

        out_a = config

        config["options"]["rows"] = self.arw["entry11"].get_text()
        config["options"]["columns"] = self.arw["entry12"].get_text()
        config["options"]["booklet"] = str(ini.booklet)
        config["options"]["step"] = self.arw["entry15"].get_text()
        config["options"]["numfolio"] = self.arw["entry13"].get_text()
        config["options"]["prependPages"] = self.arw["entry32"].get_text()
        config["options"]["appendPages"] = self.arw["entry33"].get_text()
        config["options"]["referencePage"] = self.arw["entry31"].get_text()
        config["options"]["creep"] = self.arw["creep"].get_text()
        config["options"]["pageSelection"] = self.selection_s    # TODO : is this a good idea ?
        buf = self.arw["user_layout"].get_buffer()
        start, end  = buf.get_bounds()
        layout_s = buf.get_text(start, end, True)
        config["options"]["userLayout"] = layout_s.replace("\n", "/")

        temp1 = ""
        for key in inputFiles_a :
                val = inputFiles_a[key]
                temp1 += val + '|'

        config["options"]["inputs"] = temp1
        config["options"]["output"] = self.arw["entry2"].get_text()
        config["options"]["repeat"] = str(self.arw["entry15"].get_text())
        config["options"]["showPdf"] = str(self.arw["show"].get_active())
        config["options"]["saveSettings"] = str(self.settings.get_active())
        config["options"]["autoscale"] = str(self.autoscale.get_active())
        config["options"]["width"] = str(self.arw["outputWidth"].get_text())
        config["options"]["height"] = str(self.arw["outputHeight"].get_text())

        config["options"]["noCompress"] = str(self.noCompress.get_active())
        config["options"]["righttoleft"] = str(self.righttoleft.get_active())
        config["options"]["overwrite"] = str(self.overwrite.get_active())
        config["options"]["slowmode"] = str(self.slowmode.get_active())

        if not "output" in config :
            config["output"] = OrderedDict()
        config["output"]["htranslate"] = self.arw["htranslate2"].get_text()
        config["output"]["vtranslate"] = self.arw["vtranslate2"].get_text()
        config["output"]["scale"] = self.arw["scale2"].get_text()
        config["output"]["rotate"] = self.arw["rotation2"].get_text()
        config["output"]["xscale"] = self.arw["xscale2"].get_text()
        config["output"]["yscale"] = self.arw["yscale2"].get_text()
        config["output"]["vflip"] = self.arw["vflip2"].get_active()
        config["output"]["hflip"] = self.arw["hflip2"].get_active()

        if not "page_numbers" in config :
            config["page_numbers"] = OrderedDict()
        config["page_numbers"]["page_numbers"] = self.arw["page_numbers"].get_active()
        config["page_numbers"]["font_size"] = self.arw["numbers_font_size"].get_text()
        config["page_numbers"]["start_from"] = self.arw["numbers_start_from"].get_text()
        config["page_numbers"]["bottom_margin"] = self.arw["numbers_bottom_margin"].get_text()
##        config["output"]["yscale"] = self.arw["yscale2"].get_text()

        # radio buttons

        group = self.arw["radiopreset1"].get_group()
        for a in group :
            if a.get_active() == True :
                config["options"]["presets"] = a.get_name()

        group = self.arw["radiosize1"].get_group()
        for a in group :
            if a.get_active() == True :
                config["options"]["size"] = a.get_name()

        group = self.arw["presetOrientation1"].get_group()
        for a in group :
            if a.get_active() == True :
                config["options"]["presetOrientation"] = a.get_name()

        group = self.arw["globalRotation0"].get_group()
        for a in group :
            if a.get_active() == True :
                config["options"]["globalRotation"] = a.get_name()

        # most recently used

        # TODO : if file exists (ici et ailleurs)
        configtemp = parser.read(sfp3("pdfbooklet.cfg"))

        if "mru" in configtemp :
            for option in configtemp["mru"] :
                if "mru" in config :
                    config["mru"][option] = configtemp["mru"][option]





        return config


    def _______________________PRESETS() :
        pass


    def guiPresets(self, radiobutton = 0, event = None) :

        global startup_b, project_b, preview_b

        if radiobutton != 0 :
            if radiobutton.get_active() == 0 :  # signal is sent twice, ignore one of them
                return
        if project_b == True :  # Don't change values if we are loading a project
            return

        preview_b = False   # prevent multiple preview commands due to signals emitted by controls
        presetOrientation_i = self.arw["presetOrientation1"].get_active()

        if self.arw["radiopreset1"].get_active() == 1 : # single booklet
            if presetOrientation_i == 1 :
                self.presetBooklet(0,0)
            else :
                self.presetBooklet(0,1)
            self.guiPresetsShow("booklet")


        elif self.arw["radiopreset2"].get_active() == 1 :    # Multiple booklets
            if presetOrientation_i == 1 :
                self.presetBooklet(5,0)
            else :
                self.presetBooklet(5,1)
            self.guiPresetsShow("booklet")

        elif self.arw["radiopreset3"].get_active() == 1 :    # 2-up
            if presetOrientation_i == 1 :
                self.presetUp(1,2)
            else :
                self.presetUp(2,1)
            self.guiPresetsShow("copies")

        elif self.arw["radiopreset4"].get_active() == 1 :   # 4-up in lines
            if presetOrientation_i == 1 :
                self.presetUp(2,2,1)
            else :
                self.presetUp(2,2,1)
            self.guiPresetsShow("")

        elif self.arw["radiopreset5"].get_active() == 1 :   # 4-up in columns
            if presetOrientation_i == 1 :
                self.presetUp(2,2,2)
            else :
                self.presetUp(2,2,2)
            self.guiPresetsShow("")

        elif self.arw["radiopreset6"].get_active() == 1 :   # x copies
            if presetOrientation_i == 1 :
                self.presetCopies(1,2)
            else :
                self.presetCopies(2,1)
            self.guiPresetsShow("copies")

        elif self.arw["radiopreset7"].get_active() == 1 :  # 1 page
            if presetOrientation_i == 1 :
                self.presetMerge()
            else :
                self.presetMerge()
            self.guiPresetsShow("copies")

        elif self.arw["radiopreset8"].get_active() == 1 :   # User defined
            return      # This button launchs the function "user_defined" which will handle the request


        preview_b = True
        if radiobutton != 0 and startup_b == False :
            self.preview(self.previewPage)

    def user_defined(self, widget) :
        # Called by the "user defined" option button in the main window
        # Gets data from the dialog where user enters the user defined layout
        # Process the text from the TextView and sets controls and variables
        # then update the preview.
        # @widget : if this parameter is False, the dialog is not shown (used by OpenProject)

        global startup_b, project_b, preview_b

        preview_b = False   # prevent multiple preview commands due to signals emitted by controls
        if widget == False :
            response = 1
        else :
            dialog = self.arw["dialog2"]
            response = dialog.run()
            dialog.hide()

        if response == 0 :
            return
        if response == 1 :
            buf = self.arw["user_layout"].get_buffer()
            start, end  = buf.get_bounds()
            layout_s = buf.get_text(start, end, False)

            imposition2 = ini.parse_user_layout(layout_s)

            self.userpages = imposition2[0]
            (self.imposition, numrows, numcols, pages) = imposition2

            # set step
            if self.arw["step_defined"].get_active() == True :
                step_s = self.arw["step_value"].get_text()
                self.presetCopies(numrows,numcols,step_s)
                self.guiPresetsShow("copies")
            else :
                self.presetUp(numrows,numcols)
                self.guiPresetsShow("")

            total_pages = numrows * numcols
            if len(pages) != total_pages :
                message =_("Expected page number was : %d. Only %d found. \nThere is an error in your layout, please correct") % (total_pages, len(pages))
                alert(message)



            # Update gui before updating preview, since preview takes its data from the gui
            while Gtk.events_pending():
                        Gtk.main_iteration()

            preview_b = True
            if startup_b == False :
                self.preview(self.previewPage)

    def select_step_value(self, widget, event) :
        # launched when user types something in "step_value" entry
        # Selects the appropriate radio button
        self.arw["step_defined"].set_active(True)

    def guiPresetsShow(self, action_s) :

        StepWidgets = [self.arw["label15"], self.arw["entry15"]]
        LeafsWidgets = [self.arw["label13"], self.arw["entry13"]]
        OrientationWidgets = [self.arw["label11"], self.arw["presetOrientation1"],
                              self.arw["label12"], self.arw["presetOrientation2"]]


        for a in StepWidgets + LeafsWidgets + OrientationWidgets :
            a.hide()

        if action_s == "booklet" :
            for a in LeafsWidgets + OrientationWidgets :
                a.show()

        if action_s == "copies" :
            for a in StepWidgets + OrientationWidgets :
                a.show()


    def presetBooklet(self, leafs_i, orientation) :
        if orientation == 0 :
            self.arw["entry11"].set_value(1)                    # rows
            self.arw["entry12"].set_value(2)                    # columns
        else :
            self.arw["entry11"].set_value(2)                    # rows
            self.arw["entry12"].set_value(1)                    # columns
        self.arw["entry13"].set_text(str(leafs_i))              # leafs in booklet
        ini.repeat = 0
        ini.booklet = 1

    def presetUp(self, r,c,l=1) :
        self.arw["entry11"].set_value(r)                    # rows
        self.arw["entry12"].set_value(c)                    # columns
        ini.booklet = 0                          # checkerboard
        ini.radioDisp = l                        # lines / columns
        ini.repeat = 0

    def presetCopies(self, r,c, step="1") :
        global step_i
        self.arw["entry11"].set_value(r)                    # rows
        self.arw["entry12"].set_value(c)                    # columns
        ini.booklet = 0                          # checkerboard
        ini.repeat = 1
        self.arw["entry15"].set_text(step)                   # step

    def presetCopies2(self, r,c,l=1) :
        self.arw["entry11"].set_value(r)                    # rows
        self.arw["entry12"].set_value(c)                    # columns
        ini.booklet = 0                          # checkerboard
        ini.radioDisp = l                        # lines / columns
        ini.repeat = 0


    def presetMerge(self) :                     # One page
        global outputFile, inputFile_a

        self.arw["entry11"].set_value(1)                    # rows
        self.arw["entry12"].set_value(1)                    # columns
        ini.booklet = 0                          # checkerboard
        ini.repeat = 0

    def _________________________PREVIEW() :
        pass

    def OnDraw(self, area, cr):
        global page
        global areaAllocationW_i, areaAllocationH_i
        global previewColPos_a, previewRowPos_a, pageContent_a
        global refPageSize_a, numPages
        global outputStream, outputStream_mem

        # Was the size changed ?

        if (areaAllocationW_i == self.area.get_allocated_width()
            and areaAllocationH_i  == self.area.get_allocated_height()) :
                nochange_b = True
        else :
            nochange_b = False
            areaAllocationW_i = self.area.get_allocated_width()
            areaAllocationH_i  = self.area.get_allocated_height()


        # If nothing has not yet been loaded, show nofile.pdf
        try :
            data1 = outputStream.getvalue()
        except :
            f1 = open(sfp2("data/nofile.pdf"),"rb")
            data1 = f1.read()
            f1.close()


        # TODO : When two calls are too close, it may create a strange stack resulting in an empty OutputStream
        #        This has to be redesigned.
        if len(data1) == 0 :
            #print(".........  OutputStream is empty")
            return

        # If the preview has not changed, don't render
        # TODO : This must be redesigned, because with the image in memory, it may be necessary to render again with the same data
##        if data1 == outputStream_mem :
##            return
##        else :
##            outputStream_mem = data1

        try :
            bytes_data = GLib.Bytes(data1)
            input_stream = Gio.MemoryInputStream.new_from_bytes(bytes_data)
            # Take care that you need to call .close() on the Gio.MemoryInputStream once you're done with your pdf document.
            document = Poppler.Document.new_from_stream(input_stream, -1, None, None)
            self.document= document

        except :
            # bug workaround
            """
            Hi there, I installed the deb on Ubuntu 19.04. It installed fine but gives this message:

            Traceback (most recent call last):
               File "/usr/local/lib/python3.7/dist-packages/pdfbooklet/pdfbooklet.py", line 2342, in OnDraw
                document = Poppler.Document.new_from_stream(input_stream, -1, None, None)
             gi.repository.GLib.GError: poppler-quark: Failed to load document (0)

            The preview panel remains blank but when I press the Go button the .bklt file is produced correctly. I get the same if I download the tar and install manually. Also the same with many different input pdf files.
            """
            try:
                filepath = os.path.join(tempfile.gettempdir(), "preview.pdf")
                with open(filepath, "wb") as f1:
                    f1.write(data1)
                document = Poppler.Document.new_from_file("file:///" + filepath, None)
                self.document= document
            except:
                print("Error rendering document in poppler")
                printExcept()
                return False

        x = document.get_n_pages()
        if x == 0:
            return

        page = document.get_page(0)
        self.page = page

        if x > 1 :
            self.page1 = document.get_page(1)
        else :
            self.page1 = None

        # calculate the preview size

        pix_w, pix_h = page.get_size()

        A = int((areaAllocationH_i * pix_w) / pix_h)    # width of preview if full height
        B = int((areaAllocationW_i * pix_h) / pix_w)    # height of preview if full width


        if A < areaAllocationW_i :                      # if full height is OK
            heightPoints = areaAllocationH_i
            widthPoints = A
            scale = areaAllocationH_i / pix_h
        else :
            widthPoints = areaAllocationW_i
            heightPoints = B
            scale = areaAllocationW_i / pix_w

        self.preview_scale = scale          # this will be needed for drag (see the end_drag function)
        Hoffset_i = int((areaAllocationW_i - widthPoints) /2)
        Voffset_i = int((areaAllocationH_i - heightPoints)/2)

        # set background.
        cr.set_source_rgb(0.7, 0.6, 0.5)
        cr.paint()

        # set page background
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(Hoffset_i, Voffset_i, widthPoints, heightPoints)

        cr.fill()

        # render page

        cr.save()
        cr.translate(Hoffset_i, Voffset_i)
        cr.scale(scale,scale)
        self.page.render(cr)
        cr.restore()

        # If there are two pages in the preview, the second will be printed over the other
        # to help fine tuning the margins for duplex printing

        if self.page1 :
            cr.save()
            cr.translate(Hoffset_i, Voffset_i)
            cr.scale(scale,scale)
            self.page1.render(cr)
            cr.restore()

        # clear memory
        input_stream.close()


        # draw middle line

        if ((ini.booklet > 0 and len(inputFiles_a) > 0)
            or self.arw["draw_middle_line"].get_active() == True) :
            cr.save()
            cr.set_line_width(1)
            cr.set_dash((10,8))
            cr.set_source_rgb(0.5, 0.5, 1)
            line_position = (areaAllocationW_i/2) + 0.5         # The reason for + 0.5 is explained here : https://www.cairographics.org/FAQ/#sharp_lines
                                                                # under the title : How do I draw a sharp, single-pixel-wide line?
            cr.move_to(line_position, Voffset_i)
            cr.line_to(line_position, (areaAllocationH_i - Voffset_i ))
            cr.stroke()
            cr.restore()


        # if the output is turned, swap the numbers of rows and columns
        if app.arw["globalRotation90"].get_active() == 1 \
          or  app.arw["globalRotation270"].get_active() == 1:
            preview_cols = rows_i
            preview_rows = columns_i
        else :
            preview_cols = columns_i
            preview_rows = rows_i


        columnWidth = widthPoints / preview_cols
        rowHeight = heightPoints / preview_rows

        #store position of columns and rows
        # previewColPos_a will contain the position of the left of all columns (from left to right)
        # previewRowPos_a will contain the position of the top of all rows (from bottom to top)
        previewColPos_a = []
        previewRowPos_a = []
        previewPagePos_a = {}


        for a1 in range(preview_cols) :
            #left of the column
            previewColPos_a += [int((a1 * columnWidth) + Hoffset_i)]
        for a2 in range(preview_rows) :
            #top of the row
            # rows count starts from bottom => areaAllocationH_i - ...
            previewRowPos_a += [areaAllocationH_i - (int((a2 * rowHeight) + Voffset_i ))]
        # add the right pos of the last col
        previewColPos_a += [int(previewColPos_a[a1] + columnWidth)]
        previewRowPos_a += [int(previewRowPos_a[a2] - rowHeight)]


        # show page numbers
        i = 0
        pageContent_a = {}


        for a in self.rotate_layout() :     # returns the layout, rotated if necessary

            # human readable page number
            pageRef_s = self.ar_pages[0][i]
            file_number, page_number = pageRef_s.split(":")
            page_number = int(page_number) + 1
            if file_number == "1" :
                pageNumber = str(page_number)
            else :
                pageNumber = str(file_number) + ":" + str(page_number)


            fontsize_i = int(columnWidth / 4)
            if fontsize_i < 10 :
                fontsize_i = 10
            colpos_i = previewColPos_a[a[1]] + (columnWidth / 2)
            rowpos_i = previewRowPos_a[a[0]] - (rowHeight / 2)
            x1,x2 = colpos_i,rowpos_i

            # draw page number
            if self.arw["hide_numbers"].get_active() == 0 :
                # TODO cr.select_font_face("Georgia",
    ##                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ##            AttributeError: 'gi.repository.cairo' object has no attribute 'FONT_SLANT_NORMAL'
    ##            Remplacé par 0 et 1 ci-dessous
                cr.select_font_face("Georgia", 0, 1)
                cr.set_font_size(fontsize_i)
                x_bearing, y_bearing, txtWidth, txtHeight = cr.text_extents(pageNumber)[:4]

                colpos_i -= int(txtWidth / 4)
                rowpos_i -= int(txtHeight / 4)


                cr.move_to(colpos_i, rowpos_i - y_bearing)
                cr.set_source_rgba(1, 0, 0, 0.6)
                cr.show_text(pageNumber)

            pageId = str(a[0]) + ":" + str(a[1])
            pageContent_a[pageId] = [file_number, page_number]

            # page position
            bottom = previewRowPos_a[a[0]]
            top = previewRowPos_a[a[0]] - rowHeight
            left = previewColPos_a[a[1]]
            right = previewColPos_a[a[1]] + columnWidth



            # draw rectangle if selected
            humanReadableRow_i = (preview_rows - a[0])
            pagePosition_a = [humanReadableRow_i, a[1] + 1]
            pagePosition_s = self.rotate_position(pagePosition_a)
            pageNumber_s = str(file_number) + ":" + str(page_number)
            draw_page_b = False
            type_s = ""

            # is this page odd or even ?
            if self.arw["evenpages"].get_active() == 1 :
                if int(pageNumber) % 2 == 0 :
                    cr.set_source_rgb(0, 0, 1)
                    draw_page_b = True
                    type_s = "even"

            elif self.arw["oddpages"].get_active() == 1 :
                if int(pageNumber) % 2 == 1 :
                    cr.set_source_rgb(0, 0, 1)
                    draw_page_b = True
                    type_s = "odd"

            # if page is selected
            elif pagePosition_s in selectedIndex_a :
                # Select the rectangle color
                cr.set_source_rgb(1, 0, 0)
                draw_page_b = True
                type_s = "select"


            elif pageNumber_s in selectedIndex_a :
                # Select the rectangle color
                cr.set_source_rgb(0, 0.7, 0)
                draw_page_b = True
                type_s = "select"




            # draw rectangle
            if draw_page_b == True :

                if hasattr(self, 'myselectedpage') and self.myselectedpage and ":" in self.myselectedpage:
                    try:
                        file_number, page_number = self.myselectedpage.split(":")
                        # selected_ref = file_number + ":" + str(int(page_number) - 1) # Unused?
        
        
                        coord = [left, top]
                        cr.set_line_width(3)
                        cr.rectangle(coord[0], coord[1],  columnWidth, rowHeight)
                        cr.stroke()
                    except: pass


            i += 1


        # Show page size and total pages number
##        cr.select_font_face("Arial", 0, 1)
            # TODO Anciennement cr.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            # mais les attributs ne marche plus.
##        cr.set_font_size(12)
        try :
            message = str(round(refPageSize_a[0] * adobe_l))
            message += " x " + str(round(refPageSize_a[1] * adobe_l))
            message += " - " + str(numPages) + " pages"
##            x_bearing, y_bearing, txtWidth, txtHeight = cr.text_extents(message)[:4]
##            cr.move_to(20,20)
##            cr.set_source_rgb(0, 0.6, 0)
##            cr.show_text(message)
            self.arw["info_fichier"].set_text(message)
        except :
            pass        # if refPageSize is not defined, error



    def rotate_layout(self) :
        rotated_layout= []
        for i in range (len(self.ar_layout)) :
            r, c = self.ar_layout[i]

            # Flip columns or rows if vertical or horizontal flip is selected
            if app.arw["vflip2"].get_active() == 1 :
                r = (rows_i - 1) - r
            if app.arw["hflip2"].get_active() == 1 :
                c = (columns_i - 1) - c

            # if output page is rotated (global rotation)
            if app.arw["globalRotation270"].get_active() == 1 :
                # invert row; We use columns_i because when rotated 90°,
                # the numbers of rows of the preview is the number of columns of the page
                r = (rows_i - 1) - r
                r,c = c,r       # swap

            elif app.arw["globalRotation90"].get_active() == 1 :
                # invert column; ; We use rows_i because when rotated 90°,
                # the numbers of columns of the preview is the number of rows of the page
                c = (columns_i - 1) - c
                r,c = c,r       # swap

            elif app.arw["globalRotation180"].get_active() == 1 :
                # invert row and column
                r = (rows_i - 1) - r
                c = (columns_i - 1) - c


            rotated_layout.append([r,c])
        return rotated_layout



    def rotate_position(self, position) :

##        print( "source : ", position)
        r, c = position
        # if output page is rotated (global rotation)
        if app.arw["globalRotation270"].get_active() == 1 :
            # invert row; We use columns_i because when rotated 90°,
            # the numbers of rows of the preview is the number of columns of the page
            r = (columns_i + 1) - r
            r,c = c,r       # swap

        elif app.arw["globalRotation90"].get_active() == 1 :
            # invert column; ; We use rows_i because when rotated 90°,
            # the numbers of columns of the preview is the number of rows of the page
            c = (rows_i + 1) - c
            r,c = c,r       # swap

        elif app.arw["globalRotation180"].get_active() == 1 :
            # invert row and column
            r = (rows_i + 1) - r
            c = (columns_i  +1) - c

##        print ("dest : ", str(r) + "," + str(c))

        return str(r) + "," + str(c)



    def selectPage (self, widget, event=None):
        # Called by a click on the preview or on the radio buttons, this function will :
        #   - Select the appropriate Id
        #   - launch area_expose to update the display
        #   - fill in the gtkEntry widgets which contains the transformations
        #
        # The selected_page list contains a list of six values :
        #   - row and column (Pdf format)
        #   - file number and page number
        #   - row and column if the output page is rotated

        global previewColPos_a, previewRowPos_a, canvasId20, pageContent_a
        global selectedIndex_a, selected_page, selected_pages_a, pageId


        if event == None :                  # Click on a radio button
            if self.thispage.get_active() == 1 :
                pageId = str(selected_page[2]) + ":" + str(selected_page[3])
                Id = pageId
            elif self.evenpages.get_active() == 1 :
                Id = "even"
            elif self.oddpages.get_active() == 1 :
                Id = "odd"
            else :         # first button, pages in this position
                humanReadableRow_i = rows_i - selected_page[4]
                Id = str(str(humanReadableRow_i) + "," + str(selected_page[5] + 1))
                Id = str(str(selected_page[5] + 1) + "," + str(humanReadableRow_i))

        elif event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == 3 :            # right click, runs the context menu
                self.arw["contextmenu1"].popup(None, None, None, None, event.button, event.time)
                return

            else :
                # get preview area
                left_limit = previewColPos_a[0]
                bottom_limit = previewRowPos_a[-1]
                right_limit = previewColPos_a[-1]
                top_limit = previewRowPos_a[0]

                xpos = event.x
                ypos = event.y

                self.initdrag = [xpos, ypos]        # Will be used for moving page with the mouse
                self.preview_limits = [left_limit, right_limit, top_limit, bottom_limit]

                # check if click is inside preview
                if (xpos < left_limit
                    or xpos > right_limit
                    or ypos < bottom_limit
                    or ypos > top_limit) :

                        return

                # find the row and column
                for c in range(len(previewColPos_a)) :
                    if xpos > previewColPos_a[c] and xpos < previewColPos_a[c + 1]:
                        leftPos_i = previewColPos_a[c]
                        rightPos_i = previewColPos_a[c + 1]
                        break


                for r in range(len(previewRowPos_a)) :
                    if ypos < previewRowPos_a[r] and ypos > previewRowPos_a[r + 1]:
                        bottomPos_i = previewRowPos_a[r]
                        topPos_i = previewRowPos_a[r + 1]
                        break

                r1 = r
                c1 = c

                # it should be possible to use rotate_layout

                # Flip columns or rows if vertical or horizontal flip is selected
##                if app.arw["vflip2"].get_active() == 1 :
##                    r1 = (rows_i - 1) - r
##                if app.arw["hflip2"].get_active() == 1 :
##                    c1 = (columns_i - 1) - c

                # if output page is rotated (global rotation)
                if app.arw["globalRotation90"].get_active() == 1 :
                    # invert row; We use columns_i because when rotated 90°,
                    # the numbers of rows of the preview is the number of columns of the page
                    r1 = (columns_i - 1) - r1
                    r1,c1 = c1,r1       # swap

                elif app.arw["globalRotation270"].get_active() == 1 :
                    # invert column; ; We use rows_i because when rotated 90°,
                    # the numbers of columns of the preview is the number of rows of the page
                    c1 = (rows_i - 1) - c1
                    r1,c1 = c1,r1       # swap

                elif app.arw["globalRotation180"].get_active() == 1 :
                    # invert row and column
                    r1 = (rows_i - 1) - r1
                    c1 = (columns_i - 1) - c1

                selected_page = [r, c]
                selected_page += pageContent_a[str(r)  + ":"  + str(c)]
                selected_page += [r1, c1]


                # Selection information
                self.myselectedpage = str(selected_page[2]) + ":" + str(selected_page[3])
                if self.thispage.get_active() == 1 :        # This page
                    Id = self.myselectedpage
                elif self.evenpages.get_active() == 1 :     # even pages
                    Id = "even"
                elif self.oddpages.get_active() == 1 :      # odd pages
                    Id = "odd"
                else :                                      # first button, pages in this position
                    humanReadableRow_i = rows_i - selected_page[4]
                    Id = str(str(humanReadableRow_i) + "," + str(selected_page[5] + 1))



                if event.state != Gdk.ModifierType.CONTROL_MASK :        # If Control not pressed, delete previous selection
                    selectedIndex_a = {}
                    selected_pages_a = []

                # position reference
                selectedIndex_a[Id] = 1
                selected_pages_a.append(selected_page)


                # force the "draw" signal to update the display
                self.arw["drawingarea1"].hide()
                self.arw["drawingarea1"].show()






        else :              # unsupported event
            return

        # Load settings in transformation dialogs
        if event.state != Gdk.ModifierType.CONTROL_MASK :       # but only if CONTROL is not pressed
            self.load_settings_in_dialog(Id)


    def load_settings_in_dialog(self, Id) :


            # defaults
            self.arw["htranslate1"].set_text("0")
            self.Vtranslate1.set_text("0")
            self.scale1.set_text("100")
            self.rotation1.set_text("0")
            self.arw["xscale1"].set_text("100")
            self.arw["yscale1"].set_text("100")
            self.arw["vflip1"].set_active(False)
            self.arw["hflip1"].set_active(False)


            if Id in config :
                if "htranslate" in config[Id] :
                    self.arw["htranslate1"].set_text(str(config[Id]["htranslate"]))
                if "vtranslate" in config[Id] :
                    self.Vtranslate1.set_text(str(config[Id]["vtranslate"]))
                if "scale" in config[Id] :
                    self.scale1.set_text(str(config[Id]["scale"]))
                if "rotate" in config[Id] :
                    self.rotation1.set_text(str(config[Id]["rotate"]))
                if "xscale" in config[Id] :
                    self.arw["xscale1"].set_text(str(config[Id]["xscale"]))
                if "yscale" in config[Id] :
                    self.arw["yscale1"].set_text(str(config[Id]["yscale"]))

                if "vflip" in config[Id] :
                    bool_b = config[Id]["vflip"]
                    if bool_b == "True" or bool_b == True or bool_b == "1" :           # when parameter comes from the ini file, it is a string
                        bool_b = 1
                    elif bool_b == "False" or bool_b == False or bool_b == "0" :
                        bool_b = 0
                    self.arw["vflip1"].set_active(bool_b)
                if "hflip" in config[Id] :
                    bool_b = config[Id]["hflip"]
                    if bool_b == "True" or bool_b == True or bool_b == "1" :           # when parameter comes from the ini file, it is a string
                        bool_b = 1
                    elif bool_b == "False" or bool_b == False or bool_b == "0" :
                        bool_b = 0

                    self.arw["hflip1"].set_active(bool_b)


    def drag_motion(self, widget, cr, x, y, time) :
        # unused
        # To activate, connect the signal "drag-motion" of then eventbox parent of drawingarea1
        # to this function
        print (x)
        cr.set_line_width(1)
        cr.rectangle(x, y,  2, 2)
        cr.stroke()
        return False


    def set_even_odd_settings(self, widget) :    # launched by a clic on the domain buttons
        global selected_page, selectedIndex_a
        #print ("set even odd")
        if self.evenpages.get_active() == 1 :
            Id = "even"
            selected_page = Id
            self.load_settings_in_dialog(Id)
        elif self.oddpages.get_active() == 1 :
            Id = "odd"
            selected_page = Id
            self.load_settings_in_dialog(Id)
        else :
            #print ("reset selection")
            selected_page = None
            selectedIndex_a = {}
        self.previewUpdate()



    def end_drag(self, widget, event) :
        global outputScale

        # Thisfunction will move the page when the mouse button is released
        x = event.x
        y = event.y

        # scaling factor
        if self.arw["autoscale"].get_active() == 1 :
            scaling_factor = self.preview_scale * outputScale
        else :
            scaling_factor = self.preview_scale


        scaling_factor2 = scaling_factor / adobe_l

        hmove = ((x - self.initdrag[0]) / scaling_factor2)
        vmove = ((y - self.initdrag[1]) / scaling_factor2)

        if self.arw["move_with_mouse"].get_active() == 1 :

            # Calculate the scaling factor

            temp = self.arw["htranslate1"].get_text()
            temp = temp.replace(",", ".")
            temp = float(temp)
            temp += hmove
            temp = str(temp).split(".")
            temp = temp[0] + "." + temp[1][0:1]
            self.arw["htranslate1"].set_text(temp)
            self.transformationsApply("")

            temp = self.arw["vtranslate1"].get_text()
            temp = temp.replace(",", ".")
            temp = float(temp)
            temp -= vmove
            temp = str(temp).split(".")
            temp = temp[0] + "." + temp[1][0:1]
            self.arw["vtranslate1"].set_text(temp)
            self.transformationsApply("")

        elif self.arw["delete_rectangle"].get_active() == 1 :
            # preview_limits gives : left x,  right x, bottom y, top y, in pixels.
            #
            # init_drag gives : x, y
            # x = horizontal position
            left = self.preview_limits[0] # left margin
            top = self.preview_limits[3] # top margin


            x1 = (self.initdrag[0] - left)       # start drag
            y1 = self.initdrag[1]
            y1 = self.preview_limits[2] - y1        # invert the vertical position, because Pdf counts from bottom
                                                    # This corrects also the top margin because bottom y = page height + margin
            x2 = x - left        # end drag
            y2 = y
            y2 = self.preview_limits[2] - y2
            width = x2 - x1
            height = y2 - y1
            x1 = x1 / scaling_factor
            y1 = y1 / scaling_factor
            width = width / scaling_factor
            height = height / scaling_factor
            ini.delete_rectangle = [x1,y1,width,height]

        elif self.arw["divide"].get_active() == 1 :
            # preview_limits gives : left x,  right x, bottom y, top y, in pixels.
            #
            # init_drag gives : x, y
            # x = horizontal position
            left = self.preview_limits[0] # left margin
            top = self.preview_limits[3] # top margin


            x1 = (self.initdrag[0] - left)       # start drag
            y1 = self.initdrag[1]
            y1 = self.preview_limits[2] - y1        # invert the vertical position, because Pdf counts from bottom
                                                    # This corrects also the top margin because bottom y = page height + margin
            x2 = x - left        # end drag
            y2 = y
            y2 = self.preview_limits[2] - y2
            width = x2 - x1
            height = y2 - y1
            x1 = x1 / scaling_factor
            y1 = y1 / scaling_factor
            width = width / scaling_factor
            height = height / scaling_factor
            ini.delete_rectangle = [x1,y1,width,height]



    def createSelection(self) :
        global inputFiles_a
        i = 1
        x = []
        for f in inputFiles_a :
            fileName = inputFiles_a[f]
            numPages = len(inputFile_a[fileName].pages)
            for z in range(numPages) :
                pageRef_s = str(i) + ":" + str(z)
                if pageRef_s + "deleted" in deletedIndex_a :
                    if deletedIndex_a[pageRef_s + "deleted"] == 1 :
                        pass
                    else :
                        x += [pageRef_s]
                else :
                    x += [pageRef_s]
            i += 1
        self.selection_s = self.compressSelection(x)

    def compressSelection(self, x) :
        if not x:
            return ""
        i = 0
        temp = {}
        out = ""
        for a in x :
            b = a.split(":")
            if len(b) == 1 :
                npage = b[0]
                nfile = 1
            else :
                npage = b[1]
                nfile = b[0]

            if i == 0 :
                temp["file"] = nfile
                temp["first"] = npage
                temp["last"] = npage
            else :
                if nfile == temp["file"] and int(npage) == int(temp["last"]) + 1  :
                    temp["last"] = npage            # on continue
                else :                              # sinon on écrit
                    if temp["first"] == "-1":
                        out += "b"
                    else :
                        out += str(temp["file"]) + ":" + str(temp["first"])
                        if temp["last"] != temp["first"] :
                            out += "-" + str(temp["last"])
                    out += "; "
                    # et on mémorise
                    temp["file"] = nfile
                    temp["first"] = npage
                    temp["last"] = npage
            i += 1

        if temp["first"] == "-1":
            out += "b"
        else :
            out += str(temp["file"]) + ":" + str(temp["first"])
        if temp["last"] != temp["first"] :
            out += "-" + str(temp["last"])

        # compress blank pages
        temp1 = out.split(";")
        out = ""
        blank_count = 0
        for a in temp1 :
            if a.strip() == "b" :
                blank_count += 1
            else :
                if blank_count > 0 :
                    out += str(blank_count) + "b;"
                    blank_count = 0
                out += a + ";"
        if blank_count > 0 :
            out += str(blank_count) + "b"

        return out

    def edit_selection(self, widget) :
        dialog = self.arw["dialog1"]
        TextBuffer = self.arw["textview1"].get_buffer()
        selection1 = self.selection_s.replace(";","\n")
        TextBuffer.set_text(selection1)
        choice = dialog.run()
        if choice == 1 :
            start_iter = TextBuffer.get_start_iter()
            end_iter = TextBuffer.get_end_iter()
            selection2 = TextBuffer.get_text(start_iter, end_iter, False)
            selection2 = selection2.replace("\n",";")
            self.selection_s = selection2
            if self.arranger_view:
                self.arranger_view.model.clear()
                self.arranger_view.pdfqueue = []
                self.arranger_view.nfile = 0
                self.loadShuffler()
                # TODO : N'est à faire que si la liste des fichiers a changé
                self.arranger_view.rendering_thread.pdfqueue = self.arranger_view.pdfqueue
        dialog.hide()
        self.previewUpdate()


    def compare_files_selection(self,widget) :
        # Create a selection to display two or more files side by side

        # Number of files and pages
        files_data = {}
        index = 1
        maxPages = 0
        numFiles = len(inputFiles_a)
        for f in inputFiles_a :
            fileName = inputFiles_a[f]
            numPages = len(inputFile_a[fileName].pages)
            if numPages > maxPages :
                maxPages = numPages
            files_data[index] = numPages
            index += 1

        # create the selection
        index = 1
        text = ""
        for i in range(maxPages) :
            temp = []
            for j in range(1, numFiles + 1) :
                if files_data[j] > i :              # if the file is shorter, insert blank pages
                    temp.append(str(j) + ":" + str(i))
                else :
                    temp.append("b")
            text += ",".join(temp) + "\n"

        TextBuffer = self.arw["textview1"].get_buffer()
        TextBuffer.set_text(text)


    def preview(self, previewPage, delete = 1) :


        global mediabox_l0, columns_i, rows_i, step_i, urx_i, ury_i, mediabox_l
        global outputScale, pageContent_a
        global selectedIndex_a, deletedIndex_a
        global areaAllocationW_i, areaAllocationH_i
        
        
        if preview_b == False :
            return



        if self.readGui(0) :
            self.manage_backup()
            if self.render.parsePageSelection() :
                #self.readConditions()
                ar_pages, ar_layout, ar_cahiers = self.render.createPageLayout(0)
                if ar_pages != None :
                    if previewPage > len(ar_pages) - 1 :
                        previewPage = len(ar_pages) - 1
                        self.previewPage = previewPage
                    self.arw["previewEntry"].set_text(str(previewPage + 1))
                    mem = ar_pages[previewPage]
                    try :
                        mem1 = ar_pages[previewPage + 1]
                    except :                # If we are arrived at the last page
                        pass
                    ar_pages = {}
                    ar_pages[0] = mem

                    # If previewing of two pages one over the other is requested
                    if 1 == 2 :
                        ar_pages[1] = mem1

                    self.ar_pages = ar_pages
                    self.ar_layout = ar_layout
                    
                    if self.render.createNewPdf(ar_pages, ar_layout, ar_cahiers, "", previewPage) :

                        # force the "draw" signal to update the display
                        self.arw["drawingarea1"].hide()
                        self.arw["drawingarea1"].show()


    PAPER_SIZES = {
        "A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420),
        "A4": (210, 297), "A5": (148, 210), "A6": (105, 148), "A7": (74, 105),
        "A8": (52, 74), "A9": (37, 52), "A10": (26, 37),
        "B0": (1000, 1414), "B1": (707, 1000), "B2": (500, 707), "B3": (353, 500),
        "B4": (250, 353), "B5": (176, 250), "B6": (125, 176), "B7": (88, 125),
        "B8": (62, 88), "B9": (44, 62), "B10": (31, 44),
        "C0": (917, 1297), "C1": (648, 917), "C2": (458, 648), "C3": (324, 458),
        "C4": (229, 324), "C5": (162, 229), "C6": (114, 162), "C7": (81, 114),
        "C8": (57, 81), "C9": (40, 57), "C10": (28, 40),
        "Letter": (216, 279), "Legal": (216, 356), "Tabloid": (279, 432),
        "Ledger": (432, 279), "Executive": (184, 267), "Folio": (210, 330),
        "Quarto": (215, 275), "Statement": (140, 216), "A4_Landscape": (297, 210),
        "Letter_Landscape": (279, 216), "HalfLetter": (139.7, 215.9)
    }

    def on_radiosize_toggled(self, widget):
        is_user_defined = widget.get_active()
        self.arw["outputSizeDropdown"].set_sensitive(is_user_defined)
        if is_user_defined:
             self.output_page_size(3) # 3 is user defined
        
    def on_output_size_changed(self, widget):
        active_id = widget.get_active_id()
        if active_id in self.PAPER_SIZES:
            self.updating_from_dropdown = True
            width, height = self.PAPER_SIZES[active_id]
            self.arw["outputWidth"].set_text(str(height))
            self.arw["outputHeight"].set_text(str(width))
            self.updating_from_dropdown = False
            self.previewUpdate(widget)

    def on_output_dimension_changed(self, widget):
        if not self.updating_from_dropdown:
            # Check if current values match the selected preset
            active_id = self.arw["outputSizeDropdown"].get_active_id()
            if active_id and active_id != "preset_placeholder":
                try:
                    current_width = float(self.arw["outputWidth"].get_text())
                    current_height = float(self.arw["outputHeight"].get_text())
                    preset_width, preset_height = self.PAPER_SIZES[active_id]
                    epsilon = 0.01
                    if abs(current_width - preset_height) > epsilon or abs(current_height - preset_width) > epsilon:
                         self.arw["outputSizeDropdown"].set_active_id("preset_placeholder")
                except ValueError:
                    self.arw["outputSizeDropdown"].set_active_id("preset_placeholder")

    def preview_keys(self, widget, event = None) :
        print ( "==========>>", event)

    def previewNext(self, dummy, event=None) :
        global selected_page, selectedIndex_a
        if event.state != Gdk.ModifierType.CONTROL_MASK :
            selected_page = None
            selectedIndex_a = {}
        self.previewPage += 1
        self.arw["previewEntry"].set_text(str(self.previewPage + 1))
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview

    def previewPrevious(self, dummy, event = None) :
        global selected_page, selectedIndex_a
        if event.state != Gdk.ModifierType.CONTROL_MASK :
            selected_page = None
            selectedIndex_a = {}
        self.previewPage -= 1
        if self.previewPage < 0 :
            self.previewPage = 0
        self.arw["previewEntry"].set_text(str(self.previewPage + 1))
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview

    def previewFirst(self, widget) :
        global selected_page, selectedIndex_a
        selected_page = None
        selectedIndex_a = {}
        self.previewPage = 0
        self.arw["previewEntry"].set_text(str(self.previewPage + 1))
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview

    def previewLast(self, widget) :
        global selected_page, selectedIndex_a
        selected_page = None
        selectedIndex_a = {}
        self.previewPage = 1000000    # CreatePageLayout will substitute the right number
        self.arw["previewEntry"].set_text(str(self.previewPage + 1))
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview

    def previewUpdate(self, Event = None, mydata = None) :
        global inputFiles_a

        if len(inputFiles_a) == 0 :
            #showwarning(_("No file loaded"), _("Please select a file first"))
            return False
        if Event != None :
            value_s = self.arw["entry11"].get_text()
            value2_s = self.arw["entry12"].get_text()
            if value_s != "" and value2_s != "" :
                previewPage = self.arw["previewEntry"].get_text()
                if previewPage != "" :
                    self.preview(int(previewPage) - 1)
                return
            else :
                return
##        self.preview(self.previewPage)
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview




    def previewDelayedUpdate(self, event) :     # Unused : does not work
        return
        print("previewUpdateDelayed")
        try :
            self.t1.cancel()
        except :
            pass
        self.t1 = threading.Timer(1, self.previewUpdate, [event])
        self.t1.start()
        print("timer démarré")

    def preview2(self, widget) :
        global selected_page
        selected_page = None
        previewPage = int(widget.get_text())
        self.previewPage = previewPage - 1
        self.arw["previewEntry"].set_text(str(self.previewPage + 1))
        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview

    def manage_backup(self) :
        return
        if self.backup_command == False :
            self.backup_command = True
            return
        if len(self.backup) == 0 :
            self.backup.append(copy.deepcopy(config))
            self.backup_index = len(self.backup)
        else :
            last = self.backup[-1]
            a = repr(config)
            b = repr(last)
            if a == b :
                return
            else :
                self.backup.append(copy.deepcopy(config))
                #print (len(self.backup))
                self.backup_index = len(self.backup)

    def go_back(self, widget) :
        config = copy.deepcopy(self.backup[self.backup_index - 2])
        self.setupGui()
        self.backup_command = False

    def _____________________SHUFFLER() :
        pass


    def runPS(self, widget=None) :
        global inputFiles_a, pagesSel

        if len(inputFiles_a) == 0 :
            showwarning(_("No selection"), _("There is no selected file. \nPlease select a file first. "))
            return
        if self.arranger_view == None :
            self.arranger_view = EmbeddedPdfArranger()
            # USE THE ACTIVE WINDOW (Handles Handy replacement)
            self.arranger_view_window = self.arranger_view.window 
            self.arranger_view.uiXML.get_object('menubar').hide()
            self.arranger_view.uiXML.get_object('toolbar1').hide()
            #self.arranger_view.uiXML.get_object('menu1_RR').hide()
            #self.arranger_view.uiXML.get_object('menu1_RL').hide()
            self.arranger_view.uiXML.get_object('menu1_crop').hide()
            shufflerBB = self.arw['shufflerbuttonbox']
            shufflerBB.unparent()
            vbox = self.arranger_view.uiXML.get_object('vbox1')
            vbox.pack_start(shufflerBB, False, True, 0)

            self.loadShuffler()

        else :
            self.reloadShuffler()
            self.arranger_view_window.show()


    def reloadShuffler(self):
        """Reloads the shuffler from the current application state (app.selection_s)."""
        if hasattr(self.arranger_view, 'pool') and self.arranger_view.pool:
            self.arranger_view.pool.terminate()
            self.arranger_view.pool.join()
            self.arranger_view.pool = None
        self.arranger_view.model.clear()
        self.arranger_view.pdfqueue = []
        self.arranger_view.nfile = 0
        self.loadShuffler()

    def resetShuffler(self, widget=None):
        """Resets the shuffler to the original PDF order (1..N)."""

        if hasattr(self.arranger_view, 'pool') and self.arranger_view.pool:
            self.arranger_view.pool.terminate()
            self.arranger_view.pool.join()
            self.arranger_view.pool = None
        self.arranger_view.model.clear()
        self.arranger_view.pdfqueue = []
        self.arranger_view.nfile = 0
        # Passing " " (space) forces parsePageSelection to generate the default 1..N selection
        self.loadShuffler(" ")

    def loadShuffler(self, selection="") :
            self.render.parsePageSelection(selection, 0)

            doc_map = {}
            for key in inputFiles_a :
                pdfdoc = PDF_Doc(inputFiles_a[key], self.arranger_view.nfile, self.arranger_view.tmp_dir)
                if pdfdoc.nfile != 0 and pdfdoc != []:
                    self.arranger_view.nfile = pdfdoc.nfile
                    self.arranger_view.pdfqueue.append(pdfdoc)
                    doc_map[key] = pdfdoc

            angle=0
            crop=[0.,0.,0.,0.]
            res = False
            for page in pagesSel :
                file1, page1 = page.split(":")
                npage = int(page1) + 1
                # filenumber = int(file1) - 1 # This logic is flawed if keys are not sequential 1..N
                pdfdoc = doc_map.get(int(file1))
                if not pdfdoc:
                    # Should not happen if data consistency is maintained
                    continue
                if npage > 0 :
                    docPage = pdfdoc.document.get_page(npage-1)
                else :
                    docPage = pdfdoc.document.get_page(0)
                w, h = docPage.get_size()

                # blank page
                if npage == 0 :
                    descriptor = 'Blank'
                    # width/height are in points (from get_size), create blank pdf matching this
                    # PdfArranger uses points for size
                    b_doc, b_nfile = self.arranger_view.get_blank_pdf(w, h)
                    
                    page_obj = Page(
                        b_nfile, 
                        1, 
                        self.arranger_view.zoom_scale, 
                        b_doc.copyname, 
                        0, 
                        1.0, 
                        Sides(0,0,0,0), 
                        Sides(0,0,0,0), 
                        Dims(w, h), 
                        descriptor, 
                        []
                    )
                    self.arranger_view.model.append([page_obj, descriptor])
                else :
                    Id = str(file1) + ":" + str(npage)
                    angle = 0
                    crop = [0., 0., 0., 0.]
                    if Id in config:
                         if "shuffler_rotate" in config[Id]:
                             angle = int(config[Id]["shuffler_rotate"])
                             
                         if "shuffler_crop" in config[Id]:
                             try:
                                 vals = config[Id]["shuffler_crop"].split(",")
                                 if len(vals) == 4:
                                     crop = [float(x) for x in vals]
                             except:
                                 pass
                    descriptor = ''.join([pdfdoc.shortname, '\n', _('page'), ' ', str(npage)])
                    page_obj = Page(
                        pdfdoc.nfile, 
                        npage, 
                        self.arranger_view.zoom_scale, 
                        pdfdoc.filename, 
                        angle, 
                        1.0, 
                        Sides(crop[0], crop[1], crop[2], crop[3]), 
                        Sides(0,0,0,0), 
                        Dims(w, h), 
                        descriptor, 
                        []
                    )
                    iter = self.arranger_view.model.append([page_obj, descriptor])
                    res = True

            self.arranger_view.reset_iv_width()
            if res:
                self.arranger_view.render()

    def on_shuffler_delete(self, widget, event):
        """Handle window close request (X button) as Cancel."""
        self.closePS()
        return True

    def closePS(self) :
        if self.arranger_view :
            self.arranger_view.rendering_thread.quit = True
            # self.arranger_view.rendering_thread.quit = True # This was already set? Line 3774
            # Gdk.threads_enter() # REMOVED to avoid lock
            # TODO ££
##            if self.arranger_view.rendering_thread.paused == True:
##                 self.arranger_view.rendering_thread.evnt.set()
##                 self.arranger_view.rendering_thread.evnt.clear()
            self.arranger_view_window.destroy()
            self.arranger_view= None
            self.arranger_view
            self.runPS()

    def getShufflerSel(self, widget):

        selection = []
        for row in self.arranger_view.model:
            page = row[0]
            # Decoupling Selection ID (1-based for string parsing) from Config ID (0-based for internal use)
            if page.description == 'Blank':
                page_idx_sel = -1
                page_idx_cfg = -1
            else:
                page_idx_sel = page.npage
                page_idx_cfg = page.npage
            
            Id_sel = str(page.nfile) + ":" + str(page_idx_sel)
            Id_cfg = str(page.nfile) + ":" + str(page_idx_cfg)
            
            selection += [Id_sel]
            try:
                angle = int(page.angle)
            except:
                angle = 0
            
            if angle != 0 :
                if angle == 90 :        # In Pdf format, global rotation rotates clockwise,
                    angle = 270         # fine rotation (used by PdfBooklet) rotates counterclockwise.

                elif angle == -90 :
                    angle = 90

            # Use Id_cfg for config storage
            if not Id_cfg in config and angle != 0 :
                config[Id_cfg] = {}
                # defaults
                config[Id_cfg]["htranslate"] = 0
                config[Id_cfg]["vtranslate"] = 0
                config[Id_cfg]["scale"] = 1
                config[Id_cfg]["rotate"] = 0

            if angle != 0 :
                config[Id_cfg]["shuffler_rotate"] = angle
            elif Id_cfg in config and "shuffler_rotate" in config[Id_cfg]:
                del config[Id_cfg]["shuffler_rotate"]

            # Save shuffler_crop
            # page.crop is Sides(left, right, top, bottom)
            crop_rect = page.crop
            has_crop = False
            if crop_rect:
                if (crop_rect.left != 0 or crop_rect.right != 0 or crop_rect.top != 0 or crop_rect.bottom != 0):
                    has_crop = True
            
            if has_crop:
                 val = f"{crop_rect.left},{crop_rect.right},{crop_rect.top},{crop_rect.bottom}"
                 config[Id_cfg]["shuffler_crop"] = val
            elif Id_cfg in config and "shuffler_crop" in config[Id_cfg]:
                 del config[Id_cfg]["shuffler_crop"]
##                elif angle == 90 :
##                    config[Id_cfg]["htranslate"] = pix_h





        self.selection_s = self.compressSelection(selection)
        self.arranger_view_window.hide()
        self.previewUpdate()


    def closeShuffler(self, widget) :
        self.arranger_view_window.hide()


    def ________________TRANSFORMATIONS() :
        pass


    def ta2(self, widget, event = "") :
        print("ta2", event)
        self.transformationsApply("")

    def transformationsApply(self, widget, event="", force_update = False) :
        # Reads the values in the gui and updates the config dictionary

        global selected_page, selected_pages_a, rows_i

        for this_selected_page in selected_pages_a :

            if this_selected_page == None :
                showwarning(_("No selection"), _("There is no selected page. \nPlease select a page first. "))
                return
            # this_selected_page 4 and 5 contain the correct page reference, including the global rotation.
            humanReadableRow_i = rows_i - this_selected_page[4]
            Id = str(str(humanReadableRow_i) + "," + str(this_selected_page[5] + 1))

            pageId = str(this_selected_page[2]) + ":" + str(this_selected_page[3])

            # if transformation is for this page only, use page ref instead of position ref
            if self.thispage.get_active() == 1 :
                Id = pageId
            if self.evenpages.get_active() == 1 :
                Id = "even"
            if self.oddpages.get_active() == 1 :
                Id = "odd"

            config[Id] = {}

            config[Id]["htranslate"] = self.arw["htranslate1"].get_text()     # data from the gui unmodified
            config[Id]["vtranslate"] = self.Vtranslate1.get_text()
            config[Id]["scale"] = self.scale1.get_text()
            config[Id]["rotate"] = self.rotation1.get_text()
            config[Id]["xscale"] = self.arw["xscale1"].get_text()
            config[Id]["yscale"] = self.arw["yscale1"].get_text()
            config[Id]["vflip"] = self.arw["vflip1"].get_active()
            config[Id]["hflip"] = self.arw["hflip1"].get_active()
        #if not force_update :
            # prevent useless update. If no change, return.
            # TODO : à débuguer
##            a = repr(config[Id])
##            if not "memory1" in self :
##                memory1 = {}
##                b = self.memory1["memory1"]
##                if a == b :
##                    return
##            else :
##                self.memory1["memory2"] = 0
##            self.memory1["memory1"] = a
##            self.memory1["memory2"] += 1

        if self.arw["automaticUpdate"].get_active() == 0 :  # If automatic update is not disabled
            self.preview(self.previewPage)                # update the preview


    def resetTransformations(self, event = 0) :
        self.arw["htranslate1"].set_value(0)
        self.arw["vtranslate1"].set_value(0)
        self.arw["scale1"].set_value(100)
        self.arw["xscale1"].set_value(100)
        self.arw["yscale1"].set_value(100)
        self.arw["rotation1"].set_value(0)
        self.arw["vflip1"].set_active(False)
        self.arw["hflip1"].set_active(False)

        if event != 0 : self.transformationsApply("dummy", force_update = True)
        pass

    def resetTransformations2(self, event = 0) :
        # reset default values for global transformations
        self.arw["htranslate2"].set_value(0)
        self.arw["vtranslate2"].set_value(0)
        self.arw["scale2"].set_value(100)
        self.arw["xscale2"].set_value(100)
        self.arw["yscale2"].set_value(100)
        self.arw["rotation2"].set_value(0)
        self.arw["vflip2"].set_active(False)
        self.arw["hflip2"].set_active(False)
        if event != 0 :
            self.arw["globalRotation0"].set_active(1)
            self.previewUpdate()
        pass

    def copy_transformations(self, event) :          # called by context menu
        self.clipboard["htranslate1"] = self.arw["htranslate1"].get_text()     # data from the gui unmodified
        self.clipboard["vtranslate1"] = self.Vtranslate1.get_text()
        self.clipboard["scale1"] = self.scale1.get_text()
        self.clipboard["rotate1"] = self.rotation1.get_text()
        self.clipboard["this_page"] = self.thispage.get_active()
        self.clipboard["xscale1"] = self.arw["xscale1"].get_text()
        self.clipboard["yscale1"] = self.arw["yscale1"].get_text()
        self.clipboard["vflip1"]  = self.arw["vflip1"].get_active()
        self.clipboard["hflip1"]  = self.arw["hflip1"].get_active()

    def paste_transformations(self, event) :          # called by context menu
         self.arw["htranslate1"].set_text(self.clipboard["htranslate1"])
         self.Vtranslate1.set_text(self.clipboard["vtranslate1"])
         self.scale1.set_text(self.clipboard["scale1"])
         self.rotation1.set_text(self.clipboard["rotate1"])
         self.thispage.set_active(self.clipboard["this_page"])
         self.arw["xscale1"].set_text(self.clipboard["xscale1"])
         self.arw["yscale1"].set_text(self.clipboard["yscale1"])
         self.arw["vflip1"].set_active(self.clipboard["vflip1"])
         self.arw["hflip1"].set_active(self.clipboard["hflip1"])

         self.transformationsApply("", force_update = True)



    def version21(self, widget) :
        showwarning("Not yet implemented", "This feature will be implemented in version 2.2")

    def aboutPdfbooklet(self, widget) :
        about = self.arw["Pdf-Booklet"]
        about.set_version(PB_version)
        
        authors = about.get_authors()
        new_authors = [
            "",
            "Core Dependencies:",
            "pypdf (v3+) - https://github.com/py-pdf/pypdf",
            "pdfarranger - https://github.com/pdfarranger/pdfarranger",
            "",
            "PdfBooklet maintainer:",
            "Tomas Julian Resquin",
        ]
        
        # Avoid duplicating credits if opened multiple times
        if not any("pypdf" in s for s in authors):
             about.set_authors(new_authors + authors)
             
        about.show()

    def aboutdialog1_close(self, widget,event) :
        self.arw["Pdf-Booklet"].hide()

    def print2(self, string, cr=0) :        # no  longer used
        global editIniFile

        return
        editIniFile = 0
        enditer = self.text1.get_end_iter()
        self.text1.insert(enditer, string)
        if cr == 1 :
            self.text1.insert(enditer, chr(10))
        iter0 = self.text1.get_end_iter()
        self.arw["text1"].scroll_to_iter(iter0,0)
        #  TODO : bug
        # This command hangs the program (the interface remains blank) when :
        #   a file has been loaded
        #   The page selector has been used
        #   a second file is loaded.
        #while Gtk.events_pending():
        #            Gtk.main_iteration()

    def test(self,event, dummy = None) :
        print("test")

    def destroyWindow() :
        pass        # commande encore présente dans Glade, à supprimer

    def go(self, button, preview = -1) :

        if self.readGui() :
            if self.render.parsePageSelection() :
                self.readConditions()
                ar_pages, ar_layout, ar_cahiers = self.render.createPageLayout()
                if ar_pages != None :
                    # Verify that the output file may be written to

                    if app.arw["entry2"].get_text() == "" :
                        inputFile = inputFiles_a[1]
                        inputFile_name = os.path.splitext(inputFile)[0]
                        outputFile = inputFile_name + "-bklt.pdf"
                    else :
                        outputFile = app.arw["entry2"].get_text()
                        inputFile = inputFiles_a[1]
                        inputFile_wo_ext = os.path.splitext(inputFile)[0]
                        (inputFile_path, inputFile_name) = os.path.split(inputFile)
                        (inputFile_basename, inputFile_ext) = os.path.splitext(inputFile_name)
                        inputFile_path += "/"
                        inputFile_ext = inputFile_ext[1:]


                        outputFile = outputFile.replace("%F", inputFile_wo_ext)
                        outputFile = outputFile.replace("%N", inputFile_name)
                        outputFile = outputFile.replace("%B", inputFile_basename)
                        outputFile = outputFile.replace("%P", inputFile_path)
                        outputFile = outputFile.replace("%E", inputFile_ext)

                    if preview == -1 :
                        if os.path.isfile(outputFile) :
                            if app.overwrite.get_active() == 0 :
                                answer_b = askyesno(_("File existing"), _("The outputfile already exists \n" \
                                "overWrite ? " ))
                                if False == answer_b :
                                    return False


                        if self.render.createNewPdf(ar_pages, ar_layout, ar_cahiers, outputFile, preview) :
                            if self.arw["show"].get_active() == 1 :

                                if 'linux' in sys.platform :
                                    subprocess.call(["xdg-open", outputFile])
                                else:
                                    os.startfile(outputFile)

        return [ar_pages, ar_layout, ar_cahiers]




    def readConditions(self) :
        global optionsDict, config
        # Used by the go function above
        return
        if app.arw["entry3"].get() == "" :
            return
        else :
            inifile = app.arw["entry3"].get()
            config = parser.read(inifile)
            optionsDict = {}
            optionsDict["pages"] = {}
            optionsDict["conditions"] = {}

            if config.has_section("pages") :
                for a in config.options("pages") :
                    optionsDict["pages"][a] = config["pages"][a]

            if config.has_section("conditions") :
                for a in config.options("conditions") :
                    optionsDict["conditions"][a] = config["conditions"][a]


    def test1(self, widget) :
        print("input")
    def test2(self, widget) :
        print("output")
    def test3(self, widget) :
        print("value_changed")
    def test4(self, widget) :
        print("change value")
    def test5(self, widget) :
        print("test5")




class pdfRender():

    def transform(self, row, column, page_number, output_page_number, file_number) :
        global optionsDict, config, rows_i, outputScale, mediabox_l, columns_i

        # init variables
        # Calculate cell positions including output scaling and centering
        autoscale_enabled = app.autoscale.get_active() == 1
        
        if autoscale_enabled and outputScale != 1 and mediabox_l:
            # Calculate centering offsets for when content is scaled to fit output
            oWidth_i = urx_i * columns_i
            oHeight_i = ury_i * rows_i
            scaled_width = oWidth_i * outputScale
            scaled_height = oHeight_i * outputScale
            output_width = mediabox_l[0]
            output_height = mediabox_l[1]
            
            # Center the scaled content on the output page
            h_center = (output_width - scaled_width) / 2
            v_center = (output_height - scaled_height) / 2
            
            # Cell position: input coords scaled, plus centering offset
            # This position will NOT be further scaled by outputScale (already included)
            V_offset = row * ury_i * outputScale + v_center
            H_offset = column * urx_i * outputScale + h_center
        else:
            # No output scaling - use original coordinates
            V_offset = row * ury_i
            H_offset = column * urx_i
            
        cos_l = 1
        sin_l = 0

        transform_s = " %s %s %s %s %s %s cm  \n" % (cos_l , sin_l, -sin_l, cos_l , H_offset , V_offset)
        transformations = []

        # Transformations defined in gui

        # Transformations for page in position (row, col)
        section_s = str(rows_i - row) + "," + str(column + 1)
        if section_s in config :
            transform_s += self.transform2(section_s)

        # Transformations for page #:#
        pageId = str(file_number) + ":" + str(page_number + 1)
        if pageId in config :
            transform_s += self.transform2(pageId)

            # Debug !!!
            """  Je ne comprends pas le sens de ce bloc, qui refait une deuxième fois la transformation,
                si bien que quand, par exemple, on demande une transformation de 45, on obtient 90 !
            ht = ini.readmmEntry(config[pageId]["htranslate"])
            vt = ini.readmmEntry(config[pageId]["vtranslate"])
            sc = ini.readPercentEntry(config[pageId]["scale"])
            ro = ini.readNumEntry(config[pageId]["rotate"])
            try :
                pdfrotate = ini.readNumEntry(config[pageId]["pdfrotate"])
            except :
                pdfrotate = 0
            xs = ini.readPercentEntry(config[pageId]["xscale"])
            ys = ini.readPercentEntry(config[pageId]["yscale"])



            matrix_s = self.calcMatrix2(ht, vt,
                                       cScale = sc,
                                       xscale = xs,
                                       yscale = ys,
                                       cRotate = ro,
                                       Rotate = pdfrotate,
                                       vflip = config[pageId]["vflip"],
                                       hflip = config[pageId]["hflip"])



##            if "shuffler_rotate" in config[pageId] :
##                # we need the page size
##                pdfDoc = app.shuffler.pdfqueue[file_number-1]
##                page = pdfDoc.document.get_page(page_number)
##                pix_w, pix_h = page.get_size()
##
##                angle = int(config[pageId]["shuffler_rotate"])
##                pdfrotate +=   angle
##                if angle == 270 :
##                    vtranslate = float(vtranslate) + float(pix_w)
##                elif angle == 90 :
##                    htranslate = float(htranslate) + float(pix_h)
##                elif angle == 180 :
##                    htranslate = float(htranslate) + float(pix_w)
##                    vtranslate = float(vtranslate) + float(pix_h)


            transform_s += self.calcMatrix2(ht, vt,
                                       cScale = sc,
                                       cRotate = ro,
                                       Rotate = pdfrotate)
            """
        # Transformations for even and odd pages
        if page_number % 2 == 1 :
            transform_s += self.transform2("even")
        if page_number % 2 == 0 :
            transform_s += self.transform2("odd")




        # Transformations defined in ini file

        if "pages" in config :
            pages_a = config["pages"].keys()
            if section_s in pages_a :               # If the layout page presently treated is referenced in [pages]
                temp1 = config["pages"][section_s]
                transformations += temp1.split(", ")

            if str(page_number + 1) in pages_a :    # If the page presently treated is referenced in [pages]
                temp1 = config["pages"][str(page_number + 1)]
                transformations += temp1.split(", ")


        if "conditions" in config :
            conditions_a = config["conditions"].keys()
            for line1 in conditions_a :
                condition_s = config["conditions"][line1]
                command_s, filters_s = condition_s.split("=>")
                if (eval(command_s)) :
                    transformations += filters_s.split(", ")

        for a in transformations :

            transform_s += self.calcMatrix(a)
        return (transform_s)

    def transform2(self, Id) :
        # Calculates matrix for a given section
        matrix_s = ""
        if Id in config :
            if not "pdfRotate" in config[Id] :
                config[Id]["pdfRotate"] = 0
            if not "rotate" in config[Id] :
                config[Id]["rotate"] = 0

            htranslate = 0
            vtranslate = 0
            pdfrotate = 0

            if "shuffler_rotate" in config[Id] :
                try:
                    # Parse Id "file:page" (1-based indices in config key)
                    file_s, page_s = Id.split(":")
                    file_idx = int(file_s)
                    page_idx = int(page_s) - 1 # Convert to 0-based for list access
                    
                    # retrieve page size from internal structure instead of app.shuffler
                    # global inputFiles_a maps 1..N to filename
                    # global inputFile_a maps filename to PDF object
                    fileName = inputFiles_a[file_idx]
                    pdfObj = inputFile_a[fileName]
                    pageObj = pdfObj.pages[page_idx]
                    
                    # Assume mediaBox is [x1, y1, x2, y2]
                    # width = x2 - x1, height = y2 - y1
                    # pdfrw objects? or pikepdf?
                    # PdfBooklet usually uses internal PDF class where page.mediaBox is a list of floats
                    mbox = pageObj.mediaBox
                    pix_w = float(mbox[2]) - float(mbox[0])
                    pix_h = float(mbox[3]) - float(mbox[1])

                    angle = int(config[Id]["shuffler_rotate"])
                    pdfrotate += angle
                    if angle == 270 or angle == -90:
                        vtranslate += float(pix_w)
                    elif angle == 90 or angle == -270:
                        htranslate += float(pix_h)
                    elif angle == 180 or angle == -180:
                        htranslate += float(pix_w)
                        vtranslate += float(pix_h)
                except Exception as e:
                    print(f"Error applying shuffler_rotate: {e}")

            ht = ini.readmmEntry(config[Id]["htranslate"]) + htranslate
            vt = ini.readmmEntry(config[Id]["vtranslate"]) + vtranslate
            sc = ini.readPercentEntry(config[Id]["scale"])
            ro = ini.readNumEntry(config[Id]["rotate"])
            xs = ini.readPercentEntry(config[Id]["xscale"])
            ys = ini.readPercentEntry(config[Id]["yscale"])

            try:
                base_pdfrotate = ini.readNumEntry(config[Id]["pdfRotate"])
            except:
                base_pdfrotate = 0

            matrix_s = self.calcMatrix2(ht, vt,
                                       cScale = sc,
                                       xscale = xs,
                                       yscale = ys,
                                       cRotate = ro,
                                       Rotate = base_pdfrotate + pdfrotate,
                                       vflip = ini.readBoolean(config[Id]["vflip"]),
                                       hflip = ini.readBoolean(config[Id]["hflip"]))



        return matrix_s


    def calcMatrix(self, mydata, myrows_i = 1, mycolumns_i = 1) :
            # Calculate matrix for transformations defined in the configuration
            global config

            trans = mydata.strip()
            cos_l = 1
            cos2_l = 1
            sin_l = 0
            Htranslate = 0
            Vtranslate = 0


            Rotate = 0
            if config.has_option(trans, "PdfRotate") :
                Rotate = config.getint(trans, "PdfRotate")

            if config.has_option(trans, "shuffler_rotate") :
                 angle = config.getint(trans, "shuffler_rotate")
                 Rotate += angle
                 
                 # Adjust translation for standard 90-degree rotations
                 # Using global page dimensions urx_i, ury_i
                 if angle == 90 or angle == -270:
                     Htranslate += ury_i
                 elif angle == 270 or angle == -90:
                     Vtranslate += urx_i
                 elif angle == 180 or angle == -180:
                     Htranslate += urx_i
                     Vtranslate += ury_i
            
            if Rotate != 0:
                sin_l = math.sin(math.radians(Rotate))
                cos_l = math.cos(math.radians(Rotate))
                cos2_l = cos_l

            if config.has_option(trans, "Rotate") :
                try :
                    Rotate = config.getfloat(trans, "Rotate")
                except :
                    pass

                sin_l, cos_l, HCorr, VCorr = self.centeredRotation(Rotate, myrows_i, mycolumns_i)
                cos2_l = cos_l

                Htranslate += HCorr
                Vtranslate += VCorr


            if config.has_option(trans, "Scale") :
                Scale_f = ini.readPercentEntry(config[trans]["Scale"])
                cos_l = cos_l * Scale_f
                cos2_l = cos_l

                HCorr = (urx_i * mycolumns_i * (Scale_f - 1)) / 2
                VCorr = (ury_i * myrows_i * (Scale_f - 1)) / 2
                Htranslate -= HCorr
                Vtranslate -= VCorr

            if config.has_option(trans, "xscale") :
                Scale_f = ini.readPercentEntry(config[trans]["xscale"])
                cos_l = cos_l * Scale_f

                HCorr = (urx_i * mycolumns_i * (Scale_f - 1)) / 2
                Htranslate -= HCorr

            if config.has_option(trans, "yScale") :
                Scale_f = ini.readPercentEntry(config[trans]["yScale"])
                cos2_l = cos2_l * Scale_f

                VCorr = (ury_i * myrows_i * (Scale_f - 1)) / 2
                Vtranslate -= VCorr

            # Vertical flip  : 1 0 0 -1 0 <height>
            if config.has_option(trans, "vflip") :
                value = config[trans]["vflip"].lower()
                if value == "true" or value == "1" :
                    cos2_l = cos2_l * (-1)
                    Vtranslate += ury_i * myrows_i

            # Horizontal flip  : -1 0 0 1 0 <width>
            if config.has_option(trans, "hflip") :
                value = config[trans]["hflip"].lower()
                if value == "true" or value == "1" :
                    cos_l = cos_l * (-1)
                    Htranslate += urx_i * mycolumns_i


            if config.has_option(trans, "htranslate") :
                ht = ini.readNumEntry(config[trans]["htranslate"])
                Htranslate += ht / adobe_l

            if config.has_option(trans, "vtranslate") :
                vt = ini.readNumEntry(config[trans]["vtranslate"])
                Vtranslate += vt / adobe_l



            if abs(sin_l) < 0.00001 : sin_l = 0          # contournement d'un petit problème : sin 180 ne renvoie pas 0 mais 1.22460635382e-16
            if abs(cos_l) < 0.00001 : cos_l = 0



            transform_s = " %s %s %s %s %s %s cm  \n" % (cos_l , sin_l, -sin_l, cos2_l , Htranslate , Vtranslate)


            if "Matrix" in config[trans] :
                Matrix = config[trans]["Matrix"]
                transform_s = " %s  cm  \n" % (Matrix)


            return transform_s


    def calcMatrix2(self, Htranslate, Vtranslate,
                          cScale = 1, Scale = 1,
                          Rotate = 0, cRotate = 0,
                          vflip = 0, hflip = 0,
                          xscale = 1, yscale = 1,
                          global_b = False) :
            # calculate matrix for transformations defined in parameters

            Htranslate = float(Htranslate)
            Vtranslate = float(Vtranslate)
            cos_l = 1
            sin_l = 0

            if global_b == True :   # for global transformations, reference for centered scale, rotation and flip is the output page
                myrows_i = rows_i
                mycolumns_i = columns_i
            else :                  # for page transformations, reference is the active source page
                myrows_i = 1
                mycolumns_i = 1

            if Scale != 1:
                Scale_f = float(Scale)
            elif cScale != 1 :
                Scale_f = float(cScale)
            else :
                Scale_f = 1

            if Rotate != 0 :
                sin_l = math.sin(math.radians(float(Rotate)))
                cos_l = math.cos(math.radians(float(Rotate)))
            # TODO Rotate and cRotate are not compatible.
            elif cRotate != 0 :
                sin_l, cos_l, HCorr, VCorr = self.centeredRotation(float(cRotate), myrows_i, mycolumns_i)
                Htranslate += (HCorr * Scale_f)
                Vtranslate += (VCorr * Scale_f)

            if Scale != 1 :
                sin_l = sin_l * Scale_f
                cos_l = cos_l * Scale_f
                HCorr = (urx_i * (Scale_f - 1)) / 2
                VCorr = (ury_i * (Scale_f - 1)) / 2

            if cScale != 1 :
                sin_l = sin_l* Scale_f
                cos_l = cos_l * Scale_f
                HCorr = (urx_i * mycolumns_i * (Scale_f - 1)) / 2
                VCorr = (ury_i * myrows_i * (Scale_f - 1)) / 2

                Htranslate -= HCorr
                Vtranslate -= VCorr


            if abs(sin_l) < 0.00001 : sin_l = 0          # contournement d'un petit problème : sin 180 ne renvoie pas 0 mais 1.22460635382e-16
            if abs(cos_l) < 0.00001 : cos_l = 0

            transform_s = " %s %s %s %s %s %s cm  \n" % (cos_l , sin_l, -sin_l, cos_l , Htranslate , Vtranslate)


            Htranslate = 0
            Vtranslate = 0
            cos_l = 1
            cos2_l = 1
            sin_l = 0


            if xscale != '1' and xscale != 1 :
                xscale = float(xscale)
                cos_l = cos_l * xscale

                HCorr = (urx_i * mycolumns_i * (xscale - 1)) / 2
                Htranslate -= HCorr

            if yscale != '1' and yscale != 1:
                yscale = float(yscale)
                cos2_l = cos2_l * yscale

                VCorr = (ury_i * myrows_i * (yscale - 1)) / 2
                Vtranslate -= VCorr

            if abs(sin_l) < 0.00001 : sin_l = 0          # contournement d'un petit problème : sin 180 ne renvoie pas 0 mais 1.22460635382e-16
            if abs(cos_l) < 0.00001 : cos_l = 0

            transform_s += " %s %s %s %s %s %s cm  \n" % (cos_l , sin_l, -sin_l, cos2_l , Htranslate , Vtranslate)


            Htranslate = 0
            Vtranslate = 0
            cos_l = 1
            cos2_l = 1
            sin_l = 0

            # Vertical flip  : 1 0 0 -1 0 <height>
            if vflip != 0 and vflip != False  :
                cos2_l = cos2_l * (-1)
                Vtranslate += ury_i * myrows_i

            # Horizontal flip  : -1 0 0 1 0 <width>
            if hflip != 0 and hflip != False :
                cos_l = cos_l * (-1)
                Htranslate += urx_i * mycolumns_i



            if abs(sin_l) < 0.00001 : sin_l = 0          # contournement d'un petit problème : sin 180 ne renvoie pas 0 mais 1.22460635382e-16
            if abs(cos_l) < 0.00001 : cos_l = 0
            if abs(cos2_l) < 0.00001 : cos2_l = 0

            transform_s += " %s %s %s %s %s %s cm  \n" % (cos_l , sin_l, -sin_l, cos2_l , Htranslate , Vtranslate)
            return transform_s

    def centeredRotation_old(self, Rotate) :

        Rotate = math.radians(Rotate)
        sin_l = math.sin(Rotate)
        cos_l = math.cos(Rotate)

        # If a is the angle of the diagonale, and R the rotation angle, the center of the rectangle moves like this :
        # Horizontal move = sin(a + R) - sin(a)
        # Vertical move   = cos(a + R) - cos(a)
        #Hence, corrections are sin(a) - sin(a+R) and cos(a) - cos(a-R)

        diag = math.pow((urx_i * urx_i) + (ury_i * ury_i), 0.5)
        alpha = math.atan2(ury_i, urx_i)

        S1 = math.sin(alpha)
        S2 = math.sin(alpha + Rotate)

        C1 = math.cos(alpha)
        C2 = math.cos(alpha + Rotate)

        Vcorr = (S1 - S2) * diag / 2
        Hcorr = (C1 - C2) * diag / 2

        return (sin_l, cos_l, Hcorr, Vcorr)

    def centeredRotation(self, Rotate, myrows_i = 1, mycolumns_i = 1) :

        Rotate = math.radians(Rotate)
        sin_l = math.sin(Rotate)
        cos_l = math.cos(Rotate)

        # If a is the angle of the diagonale, and R the rotation angle, the center of the rectangle moves like this :
        # Horizontal move = sin(a + R) - sin(a)
        # Vertical move   = cos(a + R) - cos(a)
        #Hence, corrections are sin(a) - sin(a+R) and cos(a) - cos(a-R)

        oWidth_i = urx_i * mycolumns_i
        oHeight_i = ury_i * myrows_i

        diag = math.pow((oWidth_i * oWidth_i) + (oHeight_i * oHeight_i), 0.5)
        alpha = math.atan2(oHeight_i, oWidth_i)

        S1 = math.sin(alpha)
        S2 = math.sin(alpha + Rotate)

        C1 = math.cos(alpha)
        C2 = math.cos(alpha + Rotate)

        Vcorr = (S1 - S2) * diag / 2
        Hcorr = (C1 - C2) * diag / 2

        return (sin_l, cos_l, Hcorr, Vcorr)

    def autoScaleAndRotate(self, fileNum, page, column=0, row=0) :
        global inputFiles_a, inputFile_a, refPageSize_a, outputScale, mediabox_l, columns_i, rows_i

        fileName = inputFiles_a[fileNum]
        page0 = inputFile_a[fileName].pages[page]
        llx_i=page0.mediabox.left
        lly_i=page0.mediabox.bottom
        urx_i=page0.mediabox.right
        ury_i=page0.mediabox.top

        page_width = float(urx_i) - float(llx_i)
        page_height =  float(ury_i) - float(lly_i)


        (ref_width, ref_height) = refPageSize_a
        #available_width = mediabox_l[0] / mediabox_l[2]  # mediabox_l[2] contains the number of columns
        #available_height = mediabox_l[1] / mediabox_l[3]  # mediabox_l[3] contains the number of rows





        # Rotate if needed
        # check source orientation
        if ref_height > ref_width :
            ref_orientation = "portrait"
        else :
            ref_orientation = "landscape"

        # check page orientation
        if page_height > page_width :
            page_orientation = "portrait"
        else :
            page_orientation = "landscape"


        if ref_orientation != page_orientation :     # orientation is not the same
            Rotate = 270
            h = page_height
            w = page_width
            page_height = w
            page_width = h
            #Htranslate1 = page_width  # for 90
            Vtranslate1 = page_height  # for 270
        else:
            Rotate = 0
            #Htranslate1 = 0
            Vtranslate1 = 0


        delta1 = ref_height / page_height
        delta2 = ref_width  / page_width
        Vdiff = ref_height - (page_height * delta2)
        Hdiff = ref_width - (page_width * delta1)

        # Choose the lower factor, and calculate the translation for centering the image
        if delta1 < delta2 :
            Scale = delta1
            Vtranslate = 0
            Htranslate = Hdiff/2
        else:
            Scale = delta2
            Vtranslate = Vdiff/2
            Htranslate = 0
        #Htranslate += Htranslate1
        Vtranslate += (Vtranslate1 * Scale)
        
        # Compensate for cell position scaling issue:
        # When matrices are multiplied, the cell position translation gets scaled
        # by autoScale. We need to add a compensation to undo this effect.
        # The cell position is ref_width * column (in input coordinates), 
        # and it gets multiplied by Scale.
        # To restore the correct position, we add: cell_position * (1 - Scale)
        if Scale != 1.0:
            Htranslate += column * ref_width * (1 - Scale)
            Vtranslate += row * ref_height * (1 - Scale)

        
        # We start with the page ID itself to pick up per-page settings like shuffler_rotate
        transformations = [page]
        
        # Transformations for even and odd pages
        print(f"[DEBUG] autoScaleAndRotate: page={page}, col={column}, page_size=({page_width:.1f}x{page_height:.1f}), ref_size=({ref_width:.1f}x{ref_height:.1f}), Scale={Scale:.4f}, Htranslate={Htranslate:.2f}, Vtranslate={Vtranslate:.2f}")
        return (Rotate, Scale, Htranslate, Vtranslate)


    def parsePageSelection(self, selection = "", append_prepend = 1) :
        global pagesSel, totalPages, pgcount, input1, numPages, step_i, blankPages
        global inputFiles_a, inputFile_a

        if len(inputFiles_a) == 0 :
            showwarning(_("No file loaded"), _("Please select a file first"))
            return False

        if selection == "" :
            selection = app.selection_s

        if selection.strip() == "" :        # if there is no selection, then we create the default selection
                                            # which contains all pages of all documents
            i = 1
            for f in inputFiles_a :
                fileName = inputFiles_a[f]
                numPages = len(inputFile_a[fileName].pages)
                selection += str(i) + ":1-%s;" % (numPages)
                i += 1
            app.selection_s = selection

        if selection == "" :                # This should not happen...
            showwarning(_("No selection"), _("There is no selection"))
            return False

        selection = re.sub("[;,]{2,}", ";", selection)          # we replace successive ; or , by a single ;
        syntax_s = re.sub("[0-9,;:b\-\s]*", "", selection)      # To verify all characters are valid, we remove all them and there should remain nothing
        syntax_s = syntax_s.strip()
        if syntax_s != "" :                                     # If something remains, it is not valid
            showwarning(_("Invalid data"), _("Invalid data for Selection : %s. Aborting \n") % syntax_s)
            return False

        if append_prepend == 1 :
            pagesSel = prependPages * ["1:-1"]
        else :
            pagesSel = []


        selection = selection.replace(";", ",")
        selection = selection.strip()
        if selection[-1:] == "," :      # remove the trailing ,
            selection = selection[0:-1]
        list1 = selection.split(",")

        for a in list1 :
            a = a.strip()
            b = a.split(":")
            if (len(b) == 1) :
                docId_s = "1:"
            else :
                docId_s = b[0] + ":"
                a = b[1]

            if a.count("-") > 0:
                list2 = a.split("-")
                serie = list(range(int(list2[0]) - 1, int(list2[1])))
                for x in serie :
                    page_s = docId_s + str(x)
                    pagesSel = pagesSel + [page_s]
            elif a[-1:] == "b" :
                if a[0:-1].strip() == "" :
                    blank_pages_i = 1
                else :
                    blank_pages_i = int(a[0:-1])
                pagesSel = pagesSel + (["1:-1"] * blank_pages_i)
            else :
                try :
                    a = str(int(a) - 1)
                    pagesSel = pagesSel + [docId_s + a]
                except :
                    alert("Invalid selection ", a)
        if append_prepend == 1 :
            pagesSel = pagesSel + appendPages * ["1:-1"]

            if ini.booklet > 0 :
                step_i = 2
                blankPages = (len(pagesSel) % -4) * -1
                #app.print2(_("Blank pages to be added : %s") % (blankPages) , 1)

            else :
                if step_i < 1 :
                    step_i = 1
                blankPages = (len(pagesSel) % (step_i * -1)) * -1

            pagesSel += ["1:-1"] * blankPages



        totalPages = len(pagesSel)
        pgcount = totalPages

        return True


    def createPageLayout(self, logdata = 1) :
        global config, rows_i, columns_i, cells_i, step_i, sections, output, input1, adobe_l
        global numfolio,prependPages, appendPages, ref_page, selection
        global numPages, blankPages, pagesSel, llx_i, lly_i, urx_i, ury_i, mediabox_l, pgcount

        ar_pages = {}
        ar_cahiers = {}
        index=0
        last=0
        cells_i = columns_i * rows_i


        # Create booklets
        if ini.booklet > 0 :

            multiple_bkt = int(cells_i / 2)
            ini.radioDisp= 1


            folios =  pgcount / 4
            if numfolio == 0 :                  # single booklet
                numcahiers = 1
            else :                              # multiple booklets
                numcahiers = int(folios / numfolio)
                if (folios % numfolio > 0) :
                    numcahiers = numcahiers + 1

            # equilibrate booklets size
            minfolios = int(folios / numcahiers)
            restefolios = folios - (minfolios * numcahiers)

            for k in range(numcahiers) :
                if (k < restefolios) :              # number of folios in each booklet
                    ar_cahiers[k] = minfolios + 1
                else :
                    ar_cahiers[k] = minfolios

                first = last + 1                            # num of first page of the booklet
                last = first + (ar_cahiers[k] * 4) - 1      # num of the last page of the booklet

                if logdata == 1 :
                    #app.print2(_( "Booklet %s : pages %s - %s") % (k + 1, first, last), 1)
                    pass

                bkltPages = (last - first) + 1              # number of pages in the booklet
                for i in range (bkltPages // 2) :           # page nums for each sheet
                    if ((i % 2) == 0) :                     # Page paire à gauche
                        pg2 = (i + first)
                        pg1 = (last - i)
                    else :
                        pg1 = (i + first)
                        pg2 = (last - i)

                    ar_pages[index] = [pagesSel[pg1 - 1], pagesSel[pg2 - 1]] * multiple_bkt
                    index += 1

        else :
            while index < (pgcount / step_i) :
                start = last
                last = last + step_i
                pages = []
                for a in range(start, start + cells_i) :
                    PageX = start + (a % step_i)
                    if PageX > totalPages :
                        pages = pages + [-1]
                    else :
                        pages = pages + [pagesSel[PageX]]
                ar_pages[index] = pages
                index += 1


        # create layout
        ar_layout = []
        if ini.radioDisp == 1 :
            for r in range(rows_i) :
                r2 = rows_i - (r + 1)       # rows are counted from bottom because reference is lower left in pdf so we must invert
                for c in range (columns_i) :
                    ar_layout += [[r2, c]]
        elif ini.radioDisp == 2 :
            for c in range(columns_i) :
                for r in range(rows_i) :
                    r2 = rows_i - (r + 1)   # rows are counted from bottom so we must invert
                    ar_layout += [[r2, c]]

        # If option "Right to left" has been selected creates inverted layout (which will overwrite the previous one)

        if bool_test(config["options"]["righttoleft"]) == True :

            # create inverted layout
            ar_layout = []
            if ini.radioDisp == 1 :
                for r in range(rows_i) :
                    r2 = rows_i - (r + 1)         # rows are counted from bottom because reference is lower left in pdf so we must invert
                    for c in range (columns_i) :
                        c2 = columns_i - (c + 1)  # Invert for right to left option
                        ar_layout += [[r2, c2]]
            elif ini.radioDisp == 2 :
                for c in range(columns_i) :
                    c2 = columns_i - (c + 1)      # Invert for right to left optionInvert for right to left option Invert for right to left option
                    for r in range(rows_i) :
                        r2 = rows_i - (r + 1)     # rows are counted from bottom so we must invert
                        ar_layout += [[r2, c2]]

            # End of inverted layout


        # User defined layout
        if "radiopreset8" in app.arw and app.arw["radiopreset8"].get_active() == 1 :

            # number of sheets of this layout
            sheets = len(ini.imposition)

            # create blank pages if necessary
            rest = len(ar_pages) % sheets

            if rest > 0 :
                blank = []
                for i in range(len(ar_pages[0])) :
                    blank.append(["1:-1"])
                for i in range(rest) :
                    ar_pages[len(ar_pages) + i] = blank


            # create a copy of ar_pages

            ar_pages1 = {}
            for key in ar_pages :
                pages1 = ar_pages[key]
                temp = []
                for a in pages1 :
                    temp.append(a)
                ar_pages1[key] = temp


            if sheets == 1 :
                userpages = ini.imposition[0]

                for key in ar_pages :
                    pages = ar_pages[key]
                    pages1 = ar_pages1[key]

                    i = 0
                    # we reorder the pages following the order given in userpages
                    for value in userpages :
                        if value == "b" :
                            pages[i] = "1:-1"
                        else :
                            row = int(value) - 1
                            pages[i] = pages1[row]
                        i += 1
                    ar_pages[key] = pages

            elif sheets == 2 :              # more complicated...

                userpagesA = app.imposition[0]
                userpagesB = app.imposition[1]
                step = len(userpagesA)

                for key in range(0,len(ar_pages),2) :

                    pagesA = ar_pages[key]
                    pages1A = ar_pages1[key]
                    pagesB = ar_pages[key + 1]
                    pages1B = ar_pages1[key + 1]


                    i = 0
                    # we reorder the pages following the order given in userpages
                    for value in userpagesA :
                        if value == "b" :
                            pagesA[i] = "1:-1"
                        else :
                            row = int(value) - 1
                            if row < step :
                                index = pages1A[row]
                            else :
                                rowB = row % step
                                index = pages1B[rowB]
                            pagesA[i] = index
                        i += 1
                    i = 0
                    for value in userpagesB :
                        if value == "b" :
                            pagesB[i] = "1:-1"
                        else :
                            row = int(value) - 1
                            if row < step :
                                index = pages1A[row]
                            else :
                                rowB = row % step
                                index = pages1B[rowB]
                            pagesB[i] = index
                        i += 1
                    ar_pages[key] = pagesA
                    ar_pages[key + 1] = pagesB

        return (ar_pages, ar_layout, ar_cahiers)



    def createNewPdf(self, ar_pages, ar_layout, ar_cahiers, outputFile, preview = -1) :
        global debug_b, inputFile_a, inputFiles_a, result
        global mediabox_l
        global outputStream
        import io
        import os


        if debug_b == 1 :
            logfile_f = open ("log.txt", "wb")
        # status
        statusTotal_i = len(ar_pages)
        statusValue_i = 1


        time_s=time.time()
        output = PdfWriter()



        if preview >= 0 :           # if this is a preview
            outputStream = io.BytesIO()

        else :
            try :
                outputStream = open(outputFile, "wb")
            except :
                showwarning(_("File already open"), _("The output file is already opened \n" \
                "probably in Adobe Reader. \n" \
                "Close the file and start again"))
                return

        if preview >= 0 :           # if this is a preview
            output_page_number = preview + 1
        else :
            output_page_number = 1
##            # encryption
##            if app.permissions_i != -1 and app.password_s != "" :       # if permissions or password were present in the file
##                output.encrypt("", app.password_s, P = app.permissions_i)     # TODO : there may be two passwords (user and owner)
        # Determine if we can use the new transformation approach (Strategy C prerequisite)
        use_new_transform_global = False
        if "options" in config and "autoscale" in config["options"]:
            val = ini.readBoolean(config["options"]["autoscale"])
            if val == True:
                use_new_transform_global = True
            else:
                print(f"DEBUG: Autoscale config is {val} (False)")
        else:
            print("DEBUG: 'autoscale' not found in config['options']")
        
        # Disable optimizations if booklet/creep is likely involved (safety check)
        # try:
        #      if hasattr(ini, 'booklet') and ini.booklet > 0: 
        #          use_new_transform_global = False
        #          print(f"DEBUG: MP Disabled due to Booklet mode: {ini.booklet}")
        # except: pass

        # Strategy C: Multiprocessing Batch Processing
        # Only for real output, new transform mode, and sufficient pages
        if debug_b: print(f"DEBUG: MP Check - Preview: {preview}, UseNew: {use_new_transform_global}, Pages: {len(ar_pages)}")
        if False and preview == -1 and use_new_transform_global and len(ar_pages) >= 8:
            try:
                if debug_b: print("DEBUG: Starting Multiprocessing...")
                app.status.set_text(_("Processing pages in parallel..."))
                while Gtk.events_pending(): Gtk.main_iteration()
                
                from concurrent.futures import ProcessPoolExecutor
                import os
                
                # Creep Calculation Init
                creep_val = 0
                creep_factor = 0
                start_pages = [0]
                
                try:
                    if hasattr(ini, 'booklet') and ini.booklet > 0:
                         # Attempt to read creep value safely
                         # Using raw access or app method if available
                         if hasattr(app, "readmmEntry") and "creep" in app.arw and app.arw["creep"].get_text():
                             creep_val_raw = app.readmmEntry(app.arw["creep"])
                             if creep_val_raw > 0:
                                 creep_val = creep_val_raw
                                 mem = 0
                                 sorted_keys = sorted(ar_cahiers.keys())
                                 for k in sorted_keys:
                                     val = ar_cahiers[k]
                                     if val > 0: creep_factor = creep_val / val
                                     page_val = val * 2
                                     start_pages.append(page_val + mem)
                                     mem += page_val
                except: pass

                # Prepare data for workers
                page_tasks = []
                for i, a in enumerate(ar_pages):
                     specs = ar_pages[a]
                     enriched_specs = []
                     
                     # Calculate base creep for this Output Page Index (i)
                     Htrans_base = 0
                     if creep_val > 0:
                         s_p = 0
                         for x in start_pages:
                             if i >= x: s_p = x
                             # start_pages is sorted ascending
                         
                         page_in_bk = i - s_p
                         Htrans_base = creep_factor * (int(page_in_bk/2) - (page_in_bk % 2))
                     
                     for idx_spec, spec in enumerate(specs):
                         if spec:
                             try:
                                 parts = spec.split(":")
                                 if len(parts) >= 2:
                                     f_n_str = parts[0]
                                     p_n_str = parts[1]
                                     
                                     conf_key = f"{f_n_str}:{int(p_n_str)+1}"
                                     rot = 0
                                     
                                     # Rotation lookup
                                     if conf_key in config and "shuffler_rotate" in config[conf_key]:
                                          rot = int(config[conf_key]["shuffler_rotate"])
                                     elif "pages" in config and conf_key in config["pages"]:
                                          pg = config["pages"][conf_key]
                                          if isinstance(pg, dict) and "shuffler_rotate" in pg:
                                              rot = int(pg["shuffler_rotate"])
                                          elif hasattr(pg, "get"): 
                                              val = pg.get("shuffler_rotate")
                                              if val: rot = int(val)
                                     
                                     # Creep lookup (depends on column)
                                     creep_x = 0
                                     if Htrans_base != 0 and idx_spec < len(ar_layout):
                                         col = ar_layout[idx_spec][1]
                                         if col == 0: creep_x = Htrans_base
                                         else: creep_x = -Htrans_base
                                     
                                     # Append extra data if non-zero
                                     if rot != 0 or creep_x != 0:
                                          spec = f"{f_n_str}:{p_n_str}:{rot}:{creep_x}"
                             except: pass
                         enriched_specs.append(spec)
                     page_tasks.append((i, enriched_specs)) 
                
                # Split into chunks
                num_workers = min(os.cpu_count() or 4, len(page_tasks), 8)
                chunk_size = max(1, len(page_tasks) // num_workers)
                if len(page_tasks) % num_workers != 0: chunk_size += 1
                
                chunks = [page_tasks[i:i + chunk_size] for i in range(0, len(page_tasks), chunk_size)]
                if debug_b: print(f"DEBUG: Created {len(page_tasks)} tasks in {len(chunks)} chunks using {num_workers} workers.")
                
                # Prepare params
                output_params = (mediabox_l, outputScale, columns_i, rows_i)
                config_params = (urx_i, ury_i)
                file_paths = inputFiles_a 
                
                # Submit jobs
                results = []
                with ProcessPoolExecutor(max_workers=num_workers) as executor:
                    futures = []
                    for chunk in chunks:
                        futures.append(executor.submit(batch_render_worker, chunk, ar_layout, file_paths, output_params, config_params, debug_b==1))
                    
                    for f in futures:
                        results.extend(f.result())
                
                # Sort results by page index to ensure correct order
                results.sort(key=lambda x: x[0])
                
                # Merge into final output
                import io
                from pdfbooklet.pypdf import PdfReader
                
                for idx, pdf_bytes in results:
                    if debug_b: print(f"DEBUG: Chunk {idx} received {len(pdf_bytes)} bytes")
                    bio = io.BytesIO(pdf_bytes)
                    try:
                        reader = PdfReader(bio)
                        pages_added = 0
                        for p in reader.pages:
                            output.add_page(p)
                            pages_added += 1
                        if debug_b: print(f"DEBUG: Chunk {idx} added {pages_added} pages")
                    except Exception as e:
                        print(f"ERROR: Error reading chunk {idx}: {e}")
                    
                    statusValue_i += 1
                    if statusValue_i % 5 == 0:
                        app.status.set_text("Merged %d / %d" % (statusValue_i, statusTotal_i))
                        while Gtk.events_pending(): Gtk.main_iteration()

                if debug_b: print(f"DEBUG: Total pages in output: {len(output.pages)}")

                # Global Rotation (Post-Merge)
                try:
                     if "options" in config and "globalRotation" in config["options"]:
                         gr = config["options"]["globalRotation"]
                         # Legacy parsing logic: expects format like "Rotation XXX : 90" ?
                         # Legacy used gr.strip()[14:]. 
                         if len(gr) > 14:
                             gr_s = gr.strip()[14:]
                             if gr_s.isdigit():
                                 gr_i = int(gr_s)
                                 from pdfbooklet.pypdf.generic import NameObject, NumberObject
                                 if gr_i > 0:
                                     n_obj = NumberObject(gr_i)
                                     for p in output.pages:
                                         p[NameObject("/Rotate")] = n_obj
                except Exception as e:
                     if debug_b: print(f"DEBUG: Global Rotation Error: {e}")

                # Finish
                time_e = time.time()
                output.write(outputStream)
                outputStream.close()
                del output
                if debug_b == 1: logfile_f.close()
                return True
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"DEBUG: Multiprocessing failed, falling back to sequential: {e}")
                # Fall through to sequential loop
        
        
        for i, a in enumerate(ar_pages) :
            # Performance optimization:
            # If generating a preview, only process the specific page requested.
            # However, sometimes ar_pages is already subsetted (size 1) by caller.
            # Only apply filter if we appear to have a full set.
            if preview != -1 and len(ar_pages) > 1:
                # ar_pages can be dict (a=key) or list (a=value).
                # If dict, key usually matches preview index.
                # If list, index i usually matches preview index.
                current_idx = a if isinstance(ar_pages, dict) else i
                if current_idx != preview:
                    continue
            # create the output sheet
            page2 = output.add_blank_page(100,100)
            newSheet = page2.get_object()
            newSheet[generic.NameObject("/Contents")] = generic.ArrayObject([])
            newSheet.mediabox.upper_right = (mediabox_l[0], mediabox_l[1])       # output page size
            newSheet.cropbox.upper_right = (mediabox_l[0], mediabox_l[1])
            # global rotation
            if ("options" in config) and ("globalRotation" in config["options"]) :
                gr = config["options"]["globalRotation"]
                gr_s = gr.strip()[14:]
                gr_i = int(gr_s)
                if gr_i > 0 :
                        newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(gr_i)

            i = 0
            ar_data = []


            if outputScale != 1 and app.autoscale.get_active() == 1 :
                temp1 = "%s 0 0 %s 0 0 cm \n" % (str(outputScale), str(outputScale))
                ar_data.append([temp1])
                #print("====>", outputScale)


            #Output page transformations
            if "output" in config :
                OHShift = ini.readmmEntry(config["output"]["htranslate"])
                OVShift = ini.readmmEntry(config["output"]["vtranslate"])
                OScale = ini.readPercentEntry(config["output"]["scale"])
                ORotate = ini.readNumEntry(config["output"]["rotate"])

                Ovflip = ini.readBoolean(config["output"]["vflip"])
                Ohflip = ini.readBoolean(config["output"]["hflip"])

                Oxscale = ini.readPercentEntry(config["output"]["xscale"])
                if Oxscale == None : return False

                Oyscale = ini.readPercentEntry(config["output"]["yscale"])
                if Oyscale == None : return False



                temp1 = self.calcMatrix2(OHShift, OVShift,
                                         cScale = OScale,
                                         cRotate = ORotate,
                                         vflip = Ovflip,
                                         hflip = Ohflip,
                                         xscale = Oxscale,
                                         yscale = Oyscale,
                                         global_b = True)
                ar_data.append([temp1])



            # Transformations defined in ini file


            if "pages" in config :
                pages_a = config["pages"].keys()
                if "@" + str(output_page_number) in pages_a :               # If the output page presently treated is referenced in [pages]
                    temp1 = config["pages"]["@" + str(output_page_number)]
                    transformations = temp1.split(", ")
                    for name_s in transformations :
                        if config.has_option(name_s, "globalRotation") :
                            gr_s = config[name_s.strip()]["globalRotation"]
                            gr_i = int(gr_s)
                            if gr_i == 90 :
                                newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(90)
                            elif gr_i == 180 :
                                newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(180)
                            elif gr_i == 270 :
                                newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(270)
                        else :
                            transform_s = self.calcMatrix(name_s, rows_i, columns_i)
                            ar_data.append([transform_s])




            if "output_conditions" in config :
                conditions_a = config["output_conditions"].keys()
                for line1 in conditions_a :
                    condition_s = config["output_conditions"][line1]
                    command_s, filters_s = condition_s.split("=>")
                    if (eval(command_s)) :
                        transformations = filters_s.split(", ")
                        for name_s in transformations :
                            if "globalRotation" in config[name_s.strip()] :
                                gr_s = config[name_s.strip()]["globalRotation"]
                                gr_i = int(gr_s)
                                if gr_i == 90 :
                                    newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(90)
                                elif gr_i == 180 :
                                    newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(180)
                                elif gr_i == 270 :
                                    newSheet[generic.NameObject("/Rotate")] = generic.NumberObject(270)
                            else :
                                transform_s = self.calcMatrix(name_s, rows_i, columns_i)
                                ar_data.append([transform_s])



            oString = ""
            
            # Check if we can use the new transformation approach
            # Conditions: autoscale enabled and no complex transformations
            use_new_transform = False
            if "options" in config and "autoscale" in config["options"]:
                if ini.readBoolean(config["options"]["autoscale"]) == True:
                    use_new_transform = True
            
            # Use new structured transformation approach
            if use_new_transform:
                structured_data = []
                for r, c in ar_layout:
                    if ar_pages[0] == []:
                        return
                    file_number, page_number = ar_pages[a][i].split(":")
                    file_number = int(file_number)
                    page_number = int(page_number)
                    if page_number < 0:
                        i += 1
                        continue  # blank page
                    
                    import copy
                    file_name = inputFiles_a[file_number]
                    newPage = copy.copy(inputFile_a[file_name].pages[page_number])
                    
                    # Apply booklet rotation if specified (Fix for Preview/Sequential mode)
                    try:
                         conf_key = f"{file_number}:{page_number+1}"
                         rot = 0
                         # Check direct key
                         if conf_key in config and "shuffler_rotate" in config[conf_key]:
                              rot = int(config[conf_key]["shuffler_rotate"])
                         # Check nested pages dict
                         elif "pages" in config and conf_key in config["pages"]:
                              pg = config["pages"][conf_key]
                              if hasattr(pg, "get"): 
                                  val = pg.get("shuffler_rotate")
                                  if val: rot = int(val)
                              elif isinstance(pg, dict) and "shuffler_rotate" in pg:
                                  rot = int(pg["shuffler_rotate"])
                         
                         if rot != 0:
                              newPage.rotate(rot)
                    except: pass
                    
                    # Calculate complete transformation using new function
                    transform = calculate_page_transform(
                        page=newPage,
                        row=r,
                        column=c,
                        ref_width=urx_i,
                        ref_height=ury_i,
                        output_width=mediabox_l[0],
                        output_height=mediabox_l[1],
                        output_scale=outputScale if outputScale != 1 else 1.0,
                        columns_i=columns_i,
                        rows_i=rows_i,
                        rotate_to_fit=False  # Don't auto-rotate for now
                    )
                    
                    structured_data.append((newPage, transform))
                    i += 1
                
                # Merge all pages with their transformations
                newSheet.mergePage3(structured_data)
            
            else:
                # Legacy approach with string-based transformations
                # Ready to create the page
                for r, c in ar_layout :         # We are creating the page in row r and column c
                    data_x = []
                    if ar_pages[0] == [] :      # system not yet initialised
                        return
                    file_number, page_number = ar_pages[a][i].split(":")
                    file_number = int(file_number)
                    page_number = int(page_number)
                    if (page_number < 0) :
                        i += 1
                        continue          # blank page


                    data_x.append("q\n")
                    # Create the transformation matrix for the page
                    matrix_s = self.transform(r, c, page_number, output_page_number, file_number)
                    if matrix_s == False :
                        return False
                    data_x.append(matrix_s)

                    # Booklets : option "creep"
                    if ini.booklet > 0 :                # This option makes sense only for booklets
                        creep_f1 = app.readmmEntry(app.arw["creep"])
                        if creep_f1 > 0 :
                            # calculate creep for each booklet (number of folios may vary)
                            for key, value in ar_cahiers.items() :
                                creep_f = creep_f1 / value

                            # reset to 0 for each booklet
                            # Starting page of each booklet
                            start_pages = [0]
                            mem = 0
                            for key, value in ar_cahiers.items() :
                                page_value = value * 2              # ar_cahiers gives the number of folios, not pages
                                start_pages.append(page_value + mem)
                                mem += page_value

                            # Calculate creep for a given page

                            for start_page in start_pages :
                                if output_page_number <= start_page :
                                    page_in_booklet = output_page_number - start_page   # page number inside a given booklet
                                    Htrans = creep_f * (int(page_in_booklet/2) - (page_in_booklet % 2))         # increment every two pages.
                                                            # It is a bit difficult to explain...
                                                            # We must get this :
                                                            #       page -5 => -3       External page
                                                            #       page -4 => -2
                                                            #       page -3 => -2
                                                            #       page -2 => -1
                                                            #       page -1 => -1
                                                            #       page 0  => 0        Internal page

                                    if c == 0 :
                                        data_x.append(self.calcMatrix2(Htrans , 0))     # shift left
                                    else :
                                        data_x.append(self.calcMatrix2((Htrans * -1), 0))  # shift right
                                    break


                    # scale the page to fit the output sheet, if required
                    if"autoscale" in config["options"]:
                        if ini.readBoolean(config["options"]["autoscale"]) == True :
                            (Rotate, scaleFactor_f, Htranslate, Vtranslate) = self.autoScaleAndRotate(file_number, page_number, c, r)
                            matrix1_s = self.calcMatrix2(Htranslate, Vtranslate, Scale = scaleFactor_f, Rotate = Rotate)
                            data_x.append(matrix1_s)

                    file_name = inputFiles_a[file_number]
                    newPage = inputFile_a[file_name].pages[page_number]

                    data_x.append(newPage)

                    # Add page number if required
                    # Choose font
                    try:
                        temp1 = newPage['/Resources'].get_object()
                        if isinstance(temp1, dict) :
                            temp2 = temp1['/Font'].get_object()
                            temp3 = temp2.keys()
                            if '/F1' in temp3 :
                                font = '/F1'
                            else :          # we get the first font in the list
                                for k in temp3 :
                                    font = k
                                    break
                    except :
                        pass            # Not critical. Default font will be used, but it does not show in the preview, that's why it is better to have an available font number.


                    if app.arw["page_numbers"].get_active() == True :
                        font_size = ini.readIntEntry(app.arw["numbers_font_size"], default = 18)
                        bottom_margin = ini.readIntEntry(app.arw["numbers_bottom_margin"], default = 20)
                        start_from = ini.readIntEntry(app.arw["numbers_start_from"])
                        position = urx_i / 2
                        if start_from <= page_number + 1 :
                            data_x.append(" q BT %s %d Tf  1 0 0 1 %d %d Tm (%d) Tj ET Q\n" % (font, font_size, position, bottom_margin, page_number + 1))
                    data_x.append("Q\n")
                    if len(ini.delete_rectangle) > 0 :
                        (x1,y1,w1,h1) = ini.delete_rectangle
                        data_x.append("q n 1 1 1 rg \n")        # Couleur RGB ; 1 1 1 = white; 0,0,0 = black
                        data_x.append(" n %d %d %d %d re f* Q\n" % (x1,y1,w1,h1))  # rectangle : x, y, width, height
                    ar_data.append(data_x)

                    i += 1

                aa = urx_i
                bb = ury_i


                datay = []
                for datax in ar_data :
                    datay += datax + ["\n"]


##            datay += ["q n 10 10 m 10 122 l S \n"]
##            datay += ["  n 10 10 m 72 10  l S \n"]
##            datay += ["Q\n"]
            # Only run legacy merge if we used the legacy approach (datay exists)
            if not use_new_transform:
                if preview > 0 :
                    newSheet.mergePage3(datay)                  # never use slow mode for preview
                elif ("slowMode" in app.arw
                       and app.arw["slowMode"].get_active() == 0) :        # normal mode
                            newSheet.mergePage3(datay)

                else :                                          # slow mode (uses mergePage instead of mergePage3)

                    dataz = ""
                    pages = []
                    end_code = ""
                    for data2 in datay :
                        if not isinstance(data2, str) :

                            pages.append([data2, dataz])
                            dataz = ""
                        else :
                            dataz += data2
                    if not (dataz == "" or len(pages) == 0) :    # skip blank pages

                        i = len(pages)
                        pages[i - 1].append(dataz)

                    for content in pages :
                        if len(content) == 3 :
                            end_code == content[2]
                        else :
                            end_code = ""
                        newSheet.mergeModifiedPage(content[0], content[1], end_code)



            if preview == -1 :      # if we are creating a real file (not a preview)
                message_s = _("Assembling pages: %s ")   % (ar_pages[a])
                app.print2( message_s , 1)
                app.status.set_text("page " + str(statusValue_i) + " / " + str(statusTotal_i))
                statusValue_i += 1
            output_page_number += 1
            while Gtk.events_pending():
                            Gtk.main_iteration()

        # Defer compression to end of process
        # Compress all pages at once for efficiency
        if preview == -1:  # Real file output only
            if ( "noCompress" in app.arw
                  and app.arw["noCompress"].get_active() == 0) :
                app.status.set_text(_("Compressing pages..."))
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                # Parallel compression using threads
                # zlib releases the GIL during compression, allowing true parallelism
                from concurrent.futures import ThreadPoolExecutor
                import os
                
                def compress_page(page):
                    page.compress_content_streams()
                    return True
                
                # Use available CPU cores for optimal parallelism
                num_workers = min(os.cpu_count() or 4, len(output.pages), 8)
                
                if num_workers > 1 and len(output.pages) > 1:
                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        list(executor.map(compress_page, output.pages))
                else:
                    # Sequential fallback for single page or single core
                    for page in output.pages:
                        page.compress_content_streams()

        time_e=time.time()

        #app.print2(_("Total length : %s ") % (time_e - time_s), 1)

        output.write(outputStream)
        if preview == -1 :          # if we are creating a real file (not a preview)
            outputStream.close()    # We must close the file, otherwise it is not possible to see it in the Reader
                                    # TODO : after closing the reader, preview should be automatically updated.

        del output

        if debug_b == 1 :
            logfile_f.close()

        # TODO
        """
        if preview == -1 :      # if we are creating a real file (not a preview)
            if app.settings.get_active() == 1 :
                app.saveProjectAs("",inputFile + ".ini")
        """
        return True




def printTree(curPage,out) :

        #curPage = source.pages[page]
        keys_a = list(curPage.keys())
        #temp1 = curPage["/Parent"].get_object()
        for j in keys_a :
            #if j in ["/Parent", "/Rotate", "/MediaBox", "/Type", "/Annots", "/Contents"] :
            if j in ["/Parent"] :
                continue
            temp1 = curPage[j].get_object()
            print("======> page "  + str(page) + "  " + j, file=out)
            print(temp1, file=out)
            if isinstance(temp1, dict) :
                for k in temp1 :
                    temp2 = temp1[k].get_object()
                    print(str(k) + " : ", end=' ', file=out)
                    print(temp2, file=out)
                    if isinstance(temp2, dict) :
                        for l in temp2 :
                            temp3 = temp2[l].get_object()
                            print(str(l) + " : ", end=' ', file=out)
                            print(temp3, file=out)
                            if isinstance(temp3, dict) :
                                for m in temp3 :
                                    temp4 = temp3[m].get_object()
                                    print(str(m) + " : ", end=' ', file=out)
                                    print(temp4, file=out)
                                    if isinstance(temp4, dict) :
                                        for n in temp4 :
                                            temp5 = temp4[n].get_object()
                                            print(str(n) + " : ", end=' ', file=out)
                                            print(temp5, file=out)

    #out.close()


def parseOptions() :
    global arg_a
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-r", "--rows", dest="rows_i",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-c", "--columns", dest="columns_i",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-n", "--numfolio", dest="numfolio",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-b", "--booklet", dest="booklet",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-a", "--appendPages", dest="appendPages",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-p", "--prependPages", dest="prependPages",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-s", "--selection", dest="selection",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-o", "--output", dest="outputFile",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-i", "--iniFile", dest="iniFile",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-e", "--referencePage", dest="referencePage",
                      help="write report to FILE", metavar="FILE")

    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    (option_v, arg_a) = parser.parse_args()


##    if None != option_v.iniFile :
##            ini_s = option_v.iniFile
##            parseIniFile(ini_s)


def extractBase() :
    """
    extract absolute path to script
    @return prog_s : absolute program path
    @return pwd_s : current working dir
    @return base_s : dirname of prog_s
    """

    # read current dir
    prog_s = sys.argv[0]
    pwd_s = os.path.abspath(".")
    name_s = os.path.basename(prog_s)
    _sep_s = '\\'

    # extract program path
    # if path starts with \ or x:\ absolute path
    if _sep_s == prog_s[0] or \
       (2 < len(prog_s) and \
        ":" == prog_s[1] and
        _sep_s == prog_s[2]) :
        base_s = os.path.dirname(prog_s)
    # if it starts with ./  , relative path
    elif 1 < len(prog_s) and \
         "." == prog_s[0] and \
         _sep_s == prog_s[1] :
        path_s = os.path.abspath(prog_s)
        base_s = os.path.dirname(path_s)
    # if it is in the active directory
    elif os.path.exists(os.path.join(pwd_s, prog_s)) or \
        os.path.exists(os.path.join(pwd_s, prog_s) + ".exe"):       # Necessary if the user starts the program without the extension (maggy, without .exe)
        path_s = os.path.join(pwd_s, prog_s)
        base_s = os.path.dirname(path_s)
    else :
        tab_a = os.environ["PATH"].split(":")
        limit = len(tab_a)
        found = False
        for scan in range(limit) :
            path_s = os.path.join(tab_a[scan], prog_s)
            if os.path.exists(path_s) :
                base_s = os.path.dirname(path_s)
                found = True
                break
        if not found :
            raise ScriptRt("path to program is undefined")

    # application base import
    return(name_s, pwd_s, base_s)


def sfp(path) :
    # sfp = set full path
    return os.path.join(prog_path_u, path)

def sfp2(file1) :
    # sfp2 = set full path, used for temporary directory
    try:
        return os.path.join(share_path_u, file1)
    except :
        time.sleep(1)                 # Sometimes there was a sort of conflict with another thread
        return os.path.join(share_path_u, file1)

def sfp3(file1) :
    # sfp3 = set full path, used for config directory
    try:
        return os.path.join(cfg_path_u, file1)
    except :
        time.sleep(1)                 # Sometimes there was a sort of conflict with another thread

def close_applicationx(self, widget, event=None, mydata=None):

    if Gtk.main_level():
        app.arw["window1"].destroy()
        Gtk.main_quit()
    else:
        sys.exit(0)

    return False

###########################################################################
# MAIN ####################################################################
###########################################################################

def main() :

    global EmbeddedPdfArranger, PDF_Doc, Page, Sides, Dims

    from pdfbooklet.pdfarranger_embed import EmbeddedPdfArranger, PDF_Doc, Page, Sides, Dims

    global isExcept
    global startup_b
    global preview_b
    global project_b
    global openedProject_u
    global areaAllocationW_i
    global areaAllocationH_i

    global base_a
    global prog_path_u
    global temp_path_u
    global cfg_path_u
    global share_path_u

    global rows_i
    global columns_i
    global step_i
    global outputScale
    global outputStream_mem
    global mem

    isExcept = False
    startup_b = True
    preview_b = True
    project_b = False
    openedProject_u = ""
    areaAllocationW_i = 1
    areaAllocationH_i = 1
    rows_i = 1
    columns_i = 2
    step_i = 1
    outputScale = 1
    outputStream_mem = ""
    mem = {}
    mem["update"] = time.time()

    base_a = extractBase()
    prog_path_u = unicode2(base_a[2])


    errorLog = sys.argv[0] + ".log"
    argv_a = sys.argv
    sys.argv = [sys.argv[0]]            # remove any parameter because they are not supported by EmbeddedPdfArranger
    if os.path.exists(sfp(errorLog)) :
        try :           # Sometimes the file may be locked
            os.remove(sfp(errorLog))
        except :
            pass

    # set directories for Linux and Windows

    if 'linux' in sys.platform :
        cfg_path_u = os.path.join(os.environ['HOME'], ".config", "pdfbooklet")
        if os.path.isdir(cfg_path_u) == False :
            os.mkdir(cfg_path_u)

        share_path_u = "/usr/share/pdfbooklet"
        if os.path.isdir(share_path_u) == False :
            os.mkdir(share_path_u)

    else:
        #TODO : this is not the recommended situation.
        cfg_path_u = prog_path_u
        share_path_u = prog_path_u



    #parseOptions()

    try:


        global render, app, parser, ini
        global inputFiles_a

        render = pdfRender()
        parser = myConfigParser()
        ini = TxtOnly(render)


        # command line processing
        if len(argv_a) > 2 and argv_a[2].strip() != "" :
            arg1 = argv_a[1]
            (name,ext) = os.path.splitext(arg1)     # determine file type from the extension
                                                    # TODO : determine from mimetype for Linux
            if ext == ".ini" :
               startup_b = False
               app = dummy()
               ini.openProject2(arg1)
               ini.output_page_size(1)
               app.pagesTr = copy.deepcopy(config)
               if render.parsePageSelection("1-20", 0) :

##                    self.readConditions()
                    ar_pages, ar_layout, ar_cahiers = render.createPageLayout()
                    if ar_pages != None :
                        render.createNewPdf(ar_pages, ar_layout, ar_cahiers, "test.pdf", -1)

            return True

        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        app = gtkGui(render)

        app.guiPresetsShow("booklet")
        app.resetTransformations(0)
        app.resetTransformations2(0)
        app.guiPresets(0)



        if os.path.isfile(sfp3("pdfbooklet.cfg")) == False :
            f1 = open(sfp3("pdfbooklet.cfg"), "w")
            f1.close()
        ini.parseIniFile(sfp3("pdfbooklet.cfg"))


        if len(argv_a) > 1 :            # a filename has been added in the command line
            if len(argv_a[1]) > 0 :     # this is not an empty string
                arg1 = argv_a[1]
                (name,ext) = os.path.splitext(arg1)     # determine file type from the extension
                                                        # TODO : determine from mimetype for Linux
                if ext == ".ini" :                      # If it is a project
                    startup_b = False
                    if not ini.openProject2(arg1) :     # if file not found
                        print ("Unknown file on the command line : " + arg1)
                    else :
                        app.arw["previewEntry"].set_text("1")
                    while Gtk.events_pending():
                                Gtk.main_iteration()
                    app.previewUpdate()

                    if len(argv_a) > 2 :
                        if argv_a[2].strip() == "-r" :
                            app.go("")          # TODO : should be go("", 0) but this creates errors
                            app.close_application("")

                elif ext == ".pdf" :
                    inputFiles_a = {}
                    inputFiles_a[1] = argv_a[1]
                    ini.loadPdfFiles()
                    app.selection_s = ""
                    app.arw["previewEntry"].set_text("1")
                    app.previewUpdate()
                else :
                    print("Unknown file type in the command line")


        startup_b = False

##        Gdk.threads_init()
##        Gdk.threads_enter()
        Gtk.main()
##        Gdk.threads_leave()

##        os._exit(0) # required because pdf-shuffler does not close correctly



    except :
        isExcept = True
        excMsg_s = "unexpected exception"
        (excType, excValue, excTb) = sys.exc_info()
        tb_a = traceback.format_exception(excType, excValue, excTb)
        for a in tb_a :
            print(a)

    # handle eventual exception
    if isExcept :

##        if app.shuffler != None :
##            app.shuffler.window.destroy()
        if Gtk.main_level():
##            Gtk.gdk.threads_enter()
            Gtk.main_quit()
##            Gtk.gdk.threads_leave()
            #os._exit(0)
            sys.exit(1)
        else:
            sys.exit(1)





# ---------------------------------------------------------------------
# Multiprocessing Worker Function
# ---------------------------------------------------------------------

def batch_render_worker(chunk_data, ar_layout, file_paths, output_params, config_params, debug_mode=False):
    """
    Worker function to render a chunk of pages in a separate process.
    
    Args:
        chunk_data: List of tuples (page_idx, [input_page_specs...])
        ar_layout: Layout list [(r, c), ...]
        file_paths: Dict {file_number: file_path}
        output_params: Tuple (mediabox_l, outputScale, columns_i, rows_i)
        config_params: Tuple (urx_i, ury_i)
        debug_mode: Boolean
        
    Returns:
        List of (page_idx, pdf_bytes) tuples
    """
    try:
        import io
        from pdfbooklet.pypdf import PdfWriter, PdfReader, PageObject
        from pdfbooklet.pypdf.generic import RectangleObject, NameObject
        
        # Unpack parameters
        mediabox_l, outputScale, columns_i, rows_i = output_params
        urx_i, ury_i = config_params
        
        # Open readers
        readers = {}
        for fid, path in file_paths.items():
            try:
                readers[fid] = PdfReader(path)
            except Exception as e:
                # Ignore file open errors in worker
                if debug_mode: print(f"Worker failed to open {path}: {e}")
                pass
            
        # Use single PdfWriter for the chunk to reduce overhead
        writer = PdfWriter()
        if not chunk_data: return []
        chunk_start_idx = chunk_data[0][0]
        
        for out_idx, page_specs in chunk_data:
            # Create blank page
            page = writer.add_blank_page(width=mediabox_l[0], height=mediabox_l[1])
            
            # Explicitly set cropbox
            page.mediabox.upper_right = (mediabox_l[0], mediabox_l[1])
            page.cropbox.upper_right = (mediabox_l[0], mediabox_l[1])
            
            structured_data = []
            
            # Loop through layout slots
            layout_idx = 0
            for r, c in ar_layout:
                if layout_idx >= len(page_specs):
                    break
                    
                spec = page_specs[layout_idx]
                if spec: 
                    try:
                        parts = spec.split(":")
                        file_n_str = parts[0]
                        page_n_str = parts[1]
                        rotation = 0
                        creep_x = 0
                        if len(parts) > 2:
                            rotation = int(parts[2])
                        if len(parts) > 3:
                            creep_x = float(parts[3])
                            
                        file_n = int(file_n_str)
                        page_n = int(page_n_str)
                        
                        if page_n >= 0 and file_n in readers:
                            reader = readers[file_n]
                            if page_n < len(reader.pages):
                                source_page = reader.pages[page_n]
                                
                                # Apply booklet rotation
                                if rotation != 0:
                                    source_page.rotate(rotation)
                                
                                # Calculate transformation
                                transform = calculate_page_transform(
                                    page=source_page,
                                    row=r,
                                    column=c,
                                    ref_width=config_params[0], # urx_i
                                    ref_height=config_params[1], # ury_i
                                    output_width=output_params[0][0],
                                    output_height=output_params[0][1],
                                    output_scale=output_params[1],
                                    columns_i=output_params[2],
                                    rows_i=output_params[3],
                                    rotate_to_fit=False # Rotation handled above
                                )
                                
                                # Apply Creep Offset
                                if creep_x != 0:
                                    transform = transform.translate(tx=creep_x, ty=0)
                                
                                # Merge transformed page
                                # Fix cropbox to avoid clipping
                                orig_crop = source_page.get("/CropBox")
                                large_crop = RectangleObject([-10000, -10000, 10000, 10000])
                                source_page[NameObject("/CropBox")] = large_crop
                                try:
                                    page.merge_transformed_page(source_page, transform)
                                finally:
                                    if orig_crop:
                                        source_page[NameObject("/CropBox")] = orig_crop
                                    elif "/CropBox" in source_page:
                                        del source_page["/CropBox"]
                    except Exception as e:
                        if debug_mode: print(f"Error processing spec {spec}: {e}")
                        pass
                        
                layout_idx += 1
            
                for item in structured_data:
                    pg, tr = item
                    # Fix cropbox for merge to avoid clipping
                    orig_crop = pg.get("/CropBox")
                    large_crop = RectangleObject([-10000, -10000, 10000, 10000])
                    pg[NameObject("/CropBox")] = large_crop
                    try:
                        page.merge_transformed_page(pg, tr)
                    finally:
                        if orig_crop:
                            pg[NameObject("/CropBox")] = orig_crop
                        elif "/CropBox" in pg:
                            del pg["/CropBox"]

            # Compress content
            page.compress_content_streams()
            
        # Serialize entire chunk
        bio = io.BytesIO()
        writer.write(bio)
        return [(chunk_start_idx, bio.getvalue())]
    except Exception as e:
        print(f"WORKER FAIL: {e}")
        import traceback
        try: traceback.print_exc()
        except: pass
        return []

if __name__ == '__main__' :
    main()
