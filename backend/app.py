from flask import Flask, render_template, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from Sights_DB_DF import Sights_DB
import pandas as pd
import os
import json


app = Flask(__name__)
with open('db_verification.json', 'r') as f:
    access_dict = json.load(f)

# No idea why the following works. Should I be using g or session instead? Only want this persistent for single request
# Session sounds most reasonable but I do not want data stored server side
# Current issue - Going home does not reset search
app.sights = pd.DataFrame()
# Sight additional fields:
# Relevancy index? (popularity)
app.inventory = pd.DataFrame()
# Inventory additional fields: 
# Place type (Sight, Hotel, Eatery), Must visit/Optional, 
# TODO: Include custom point entry 
app.city = ''

# Two approaches
# 1. Load sights into DF via methods in Sights module
# 2. Query database directly

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        app.city = request.form['city'].capitalize()
        app.sights = Sights_DB(access_dict).load_sights(app.city)

    search_titles = {'name': 'Name', 'category': 'Category', 'descrip_title': 'Description', 'rating': 'Rating'}
    inv_titles = {'name': 'Name', 'category': 'Category', 'descrip_title': 'Description'}
    return render_template('index.html', city=app.city, search_titles = search_titles, inv_titles = inv_titles, \
                            places=app.sights.to_dict('records'), inventory = app.inventory.to_dict('records'))


#these methods should use javascript instead
@app.route('/add/<place_id>')
def add(place_id):
    try:
        app.inventory = app.inventory.append(app.sights.loc[app.sights['place_id'] == place_id], ignore_index=True)
    except Exception as e:
        return f'There was an issue adding your sight. Exception: {e}'
    return redirect('/')

@app.route('/remove/<int:id>')
def remove(id):
    try:
        app.inventory = app.inventory.drop([id]).reset_index(drop=True)
    except Exception as e:
        print(e)
        return f'There was an issue removing that sight: {e}'
    return redirect('/')

@app.route('/savefile')
def save():
    try:
        if not app.inventory.empty:
            path = os.getcwd()
            filename = 'sights.json'
            filepath = os.path.join(path, filename)
            app.inventory.to_json(filepath, indent=4)
            return send_from_directory(path, filename, as_attachment=True, cache_timeout=0)
        else:
            print('Inventory is empty')
            return redirect('/')
    except Exception as e:
        print(e)
        return f'There was an issue saving: {e}'


@app.route('/reset')
def reset():
    try:
        app.city = ''
        app.sights = pd.DataFrame()
    except Exception as e:
        return f'There was an issue resetting: {e}'
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)