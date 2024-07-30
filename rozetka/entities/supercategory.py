from itertools import chain
from typing import List

from global_logger import Log
from requests import Response

from rozetka.entities.category import Category
from rozetka.entities.item import Item, SubItem
from rozetka.tools import tools, constants

LOG = Log.get_logger()


def get_fat_menu_categories():
    # noinspection PyProtectedMember
    if SuperCategory._fat_menu_categories is not None:
        # noinspection PyProtectedMember
        return SuperCategory._fat_menu_categories

    params = {
        'front-type': 'xl',
        'country': 'UA',
        'lang': 'ua',
    }
    output = []
    response = tools.get('https://common-api.rozetka.com.ua/v2/fat-menu/full', params=params,
                         headers=constants.DEFAULT_HEADERS)
    if response is None:
        LOG.error(f"get_fat_menu_categories: response is None")
        return output

    if not response.ok:
        LOG.error(f"get_fat_menu_categories: response not ok: {response.status_code} {response.reason}")
        return output

    data: dict = response.json().get('data', dict())
    for div in data.values():
        children = div.get('children', dict())
        # noinspection DuplicatedCode
        if not children:
            category_id = div.get('category_id')
            if category_id is not None:
                category_title = div.get('title')
                category_url = div.get('manual_url')
                category = Category.get(id_=category_id, title=category_title, url=category_url)
                output.append(category)

        for subchild in children.values():
            for subsubchild in subchild:
                subchildren = subsubchild.get('children', list())
                # noinspection DuplicatedCode
                if not subchildren:
                    category_id = subsubchild.get('category_id')
                    if category_id is not None:
                        category_title = subsubchild.get('title')
                        category_url = subsubchild.get('manual_url')
                        category = Category.get(id_=category_id, title=category_title, url=category_url)
                        output.append(category)

                for subsubsubchild in subchildren:
                    category_id = subsubsubchild.get('category_id')
                    if category_id is not None:
                        category_title = subsubsubchild.get('title')
                        category_url = subsubsubchild.get('manual_url')
                        category = Category.get(id_=category_id, title=category_title, url=category_url)
                        output.append(category)

    SuperCategory._fat_menu_categories = output = list(set(output))
    return output


def get_all_item_ids_recursively():
    _ = get_super_category_ids()
    categories = list(get_all_categories_recursively())
    all_categories = list(set(categories))
    all_categories.sort(key=lambda _: _.id_)
    all_categories = list(filter(lambda _: _ is not None, all_categories))

    all_categories_len = len(all_categories)
    LOG.green(f"Got total {all_categories_len} categories")
    LOG.green("Getting ALL items recursively")
    # noinspection PyProtectedMember
    items_ids = tools.fncs_map((_._get_item_ids for _ in all_categories))
    items_ids = list(filter(lambda _: _ is not None, items_ids))
    items_ids = list(set(chain(*items_ids)))
    LOG.green(f"Got {len(items_ids)} item ids from {all_categories_len} categories")
    return items_ids, all_categories_len


def get_all_items_recursively(loop=False, items_ids=None, all_categories_len=None) -> List[Item]:
    if loop:
        return list()

    if items_ids is None:
        items_ids, all_categories_len = get_all_item_ids_recursively()

    items = Item.parse_multiple(*items_ids, parse_subitems=False)
    LOG.green(f"Got {len(items)} items from {all_categories_len} categories")

    LOG.green("Getting subitem ids")
    subitems_ids = list(set(list(chain(*[_.subitem_ids for _ in items]))))
    LOG.debug(f"Got {len(subitems_ids)} subitem ids from {all_categories_len} categories")
    subitems = Item.parse_multiple(*subitems_ids, subitems=True)
    LOG.debug(f"Got {len(subitems)} subitems from {all_categories_len} categories")

    # noinspection PyProtectedMember
    all_items = items + subitems + list(Item._cache.values()) + list(SubItem._cache.values())

    if not loop:
        for _ in all_items:
            if _.category_id:
                Category.get(id_=_.category_id)
        all_items += get_all_items_recursively(loop=True)

    all_items = list(set(all_items))
    all_items.sort(key=lambda _: _.id_)
    LOG.green(f"Got {len(all_items)} total items")

    # all_categories_ids = [_.id_ for _ in all_categories]
    # items_categories_ids = list(set([i.category_id for i in all_items]))
    # missing_categories_ids = [icid for icid in items_categories_ids if icid not in all_categories_ids]
    # missing_categories_ids.sort()
    # _ = [Category.get(id_=icid) for icid in missing_categories_ids]

    return all_items


def get_super_categories():
    """

    :rtype: List[SuperCategory]
    """
    LOG.debug(f"Getting super categories")
    output = []
    for super_category_id in get_super_category_ids():
        super_category = SuperCategory.get(id_=super_category_id)
        output.append(super_category)
    output.sort(key=lambda i: i.id_)
    SuperCategory._super_categories = output
    LOG.green(f"Got {len(output)} super categories")
    # noinspection PyProtectedMember
    return SuperCategory._super_categories


def get_super_category_ids():
    # noinspection PyProtectedMember
    if SuperCategory._super_category_ids is None:
        LOG.debug(f"Getting super category ids")
        url = 'https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList'
        response: Response = tools.get(url, headers=constants.DEFAULT_HEADERS, cookies=constants.DEFAULT_COOKIES)
        if response is None or not response.ok:
            msg = f'Error requesting "{url}": {response.status_code if response is not None else None} ' \
                  f'{response.reason if response is not None else None}'
            LOG.error(msg)
            raise Exception(msg)

        SuperCategory._super_category_ids = output = response.json().get('data', list())
        # noinspection PyProtectedMember
        SuperCategory._super_category_ids.sort()
        LOG.debug(f"Got {len(output)} super category ids")
    # noinspection PyProtectedMember
    return SuperCategory._super_category_ids


def get_all_categories_recursively():
    LOG.green("Getting ALL categories recursively")
    supercategories = list(get_super_categories() + get_fat_menu_categories())
    # noinspection PyProtectedMember
    cache = list(Category._cache.values())
    # noinspection PyProtectedMember
    supers_cache = list(SuperCategory._cache.values())
    # noinspection PyTypeChecker
    categories = supercategories + cache + supers_cache
    categories = list(set(categories))
    categories.sort(key=lambda i: i.id_)
    for category in categories:
        LOG.debug(f"get_all_categories_recursively: yielding {category}")
        yield category
        LOG.debug(f"get_all_categories_recursively: yielding parents for {category}")
        yield from category.iter_parents()
        LOG.debug(f"get_all_categories_recursively: yielding from {category}")
        yield from category.__iter__()

    LOG.green("Got ALL categories recursively")


class SuperCategory(Category):
    _super_category_ids: List[int] = None
    _super_categories = None  # type: List[SuperCategory]
    _fat_menu_categories = None  # type: List[Category]

    def __init__(self, id_, title=None, url=None, parent_category=None, parent_category_id=None, direct=True):
        super().__init__(id_=id_, title=title, url=url, parent_category=parent_category,
                         parent_category_id=parent_category_id, direct=direct)

    @property
    def data(self):
        if self._data is None:
            params = {
                'category_id': self.id_,
                'lang': constants.LANGUAGE,
                'country': constants.COUNTRY,
            }
            url = 'https://xl-catalog-api.rozetka.com.ua/v4/super-portals/get'
            response = tools.get(url, params=params, headers=constants.DEFAULT_HEADERS)
            if response is None:
                return

            self._data = response.json().get('data', dict()) or dict()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def subcategories_data(self):
        if self._subcategories_data is None:
            if not self.data:
                return list()

            blocks: list = self.data.get('blocks', list())
            category_trees = list(filter(lambda i: i.get('type') == 'seo_category_tree', blocks))
            if not category_trees:
                return {}

            category_tree: dict = category_trees[0]
            content: dict = category_tree.get('content', dict())
            output = content.get('items', list())
            output = [_ for _ in output if isinstance(_, dict)]
            self._subcategories_data = output
            LOG.debug(f"Got {len(output)} subcategories data for {self}")
        return self._subcategories_data

    @subcategories_data.setter
    def subcategories_data(self, value):
        self._subcategories_data = value

    @property
    def subcategories(self):
        return self._get_subcategories('root_id')


if __name__ == '__main__':
    LOG.verbose = False
    # get_fat_menu_categories()
    # all_items_ = get_all_items_recursively()
    # supercategory = SuperCategory.get(4625734)
    # supercategory.subcategories_data
    # iids = supercategory.items_ids
    # supers = get_super_categories()
    # ac = list(get_all_categories_recursively())
    # supercategory = SuperCategory.get(4627893)
    # subs = supercategory.subcategories
    # a = list(supercategory.__iter__())
    # all_items_ = SuperCategory.get_all_items_recursively()
    pass
