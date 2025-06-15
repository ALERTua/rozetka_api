import re
import time
from itertools import zip_longest
from typing import Any, Literal

from curl_cffi import requests
from curl_cffi.requests import Response
from global_logger import Log
from ratelimit import limits, sleep_and_retry, RateLimitException

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
        return ""

    tails = [
        " - ROZETKA",
        " – в інтернет-магазині ROZETKA",
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


def byparr_get(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    data: Any = None,
    json_body: Any = None,
    timeout: int = constants.GET_TIMEOUT,
) -> requests.Response:
    payload = {
        "url": url,
        "method": method,
        "headers": headers or {},
        "params": params or {},
        "data": data,
        "json": json_body,
    }
    resp = requests.post(constants.BYPARR_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp


@sleep_and_retry
@limits(calls=constants.CALLS_MAX, period=constants.CALLS_PERIOD, raise_on_limit=True)
def get(
    *args: Any,
    method: Literal[
        "GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "TRACE", "PATCH", "QUERY"
    ] = "GET",
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    data: Any = None,
    json_body: Any = None,
    allowed_codes=None,
    **kwargs: Any,
) -> Response:
    if allowed_codes is None:
        allowed_codes = []
    sleep_time = constants.GET_RETRY_DELAY_SEC

    try:
        if constants.BYPARR_URL:
            response = byparr_get(
                url=args[0],
                method=method,
                headers=headers,
                params=params,
                data=data,
                json_body=json_body,
                timeout=constants.GET_TIMEOUT,
            )
        else:
            response = requests.request(
                method,
                *args,
                headers=headers,
                params=params,
                data=data,
                json=json_body,
                timeout=constants.GET_TIMEOUT,
                impersonate=constants.IMPERSONATE,
                **kwargs,
            )
    except Exception as e:
        msg = f"Exception while requesting {args}: {type(e)} {e}. Retrying"
        LOG.error(msg)
        raise RateLimitException(msg, sleep_time)

    if response is None:
        msg = f"Empty response for {args}. Retrying"
        LOG.debug(msg)
        raise RateLimitException(msg, sleep_time)

    status = response.status_code
    if status in (500, 502, 503, 504, 508, 521, 522, 524, 203, *allowed_codes):
        msg = f"Request status {status} for {args}. Retrying"
        LOG.error(msg)
        raise RateLimitException(msg, sleep_time)

    return response


def fnc_map(fnc, *tuple_of_args, **kwargs):
    threads_limit = constants.THREADS_MAX
    outputs = []
    workers = []

    @worker
    def _worker(*worker_args, **worker_kwargs):
        return fnc(*worker_args, **worker_kwargs)

    for tuple_ in tuple_of_args:
        if (workers_len := len(workers)) >= threads_limit:
            LOG.debug(f"Workers: {workers_len}. Waiting")
            for worker_ in workers:
                outputs.append(worker_.await_worker())
                workers.remove(worker_)
            LOG.debug("Done waiting")

        try:
            __worker = _worker(*tuple_, **kwargs)
        except Exception as e:
            if "thread failed to start" in str(e):
                threads_len = len(ThreadWorkerManager.allWorkers.keys())
                LOG.exception(f"Threads Limit Reached {threads_len}", exc_info=True)
                LOG.debug(f"Waiting for {len(workers)} workers to finish")
                for worker_ in workers:
                    outputs.append(worker_.await_worker())
                    workers.remove(worker_)
                LOG.debug("Done waiting")

                __worker = _worker(*tuple_, **kwargs)
            else:
                raise e

        workers.append(__worker)

    for worker_ in workers:
        outputs.append(worker_.await_worker())
        workers.remove(worker_)
    return outputs


def fncs_map(tuple_of_fncs, *tuple_of_args):
    workers = []
    outputs = []
    threads_limit = constants.THREADS_MAX
    for fnc, fnc_args in zip_longest(tuple_of_fncs, tuple_of_args):
        if (workers_len := len(workers)) >= threads_limit:
            LOG.debug(f"Workers: {workers_len}. Waiting")
            for worker_ in workers:
                outputs.append(worker_.await_worker())
                workers.remove(worker_)
            LOG.debug("Done waiting")

        @worker
        def _worker(*worker_args):
            return fnc(*worker_args)

        fnc_args = fnc_args or []
        try:
            __worker = _worker(*fnc_args)
        except RuntimeError as e:
            if "thread failed to start" in str(e) or "can't start new thread" in str(e):
                threads_len = len(ThreadWorkerManager.allWorkers.keys())
                LOG.exception(f"Threads Limit Reached {threads_len}", exc_info=True)
                LOG.debug(f"Waiting for {len(workers)} workers to finish")
                for worker_ in workers:
                    outputs.append(worker_.await_worker())
                    workers.remove(worker_)
                LOG.debug("Done waiting")

                __worker = _worker(*fnc_args)
            else:
                raise e

        workers.append(__worker)

    for worker_ in workers:
        outputs.append(worker_.await_worker())
        workers.remove(worker_)
    return outputs


def wait_workers_limit(limit=None):
    limit = limit or constants.THREADS_MAX
    while len(ThreadWorkerManager.allWorkers.keys()) > limit:
        time.sleep(0.1)


def slice_list(list_, chunk_size):
    return [list_[i : i + chunk_size] for i in range(0, len(list_), chunk_size)]
