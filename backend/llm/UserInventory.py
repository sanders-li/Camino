import pandas as pd
import numpy as np
import os

class User:
    def __init__(self, first_name, last_name, email, interests={}, bio=""):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.bio = bio
        self.interests = interests
        self._full_description = None
    
    @property
    def full_description(self):
        return self._full_description
    
    @full_description.setter
    def full_description(self):
        self._full_description = "" #chatgpt generated description from user attributes and user given description
    
    def convert(self):
        base = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "bio": self.bio,
            "full_description": self.full_description
        }
        base.update(self.interests)
        return pd.Series(base)

    def __str__(self):
        return self.convert().to_string()

    def __repr__(self):
        return self.convert()

class Trip:
    def __init__(self, id, name, location="", hotel="", budget=3, length=7, inventory=None, day_trip=False):
        self.id = id
        self.name = name
        self.location = location
        self.hotel = hotel
        self.budget = budget
        self.length = length
        self.inventory = inventory
        self.day_trip = day_trip
    
class Inventory:
    def __init__(self):
        try:
            self.inventory= pd.read_json(self.filepath)
        except ValueError:
            self.inventory = pd.DataFrame(columns = self.sights.columns)
    
    def add_item(self):
        print(self.sights)
        sight_index = int(input('Which sight do you want to add? '))
        row = self.sights.loc[sight_index]
        self.inventory = self.inventory.append(row).reset_index(drop=True)
        print('Your Inventory is now:')
        print(self.inventory)
        
    def del_item(self):
        if not self.inventory.empty:
            print(self.inventory)
            inventory_index = int(input('Which sight do you want to remove? '))
            self.inventory = self.inventory.drop(inventory_index).reset_index(drop=True)
        print('Your Inventory is now:')
        print(self.inventory)

    def save_inventory(self):
        json.dump(self.filepath)
#Add trips class for UserInventory to inherit

if __name__ == '__main__':
    access_dict = {"user": "postgres", "password": "camino", "host": "127.0.0.1", "port": "5432", "database": "sights"}

    print('Staging')
    