<div align="center">

  <img src="pdfbooklet/data/pdfbooklet.png" width="96" alt="PdfBooklet Logo">

  # PdfBooklet

  **A powerful desktop application for creating booklets, multi-page imposition, and print preparation.**

  <p align="center">
    <a href="https://github.com/TomasResquin/PdfBooklet/releases/latest"><img src="https://img.shields.io/github/v/release/TomasResquin/PdfBooklet?color=blue&label=version" height="20" alt="Latest Release"></a>
    <a href="https://github.com/TomasResquin/PdfBooklet/actions"><img src="https://img.shields.io/github/actions/workflow/status/TomasResquin/PdfBooklet/python-package.yml?branch=master&label=build" height="20" alt="CI Build Status"></a>
    <a href="https://sourceforge.net/projects/pdfbooklet/files/latest/download"><img src="https://img.shields.io/sourceforge/dt/pdfbooklet.svg" height="20" alt="Download PdfBooklet (Total)"></a>
    <a href="https://sourceforge.net/projects/pdfbooklet/files/latest/download"><img src="https://img.shields.io/sourceforge/dm/pdfbooklet.svg" height="20" alt="Download PdfBooklet (Monthly)"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" height="20" alt="License: GPL v3"></a>
  </p>

  <p align="center">
    <a href="https://sourceforge.net/projects/pdfbooklet/files/latest/download"><img src="https://a.fsdn.com/con/app/sf-download-button" width="180" alt="Download PdfBooklet"></a>
  </p>

  <p align="center">
    <a href="https://github.com/TomasResquin/PdfBooklet/releases/latest/download/PdfBooklet-3.1.7-windows-portable.zip"><b>Windows Portable (.zip)</b></a> • 
    <a href="https://github.com/TomasResquin/PdfBooklet/releases/latest/download/pdfbooklet_3.1.7_all.deb"><b>Linux Debian (.deb)</b></a> • 
    <a href="https://sourceforge.net/projects/pdfbooklet/"><b>SourceForge Project</b></a>
  </p>

</div>

---

PdfBooklet is a comprehensive utility for creating booklets, manipulating PDF files, and preparing documents for precise, reliable printing workflows. Originally developed to generate booklets from existing PDFs, it has evolved into a complete imposition tool that handles margin adjustments, scaling, rotation, merging, splitting, and section binding.

---

## Quick Downloads

| Platform | Format | Description | Download Link |
| :--- | :--- | :--- | :---: |
| **Windows 10 / 11** | Standalone Portable ZIP | Pre-compiled, includes all dependencies. No installation required. | [**Download v3.1.7 (.zip)**](https://github.com/TomasResquin/PdfBooklet/releases/latest/download/PdfBooklet-3.1.7-windows-portable.zip) |
| **Linux** *(Ubuntu / Mint / Debian)* | Native `.deb` package | Automatically installs system dependencies (`pikepdf`, `poppler`, `gtk3`). | [**Download v3.1.7 (.deb)**](https://github.com/TomasResquin/PdfBooklet/releases/latest/download/pdfbooklet_3.1.7_all.deb) |
| **SourceForge Mirror** | All releases & files | Alternative mirrors, download stats, and historical archives. | <a href="https://sourceforge.net/p/pdfbooklet/"><img alt="Download PdfBooklet" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=394125" width="125" style="vertical-align:middle"></a> |

---

## Key Features

### Booklet Creation & Imposition
* **Multiple Booklets (Signatures):** Create a single folded booklet or split large documents into balanced multi-booklet signatures (e.g., 5 sheets per section for bookbinding).
* **Physical Creep Adjustment:** Compensate for paper thickness along the spine with exact millimeter calibration, preventing inner sheets from being cut off by the guillotine.
* **Flexible Imposition Layouts:** Booklet (saddle-stitch), Calendar (top-to-bottom), 2-up, 4-up, or custom grid dimensions.
* **Custom User-Defined Layouts:** Define multi-sheet custom imposing templates using manual page-number positioning.

### High-Fidelity pikepdf Engine
* **Lossless Vector Processing:** Uses Form XObjects (`/XObject /Form`) to encapsulate pages without rasterization or text stream alteration.
* **Hyperlink Preservation:** Retains active external clickable `/URI` annotations with transformed spatial coordinates.
* **Inherited Attribute Resolution:** Full ISO 32000 compliance, recursively resolving `/Rotate` and `/CropBox` across the `/Pages` tree hierarchy.

### Page Manipulation & Visual Shuffler
* **Visual Page Shuffler:** Interactive drag-and-drop interface (powered by PdfArranger) to reorder, duplicate, delete, and rotate individual pages.
* **Transformations & Overrides:** Adjust scale, margins, horizontal/vertical translation, and flips (per page, odd/even pages, or globally).
* **Real-Time Preview:** Synchronized layout preview with duplex alignment before exporting.

---

## Installation & Usage

### Windows (Portable)
1. Download **`PdfBooklet-3.1.7-windows-portable.zip`**.
2. Extract the ZIP to your desired location (e.g., Desktop, Documents, or USB drive).
3. Run **`PdfBooklet.exe`**.

### Linux (Debian / Ubuntu / Linux Mint)
Install the `.deb` package using `apt` so all system dependencies are automatically resolved:
```bash
sudo apt update
sudo apt install ./pdfbooklet_3.1.7_all.deb
```
Or run directly from your application menu or terminal with `pdfbooklet`.

### Running from Source
Ensure you have Python 3 and the required system libraries installed:
```bash
# Debian / Ubuntu / Mint dependencies
sudo apt install python3 python3-gi python3-gi-cairo python3-cairo python3-pikepdf \
    python3-dateutil python3-packaging gir1.2-gtk-3.0 gir1.2-poppler-0.18 gir1.2-handy-1

# Clone and run
git clone https://github.com/TomasResquin/PdfBooklet.git
cd PdfBooklet
python3 -m pdfbooklet.pdfbooklet3
```

---

## License

PdfBooklet is free and open-source software licensed under the **[GNU General Public License v3 (GPL-3.0)](LICENSE)**.
