import sqlalchemy
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    user_tg_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    week = sqlalchemy.Column(sqlalchemy.Integer)


class Ingestion(SqlAlchemyBase):
    __tablename__ = 'ingestions'
    ingestion_id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_tg_id = sqlalchemy.Column(sqlalchemy.Integer)
    food_name = sqlalchemy.Column(sqlalchemy.String)
    picture = sqlalchemy.Column(sqlalchemy.String)
    type_eat = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(sqlalchemy.String)
