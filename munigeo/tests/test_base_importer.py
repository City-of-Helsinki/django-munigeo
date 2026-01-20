from munigeo.importer.base import Importer
import pytest


@pytest.fixture
def importer():
    return Importer(options={})


class TestDataPaths:
    @pytest.mark.parametrize("project_root", ["project_root", ""])
    @pytest.mark.parametrize("base_dir", ["base_dir", ""])
    def test_import_data_path_is_always_included_if_set(
        self, importer, settings, project_root, base_dir
    ):
        if project_root:
            settings.PROJECT_ROOT = project_root
        settings.BASE_DIR = base_dir
        settings.IMPORT_DATA_PATH = "import_data_path"

        assert "import_data_path" in importer.data_paths

    @pytest.mark.parametrize("project_root", ["project_root", ""])
    @pytest.mark.parametrize("base_dir", ["base_dir", ""])
    @pytest.mark.parametrize("import_data_path", ["import_data_path", ""])
    def test_app_path_is_always_included(
        self, importer, settings, project_root, base_dir, import_data_path
    ):
        if project_root:
            settings.PROJECT_ROOT = project_root
        settings.BASE_DIR = base_dir
        settings.IMPORT_DATA_PATH = import_data_path

        assert any("/munigeo/data" in data_path for data_path in importer.data_paths)

    @pytest.mark.parametrize("base_dir", ["base_dir", ""])
    def test_project_root_prioritized_over_base_dir(self, importer, settings, base_dir):
        settings.PROJECT_ROOT = "project_root"
        settings.BASE_DIR = base_dir

        assert "project_root/data" in importer.data_paths
        assert f"{base_dir}/data" not in importer.data_paths

    def test_include_base_dir_if_no_project_root(self, importer, settings):
        # PROJECT_ROOT needs to literally not exist in this case.
        del settings.PROJECT_ROOT
        settings.BASE_DIR = "base_dir"

        assert "base_dir/data" in importer.data_paths

    def test_import_data_path_returns_import_data_path_if_set(self, importer, settings):
        settings.IMPORT_DATA_PATH = "import_data_path"

        assert importer.import_data_path == "import_data_path"

    def test_import_data_path_returns_first_data_path_by_default(
        self, importer, settings
    ):
        settings.PROJECT_ROOT = "project_root"

        assert importer.import_data_path == "project_root/data"
