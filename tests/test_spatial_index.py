from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.spatial.quadtree import Quadtree


def test_grid_insert_and_query():
    grid = SpatialGrid(cell_size=10)
    grid.insert(1, (5, 5))
    assert grid.query_radius((5, 5), 0) == [1]


def test_grid_remove():
    grid = SpatialGrid(10)
    grid.insert(1, (5, 5))
    grid.remove(1)
    assert grid.query_radius((5, 5), 10) == []


def test_grid_query_radius_multiple():
    grid = SpatialGrid(10)
    grid.insert(1, (5, 5))
    grid.insert(2, (15, 5))
    grid.insert(3, (25, 25))
    assert set(grid.query_radius((10, 5), 5)) == {1, 2}


def test_grid_batch_insert():
    grid = SpatialGrid(10)
    grid.insert_many([(1, (0, 0)), (2, (9, 9))])
    assert set(grid.query_radius((5, 5), 10)) == {1, 2}


def test_grid_large_batch():
    grid = SpatialGrid(1)
    batch = [(i, (i % 100, i // 100)) for i in range(5000)]
    grid.insert_many(batch)
    assert len(grid.query_radius((0, 0), 150)) == 5000


def test_quadtree_wrapper():
    qt = Quadtree(10)
    qt.insert(1, (1, 1))
    assert qt.query_radius((1, 1), 1) == [1]
    qt.remove(1)
    assert qt.query_radius((1, 1), 1) == []
