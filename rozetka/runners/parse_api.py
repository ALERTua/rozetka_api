import asyncio

import pendulum
from global_logger import Log
from knockknock import telegram_sender, discord_sender, slack_sender, teams_sender
from progress.bar import Bar
from worker import worker

from rozetka.entities.category import Category
from rozetka.entities.item import Item
from rozetka.entities.point import Point
from rozetka.tools import db, constants

LOG = Log.get_logger()

setters = (
    constants.Setter(fnc=Point.tag, flds=constants.TAGS),
    constants.Setter(fnc=Point.field, flds=constants.FIELDS),
)


def parse_item(item: Item):
    # item.parse()
    point = Point(item.id_)
    for setter in setters:
        for fld in setter.flds:
            if (item_fld := getattr(item, fld, None)) is not None:
                fnc = getattr(point, setter.fnc.__name__)
                point = fnc(fld, item_fld)
    return point


def get_category_items(category: Category):
    items = category.items
    for subcategory in category.subcategories:
        items.extend(get_category_items(subcategory))
    return items


@worker  # https://github.com/Danangjoyoo/python-worker
def parse_category(category: Category):
    category_items = get_category_items(category)
    if not category_items:
        return

    LOG.green(f"Parsing {len(category_items)} items for {category}")
    items = Item.parse_multiple(*category_items)
    if not items:
        return

    LOG.debug(f"Building points for {len(items)} items @ {category}")
    points = []
    for item in items:
        item_point = parse_item(item)
        points.append(item_point)

    LOG.debug(f"Dumping {len(points)} points for {category}")
    asyncio.run(db.dump_points_async(record=points))


def _main():
    healthcheck = asyncio.run(db.health_test())
    if not healthcheck:
        LOG.error("InfluxDB inaccessible!")
        raise Exception('healthcheck failure')

    healthcheck = asyncio.run(db.tst_write())
    if not healthcheck:
        LOG.error("InfluxDB inaccessible!")
        raise Exception('healthcheck failure')

    start = pendulum.now()
    LOG.verbose = constants.VERBOSE
    workers = []
    # for category in alive_it(Category.get_all_categories()):
    for category in Category.get_all_categories():
        worker_ = parse_category(category)
        workers.append(worker_)

    for worker_ in Bar(f'Waiting for workers').iter(workers):
        worker_.wait()

    duration = pendulum.now().diff_for_humans(start)
    LOG.debug(f"Duration: {duration}")
    pass


def main():
    assert constants.INFLUXDB_URL and constants.INFLUXDB_TOKEN and constants.INFLUXDB_ORG \
           and constants.INFLUXDB_BUCKET, "Please fill all INFLUXDB variables"

    assert constants.CALLS_MAX, "Please fill the correct CALLS_MAX variable"
    assert constants.CALLS_PERIOD, "Please fill the correct CALLS_PERIOD variable"

    fnc = _main  # https://github.com/huggingface/knockknock
    if (tg_token := constants.TELEGRAM_TOKEN) and (tg_chat := constants.TELEGRAM_CHAT_ID):
        fnc = telegram_sender(token=tg_token, chat_id=int(tg_chat))(fnc)

    if discord_webhook := constants.DISCORD_WEBHOOK_URL:
        fnc = discord_sender(discord_webhook)(fnc)

    if (slack_webhook := constants.SLACK_WEBHOOK_URL) and (slack_channel := constants.SLACK_CHANNEL):
        if slack_user_mentions := constants.SLACK_USER_MENTIONS:
            slack_user_mentions = slack_user_mentions.split()
        fnc = slack_sender(slack_webhook, slack_channel, slack_user_mentions)(fnc)

    if teams_webhook := constants.TEAMS_WEBHOOK_URL:
        if teams_user_mentions := constants.TEAMS_USER_MENTIONS:
            teams_user_mentions = teams_user_mentions.split()
        fnc = teams_sender(teams_webhook, teams_user_mentions)(fnc)

    fnc()


if __name__ == '__main__':
    main()
    pass
