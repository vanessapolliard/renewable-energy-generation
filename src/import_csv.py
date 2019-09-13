from housekeeping import ConnectPostgres
import requests
import os, sys
import time
import psycopg2
import getpass
import csv

def ConvertCSV(InFilePath):
    with open(str(InFilePath), mode="rU") as infile:
        reader = csv.reader(infile, dialect="excel")
        with open(str(InFilePath) + '_pipe.txt', mode="w") as outfile:
            writer = csv.writer(outfile, delimiter='|')
            writer.writerows(reader)
    return outfile

if __name__ == '__main__':
    create_investment_table = '''
                CREATE TABLE private_investment (
                    region varchar,
                    country varchar,
                    income_group varchar,
                    ida_status varchar,
                    fin_closing_year varchar,
                    fin_closing_month varchar,
                    project_name varchar,
                    related_names varchar,
                    type_of_ppi varchar,
                    subtype_of_ppi varchar,
                    project_status varchar,
                    primary_sector varchar,
                    secondary_sector varchar,
                    subsector varchar,
                    segment varchar,
                    location varchar,
                    contract_period varchar,
                    termination_year varchar,
                    publicly_traded varchar,
                    stock_exchange varchar,
                    multiple_systems varchar,
                    number_of_systems varchar,
                    captive_facility varchar,
                    share_percent varchar,
                    govt_granting_contract varchar,
                    type_of_govt_support varchar,
                    investment_year varchar,
                    percent_private varchar,
                    gov_payment_commitments varchar,
                    physical_assets varchar,
                    total_investment varchar,
                    cpi_adjusted_investment varchar,
                    govt_cash_assist varchar,
                    date_status_updated varchar,
                    capacity_type varchar,
                    capacity varchar,
                    capacity_year varchar,
                    technology varchar,
                    contract_history varchar,
                    related_projects varchar,
                    bid_criteria varchar,
                    award_method varchar,
                    number_of_bids varchar,
                    number_renewal_bids varchar,
                    sponsors varchar,
                    multi_lateral_support varchar,
                    revenue_source varchar,
                    renewal_bid_criteria varchar,
                    renewal_award_method varchar,
                    development_stage varchar,
                    commissioning_date varchar,
                    project_grid varchar,
                    carbon_credits varchar,
                    funding_year varchar,
                    private_funding varchar,
                    public_funding varchar,
                    govt_funding varchar,
                    bank_local_funding varchar,
                    donor_funding varchar,
                    debt_equity_grant_ratio varchar
                );
                '''
    
    # created database outside of script in docker container
    postgres_connection = ConnectPostgres()
    postgres_connection.postgres_connect()
    postgres_connection.query(create_investment_table)

    ConvertCSV('../data/All_Data_1990-2012.csv')

    # copy data from file to postgres DB
    with open('../data/All_Data_1990-2012.csv_pipe.txt', 'r') as f:
        next(f) # Skip the header row.
        postgres_connection.cur.copy_from(f, 'private_investment', sep='|')
    
    # close connection
    postgres_connection.close()