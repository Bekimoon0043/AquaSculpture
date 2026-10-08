"""Dependency-free minimal XLSX writer (zipfile + sheet XML, inline strings)."""

import zipfile
from xml.sax.saxutils import escape


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def build_xlsx(rows: list[list]) -> bytes:
    """rows: list of rows; cells are str (inline) or int/float."""
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
             "<sheetData>"]
    for r, row in enumerate(rows, start=1):
        lines.append(f'<row r="{r}">')
        for c, cell in enumerate(row, start=1):
            ref = f"{_col_letter(c)}{r}"
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                lines.append(f'<c r="{ref}"><v>{cell}</v></c>')
            else:
                lines.append(f'<c r="{ref}" t="inlineStr"><is><t>'
                             f"{escape(str(cell))}</t></is></c>")
        lines.append("</row>")
    lines.append("</sheetData></worksheet>")
    sheet_xml = "".join(lines)

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>")
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>")
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="BOM" sheetId="1" r:id="rId1"/></sheets></workbook>')
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>")

    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()


def cost_tree_rows(cost: dict) -> list[list]:
    """Flatten the estimator cost tree into spreadsheet rows."""
    rows = [["AquaSculptor — BOM & Cost Breakdown"], [],
            ["Section", "Item", "Qty", "Unit", "Unit price USD", "Amount USD"]]
    for s in cost["sections"]:
        first = True
        for item in s["items"]:
            rows.append([s["label"] if first else "", item["label"], item["qty"],
                         item["unit"], item["unit_price"], item["amount"]])
            first = False
        rows.append(["", f"{s['label']} subtotal", "", "", "", s["amount"]])
    rows += [
        [],
        ["", "SUBTOTAL", "", "", "", cost["subtotal_usd"]],
        ["", f"Contingency {cost['contingency_pct']}%", "", "", "",
         cost["contingency_usd"]],
        ["", f"Margin {cost['margin_pct']}%", "", "", "", cost["margin_usd"]],
        ["", "TOTAL", "", "", "", cost["total_usd"]],
        ["", "Budget", "", "", "", cost.get("budget_usd") or ""],
        ["", "Over budget", "", "", "",
         "YES" if cost.get("over_budget") else "NO"],
        ["", "Annual opex (energy)", "", "", "", cost["opex_annual_usd"]],
    ]
    return rows
