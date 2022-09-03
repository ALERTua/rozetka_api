from global_logger import Log

from rozetka.entities.category import Category

LOG = Log.get_logger()


class SuperCategory(Category):
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

    @subcategories_data.setter
    def subcategories_data(self, value):
        self._subcategories_data = value


if __name__ == '__main__':
    pass
