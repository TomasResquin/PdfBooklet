"""
Windows portable build script for PdfBooklet.
Adapted from pdfarranger's setup_win32.py (https://github.com/pdfarranger/pdfarranger).

Usage (inside MSYS2 MINGW64 shell):
    /mingw64/bin/python3 setup_win32.py bdist_zip
    /mingw64/bin/python3 setup_win32.py bdist_msi   # optional installer

Requires MSYS2 packages:
    mingw-w64-x86_64-python-cx-freeze
    mingw-w64-x86_64-gtk3
    mingw-w64-x86_64-python-gobject
    mingw-w64-x86_64-python-cairo
    mingw-w64-x86_64-poppler
    mingw-w64-x86_64-libhandy
    mingw-w64-x86_64-python-pikepdf
    ...and pip install keyboard
"""

VERSION = '3.1.6'

from cx_Freeze import setup, Executable
import os
import sys
import distutils
import shutil
import glob

# ---------------------------------------------------------------------------
# Helper functions (same pattern as pdfarranger upstream)
# ---------------------------------------------------------------------------

include_files = [
    # PdfBooklet application data
    ('pdfbooklet/data', 'share/pdfbooklet/data'),
]


def addfile(relpath, warn_missing=True):
    """Add a file from sys.prefix (MSYS2 MINGW64 prefix) into the bundle."""
    f = os.path.join(sys.prefix, relpath)
    if not os.path.isfile(f):
        if warn_missing:
            print("WARNING: {} cannot be found.".format(f), file=sys.stderr)
    else:
        include_files.append((f, relpath))


def adddir(relpath, warn_missing=True):
    """Add a whole directory from sys.prefix into the bundle."""
    d = os.path.join(sys.prefix, relpath)
    if not os.path.isdir(d):
        if warn_missing:
            print("WARNING: dir {} cannot be found.".format(d), file=sys.stderr)
    else:
        include_files.append((d, relpath))


def addlocale(name):
    """Bundle compiled .mo locale files that are also present in build/mo."""
    # PdfBooklet has its own locale dir at the project root
    for path in glob.glob(
        os.path.join(sys.prefix, "share/locale/*/LC_MESSAGES/{}.mo".format(name))
    ):
        lang = os.path.split(os.path.split(os.path.split(path)[0])[0])[1]
        addfile(os.path.relpath(path, sys.prefix))


# ---------------------------------------------------------------------------
# GTK locale (gtk30 translations so native file dialogs are translated)
# ---------------------------------------------------------------------------
addlocale("gtk30")

# ---------------------------------------------------------------------------
# PdfBooklet own locale
# ---------------------------------------------------------------------------
for path in glob.glob('locale/*/LC_MESSAGES/*.mo'):
    include_files.append((path, path))

# ---------------------------------------------------------------------------
# GObject Introspection typelibs — CRITICAL, this is what PyInstaller missed
# Every gi.require_version() call needs its .typelib present at runtime.
# ---------------------------------------------------------------------------
required_gi_namespaces = [
    "Gtk-3.0",
    "Gdk-3.0",
    "cairo-1.0",
    "Pango-1.0",
    "PangoCairo-1.0",
    "GObject-2.0",
    "GLib-2.0",
    "Gio-2.0",
    "GdkPixbuf-2.0",
    "GModule-2.0",
    "Atk-1.0",
    "Poppler-0.18",      # <-- the one that was failing with PyInstaller
    "HarfBuzz-0.0",
    "Handy-1",
    "freetype2-2.0",
]

for ns in required_gi_namespaces:
    addfile("lib/girepository-1.0/{}.typelib".format(ns))

# ---------------------------------------------------------------------------
# Specific DLLs not automatically picked up by cx_Freeze
# ---------------------------------------------------------------------------
required_dlls = [
    'poppler-glib-8',
    'handy-1-0',
]
for dll in required_dlls:
    fn = 'lib' + dll + '.dll'
    f = os.path.join(sys.prefix, 'bin', fn)
    if os.path.isfile(f):
        include_files.append((f, fn))
    else:
        print("WARNING: DLL {} not found".format(f), file=sys.stderr)

# ---------------------------------------------------------------------------
# GDK Pixbuf loaders (needed so GTK can render PNG/SVG/BMP images)
# ---------------------------------------------------------------------------
addfile("lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-bmp.dll",  warn_missing=False)
addfile("lib/gdk-pixbuf-2.0/2.10.0/loaders/pixbufloader_svg.dll",      warn_missing=False)
addfile("lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-png.dll",   warn_missing=False)
# Some MSYS2 versions use different loader paths — try alternatives
addfile("lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll",   warn_missing=False)
addfile("lib/gdk-pixbuf-2.0/2.10.0/loaders.cache")

# ---------------------------------------------------------------------------
# GSettings compiled schemas (GTK reads these for its own settings)
# ---------------------------------------------------------------------------
addfile("share/glib-2.0/schemas/gschemas.compiled")

# ---------------------------------------------------------------------------
# Icon themes (Adwaita + hicolor fallback)
# ---------------------------------------------------------------------------
def addicons():
    addfile("share/icons/hicolor/index.theme")
    addfile("share/icons/Adwaita/index.theme", warn_missing=False)
    # Folder / generic file icons used in file chooser dialogs
    for i in ['places/folder', 'mimetypes/text-x-generic']:
        addfile(os.path.join('share/icons/Adwaita/16x16/', i + '.png'), warn_missing=False)
    # Symbolic SVG icons used in the pdfarranger toolbar
    icons = [
        'places/user-desktop',
        'places/user-home',
        'actions/bookmark-new',
        'actions/document-open-recent',
        'actions/folder-new',
        'actions/list-add',
        'actions/list-remove',
        'actions/media-eject',
        'actions/document-save',
        'actions/document-save-as',
        'actions/document-open',
        'actions/insert-image',
        'actions/object-rotate-left',
        'actions/object-rotate-right',
        'actions/open-menu',
        'actions/zoom-in',
        'actions/zoom-out',
        'actions/go-up',
        'actions/go-down',
        'ui/pan-down',
        'ui/pan-end',
        'ui/pan-start',
        'ui/pan-up',
        'ui/window-close',
        'ui/window-maximize',
        'ui/window-minimize',
        'ui/window-restore',
        'devices/drive-harddisk',
        'devices/drive-optical',
        'places/folder-documents',
        'places/folder-download',
        'places/folder-music',
        'places/folder-pictures',
        'places/folder-videos',
        'places/user-trash',
    ]
    for i in icons:
        addfile(
            os.path.join('share/icons/Adwaita/symbolic/', i + '-symbolic.svg'),
            warn_missing=False,
        )

addicons()

# ---------------------------------------------------------------------------
# Poppler data: encoding tables for CJK, Cyrillic, etc.
# ---------------------------------------------------------------------------
poppler_data_src = os.path.join(sys.prefix, 'share/poppler/')
if os.path.isdir(poppler_data_src):
    include_files.append((poppler_data_src, 'share/poppler/'))
else:
    print("WARNING: share/poppler/ not found — CJK/Cyrillic PDF support may be broken",
          file=sys.stderr)

# ---------------------------------------------------------------------------
# gspawn helper — needed so Gtk.show_uri() can open web links
# ---------------------------------------------------------------------------
gspawn = os.path.join(sys.prefix, 'bin', 'gspawn-win64-helper.exe')
if os.path.isfile(gspawn):
    include_files.append((gspawn, 'gspawn-win64-helper.exe'))

# ---------------------------------------------------------------------------
# cx_Freeze build options
# ---------------------------------------------------------------------------
build_options = dict(
    packages=[
        'gi',
        'pikepdf',
        'pdfbooklet',
        'pdfbooklet.pdfarranger',
        'pdfbooklet.pdfarranger.utils',
    ],
    excludes=['tkinter', 'test'],
    include_files=include_files,
)

# ---------------------------------------------------------------------------
# MSI installer options (optional — used with bdist_msi)
# ---------------------------------------------------------------------------
msi_options = dict(
    target_name='PdfBooklet-{}-windows-installer.msi'.format(VERSION),
    upgrade_code='{c1e2f3a4-b5d6-7890-abcd-ef1234567890}',
    extensions=[{
        "extension": "pdf",
        "verb": "open",
        "executable": "PdfBooklet.exe",
        "argument": '"%1"',
    }],
)


# ---------------------------------------------------------------------------
# bdist_zip: portable ZIP distribution (no install needed)
# Adapted directly from pdfarranger's bdist_zip command.
# ---------------------------------------------------------------------------
class bdist_zip(distutils.cmd.Command):
    """Create a Windows portable .zip distribution."""
    description = 'create a "zip" distribution'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        build_base = self.get_finalized_command('build').build_base
        build_exe = self.get_finalized_command('build_exe')
        fullname = self.distribution.get_fullname()
        build_exe.build_exe = os.path.join(build_base, fullname)
        build_exe.run()
        dist_dir = self.get_finalized_command('bdist').dist_dir
        archname = os.path.join(
            dist_dir,
            'PdfBooklet-{}-windows-portable'.format(VERSION),
        )
        self.make_archive(archname, 'zip', root_dir=build_base, base_dir=fullname)
        shutil.rmtree(build_exe.build_exe)


# ---------------------------------------------------------------------------
# setup()
# ---------------------------------------------------------------------------
setup(
    name='PdfBooklet',
    author='GAF Software / Tomas Julian Resquin',
    version=VERSION,
    description='A simple application for creating booklets and other layouts from PDF files',
    options=dict(build_exe=build_options, bdist_msi=msi_options),
    cmdclass={'bdist_zip': bdist_zip},
    packages=['pdfbooklet', 'pdfbooklet.pdfarranger', 'pdfbooklet.pdfarranger.utils'],
    executables=[
        Executable(
            'pdfbooklet/pdfbooklet3.py',
            base='Win32GUI' if sys.platform == 'win32' else None,
            target_name='PdfBooklet.exe',
            icon='pdfbooklet/data/pdfbooklet.ico',
        )
    ],
)
