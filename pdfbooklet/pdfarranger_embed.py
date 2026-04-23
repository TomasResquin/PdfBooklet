
import sys
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, Gio

# Import local pdfarranger package
sys.path.append(os.path.dirname(__file__))

from pdfbooklet.pdfarranger import pdfarranger
from pdfbooklet.pdfarranger.core import PDFDoc as OriginPDFDoc, PDFDocError, Page, Sides, Dims
from pdfbooklet.pdfarranger.config import Config

# Mock classes for missing UI elements
class DummyWidget:
    def hide(self): pass
    def show(self): pass
    def set_sensitive(self, s): pass
    def set_active(self, s): pass

class BuilderWrapper:
    def __init__(self, builder, app=None):
        self.builder = builder
        self.app = app
    
    def get_object(self, name):
        if name == 'vbox1':
            name = 'main_box'
        if name == 'main_window' and self.app:
            return self.app.window
        obj = self.builder.get_object(name)
        if obj:
            return obj
        return DummyWidget()
    
    def connect_signals(self, handler):
        self.builder.connect_signals(handler)

class EmbeddedPdfArranger(pdfarranger.PdfArranger):
    def __init__(self):
        super().__init__()
        # Initialize window and UI
        try:
            self.register(None)
        except Exception as e:
            print(f"Warning: could not register application: {e}")
        self.do_activate()
        # Wrap builder
        self.uiXML = BuilderWrapper(self.uiXML, self)
        
        # Set default icon view column width
        self.iv_col_width = 150 # Default estimation
        
        # Hide redundant UI elements
        try:
            # Blacklist of actions to hide
            BLACKLIST_ACTIONS = ['win.open', 'win.import', 'win.save', 'win.save-as', 'win.new', 'win.quit']
            
            # 1. Hide Toolbar Buttons
            # print("DEBUG: Attempting to hide buttons...")
            header = None
            
            if hasattr(self, 'uiXML'):
                 header = self.uiXML.get_object("header_bar")

            if (header is None or isinstance(header, DummyWidget)) and self.window:
                 header = self.window.get_titlebar()
            
            if header and not isinstance(header, DummyWidget):
                def recursive_hide_widget(widget):
                    if isinstance(widget, Gtk.Container):
                        for child in widget.get_children():
                            recursive_hide_widget(child)
                    if isinstance(widget, Gtk.Button):
                        action = widget.get_action_name()
                        if action in BLACKLIST_ACTIONS:
                            widget.set_visible(False)
                            widget.set_no_show_all(True)
                
                recursive_hide_widget(header)
            
            # 2. Hide Main Menu Items (Gio.Menu)
            if hasattr(self, 'uiXML'):
                main_menu_btn = self.uiXML.get_object("main_menu_button")
                if main_menu_btn and not isinstance(main_menu_btn, DummyWidget):
                    model = main_menu_btn.get_menu_model()
                    
                    def recursive_clean_gio_menu(menu_model):
                        if not isinstance(menu_model, Gio.Menu):
                            return
                        # Iterate backwards to safely remove items
                        n = menu_model.get_n_items()
                        for i in range(n - 1, -1, -1):
                            action = menu_model.get_item_attribute_value(i, "action", None)
                            if action:
                                action_str = action.get_string()
                                if action_str in BLACKLIST_ACTIONS:
                                    menu_model.remove(i)
                                    continue
                            
                            # Check submenus/sections
                            link = menu_model.get_item_link(i, "section")
                            if link: recursive_clean_gio_menu(link)
                            
                            link = menu_model.get_item_link(i, "submenu")
                            if link: recursive_clean_gio_menu(link)

                    recursive_clean_gio_menu(model)

            # 3. Hide Context Menu Items (Gtk.Menu)
            if hasattr(self, 'popup') and isinstance(self.popup, Gtk.Menu):
                 def recursive_clean_gtk_menu(menu):
                    for child in menu.get_children():
                        if isinstance(child, Gtk.MenuItem):
                            if isinstance(child, Gtk.Actionable):
                                action = child.get_action_name()
                                if action in BLACKLIST_ACTIONS:
                                    child.set_visible(False)
                                    child.set_no_show_all(True)
                            
                            # Recurse for submenus
                            submenu = child.get_submenu()
                            if submenu and isinstance(submenu, Gtk.Menu):
                                recursive_clean_gtk_menu(submenu)
                 
                 recursive_clean_gtk_menu(self.popup)

        except Exception as e:
            print(f"Warning: could not hide buttons or menu items: {e}")
            import traceback
            traceback.print_exc()

        if self.window:
            self.window.connect("delete-event", self.on_window_delete)
        
        # Handle rendering thread access
        # Mock rendering thread if missing
        pass

    def on_window_delete(self, widget, event):
        """Handle window close request (X button) locally by hiding."""
        if self.window:
            self.window.hide()
        return True

    def on_quit(self, _action, _param=None, _unknown=None):
        """Override PdfArranger's on_quit to simply hide the window."""
        if self.window:
            self.window.hide()
        return Gdk.EVENT_STOP

    def iv_button_press_event(self, iconview, event):
        """Manages mouse clicks on the iconview - Override to fix DnD"""
        GObject.timeout_add(0, self.iv_selection_changed)
        iconview.grab_focus()
        # Toggle zoom on double-click
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS and self.click_path:

            self.pressed_button = None
            self.on_action_zoom_fit()
            return Gdk.EVENT_STOP

        # Set move cursor on middle click
        if event.button == 2:

            self.iv_pan_view.click(event)

        click_path_old = self.click_path
        self.click_path = iconview.get_path_at_pos(event.x, event.y)

        # On shift-click, select all items from cursor up to the shift-clicked item.
        # On shift-ctrl-click, toggle selection for single items.
        if event.button == 1 and self.click_path and event.state & Gdk.ModifierType.SHIFT_MASK:
            cursor_path = iconview.get_cursor()[1]
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                if iconview.path_is_selected(self.click_path):
                    iconview.unselect_path(self.click_path)
                else:
                    iconview.select_path(self.click_path)
            elif cursor_path:
                i_cursor = cursor_path[0]
                i_click = self.click_path[0]
                i_click_old = click_path_old[0] if click_path_old else i_click
                range_start = min(i_cursor, i_click, i_click_old)
                range_end = max(i_cursor, i_click, i_click_old)
                for i in range(range_start, range_end + 1):
                    path = Gtk.TreePath.new_from_indices([i])
                    if min(i_cursor, i_click) <= i <= max(i_cursor, i_click):
                        iconview.select_path(path)
                    else:
                        iconview.unselect_path(path)
            return Gdk.EVENT_STOP

        # Forget where cursor was when shift was pressed
        if event.button == 1 and not event.state & Gdk.ModifierType.SHIFT_MASK:
            self.iv_cursor.sel_start_page = None

        # Do not deselect when clicking an already selected item for drag and drop
        # MODIFIED: Allow propagation (return False) to let GtkIconView start DnD
        if event.button == 1:
            selection = iconview.get_selected_items()
            if self.click_path and self.click_path in selection:
                self.pressed_button = event
                if iconview.get_cursor()[1] != self.click_path:
                    self.iconview.set_cursor(self.click_path, None, False)
                # return Gdk.EVENT_STOP  <-- This was blocking DnD
                return False 

        # Display right click menu
        if event.button == 3 and not self.iv_auto_scroll_timer:
            self.iv_drag_select.end()
            self.iv_pan_view.end()
            if self.click_path:
                selection = iconview.get_selected_items()
                if self.click_path not in selection:
                    iconview.unselect_all()
                    iconview.select_path(self.click_path)
            else:
                iconview.unselect_all()
            self.popup.popup(None, None, None, None, event.button, event.time)
            return Gdk.EVENT_STOP

        # Go into drag-select mode if clicked between items
        if not self.click_path:
            if event.button == 1:
                self.iv_drag_select.click(event)
            return Gdk.EVENT_STOP

        return False

    def iv_dnd_motion(self, iconview, context, x, y, etime):
        """Handles drag motion: autoscroll, select move or copy, select drag cursor location."""
        # Removed modal check which was causing issues since the window itself is modal
        
        x, y = iconview.convert_widget_to_bin_window_coords(x, y)

        # Auto-scroll when drag up/down
        self.iv_autoscroll(x, y, autoscroll_area=40)

        # Select move or copy dragAction
        drag_move_posix = os.name == 'posix' and context.get_actions() & Gdk.DragAction.MOVE
        if drag_move_posix:
            Gdk.drag_status(context, Gdk.DragAction.MOVE, etime)
        else:
            Gdk.drag_status(context, Gdk.DragAction.COPY, etime)

        # We override default behaviour and only allow drag & drop to left or right.
        model = iconview.get_model()
        if len(model) == 0:
            return Gdk.EVENT_STOP
        cell_width, _cell_height = self.cellthmb.get_fixed_size()
        row_distance = iconview.get_row_spacing() + 2 * iconview.get_item_padding()
        column_distance = iconview.get_column_spacing() + 2 * iconview.get_item_padding()
        search_positions = [('XY', x, y),
                            ('Right', x + column_distance / 2, y),
                            ('Left', x - column_distance / 2, y),
                            ('Below', x, y + row_distance / 2),
                            ('Above', x, y - row_distance / 2),
                            ('Left-Above', x - column_distance, y - row_distance),
                            ('Right-Far', x + cell_width, y),
                            ('Left-Far', x - cell_width, y),
                            ('Right-Below-Far', x + cell_width, y + row_distance),
                            ('Left-Below-Far', x - cell_width, y + row_distance),
                            ('Below-Far', x, y + row_distance)]
        search_pos = None
        path = None
        for search_pos_curr, x_s, y_s in search_positions:
            path = iconview.get_path_at_pos(x_s, y_s)
            if path:
                search_pos = search_pos_curr
                break
        
        if search_pos in ['XY', 'Right', 'Left', 'Below', 'Above']:
            self.drag_path = path
            if path == iconview.get_path_at_pos(x + cell_width * 0.6, y): # approximate logic check from original
                pass
            
            # Check drop position
            if path == iconview.get_path_at_pos(x_s + cell_width * 0.6, y_s):
                self.drag_pos = Gtk.IconViewDropPosition.DROP_LEFT
            elif path == iconview.get_path_at_pos(x_s - cell_width * 0.6, y_s):
                self.drag_pos = Gtk.IconViewDropPosition.DROP_RIGHT
            else:
                 p_rect = iconview.get_cell_rect(path)[1] # Gdk.Rectangle
                 # Relative x in cell
                 rel_x = x - p_rect.x
                 if rel_x < p_rect.width / 2:
                     self.drag_pos = Gtk.IconViewDropPosition.DROP_LEFT
                 else:
                     self.drag_pos = Gtk.IconViewDropPosition.DROP_RIGHT

        elif search_pos == 'Left-Above' and iconview.get_drag_dest_item()[0]:
            return Gdk.EVENT_STOP
        elif not path or (path == model[-1].path and x_s < x):
            self.drag_path = model[-1].path
            if self.iconview.get_direction() == Gtk.TextDirection.LTR:
                self.drag_pos = Gtk.IconViewDropPosition.DROP_RIGHT
            else:
                self.drag_pos = Gtk.IconViewDropPosition.DROP_LEFT
        else:
            iconview.stop_emission('drag_motion')
            return Gdk.EVENT_PROPAGATE
            
        iconview.set_drag_dest_item(self.drag_path, self.drag_pos)
        return Gdk.EVENT_STOP

    def iv_drag_begin(self, iconview, context):
        # Call static method from parent class
        pdfarranger.PdfArranger.iv_drag_begin(iconview, context)

    def iv_dnd_get_data(self, iconview, context, selection_data, target_id, etime):
        super().iv_dnd_get_data(iconview, context, selection_data, target_id, etime)

    def iv_dnd_received_data(self, iconview, context, x, y, selection_data, info, etime):
        super().iv_dnd_received_data(iconview, context, x, y, selection_data, info, etime)

    def add_pdf_pages(self, filename, firstpage=None, lastpage=None, angle=0, crop=[0.,0.,0.,0.]):
        # Wrapper for PageAdder
        from pdfbooklet.pdfarranger import core
        adder = core.PageAdder(self)
        # Wrapper for PageAdder
        # Unlike the old add_pdf_pages, PageAdder adds either a single page or all pages (p=-1).
        # Iterate to support adding a specific page range.

        if firstpage is None: firstpage = 1

        
        doc_data = adder.get_pdfdoc(filename)
        if not doc_data: return False
        pdfdoc, nfile, _ = doc_data
        
        total_pages = pdfdoc.document.get_n_pages()
        end = lastpage if lastpage else total_pages
        
        # Loop pages
        ret = False
        crops = core.Sides(crop[0], crop[1], crop[2], crop[3])
        for p in range(firstpage, end + 1):
             res = adder.addpages(filename, page=p, angle=angle, crop=crops)
             if res: ret = True
             
        if ret:
            adder.commit(select_added=True, add_to_undomanager=False)
            
        return ret

    def update_geometry(self, iter):
        # PdfArranger Pages handle geometry automatically, but we might need to refresh view
        pass

    def reset_iv_width(self):
        self.update_iconview_geometry()

    def render(self):
        super().render()
    
    def get_blank_pdf(self, width, height):
        from pdfbooklet.pdfarranger.exporter import _create_blank_page
        from pdfbooklet.pdfarranger.core import Dims, PDFDoc
        
        size = Dims(width, height)
        # Check if we already have a matching blank doc
        for i, doc in enumerate(self.pdfqueue):
            if doc.blank_size == size:
                 return doc, i + 1
                 
        # Create new blank doc
        filename = _create_blank_page(self.tmp_dir, size, 1)
        pdfdoc = PDFDoc(filename, None, size, (0,0,0), self.tmp_dir, self.window)
        self.pdfqueue.append(pdfdoc)
        return pdfdoc, len(self.pdfqueue)

    # PdfBooklet might access pool
    pool = None

    # Legacy add_pdf_pages implementation
    # Note that PdfArranger model updates happen via PageAdder.commit().
    # Direct appends to self.pdfqueue will bypass model updates.


class PDF_Doc(OriginPDFDoc):
    def __init__(self, filename, nfile, tmp_dir):
        # Initialize PDFDoc with core parameters
        try:
             stat_info = os.stat(filename)
             stat = (stat_info.st_dev, stat_info.st_ino, stat_info.st_mtime)
             super().__init__(filename, None, None, stat, tmp_dir, None)
             self.nfile = nfile + 1
             self.shortname = os.path.basename(filename)
        except Exception as e:
            print(f"Error creating PDF_Doc wrapper: {e}")
            self.nfile = 0

