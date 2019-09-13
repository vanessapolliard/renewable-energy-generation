from housekeeping import ConnectPostgres
import psycopg2
import getpass

if __name__ == '__main__':
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
    # connect to postgres, query, and close
    postgres_connection = ConnectPostgres()
    postgres_connection.query(add_cols)
    postgres_connection.close()
