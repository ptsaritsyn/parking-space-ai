from . import _BaseSQLDB
from .models import Base, Spot


class SQLiteDB(_BaseSQLDB):
    def _init_db(self, *args, **kwargs):
        Base.metadata.create_all(self.engine)

        with self.Session() as session:
            for i in range(1, 51):
                number = f"A{i}"
                spot = session.query(Spot).filter_by(number=number).first()

                if not spot:
                    spot = Spot(number=number, status="free")
                    session.add(spot)

            session.commit()

    def _add(self, model, **kwargs):
        with self.Session() as session:
            obj = model(**kwargs)
            session.add(obj)
            session.commit()
            return obj

    def _get(self, model, **kwargs):
        with self.Session() as session:
            return session.query(model).filter_by(**kwargs).first()

    def _update(self, model, filters: dict, updates: dict):
        with self.Session() as session:
            obj = session.query(model).filter_by(**filters).first()
            if obj:
                for k, v in updates.items():
                    setattr(obj, k, v)
                session.commit()
            return obj

    def _delete(self, model, **kwargs):
        with self.Session() as session:
            return session.query(model).filter_by(**kwargs).first()
