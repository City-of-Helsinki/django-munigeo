import pytest

from munigeo.importer.sync import ModelSyncher
from munigeo.models import Municipality


@pytest.fixture
def municipalities():
    return [Municipality(id=str(x), name_fi=str(x)) for x in range(10)]


@pytest.fixture
def syncher(municipalities):
    syncher = ModelSyncher(municipalities, lambda x: x.id)
    for i, m in enumerate(syncher.obj_dict.values()):
        if i % 3 == 0:
            m._found = True
        else:
            m._found = False
    return syncher


def test_syncher_deleted_objects(syncher):
    deleted_objects = syncher.get_deleted_objects()
    assert len(deleted_objects) < len(syncher.obj_dict.values())
    for o in syncher.obj_dict.values():
        assert hasattr(o, "_found")
        if o._found is True:
            assert o not in deleted_objects
        else:
            assert o in deleted_objects
