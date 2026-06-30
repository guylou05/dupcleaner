import io
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_MD, FONT_HEADING_SM, FONT_BODY, FONT_BODY_BOLD, FONT_CAPTION
from utils.constants import CORNER_RADIUS, CARD_ROW_HEIGHT
from utils.file_utils import format_size, open_in_explorer
from ui.components.toast import show_toast
from ui.components.space_meter import SpaceMeter
from ui.components.file_card import FileCard
from core.safe_delete import safe_delete, get_bin_size
from core.exporter import export_csv, export_html_report

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False


class ResultsView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._groups = []
        self._filtered = []
        self._scan_history_id = None
        self._capped_count = 0
        self._build()

    def _build(self):
        # Top summary bar
        top = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=0)
        top.pack(fill="x")

        self._summary_label = ctk.CTkLabel(
            top, text="No scan results yet.",
            font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
        )
        self._summary_label.pack(side="left", padx=20, pady=16)

        self._space_meter = SpaceMeter(top, width=220)
        self._space_meter.pack(side="right", padx=16, pady=8)

        # Action bar
        action_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_tertiary"], corner_radius=0, height=50)
        action_bar.pack(fill="x")
        action_bar.pack_propagate(False)

        ctk.CTkButton(
            action_bar, text="Select All Dupes", font=FONT_CAPTION,
            height=30, fg_color=COLORS["accent_muted"],
            hover_color=COLORS["accent"], command=self._select_all
        ).pack(side="left", padx=8, pady=10)

        ctk.CTkButton(
            action_bar, text="Auto-Select Smart", font=FONT_CAPTION,
            height=30, fg_color=COLORS["accent_muted"],
            hover_color=COLORS["accent"], command=self._auto_select
        ).pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            action_bar, text="Deselect All", font=FONT_CAPTION,
            height=30, fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_secondary"],
            command=self._deselect_all
        ).pack(side="left", padx=4, pady=10)

        ctk.CTkButton(
            action_bar, text="\U0001f5d1  Delete Selected", font=FONT_CAPTION,
            height=30, fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"], command=self._confirm_delete
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkButton(
            action_bar, text="\U0001f4e4  Export", font=FONT_CAPTION,
            height=30, fg_color=COLORS["accent_muted"],
            hover_color=COLORS["accent"], command=self._export
        ).pack(side="left", padx=4, pady=10)

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"], height=44)
        filter_bar.pack(fill="x", padx=16, pady=8)
        filter_bar.pack_propagate(False)

        ctk.CTkLabel(filter_bar, text="Sort:", font=FONT_CAPTION,
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self._sort_var = ctk.StringVar(value="Largest First")
        ctk.CTkOptionMenu(
            filter_bar,
            values=["Largest First", "Smallest First", "Most Copies", "Newest"],
            variable=self._sort_var,
            fg_color=COLORS["bg_tertiary"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_secondary"],
            width=160, command=lambda _: self._apply_sort()
        ).pack(side="left", padx=8)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            filter_bar, textvariable=self._search_var,
            placeholder_text="\U0001f50d  filter by path...",
            fg_color=COLORS["bg_tertiary"],
            border_color=COLORS["border"],
            width=280
        ).pack(side="left", padx=8)

        # Scrollable results area
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent"
        )
        self._scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Run a scan to see duplicate files here.",
            font=FONT_BODY, text_color=COLORS["text_muted"]
        )
        self._empty_label.pack(pady=60)

    def load_results(self, groups: list, scan_history_id: int = None, capped_count: int = 0):
        self._groups = groups
        self._scan_history_id = scan_history_id
        self._capped_count = capped_count  # total groups before free-tier cap (0 = uncapped)
        self._apply_sort()

    def _apply_sort(self):
        sort = self._sort_var.get()
        if sort == "Largest First":
            self._groups.sort(key=lambda g: g.wasted_bytes, reverse=True)
        elif sort == "Smallest First":
            self._groups.sort(key=lambda g: g.wasted_bytes)
        elif sort == "Most Copies":
            self._groups.sort(key=lambda g: len(g.files), reverse=True)
        elif sort == "Newest":
            self._groups.sort(
                key=lambda g: max((f.modified_at for f in g.files), default=None) or 0,
                reverse=True
            )
        self._apply_filter()

    def _apply_filter(self):
        term = self._search_var.get().lower()
        if term:
            self._filtered = [
                g for g in self._groups
                if any(term in f.path.lower() for f in g.files)
            ]
        else:
            self._filtered = list(self._groups)
        self._render()

    def _render(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not self._filtered:
            ctk.CTkLabel(
                self._scroll,
                text="No results." if self._groups else "Run a scan to see duplicate files here.",
                font=FONT_BODY, text_color=COLORS["text_muted"]
            ).pack(pady=60)

            total_wasted = sum(g.wasted_bytes for g in self._groups)
            self._summary_label.configure(
                text=f"{len(self._groups)} duplicate groups  •  "
                     f"Space you can free: {format_size(total_wasted)}"
            )
            self._space_meter.set_value(total_wasted)
            return

        total_wasted = sum(g.wasted_bytes for g in self._groups)
        self._summary_label.configure(
            text=f"{len(self._groups)} duplicate groups  •  "
                 f"Space you can free: {format_size(total_wasted)}"
        )
        self._space_meter.set_value(total_wasted)

        for idx, group in enumerate(self._filtered):
            self._render_group_card(idx, group)

        # Free-tier cap banner
        if self._capped_count > 0:
            banner = ctk.CTkFrame(
                self._scroll,
                fg_color=COLORS["accent_muted"],
                corner_radius=8,
                border_color=COLORS["accent"],
                border_width=1,
            )
            banner.pack(fill="x", pady=(8, 4))
            ctk.CTkLabel(
                banner,
                text=f"⭐  Showing {len(self._filtered)} of {self._capped_count} duplicate groups."
                     f"  Upgrade to Pro to see all results, export reports, and remove limits.",
                font=FONT_CAPTION,
                text_color=COLORS["text_primary"],
                wraplength=600,
                justify="left",
            ).pack(side="left", padx=16, pady=10)
            ctk.CTkButton(
                banner, text="Upgrade — $24.99 lifetime",
                font=FONT_CAPTION,
                height=28,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                command=lambda: __import__("webbrowser").open("https://dupeclearpro.com/upgrade"),
            ).pack(side="right", padx=12, pady=10)

    def _render_group_card(self, idx: int, group):
        total_wasted = format_size(group.wasted_bytes)
        copies = len(group.files)
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=COLORS["bg_secondary"],
            corner_radius=CORNER_RADIUS,
            border_color=COLORS["border"],
            border_width=1
        )
        card.pack(fill="x", pady=6)

        header = ctk.CTkFrame(card, fg_color=COLORS["bg_tertiary"], corner_radius=0, height=36)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=f"Group {idx+1}  •  {copies} copies  •  Wasting {total_wasted}",
            font=FONT_CAPTION, text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=12, pady=8)

        similarity = group.similarity_score
        if group.group_type == "similar_image" and similarity < 1.0:
            ctk.CTkLabel(
                header,
                text=f"≈ {int(similarity*100)}% similar",
                font=FONT_CAPTION, text_color=COLORS["warning"]
            ).pack(side="left", padx=4)

        for fi in group.files:
            fc = FileCard(
                card, fi,
                on_check_change=lambda: None,
                on_preview=lambda f, g=group: self._open_preview(f, g)
            )
            fc.pack(fill="x", padx=4, pady=2)

    def _open_preview(self, file_info, group):
        if not _PIL:
            return
        modal = ctk.CTkToplevel(self)
        modal.title("File Preview")
        modal.geometry("900x600")
        modal.configure(fg_color=COLORS["bg_primary"])
        modal.grab_set()

        ctk.CTkLabel(
            modal, text=f"Duplicate Group — {len(group.files)} copies",
            font=FONT_HEADING_SM, text_color=COLORS["text_primary"]
        ).pack(pady=12)

        imgs_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent", orientation="horizontal")
        imgs_frame.pack(fill="both", expand=True, padx=16)

        for fi in group.files:
            col = ctk.CTkFrame(imgs_frame, fg_color=COLORS["bg_secondary"], corner_radius=8)
            col.pack(side="left", padx=8, pady=8, fill="y")

            if fi.thumbnail and _PIL:
                try:
                    img = Image.open(io.BytesIO(fi.thumbnail))
                    img.thumbnail((320, 320))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    ctk.CTkLabel(col, image=ctk_img, text="").pack(padx=12, pady=12)
                except Exception:
                    ctk.CTkLabel(col, text="[No Preview]", font=FONT_BODY).pack(padx=24, pady=40)
            else:
                ctk.CTkLabel(col, text="[No Preview]", font=FONT_BODY).pack(padx=24, pady=40)

            ctk.CTkLabel(
                col, text=fi.name, font=FONT_BODY_BOLD,
                text_color=COLORS["text_primary"]
            ).pack(padx=12)
            ctk.CTkLabel(
                col, text=fi.path, font=("Consolas", 9),
                text_color=COLORS["text_muted"], wraplength=300
            ).pack(padx=12, pady=(0, 8))

            if fi.is_recommended_keep:
                ctk.CTkLabel(
                    col, text="\U0001f6e1 Recommended Keep",
                    font=FONT_CAPTION, text_color=COLORS["success"]
                ).pack(pady=(0, 8))

        ctk.CTkButton(
            modal, text="Close", command=modal.destroy,
            fg_color=COLORS["bg_tertiary"]
        ).pack(pady=12)

    def _get_marked_files(self) -> list:
        return [fi for g in self._filtered for fi in g.files if fi.marked_for_delete]

    def _select_all(self):
        for group in self._filtered:
            for fi in group.files:
                if not fi.is_recommended_keep:
                    fi.marked_for_delete = True
        self._render()

    def _deselect_all(self):
        for group in self._filtered:
            for fi in group.files:
                fi.marked_for_delete = False
        self._render()

    def _auto_select(self):
        from db.database import get_setting
        from core.scanner import _auto_select
        rule = get_setting("auto_select_rule", "newest")
        _auto_select(self._filtered, rule)
        self._render()
        show_toast(self, "Smart auto-select applied.", "success")

    def _confirm_delete(self):
        marked = self._get_marked_files()
        if not marked:
            show_toast(self, "No files selected for deletion.", "warning")
            return
        total = sum(f.size_bytes for f in marked)
        self._show_delete_modal(marked, total)

    def _show_delete_modal(self, files: list, total_bytes: int):
        modal = ctk.CTkToplevel(self)
        modal.title("Confirm Deletion")
        modal.geometry("480x320")
        modal.configure(fg_color=COLORS["bg_primary"])
        modal.grab_set()
        modal.resizable(False, False)

        ctk.CTkLabel(
            modal, text=f"Delete {len(files)} files?",
            font=FONT_HEADING_MD, text_color=COLORS["text_primary"]
        ).pack(pady=(24, 8))
        ctk.CTkLabel(
            modal, text=f"This will free {format_size(total_bytes)} of space.",
            font=FONT_BODY, text_color=COLORS["text_secondary"]
        ).pack()
        ctk.CTkLabel(
            modal,
            text="Files will be moved to DupeClear Pro's Recovery Bin.\nYou can restore them anytime from the Recovery Bin view.",
            font=FONT_CAPTION, text_color=COLORS["text_muted"],
            justify="center"
        ).pack(pady=8)

        perm_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            modal, text="I understand permanently deleted files cannot be recovered",
            variable=perm_var, font=FONT_CAPTION,
            text_color=COLORS["text_secondary"], fg_color=COLORS["danger"]
        ).pack(pady=12)

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(pady=8)

        ctk.CTkButton(
            btn_row, text="Cancel", width=100,
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_secondary"],
            command=modal.destroy
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="Move to Recovery Bin", width=180,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=lambda: self._do_delete(files, permanent=False,
                                            modal=modal)
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="Delete Permanently", width=160,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            command=lambda: self._do_perm_delete(files, perm_var, modal)
        ).pack(side="left", padx=6)

    def _do_delete(self, files, permanent, modal):
        modal.destroy()
        success = 0
        fail = 0
        for fi in files:
            if permanent:
                import os
                try:
                    os.remove(fi.path)
                    success += 1
                except Exception:
                    fail += 1
            else:
                if safe_delete(fi.path, self._scan_history_id):
                    success += 1
                else:
                    fail += 1

        from db.database import update_scan_history
        if self._scan_history_id:
            freed = sum(f.size_bytes for f in files if not f.marked_for_delete or True)
            update_scan_history(self._scan_history_id, freed_bytes=freed)

        # Remove deleted files from groups
        deleted_paths = {f.path for f in files}
        for group in self._filtered:
            group.files = [f for f in group.files if f.path not in deleted_paths]
        self._filtered = [g for g in self._filtered if len(g.files) >= 2]
        self._groups   = [g for g in self._groups   if len(g.files) >= 2]

        msg = f"Deleted {success} files."
        if fail:
            msg += f" {fail} failed."
        show_toast(self, msg, "success" if not fail else "warning")
        self._render()

    def _do_perm_delete(self, files, perm_var, modal):
        if not perm_var.get():
            show_toast(modal, "Check the confirmation box first.", "warning")
            return
        self._do_delete(files, permanent=True, modal=modal)

    def _export(self):
        from core.license import is_pro
        if not is_pro():
            show_toast(self, "Export requires Pro. Upgrade at dupeclearpro.com.", "warning")
            return
        if not self._groups:
            show_toast(self, "Nothing to export.", "warning")
            return
        fmt = ctk.CTkInputDialog(
            text="Export format:",
            title="Export Results"
        )
        # Use file dialog directly
        path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".csv",
            filetypes=[
                ("CSV", "*.csv"),
                ("HTML Report", "*.html"),
            ]
        )
        if not path:
            return
        try:
            if path.endswith(".html"):
                from db.database import get_setting
                import json
                folders = []
                export_html_report(self._groups, {"folders": folders}, path)
            else:
                export_csv(self._groups, path)
            show_toast(self, f"Exported to {path}", "success")
        except Exception as e:
            show_toast(self, f"Export failed: {e}", "error")
