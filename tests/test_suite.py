from rozetka.entities.category import Category
from rozetka.entities.item import Item
from rozetka.entities.point import Point
from rozetka.entities.supercategory import SuperCategory


def test_subitems():
    item = Item.get(21155478)
    item.parse()
    subsubitems = []
    subitems = item.subitems
    for subitem in subitems:
        subsubitems.extend(subitem.subitems)
    assert len(subsubitems) == 0, "There should be no subsubitems"


def test_cache_item():
    id_ = 21155478
    item1 = Item.get(id_)
    item2 = Item.get(id_)
    assert item1 is item2, "Items of the same id should be the same"


def test_cache_category():
    id_ = 146633
    category1 = Category.get(id_)
    category2 = Category.get(id_)
    assert category1 is category2, "Categories of the same id should be the same"


def test_cache_supercategory():
    id_ = 4627893
    supercategory1 = SuperCategory.get(id_)
    supercategory2 = SuperCategory.get(id_)
    assert supercategory1 is supercategory2, "SuperCategories of the same id should be the same"


def test_point_hash():
    point = Point('measurement_name').tag('tag_name', 'tag_value').field('field_name', 'field_value')
    point2 = Point('measurement_name').tag('tag_name', 'tag_value').field('field_name', 'field_value')
    point3 = Point('measurement_name').tag('tag_name', 'tag_value1').field('field_name', 'field_value')
    list_ = [point, point2, point3]
    set_ = set(list_)
    assert len(set_) < len(list_), "Points should be unique"
