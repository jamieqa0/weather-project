import os
import tempfile
import pandas as pd
import pytest
from data.storage import save_csv, load_csv


def test_save_creates_file():
    df = pd.DataFrame({'a': [1, 2, 3]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test.csv')
        save_csv(df, path)
        assert os.path.exists(path)


def test_roundtrip():
    df = pd.DataFrame({'date': ['2024-01-01', '2024-01-02'], 'temp': [10.5, 12.3]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test.csv')
        save_csv(df, path)
        loaded = load_csv(path)
    pd.testing.assert_frame_equal(df, loaded)


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_csv('/nonexistent/path/test.csv')


def test_save_creates_parent_dirs():
    df = pd.DataFrame({'x': [1]})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'subdir', 'nested', 'test.csv')
        save_csv(df, path)
        assert os.path.exists(path)
