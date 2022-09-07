import asyncio

import pendulum
import requests
from global_logger import Log
from knockknock import telegram_sender, discord_sender, slack_sender, teams_sender

from rozetka.entities.item import Item
from rozetka.entities.point import Point
from rozetka.entities.supercategory import SuperCategory
from rozetka.tools import db, constants, tools

LOG = Log.get_logger()

setters = (
    constants.Setter(fnc=Point.tag, flds=constants.TAGS),
    constants.Setter(fnc=Point.field, flds=constants.FIELDS),
)


def build_item_point(item: Item):
    # item.parse()
    point = Point(item.id_)
    for setter in setters:
        for fld in setter.flds:
            if (item_fld := getattr(item, fld, None)) is not None:
                fnc = getattr(point, setter.fnc.__name__)
                point = fnc(fld, item_fld)
    return point


def _main():
    try:
        requests.get('https://xl-catalog-api.rozetka.com.ua/v4/super-portals/getList')
    except Exception as e:
        LOG.exception("Rozetka unavailable", exc_info=e)
        raise Exception('healthcheck failure')

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

    all_items = SuperCategory.get_all_items_recursively()

    LOG.green(f"Building points for {len(all_items)} items")
    points = list(map(build_item_point, all_items))

    LOG.green(f"Dumping {len(points)} points")
    chunked_points = tools.slice_list(points, 1000)
    for chunked_points_item in chunked_points:
        asyncio.run(db.dump_points_async(record=chunked_points_item))

    duration = pendulum.now().diff_for_humans(start)
    LOG.green(f"Duration: {duration}")
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
