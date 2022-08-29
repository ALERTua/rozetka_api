#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from typing import List

from aiohttp_retry import ExponentialRetry, RetryClient
from influxdb_client import Point, InfluxDBClient  # https://github.com/influxdata/influxdb-client-python
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from global_logger import Log

log = Log.get_logger()

INFLUXDB_URL = "http://192.168.1.3:8086"
INFLUXDB_TOKEN = '8GgS4AEEEhvph_H5nL3neEhmSHHsglWfgziVGOfQ1MpBBKLcQVv5xxK8xZViKbBdRLYRyG4qFiaynavSmKSOpw=='
INFLUXDB_ORG = "ALERT"
INFLUXDB_BUCKET = 'Rozetka'


async def dump_points(points: List[Point]):
    retry_options = ExponentialRetry(attempts=3)
    async with InfluxDBClientAsync(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG,
                                   client_session_type=RetryClient,
                                   client_session_kwargs={"retry_options": retry_options}) as client:
        ready = await client.ping()
        log.green(f"InfluxDB Ready: {ready}")
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        write_api = client.write_api()
        success = await write_api.write(bucket=INFLUXDB_BUCKET, record=points)
        if not success:
            log.error(f"dump_points failure")
            return

        """
        Query: Stream of FluxRecords
        """
        # log.debug(f"\n------- Query: Stream of FluxRecords -------\n")
        # query_api = client.query_api()
        # records = await query_api.query_stream(f'from(bucket:"{BUCKET}") '
        #                                        '|> range(start: -10m) ')
        #                                        # f'|> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")')
        # async for record in records:
        #     log.debug(record)


def empty_bucket(bucket_name=INFLUXDB_BUCKET):
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, timeout=600_000) as client:
        ready = client.ping()
        # log.green(f"InfluxDB Ready: {ready}")
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        delete_api = client.delete_api()
        start = "1970-01-01T00:00:00Z"
        stop = "2052-07-18T09:00:10.000Z"
        delete_api.delete(start, stop, '', bucket=bucket_name, org=INFLUXDB_ORG)


if __name__ == "__main__":
    # empty_bucket(INFLUXDB_BUCKET)
    # asyncio.run(main1())
    pass
