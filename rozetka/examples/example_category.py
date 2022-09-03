import pprint
from rozetka.entities.category import Category
from rozetka.entities.item import Item


category = Category.get(152458)
print(f"Unparsed Category {category}")
data = category.data
print(f"""Parsed Category {category}:
---------
{data}
---------


""")

item_ids = category.items_ids
print(f"""Got category {category} item ids:
--------
{pprint.pformat(item_ids)}
--------


""")

items = category.items
print(f"""Unparsed Category {category} items:
--------
{pprint.pformat(items)}
--------


""")


Item.parse_multiple(items)
print(f"""Parsed Category {category} items:
--------
{pprint.pformat(items)}
--------


""")


subcategories = list(category.subcategories)
print(f"""Category {subcategories} subcategories:
--------
{subcategories}
--------
""")
