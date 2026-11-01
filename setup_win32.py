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

VERSION = '3.1.7'

import os
import sys
try:
    from setuptools import Command
except ImportError:
    from distutils.cmd import Command
import shutil
import glob

# ---------------------------------------------------------------------------
# Helper functions (same pattern as pdfarranger upstream)
# ---------------------------------------------------------------------------

include_files = [
    # On Windows, pdfbooklet3.py sets share_path_u = prog_path_u (exe dir).
    # sfp2('data/pdfbooklet3.glade') resolves to <exe_dir>/data/pdfbooklet3.glade
    # So data must be at 'data/' relative to the exe, NOT share/pdfbooklet/data/
    ('pdfbooklet/data', 'data'),
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
    """Bundle compiled .mo locale files that are also present in locale/."""
    supported_langs = {
        d for d in os.listdir("locale")
        if os.path.isdir(os.path.join("locale", d))
    } if os.path.isdir("locale") else set()
    for path in glob.glob(
        os.path.join(sys.prefix, "share/locale/*/LC_MESSAGES/{}.mo".format(name))
    ):
        lang = os.path.split(os.path.split(os.path.split(path)[0])[0])[1]
        base_lang = lang.split("_")[0].split("@")[0]
        if not supported_langs or lang in supported_langs or base_lang in supported_langs:
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
# GObject Introspection typelibs required at runtime
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
    "Poppler-0.18",
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
# Safe bundle pruning (unused AV1/AVIF video codecs, Tcl/Tk, unused locales)
# ---------------------------------------------------------------------------
SAFE_PRUNE_DLL_PREFIXES = (
    'libaom',
    'libsvtav1enc',
    'librav1e',
    'libdav1d',
    'libavif',
    'libyuv',
    'libpixbufloader-avif',
    'pixbufloader-avif',
    'tcl86',
    'tk86',
)

SAFE_PRUNE_DIRS = (
    '_tcl_data',
    '_tk_data',
    'tcl8',
)

ALLOWED_LOCALE_DOMAINS = {
    'gtk30.mo',
    'gtk30-properties.mo',
    'glib20.mo',
    'gdk-pixbuf.mo',
    'pdfbooklet.mo',
    'pdfshuffler.mo',
}


def prune_windows_bundle(bundle_dir):
    """Safely remove unused codecs (AV1/AVIF), Tcl/Tk, and excess locales from a Windows build."""
    if not os.path.isdir(bundle_dir):
        return 0
    removed_bytes = 0
    supported_langs = {
        d for d in os.listdir("locale")
        if os.path.isdir(os.path.join("locale", d))
    } if os.path.isdir("locale") else {'ar', 'cs', 'de', 'el', 'es', 'fr', 'it'}

    for root, dirs, files in os.walk(bundle_dir, topdown=True):
        # 1. Remove Tcl/Tk data directories and __pycache__
        for d in list(dirs):
            if d in SAFE_PRUNE_DIRS or d == '__pycache__':
                full_d = os.path.join(root, d)
                for r2, _, f2 in os.walk(full_d):
                    for fn in f2:
                        try:
                            removed_bytes += os.path.getsize(os.path.join(r2, fn))
                        except OSError:
                            pass
                shutil.rmtree(full_d, ignore_errors=True)
                dirs.remove(d)

        # 2. Remove unused AV1/AVIF/Tcl/Tk binaries and duplicate source files
        for fn in list(files):
            low = fn.lower()
            full_f = os.path.join(root, fn)
            should_remove = False
            if low.endswith(('.dll', '.pyd')) and (
                low.startswith(SAFE_PRUNE_DLL_PREFIXES)
                or low.startswith('_tkinter')
                or low.startswith('_avif')
            ):
                should_remove = True
            elif low.endswith('.mo') and ('share' + os.sep + 'locale' in full_f):
                rel_loc = full_f.split('share' + os.sep + 'locale' + os.sep, 1)[1]
                lang = rel_loc.split(os.sep, 1)[0]
                base_lang = lang.split('_')[0].split('@')[0]
                if (lang not in supported_langs and base_lang not in supported_langs) or (
                    low not in ALLOWED_LOCALE_DOMAINS
                ):
                    should_remove = True
            elif low.endswith(('.py', '.pyc', '.po')) and (
                '_internal' + os.sep + 'pdfbooklet' in full_f
            ):
                # Duplicate source/bytecode files inside PyInstaller data folder
                should_remove = True

            elif low == 'loaders.cache':
                try:
                    with open(full_f, 'r', encoding='utf-8') as f_in:
                        cache_text = f_in.read()
                    blocks = [
                        b for b in cache_text.split('\n\n')
                        if 'pixbufloader-avif' not in b.lower()
                    ]
                    with open(full_f, 'w', encoding='utf-8') as f_out:
                        f_out.write('\n\n'.join(blocks))
                except OSError:
                    pass

            if should_remove:
                try:
                    removed_bytes += os.path.getsize(full_f)
                    os.remove(full_f)
                except OSError:
                    pass

    # 3. Clean empty locale directories
    for root, dirs, files in os.walk(bundle_dir, topdown=False):
        if not dirs and not files and root != bundle_dir:
            try:
                os.rmdir(root)
            except OSError:
                pass

    # 4. If this is a PyInstaller bundle (_internal/ exists), keep empty _tcl_data/_tk_data
    #    dirs (0 bytes) in case pyi_rth__tkinter was baked into the bootloader.
    internal_dir = os.path.join(bundle_dir, '_internal')
    if os.path.isdir(internal_dir):
        for tk_dir in ('_tcl_data', '_tk_data'):
            os.makedirs(os.path.join(internal_dir, tk_dir), exist_ok=True)

    return removed_bytes


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
        'keyboard',   # Windows-only: detect Ctrl key during drag & drop
    ],
    excludes=[
        'tkinter', '_tkinter', 'tcl', 'tk',
        'test', 'unittest', 'pydoc', 'sqlite3', 'xmlrpc',
        'PIL._avif', 'PIL.AvifImagePlugin',
    ],
    bin_excludes=[
        'libaom.dll', 'libSvtAv1Enc.dll', 'libSvtAv1Enc-2.dll', 'libSvtAv1Enc-3.dll',
        'librav1e.dll', 'libdav1d.dll', 'libdav1d-7.dll',
        'libavif.dll', 'libavif-16.dll', 'libyuv.dll',
        'libpixbufloader-avif.dll', 'tcl86.dll', 'tk86.dll',
    ],
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
class bdist_zip(Command):
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
        prune_windows_bundle(build_exe.build_exe)
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
if __name__ == '__main__':
    from cx_Freeze import setup, Executable
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
                # Disable console window for production builds
                base='gui',
                target_name='PdfBooklet.exe',
                icon='pdfbooklet/data/pdfbooklet.ico',
            )
        ],
    )
