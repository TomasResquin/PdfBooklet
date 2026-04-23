import os
import sys
import mimetypes
import hashlib
from gi.repository import Gtk, GObject

from . import pageutils
from . import splitter
from . import exporter
from . import metadata
from .core import PageAdder, PDFDocError
from .utils.clipboard import deserialize

class DocumentManagerMixin:
    """
    Mixin class for PdfArranger to handle PDF manipulation logic and GUI actions.
    This separates the core document transactions (split, merge, copy, paste) 
    from the main application initialization.
    """

    def copy_pages(self, add_hash=True, deserialize=False):
        """Collect data from selected pages"""

        model = self.iconview.get_model()
        selection = self.iconview.get_selected_items()
        selection.sort(key=lambda x: x.get_indices()[0])

        data = []
        for path in selection:
            it = model.get_iter(path)
            data.append(model.get_value(it, 0).serialize())

        if data:
            if deserialize:
                return deserialize(data)
            data = '\n;\n'.join(data)
            if add_hash:
                h = hashlib.sha256(data.encode('utf-8')).hexdigest()
                data = h + '\n' + data
        return data

    def paste_pages(self, data, before, ref_to, select_added):
        """Paste pages to iconview"""

        pageadder = PageAdder(self)
        if ref_to:
            pageadder.move(ref_to, before)

        for d in data:
            added = pageadder.addpages(*d)
            if not added:
                break
        return pageadder.commit(select_added, add_to_undomanager=True)

    def paste_files(self, filepaths, before, ref_to):
        """Paste files to iconview."""
        pageadder = PageAdder(self)

        for filepath in filepaths:
            pageadder.move(ref_to, before)
            added = pageadder.addpages(filepath)
            if not added:
                break
        pageadder.commit(select_added=False, add_to_undomanager=True)

    def paste_pages_interleave(self, data, before, ref_to):
        """Paste pages or files interleved to iconview."""
        pageadder = PageAdder(self)
        model = self.iconview.get_model()
        scroll = len(model) > 0
        iter_to = None
        iref = ref_to.get_path().get_indices()[0] if ref_to else 0

        self.undomanager.commit("Paste")
        self.set_unsaved(True)

        for d in data:
            added = pageadder.addpages(*d)
            if not added:
                break

            pageadder.move(ref_to, before)
            pageadder.commit(select_added=False, add_to_undomanager=False)

            if ref_to:
                path = ref_to.get_path()
                iter_to = model.get_iter(path)
                iter_to = model.iter_next(iter_to)
                if not before:
                    iter_to = model.iter_next(iter_to)
            if iter_to:
                path = model.get_path(iter_to)
                ref_to = Gtk.TreeRowReference.new(model, path)
            else:
                ref_to = None

        if scroll:
            iscroll = iref if before else iref + 1
            scroll_path = Gtk.TreePath.new_from_indices([iscroll])
            self.iconview.scroll_to_path(scroll_path, False, 0, 0)

    def on_action_delete(self, _action, _parameter, _unknown):
        """Removes the selected elements in the IconView"""
        self.clear_selected()

    def on_action_cut(self, _action, _param, _unknown):
        """Cut selected pages to clipboard."""
        data = self.copy_pages()
        self.clipboard.set_text('pdfarranger-clipboard\n' + data, -1)
        self.clear_selected()
        self.window.lookup_action("paste").set_enabled(True)

    def on_action_copy(self, _action, _param, _unknown):
        """Copy selected pages to clipboard."""
        data = self.copy_pages()
        self.clipboard.set_text('pdfarranger-clipboard\n' + data, -1)
        self.window.lookup_action("paste").set_enabled(True)

    def on_action_paste(self, _action, mode, _unknown):
        """Paste pages, file paths or an image from clipboard."""
        data, data_is_filepaths = self.read_from_clipboard()
        if not data:
            return

        pastemodes = {0: 'AFTER', 1: 'BEFORE', 2: 'ODD', 3: 'EVEN', 4: 'OVERLAY', 5: 'UNDERLAY'}
        pastemode = pastemodes[mode.get_int32()]

        ref_to, before = self.set_paste_location(pastemode)

        if pastemode in ['AFTER', 'BEFORE']:
            if data_is_filepaths:
                self.paste_files(data, before, ref_to)
            else:
                self.paste_pages(data, before, ref_to, select_added=False)
        elif pastemode in ['ODD', 'EVEN']:
            if data_is_filepaths:
                # Generate data to send to paste_pages_interleave
                filepaths = []
                try:
                    for filepath in data:
                        filemime = mimetypes.guess_type(filepath, strict=False)[0]
                        if not filemime:
                            raise PDFDocError(filepath + ':\n' + _('Unknown file format'))
                        if filemime == 'application/pdf':
                            num_pages = exporter.num_pages(filepath)
                            if num_pages is None:
                                raise PDFDocError(filepath + ':\n' + _('PDF document is damaged'))
                            for page in range(1, num_pages + 1):
                                filepaths.append((filepath, page))
                        elif filemime.split('/')[0] == 'image':
                            filepaths.append((filepath, 1))
                        else:
                            raise PDFDocError(filepath + ':\n' + _('File is neither pdf nor image'))
                except PDFDocError as e:
                    print(e.message, file=sys.stderr)
                    self.error_message_dialog(e.message)
                    return
                data = filepaths
            self.paste_pages_interleave(data, before, ref_to)
            self.update_iconview_geometry()
            GObject.idle_add(self.retitle)
            self.iv_selection_changed()
            self.update_max_zoom_level()
            self.silent_render()
        elif pastemode in ['OVERLAY', 'UNDERLAY'] and not data_is_filepaths:
            selection = self.iconview.get_selected_items()
            self.paste_as_layer_dialog(data, selection, laypos=pastemode)

    def insert_blank_page(self, _action, _option, _unknown):
        size = None
        selection = self.iconview.get_selected_items()
        selection.sort()
        model = self.iconview.get_model()
        if len(selection) > 0:
            size = model[selection[-1]][0].size_in_mm()
        page_size = pageutils.BlankPageDialog(size, self.window).run_get()
        if page_size is not None:
            adder = PageAdder(self)
            if len(selection) > 0:
                adder.move(Gtk.TreeRowReference.new(model, selection[-1]), False)
            file, _ = exporter.get_blank_doc(adder, self.pdfqueue, self.tmp_dir, page_size)
            if file is None:
                return
            adder.addpages(file)
            adder.commit(select_added=False, add_to_undomanager=True)

    def rotate_page_action(self, _action, angle, _unknown):
        """Rotates the selected page in the IconView"""
        self.undomanager.commit("Rotate")
        angle = angle.get_int32()
        selection = self.iconview.get_selected_items()
        if self.rotate_page(selection, angle):
            self.set_unsaved(True)
            self.update_statusbar()

    def rotate_page(self, selection, angle):
        model = self.iconview.get_model()
        rotated = False
        page_width_old = max(p.width_in_points() for p, _ in self.model)
        page_height_old = max(p.height_in_points() for p, _ in self.model)
        for path in selection:
            treeiter = model.get_iter(path)
            p = model.get_value(treeiter, 0)
            if p.rotate(angle):
                rotated = True
                model.set_value(treeiter, 0, p)
        self.update_iconview_geometry()
        page_width_new = max(p.width_in_points() for p, _ in self.model)
        page_height_new = max(p.height_in_points() for p, _ in self.model)
        if page_width_old != page_width_new or page_height_old != page_height_new:
            self.scroll_to_selection()
        return rotated

    def split_pages(self, _action, _parameter, _unknown):
        """ Split selected pages """
        diag = splitter.Dialog(self.window)
        leftcrops, topcrops = diag.run_get()
        if leftcrops is None or topcrops is None:
            return
        model = self.iconview.get_model()
        self.set_unsaved(True)
        self.undomanager.commit("Split")
        # selection is a list of 1-tuples, not in order
        selection = self.iconview.get_selected_items()
        selection.sort(key=lambda x: x.get_indices()[0])
        ref_list = [Gtk.TreeRowReference.new(model, path)
                    for path in selection]
        with self.render_lock():
            # This is not an unimposition process, simply splitting pages in the order they appear
            for ref in ref_list:
                iterator = model.get_iter(ref.get_path())
                page = model.get_value(iterator, 0)
                page.resample = -1
                newpages = page.split(leftcrops, topcrops)
                # Here newpages only contains n-1 new pages when splitting into n pages,
                # because the upper-lefter-most page is still our good old `page` instance
                for p in newpages:
                    p.resample = -1
                    model.insert_after(iterator, [p, p.description])
                model.set_value(iterator, 0, page)
        self.update_iconview_geometry()
        self.iv_selection_changed()
        self.update_max_zoom_level()
        GObject.idle_add(self.render)

    def duplicate(self, _action, _parameter, _unknown):
        """Duplicates the selected elements"""

        self.set_unsaved(True)
        self.undomanager.commit("Duplicate")

        model = self.iconview.get_model()
        # selection is a list of 1-tuples, not in order
        selection = self.iconview.get_selected_items()
        selection.sort(key=lambda x: x.get_indices()[0])
        ref_list = [Gtk.TreeRowReference.new(model, path)
                    for path in selection]
        with self.render_lock():
            for ref in ref_list:
                iterator = model.get_iter(ref.get_path())
                page = model.get_value(iterator, 0).duplicate()
                model.insert_after(iterator, [page, page.description])
        self.iv_selection_changed()
        GObject.idle_add(self.render)

    @staticmethod
    def reverse_order_available(selection):
        """Determine whether the selection is suitable for the
           reverse-order command: the selection must be a multiple and
           contiguous range of pages.
        """
        if len(selection) < 2:
            return False

        # selection is a list of 1-tuples, not in order
        indices = sorted([i[0] for i in selection])
        first = indices[0]
        last = indices[-1]
        contiguous = (len(indices) == last - first + 1)

        return contiguous

    def reverse_order(self, _action, _parameter, _unknown):
        """Reverses the selected elements in the IconView"""

        model = self.iconview.get_model()
        selection = self.iconview.get_selected_items()

        # selection is a list of 1-tuples, not in order
        indices = sorted([i[0] for i in selection])
        first = indices[0]
        last = indices[-1]

        self.set_unsaved(True)
        indices.reverse()
        new_order = list(range(first)) + indices + list(range(last + 1, len(model)))
        self.undomanager.commit("Reorder")
        with self.render_lock():
            model.reorder(new_order)
        GObject.idle_add(self.render)

    def generate_booklet(self, _action, _option, _unknown):
        selection = self.iconview.get_selected_items()
        _sizes, max_size, equal_size = self.get_size_info(selection)

        # Need uniform page size.
        if not equal_size:
            msg = _('All pages must have the same size.')
            self.error_message_dialog(msg)
            return
        self.undomanager.commit("generate booklet")

        data = self.copy_pages(add_hash=False, deserialize=True)
        self.clear_selected(add_to_undomanager=False)
        self.iconview.unselect_all()

        adder = PageAdder(self)
        blank_page_count = 0 if len(data) % 4 == 0 else 4 - len(data) % 4
        npages = len(data) + blank_page_count
        nbooklet = npages // 2
        ndpage = selection[-1].get_indices()[0]
        before = ndpage < len(self.model)
        ref = Gtk.TreeRowReference.new(self.model, selection[-1]) if before else None
        w, h = max_size
        a = adder, self.pdfqueue, self.tmp_dir, (w * 2, h), nbooklet
        file = exporter.get_blank_doc(*a)[0]
        adder.move(ref, before)
        adder.addpages(file)
        adder.commit(select_added=True, add_to_undomanager=False)
        self.update_iconview_geometry()
        self.update_max_zoom_level()

        for i in range(nbooklet):
            even = i % 2 == 0
            first_id = -i - 1 if even else i
            second_id = i if even else -i - 1
            if first_id < 0:
                first_id += npages
            if second_id < 0:
                second_id += npages
            destination = self.model[ndpage + i].path
            if first_id < len(data):
                self.paste_as_layer([data[first_id]], destination, 'OVERLAY', (0, 0.5))
            if second_id < len(data):
                self.paste_as_layer([data[second_id]], destination, 'OVERLAY', (1, 0.5))

    def split_booklet(self, _action, _option, _unknown):
        """ Split selected pages as a booklet (unimposition) """
        # selection is a list of 1-tuples, not in order
        selection = self.iconview.get_selected_items()
        selected_page_numbers = sorted_selection_indices(selection)

        if not is_selection_contiguous(selected_page_numbers):
            msg = _('The page selection is not contiguous. Cannot unimpose.')
            self.error_message_dialog(msg)
            return

        model = self.iconview.get_model()
        ref_list = [Gtk.TreeRowReference.new(model, path)
                    for path in selection]
        pages = [model.get_value(model.get_iter(ref.get_path()), 0)
                 for ref in ref_list]

        # Need uniform page size.
        if not is_same_page_size(pages):
            msg = _('All pages must have the same size.')
            self.error_message_dialog(msg)
            return

        # Simulate split window
        horizontal = [[1, 100]]
        vertical = [[1, 50], [2, 50]]

        leftcrops, topcrops = splitter._crops(vertical), splitter._crops(horizontal)

        self.set_unsaved(True)
        self.undomanager.commit("split booklet")
        with self.render_lock():
            offset = selected_page_numbers[0]
            halves = len(selected_page_numbers) * 2

            count = 0
            half_pages = [ None for x in range(0, halves) ]

            for ref in ref_list:
                iterator = model.get_iter(ref.get_path())
                page = model.get_value(iterator, 0)
                page.resample = -1

                splits = page.split(leftcrops, topcrops)
                assert len(splits) == 1
                rpage = splits[0]
                rpage.resample = -1

                lpageentry = [ page, page.description ]
                rpageentry = [ rpage, rpage.description ]

                if count % 2 == 0:
                    half_pages[halves - count - 1] = lpageentry
                    half_pages[count] = rpageentry
                else:
                    half_pages[count] = lpageentry
                    half_pages[halves - count - 1] = rpageentry
                count += 1

                model.remove(iterator)

            for p in half_pages:
                model.append(p)

            final_page_number = len(self.model)
            reorder_pages = [ None for x in range(0, final_page_number) ]
            half_count = 0

            for x in range(0, final_page_number):
                if x < offset:
                    reorder_pages[x] = x
                elif x < (final_page_number - halves):
                    reorder_pages[x + halves] = x
                else:
                    reorder_pages[half_count + offset] = x
                    half_count += 1

            self.model.reorder(reorder_pages)

        self.update_iconview_geometry()
        self.iv_selection_changed()
        self.update_max_zoom_level()
        GObject.idle_add(self.render)



    def get_size_info(self, selection):
        sizes = [self.model[row][0].size_in_points() for row in reversed(selection)]
        max_width = max(s[0] for s in sizes)
        min_width = min(s[0] for s in sizes)
        max_height = max(s[1] for s in sizes)
        min_height = min(s[1] for s in sizes)
        equal = max_width - min_width < 1e-2 and max_height - min_height < 1e-2
        return sizes, (max_width, max_height), equal

    def merge_pages(self, _action, _parameter, _unknown):
        """Merge selected pages."""
        selection = self.iconview.get_selected_items()
        if not self.is_paste_layer_available(selection):
            return
        data = self.copy_pages(add_hash=False, deserialize=True)
        sizes, max_size, equal = self.get_size_info(selection)
        r = pageutils.MergePagesDialog(self.window, max_size, equal).run_get()
        if r is None:
            return
        cols, rows, add_order, size = r
        self.undomanager.commit("Merge")
        self.set_unsaved(True)
        self.clear_selected()
        self.iconview.unselect_all()

        ndpage = selection[-1].get_indices()[0]
        before = ndpage < len(self.model)
        ref = Gtk.TreeRowReference.new(self.model, selection[-1]) if before else None
        wdpage, hdpage = size[0] * cols, size[1] * rows
        ndpages = -(len(data) // -(cols * rows))
        adder = PageAdder(self)
        a = adder, self.pdfqueue, self.tmp_dir, (wdpage, hdpage), ndpages
        file, _ = exporter.get_blank_doc(*a)
        if file is None:
            return
        adder.move(ref, before)
        adder.addpages(file)
        adder.commit(select_added=True, add_to_undomanager=False)

        nlpage = 0
        while ndpage < len(self.model) and nlpage < len(data):
            for row, col in add_order:
                wlpage, hlpage = sizes[nlpage]
                wdiff, hdiff = wdpage - wlpage, hdpage - hlpage
                off_x = off_y = 0.5
                if wdiff != 0:
                    off_x = (col * wdpage / cols + 0.5 * wdpage / cols - wlpage / 2) / wdiff
                if hdiff != 0:
                    off_y = (row * hdpage / rows + 0.5 * hdpage / rows - hlpage / 2) / hdiff
                dest = self.model[ndpage].path
                self.paste_as_layer([data[nlpage]], dest, 'OVERLAY', (off_x, off_y))
                nlpage += 1
                if nlpage > len(data) - 1:
                    break
            ndpage += 1
        self.update_iconview_geometry()
        self.update_max_zoom_level()

    def edit_metadata(self, _action, _parameter, _unknown):
        files = [(pdf.copyname, pdf.password) for pdf in self.pdfqueue]
        if metadata.edit(self.metadata, files, self.window):
            self.set_unsaved(True)

    def page_size_dialog(self, _action, _parameter, _unknown):
        """Opens a dialog box to define page size."""
        selection = self.iconview.get_selected_items()
        diag = pageutils.ScaleDialog(self.iconview.get_model(), selection, self.window)
        result = diag.run_get()
        if result is None:
            return
        newscale, mode = result
        if mode == 'SCALE':
            self.undomanager.commit("Scale")
            if not pageutils.scale(self.model, selection, newscale):
                return
        elif mode == 'SCALE-ADD-MARG':
            self.undomanager.commit("Scale & add margins")
            pageutils.scale(self.model, selection, newscale)
            self.center_on_blank_page(selection, newscale)
        else:
            self.undomanager.commit("Crop & add margins")
            self.center_on_blank_page(selection, newscale)
        self.set_unsaved(True)
        self.update_statusbar()
        self.update_iconview_geometry()
        self.update_max_zoom_level()
        self.scroll_to_selection(center=False)
        GObject.idle_add(self.render)

    def range_select_dialog(self):
        """Opens a dialog box to range select"""
        model = self.iconview.get_model()
        diag = pageutils.RangeSelectDialog(self.window)
        range_selected = diag.run_get()
        # clean up the selection and split the ranges
        if range_selected is not None:
            result_list = []
            # split the string using commas
            comma_split = range_selected.split(',')
            for element in comma_split:
                element = element.strip()
                # check if the element has a dash
                # Consider multiple dashes? Might create problems?
                if '-' in element and element.count('-') == 1:
                    # split the range by the dash
                    range_split = element.split('-')
                    # convert the range to integers
                    # If the dash range is given without the first element (-3)
                    # then the range starts from the first page
                    if len(range_split) == 2 and range_split[0]:
                        range_start = int(range_split[0])
                        if range_start < 1:
                            range_start = 1
                    else:
                        # Set to 1 because the model is zero indexed
                        range_start = 1
                    # If the dash range is given without the last element (3-)
                    # then the range ends at the last page
                    if len(range_split) == 2 and range_split[1]:
                        range_end = int(range_split[1])
                        if range_end > len(model):
                            range_end = len(model)
                    else:
                        range_end = len(model)
                    # add the range to the result list
                    result_list += list(range(range_start, range_end+1))
                elif element.isdigit():
                    # add the number to the result list
                    # If it includes multiple dashes elif will not be executed
                    # Check if the element is in the range of all pages
                    if int(element) >=1 and int(element) <= len(model):
                        result_list.append(int(element))
            # Clean selection
            # TO-DO: Maybe an additive selection to the previous selection
            self.iconview.unselect_all()
            for page in result_list:
                # Because the model is zero indexed remove 1 from the page number
                row = model[page-1]
                self.iconview.select_path(row.path)
            self.update_statusbar()

    def center_on_blank_page(self, paths, size):
        """Add paths as overlay, centered on blank pages with 'size'"""
        adder = PageAdder(self)
        file, _ = exporter.get_blank_doc(adder, self.pdfqueue, self.tmp_dir, size)
        if file is None:
            return
        for path in reversed(paths):
            if self.model[path][0].size_in_points() == Dims(*size):
                continue
            ref = Gtk.TreeRowReference.new(self.model, path)
            adder.move(ref, before=False)
            adder.addpages(file)
            adder.commit(select_added=False, add_to_undomanager=False)
            data = deserialize([self.model[path][0].serialize()])
            with self.render_lock():
                self.model.remove(self.model.get_iter(path))
            self.paste_as_layer(data, path, 'OVERLAY', (0.5, 0.5))
            self.model[path][0].description = data[0][2]
            self.model[path][1] = data[0][2]
        for path in paths:
            self.iconview.select_path(path)
        self.iv_selection_changed()

    def crop_dialog(self, _action, _parameter, _unknown):
        """Opens a dialog box to define margins for page cropping."""
        s = self.iconview.get_selected_items()
        a = self.window, s, self.model, self.pdfqueue, self.is_unsaved, 'CROP', self.update_crop
        pageutils.CropHideDialog(*a)

    def update_crop(self, crops, selection, is_unsaved):
        self.undomanager.commit("Crop")
        self.crop(selection, crops)
        self.set_unsaved(is_unsaved)
        self.update_statusbar()
        self.update_iconview_geometry()
        self.update_max_zoom_level()
        GObject.idle_add(self.render)

    def hide_dialog(self, _action, _parameter, _unknown):
        """Opens a dialog box to define margins for page hiding."""
        s = self.iconview.get_selected_items()
        if not self.is_paste_layer_available(s):
            return
        a = self.window, s, self.model, self.pdfqueue, self.is_unsaved, 'HIDE', self.update_hide
        pageutils.CropHideDialog(*a)

    def update_hide(self, hide, selection, is_unsaved):
        """Step 1 in update hide. This make hiding work in iconview.

        Step 2 does the 'real' hiding. This is done with:
        apply_hide_margins_on_pages() (at export).
        apply_hide_margins_on_layerpages() (at at convert_page_data_to_layerpage_lists).
        """
        self.undomanager.commit("Hide")
        for num, row in enumerate(selection):
            page = self.model[row][0]
            page.hide = Sides(*hide[num])
            page.resample = -1
        self.set_unsaved(is_unsaved)
        self.update_statusbar()
        self.update_iconview_geometry()
        self.update_max_zoom_level()
        GObject.idle_add(self.render)

    def apply_hide_margins_on_pages(self, pages):
        """Step 2, does the "real" hiding of margins:

        * Add a full size blank page under the layer stack
        * Crop & offset the stack so that nothing is in the hidden margin area
        """
        pageadder = PageAdder(self)
        for p in pages:
            if all([p.hide[i] <= p.crop[i] for i in range(4)]):
                continue
            self.hide_layer_margins(p, p.layerpages, p.hide)
            filename, nfile = exporter.get_blank_doc(pageadder, self.pdfqueue, self.tmp_dir, p.size)
            if filename is None:
                return
            d = [[p.copyname, p.npage, p.angle, p.scale, 'OVERLAY', p.hide, p.hide]]
            lp = pageadder.get_layerpages(d)
            p.layerpages.insert(0, lp[0])
            p.nfile = nfile
            p.npage = 1
            p.copyname = filename
            p.hide = Sides()
            p.angle = 0

    def apply_hide_margins_on_layerpages(self, layerpages, hide):
        """Step 2, hide margins on a layer stack. (at convert_page_data_to_layerpage_lists())"""
        p = layerpages[0]
        if all([hide[i] <= p.crop[i] for i in range(4)]):
            return
        self.hide_layer_margins(p, layerpages[1:], hide)
        pageadder = PageAdder(self)
        filename, _nfile = exporter.get_blank_doc(pageadder, self.pdfqueue, self.tmp_dir, p.size)
        d = [[filename, 1, 0, p.scale, 'OVERLAY', p.crop, Sides()]]
        lp = pageadder.get_layerpages(d)
        p.crop = Sides(*hide)
        p.offset = Sides(*hide)
        layerpages.insert(0, lp[0])

    @staticmethod
    def hide_layer_margins(p, layerpages, hide):
        """Crop and offset layers that are in the hidden margin."""
        fully_hidden_layers = []
        for num, lp in enumerate(layerpages):
            scalex = (p.size.width * p.scale) / (lp.size.width * lp.scale)
            scaley = (p.size.height * p.scale) / (lp.size.height * lp.scale)
            sm = Sides(scalex, scalex, scaley, scaley)
            outside = Sides(*(max(0, hide[i] - lp.offset[i]) for i in range(4)))
            lp.crop += outside * sm
            lp.offset = Sides(*(max(lp.offset[i], hide[i]) for i in range(4)))
            if lp.crop.left + lp.crop.right >= 1 or lp.crop.top + lp.crop.bottom >= 1:
                fully_hidden_layers.append(num)
        for num in reversed(fully_hidden_layers):
            layerpages.pop(num)

    def crop_white_borders(self, _action, _parameter, _unknown):
        selection = self.iconview.get_selected_items()
        crop = pageutils.white_borders(self.iconview.get_model(), selection, self.pdfqueue)
        self.undomanager.commit("Crop white Borders")
        if self.crop(selection, crop):
            self.set_unsaved(True)
            self.update_statusbar()
        self.update_max_zoom_level()
        GObject.idle_add(self.render)

    def crop(self, selection, newcrop):
        changed = False
        model = self.iconview.get_model()
        for id_sel, path in enumerate(selection):
            pos = model.get_iter(path)
            page = model.get_value(pos, 0)
            if page.crop != Sides(*newcrop[id_sel]):
                page.crop = Sides(*newcrop[id_sel])
                page.find_rectangles = None
                page.resample = -1
                changed = True
            model.set_value(pos, 0, page)
        self.update_iconview_geometry()
        return changed

    def content_loss_warning(self):
        d = Gtk.Dialog(_("Note"),
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(_("_OK"), Gtk.ResponseType.OK),
            resizable=False
            )
        m1 = _("Note the limitations:")
        m2 = _("Cropping/hiding does not remove any content from the PDF file, it only hides it.")
        m3 = _("Outlines and links can be preserved only in certain cases.")
        link = "https://github.com/pdfarranger/pdfarranger/wiki/User-Manual"
        section = "#preserving-of-outlines-and-links"
        markup = (m1 + "\n\n" + m2 + "\n\n" + m3 + " " + _("For more info see") +
                  " " + '<a href="' + link + section + '">' + _("User Manual") + "</a>")
        label = Gtk.Label(label=markup, use_markup=True, max_width_chars=50, wrap=True, margin=12)
        cb = Gtk.CheckButton(_("Do not show this dialog again."), can_focus=False, margin=12)
        d.vbox.pack_start(label, False, False, 6)
        d.vbox.pack_start(cb, False, False, 6)
        d.show_all()
        cb.set_can_focus(True)
        d.run()
        self.config.set_content_loss_warning(not cb.get_active())
        d.destroy()

def is_same_page_size(pages):
    p1w, p1h = pages[0].size_in_points()
    for page in pages[1:]:
        pw, ph = page.size_in_points()
        if abs(p1w-pw) > 1e-2 or abs(p1h-ph) > 1e-2:
            return False
    return True

def sorted_selection_indices(selected_items):
    selected_items.sort(key=lambda x: x.get_indices()[0])
    return [ x.get_indices()[0] for x in selected_items ]

def is_selection_contiguous(selected_page_numbers):
    return len(selected_page_numbers) == selected_page_numbers[-1] - selected_page_numbers[0] + 1
