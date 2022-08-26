Rozetka.ua Python API
---------------------

Usage
^^^^^

.. code:: py

    from rozetka.entities.grid import Grid
    grid = Grid.get('(your filter url)')
    print(f"Parsed {len(grid.parsed_cells)} cells")
    print(f"Cheapest one: {grid.cheapest_cell}")
