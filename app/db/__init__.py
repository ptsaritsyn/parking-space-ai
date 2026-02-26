import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class _BaseSQLDB:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DB_URL")
        self.engine = self._create_engine(self.db_url)
        self.Session = self._create_session(self.engine)
        self.init_db()

    def _create_engine(self, db_url):
        return create_engine(db_url, future=True)

    def _create_session(self, engine):
        return sessionmaker(engine, expire_on_commit=False)

    def init_db(self, *args, **kwargs):
        try:
            return self._init_db(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in init_db: {e}")
            raise

    def add(self, model, **kwargs):
        try:
            return self._add(model, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in add: {e}")
            raise

    def get(self, model, **kwargs):
        try:
            return self._get(model, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in get: {e}")
            raise

    def update(self, model, filters, updates):
        try:
            return self._update(model, filters, updates)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in update: {e}")
            raise

    def delete(self, model, **kwargs):
        try:
            return self._delete(model, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in delete: {e}")
            raise

    def _init_db(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._init_db()")

    def _add(self, model, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._add()")

    def _get(self, model, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._get()")

    def _update(self, model, filters, updates):
        raise NotImplementedError(f"{self.__class__.__name__}._update")

    def _delete(self, model, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._delete()")


class _BaseVectorDB:
    def add_documents(self, *args, **kwargs):
        try:
            return self._add_documents(*args, **kwargs)
        except Exception as e:
            print(f"Error in add_documents: {e}")
            raise

    def search(self, *args, **kwargs):
        try:
            return self._search(*args, **kwargs)
        except Exception as e:
            print(f"Error in search: {e}")
            raise

    def _add_documents(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._add_documents()")

    def _search(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._search()")
