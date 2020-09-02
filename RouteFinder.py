import pandas as pd
from Place import Sight
import numpy as np
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import matplotlib.pyplot as plt
from geopy.distance import distance as geopy_distance
from collections import namedtuple
from SightScraper import WebAPIRequestHandler
from adjustText import adjust_text

class RouteFinder:
    def __init__(self, data = {}):
        self.data = data
        self.routing = None
        self.manager = None
        self.solution = None
        self.bb = None

    def create_test_data_model(self, filepath):
        '''File must be in json'''
        sights_list = []
        sights_df = pd.read_json(filepath)
        '''
        for row in sights_df.itertuples():
            sights_list.append(Sight(row))
        df = pd.DataFrame(columns=['name', 'lat', 'lng'])
        for place in sights_list:
            lat = float(place.location.lat)
            lng = float(place.location.lng)
            df = df.append(pd.Series({'name': place.name, 'lat': lat, 'lng': lng}), ignore_index=True)
        '''
        Location = namedtuple('Location', ['lat', 'lng'])
        self.data['names'] = ['Dormy Inn Akihabara']
        self.data['names'] += [name for name in sights_df['name']]
        self.data['locations'] = [Location(35.702540, 139.773290)]
        self.data['locations'] += [Location(point.location[0], point.location[1]) for point in sights_df.itertuples()]
        self.bb = self.get_bb(self.data['locations'])
        self.data['num_locations'] = len(self.data['locations'])
        self.data['hotel_index'] = 0

        #Rest of this is test stuff, find a way to transform the data
        self.data['time_windows'] = [(0,0)] + [(0,540) for i in range(self.data['num_locations']-1)]
        self.data['visit_times'] = [0] + [90 for i in range(self.data['num_locations']-1)]
        self.data['length_of_stay'] = 3
        self.data['available_time'] = [1440 for i in range(self.data['length_of_stay'])]

    @staticmethod   
    def get_bb(locations, offset=0.01):
        lngs = [point.lng for point in locations]
        lats = [point.lat for point in locations]
        bb = (min(lngs) - offset, max(lngs) + offset, \
            min(lats) - offset, max(lats) + offset)
        return bb

    #Constraints
    @staticmethod
    def calc_distance(u,v):
        return geopy_distance(u,v).meters

    def calc_travel_time(self, from_node, to_node):
        if from_node == to_node:
            travel_time = 0
        else:
            travel_time = self.calc_distance(self.data['locations'][from_node], self.data['locations'][to_node]) / 300
        return travel_time

    def gen_distance_matrix(self):
        distance_matrix = {}
        for from_node in range(self.data['num_locations']):
            distance_matrix[from_node] = {}
            for to_node in range(self.data['num_locations']):
                if from_node == to_node:
                    distance_matrix[from_node][to_node] = 0
                else:
                    distance_matrix[from_node][to_node] = (self.calc_distance(
                        self.data['locations'][from_node], self.data['locations'][to_node]))
        self.data['distance_matrix'] = distance_matrix

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
        result_json = WebAPIRequestHandler().call_api(url)
        distance_matrix = []
        for row in result_json['rows']:
            elements = row['elements']
            for i, element in enumerate(row['elements']):
                distance_matrix.append(element['distance']['value'])
        return distance_matrix

    def add_capacity_constraints(self, routing, demand_evaluator_index):
        """Adds capacity constraint"""
        capacity = 'Capacity'
        routing.AddDimensionWithVehicleCapacity(
            demand_evaluator_index,
            0,  # capacity slack
            self.data['available_time'],
            True,  # start cumul to zero
            capacity)

    def gen_time_matrix_wst(self):
        time_matrix = {}
        for from_node in range(self.data['num_locations']):
            time_matrix[from_node] = {}
            for to_node in range(self.data['num_locations']):
                if from_node == to_node:
                    time_matrix[from_node][to_node] = 0
                else:
                    time_matrix[from_node][to_node] = self.data['visit_times'][from_node] + self.calc_travel_time(from_node, to_node)
        self.data['time_matrix_wst'] = time_matrix

    def add_time_window_constraints(self, routing, manager, time_evaluator_index):
        """Add Global Span constraint"""
        time = 'Time'
        routing.AddDimension(
            time_evaluator_index,
            15,  # allow waiting time
            self.data['available_time'][0],  # maximum time per vehicle
            False,  # don't start cumul to zero since we are giving TW to start nodes
            time)
        time_dimension = routing.GetDimensionOrDie(time)
        # Add time window constraints for each location except depot
        # Include slack in solution object
        for location_idx, time_window in enumerate(self.data['time_windows']):
            if location_idx == 0:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
            routing.AddToAssignment(time_dimension.SlackVar(index))
        # Add time window constraints for each vehicle start node
        # Include slack in solution object
        for day in range(self.data['length_of_stay']):
            index = routing.Start(day)
            time_dimension.CumulVar(index).SetRange(self.data['time_windows'][0][0],
                                                    self.data['time_windows'][0][1])
            routing.AddToAssignment(time_dimension.SlackVar(index))

    def solve(self):
        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(self.data['num_locations'],
                                                self.data['length_of_stay'], self.data['hotel_index'])

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)
        
        # Define weight of each edge
        self.gen_distance_matrix()
        def distance_callback(from_node, to_node):
            return self.data['distance_matrix'][manager.IndexToNode(from_node)][manager.IndexToNode(
                to_node)]
        distance_evaluator_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(distance_evaluator_index)


        # Add Capacity constraint
        def cost_callback(from_node):
            return self.data['visit_times'][manager.IndexToNode(from_node)]
        demand_evaluator_index = routing.RegisterUnaryTransitCallback(cost_callback)
        self.add_capacity_constraints(routing, demand_evaluator_index)


        # Add Time Window constraint
        self.gen_time_matrix_wst()
        def tw_callback(from_node, to_node):
            return self.data['time_matrix_wst'][manager.IndexToNode(from_node)][manager.IndexToNode(to_node)]
        time_evaluator_index = routing.RegisterTransitCallback(tw_callback)
        self.add_time_window_constraints(routing, manager, time_evaluator_index)

        # Setting first solution heuristic (cheapest addition).
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            self.manager = manager
            self.routing = routing
            self.solution = solution
        else:
            print('Failed to find solution')

    def print_solution(self):
        """Prints solution on console"""
        #This is rather messy
        print('Objective: {}'.format(self.solution.ObjectiveValue()))
        total_distance = 0
        total_load = 0
        total_time = 0
        capacity_dimension = self.routing.GetDimensionOrDie('Capacity')
        time_dimension = self.routing.GetDimensionOrDie('Time')
        trip_travel_times = []
        Travel = namedtuple('Travel', ['start_index', 'end_index', 'time'])
        for day in range(self.data['length_of_stay']):
            index = self.routing.Start(day)
            plan_output = 'Route for day {}:\n'.format(day+1)
            distance = 0
            sights_visited = 0
            previous_time = 0
            previous_load_agg = 0
            day_travel_times = []
            while not self.routing.IsEnd(index):
                # Time is capacity - CVRP format defaults to displaying vehicle capacity upon arrival at any given location
                # This capacity is an aggregate of accumulated capacity)
                # Instead, advance load_var one index to reflect time spent at any given location
                # Track both previous load aggregate and previous load value to make calculation easier
                next_index = self.solution.Value(self.routing.NextVar(index))
                load_var = capacity_dimension.CumulVar(next_index)
                load = self.solution.Value(load_var) - previous_load_agg
                time_var = time_dimension.CumulVar(index)
                slack_var = time_dimension.SlackVar(index)
                plan_output += ' [Location {0}: {1}] | Time({2},{3}) Slack({4},{5})'.format(
                    self.manager.IndexToNode(index), 
                    self.data['names'][self.manager.IndexToNode(index)],
                    self.solution.Min(time_var),
                    self.solution.Max(time_var),
                    self.solution.Min(slack_var), 
                    self.solution.Max(slack_var))
                if self.manager.IndexToNode(index) != self.data['hotel_index']:
                    travel_time = self.solution.Min(time_var) - previous_time - previous_load
                    plan_output += ' | Travel Time From Prev: {}'.format(travel_time)
                    day_travel_times.append(Travel(previous_index, self.manager.IndexToNode(index), travel_time))
                plan_output += ' | Time Spent Here: {} | -> \n'.format(load)
                previous_index = index
                previous_load_agg = self.solution.Value(load_var)
                previous_load = load
                previous_time = self.solution.Min(time_var)
                index = self.solution.Value(self.routing.NextVar(index))
                distance += self.routing.GetArcCostForVehicle(previous_index, index, day)
                sights_visited += 1
            load_var = capacity_dimension.CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            slack_var = time_dimension.SlackVar(index)
            load = self.solution.Value(load_var) - previous_load_agg
            travel_time = self.solution.Min(time_var) - previous_time - previous_load
            plan_output += ' [Location {0}: {1}] | Time({2},{3}) | Travel Time From Prev: {4}\n'.format(
                self.manager.IndexToNode(index),
                self.data['names'][self.manager.IndexToNode(index)],
                self.solution.Min(time_var), 
                self.solution.Max(time_var),
                travel_time)
            day_travel_times.append(Travel(previous_index, self.manager.IndexToNode(index), travel_time))
            plan_output += 'Distance of the route: {}m\n'.format(distance)
            plan_output += 'Load of the route (Time spent at places): {}min\n'.format(self.solution.Value(load_var))
            plan_output += 'Travel Time of the route: {}min\n'.format(sum([travel.time for travel in day_travel_times]))
            plan_output += 'Total Time of the route: {}min\n'.format(self.solution.Value(time_var))
            plan_output += 'Number of sights visited: {} places\n'.format(sights_visited - 1)
            print(plan_output)
            total_distance += distance
            total_load += self.solution.Value(load_var)
            total_time += self.solution.Value(time_var)
            trip_travel_times.append(day_travel_times)
        print('Total Distance of all routes: {}m'.format(total_distance))
        print('Total Load of all routes (Time spent at places): {}min'.format(total_load))
        #print('Total Time of all routes: {}min'.format(total_time))
        print('Total Travel Time of all routes: {}min'.format(sum([sum([travel.time for travel in day_travel_times]) for day_travel_times in trip_travel_times])))

    def visualize(self, save=False):
        fig, ax = plt.subplots(figsize=(16, 9))
        tokyo_map = plt.imread('tokyo_map.png')
        styling = dict(boxstyle="round", alpha=0.6, facecolor='white')
        
        texts = []
        for i, point in enumerate(self.data['locations']):
            if i == self.data['hotel_index']:
                plt.scatter(point.lng, point.lat, zorder=2, alpha=1, c='r', s=100)
                texts.append(ax.text(point.lng, point.lat, '{}: {}'.format(i, self.data['names'][i]), ha='center', va='center', bbox=styling))
            else:
                plt.scatter(point.lng, point.lat, zorder=1, alpha=0.5, c='b', s=100)
                texts.append(ax.text(point.lng, point.lat, '{}: {}'.format(i+1, self.data['names'][i]), ha='center', va='center', bbox=styling))
                
        adjust_text(texts, expand_text=(1.05, 2.5), only_move={'text': 'y'})
        
        cgroup = ['b', 'g', 'r', 'm', 'k']
        for day in range(self.data['length_of_stay']):
            index = self.routing.Start(day)
            start_x, start_y = self.data['locations'][0][1], self.data['locations'][0][0]
            while not self.routing.IsEnd(index):
                x = self.data['locations'][self.manager.IndexToNode(index)][1]
                y = self.data['locations'][self.manager.IndexToNode(index)][0]
                plt.arrow(start_x, start_y, x-start_x, y-start_y, length_includes_head=True, width=0.0005, alpha=0.5, color=cgroup[day])
                start_x, start_y = x, y
                index = self.solution.Value(self.routing.NextVar(index))
            x = self.data['locations'][self.manager.IndexToNode(index)][1]
            y = self.data['locations'][self.manager.IndexToNode(index)][0]
            plt.arrow(start_x, start_y, x-start_x, y-start_y, length_includes_head=True, width=0.0005, alpha=0.5, color=cgroup[day])

        ax.set_xlim(self.bb[0], self.bb[1])
        ax.set_ylim(self.bb[2], self.bb[3])
        ax.set_xlabel('Lng')
        ax.set_ylabel('Lat')

        ax.imshow(tokyo_map, zorder=0, extent=self.bb, aspect='auto')
        plt.show()
        if save:
            fig.savefig('example.png', bbox_inches='tight')
            plt.close(fig)

if __name__ == '__main__':
    filepath = 'sights.json'
    routefinder = RouteFinder()
    routefinder.create_test_data_model(filepath)
    routefinder.solve()
    routefinder.print_solution()
    routefinder.visualize(save=True)