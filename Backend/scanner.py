# scanner.py
import json
import requests
from datetime import datetime
from pathlib import Path

INVENTORY_FILE = Path("data/sample_food.json") 

def load_inventory():
    """Load inventory JSON file, create if it doesn't exist."""
    if not INVENTORY_FILE.exists():
        return {"items": []}
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_inventory(inventory):
    """Save inventory back to JSON."""
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

def lookup_product(barcode):
    """Query Open Food Facts API for barcode info."""
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") != 1:
            return None

        p = data["product"]
        return {
            "name": p.get("product_name", "Unknown"),
            "brand": p.get("brands", "Unknown"),
            "category": p.get("categories", "Unknown"),
            "calories": p.get("nutriments", {}).get("energy-kcal_100g", None)
        }
    except Exception as e:
        print("Error connecting to API:", e)
        return None

def add_item_to_inventory(barcode, product_info):
    """Add a scanned item to inventory JSON."""
    inventory = load_inventory()
    new_id = max([item["id"] for item in inventory["items"]] + [0]) + 1

    item = {
        "id": new_id,
        "barcode": barcode,
        "product": product_info,
        "quantity": 1,
        "expiration_date": None,
        "added_at": datetime.now().isoformat()
    }

    inventory["items"].append(item)
    save_inventory(inventory)
    print(f"✅ Added {product_info['name']} to inventory.")

def main():
    print("📦 Inventory Scanner")
    print("Scan a barcode or type 'exit' to quit.\n")

    while True:
        barcode = input("Scan item: ").strip()
        if barcode.lower() == "exit":
            break

        product = lookup_product(barcode)
        if product:
            print(f"🔍 Found: {product['name']} ({product['brand']})")
        else:
            print("⚠️ Product not found. Saving as 'Unknown'.")
            product = {
                "name": "Unknown",
                "brand": "Unknown",
                "category": "Unknown",
                "calories": None
            }

        add_item_to_inventory(barcode, product)
        print()

    print(f"All scanned items saved to {INVENTORY_FILE}")

if __name__ == "__main__":
    main()
