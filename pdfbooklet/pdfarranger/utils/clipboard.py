import os
import hashlib
from urllib.request import url2pathname
from .platform import is_posix, is_windows

def get_file_path_from_uri(uri):
    """Extracts the path from an uri"""
    uri = uri[5:]  # remove 'file:'
    path = url2pathname(uri)  # escape special chars
    path = path.strip('\r\n\x00\x2F')  # remove \r\n and NULL and \
    if is_posix():
        path = '/' + path
    return path

def deserialize(data):
    """Deserialize data from copy & paste or drag & drop operation."""
    d = []
    while data:
        tmp = data.pop(0).split('///')
        filename = tmp[0]
        npage = int(tmp[1])
        if len(tmp) < 3:  # Only when paste files interleaved
            d.append((filename, npage))
        else:
            description = tmp[2]
            angle = int(tmp[3])
            scale = float(tmp[4])
            crop = [float(side) for side in tmp[5:9]]
            hide = [float(side) for side in tmp[9:13]]
            layerdata = []
            i = 13
            while i < len(tmp):  # If page has overlay/underlay
                lfilename = tmp[i]
                lnpage = int(tmp[i + 1])
                langle = int(tmp[i + 2])
                lscale = float(tmp[i + 3])
                laypos = tmp[i + 4]
                lcrop = [float(side) for side in tmp[i + 5:i + 9]]
                loffset = [float(offs) for offs in tmp[i + 9:i + 13]]
                layerdata.append([lfilename, lnpage, langle, lscale, laypos, lcrop, loffset])
                i += 13
            d.append((filename, npage, description, angle, scale, crop, hide, layerdata))
    return d

def parse_clipboard_text(data):
    """
    Parses string data from the clipboard.
    
    Returns:
        tuple: (data_list, data_is_filepaths, is_valid)
    """
    if not data:
        return [], False, True

    data_is_filepaths = False
    is_valid = True
    
    if data.startswith('pdfarranger-clipboard\n'):
        data = data.replace('pdfarranger-clipboard\n', '', 1)
        try:
            copy_hash = data[:data.index('\n')]
        except ValueError:
            copy_hash = None
        else:
            data = data.replace(copy_hash + '\n', '', 1)
            paste_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
        
        if copy_hash is not None and copy_hash == paste_hash:
            parsed_data = deserialize(data.split('\n;\n'))
            if not all(os.path.isfile(d[0]) for d in parsed_data):
                parsed_data = []
        else:
            parsed_data = []
            
        if len(parsed_data) == 0:
            is_valid = False
            
    else:
        data_is_filepaths = True
        if is_posix() and data.startswith('x-special/nautilus-clipboard\ncopy'):
            data = data.replace('x-special/nautilus-clipboard\ncopy', '', 1)
        rows = data.split('\n')
        rows = filter(None, rows)
        parsed_data = []
        for row in rows:
            if is_posix() and row.startswith('file:///'):  # Dolphin, Nautilus
                row = get_file_path_from_uri(row)
            elif is_windows() and row.startswith('"') and row.endswith('"'):
                row = row[1:-1]
            if os.path.isfile(row):
                parsed_data.append(row)
            else:
                parsed_data = []
                break
                
    return parsed_data, data_is_filepaths, is_valid
