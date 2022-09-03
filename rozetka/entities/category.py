from functools import cached_property
from typing import List

from global_logger import Log

from rozetka.tools import tools, constants

LOG = Log.get_logger()


class Category:
    _cache: dict[int, object] = dict()
    _super_category_ids: List[int] = None
    _super_categories: List[object] = None
    _got_all_categories: bool = False

    def __init__(self, id_, title=None, url=None, parent_category=None, parent_category_id=None, direct=True):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.id_ = id_
        assert isinstance(self.id_, int), f"{self.__class__.__name__} id must be an int"
        self._title = title
        self.url = url
        self._parent_category_id = parent_category_id
        self._parent_category = parent_category
        self._data: dict | None = None
        self._subcategories_data: List[dict] | None = None
        self._subcategories: List[Category] | None = None

    def __str__(self):
        if self._title:
            return f"({self.id_}) {self.title}"

        return f"{self.id_}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id_ == other.id_

    def __hash__(self):
        return int(self.id_)

    def __iter__(self):
        yield self
        for subcategory in self.subcategories:
            yield from subcategory.__iter__()

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
            self._data = response.json().get('data', dict())
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def title(self):
        if self._title is None:
            self._title = self.data.get('title')
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @staticmethod
    def get_all_categories():
        LOG.green(f"Getting all categories")
        for super_category in Category.get_super_categories():
            yield super_category
            yield from super_category

    @staticmethod
    def get_super_categories():
        LOG.debug(f"Getting super categories")
        output = []
        for super_category_id in Category.get_super_category_ids():
            from rozetka.entities.supercategory import SuperCategory
            super_category = SuperCategory.get(id_=super_category_id)
            output.append(super_category)
        Category._super_categories = output
        LOG.debug(f"Got {len(output)} super categories")
        return Category._super_categories

    @staticmethod
    def get_super_category_ids():
        if Category._super_category_ids is None:
            LOG.debug(f"Getting super category ids")
            response = tools.get('https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList',
                                 headers=constants.DEFAULT_HEADERS, retry=True)
            Category._super_category_ids = output = response.json().get('data', list())
            LOG.debug(f"Got {len(output)} super category ids")
        return Category._super_category_ids

    @property
    def parent_category(self):
        if self._parent_category:
            return self._parent_category

        if self.parent_category_id:
            self._parent_category = self.__class__.get(self.parent_category_id)
        return self._parent_category

    @parent_category.setter
    def parent_category(self, value):
        self._parent_category = value

    @property
    def parent_category_id(self):
        if self._parent_category_id:
            return self._parent_category_id

        if self._parent_category:
            self._parent_category_id = self._parent_category.id_

        return self._parent_category_id

    @parent_category_id.setter
    def parent_category_id(self, value):
        self._parent_category_id = value

    @classmethod
    def get(cls, id_, title=None, url=None, data=None, parent_category_id=None, parent_category=None):
        if id_ in cls._cache:
            # noinspection PyTypeChecker
            output: Category = cls._cache.get(id_)
            output.title = output._title or title
            output.url = output.url or url
            output.parent_category_id = output._parent_category_id or parent_category_id
            output.parent_category = output._parent_category or parent_category
            output.data = output._data or data
        else:
            if data is None:
                pass  # todo:
            cls._cache[id_] = output = cls(id_=id_, title=title, url=url, parent_category_id=parent_category_id,
                                           parent_category=parent_category, direct=False)
        return output

    def _get_page(self, page=1):
        # LOG.debug(f"Getting {self} page {page}")
        params = {
            'front-type': 'xl',
            'country': constants.COUNTRY,
            'lang': constants.LANGUAGE,
            'sell_status': 'available,limited',
            'seller': 'rozetka',
            'sort': 'cheap',
            'state': 'new',
            'category_id': self.id_,
            'page': page,
        }
        response = tools.get('https://xl-catalog-api.rozetka.com.ua/v4/goods/get', params=params,
                             headers=constants.DEFAULT_HEADERS, retry=True)
        if response.status_code != 200:
            raise Exception(f'API response: {response.status_code}')

        return response.json()

    @cached_property
    def items_ids(self):
        LOG.debug(f"Getting all item ids for {self}")
        initial = self._get_page()
        if not initial:
            return

        data = initial.get('data')
        output: list = data.get('ids', list())
        total_pages = data.get('total_pages', 1)
        pages = [i for i in range(2, total_pages + 1)]
        results = []
        # for page in alive_it(pages):
        for page in pages:
            result = self._get_page(page)
            results.append(result)

        for result in results:
            ids = result.get('data', dict()).get('ids', list())
            output.extend(ids)
        output = [i for i in output if i is not None]
        output = list(set(output))
        LOG.debug(f"Got {len(output)} item ids for {self}")
        return output

    @cached_property
    def items(self):
        LOG.debug(f"Getting all items for {self}")
        item_ids = self.items_ids
        from rozetka.entities.item import Item
        items = [Item.get(i) for i in item_ids]
        for item in items:
            if self.title:
                item.category = self.title
            if self.parent_category:
                item.parent_category = self.parent_category
        LOG.debug(f"Got {len(items)} items for {self}")
        return items

    @property
    def subcategories_data(self):
        if self._subcategories_data is None:
            data = self.data

            id_ = data.get('id')
            assert id_ == self.id_

            title = data.get('title')
            if title and self._title is None:
                self.title = title

            url = data.get('href')
            if url and self.url is None:
                self.url = url

            parent_category_id = data.get('root_id')
            if parent_category_id and self._parent_category_id is None:
                self.parent_category_id = parent_category_id

            self._subcategories_data = data.get('children', list())
        return self._subcategories_data

    @subcategories_data.setter
    def subcategories_data(self, value):
        self._subcategories_data = value

    @property
    def subcategories(self):
        if not (subcategories_data := self.subcategories_data):
            return

        for subcategory_data in subcategories_data:
            parent_category_id = subcategory_data.get('parent_id')
            if parent_category_id != self.id_:
                pop = subcategories_data.pop(subcategories_data.index(subcategory_data))
                true_cat = self.__class__.get(parent_category_id)
                true_cat.subcategories_data = true_cat.subcategories_data or []
                true_cat.subcategories_data.append(pop)
                true_cat.subcategories_data.sort(key=lambda i: i.get('id', 0))
                true_subcategories_data = []
                for data in true_cat.subcategories_data:
                    if data.get('id') not in [i.get('id') for i in true_subcategories_data]:
                        true_subcategories_data.append(data)
                true_cat.subcategories_data = true_subcategories_data
                continue

            id_ = subcategory_data.get('id')
            title = subcategory_data.get('title')
            url = subcategory_data.get('href')
            children = subcategory_data.get('children', list())

            subcategory = self.__class__.get(id_)
            subcategory.title = title
            subcategory.url = url
            subcategory.parent_category_id = parent_category_id
            subcategory.parent_category = self
            subcategory.subcategories_data = children
            yield subcategory


if __name__ == '__main__':
    all_ = Category.get_all_categories()
    pass
