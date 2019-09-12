import psycopg2
import getpass

upass = getpass.getpass()
conn = psycopg2.connect(database="renewable_energy_generation", user="admin", password=upass, host="localhost", port="5432")
print("connected")
cur = conn.cursor()

add_cols = '''
            ALTER TABLE installed_capacity 
            ADD COLUMN bkwh_100 FLOAT;

            ALTER TABLE installed_capacity 
            ADD COLUMN bkwh_98 FLOAT;

            ALTER TABLE installed_capacity 
            ADD COLUMN bkwh_95 FLOAT;

            ALTER TABLE installed_capacity 
            ADD COLUMN bkwh_75 FLOAT;
            
            ALTER TABLE installed_capacity 
            ADD COLUMN bkwh_50 FLOAT;

            UPDATE installed_capacity
            SET bkwh_100 = (value*8760*1/1000);

            UPDATE installed_capacity
            SET bkwh_98 = (value*8760*0.98/1000);

            UPDATE installed_capacity
            SET bkwh_95 = (value*8760*0.95/1000);
            UPDATE installed_capacity
            SET bkwh_75 = (value*8760*0.75/1000);

            UPDATE installed_capacity
            SET bkwh_50 = (value*8760*0.5/1000);
            '''

cur.execute(add_cols)
conn.commit()
conn.close()