from itertools import chain
from rozetka.entities.category import Category
from rozetka.entities.item import Item
from rozetka.entities.point import Point
from rozetka.entities.supercategory import SuperCategory

ITEM_ID = 330283417  # item id with subitems
CATEGORY_ID = 146633
SUPERCATEGORY_ID = 4627893


def test_item_getter():
    item = Item.get(ITEM_ID)
    assert item._parsed is False
    item.parse()
    assert item.brand
    assert item.brand_id
    # assert item.category
    assert item.category_id
    # assert item.comments_ammount
    assert item.comments_mark is not None  # may be 0
    assert item.config
    assert item.data
    assert item.discount is not None
    # assert item.docket
    assert item.group_id is not None
    # assert item.group_name
    # assert item.group_title
    # assert item.groups
    assert item.href
    assert item.id_
    assert item.image_main
    assert item.images
    assert item.mpath
    assert item.old_price is not None
    assert item.parent_category_id
    assert item.price is not None
    assert item.price_pcs is not None
    # assert item.primary_goods_title
    assert item.sell_status
    assert item.seller_id is not None
    assert item.stars
    assert item.state
    assert item.status
    assert item.subitem_ids
    assert item.subitems
    assert item.tag
    assert item.title


def test_item_in_category():
    item = Item.get(ITEM_ID)
    item.parse()
    category = Category.get(item.category_id)
    assert item.category_id == category.id_

    category_items = category.items
    category.parse_items()

    subitems_ids = list(set(list(chain(*[_.subitem_ids for _ in category_items]))))
    subitems_ids.sort()
    # assert item.id_ in category.items_ids or item.id_ in subitems_ids

    subitems = Item.parse_multiple(*subitems_ids, subitems=True)
    items_and_subitems = category_items + subitems
    items_and_subitems.sort(key=lambda _: _.id_)
    assert item in items_and_subitems


def test_subitems():
    item = Item.get(ITEM_ID)
    item.parse()
    subitems = item.subitems
    assert len(subitems) > 0, "There should be some subitems"

    subsubitems = []
    for subitem in subitems:
        subsubitems.extend(subitem.subitems)
    assert len(subsubitems) == 0, "There should be no subsubitems"


def test_cache_item():
    id_ = ITEM_ID
    item1 = Item.get(id_)
    item2 = Item.get(id_)
    assert item1 is item2, "Items of the same id should be the same"


def test_cache_category():
    id_ = CATEGORY_ID
    category1 = Category.get(id_)
    category2 = Category.get(id_)
    assert category1 is category2, "Categories of the same id should be the same"


def test_cache_supercategory():
    id_ = SUPERCATEGORY_ID
    supercategory1 = SuperCategory.get(id_)
    supercategory2 = SuperCategory.get(id_)
    assert supercategory1 is supercategory2, (
        "SuperCategories of the same id should be the same"
    )


def test_point_hash():
    point = (
        Point("measurement_name")
        .tag("tag_name", "tag_value")
        .field("field_name", "field_value")
    )
    point2 = (
        Point("measurement_name")
        .tag("tag_name", "tag_value")
        .field("field_name", "field_value")
    )
    point3 = (
        Point("measurement_name")
        .tag("tag_name", "tag_value1")
        .field("field_name", "field_value")
    )
    list_ = [point, point2, point3]
    set_ = set(list_)
    assert len(set_) < len(list_), "Points should be unique"
