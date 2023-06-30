import asyncio
from copy import copy
import datetime

import pendulum
from aiohttp_retry import ExponentialRetry, RetryClient
from global_logger import Log
# https://github.com/influxdata/influxdb-client-python
from influxdb_client import InfluxDBClient, Bucket, BucketRetentionRules
from influxdb_client.client.flux_table import FluxRecord
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from rozetka.entities.point import Point
from rozetka.tools import constants

log = Log.get_logger()

INFLUXDB_URL = constants.INFLUXDB_URL
INFLUXDB_TOKEN = constants.INFLUXDB_TOKEN
INFLUXDB_ORG = constants.INFLUXDB_ORG
INFLUXDB_BUCKET = constants.INFLUXDB_BUCKET

INFLUX_KWARGS = dict(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, timeout=600_000_000, enable_gzip=True)
INFLUX_KWARGS_ASYNC = copy(INFLUX_KWARGS)
INFLUX_KWARGS_ASYNC.update(dict(client_session_type=RetryClient,
                                client_session_kwargs={"retry_options": ExponentialRetry(attempts=3)}))


def dump_points(record=None, *args, **kwargs):
    if not record:
        return

    with InfluxDBClient(**INFLUX_KWARGS) as client:
        ready = client.ping()
        # log.green(f"InfluxDB Ready: {ready}")
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        write_api = client.write_api()
        success = write_api.write(bucket=INFLUXDB_BUCKET, *args, **kwargs)
        if success is False:
            log.error(f"Error dumping points")
        return success


async def dump_points_async(*args, **kwargs):
    async with InfluxDBClientAsync(**INFLUX_KWARGS_ASYNC) as client:
        ready = await client.ping()
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        write_api = client.write_api()
        success = await write_api.write(bucket=INFLUXDB_BUCKET, *args, **kwargs)
        if not success:
            log.error(f"dump_points_async failure")
            raise Exception('dump_points_async failure')

        # query_api = client.query_api()
        # records = await query_api.query_stream(f'from(bucket:"{INFLUXDB_BUCKET}") '
        #                                        '|> range(start: -5s) ')
        #                                        # f'|> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")')
        # async for record in records:
        #     log.debug(record)

        # log.debug(f"Dumping points success")
        return success


def empty_bucket(bucket_name=INFLUXDB_BUCKET):
    with InfluxDBClient(**INFLUX_KWARGS) as client:
        ready = client.ping()
        # log.green(f"InfluxDB Ready: {ready}")
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        delete_api = client.delete_api()
        start = "1970-01-01T00:00:00Z"
        stop = "2052-07-18T09:00:10.000Z"
        delete_api.delete(start, stop, '', bucket=bucket_name, org=INFLUXDB_ORG)


def recreate_bucket(bucket_name=INFLUXDB_BUCKET):
    with InfluxDBClient(**INFLUX_KWARGS) as client:
        ready = client.ping()
        # log.green(f"InfluxDB Ready: {ready}")
        if not ready:
            log.error(f"InfluxDB NOT READY")
            return

        buckets_api = client.buckets_api()
        bucket: Bucket = buckets_api.find_bucket_by_name(bucket_name=bucket_name)
        if bucket:
            seconds = pendulum.duration(hours=1).in_seconds()
            bucket.retention_rules = [BucketRetentionRules(type="expire", shard_group_duration_seconds=seconds,
                                                           every_seconds=seconds)]
            bucket.name = f"{bucket.name}_old_{pendulum.now().timestamp()}"
            buckets_api.update_bucket(bucket)
        # result_delete = buckets_api.delete_bucket(bucket)
        # bucket = Bucket(name=bucket_name, retention_rules=retention_rules)
        retention_rules = BucketRetentionRules(type="expire", every_seconds=0)
        result_create = buckets_api.create_bucket(bucket_name=bucket_name, retention_rules=retention_rules,
                                                  org=INFLUXDB_ORG)
        pass


async def tst_write():
    points = [Point('goods').tag('id_', '0').field('price', 0)]
    return await dump_points_async(record=points)


async def health_test():
    async with InfluxDBClientAsync(**INFLUX_KWARGS_ASYNC) as client:
        ready = await client.ping()
        return ready


if __name__ == "__main__":
    # asyncio.run(empty_bucket(INFLUXDB_BUCKET))
    # recreate_bucket(INFLUXDB_BUCKET)
    # asyncio.run(tst_write())
    pass
