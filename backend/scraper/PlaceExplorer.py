import pandas as pd
import numpy as np
import os
import json
import time
from collections import defaultdict, namedtuple

from Place import Sight
from PlaceFinder import GooglePlacesFinder
from PlaceDetailer import GoogleSightsDetailer, GoogleEatsDetailer, GoogleHotelDetailer
from WebRequestHandler import GoogleApiHandler
from Sights_DB_DF import Sights_DB


# TODO: Implement FourSquareAPI handling

#scrape isn't the right word here
class GooglePlacesExplorer(GoogleApiHandler):
    '''Wrapper class for PlaceFinder and PlaceDetailer. 
    Includes additional functionality in finding geo-center/bounds for PlaceDetailer.
    '''
    def __init__(self, city, country, sights_access):
        super().__init__()
        self.city = city.lower()
        self.country = country.lower()
        self.db = Sights_DB(sights_access)

    def discover(self, url):
        '''
        Input: URL of Google Travel Sights (String)
        Output: Details of all sights using Google services (Pandas Dataframe Object)
        '''
        try:
            city_df = self.load_from_db('cities')
            finder = GooglePlacesFinder(self.city, self.country)
            location = self.format_loc(city_df['location'].values[0])
            bounds = self.format_bounds(city_df['bounds'].values[0])
            detailer = GoogleSightsDetailer(self.city, self.country, location, bounds)
        except (AttributeError, ValueError):
            print("Fetching data from api")
            city, finder, detailer = self.add_city()        

        sights_list = finder.things_to_do_scrape(url)
        #get more detailed information here        
        count = 0
        sights_df = pd.DataFrame()
        for sight in sights_list.values():
            #if sight != 'National Museum of Modern and Contemporary Art - Seoul':
                #continue
            detailer.detail(sight)
            row = pd.Series(sight.as_dict())
            sights_df = sights_df.append(row, ignore_index=True)
            count += 1
            #if count > 2:
                #break
        return sights_df
    
    def set_geo_limits(self, result):
        loc_dict = result['results'][0]['geometry']['location']
        center = self.format_loc(loc_dict)
        viewport = result['results'][0]['geometry']['viewport']
        bounds = self.format_bounds(viewport)
        return center, bounds

    def format_loc(self, loc):
        Location = namedtuple('Location', ['lat', 'lng'])
        if isinstance(loc, dict):
            return Location(loc['lat'], loc['lng'])
        else: #should be list or tuple
            return Location(loc[0], loc[1])
    
    def format_bounds(self, bounds):
        Bounds = namedtuple('Bounds', ['NE', 'SW'])
        if isinstance(bounds, dict):
            return Bounds(self.format_loc(bounds['northeast']), self.format_loc(bounds['southwest']))
        else:
            return Bounds(self.format_loc(bounds[0]), self.format_loc(bounds[1]))

    def add_city(self):
        api_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        params = 'input={},{}&inputtype=textquery&key={}'.format(self.city, self.country, self.api_keys['google'])
        result = self.call_api(api_url, params)
        location, bounds = self.set_geo_limits(result)
        finder = GooglePlacesFinder(self.city, self.country)
        detailer = GoogleSightsDetailer(self.city, self.country, location, bounds) 
        #get photo
        photos_arr = result.get('results', [])[0].get('photos')
        if photos_arr:
            photo_ref = photos_arr[0].get('photo_reference')
            photo = detailer.fetch_place_photo(photo_ref)
            attributions = photos_arr[0].get('html_attributions')
        city_df = pd.DataFrame().append(pd.Series(
            {
            'city': self.city, 
            'country': self.country, 
            'location': location, 
            'bounds': bounds, 
            'photo': photo, 
            'photo_attributions': attributions
            }), ignore_index=True)
        self.save_to_db('cities', city_df)
        return city_df, finder, detailer

    def save_df(self, df, filepath=None):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights.json'.format(self.city, self.country))
        df.to_json(filepath, default_handler=str, indent=4)
        print(f'Saved DF to {filepath}')

    def load_df(self, filepath=None):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights.json'.format(self.city, self.country))
        return pd.read_json(filepath)

    def save_to_db(self, table_name, df):
        self.db.add(table_name, df)
        self.db.commit(table_name)
        print('Saved to DB')
    
    def load_from_db(self, table_name):
        df = self.db.load(table_name, self.city)
        return df

    def save_excel(self, df, filepath=None):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights.xlsx'.format(self.city, self.country))
        df.to_excel(filepath)
        print(f'Saved excel to {filepath}')

    def load_excel(self, filepath):
        df = pd.read_excel('{}_{}_sights.xlsx'.format(self.city, self.country))
        return df


if __name__ == '__main__':
    #url = 'https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4260007%2C4270442%2C4274032%2C4291318%2C4305595%2C4306835%2C4317915%2C4322822%2C4326765%2C4328159%2C4329288%2C4366684%2C4367953%2C4373849%2C4385383%2C4386665%2C4387290%2C4388508%2C4270859%2C4284970%2C4291517%2C4316256%2C4356900&hl=en&gl=us&un=1&otf=1&dest_mid=%2Fm%2F07dfk&dest_state_type=sattd&tcfs=EgoKCC9tLzA3ZGZr&sa=X&ved=0ahUKEwiBhpS79NzpAhUTK30KHcTgChsQx2gIGA#ttdm=35.674835_139.763908_11&ttdmf=%252Fm%252F07thkr'
    #city = 'Tokyo'
    #country = 'Japan'

    #url = 'https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4270442%2C4305595%2C4306835%2C4317915%2C4319922%2C4322823%2C4328159%2C4367953%2C4371334%2C4381263%2C4384467%2C4393966%2C4401769%2C4402623%2C4403882%2C4412670%2C4270859%2C4284970%2C4291517%2C4412693&hl=en&gl=us&un=1&otf=1&dest_mid=%2Fm%2F09d4_&dest_state_type=sattd&dest_src=ts&sa=X#ttdm=35.009561_135.726459_12&ttdmf=%252Fm%252F05ldrm'
    #city = 'Kyoto'
    #country = 'Japan'

    url = 'https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4270442%2C4306835%2C4317915%2C4322823%2C4328159%2C4371334%2C4401769%2C4403882%2C4419364%2C4424916%2C4425458%2C4425793%2C4427777%2C4432285%2C4270859%2C4284970%2C4291517%2C4412693&hl=en&gl=us&un=1&dest_mid=%2Fm%2F0hsqf&dest_state_type=sattd&dest_src=ts&sa=X#ttdm=37.533159_127.037604_12&ttdmf=%252Fm%252F070chh'
    city = 'Seoul'
    country = 'Korea'

    with open('backend/scraper/db_access.json', 'r') as f:
        sights_access = json.load(f)
    explorer = GooglePlacesExplorer(city, country, sights_access)
    sights_df = explorer.discover(url)
    
    explorer.save_to_db('sights', sights_df)
    explorer.save_df(sights_df)