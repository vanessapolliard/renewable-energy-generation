from bson.json_util import loads
from pymongo import MongoClient
import requests
import os, sys
import time
import psycopg2
import getpass
import this

# OTHER MONGO - mongoimport --db renewable_energy --collection bulk_import < INTL.txt
# OTHER POSTGRES - created PostgreSQL database outside of script in docker container

def housekeeping():
    # globals
    globals conn, cur
    # connect to mongo
    client = MongoClient('localhost',27017)
    db = client['renewable_energy']
    table = db['bulk_import'] # includes all keys needed to pull from specific API series_ids for generation and capacity
    # connect to postgres
    upass = getpass.getpass()
    conn = psycopg2.connect(database="renewable_energy_generation", user="admin", password=upass, host="localhost", port="5432")
    print("connected")
    cur = conn.cursor()

# Format Mongo output
def format_output(data):
    list_temp = []
    for item in data:
        list_temp.append(item)
    # remove formatting from string and turn into list
    str_temp = str(list_temp).replace("{","").replace("}","").replace("'childseries': ","").replace("'","").replace("[[","[").replace("]]","]").replace("[","").replace("]","")
    api_query_vals = str_temp.split(", ")
    if data == generation_category:
        api_query_vals_kwh = [series for series in api_query_vals if 'BKWH' in series]
        return api_query_vals_kwh
    elif data == capacity_category:
        return api_query_vals

# POSTGRESQL
# Single API request function - not needed but helpful for troubleshooting
def single_api_query(link, payload, series=None):
    full_link = link + series
    response = requests.get(full_link, params=payload)
    if response.status_code != 200:
        print('WARNING', response.status_code)
    else:
        api_response = response.json()
        return api_response

def run_query(query):
    cur.execute(query)
    conn.commit()


def call_api_insert(url,payload,series_list,table):
    for series_id in series_list:
        result = single_api_query(url,payload,series_id)
        data = result['series'][0]['data']
        name = result['series'][0]['name'].split(',')[1].replace(" ","")
        units = result['series'][0]['units']
        for item in data:
            year = item[0]
            value = item[1]
            insert_vals = [name, year, value, units]
            if table == generation_table:
                insert_query = "INSERT INTO net_generation VALUES (%s, %s, %s, %s)"
            elif table == capacity_table:
                insert_query = "INSERT INTO installed_capacity VALUES (%s, %s, %s, %s)"
            cur.execute(insert_query, tuple(insert_vals))
            conn.commit()


if __name__ == '__main__':
    # Define API URLs and API key
    net_generation_series = 'http://api.eia.gov/series/?series_id='
    installed_capacity_series = 'http://api.eia.gov/series/?series_id='
    # MVP++ us_demand = 'http://api.eia.gov/category/?series_id=EBA.US48-ALL.D.H'
    payload = {'api_key': os.environ['EIA_API_KEY']}
    generation_table = 'net_generation'
    capacity_table = 'installed_capacity'

    create_generation_table = '''
                CREATE TABLE net_generation (
                    country varchar,
                    period varchar,
                    value varchar,
                    units varchar
                );
                '''
    creation_capacity_table = '''
                CREATE TABLE installed_capacity (
                    country varchar,
                    period varchar,
                    value varchar,
                    units varchar
                );
                '''

    # connect to DBs
    housekeeping()

    # create tables
    run_query(create_generation_table)
    run_query(creation_capacity_table)

    # find series IDs to use in API calls
    generation_category = db.bulk_import.find({'category_id': '2134668'},{'childseries': 1,'_id': 0})
    capacity_category = db.bulk_import.find({'category_id': '2134665'},{'childseries': 1,'_id': 0})
    
    # format series lists
    series_list1 = format_output(generation_category)
    series_list2 = format_output(capacity_category)

    # call APIs for all series and insert into postgres table
    call_api_insert(net_generation_series,payload,series_list1,generation_table)
    call_api_insert(installed_capacity_series,payload,series_list2,capacity_table)

    conn.close()