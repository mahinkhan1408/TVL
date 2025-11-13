import csv
import io
import re
from urllib.request import urlopen

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQv3sHuJQ_wjPViqn8-b3pNz8QBH_l-wAllPa-RhCZ8Vlaf9bRltG-WguziYKYn1SMj4D3snIZfn-9w/pub?output=csv"

with urlopen(url, timeout=10) as resp:
    raw = resp.read().decode('utf-8')
import csv
import io
import re
from urllib.request import urlopen

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQv3sHuJQ_wjPViqn8-b3pNz8QBH_l-wAllPa-RhCZ8Vlaf9bRltG-WguziYKYn1SMj4D3snIZfn-9w/pub?output=csv"

with urlopen(url, timeout=10) as resp:
    raw = resp.read().decode('utf-8')

reader = csv.DictReader(io.StringIO(raw))

header_map = {fn.strip().lower(): fn for fn in (reader.fieldnames or [])}

category_key = None
item_key = None
price_key = None
unit_key = None
for n in header_map:
    if n in ('category', 'cat'):
        category_key = header_map[n]
    if n in ('item', 'item name', 'description', 'line item', 'line_item'):
        item_key = header_map[n]
    if n.startswith('price') or 'price' in n:
        price_key = header_map[n]
    if n in ('unit', 'units', 'uom', 'measure'):
        unit_key = header_map[n]

if not category_key and 'Category' in (reader.fieldnames or []):
    category_key = 'Category'
if not item_key and 'Item' in (reader.fieldnames or []):
    item_key = 'Item'
if not price_key and 'Price' in (reader.fieldnames or []):
    price_key = 'Price'
if not unit_key and 'Unit' in (reader.fieldnames or []):
    unit_key = 'Unit'

print('Detected headers ->', 'category:', category_key, 'item:', item_key, 'price:', price_key, 'unit:', unit_key)

rows = []
for row in reader:
    if not (category_key and item_key and price_key):
        continue
    raw_category = row.get(category_key, '')
    raw_item = row.get(item_key, '')
    raw_price = row.get(price_key, '')
    raw_unit = row.get(unit_key, '') if unit_key else ''

    category = raw_category.strip() if raw_category is not None else ''
    item_name = raw_item.strip() if raw_item is not None else ''
    price_str = raw_price.strip() if raw_price is not None else ''
    unit = raw_unit.strip() if raw_unit is not None else ''

    cleaned = price_str.replace('\u00A0', '').strip()
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace(',', '')
    else:
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
    cleaned_price_str = re.sub(r"[^0-9.\\-]", '', cleaned)

    try:
        if cleaned_price_str in ('', '.', '-', None):
            raise ValueError('empty')
        price = float(cleaned_price_str)
    except Exception:
        price = 'N/A'
        print(f"Warning: Could not parse price for item '{item_name}'. Raw value was: '{price_str}'")

    rows.append((category, item_name, price, unit))

for r in rows[:30]:
    print(r)

print('Total rows parsed:', len(rows))

