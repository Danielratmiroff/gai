import os
import pytest
import yaml
from unittest.mock import patch
from pathlib import Path
from gai_tool.src.myconfig import ConfigManager, DEFAULT_CONFIG
from gai_tool.src.myconfig import CONFIG_FOLDER, CONFIG_FILE, RULES_FILE


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary directory to simulate a project root and chdir into it."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


@pytest.fixture
def config_manager(temp_project_dir):
    """Fixture to provide a ConfigManager instance within a temporary project directory."""
    return ConfigManager(app_name="gai-tool")


@pytest.fixture
def setup_gai_folder(temp_project_dir):
    """Fixture to set up the .gai folder for tests that need it to exist beforehand."""
    gai_dir = temp_project_dir / CONFIG_FOLDER
    gai_dir.mkdir()
    return gai_dir

# -------------------------- Init Command Tests --------------------------


def test_init_creates_folder_and_files(config_manager):
    # Arrange
    gai_dir = Path.cwd() / CONFIG_FOLDER
    rules_file = gai_dir / RULES_FILE
    config_file = gai_dir / CONFIG_FILE

    # Act
    config_manager.init_local_config()

    # Assert
    assert gai_dir.is_dir()
    assert rules_file.is_file()
    assert config_file.is_file()
    with config_file.open('r') as f:
        content = yaml.safe_load(f)
    assert content['interface'] == DEFAULT_CONFIG['interface']


def test_init_does_not_overwrite_existing_rules_file(config_manager, setup_gai_folder):
    # Arrange
    rules_file = setup_gai_folder / RULES_FILE
    custom_content = "custom rule"
    rules_file.write_text(custom_content)

    # Act
    config_manager.init_local_config()

    # Assert
    assert rules_file.read_text() == custom_content


def test_init_does_not_overwrite_existing_config_file(config_manager, setup_gai_folder):
    # Arrange
    config_file = setup_gai_folder / CONFIG_FILE
    custom_config = {'interface': 'test-custom'}
    with config_file.open('w') as f:
        yaml.dump(custom_config, f)

    # Act
    config_manager.init_local_config()

    # Assert
    with config_file.open('r') as f:
        content = yaml.safe_load(f)
    assert content == custom_config

# -------------------------- Config Loading Tests (No Merge) --------------------------


def test_load_default_config(temp_project_dir):
    # Arrange: No project or home config files.
    home_dir = temp_project_dir / "home"
    home_dir.mkdir()

    with patch('pathlib.Path.home', return_value=home_dir):
        # Act
        cm = ConfigManager(app_name="gai-tool")

        # Assert
        assert cm.config == DEFAULT_CONFIG
        assert cm.get_config('interface') == DEFAULT_CONFIG['interface']


def test_load_home_config_overrides_default(temp_project_dir):
    # Arrange: Home config exists, project config does not.
    home_dir = temp_project_dir / "home"
    home_dir.mkdir()
    gai_home_dir = home_dir / CONFIG_FOLDER
    gai_home_dir.mkdir()
    home_config_file = gai_home_dir / CONFIG_FILE
    home_config_data = {'interface': 'home-only', 'temperature': 0.1}
    with home_config_file.open('w') as f:
        yaml.dump(home_config_data, f)

    with patch('pathlib.Path.home', return_value=home_dir):
        # Act
        cm = ConfigManager(app_name="gai-tool")

        # Assert: Config should be exactly home_config_data, not a merge
        assert cm.config == home_config_data
        assert cm.get_config('interface') == 'home-only'
        assert cm.get_config('temperature') == 0.1
        # Assert that a key from default config is NOT present
        assert 'target_branch' not in cm.config


def test_load_project_config_overrides_home_and_default(temp_project_dir):
    # Arrange: Project and Home configs exist.
    # 1. Setup home config
    home_dir = temp_project_dir / "home"
    home_dir.mkdir()
    gai_home_dir = home_dir / CONFIG_FOLDER
    gai_home_dir.mkdir()
    home_config_file = gai_home_dir / CONFIG_FILE
    home_config_data = {'interface': 'home-test', 'temperature': 0.2}
    with home_config_file.open('w') as f:
        yaml.dump(home_config_data, f)

    # 2. Setup project config
    gai_project_dir = temp_project_dir / CONFIG_FOLDER
    gai_project_dir.mkdir()
    project_config_file = gai_project_dir / CONFIG_FILE
    project_config_data = {'interface': 'project-only', 'max_tokens': 100}
    with project_config_file.open('w') as f:
        yaml.dump(project_config_data, f)

    with patch('pathlib.Path.home', return_value=home_dir):
        # Act
        cm = ConfigManager(app_name="gai-tool")

        # Assert: Config should be exactly project_config_data
        assert cm.config == project_config_data
        assert cm.get_config('interface') == 'project-only'
        assert cm.get_config('max_tokens') == 100
        # Assert that keys from home and default are NOT present
        assert 'temperature' not in cm.config
        assert 'target_branch' not in cm.config


def test_load_empty_config_files(temp_project_dir):
    # Arrange: Project and Home config files exist but are empty.
    # 1. Setup empty home config
    home_dir = temp_project_dir / "home"
    home_dir.mkdir()
    gai_home_dir = home_dir / CONFIG_FOLDER
    gai_home_dir.mkdir()
    home_config_file = gai_home_dir / CONFIG_FILE
    home_config_file.touch()

    # 2. Setup empty project config
    gai_project_dir = temp_project_dir / CONFIG_FOLDER
    gai_project_dir.mkdir()
    project_config_file = gai_project_dir / CONFIG_FILE
    project_config_file.touch()

    with patch('pathlib.Path.home', return_value=home_dir):
        # Act
        cm = ConfigManager(app_name="gai-tool")

        # Assert: Should fall back to default config
        assert cm.config == DEFAULT_CONFIG
