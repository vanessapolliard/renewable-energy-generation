import requests
import os, sys
import time
from bson.json_util import loads
import psycopg2
import getpass
from pymongo import MongoClient

# MONGO
# find series IDs to use in API calls for Generation (need to do consumption as well)
# mongoimport --db renewable_energy --collection bulk_import < INTL.txt
client = MongoClient('localhost',27017)
db = client['renewable_energy']
table = db['bulk_import'] # includes all keys needed to pull from specific API series_ids for generation and capacity

generation_category = db.bulk_import.find({'category_id': '2134668'},{'childseries': 1,'_id': 0})
capacity_category = db.bulk_import.find({'category_id': '2134665'},{'childseries': 1,'_id': 0})

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

# created PostgreSQL database outside of script in docker container
# connect to database
upass = getpass.getpass()
conn = psycopg2.connect(database="renewable_energy_generation", user="admin", password=upass, host="localhost", port="5432")
print("connected")

cur = conn.cursor()
query = '''
            CREATE TABLE net_generation (
                country varchar,
                period varchar,
                value varchar,
                units varchar
            );
            '''
query2 = '''
            CREATE TABLE installed_capacity (
                country varchar,
                period varchar,
                value varchar,
                units varchar
            );
            '''
cur.execute(query)
cur.execute(query2)
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

    # FULL RUN
    series_list1 = format_output(generation_category)
    series_list2 = format_output(capacity_category)

    call_api_insert(net_generation_series,payload,series_list1,generation_table)
    call_api_insert(installed_capacity_series,payload,series_list2,capacity_table)

    conn.close()