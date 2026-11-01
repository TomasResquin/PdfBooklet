import os
import sys

def get_resource_path(filename, domain='pdfarranger'):
    """Finds a resource file cross-platform.
    
    Order of resolution:
    1. PyInstaller frozen bundle (_MEIPASS or executable directory)
    2. Local PdfBooklet source tree (pdfbooklet/data/)
    3. Deployed Linux packages (/usr/share/pdfbooklet/data/)
    4. Standard pdfarranger locations
    """
    # basedir is `pdfbooklet/pdfarranger/`
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. PyInstaller / frozen bundle locations
    if getattr(sys, 'frozen', False):
        for root in [getattr(sys, '_MEIPASS', ''), os.path.dirname(os.path.abspath(sys.executable))]:
            if root:
                for sub in ['data', os.path.join('share', domain)]:
                    f = os.path.join(root, sub, filename)
                    if os.path.exists(f):
                        return f

    # 2. Local fallback for PdfBooklet source tree execution
    # Allows running directly from cloning repo: pdfbooklet/data/
    pdfbooklet_data = os.path.join(os.path.dirname(basedir), 'data')
    f = os.path.join(pdfbooklet_data, filename)
    if os.path.exists(f):
        return f

    # 3. Custom fix for PdfBooklet integration (deployed packages)
    for p in ['/usr/share/pdfbooklet/data/', '/usr/local/share/pdfbooklet/data/']:
        f = os.path.join(p, filename)
        if os.path.exists(f):
            return f
            
    # 4. Standard locations for pdfarranger
    dirs = [
        os.path.join(basedir, 'share', domain, filename),
        os.path.join(basedir, 'data', filename),
        f'/usr/share/{domain}/{filename}',
        f'/usr/local/share/{domain}/{filename}'
    ]
    
    for f in dirs:
        if os.path.exists(f):
            return f
            
    # Default fallback if nothing exists (will probably throw FileNotFoundError on open)
    return os.path.join(basedir, 'data', filename)
