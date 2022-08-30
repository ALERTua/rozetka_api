from typing import Optional
from bs4 import ResultSet, BeautifulSoup, Tag
from global_logger import Log

from rozetka.tools import tools

LOG = Log.get_logger()


class Page:
    _cache: dict[str, object] = {}
    _title: str = 'Unknown Title'

    def __init__(self, url, direct=True, **kwargs):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.url: str = url
        self.id_: str = kwargs.get('id_')
        self.pictures: list[str] = kwargs.get('pictures', list())
        self.title: str = kwargs.get('title')
        self.price_old: Optional[int] = kwargs.get('price_old')
        self.price: int = kwargs.get('price')
        self.available: bool = kwargs.get('available')
        self.reviews = kwargs.get('reviews')

    def __str__(self):
        return f"{self.url}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    @classmethod
    def get(cls, url: str, allow_cache=True):
        name = f"{cls.__name__}"
        LOG.green(f"Parsing page data for {url}")
        response = tools.get(url)
        assert response.ok, f"Error requesting {url}"
        soup = BeautifulSoup(response.text, "lxml")

        id_block: Tag = soup.find('p', class_='product__code')
        assert id_block is not None, f'Error parsing {name}. no id found:\n{soup}'
        id_ = tools.ints_from_str(id_block.text) if id_block.text else None
        assert id_ is not None, f'Error parsing {name}. no id_ found:\n{soup}'
        id_ = str(id_[0])
        if allow_cache and cls._cache.get(id_):
            LOG.debug(f"Returning cached {name}")
            return cls._cache[id_]

        LOG.debug(f"{name} id: {id_}")

        product_title_block: Tag = soup.find('h1', class_='product__title')
        assert product_title_block is not None, f'Error parsing {name}. no product_title_block found:\n{soup}'
        title = tools.title_clean(product_title_block.text)
        name = f"{cls.__name__} {title}"

        picture_block: Tag = soup.find("rz-gallery-main-content-image", class_="main-slider__item")
        picture_img_blocks: ResultSet = picture_block.find_all("img")
        pictures: list[str] = [i.attrs.get('src') for i in picture_img_blocks]
        pictures = [i for i in pictures if i and not i.endswith('.svg')]  # no empty urls or stubs
        # assert len(pictures) > 0, f'Error parsing {name}. no pictures found:\n{cell}'  # allow no images
        LOG.debug(f"{name} pictures: {pictures}")

        prices_block: Tag = soup.find('div', class_='product-trade')
        assert prices_block is not None, f'Error parsing {name}. no prices_block found:\n{soup}'

        price_old_block: Tag = prices_block.find("p", class_="product-prices__small")
        price_old = tools.str_to_price(price_old_block.text) if price_old_block.text else None
        LOG.debug(f"{name} price_old: {price_old}")

        price_block: Tag = prices_block.find("p", class_="product-prices__big")  # todo: currency symbol
        assert price_block is not None, f'Error parsing {name}. no price_block found:\n{soup}'
        price = tools.str_to_price(price_block.text)
        assert price not in (None, ''), f'Error parsing {name}. no price found:\n{soup}'
        LOG.debug(f"{name} price: {price}")

        about_block: Tag = soup.find('div', class_='product-about__right')
        assert about_block is not None, f'Error parsing {name}. no about_block found:\n{soup}'

        available_block: Tag = about_block.find("div", class_="status-label--green")
        available = available_block is not None  # todo: half-empty
        LOG.debug(f"{name} available: {available}")

        # rating_block: Tag = soup.find("svg", attrs={'aria-label': True})  # todo:
        # rating = tools.parse_rating(rating_block.attrs.get('aria-label')) if rating_block else None
        # LOG.debug(f"{name} rating: {rating}")

        reviews_block: Tag = soup.find('a', class_='product__rating-reviews')
        reviews = tools.parse_reviews(reviews_block.text) if reviews_block else None
        LOG.debug(f"{name} reviews: {reviews}")

        output = cls(direct=False, id_=id_, url=url, pictures=pictures, title=title, price_old=price_old, price=price,
                     available=available, reviews=reviews)
        cls._cache[id_] = output
        LOG.debug(f"Returning new {name}")
        return output


def main():
    LOG.verbose = True
    page = Page.get('https://rozetka.com.ua/ua/atlantic_5903351335904/p325214854/')
    pass


if __name__ == '__main__':
    main()
