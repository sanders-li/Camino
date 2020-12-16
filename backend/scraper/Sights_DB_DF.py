import pandas as pd
import numpy as np
import os
import psycopg2
import sqlalchemy
import json
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSON, ARRAY, BYTEA


#Separate frontend data from routerfinder data? Aka (photo/rating/category/descrips/tags/phone/opening_hours_text, )
class Sights_DB():
    def __init__(self, access_dict):
        engine_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(access_dict['user'], access_dict['password'], access_dict['host'], access_dict['port'], access_dict['database'])
        self.engine = sqlalchemy.create_engine(engine_URI)
        self.conn = self.engine.connect()
        self.staged_dfs = {}
        # Should certain groups be unpacked? e.g. photo => photo_url + photo_attributions?
        # Is this a performance gain or loss?
        self.dtypes = {
            'sights': {
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
                'photo': JSON,
                'tags': ARRAY(String),
                'category': String,
                'summary': String,
                'description': JSON,
                'opening_hours': JSON,
                'opening_hours_text': ARRAY(String),
            },
            # cities photo is not packed for performance increase?
            'cities': {
                'city': String,
                'country': String,
                'location': ARRAY(Numeric),
                'bounds': ARRAY(Numeric),
                'photo_url': String,
                'photo_attributions': ARRAY(String)
            }
        }

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.conn.close()
        self.engine.dispose()

    def load(self, db_name, city):
        try:
            table = sqlalchemy.Table(db_name, sqlalchemy.MetaData(), autoload=True, autoload_with=self.engine)
        except sqlalchemy.NoSuchTableError:
            raise ValueError('Empty DataFrame')
        query = sqlalchemy.select([table]).where(table.columns.city == city.lower())
        df = pd.read_sql(query, self.conn)
        if not df.empty:
            return df
        else:
            raise ValueError('Empty DataFrame')
    
    def add(self, db_name, df):
        if db_name in self.staged_dfs:
            self.staged_dfs[db_name] = self.staged_df[db_name].append(df)
        else:
            self.staged_dfs[db_name] = df

    def status(self):
        print(self.staged_df)
        col_names = [col for col in self.staged_df]
        d_types = [type(self.staged_df[col][0]) for col in self.staged_df]
        print(list(zip(col_names, d_types)))

    def commit(self, db_name):
        self.staged_dfs[db_name].to_sql(db_name, con=self.conn, schema='public', index=False, if_exists='append', dtype=self.dtypes[db_name])


if __name__ == '__main__':
    with open('backend/scraper/db_access.json', 'r') as f:
        sights_access = json.load(f)

    with Sights_DB(sights_access) as sights_db:
        df = sights_db.load('sights', 'tokyo')
        print(df.head())
        df = sights_db.load('cities', 'kyoto')
        print(df.head())
