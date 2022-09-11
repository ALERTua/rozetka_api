from itertools import chain
from typing import List

from global_logger import Log
from requests import Response

from rozetka.entities.category import Category
from rozetka.entities.item import Item, SubItem
from rozetka.tools import tools, constants

LOG = Log.get_logger()


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
            response = tools.get(url, params=params, headers=constants.DEFAULT_HEADERS, retry=True)
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
            self._subcategories_data = output = content.get('items', list())
            LOG.debug(f"Got {len(output)} subcategories data for {self}")
        return self._subcategories_data

    @staticmethod
    def get_fat_menu_categories():
        if SuperCategory._fat_menu_categories is not None:
            return SuperCategory._fat_menu_categories

        params = {
            'front-type': 'xl',
            'country': 'UA',
            'lang': 'ua',
        }
        response = tools.get('https://common-api.rozetka.com.ua/v2/fat-menu/full', params=params,
                             headers=constants.DEFAULT_HEADERS, retry=True)
        output = []
        data: dict = response.json().get('data', dict())
        for div in data.values():
            children = div.get('children', dict())
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

    @staticmethod
    def get_all_categories_recursively():
        LOG.green(f"Getting all categories")
        supercategories = list(SuperCategory.get_super_categories() + SuperCategory.get_fat_menu_categories())
        cache = list(Category._cache.values())
        supers_cache = list(SuperCategory._cache.values())
        # noinspection PyTypeChecker
        categories = supercategories + cache + supers_cache
        categories = list(set(categories))
        categories.sort(key=lambda i: i.id_)
        for category in categories:
            LOG.debug(f"get_all_categories_recursively: yielding {category}")
            yield category
            LOG.debug(f"get_all_categories_recursively: yielding from {category}")
            yield from category.__iter__()

    @staticmethod
    def get_all_categories_without_subcategories():
        all_categories = list(SuperCategory.get_all_categories_recursively())
        LOG.green(f"Got {len(all_categories)} total categories recursively")
        output = list(set([cat for cat in all_categories if not cat.subcategories_data]))
        LOG.green(f"Got {len(output)} categories without subcategories in them")
        return output

    @staticmethod
    def get_all_items_recursively() -> List[Item]:
        categories_without_subcategories = SuperCategory.get_all_categories_without_subcategories()
        # noinspection PyProtectedMember
        items_ids = tools.fncs_map((cat._get_item_ids for cat in categories_without_subcategories))
        items_ids = list(set(chain(*items_ids)))
        LOG.debug(f"Got {len(items_ids)} items from {len(categories_without_subcategories)} categories")
        items = Item.parse_multiple(*items_ids, parse_subitems=False)

        subitems_ids = list(set(list(chain(*[i.subitem_ids for i in items]))))
        LOG.debug(f"Got {len(subitems_ids)} subitems from {len(categories_without_subcategories)} categories")
        subitems = Item.parse_multiple(*subitems_ids, subitems=True)

        # noinspection PyProtectedMember
        all_items = list(set(items + subitems + list(Item._cache.values()) + list(SubItem._cache.values())))
        LOG.green(f"Got {len(all_items)} total items from {len(categories_without_subcategories)} categories")
        return all_items

    @staticmethod
    def get_super_categories():
        """

        :rtype: List[SuperCategory]
        """
        LOG.debug(f"Getting super categories")
        output = []
        for super_category_id in SuperCategory.get_super_category_ids():
            super_category = SuperCategory.get(id_=super_category_id)
            output.append(super_category)
        output.sort(key=lambda i: i.id_)
        SuperCategory._super_categories = output
        LOG.green(f"Got {len(output)} super categories")
        return SuperCategory._super_categories

    @staticmethod
    def get_super_category_ids():
        if SuperCategory._super_category_ids is None:
            LOG.debug(f"Getting super category ids")
            url = 'https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList'
            response: Response = tools.get(url, headers=constants.DEFAULT_HEADERS, cookies=constants.DEFAULT_COOKIES,
                                           retry=True)
            if not response.ok:
                msg = f'Error requesting "{url}": {response.status_code} {response.reason}'
                LOG.error(msg)
                raise Exception(msg)

            SuperCategory._super_category_ids = output = response.json().get('data', list())
            SuperCategory._super_category_ids.sort()
            LOG.debug(f"Got {len(output)} super category ids")
        return SuperCategory._super_category_ids

    @subcategories_data.setter
    def subcategories_data(self, value):
        self._subcategories_data = value


if __name__ == '__main__':
    LOG.verbose = True
    # supercategory = SuperCategory.get(1162030)
    # subs = supercategory.subcategories
    # get_super_category_ids = SuperCategory.get_super_category_ids()
    # get_super_categories = SuperCategory.get_super_categories()
    # get_all_categories_recursively = list(SuperCategory.get_all_categories_recursively())
    all_items_ = SuperCategory.get_all_items_recursively()
    pass
