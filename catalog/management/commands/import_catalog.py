"""Import products from R i D A .xlsx into Brand/Category/Product models.

Usage:
    python manage.py import_catalog
    python manage.py import_catalog --xlsx "path/to/file.xlsx"
    python manage.py import_catalog --keep   # don't wipe existing products first
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.services import parse_excel, sync_catalog_from_data


class Command(BaseCommand):
    help = "Import FMCG catalog from Excel (size variants collapsed, no gram in names)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--xlsx",
            type=str,
            default="",
            help="Path to Excel file (default: CATALOG_XLSX setting)",
        )
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Do not delete existing products/categories before import",
        )

    def handle(self, *args, **options):
        path = Path(options["xlsx"]) if options["xlsx"] else Path(settings.CATALOG_XLSX)
        if not path.exists():
            raise CommandError(f"Excel file not found: {path}")

        self.stdout.write(f"Reading {path} …")
        data = parse_excel(path)
        meta = data["meta"]
        self.stdout.write(
            f"  rows={meta['total_rows']} unmatched={meta['unmatched_count']}"
        )
        for b in data["brands"]:
            self.stdout.write(
                f"  {b['name']:16s} raw={b['raw_count']:4d} unique={len(b['products']):4d}"
            )

        stats = sync_catalog_from_data(data, clear_products=not options["keep"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Synced brands={stats['brands']} categories={stats['categories']} "
                f"products={stats['products']}"
            )
        )
