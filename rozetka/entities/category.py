from rozetka.entities.item import Item
from typing import List

from global_logger import Log

from rozetka.tools import tools, constants

LOG = Log.get_logger()


class Category:
    _cache: dict[int, object] = dict()

    def __init__(self, id_, title=None, url=None, parent_category=None, parent_category_id=None, direct=True):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.id_ = id_
        assert isinstance(self.id_, int), f"{self.__class__.__name__} id must be an int"
        self._title = title
        self.url = url
        self._items_ids = None
        self._items = None
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
        for subcategory in self.subcategories:
            LOG.debug(f"category iter: yielding {subcategory}")
            yield subcategory
            LOG.debug(f"category iter: yielding from {subcategory}")
            yield from subcategory.__iter__()

    def iter_parents(self):
        parent = self.parent_category
        if parent is self:
            LOG.warning(f"Looped parent detected for {self}")
        elif parent and parent is not self:
            LOG.debug(f"category parents iter: yielding {parent}")
            yield parent
            LOG.debug(f"category parents iter: yielding parents from {parent}")
            yield from parent.iter_parents()

    @property
    def data(self):
        if self._data is None:
            params = {
                'id': self.id_,
                'lang': constants.LANGUAGE,
                'country': constants.COUNTRY,
            }
            url = 'https://xl-catalog-api.rozetka.com.ua/v4/categories/get'
            response = tools.get(url, params=params, headers=constants.DEFAULT_HEADERS)
            if response is None:
                return

            self._data = response.json().get('data', dict()) or dict()

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
            from rozetka.entities.supercategory import SuperCategory
            class_ = Category
            from rozetka.entities.supercategory import get_super_category_ids
            if id_ in get_super_category_ids():
                class_ = SuperCategory
            output = class_(id_=id_, title=title, url=url, parent_category_id=parent_category_id,
                            parent_category=parent_category, direct=False)
            output.data = output._data or data
            cls._cache[id_] = output
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
                             headers=constants.DEFAULT_HEADERS)
        if response is None or response.status_code != 200:
            return {}

        return response.json()

    def _get_item_ids(self):
        LOG.debug(f"Getting all item ids for {self}")
        initial = self._get_page()
        if not initial:
            return []

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
        output.sort()
        LOG.debug(f"Got {len(output)} item ids for {self}")
        return output

    @property
    def items_ids(self):
        if self._items_ids is None:
            self._items_ids = self._get_item_ids()
        return self._items_ids

    @property
    def items(self):
        if self._items is None:
            LOG.debug(f"Getting all items for {self}")
            item_ids = self.items_ids
            if not item_ids:
                return []

            from rozetka.entities.item import Item
            items = [Item.get(i) for i in item_ids]
            # items.extend([list(i.__iter__()) for i in items])
            output = []
            for item in items:
                item.category = self
                output.append(item)
            output = list(set(output))
            output.sort(key=lambda i: i.id_)
            LOG.debug(f"Got {len(output)} items for {self}")
            self._items = output
        return self._items

    def parse_items(self):
        _ = Item.parse_multiple(*self.items_ids, parse_subitems=True)

    @property
    def subcategories_data(self):
        if self._subcategories_data is None:
            data = self.data
            if not data:
                return []

            id_ = data.get('id')
            if not id_:
                data = data.get('category')
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

    def _get_subcategories(self, parent_key='parent_id'):
        if self._subcategories is None:
            if not (subcategories_data := self.subcategories_data):
                # LOG.debug(f"No subcategories found for {self}")
                self._subcategories = []
                return self._subcategories

            output = []
            for subcategory_data in subcategories_data:
                parent_category_id = subcategory_data.get(parent_key, subcategory_data.get('parent_id'))
                if not parent_category_id:
                    LOG.error("THIS SHOULDN'T HAPPEN")

                if parent_category_id != self.id_:
                    pop = subcategories_data.pop(subcategories_data.index(subcategory_data))
                    true_cat = Category.get(parent_category_id)
                    true_cat.subcategories_data = true_cat.subcategories_data or []
                    true_cat.subcategories_data.append(pop)
                    true_cat.subcategories_data = [_ for _ in true_cat.subcategories_data if isinstance(_, dict)]
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
                if self.id_ == id_:
                    LOG.warning(f"Loop subcategory detected @ {id_} {title}")
                    continue

                children = subcategory_data.get('children', list())

                subcategory = Category.get(id_)
                subcategory.title = title
                subcategory.url = url
                subcategory.parent_category_id = parent_category_id
                subcategory.parent_category = self
                subcategory.subcategories_data = children
                output.append(subcategory)

            output.sort(key=lambda i: i.id_)
            self._subcategories = output
            LOG.debug(f"Got {len(output)} subcategories for {self}")
        return self._subcategories

    @property
    def subcategories(self):
        return self._get_subcategories()


if __name__ == '__main__':
    LOG.verbose = True
    category_ = Category.get(4658162)
    iids = category_.items_ids
    a = Item.parse_multiple(*iids, parse_subitems=False)
    items_ = category_.items
    pass
