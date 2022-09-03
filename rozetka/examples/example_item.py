from rozetka.entities.item import Item

item = Item.get(329710705)
item.parse()
print(item.__dict__())
