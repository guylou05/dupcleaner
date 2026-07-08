import csv
import json
import os
from datetime import datetime
from utils.file_utils import format_size


def export_csv(groups: list, output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Group ID", "File Path", "File Name", "Size (MB)",
            "Modified Date", "Hash", "Status", "Group Type"
        ])
        for i, group in enumerate(groups, 1):
            for fi in group.files:
                status = "Keep" if fi.is_recommended_keep else "Delete"
                writer.writerow([
                    i,
                    fi.path,
                    fi.name,
                    f"{fi.size_bytes / 1024**2:.2f}",
                    fi.modified_at.strftime("%Y-%m-%d %H:%M:%S") if fi.modified_at else "",
                    group.hash_value[:16],
                    status,
                    group.group_type,
                ])


def export_html_report(groups: list, scan_meta: dict, output_path: str):
    total_wasted = sum(g.wasted_bytes for g in groups)
    now = datetime.now().strftime("%B %d, %Y %H:%M")

    rows_html = ""
    for i, group in enumerate(groups, 1):
        for fi in group.files:
            status_class = "keep" if fi.is_recommended_keep else "delete"
            status_label = "Keep" if fi.is_recommended_keep else "Delete"
            rows_html += f"""
            <tr class="{status_class}">
                <td>{i}</td>
                <td title="{fi.path}">{fi.name}</td>
                <td>{format_size(fi.size_bytes)}</td>
                <td>{fi.modified_at.strftime('%Y-%m-%d') if fi.modified_at else ''}</td>
                <td>{group.group_type}</td>
                <td><span class="badge {status_class}">{status_label}</span></td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DupeClear Pro — Scan Report</title>
<style>
  body {{ font-family: Segoe UI, sans-serif; background:#f6f8fa; color:#24292e; margin:0; padding:20px; }}
  h1 {{ color:#2f81f7; }}
  .summary {{ background:#fff; border:1px solid #e1e4e8; border-radius:8px; padding:16px; margin-bottom:20px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:8px; overflow:hidden; }}
  th {{ background:#2f81f7; color:#fff; padding:10px 12px; text-align:left; }}
  td {{ padding:8px 12px; border-bottom:1px solid #e1e4e8; font-size:13px; }}
  tr.keep {{ background:#f0fff4; }}
  tr.delete {{ background:#fff5f5; }}
  .badge {{ padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold; }}
  .badge.keep {{ background:#3fb950; color:#fff; }}
  .badge.delete {{ background:#f85149; color:#fff; }}
</style>
</head>
<body>
<h1>DupeClear Pro — Duplicate Scan Report</h1>
<div class="summary">
  <strong>Scan Date:</strong> {now}<br>
  <strong>Folders Scanned:</strong> {', '.join(scan_meta.get('folders', []))}<br>
  <strong>Duplicate Groups:</strong> {len(groups)}<br>
  <strong>Potential Space Savings:</strong> {format_size(total_wasted)}
</div>
<table>
<thead><tr>
  <th>#</th><th>File Name</th><th>Size</th><th>Modified</th><th>Type</th><th>Action</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
