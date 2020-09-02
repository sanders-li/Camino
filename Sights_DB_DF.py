import pandas as pd
import numpy as np
import os
import psycopg2
import sqlalchemy
import json
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSON, ARRAY

# Pros: Automatic, requires no primary key
# Cons: None

class Sights_DB():
    def __init__(self, access_dict):
        engine_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(access_dict['user'], access_dict['password'], access_dict['host'], access_dict['port'], access_dict['database'])
        self.engine = sqlalchemy.create_engine(engine_URI)
        self.conn = self.engine.connect()
        self.staged_df = pd.DataFrame()
        self.col_dtypes = {
            'place_id': String,
            'name': String,
            'city': String,
            'country': String,
            'address': String,
            'address_components': JSON,
            'location': ARRAY(Numeric), 
            'rating': Numeric,
            'visit_time': String,
            'phone_num_dom': String,
            'phone_num_intl': String,
            'tags': ARRAY(String),
            'category': String,
            'descrip_title': String,
            'descrip_long': String,
            'opening_hours': ARRAY(String)
            }

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.conn.close()
        self.engine.dispose()

    def load_sights(self, city):
        sights = sqlalchemy.Table('sights_df', sqlalchemy.MetaData(), autoload=True, autoload_with=self.engine)
        query = sqlalchemy.select([sights]).where(sights.columns.city == city.lower())
        df = pd.read_sql(query, self.conn)
        return df

    def add(self, df):
        self.staged_df = self.staged_df.append(df)

    def status(self):
        print(self.staged_df)
        col_names = [col for col in self.staged_df]
        d_types = [type(self.staged_df[col][0]) for col in self.staged_df]
        print(list(zip(col_names, d_types)))

    def commit(self):
        self.staged_df.to_sql('sights_df', con=self.conn, schema='public', index=False, if_exists='replace', dtype=self.col_dtypes)


if __name__ == '__main__':
    with open('db_verification.json', 'r') as f:
        sights_access = json.load(f)

    with Sights_DB(sights_access) as sights_db:
        df = pd.read_json('tokyo_japan_sights_df.json')
        sights_db.add(df)
        sights_db.status()

        print('\nWriting to db')
        sights_db.commit()

        print('\nTokyo sights now in db:')
        print(sights_db.load_sights('Tokyo'))
