"""Generate realistic sample invoice PDFs for the UiPath bot to consume.

This is a developer tool, not part of the production pipeline. Run it once to
seed Data/Samples/ with PDFs you can drop into Data/Inbox/ during testing.

Usage:
    python tools/generate_sample_invoices.py            # writes to Data/Samples/
    python tools/generate_sample_invoices.py --count 10
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


VENDORS = [
    ("Acme Office Supplies", "1209 Riverwalk St, Austin, TX 78701", "USD"),
    ("Northwind Logistics", "47 Harbor Rd, Seattle, WA 98101", "USD"),
    ("Bluebird Software Pvt Ltd", "Tower A, Embassy Tech Village, Bengaluru 560103", "INR"),
    ("Alpine Catering GmbH", "Marktplatz 12, 80331 München", "EUR"),
    ("Lighthouse Marketing", "88 King St W, Toronto, ON M5H 1A1", "CAD"),
    ("Sakura Components KK", "2-7-1 Marunouchi, Chiyoda, Tokyo 100-0005", "JPY"),
]

CUSTOMERS = [
    ("Globex Corporation", "500 Grand Ave, San Francisco, CA 94110"),
    ("Initech LLC", "1234 Cubicle Way, Austin, TX 78704"),
    ("Hooli Inc.", "1 Hooli Way, Palo Alto, CA 94301"),
]

ITEM_CATALOG = [
    ("A4 paper, 80gsm, ream", 4.50),
    ("Ballpoint pens, box of 12", 3.20),
    ("Cloud storage subscription, monthly", 49.00),
    ("Logo redesign — flat fee", 1200.00),
    ("Desk chair, ergonomic", 289.00),
    ("USB-C dock, 8-port", 79.99),
    ("Server rack rental, 1U month", 95.00),
    ("Catering — boxed lunches", 18.50),
    ("Whiteboard markers, set of 8", 12.40),
    ("Software license, annual", 599.00),
    ("Consulting hours, senior engineer", 175.00),
    ("Shipping & handling", 24.95),
]


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


def random_invoice(seed: int) -> dict:
    rng = random.Random(seed)
    vendor_name, vendor_addr, currency = rng.choice(VENDORS)
    customer_name, customer_addr = rng.choice(CUSTOMERS)
    invoice_date = date(2026, 1, 1) + timedelta(days=rng.randint(0, 120))
    due_date = invoice_date + timedelta(days=rng.choice([15, 30, 45]))

    items = []
    for desc, base_price in rng.sample(ITEM_CATALOG, k=rng.randint(2, 5)):
        qty = rng.choice([1, 1, 2, 3, 5, 10])
        # mild price jitter so the same item differs across invoices
        unit = round(base_price * rng.uniform(0.95, 1.08), 2)
        items.append(LineItem(desc, qty, unit))

    subtotal = round(sum(i.total for i in items), 2)
    tax_rate = rng.choice([0.0, 0.05, 0.0825, 0.10, 0.18, 0.20])
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    return {
        "invoice_number": f"INV-{2026}-{seed:05d}",
        "invoice_date": invoice_date,
        "due_date": due_date,
        "vendor_name": vendor_name,
        "vendor_address": vendor_addr,
        "customer_name": customer_name,
        "customer_address": customer_addr,
        "currency": currency,
        "items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
    }


def build_pdf(invoice: dict, out_path: Path) -> None:
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=invoice["invoice_number"],
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=22, spaceAfter=4)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=11)
    label = ParagraphStyle("label", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []
    story.append(Paragraph("INVOICE", h1))
    story.append(Paragraph(f"<b>{invoice['vendor_name']}</b>", styles["Normal"]))
    story.append(Paragraph(invoice["vendor_address"], small))
    story.append(Spacer(1, 0.25 * inch))

    meta = [
        [Paragraph("BILL TO", label), Paragraph("INVOICE #", label), Paragraph("ISSUE DATE", label), Paragraph("DUE DATE", label)],
        [
            Paragraph(f"<b>{invoice['customer_name']}</b><br/>{invoice['customer_address']}", small),
            Paragraph(invoice["invoice_number"], styles["Normal"]),
            Paragraph(invoice["invoice_date"].isoformat(), styles["Normal"]),
            Paragraph(invoice["due_date"].isoformat(), styles["Normal"]),
        ],
    ]
    meta_tbl = Table(meta, colWidths=[2.6 * inch, 1.4 * inch, 1.3 * inch, 1.3 * inch])
    meta_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ]
        )
    )
    story.append(meta_tbl)
    story.append(Spacer(1, 0.3 * inch))

    rows = [["Description", "Qty", "Unit Price", "Amount"]]
    for it in invoice["items"]:
        rows.append(
            [
                it.description,
                f"{it.quantity:g}",
                f"{it.unit_price:,.2f}",
                f"{it.total:,.2f}",
            ]
        )
    rows.append(["", "", "Subtotal", f"{invoice['subtotal']:,.2f}"])
    rows.append(["", "", f"Tax ({invoice['tax_rate'] * 100:g}%)", f"{invoice['tax']:,.2f}"])
    rows.append(["", "", "Total", f"{invoice['currency']} {invoice['total']:,.2f}"])

    items_tbl = Table(rows, colWidths=[3.6 * inch, 0.7 * inch, 1.3 * inch, 1.4 * inch])
    items_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b5394")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#0b5394")),
                ("LINEBELOW", (0, -4), (-1, -4), 0.4, colors.grey),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (2, -1), (-1, -1), colors.HexColor("#eef3f8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, colors.HexColor("#f7f9fb")]),
            ]
        )
    )
    story.append(items_tbl)
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            f"Payment terms: net {(invoice['due_date'] - invoice['invoice_date']).days} days. "
            f"Make checks payable to {invoice['vendor_name']}.",
            small,
        )
    )

    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=6, help="Number of invoices to generate")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "Data" / "Samples",
        help="Output folder for the PDFs",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for i in range(1, args.count + 1):
        inv = random_invoice(seed=i)
        out = args.out / f"{inv['invoice_number']}.pdf"
        build_pdf(inv, out)
        print(f"  wrote {out.name}  ({inv['vendor_name']}, {inv['currency']} {inv['total']:,.2f})")

    print(f"\nGenerated {args.count} sample invoice(s) in {args.out}")
    print("Drop them into Data/Inbox/ to feed the UiPath bot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
