import csv
from datetime import datetime, timezone
from pathlib import Path
import shutil

MAX_PDF_SALES_ROWS = 60


class ExportService:
    @staticmethod
    def export_report_csv(report: dict, output_dir: str = "exports") -> str:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"sales_report_{report['period']}_{ts}.csv"

        with out_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Period", report["period"]])
            writer.writerow(["From", report["start"].isoformat()])
            writer.writerow(["To", report["end"].isoformat()])
            writer.writerow(["Transactions", report["count"]])
            writer.writerow(["Revenue", f"{report['revenue']:.2f}"])
            writer.writerow(["Profit", f"{report['profit']:.2f}"])
            writer.writerow([])
            writer.writerow(["Sale ID", "Revenue", "Profit", "Sold At"])
            for row in report["sales"]:
                writer.writerow([row["id"], row["total_amount"], row["total_profit"], row["sold_at"]])
        return str(out_file)

    @staticmethod
    def export_report_pdf(report: dict, output_dir: str = "exports") -> str:
        """Export report to PDF (shows up to MAX_PDF_SALES_ROWS detailed sale rows)."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"sales_report_{report['period']}_{ts}.pdf"

        lines = [
            f"Sales Report ({report['period'].title()})",
            f"From: {report['start'].isoformat()}",
            f"To: {report['end'].isoformat()}",
            f"Transactions: {report['count']}",
            f"Revenue: {report['revenue']:.2f}",
            f"Profit: {report['profit']:.2f}",
            "",
            "SaleID  Revenue  Profit  SoldAt",
        ]
        for row in report["sales"][:MAX_PDF_SALES_ROWS]:
            lines.append(f"{row['id']}  {row['total_amount']:.2f}  {row['total_profit']:.2f}  {row['sold_at']}")
        if len(report["sales"]) > MAX_PDF_SALES_ROWS:
            lines.append("")
            lines.append(
                f"Note: Showing first {MAX_PDF_SALES_ROWS} of {len(report['sales'])} sales rows in PDF."
            )

        def _pdf_escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        stream_lines = ["BT /F1 11 Tf 50 800 Td"]
        for i, line in enumerate(lines):
            escaped = _pdf_escape(line)
            if i == 0:
                stream_lines.append(f"({escaped}) Tj")
            else:
                stream_lines.append(f"0 -14 Td ({escaped}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
            b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            + f"5 0 obj<</Length {len(stream)}>>stream\n{stream}\nendstream endobj\n".encode("latin-1", "replace")
            + b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000311 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n"
            + str(311 + len(stream)).encode()
            + b"\n%%EOF"
        )
        out_file.write_bytes(pdf_bytes)
        return str(out_file)


class ReceiptService:
    @staticmethod
    def create_receipt(sale: dict, items: list, output_dir: str = "receipts") -> str:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        file = out_dir / f"receipt_sale_{sale['id']}.txt"

        with file.open("w", encoding="utf-8") as f:
            f.write("Retail Shop Receipt\n")
            f.write("=" * 40 + "\n")
            f.write(f"Sale ID: {sale['id']}\n")
            f.write(f"Shop: {sale['shop_name']}\n")
            f.write(f"Sold by: {sale['username']}\n")
            f.write(f"Date: {sale['sold_at']}\n")
            f.write("-" * 40 + "\n")
            for item in items:
                f.write(
                    f"{item['product_name']} x{item['quantity']} @ {item['unit_price']:.2f} = {item['line_total']:.2f}\n"
                )
            f.write("-" * 40 + "\n")
            f.write(f"TOTAL: {sale['total_amount']:.2f}\n")
            f.write(f"PROFIT: {sale['total_profit']:.2f}\n")
            f.write("=" * 40 + "\n")
        return str(file)


class BackupService:
    @staticmethod
    def backup_database(db_path: str, backup_dir: str = "backups") -> str:
        out_dir = Path(backup_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = out_dir / f"inventory_backup_{ts}.db"
        shutil.copy2(db_path, backup_file)
        return str(backup_file)

    @staticmethod
    def restore_database(backup_file: str, db_path: str):
        src = Path(backup_file)
        if not src.exists():
            raise FileNotFoundError("Backup file not found")
        shutil.copy2(src, db_path)
