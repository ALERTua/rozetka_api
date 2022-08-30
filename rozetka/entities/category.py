from functools import cached_property
from typing import List
from rozetka.tools import tools
from global_logger import Log

LOG = Log.get_logger()


class Category:
    cache: dict[int, object] = {}

    def __init__(self, id_, title=None, url=None, parent_category=None, direct=True):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.id_ = id_
        assert isinstance(self.id_, int), f"{self.__class__.__name__} id must be an int"
        self.title = title
        self.url = url
        self.parent_category = parent_category

    def __str__(self):
        return f"({self.id_}) {self.title}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id_ == other.id_

    def __hash__(self):
        return int(self.id_)

    @classmethod
    def get(cls, id_, title=None, url=None, parent_category=None):
        output = cls.cache.get(id_) or cls(id_=id_, direct=False)
        output.title = output.title or title
        output.url = output.url or url
        output.parent_category = output.parent_category or parent_category
        cls.cache[id_] = output
        return output

    def _get_page(self, page=1):
        # LOG.debug(f"Getting {self} page {page}")
        params = {
            'front-type': 'xl',
            'country': 'UA',
            'lang': 'ua',
            'sell_status': 'available,limited',
            'seller': 'rozetka',
            'sort': 'cheap',
            'state': 'new',
            'category_id': self.id_,
            'page': page,
        }
        response = tools.get('https://xl-catalog-api.rozetka.com.ua/v4/goods/get', params=params)
        if response.ok:
            return response.json()

        if response.status_code != 200:
            raise Exception('API response: {}'.format(response.status_code))

    @cached_property
    def items_ids(self):
        LOG.green(f"Getting all item ids for {self}")
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
        LOG.green(f"Got {len(output)} item ids for {self}")
        return output

    @cached_property
    def items(self):
        LOG.green(f"Getting all items for {self}")
        item_ids = self.items_ids
        from rozetka.entities.item import Item
        items = [Item(i) for i in item_ids]
        for item in items:
            if self.title:
                item.category = self.title
            if self.parent_category:
                item.parent_category = self.parent_category
        return items


class Categories:
    _cache: List[Category] = []

    @cached_property
    def categories(self) -> List[Category]:
        if self.__class__._cache:
            return self.__class__._cache

        params = {
            'front-type': 'xl',
            'country': 'UA',
            'lang': 'ua',
        }
        response = tools.get('https://common-api.rozetka.com.ua/v2/fat-menu/full', params=params)
        if not response.ok:
            if response.status_code != 200:
                raise LOG.exception('API response: {}'.format(response.status_code))

            return list()

        output = []
        data: dict = response.json().get('data', dict())
        for div in data.values():
            children = div.get('children', dict())
            category_title = div.get('title')
            if not children and (category_id := div.get('category_id')) is not None:
                category_url = div.get('manual_url')
                category = Category.get(id_=category_id, title=category_title, url=category_url)
                output.append(category)

            for subchild in children.values():
                for subsubchild in subchild:
                    subchildren = subsubchild.get('children', list())
                    subcategory_title = subsubchild.get('title')
                    if not subchildren and (subcategory_id := subsubchild.get('category_id')) is not None:
                        subcategory_url = subsubchild.get('manual_url')
                        category = Category.get(id_=subcategory_id, title=subcategory_title, url=subcategory_url,
                                                parent_category=category_title)
                        output.append(category)

                    for subsubsubchild in subchildren:
                        if (subsubcategory_id := subsubsubchild.get('category_id')) is not None:
                            subsubcategory_title = subsubsubchild.get('title')
                            subsubcategory_url = subsubsubchild.get('manual_url')
                            category = Category.get(id_=subsubcategory_id, title=subsubcategory_title,
                                                    url=subsubcategory_url, parent_category=subcategory_title)
                            output.append(category)

        # hashes = [hash(i) for i in output]
        Categories._cache = output = list(set(output))
        return output


def get_all_categories() -> List[Category]:
    return Categories().categories


if __name__ == '__main__':
    # category_ = Category(4624997)
    # category_.items_ids
    Categories().categories
    pass
