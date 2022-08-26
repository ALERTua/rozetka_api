from global_logger import Log

from rozetka.entities.grid import Grid

LOG = Log.get_logger()


def main():
    LOG.verbose = True
    grid = Grid.get('https://rozetka.com.ua/ua/notebooks/c80004/page=2/')
    print(f"Parsed {len(grid.parsed_cells)} cells")
    print(f"Cheapest one: {grid.cheapest_cell}")
    pass


if __name__ == '__main__':
    main()
