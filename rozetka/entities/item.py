from rozetka.tools import tools

from global_logger import Log

LOG = Log.get_logger()


class Item:
    def __init__(self, id_):
        self.id_ = id_
        assert isinstance(self.id_, int), f"{self.__class__.__name__} id must be an int"
        self.title = None
        self.url = None
        self.docket = None
        self.is_docket = None
        self.description_fields = None
        self.category_id = None
        self.category = None
        self.comments_amount = None
        self.comments_mark = None
        self.merchant_id = None
        self.price_old = None
        self.pl_bonus_charge_pcs = None
        self.pl_use_instant_bonus = None
        self.price = None
        self.price_pcs = None
        self.sell_status = None
        self.status = None
        self.seller_id = None
        self.state = None
        self.image_main = None
        self.images = None
        self.parent_category_id = None
        self.parent_category = None
        self.brand = None
        self.brand_id = None
        self.producer_id = None
        self.discount = None
        self.stars = None
        self.groups = None
        self.is_groups_title = None
        self.config = None
        self.has_brand = None
        self.has_buy_button = None
        self.has_compare_button = None
        self.has_description = None
        self.has_gift = None
        self.has_image = None
        self.has_old_price = None
        self.has_pictograms = None
        self.has_price = None
        self.has_promo_price = None
        self.has_rating = None
        self.has_status = None
        self.has_tags = None
        self.has_title = None
        self.has_variables = None
        self.has_wishlist_button = None
        self.has_promo_code = None
        self.has_hide_rating_review = None
        self.has_show_supermarket_price = None

    def __str__(self):
        return f"{self.id_}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    def parse(self):
        # LOG.debug(f"Parsing {self}")
        params = {'country': 'UA', 'lang': 'ua', 'text': self.id_}
        req = tools.get('https://search.rozetka.com.ua/search/api/v6', params=params)
        if not req.ok:
            return

        data = req.json().get('data')
        item_data = data.get('goods')
        if not item_data:
            return

        item_data: dict = item_data[0]
        self.title = item_data.get('title')
        self.url = item_data.get('href')
        self.docket = item_data.get('docket')
        self.is_docket = item_data.get('is_docket')
        self.description_fields = item_data.get('description_fields')
        self.category_id = item_data.get('category_id')
        self.comments_amount = item_data.get('comments_amount')
        self.comments_mark = item_data.get('comments_mark')
        self.merchant_id = item_data.get('merchant_id')
        self.price_old = item_data.get('old_price')
        self.pl_bonus_charge_pcs = item_data.get('pl_bonus_charge_pcs')
        self.pl_use_instant_bonus = item_data.get('pl_use_instant_bonus')
        self.price = item_data.get('price')
        self.price_pcs = item_data.get('price_pcs')
        self.sell_status = item_data.get('sell_status')
        self.status = item_data.get('status')
        self.seller_id = item_data.get('seller_id')
        self.state = item_data.get('state')
        self.image_main = item_data.get('image_main')
        self.images = item_data.get('images')
        self.parent_category_id = item_data.get('parent_category_id')
        self.brand = item_data.get('brand')
        self.brand_id = item_data.get('brand_id')
        self.producer_id = item_data.get('producer_id')
        self.discount = item_data.get('discount')

        if stars := item_data.get('stars'):
            self.stars = int(stars.rstrip('%')) / 100
        self.groups = item_data.get('groups')
        self.is_groups_title = item_data.get('is_groups_title')
        self.config = config = item_data.get('config', {})
        self.has_brand = config.get('brand')
        self.has_buy_button = config.get('buy_button')
        self.has_compare_button = config.get('compare_button')
        self.has_description = config.get('description')
        self.has_gift = config.get('gift')
        self.has_image = config.get('image')
        self.has_old_price = config.get('old_price')
        self.has_pictograms = config.get('pictograms')
        self.has_price = config.get('price')
        self.has_promo_price = config.get('promo_price')
        self.has_rating = config.get('rating')
        self.has_status = config.get('status')
        self.has_tags = config.get('tags')
        self.has_title = config.get('title')
        self.has_variables = config.get('variables')
        self.has_wishlist_button = config.get('wishlist_button')
        self.has_promo_code = config.get('promo_code')
        self.has_hide_rating_review = config.get('hide_rating_review')
        self.has_show_supermarket_price = config.get('show_supermarket_price')
        return True


if __name__ == '__main__':
    item = Item(329710705)
    item_data_ = item.parse()
    pass