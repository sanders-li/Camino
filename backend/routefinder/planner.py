import os
import pandas as pd
from Place import Sight, Hotel
import datetime
import ortools
from collections import defaultdict, namedtuple
from SightScraper import GoogleAPI_TK
from scipy.spatial import distance_matrix
import matplotlib.pyplot as plt

class HotelEvent():
    def __init__(self, name=None, location=None, start=None, end=None):
        self.name = name
        self.location = location
        self.start = start
        self.end = end
    
    def from_place(self, place, start=None, end=None):
        self.name = place.name
        self.location = place.location
        self.start = start
        self.end = end


class SightEvent():
    default_visit_time = datetime.time(2)

    def __init__(self, name=None, location=None, start_time=None, end_time=None):
        self.name = name
        self.location = location
        self.start_time = start_time
        self.end_time = end_time
    
    def from_place(self, place):
        self.name = place.name
        self.location = place.location
        if place.visit_time:
            if self.start_time:
                self.end_time = datetime.timedelta(self.start_time, place.visit_time)
        else:
            if self.start_time:
                self.end_time = datetime.timedelta(self.start_time, default_visit_time)
        


class Day():
    def __init__(self, start_time=datetime.time(9, 0), end_time=datetime.time(21, 0), events=[]):
        '''Default times (local):
        Start time = 9:00am (9:00)
        End time = 9:00pm (21:00)
        '''
        self.start_time = start_time
        self.end_time = end_time
        self.events = events


class Plan():
    def __init__(self, start=None, plan=None):
        self.start = start
        self.plan = []
        
    def create_day(self, start, end, events):
        day = Day(start, end, events)
        self.plan.append(day)

# Vehicle routing problem with:
# Time window Limitations - Closest to ideal time window (can be inherent, inferred or user-set) or within a strict (opening and closing times) time window (VRPTW)
# Place Visit time - maybe consider time a capacity (C - capacity), but more appropriately include service time for each location (ST - stochastic time?)
# Restaurant inclusion - must visit a restaurant near an idealized time (PD - pickup and delivery?)
# Problem to solve - CVRPPD-ST or VRPPDTW-ST
# Optimal solution: space on x,y, time on z. Shortest route would be shortest line distance overall in spacetime

class Planner():
    def __init__(self, plan=None, sight_list=[], hotel_list=[], eat_list=[], scale=0.001):
        self.plan = plan
        self.sight_list = sight_list
        self.hotel_list = hotel_list
        self.eat_list = eat_list
        self.bb_offset = 0.01
        self.bb = None
    
    def create_plan(self):
        pass

    def visualize(self, sights_list, hotels_list, frugal=True):              
        sights_loc_df = self.gen_loc_df(sights_list)
        hotels_loc_df = self.gen_loc_df(hotels_list)

        fig, ax = plt.subplots(figsize=(16,9))
        tokyo_map = plt.imread('tokyo_map.png')
        ax.scatter(sights_loc_df.lng, sights_loc_df.lat, zorder=1, alpha=0.5, c='b')
        ax.scatter(hotels_loc_df.lng, hotels_loc_df.lat, zorder=2, alpha=1, c='r')
        for point in sights_loc_df.itertuples():
            ax.annotate(s=str(point.Index), xy=(point.lng, point.lat))
        ax.set_title('Locations', size=24)
        ax.set_xlim(self.bb[0], self.bb[1])
        ax.set_ylim(self.bb[2], self.bb[3])

        ax.imshow(tokyo_map, zorder=0, extent=self.bb, aspect='auto')
        plt.show()
        
        return sights_loc_df

    def update_bb(self, df):
        new_bb = (df.lng.min() - self.bb_offset), df.lng.max() + self.bb_offset), \
                  df.lat.min() - self.bb_offset), df.lat.max() + self.bb_offset))
        if self.bb:
            self.bb = (min(self.bb[0], new_bb[0]), max(self.bb[1], new_bb[1]), \
                       min(self.bb[2], new_bb[2]), max(self.bb[3], new_bb[3]))
        else:
            self.bb = new_bb
        return self.bb

    def print_bb(self):
        print('\t\t{}\n{}\t\t\t{}\n\t\t{}'.format(self.bb[1], self.bb[2], \
                                                  self.bb[3], self.bb[0]))

    def gen_loc_df(self, place_list, update=True):
        df = pd.DataFrame(columns=['name', 'lat', 'lng'])
        for place in place_list:
            lat = float(place.location.lat)
            lng = float(place.location.lng)
            df = df.append(pd.Series({'name': place.name, 'lat': lat, 'lng': lng}), ignore_index=True)
        if update:
            self.update_bb(df)
        return df

    def generate_distance_matrix(self, place_list):
        max_ele = 100
        addresses = [place.place_id for place in place_list]
        n = len(place_list)
        max_rows = max_ele // n
        q, r = divmod(n, max_rows)
        distance_matrix = []
        for i in range(q):
            origins = places[i*max_rows : (i+1)*max_rows]
            distance_matrix += self.call_distance_matrix_api(origins, addresses)
        if r:
            origins = addresses[q*max_rows : ]
            distance_matrix += self.call_distance_matrix_api(origins, addresses)
        with open('distance_matrix.txt', 'w+') as f:
            f.write(distance_matrix)
        return distance_matrix
            
    def call_distance_matrix_api(self, origins, destinations):
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins={}&destinations={}'.format('|'.join(origins), '|'.join(destinations))
        result_json = GoogleAPI_TK().call_api(url)
        distance_matrix = []
        for row in result_json['rows']:
            elements = row['elements']
            for i, element in enumerate(row['elements']):
                distance_matrix.append(element['distance']['value'])
        return distance_matrix

if __name__=='__main__':
    interests = []
    sights_list = []
    sights_df = pd.read_json('sights.json')
    for row in sights_df.itertuples():
        sights_list.append(Sight(row))
    
    Location = namedtuple('Location', ['lat', 'lng'])
    hotel = Hotel({'name': 'Dormy Inn Akihabara', 'location': Location(35.702540, 139.773290)})
    planner = Planner()
    planner.visualize(sights_list, [hotel])