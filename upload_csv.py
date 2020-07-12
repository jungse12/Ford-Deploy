'''
import csv
from dashboard.models import GWP

CSV_PATH = 'static/data/gwp.csv'
years = [2016, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
index = 0
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if index != 0:
            code = row[0]
            for i in range(1, len(row)):
                #print(years[i], code, row[i])
                GWP.objects.create(year=years[i], eGRID_subregion=code, gwp=row[i])
        index += 1

CSV_PATH = 'static/data/HomeESS.csv'
index = 0
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if index != 0:
            HomeESS.objects.create(Zone_1=row[0], Zone_2=row[1],Zone_3=row[2],Zone_4=row[3],Zone_5=row[4],Zone_6=row[5],Zone_7=row[6])
        index += 1
'''


'''
CSV_PATH = 'static/data/gwp.csv'
years = [2016, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
index = 0
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if index != 0:
            code = row[0]
            for i in range(1, len(row)):
                print(years[i], code, row[i])
                # GWP.objects.create(year=years[i], eGRID_subregion=code, gwp=row[i])
        index += 1



CSV_PATH_CLIMATE_ZONE = 'static/data/climate_zones.csv'

index = 0
with open(CSV_PATH_CLIMATE_ZONE, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        # Skip the first line
        if index != 0:
            ClimateZone.objects.create(state=row[0], state_FIPS=row[1], county_FIPS=row[2], county_name=row[6], climate_zone=row[3])
        index += 1

CSV_PATH_EGRID_SUBREGION = 'static/data/eGrid_subregion.csv'

index = 0
with open(CSV_PATH_EGRID_SUBREGION, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        # Skip the first line
        if index != 0:
            EGRID.objects.create(zip_code=row[1], state=row[2], eGRID_subregion=row[3])
        index += 1

CSV_PATH = 'static/data/zipcode_county.csv'
index = 0
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        # Skip the first line
        if index != 0:
            ZipcodeCounty.objects.create(zip_code=row[0], county_name=row[4])
        index += 1
        '''

