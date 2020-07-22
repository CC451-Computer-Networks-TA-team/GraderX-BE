from . import manager
import pytest
import random
import string
from pathlib import Path
import patoolib
import os
import werkzeug.datastructures
from unittest.mock import Mock, patch


def generate_random_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(12))


def test_extraction_cleans_directory_if_exists(monkeypatch):
    monkeypatch.setattr(manager, 'extract_file', lambda x: None)
    manager.clean_directory = Mock()

    # passing Mock that returns True when called with exists() method
    manager.extract_submissions(Mock(**{'exists.return_value': True}), Mock())

    manager.clean_directory.assert_called_once()


def test_extraction_creates_dir_if_not_exist(monkeypatch):
    monkeypatch.setattr(manager, 'extract_file', lambda x: None)
    monkeypatch.setattr(manager, 'clean_directory', lambda x: None)
    path_mock = Mock(**{'exists.return_value': False})

    # passing Mock that returns False when called with exists() method
    manager.extract_submissions(path_mock, Mock())

    path_mock.mkdir.assert_called_once_with(parents=True)


def test_extraction_return_if_extract_file_succeeds(monkeypatch):
    monkeypatch.setattr(manager, 'extract_file', lambda x: None)
    monkeypatch.setattr(manager, 'clean_directory', lambda x: None)

    try:
        manager.extract_submissions(Mock(), Mock())
    except Exception as e:
        pytest.fail(
            "manager.extract_submissions raised an unexpected exception\n" + str(e))


def test_extraction_return_if_extract_file_fails(monkeypatch):
    def mock_extract_file(filepath):
        raise FileNotFoundError
    monkeypatch.setattr(manager, 'extract_file', mock_extract_file)
    monkeypatch.setattr(manager, 'clean_directory', lambda x: None)

    with pytest.raises(manager.ArchiveDamagedError):
        manager.extract_submissions(Mock(), Mock())
