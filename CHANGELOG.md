# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.1.7] - 2026-11-01

### Added
- Added support for descending page ranges (e.g., 10-8) in the page selection parser.
- Added recursive resolution for inherited /Rotate and /CropBox attributes across parent nodes in the PDF page tree.

### Changed
- Restored outward creep adjustment behavior for both LTR and RTL layouts, ensuring inner pages shift consistently toward outer margins.
- Set Creep adjustment and manual translations to absolute physical millimeters on the output sheet.
- Enforced LC_NUMERIC = 'C' across the application and embedded PdfArranger to prevent decimal comma parsing errors on non-English locales.
- Updated application icons to official 64x64 RGBA assets.
- Updated Debian packaging scripts to dynamically bundle locales, icons, and Glade UI assets under /usr/share/pdfbooklet.
- Migrated Windows build and GitHub Actions CI workflow to MSYS2 UCRT64 environment.

### Fixed
- Fixed Form XObject placement in the rendering engine to properly preserve external clickable /URI links and handle non-zero CropBox origins.
- Fixed 270-degree auto-rotation translation offset and separated manual rotation from PdfArranger base rotations in calculate_page_transform.
- Fixed batch rendering crashes when exporting PDFs protected with a user password that were already unlocked in the session.
- Fixed IndexError and blank cell padding in non-booklet layouts (2-up, 4-up, Copies) when the last sheet is partially filled.
- Fixed crashes when loading multi-sheet custom templates (====) in User Defined layout mode.
- Fixed case-sensitivity mismatch for pageSelection when loading saved .ini project files.
- Fixed UI state errors when toggling transformation scope radio buttons ("This page" / "Pages in this position") without an active cell selection.
- Fixed out-of-range reference page fallback handling and constrained reference page and creep entry fields from stretching vertically.

### Removed
- Pruned unused AV1/AVIF codecs, Tcl/Tk data, and development files from the Windows standalone bundle, reducing total size by ~31%.

## [3.1.6] - 2026-05-16

### Added
- Created a complete Windows CI build pipeline via GitHub Actions using `cx_Freeze` for standalone `.exe` distribution.
- Added strict structural constraints to GTK/Glade layouts to prevent entry fields from improperly stretching across the UI.

### Changed
- Migrated core PDF processing engine from legacy `pypdf`/`pdfrw` to `pikepdf`, significantly improving rendering speed and memory utilization.
- Refactored core application structure to decouple GUI code from document processing logic by introducing `DocumentManagerMixin`.
- Completely rewrote the page transformation matrix engine to enforce strict mathematical post-multiplication for reliable scaling, translation, and rotation handling.
- Optimized the preview rendering pipeline by removing synchronous debugging loggers to improve scrolling and configuration responsiveness.

### Fixed
- Resolved pervasive page centering regressions that occurred when combining page rotation, custom output scaling, and manual translations.
- Fixed real-time preview synchronization for "Creep adjustment" and global transformations.
- Fixed critical Windows-specific GTK Drag-and-Drop (DnD) crashes triggered by dragging pages while holding modifier keys (Ctrl/Shift).

### Removed
- Pruned obsolete legacy files, unused helper functions, and deprecated third-party dependencies from the codebase.
