from typing import Optional

from bs4 import Tag, ResultSet
from global_logger import Log

from rozetka.tools import tools

LOG = Log.get_logger()


class Cell:
    _cache: dict[str, object] = {}

    def __init__(self, direct=True, **kwargs):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use construct classmethod."
        self.id_: str = kwargs.get('id_')
        self.href: str = kwargs.get('href')
        self.pictures: list[str] = kwargs.get('pictures', list())
        self.title: str = kwargs.get('title')
        self.price_old: Optional[int] = kwargs.get('price_old')
        self.price: int = kwargs.get('price')
        self.available: bool = kwargs.get('available')
        self.rating = kwargs.get('rating')
        self.reviews = kwargs.get('reviews')
        # self.bonuses = kwargs.get('bonuses')  # todo:
        self.promo = kwargs.get('promo')
        # self.promo_type = kwargs.get('promo_type')  # todo:

    def __str__(self):
        return f"({self.price}) {self.title}"

    def __repr__(self):
        return f"[{self.__class__.__name__}] {self.price} {self.title} {self.href}"

    @classmethod
    def construct(cls, cell: Tag, allow_cache=True):
        name = f"{cls.__name__}"
        id_block: Tag = cell.find('div', class_='g-id')
        assert id_block is not None, f'Error parsing {name}. no id found:\n{cell}'
        id_ = id_block.text
        if allow_cache and cls._cache.get(id_):
            LOG.debug(f"Returning cached {name}")
            return cls._cache[id_]

        LOG.debug(f"{name} id: {id_}")

        title_block: Tag = cell.find("span", class_="goods-tile__title")
        assert title_block is not None, f'Error parsing {name}. no title_block found:\n{cell}'
        title = title_block.text
        assert title not in (None, '') and (title := title.strip()) not in (None, ''), \
            f'Error parsing {name}. wrong or empty title found: {title}\n{cell}'
        LOG.debug(f"{name} title: {title}")
        name = f"{cls.__name__} {title}"

        href_block: Tag = cell.find("a", class_="goods-tile__heading")
        assert href_block is not None, f'Error parsing {name}. no href_block found:\n{cell}'
        href = href_block.get('href')
        assert href is not None, f'Error parsing {name}. no href found:\n{cell}'
        LOG.debug(f"{name} href: {href}")

        picture_block: Tag = cell.find("a", class_="goods-tile__picture")
        picture_img_blocks: ResultSet = picture_block.find_all("img")
        pictures: list[str] = [i.attrs.get('src') for i in picture_img_blocks]
        pictures = [i for i in pictures if i and not i.endswith('.svg')]  # no empty urls or stubs
        # assert len(pictures) > 0, f'Error parsing {name}. no pictures found:\n{cell}'  # allow no images
        LOG.debug(f"{name} pictures: {pictures}")

        price_old_block: Tag = cell.find("div", class_="goods-tile__price--old")
        assert price_old_block is not None, f'Error parsing {name}. no price_old_block found:\n{cell}'
        price_old = tools.str_to_price(price_old_block.text) if price_old_block.text else None
        LOG.debug(f"{name} price_old: {price_old}")

        price_block: Tag = cell.find("div", class_="goods-tile__price")  # todo: currency symbol
        assert price_block is not None, f'Error parsing {name}. no price_block found:\n{cell}'
        price = tools.str_to_price(price_block.text)
        assert price not in (None, ''), f'Error parsing {name}. no price found:\n{cell}'
        LOG.debug(f"{name} price: {price}")

        available_block: Tag = cell.find("div", class_="goods-tile__availability")
        assert available_block is not None, f'Error parsing {name}. no available_block found:\n{cell}'
        available = 'goods-tile__availability--available' in available_block.attrs.get('class', [])
        LOG.debug(f"{name} available: {available}")

        rating_block: Tag = cell.find("svg", attrs={'aria-label': True})
        rating = tools.parse_rating(rating_block.attrs.get('aria-label')) if rating_block else None
        LOG.debug(f"{name} rating: {rating}")

        reviews_block: Tag = cell.find('span', class_='goods-tile__reviews-link')
        reviews = tools.parse_reviews(reviews_block.text) if reviews_block else None
        LOG.debug(f"{name} reviews: {reviews}")

        promo_block: Tag = cell.find('span', class_='promo-label')
        promo = promo_block.text.strip() if promo_block else None
        LOG.debug(f"{name} promo: {promo}")
        output = cls(direct=False, id_=id_, href=href, pictures=pictures, title=title, price_old=price_old, price=price,
                     available=available, rating=rating, reviews=reviews, promo=promo)
        cls._cache[id_] = output
        LOG.debug(f"Returning new {name}")
        return output
