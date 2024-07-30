import re
from itertools import zip_longest

from curl_cffi import requests
from global_logger import Log
from ratelimit import limits, sleep_and_retry, RateLimitException
from requests import Response
# noinspection PyPackageRequirements
from worker import worker, ThreadWorkerManager

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


# @sleep_and_retry
# @limits(calls=constants.CALLS_MAX, period=constants.CALLS_PERIOD, raise_on_limit=True)
# def _get(*args, retry=False, max_tries=constants.GET_RETRIES, delay=constants.GET_DELAY, **kwargs) -> Response:
#     try:
#         response = requests.get(*args, timeout=constants.GET_TIMEOUT, **kwargs)
#     except Exception as e:
#         response = None
#
#     if retry:
#         i = 0
#         while response is None or not response.ok and response.status_code in (502, 524, ) and (i := i + 1) < max_tries:
#             if response:
#                 LOG.error(f"ERROR Requesting {response.request.url} {kwargs.get('params', '')}: {response.status_code}."
#                           f" Retrying in {delay}")
#             else:
#                 LOG.error(f"ERROR Requesting {args} {kwargs.get('params', '')}. Retrying in {delay}")
#
#             time.sleep(delay)
#             try:
#                 response = requests.get(*args, timeout=constants.GET_TIMEOUT, **kwargs)
#             except Exception as e:
#                 response = None
#                 pass
#
#         if i >= max_tries:
#             LOG.error(f"Max tries reached requesting {args}.")
#     return response


@sleep_and_retry
@limits(calls=constants.CALLS_MAX, period=constants.CALLS_PERIOD, raise_on_limit=True)
def get(*args, **kwargs) -> Response:
    allowed_codes = kwargs.pop('allowed_codes', [])
    sleep_time = constants.GET_RETRY_DELAY_SEC
    try:
        response = requests.get(*args, timeout=constants.GET_TIMEOUT, impersonate=constants.IMPERSONATE, **kwargs)
    except Exception as e:
        msg = f"Exception while Requesting {args}: {type(e)} {e}. Retrying"
        LOG.error(msg)
        raise RateLimitException(msg, sleep_time)

    if response is None:
        msg = f"Empty response for {args}. Retrying"
        LOG.debug(msg)
        raise RateLimitException(msg, sleep_time)

    if (status := response.status_code) in (500, 502, 503, 504, 508, 521, 522, 524, *allowed_codes):
        msg = f"Request status {status} for {args}. Retrying"
        LOG.error(msg)
        raise RateLimitException(msg, sleep_time)

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
        while ((active_workers := ThreadWorkerManager.list(active_only=True))
               and ((workers_len := len(active_workers)) > constants.THREADS_MAX)):
            LOG.info(f"{workers_len} active workers. Waiting...")
            ThreadWorkerManager.wait(wait_all=True)

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
