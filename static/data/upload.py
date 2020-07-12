import csv
from dashboard.models import CED

CSV_PATH = 'static/data/ced.csv'
years = [2016, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
index = 0
with open(CSV_PATH, encoding='UTF-8', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if index != 0:
            y_idx = 0
            code = row[0]
            for i in range(1, 9):
                CED.objects.create(year=years[y_idx], eGRID_subregion=code, ced=row[i])
                y_idx += 1
        index += 1