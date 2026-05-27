import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def get_latest_munigeo_migration(executor):
    """Resolve the latest munigeo migration from the graph."""
    leaves = [k for k in executor.loader.graph.leaf_nodes() if k[0] == "munigeo"]
    assert len(leaves) == 1, f"Expected 1 munigeo leaf, got {leaves}"
    return leaves[0]


@pytest.fixture()
def migration_executor():
    """Yield (executor, latest_migration) and restore schema on teardown."""
    executor = MigrationExecutor(connection)
    latest = get_latest_munigeo_migration(executor)
    yield executor, latest
    executor.loader.build_graph()
    executor.migrate([latest])
