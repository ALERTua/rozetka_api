import asyncio
import os
from collections import namedtuple
from typing import List

from influxdb_client import Point
from alive_progress import alive_it

from rozetka.tools import db
from rozetka.entities.category import Category, get_all_categories
from rozetka.entities.item import Item
from global_logger import Log

LOG = Log.get_logger()

Setter = namedtuple('Setter', ['fnc', 'flds'])
tags = [
    'title',
    'url',
    'brand',
    'brand_id',
    'category_id',
    'category',
    'parent_category_id',
    'parent_category',
]
fields = [
    'price',
    'price_old',
    'stars',
    'discount',
]
setters = (
    Setter(fnc=Point.tag, flds=tags),
    Setter(fnc=Point.field, flds=fields),
)


def parse_item(item: Item):
    item.parse()
    point = Point(item.id_)
    for setter in setters:
        for fld in setter.flds:
            if (item_fld := getattr(item, fld, None)) is not None:
                fnc = getattr(point, setter.fnc.__name__)
                point = fnc(fld, item_fld)
    return point


def parse_item_id(item_id):
    item: Item = Item(item_id)
    return parse_item(item)


def parse_category(category: Category):
    items = category.items
    points = []
    LOG.green(f"Parsing {len(items)} items for {category}")
    # for item_id in alive_it(item_ids):
    for item in items:
        item_points = parse_item(item)
        points.append(item_points)
    return points


def dump_points(points: List[Point]):
    LOG.green(f"Dumping {len(points)} data points")
    asyncio.run(db.dump_points(points))


def main():
    LOG.verbose = os.getenv('VERBOSE') == 'True'
    categories: List[Category] = get_all_categories()
    # for category in alive_it(categories):
    for category in categories:
        points = parse_category(category)
        dump_points(points)
    pass


if __name__ == '__main__':
    # parse_item_id(329710705)
    # asyncio.run(main())
    main()
    pass
