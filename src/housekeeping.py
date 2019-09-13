from pymongo import MongoClient
import psycopg2
import getpass


class ConnectPostgres(object):
    def __init__(self):
        upass = getpass.getpass()
        self.conn = psycopg2.connect(database="renewable_energy_generation",
                                     user="admin", password=upass,
                                     host="localhost", port="5432")
        print("connected")
        self.cur = self.conn.cursor()

    def query(self, sql):
        self.cur.execute(sql)
        self.conn.commit()

    def close(self):
        self.conn.close()


class ConnectMongo(object):
    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['renewable_energy']
        self.table = self.db['bulk_import']
        # includes all keys needed to pull from specific API
        # series_ids for generation and capacity
        # table created/populated outside script
        # mongoimport --db renewable_energy --collection bulk_import < INTL.txt
