from pymongo import MongoClient
from housekeeping import ConnectPostgres, ConnectMongo
import requests
import os, sys
import time
import psycopg2
import getpass


# OTHER POSTGRES - created PostgreSQL database outside of script in docker container

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

# Single API request function - not needed but helpful for troubleshooting
def single_api_query(link, payload, series=None):
    full_link = link + series
    response = requests.get(full_link, params=payload)
    if response.status_code != 200:
        print('WARNING', response.status_code)
    else:
        api_response = response.json()
        return api_response

# Call API and insert into Postgres DB after each country call
def call_api_insert(url,payload,series_list,table,connection):
    for series_id in series_list:
        result = single_api_query(url,payload,series_id)
        data = result['series'][0]['data']
        name = result['series'][0]['name'].split(',')[1].replace(" ","")
        units = result['series'][0]['units']
        for item in data:
            year = int(item[0])
            value = item[1]
            if value == '--':
                value = None
            else:
                value = float(item[1])
            insert_vals = [name, year, value, units]
            if table == generation_table:
                insert_query = "INSERT INTO net_generation VALUES (%s, %s, %s, %s)"
            elif table == capacity_table:
                insert_query = "INSERT INTO installed_capacity VALUES (%s, %s, %s, %s)"
            connection.cur.execute(insert_query, tuple(insert_vals))
            connection.conn.commit()


if __name__ == '__main__':
    # Define API URLs and API key
    net_generation_series = 'http://api.eia.gov/series/?series_id='
    installed_capacity_series = 'http://api.eia.gov/series/?series_id='
    payload = {'api_key': os.environ['EIA_API_KEY']}
    generation_table = 'net_generation'
    capacity_table = 'installed_capacity'

    create_generation_table = '''
                CREATE TABLE net_generation (
                    country varchar,
                    period int,
                    value float,
                    units varchar
                );
                '''
    creation_capacity_table = '''
                CREATE TABLE installed_capacity (
                    country varchar,
                    period int,
                    value float,
                    units varchar
                );
                '''

    # connect to DBs
    mongo_connection = ConnectMongo()

    postgres_connection = ConnectPostgres()
    postgres_connection.postgres_connect()

    # create tables
    postgres_connection.query(create_generation_table)
    postgres_connection.query(creation_capacity_table)
    print("Tables created")

    # find series IDs to use in API calls
    generation_category = mongo_connection.db.bulk_import.find({'category_id': '2134668'},{'childseries': 1,'_id': 0})
    capacity_category = mongo_connection.db.bulk_import.find({'category_id': '2134665'},{'childseries': 1,'_id': 0})
    print("Categories found")

    # format series lists
    series_list1 = format_output(generation_category)
    series_list2 = format_output(capacity_category)
    print("Categories formatted")

    # call APIs for all series and insert into postgres table
    call_api_insert(net_generation_series,payload,series_list1,generation_table,postgres_connection)
    print("Generation inserts complete")
    call_api_insert(installed_capacity_series,payload,series_list2,capacity_table,postgres_connection)
    print("Capacity inserts complete")

    # close postgres connection
    postgres_connection.close()
    print("DB Connection closed")