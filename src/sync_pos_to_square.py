#!/usr/bin/env python3
"""Sync POS menu prices to Square catalog.

Compares FlexePOS menu export against Square catalog via API and:
1. Updates prices in Square for matched items (preserving IDs/taxes/images)
2. Reports new POS items not yet in Square
3. Reports/deletes discontinued Square items
4. Optionally creates new items with images from Jersey Mike's website

Usage (from josiah directory):
    # Dry run (default) - shows what would change
    python src/sync_pos_to_square.py ../wmc-reconcile/data/menu-export-20358.csv

    # Apply price updates
    python src/sync_pos_to_square.py ../wmc-reconcile/data/menu-export-20358.csv --apply

    # Apply updates AND delete discontinued items
    python src/sync_pos_to_square.py ../wmc-reconcile/data/menu-export-20358.csv --apply --delete-discontinued

    # Create new items (with images)
    python src/sync_pos_to_square.py ../wmc-reconcile/data/menu-export-20358.csv --apply --create-new

    # Update images on existing items missing images
    python src/sync_pos_to_square.py ../wmc-reconcile/data/menu-export-20358.csv --apply --update-images
"""

import argparse
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Any

from square_catalog import SquareCatalog
from square_images import SquareImageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Custom matching rules for items with different names in POS vs Square
# Format: {"square": (item_name, variation_name), "pos": (plu_name, size)}
CUSTOM_MATCH_RULES = [
    {"square": ("Combo", "Regular"), "pos": ("Regular Drink & Chips", "")},
    {"square": ("Combo", "Giant"), "pos": ("Giant Drink & Chips", "")},
    # Cookie variations in Square are separate items in POS
    {"square": ("Cookie", "GF Snickerdoodle"), "pos": ("GF Snickerdoodle", "Regular")},
    # Kids Meal has "Regular" variation in Square but no size in POS
    {"square": ("Kids Meal", "Regular"), "pos": ("Kids Meal", "")},
    # Catering variations are separate items in POS
    {"square": ("Catering", "Subs by the Box"), "pos": ("Subs by the Box", "")},
]

# Items to exclude from discontinuation detection (Square-only items to keep)
EXCLUDE_FROM_DISCONTINUATION = {
    # EVENT items - intentional separate pricing
    "#3 Ham and Provolone (EVENT)",
    "#7 Turkey and Provolone (EVENT)",
    "#16 Chicken Cheese Steak (EVENT)",
    "#17 Mike's Famous Philly (EVENT)",
    "#42 Chipotle Chicken Cheese Steak (EVENT)",
    "#43 Chipotle Cheese Steak (EVENT)",
    "#55 Big Kahuna Chicken Cheese Steak (EVENT)",
    "#56 Big Kahuna Cheese Steak (EVENT)",
    # Event-only items (note: some have trailing spaces in Square)
    "Event Soda",
    "Event Water",
    "Event sub",
    "Event sub ",  # trailing space variant
}

# POS items to exclude from "new items" report (internal/not sold in Square)
EXCLUDE_FROM_NEW_ITEMS = {
    # Internal/accounting items
    "2 COOK COMBO",
    "Corp Kids Meal Chip",
    "Delivery",
    "Franchisee WLD Offset",
    "Grand_Op Donatio",
    "Local Donation",
    "Kids Meal Chip",
    "Kids Meal Chip ",  # trailing space variant
    "Kids Meal with Water",
    "PerPrsn (for 1)",
    # Discontinued or not sold
    "AMP Energy Drink",
    "Sobe Drink",
    "1/2 Cat Tray",
    "Loaf of Bread",
    "Tea",  # Gallon size not sold
    "Soda Bottle",  # 2 Liter not sold
    "Life WTR",
    "Tastykake",
    # Combo meals - not used in Square
    "#7 with Chips and Soda",
    "#7 with Chips and Water",
    "#13 with Chips and Soda",
    "#13 with Chips and Water",
    "#17 with Chips and Soda",
    "#17 with Chips and Water",
}


def normalize_name(name: str) -> str:
    """Normalize item name for matching: lowercase, collapse whitespace, strip."""
    return re.sub(r"\s+", " ", name.lower().strip())


def load_pos_items(csv_path: Path) -> list[dict[str, Any]]:
    """Load POS menu export CSV.

    Returns list of dicts with keys: category, plu_name, size, price
    """
    items = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            price_str = row.get("Current Standard Price", "0")
            try:
                price = float(price_str) if price_str else 0.0
            except ValueError:
                price = 0.0

            items.append({
                "category": row.get("Category", ""),
                "plu_name": row.get("PLU Name", ""),
                "size": row.get("Size", ""),
                "price": price,
                "normalized_name": normalize_name(row.get("PLU Name", "")),
                "normalized_size": normalize_name(row.get("Size", "")),
            })
    return items


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def build_square_catalog(catalog: SquareCatalog) -> dict[str, dict[str, Any]]:
    """Fetch Square catalog and build lookup by (item_name, variation_name).

    Returns dict keyed by (normalized_item_name, normalized_variation_name) tuple as string,
    with values containing item details and variation info.
    """
    items = catalog.list_catalog_items()
    lookup: dict[str, dict[str, Any]] = {}

    for item in items:
        item_data = _get(item, "item_data", {})
        if not item_data:
            continue
        item_name = _get(item_data, "name", "")
        item_id = _get(item, "id", "")

        variations = _get(item_data, "variations", []) or []
        for variation in variations:
            var_data = _get(variation, "item_variation_data", {})
            if not var_data:
                continue
            var_name = _get(var_data, "name", "")
            var_id = _get(variation, "id", "")
            version = _get(variation, "version", 0)

            # Get price in dollars
            price_money = _get(var_data, "price_money", {})
            price_cents = _get(price_money, "amount", 0) if price_money else 0
            price = price_cents / 100 if price_cents else 0.0

            # Get item_option_values (required for variations using Item Options)
            item_option_values = _get(var_data, "item_option_values", None)

            key = f"{normalize_name(item_name)}|{normalize_name(var_name)}"
            lookup[key] = {
                "item_id": item_id,
                "item_name": item_name,
                "variation_id": var_id,
                "variation_name": var_name,
                "version": version,
                "price": price,
                "price_cents": price_cents,
                "item_option_values": item_option_values,
            }

    return lookup


def match_items(
    pos_items: list[dict[str, Any]],
    square_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Match POS items to Square catalog.

    Returns:
        - matched: list of matched items with both POS and Square data
        - unmatched_pos: POS items not found in Square
        - unmatched_square: Square items not found in POS (excluding Tub variations)
    """
    matched = []
    unmatched_pos = []
    matched_square_keys: set[str] = set()

    # Build custom match lookup: pos key -> square key
    custom_pos_to_square: dict[str, str] = {}
    for rule in CUSTOM_MATCH_RULES:
        pos_key = f"{normalize_name(rule['pos'][0])}|{normalize_name(rule['pos'][1])}"
        square_key = f"{normalize_name(rule['square'][0])}|{normalize_name(rule['square'][1])}"
        custom_pos_to_square[pos_key] = square_key

    for pos_item in pos_items:
        pos_key = f"{pos_item['normalized_name']}|{pos_item['normalized_size']}"

        # First check custom rules
        square_key = custom_pos_to_square.get(pos_key)
        if square_key and square_key in square_lookup:
            square_item = square_lookup[square_key]
            matched.append({
                "pos": pos_item,
                "square": square_item,
                "match_type": "custom",
            })
            matched_square_keys.add(square_key)
            continue

        # Then try exact match
        if pos_key in square_lookup:
            square_item = square_lookup[pos_key]
            matched.append({
                "pos": pos_item,
                "square": square_item,
                "match_type": "exact",
            })
            matched_square_keys.add(pos_key)
            continue

        # Try matching with "each" variation (for catering items)
        each_key = f"{pos_item['normalized_name']}|each"
        if each_key in square_lookup:
            square_item = square_lookup[each_key]
            matched.append({
                "pos": pos_item,
                "square": square_item,
                "match_type": "each",
            })
            matched_square_keys.add(each_key)
            continue

        unmatched_pos.append(pos_item)

    # Find unmatched Square items (excluding Tub variations and excluded items)
    unmatched_square = []
    for key, square_item in square_lookup.items():
        if key in matched_square_keys:
            continue

        # Skip Tub variations (handled separately)
        if square_item["variation_name"].lower() == "tub":
            continue

        # Skip excluded items
        if square_item["item_name"] in EXCLUDE_FROM_DISCONTINUATION:
            continue

        unmatched_square.append(square_item)

    return matched, unmatched_pos, unmatched_square


def build_price_updates(
    matched: list[dict[str, Any]],
    square_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build list of price updates needed.

    Returns:
        - regular_updates: price updates for matched items
        - tub_updates: price updates for Tub variations (copy from Regular)
    """
    regular_updates = []
    tub_updates = []

    # Collect Regular prices by item name for Tub handling
    regular_prices: dict[str, float] = {}

    for match in matched:
        pos_item = match["pos"]
        square_item = match["square"]

        pos_price = pos_item["price"]
        square_price = square_item["price"]

        # Track Regular prices for Tub variations
        if square_item["variation_name"].lower() == "regular":
            regular_prices[normalize_name(square_item["item_name"])] = pos_price

        # Skip if prices match (within 1 cent tolerance)
        if abs(pos_price - square_price) < 0.01:
            continue

        regular_updates.append({
            "variation_id": square_item["variation_id"],
            "item_id": square_item["item_id"],
            "variation_name": square_item["variation_name"],
            "version": square_item["version"],
            "price_cents": int(round(pos_price * 100)),
            "name": f"{square_item['item_name']} / {square_item['variation_name']}",
            "old_price": square_price,
            "new_price": pos_price,
            "item_option_values": square_item.get("item_option_values"),
        })

    # Build Tub updates (copy Regular price)
    for key, square_item in square_lookup.items():
        if square_item["variation_name"].lower() != "tub":
            continue

        item_name_normalized = normalize_name(square_item["item_name"])
        if item_name_normalized not in regular_prices:
            continue

        regular_price = regular_prices[item_name_normalized]
        if abs(regular_price - square_item["price"]) < 0.01:
            continue

        tub_updates.append({
            "variation_id": square_item["variation_id"],
            "item_id": square_item["item_id"],
            "variation_name": square_item["variation_name"],
            "version": square_item["version"],
            "price_cents": int(round(regular_price * 100)),
            "name": f"{square_item['item_name']} / Tub",
            "old_price": square_item["price"],
            "new_price": regular_price,
            "item_option_values": square_item.get("item_option_values"),
        })

    return regular_updates, tub_updates


def print_report(
    regular_updates: list[dict[str, Any]],
    tub_updates: list[dict[str, Any]],
    unmatched_pos: list[dict[str, Any]],
    unmatched_square: list[dict[str, Any]],
) -> None:
    """Print sync report to stdout."""
    print(f"\n=== PRICE UPDATES ({len(regular_updates)} items) ===")
    for u in sorted(regular_updates, key=lambda x: x["name"]):
        diff = u["new_price"] - u["old_price"]
        sign = "+" if diff > 0 else ""
        print(f"  {u['name']}: ${u['old_price']:.2f} -> ${u['new_price']:.2f} ({sign}${diff:.2f})")

    print(f"\n=== TUB UPDATES ({len(tub_updates)} items) ===")
    for u in sorted(tub_updates, key=lambda x: x["name"]):
        print(f"  {u['name']}: ${u['old_price']:.2f} -> ${u['new_price']:.2f} (from Regular)")

    # Filter unmatched POS items: price > $0 and not in exclude list
    significant_pos = [
        p for p in unmatched_pos
        if p["price"] > 0 and p["plu_name"] not in EXCLUDE_FROM_NEW_ITEMS
    ]
    print(f"\n=== NEW POS ITEMS (not in Square, {len(significant_pos)} items) ===")
    for p in sorted(significant_pos, key=lambda x: (x["plu_name"], x["size"])):
        size_str = f" / {p['size']}" if p['size'] else ""
        print(f"  {p['plu_name']}{size_str}: ${p['price']:.2f}")

    print(f"\n=== DISCONTINUED (Square only, {len(unmatched_square)} items) ===")
    for s in sorted(unmatched_square, key=lambda x: (x["item_name"], x["variation_name"])):
        print(f"  {s['item_name']} / {s['variation_name']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync POS menu prices to Square catalog"
    )
    parser.add_argument(
        "pos_csv",
        type=Path,
        help="Path to FlexePOS menu export CSV",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default: dry-run)",
    )
    parser.add_argument(
        "--delete-discontinued",
        action="store_true",
        help="Delete discontinued items from Square (requires --apply)",
    )
    parser.add_argument(
        "--create-new",
        action="store_true",
        help="Create new items in Square for POS items not found (requires --apply)",
    )
    parser.add_argument(
        "--update-images",
        action="store_true",
        help="Update images on existing items that are missing images (requires --apply)",
    )
    parser.add_argument(
        "--image-urls",
        type=Path,
        default=None,
        help="Path to square-image-urls.json (default: auto-detect)",
    )
    args = parser.parse_args()

    dry_run = not args.apply

    if args.delete_discontinued and dry_run:
        print("ERROR: --delete-discontinued requires --apply")
        sys.exit(1)

    if args.create_new and dry_run:
        print("ERROR: --create-new requires --apply")
        sys.exit(1)

    if args.update_images and dry_run:
        print("ERROR: --update-images requires --apply")
        sys.exit(1)

    if not args.pos_csv.exists():
        print(f"ERROR: POS CSV not found: {args.pos_csv}")
        sys.exit(1)

    print(f"Loading POS items from {args.pos_csv}...")
    pos_items = load_pos_items(args.pos_csv)
    print(f"  Loaded {len(pos_items)} POS items")

    print("Fetching Square catalog via API...")
    catalog = SquareCatalog()
    square_lookup = build_square_catalog(catalog)
    print(f"  Fetched {len(square_lookup)} Square variations")

    print("Matching items...")
    matched, unmatched_pos, unmatched_square = match_items(pos_items, square_lookup)
    print(f"  Matched: {len(matched)}, Unmatched POS: {len(unmatched_pos)}, Unmatched Square: {len(unmatched_square)}")

    print("Building price updates...")
    regular_updates, tub_updates = build_price_updates(matched, square_lookup)

    # Print report
    print_report(regular_updates, tub_updates, unmatched_pos, unmatched_square)

    # Execute updates
    all_updates = regular_updates + tub_updates
    if all_updates:
        mode = "LIVE" if not dry_run else "DRY RUN"
        print(f"\n=== EXECUTING PRICE UPDATES ({mode}) ===")
        if dry_run:
            print(f"  Would update {len(all_updates)} variations")
        else:
            result = catalog.batch_update_prices(all_updates, dry_run=False)
            print(f"  Updated {len(result)} variations")

    # Execute deletes - only delete items where ALL variations are unmatched
    if unmatched_square and args.delete_discontinued:
        # Count total variations per item (from square_lookup)
        item_variation_counts: dict[str, int] = {}
        for sq in square_lookup.values():
            item_id = sq["item_id"]
            item_variation_counts[item_id] = item_variation_counts.get(item_id, 0) + 1

        # Count unmatched variations per item
        unmatched_by_item: dict[str, list[dict]] = {}
        for sq in unmatched_square:
            item_id = sq["item_id"]
            if item_id not in unmatched_by_item:
                unmatched_by_item[item_id] = []
            unmatched_by_item[item_id].append(sq)

        # Only delete items where ALL variations are unmatched
        items_to_delete = []
        items_partial = []  # Items with some matched variations
        for item_id, unmatched_vars in unmatched_by_item.items():
            total_vars = item_variation_counts.get(item_id, 0)
            if len(unmatched_vars) == total_vars:
                items_to_delete.append(item_id)
            else:
                items_partial.append((unmatched_vars[0]["item_name"], len(unmatched_vars), total_vars))

        if items_partial:
            print(f"\n=== SKIPPING PARTIAL DELETES ({len(items_partial)} items) ===")
            for name, unmatched, total in items_partial:
                print(f"  {name}: {unmatched}/{total} variations unmatched (keeping item)")

        if items_to_delete:
            print(f"\n=== DELETING DISCONTINUED ITEMS ({len(items_to_delete)} items) ===")
            deleted = catalog.batch_delete_catalog_objects(items_to_delete, dry_run=False)
            print(f"  Deleted {len(deleted)} items")
    elif unmatched_square and not dry_run:
        print("\n  (Use --delete-discontinued to remove discontinued items)")

    # Initialize image manager if needed for create or update operations
    image_manager = None
    if args.create_new or args.update_images:
        image_manager = SquareImageManager(args.image_urls)

    # Create new items from POS
    if args.create_new:
        # Filter unmatched POS items: price > $0 and not in exclude list
        items_to_create = [
            p for p in unmatched_pos
            if p["price"] > 0 and p["plu_name"] not in EXCLUDE_FROM_NEW_ITEMS
        ]

        if items_to_create:
            print(f"\n=== CREATING NEW ITEMS ({len(items_to_create)} items) ===")

            # Group by item name (aggregate variations)
            items_by_name: dict[str, list[dict]] = {}
            for p in items_to_create:
                name = p["plu_name"]
                if name not in items_by_name:
                    items_by_name[name] = []
                items_by_name[name].append(p)

            created_count = 0
            for item_name, variations in sorted(items_by_name.items()):
                # Build variation list
                var_list = []
                for v in variations:
                    var_name = v["size"] if v["size"] else "Regular"
                    var_list.append({
                        "name": var_name,
                        "price_cents": int(round(v["price"] * 100)),
                    })

                # Look up image URL
                image_url = image_manager.get_image_url(item_name) if image_manager else None

                var_str = ", ".join(f"{v['name']}: ${v['price_cents']/100:.2f}" for v in var_list)
                image_str = " (with image)" if image_url else " (no image found)"
                print(f"  Creating: {item_name} [{var_str}]{image_str}")

                try:
                    result = catalog.create_item(
                        name=item_name,
                        variations=var_list,
                        image_url=image_url,
                        dry_run=False,
                    )
                    if result:
                        created_count += 1
                except Exception as e:
                    print(f"    ERROR: {e}")

            print(f"  Created {created_count} items")
    elif unmatched_pos and not dry_run:
        significant_pos = [
            p for p in unmatched_pos
            if p["price"] > 0 and p["plu_name"] not in EXCLUDE_FROM_NEW_ITEMS
        ]
        if significant_pos:
            print("\n  (Use --create-new to create missing items in Square)")

    # Update images on existing items
    if args.update_images and image_manager:
        print("\n=== CHECKING IMAGES ON EXISTING ITEMS ===")

        # Get unique item IDs from matched items
        item_ids_checked: set[str] = set()
        items_needing_images: list[dict] = []

        for match in matched:
            sq = match["square"]
            item_id = sq["item_id"]
            if item_id in item_ids_checked:
                continue
            item_ids_checked.add(item_id)

            # Check if item has images
            try:
                image_ids = catalog.get_item_images(item_id)
                if not image_ids:
                    items_needing_images.append({
                        "item_id": item_id,
                        "item_name": sq["item_name"],
                    })
            except Exception as e:
                logger.warning("Failed to check images for %s: %s", item_id, e)

        print(f"  Checked {len(item_ids_checked)} items, {len(items_needing_images)} need images")

        if items_needing_images:
            print(f"\n=== UPLOADING IMAGES ({len(items_needing_images)} items) ===")
            uploaded_count = 0

            for item in items_needing_images:
                item_name = item["item_name"]
                item_id = item["item_id"]

                image_url = image_manager.get_image_url(item_name)
                if not image_url:
                    print(f"  {item_name}: no image URL found, skipping")
                    continue

                print(f"  {item_name}: uploading from {image_url}")
                try:
                    result = catalog.upload_image_from_url(
                        image_url,
                        object_id=item_id,
                        image_name=item_name,
                        dry_run=False,
                    )
                    if result:
                        uploaded_count += 1
                except Exception as e:
                    print(f"    ERROR: {e}")

            print(f"  Uploaded {uploaded_count} images")

    print("\nDone!")


if __name__ == "__main__":
    main()
