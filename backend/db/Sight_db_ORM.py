import sqlalchemy
from sqlalchemy import Table, MetaData, Column, String, Integer
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON, ARRAY
import json
from Place import Sight

# Not used

# Pros: None
# Cons: Primary key required (no duplicate place_id allowed)

Base = declarative_base()
class Sights_ORM(Base):
    __tablename__ = 'sights_orm'
    
    place_id = Column(String, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    address = Column(String)
    address_components = Column(JSON)
    location = Column(String)
    rating = Column(Integer)
    visit_time = Column(String)
    phone_num_dom = Column(String)
    phone_num_intl = Column(String)
    tags = Column(ARRAY(String))
    category = Column(String)
    descrip_title = Column(String)
    descrip_long = Column(String)
    opening_hours = Column(JSON)


class Sights_db_ORM():
    def __init__(self, access_dict):
        engine_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(access_dict['user'], access_dict['password'], access_dict['host'], access_dict['port'], access_dict['database'])
        self.engine = sqlalchemy.create_engine(engine_URI)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.session.close()
        self.engine.dispose()
        print('Closed db')

    def load_sights(self, city):
        sights = sqlalchemy.Table('sights', sqlalchemy.MetaData(), autoload=True, autoload_with=self.engine)
        query = sqlalchemy.select([sights]).where(sights.columns.city == city)

    def add(self, sights_list):
        for sight in sights_list:
            self.session.merge(Sights_ORM(**sight))

    def commit(self):
        self.session.commit()

    def create_table(self):
        try:
            Sights_ORM().__table__.create(bind = engine)
        except:
            Sights_ORM().__table__.drop(bind=engine)
            Sights_ORM().__table__.create(bind = engine)


if __name__ == '__main__':
    with open('db_verification.json', 'r') as f:
        sights_access = json.load(f)

    with Sights_db_ORM(sights_access) as sights_db:
        with open('tokyo_japan_sights_dict.json', 'r') as f:
            sights_list = json.load(f)
        sights_db.add(sights_list)
        sights_db.commit()
