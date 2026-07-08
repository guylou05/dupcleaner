import json
import customtkinter as ctk
from utils.theme import COLORS, FONT_HEADING_LG, FONT_HEADING_SM, FONT_BODY, FONT_CAPTION
from utils.constants import CORNER_RADIUS
from utils.file_utils import format_size
from db.database import get_all_history, get_lifetime_stats


class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._app = app
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(scroll, text="Scan History",
                     font=FONT_HEADING_LG, text_color=COLORS["text_primary"]
                     ).pack(anchor="w", pady=(0, 12))

        # Lifetime stats
        stats_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"],
                                    corner_radius=CORNER_RADIUS)
        stats_frame.pack(fill="x", pady=(0, 16))
        self._stats_label = ctk.CTkLabel(
            stats_frame, text="Loading...",
            font=FONT_BODY, text_color=COLORS["text_secondary"]
        )
        self._stats_label.pack(padx=16, pady=12)

        # Table header
        header = ctk.CTkFrame(scroll, fg_color=COLORS["bg_tertiary"], corner_radius=6)
        header.pack(fill="x", pady=(0, 4))
        for col, w in [("Date", 160), ("Folders", 80), ("Files", 80),
                       ("Groups", 80), ("Space Freed", 120), ("Action", 100)]:
            ctk.CTkLabel(header, text=col, font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_secondary"], width=w, anchor="w"
                         ).pack(side="left", padx=8, pady=8)

        self._list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._list_frame.pack(fill="x")

        self.refresh()

    def refresh(self):
        stats = get_lifetime_stats()
        self._stats_label.configure(
            text=f"All time: {stats['scans']} scans  •  "
                 f"{stats['total_files']:,} files analyzed  •  "
                 f"{format_size(stats['total_freed'])} freed"
        )

        for w in self._list_frame.winfo_children():
            w.destroy()

        rows = get_all_history()
        if not rows:
            ctk.CTkLabel(
                self._list_frame,
                text="No scan history yet. Run your first scan!",
                font=FONT_BODY, text_color=COLORS["text_muted"]
            ).pack(pady=40)
            return

        for row in rows:
            self._render_row(row)

    def _render_row(self, row):
        r = ctk.CTkFrame(self._list_frame, fg_color=COLORS["bg_secondary"],
                          corner_radius=6)
        r.pack(fill="x", pady=2)

        import datetime
        started = row["started_at"] or ""
        try:
            dt = datetime.datetime.fromisoformat(started)
            date_str = dt.strftime("%b %d, %Y")
        except Exception:
            date_str = started[:10]

        try:
            folders = json.loads(row["folders"] or "[]")
            folder_count = len(folders)
        except Exception:
            folder_count = 0

        data = [
            (date_str,                         160),
            (f"{folder_count} folder(s)",       80),
            (f"{row['files_scanned']:,}",        80),
            (f"{row['duplicate_groups']}",       80),
            (format_size(row["freed_bytes"] or 0), 120),
        ]
        for text, w in data:
            ctk.CTkLabel(r, text=text, font=FONT_CAPTION,
                         text_color=COLORS["text_primary"], width=w, anchor="w"
                         ).pack(side="left", padx=8, pady=8)

        if row["results_json"]:
            ctk.CTkButton(
                r, text="View Results", width=100, height=28,
                font=FONT_CAPTION,
                fg_color=COLORS["accent_muted"],
                hover_color=COLORS["accent"],
                command=lambda rid=row["id"], rj=row["results_json"]: self._reload_results(rid, rj)
            ).pack(side="left", padx=8)

    def _reload_results(self, scan_id: int, results_json: str):
        try:
            import json as _json
            raw = _json.loads(results_json)
            from db.models import DuplicateGroup, FileInfo
            import datetime
            groups = []
            for g in raw:
                files = []
                for f in g.get("files", []):
                    fi = FileInfo(
                        path=f["path"], name=f["name"],
                        size_bytes=f["size_bytes"],
                        modified_at=datetime.datetime.fromisoformat(f["modified_at"]) if f.get("modified_at") else None,
                        extension=f["extension"],
                        marked_for_delete=f.get("marked_for_delete", False),
                        is_recommended_keep=f.get("is_recommended_keep", False),
                    )
                    files.append(fi)
                grp = DuplicateGroup(
                    hash_value=g["hash_value"],
                    files=files,
                    total_size_bytes=g["total_size_bytes"],
                    wasted_bytes=g["wasted_bytes"],
                    group_type=g["group_type"],
                    similarity_score=g.get("similarity_score", 1.0),
                )
                groups.append(grp)
            self._app.show_results(groups, scan_id)
        except Exception as e:
            from ui.components.toast import show_toast
            show_toast(self, f"Could not load results: {e}", "error")
