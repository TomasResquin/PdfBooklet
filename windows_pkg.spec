# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdfbooklet/pdfbooklet3.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pdfbooklet/data/*', 'pdfbooklet/data/')
    ],
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.GObject',
        'gi.repository.Gio',
        'gi.repository.Pango',
        'gi.repository.PangoCairo',
        'gi.repository.cairo',
        'gi.repository.GdkPixbuf',
        'gi.repository.Atk',
        'gi.repository.Poppler',
        'pikepdf'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['dev_scripts/win_build_helper.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PdfBooklet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='pdfbooklet/data/pdfbooklet.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PdfBooklet',
)
