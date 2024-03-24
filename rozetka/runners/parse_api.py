import asyncio
from copy import copy

import pendulum

from global_logger import Log
from knockknock import telegram_sender, discord_sender, slack_sender, teams_sender
from progress.bar import Bar

from rozetka.entities.item import Item, SubItem
from rozetka.entities.supercategory import SuperCategory
from rozetka.entities.category import Category
from rozetka.entities.point import Point
from rozetka.entities.supercategory import get_all_items_recursively, get_all_item_ids_recursively
from rozetka.tools import db, constants, tools

LOG = Log.get_logger()

setters = (
    constants.Setter(fnc=Point.tag, flds=constants.TAGS),
    constants.Setter(fnc=Point.field, flds=constants.FIELDS),
)


def build_item_point(item: Item):
    # item.parse()
    point = Point(constants.MEASUREMENT)
    for setter in setters:
        for fld in setter.flds:
            if (item_fld := getattr(item, fld, None)) is not None:
                fnc = getattr(point, setter.fnc.__name__)
                point = fnc(fld, item_fld)
    return point


def _main():
    checks = [
        'https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList',
        'https://rozetka.com.ua',
    ]
    cookies = copy(constants.DEFAULT_COOKIES)
    cookies['city_id'] = "b205dde2-2e2e-4eb9-aef2-a67c82bbdf27"
    for check in checks:
        try:
            req = tools.get(check, headers=constants.DEFAULT_HEADERS, cookies=cookies)
        except Exception as e:
            msg = f"Rozetka unavailable: {type(e)} {e}"
            LOG.exception(msg, exc_info=True)
            raise Exception(msg)

        if not req.ok:
            msg = f"Rozetka Unavailable: {req.status_code} {req.reason}"
            LOG.error(msg)
            raise Exception(msg)

    healthcheck = asyncio.run(db.health_test())
    if not healthcheck:
        msg = "InfluxDB inaccessible!"
        LOG.error(msg)
        raise Exception(msg)

    start = pendulum.now()
    LOG.verbose = constants.VERBOSE

    all_item_ids, all_categories_len = get_all_item_ids_recursively()
    LOG.green(f"Got {len(all_item_ids)} item ids in {pendulum.now().diff_for_humans(start)}")
    chunked_items_ids = tools.slice_list(all_item_ids, 10000)
    del all_item_ids

    overal_length = 0
    for chunked_item_ids in Bar(f"Dumping {len(chunked_items_ids)} point chunks").iter(chunked_items_ids):
        Item._cache = {}
        SubItem._cache = {}
        Category._cache = {}
        SuperCategory._cache = {}
        all_items = get_all_items_recursively(items_ids=chunked_item_ids, all_categories_len=all_categories_len)
        LOG.green(f"Building points for {len(all_items)} items")
        points = list(map(build_item_point, all_items))
        LOG.green(f"Dumping {len(points)} points")
        # https://docs.influxdata.com/influxdb/v2.4/write-data/best-practices/optimize-writes/
        chunked_points = tools.slice_list(points, 5000)
        for chunked_points_item in Bar(f"Dumping {len(chunked_points)} point chunks").iter(chunked_points):
            asyncio.run(db.dump_points_async(record=chunked_points_item))

        overal_length += len(points)

    LOG.green(f"Points: {overal_length}, Duration: {pendulum.now().diff_for_humans(start)}")
    return overal_length


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
