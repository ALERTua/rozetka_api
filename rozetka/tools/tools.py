import re
import time
from itertools import zip_longest

import requests
from global_logger import Log
from ratelimit import limits, sleep_and_retry
from requests import Response
# noinspection PyPackageRequirements
from worker import worker

from rozetka.tools import constants

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

    tails = [
        ' - ROZETKA',
        ' – в інтернет-магазині ROZETKA',
    ]
    output = title
    for tail in tails:
        split = re.split(tail, output)
        # noinspection PyUnresolvedReferences
        output = split[0].strip()
    return output


def ints_from_str(str_):
    blocks = str_.split()
    output = []
    for block in blocks:
        # noinspection PyBroadException
        try:
            output.append(int(block))
        except:  # noqa: E722
            pass

    return output


def floats_from_str(str_):
    blocks = str_.split()
    floats = []
    for block in blocks:
        # noinspection PyBroadException
        try:
            floats.append(float(block))
        except:  # noqa: E722
            pass

    return floats


def str_to_price(price_str):
    if not price_str:
        return

    price_str = price_str.replace("₴", "")
    price_str = price_str.split()
    price_str = "".join(price_str)
    return int(price_str)


def parse_rating(rating_str):
    if not rating_str:
        return

    floats = floats_from_str(rating_str)
    if len(floats) == 2:
        rating_value, rating_max = floats
        return rating_value / rating_max


def parse_reviews(reviews_str):
    if not reviews_str:
        return

    floats = floats_from_str(reviews_str)
    if floats:
        return int(floats[0])


@sleep_and_retry
@limits(calls=constants.CALLS_MAX, period=constants.CALLS_PERIOD)
def get(*args, retry=False, max_tries=3, delay=30, **kwargs) -> Response:
    response = requests.get(*args, timeout=60, **kwargs)
    if retry:
        i = 0
        while not response.ok and response.status_code in (502, ) and (i := i + 1) < max_tries:
            LOG.error(f"ERROR Requesting {response.request.url} : {response.status_code}. Retrying in {delay}")
            time.sleep(delay)
            response = requests.get(*args, **kwargs)
    return response


def fnc_map(fnc, *tuple_of_args, **kwargs):
    @worker
    def _worker(*worker_args, **worker_kwargs):
        return fnc(*worker_args, **worker_kwargs)

    workers = []
    for tuple_ in tuple_of_args:
        workers.append(_worker(*tuple_, **kwargs))

    outputs = []
    for worker_ in workers:
        worker_.wait()
        outputs.append(worker_.ret)
    return outputs


def fncs_map(tuple_of_fncs, *tuple_of_args):
    workers = []
    for fnc, fnc_args in zip_longest(tuple_of_fncs, tuple_of_args):
        @worker
        def _worker(*worker_args):
            return fnc(*worker_args)

        fnc_args = fnc_args or []
        workers.append(_worker(*fnc_args))

    outputs = []
    for worker_ in workers:
        worker_.wait()
        outputs.append(worker_.ret)
    return outputs


def slice_list(list_, chunk_size):
    return [list_[i:i + chunk_size] for i in range(0, len(list_), chunk_size)]

