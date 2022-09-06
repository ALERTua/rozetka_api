from itertools import chain
from typing import List

from global_logger import Log

from rozetka.entities.category import Category
from rozetka.entities.item import Item
from rozetka.tools import tools, constants

LOG = Log.get_logger()


class SuperCategory(Category):
    _super_category_ids: List[int] = None
    _super_categories: List[object] = None

    def __init__(self, id_, title=None, url=None, parent_category=None, parent_category_id=None, direct=True):
        super().__init__(id_=id_, title=title, url=url, parent_category=parent_category,
                         parent_category_id=parent_category_id, direct=direct)

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
    def get_all_categories_recursively():
        LOG.green(f"Getting all categories")
        for super_category in SuperCategory.get_super_categories():
            yield super_category
            yield from super_category.__iter__()

    @staticmethod
    def get_all_categories_without_subcategories():
        all_categories = list(SuperCategory.get_all_categories_recursively())
        return list(set([cat for cat in all_categories if not cat.subcategories_data]))

    @staticmethod
    def get_all_items_recursively():
        categories_without_subcategories = SuperCategory.get_all_categories_without_subcategories()
        items_ids = tools.fncs_map((cat._get_item_ids for cat in categories_without_subcategories))
        items_ids = list(set(chain(*items_ids)))
        items = Item.parse_multiple(*items_ids, parse_subitems=False)

        subitems_ids = list(set(list(chain(*[i.subitem_ids for i in items]))))
        subitems = Item.parse_multiple(*subitems_ids, subitems=True)

        all_items = list(set(items + subitems))
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
        LOG.debug(f"Got {len(output)} super categories")
        return SuperCategory._super_categories

    @staticmethod
    def get_super_category_ids():
        if SuperCategory._super_category_ids is None:
            LOG.debug(f"Getting super category ids")
            response = tools.get('https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList',
                                 headers=constants.DEFAULT_HEADERS, retry=True)
            SuperCategory._super_category_ids = output = response.json().get('data', list())
            LOG.debug(f"Got {len(output)} super category ids")
        return SuperCategory._super_category_ids

    @subcategories_data.setter
    def subcategories_data(self, value):
        self._subcategories_data = value


if __name__ == '__main__':
    LOG.verbose = True
    # all_items = list(SuperCategory.all_categories_items())
    supercategory = SuperCategory.get(80004)

    pass
