import pytest
from unittest.mock import MagicMock, patch
from app.db.sqlite_db import _BaseSQLDB, SQLiteDB


class DummyModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# --- Tests for _BaseSQLDB ---

class DummySQLDB(_BaseSQLDB):
    def _init_db(self, *args, **kwargs):
        pass
    def _add(self, model, **kwargs):
        return "added"
    def _get(self, model, **kwargs):
        return "got"
    def _update(self, model, filters, updates):
        return "updated"
    def _delete(self, model, **kwargs):
        return "deleted"


def test_basesqldb_add_success():
    db = DummySQLDB(db_url="sqlite:///:memory:")
    assert db.add(DummyModel) == "added"


def test_basesqldb_get_success():
    db = DummySQLDB(db_url="sqlite:///:memory:")
    assert db.get(DummyModel) == "got"


def test_basesqldb_update_success():
    db = DummySQLDB(db_url="sqlite:///:memory:")
    assert db.update(DummyModel, {}, {}) == "updated"


def test_basesqldb_delete_success():
    db = DummySQLDB(db_url="sqlite:///:memory:")
    assert db.delete(DummyModel) == "deleted"


def test_basesqldb_not_implemented_methods():
    class NotImpl(_BaseSQLDB):
        def _init_db(self, *a, **k): pass
    db = NotImpl(db_url="sqlite:///:memory:")
    with pytest.raises(NotImplementedError):
        _BaseSQLDB._add(db, DummyModel)
    with pytest.raises(NotImplementedError):
        _BaseSQLDB._get(db, DummyModel)
    with pytest.raises(NotImplementedError):
        _BaseSQLDB._update(db, DummyModel, {}, {})
    with pytest.raises(NotImplementedError):
        _BaseSQLDB._delete(db, DummyModel)


def test_basesqldb_exception_prints_and_raises(capfd):
    class ErrorSQLDB(_BaseSQLDB):
        def _init_db(self, *a, **k): pass
        def _add(self, model, **kwargs):
            raise ValueError("fail")
    db = ErrorSQLDB(db_url="sqlite:///:memory:")
    with pytest.raises(ValueError):
        db.add(DummyModel)
    out, _ = capfd.readouterr()
    assert "Error in add" in out

# --- Tests for SQLiteDB ---

class MockSession:
    def __init__(self):
        self.add = MagicMock()
        self.commit = MagicMock()
        self.query = MagicMock()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def mock_session():
    return MockSession()


@pytest.fixture
def db_with_mock_session(mock_session):
    with patch("app.db.sessionmaker", return_value=lambda: mock_session):
        with patch.object(SQLiteDB, "_create_engine", return_value=MagicMock()):
            db = SQLiteDB(db_url="sqlite:///:memory:")
            yield db, mock_session


def test_sqlitedb_add_returns_obj(db_with_mock_session):
    db, session = db_with_mock_session
    session.add.reset_mock()
    session.commit.reset_mock()
    obj = db.add(DummyModel, foo="bar")
    session.add.assert_called_once()
    session.commit.assert_called_once()

    assert isinstance(obj, DummyModel)
    assert obj.foo == "bar"


def test_sqlitedb_get_returns_obj(db_with_mock_session):
    db, session = db_with_mock_session
    expected = DummyModel(foo="bar")
    session.query.return_value.filter_by.return_value.first.return_value = expected
    session.query.reset_mock()
    session.query.return_value.filter_by.reset_mock()
    session.query.return_value.filter_by.return_value.first.reset_mock()
    result = db.get(DummyModel, foo="bar")
    session.query.assert_called_once_with(DummyModel)
    session.query.return_value.filter_by.assert_called_once_with(foo="bar")
    session.query.return_value.filter_by.return_value.first.assert_called_once()
    assert result == expected


def test_sqlitedb_update_sets_attrs_and_commits(db_with_mock_session):
    db, session = db_with_mock_session
    obj = DummyModel(foo="bar")
    session.query.return_value.filter_by.return_value.first.return_value = obj
    session.query.reset_mock()
    session.commit.reset_mock()
    session.query.return_value.filter_by.reset_mock()
    session.query.return_value.filter_by.return_value.first.reset_mock()
    result = db.update(DummyModel, {"foo": "bar"}, {"baz": 42})
    assert result == obj
    assert obj.baz == 42
    session.commit.assert_called_once()
    session.query.assert_called_once_with(DummyModel)
    session.query.return_value.filter_by.assert_called_once_with(foo="bar")
    session.query.return_value.filter_by.return_value.first.assert_called_once()


def test_sqlitedb_delete_returns_obj(db_with_mock_session):
    db, session = db_with_mock_session
    expected = DummyModel(foo="bar")
    session.query.return_value.filter_by.return_value.first.return_value = expected
    session.query.reset_mock()
    session.query.return_value.filter_by.reset_mock()
    session.query.return_value.filter_by.return_value.first.reset_mock()
    result = db.delete(DummyModel, foo="bar")
    session.query.assert_called_once_with(DummyModel)
    session.query.return_value.filter_by.assert_called_once_with(foo="bar")
    session.query.return_value.filter_by.return_value.first.assert_called_once()
    assert result == expected


def test_sqlitedb_init_db_creates_spots(db_with_mock_session):
    db, session = db_with_mock_session
    with patch("app.db.models.Base.metadata.create_all") as mock_create_all:
        db._init_db()
        mock_create_all.assert_called_once_with(db.engine)
        session.commit.assert_called()
