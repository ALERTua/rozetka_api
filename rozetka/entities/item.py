from functools import cached_property
from typing import Dict, List, Collection

from global_logger import Log

from rozetka.tools import tools, constants

LOG = Log.get_logger()


class Item:
    _cache = dict()  # type: Dict[int, Item]
    _data: Dict = dict()

    def __init__(self, id_, direct=True, **kwargs):
        assert direct is False, f"You cannot use {self.__class__.__name__} directly. Please use get classmethod."
        self.id_ = id_
        assert isinstance(self.id_, int), f"{self.__class__.__name__} id must be an int"
        self.category = None
        self.data = kwargs

        if (stars := self.__dict__.get('stars', None)) is not None:
            if '%' in str(stars):
                self.stars = int(stars.rstrip('%')) / 100

        if (comments_mark := self.__dict__.get('comments_mark', None)) is not None:
            self.comments_mark = float(comments_mark)

        self._parsed = False

    def __str__(self):
        if title := self.__dict__.get('title'):
            return f"({self.id_}) {title}"

        return f"{self.id_}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    def __iter__(self):
        for subitem in self.subitems:
            yield subitem
            # yield from subitem.__iter__()  # prevent sub-subitems

    @staticmethod
    def _parse_batch(*product_ids, subitems=False, parse_subitems=True):
        url = 'https://xl-catalog-api.rozetka.com.ua/v4/goods/getDetails'
        params = {
            'country': constants.COUNTRY,
            'lang': constants.LANGUAGE,
            'with_groups': 1,
            'with_docket': 1,
            'goods_group_href': 1,
            'product_ids': ",".join(product_ids),
        }

        # LOG.debug(f"Parsing batch of {len(product_ids)} products")
        output = []
        req = tools.get(url, params=params, headers=constants.DEFAULT_HEADERS)
        if req.status_code != 200:
            LOG.error(f"Error while parsing batch of {len(product_ids)} products: {req.status_code}: {req.reason}")
            return output

        if req is None:
            return output

        try:
            data: List[dict] = req.json().get('data')
        except Exception as e:
            data = []
        """
        {
            "id": 280528638,
            "title": "Мобільний телефон Samsung Galaxy A32 4/128 GB Black",
            "title_suffix": "",
            "price": 10399,
            "old_price": 10499,
            "price_pcs": "281.05",
            "href": "https://rozetka.com.ua/ua/samsung_galaxy_a32_4_128gb_black/p280528638/",
            "status": "active",
            "status_inherited": "active",
            "sell_status": "available",
            "category_id": 80003,
            "seller_id": 5,
            "merchant_id": 1,
            "brand": "Samsung",
            "brand_id": 12,
            "group_id": 36310773,
            "group_name": "36310773",
            "group_title": "Мобільний телефон Samsung Galaxy A32 4/128GB",
            "pl_bonus_charge_pcs": 0,
            "pl_use_instant_bonus": 0,
            "state": "new",
            "docket": "Екран (6.4\", Super AMOLED, 2400x1080) / Mediatek Helio G80 (2 x 2.0 ГГц + 6 x 1.8 ГГц) / 
            "mpath": ".4627949.80003.",
            "is_group_primary": 1,
            "dispatch": 1,
            "premium": 0,
            "preorder": 0,
            "comments_amount": 109,
            "comments_mark": 3.9,
            "gift": null,
            "tag": {
                "name": "action",
                "title": "Акция",
                "priority": 9,
                "goods_id": 280528638
            },
            "pictograms": [{
                    "is_auction": true,
                    "view_position": 1,
                    "order": 49,
                    "id": 30277,
                    "goods_id": 280528638,
                    "title": "ROZETKA Обмін",
                    "image_url": "https://content2.rozetka.com.ua/goods_tags/images_ua/original/222408740.png",
                    "view_type": "in_central_block",
                    "announce": null,
                    "has_description": 1,
                    "description": null,
                    "url": null,
                    "url_title": null,
                    "icon_mobile": ""
                }
            ],
            "title_mode": null,
            "use_group_links": null,
            "is_need_street_id": false,
            "image_main": "https://content1.rozetka.com.ua/goods/images/big_tile/175376690.jpg",
            "images": {
                "main": "https://content1.rozetka.com.ua/goods/images/big_tile/175376690.jpg",
                "preview": "https://content1.rozetka.com.ua/goods/images/preview/175376690.jpg",
                "hover": "https://content.rozetka.com.ua/goods/images/big_tile/175376700.jpg",
                "all_images": ["https://content1.rozetka.com.ua/goods/images/original/175376690.jpg", 
                                "https://content.rozetka.com.ua/goods/images/original/175376700.jpg", 
                                "https://content2.rozetka.com.ua/goods/images/original/175376709.jpg", 
                                "https://content1.rozetka.com.ua/goods/images/original/175376715.jpg", 
                                "https://content1.rozetka.com.ua/goods/images/original/175376721.jpg", 
                                "https://content1.rozetka.com.ua/goods/images/original/175376697.jpg", 
                                "https://content1.rozetka.com.ua/goods/images/original/175376698.jpg", 
                                "https://content.rozetka.com.ua/goods/images/original/175376694.jpg"]
            },
            "parent_category_id": 4627949,
            "is_docket": true,
            "primary_good_title": "Мобільний телефон Samsung Galaxy A32 4/128 GB Black",
            "groups": {
                "color": [{
                        "value": "Black",
                        "href": "https://rozetka.com.ua/ua/samsung_galaxy_a32_4_128gb_black/p280528638/",
                        "rank": "99.9997",
                        "id": 280528638,
                        "is_group_primary": 1,
                        "option_id": 21716,
                        "option_name": "21716",
                        "value_id": 6691,
                        "color": {
                            "id": 6691,
                            "hash": "#000",
                            "url": null
                        },
                        "active_option": true
                    }, {
                        "value": "Lavenda",
                        "href": "https://rozetka.com.ua/ua/samsung_galaxy_a32_4_128gb_lavender/p280528633/",
                        "rank": "99.9997",
                        "id": 280528633,
                        "is_group_primary": 0,
                        "option_id": 21716,
                        "option_name": "21716",
                        "value_id": 1360088,
                        "color": {
                            "id": 1360088,
                            "hash": "#000",
                        "url": "https://content.rozetka.com.ua/goods_details_values/images/original/196717502.jpg"
                        },
                        "active_option": false
                    }
                ]
            },
            "stars": "78%",
            "discount": 1,
            "config": {
                "title": true,
                "brand": false,
                "image": true,
                "price": true,
                "old_price": true,
                "promo_price": true,
                "status": true,
                "bonus": true,
                "gift": true,
                "rating": true,
                "wishlist_button": true,
                "compare_button": true,
                "buy_button": true,
                "tags": true,
                "pictograms": true,
                "description": true,
                "variables": true,
                "hide_rating_review": false
            }
        }
        """

        for item_data in data:
            id_ = item_data.get('id')
            if not id_:
                continue

            item_data.pop('id')
            if subitems:
                item = SubItem.get(id_, **item_data)
            else:
                item = Item.get(id_, **item_data)
            item._parsed = True
            output.append(item)

            if parse_subitems:
                output.extend(item.subitems)
        # LOG.debug(f"Parsing batch of {len(product_ids)} products done. Got {len(output)} Items")
        return output

    @staticmethod
    def parse_multiple(*product_ids, subitems=False, parse_subitems=True):
        if not product_ids:
            return []

        if isinstance(product_ids[0], Item):
            product_ids = [i.id_ for i in product_ids]
        elif isinstance(product_ids[0], Collection):
            product_ids = product_ids[0]

        product_ids_str = [str(i) for i in product_ids]
        chunk_size = constants.BULK_ITEMS_REQUEST_MAX_LENGTH
        chunked_lists = tools.slice_list(product_ids_str, chunk_size)
        LOG.debug(f"Parsing {len(product_ids)} products divided into {len(chunked_lists)} batches by {chunk_size} each")
        outputs = Item._parse_batch(*chunked_lists[0], subitems=subitems, parse_subitems=parse_subitems)
        outputs = tools.fnc_map(Item._parse_batch, *chunked_lists, subitems=subitems, parse_subitems=parse_subitems)
        outputs = [i for i in outputs if i]
        output = []
        for list_ in outputs:
            output.extend(list_)
        return output

    @cached_property
    def subitem_ids(self):
        groups = self._data.get('groups', {})
        if not groups:
            return []

        for _, block in groups.items():
            block_iterator = block if isinstance(block, list) else block.values()
            for group in block_iterator:
                if isinstance(group, list):
                    subitem_iterator = group
                elif isinstance(group, dict):
                    subitem_iterator = [group]
                else:
                    continue

                for subitem in subitem_iterator:
                    if id_ := subitem.get('id'):
                        if id_ == self.id_:
                            continue

                        yield id_

    @cached_property
    def subitems(self):
        subitem_ids = list(set(self.subitem_ids))
        if not subitem_ids:
            return []

        output = self.__class__.parse_multiple(*subitem_ids, subitems=True)
        for subitem in output:
            subitem.parent_item = self
            subitem.category = self.category
        return output

    def parse(self, force=False, *args, **kwargs):
        if not force and self._parsed:
            return

        self.__class__.parse_multiple(*[self.id_], *args, **kwargs)

    @classmethod
    def get(cls, id_, **kwargs):
        if id_ in cls._cache:
            output = cls._cache[id_]
            if kwargs and not output.data:
                output.data = kwargs
        else:
            output = cls(id_, direct=False, **kwargs)
        cls._cache[id_] = output
        return output

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self.__dict__.update(value)
        self._data = value


class SubItem(Item):
    def __init__(self, id_, **kwargs):
        super().__init__(id_, **kwargs)
        self.parent_item = None

    @property
    def subitems(self):
        return []

    @property
    def subitem_ids(self):
        return []

    def parse(self, force=False, *args, **kwargs):
        return super().parse(force=force, subitems=True, parse_subitems=False)


if __name__ == '__main__':
    item_ = Item.get(331350610)
    item_.parse()
    from rozetka.entities.category import Category

    category = Category.get(2394287)
    category.parse_items()

    pass
