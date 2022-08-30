import asyncio
import os
import re
from typing import List

from global_logger import Log
from influxdb_client import Point

from rozetka.tools import db
from rozetka.entities.grid import Grid
from rozetka.entities.page import Page

LOG = Log.get_logger()


def url_type(url):
    if re.search(r'.*/p\d+(/)?', url):
        type_ = Page
    elif re.search(r'.*/c\d+(/)?', url):
        type_ = Grid
    else:
        return

    return type_


def parse_grid(grid: Grid) -> List[Point]:
    LOG.green(f"Parsing {grid}")  # todo: paging
    output = []
    for cell in grid.parsed_cells:
        point = Point(cell.id_) \
            .tag('title', cell.title) \
            .tag('url', cell.url) \
            .field('price', cell.price) \
            .field('price', cell.price_old)
        if cell.price_old:
            point = point.field('price_old', cell.price_old)
        if cell.reviews:
            point = point.field('reviews', cell.reviews)
        if cell.rating:
            point = point.field('rating', cell.rating)
        if cell.promo:
            point = point.field('promo', cell.promo)
        output.append(point)
    return output


def parse_page(page: Page) -> Point:
    LOG.green(f"Parsing {page}")
    # Point(MEASUREMENT).tag("id", "id1").field("price", 24.3).field("old_price", 25.2)
    output = Point(page.id_) \
        .tag('title', page.title) \
        .tag('url', page.url) \
        .field('price', page.price) \
        .field('available', page.available)
    if page.price_old:
        output = output.field('price_old', page.price_old)
    if page.reviews:
        output = output.field('reviews', page.reviews)
    return output


def main():
    LOG.verbose = os.getenv('VERBOSE') == 'True'

    LOG.green(f"Parsing {len(URLS)} URLs")
    points: List[Point] = []
    for url in URLS:
        type_ = url_type(url)
        if type_ == Grid:
            grid: Grid = type_.get(url)
            points.extend(parse_grid(grid=grid))
        elif type_ == Page:
            page: Page = type_.get(url)
            points.append(parse_page(page=page))
        else:
            LOG.error(f"Skipping unknown URL type: {url}")
            continue

    LOG.green(f"Dumping {len(points)} data points")
    asyncio.run(db.dump_points(points))
    pass


if __name__ == '__main__':
    main()
