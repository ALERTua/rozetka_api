import itertools
import re

import requests
from bs4 import ResultSet, BeautifulSoup
from global_logger import Log

from rozetka.entities.cell import Cell

LOG = Log.get_logger()


def title_clean(title):
    """
    Cleans
    Ноутбуки - ROZETKA | Купити ноутбук в Києві: ціна, відгуки, продаж, вибір ноутбуків в Україні'
    to
    Ноутбуки
    """
    if not title:
        return ''

    split = re.split(' - ROZETKA', title)
    return split[0].strip()


def url_page(url, page_num):
    return f"{url.rstrip('/')}/page={page_num}"


class Grid:
    _cache: dict[str, object] = {}

    _title: str = 'Unknown Title'
    page: int = 0
    cell_blocks: dict[int, ResultSet] = {}
    cells: dict[int, list[Cell]] = {}

    def __init__(self, url, direct=True):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.url: str = url

    def __str__(self):
        return f"({len(self.parsed_cells)}) {self.title}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    @property
    def parsed_cells(self):
        return list(itertools.chain.from_iterable(self.cells.values()))

    @property
    def cheapest_cell(self):
        if cheapest := sorted(self.parsed_cells, key=lambda i: i.price):
            return cheapest[0]

    @staticmethod
    def _parse_cells(blocks):
        return [Cell.construct(i) for i in blocks]

    def _get_page_data(self, page: int):
        page_url = url_page(self.url, page)
        LOG.green(f"Parsing data for {page_url}")
        response = requests.get(page_url)
        assert response.ok, f"Error requesting {page_url} page {page}"
        soup = BeautifulSoup(response.text, "lxml")
        self.title = title_clean(soup.title.text)
        return soup.find_all("li", class_="catalog-grid__cell")

    def _get_cell_blocks(self, page: int):
        if cell_blocks := self.cell_blocks.get(page):
            LOG.debug(f"Returning cached cells for {self} page {page}")
            return cell_blocks

        output = self.cell_blocks[page] = self._get_page_data(page=page)
        LOG.debug(f"Got {len(output)} cell blocks for {self} page {page}")
        return output

    def _get_cells(self, page: int):
        if page in self.cells:
            LOG.debug(f"Returning cached cells for {self} page {page}")
            return self.cells[page]

        cell_blocks = self._get_cell_blocks(page=page)
        output = self.cells[page] = self._parse_cells(blocks=cell_blocks)
        LOG.debug(f"Got {len(output)} cells for {self} page {page}")
        return output

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value: str):
        if page_index := re.search(r'/page=\d+', value):
            page_index_str = page_index.group()
            self._url = value.replace(page_index_str, '')
            self.page = int("".join(re.findall(r'\d+', page_index_str)))
        else:
            self._url = value
            self.page = 1

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = title_clean(value)

    @classmethod
    def get(cls, url: str, allow_cache=True, parse=True):
        name = f"{cls.__name__}"
        if allow_cache and cls._cache.get(url):
            # noinspection PyTypeChecker
            output: Grid = cls._cache[url]
            LOG.debug(f"Returning cached {name}")
            return output

        output = cls(direct=False, url=url)
        if parse:
            output._get_cells(output.page)
        cls._cache[url] = output
        LOG.debug(f"Returning new {name}")
        return output


def main():
    LOG.verbose = True
    grid = Grid.get('https://rozetka.com.ua/ua/notebooks/c80004/page=2/')
    pass


if __name__ == '__main__':
    main()
