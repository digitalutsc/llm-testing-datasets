# this script reads an input.csv and writes 250 randomly selected rows to output.csv

import csv
import random

# read the input csv file
with open('input.csv', 'r') as input_file:
    reader = csv.reader(input_file)
    header = next(reader) 
    rows = list(reader)

# check if there are at least 250 rows
if len(rows) < 250:
    print("Error: Not enough rows in the CSV file.")
    exit(1)

# select 250 random rows
selected_rows = random.sample(rows, 250)

# write the selected rows to output.csv
with open('output.csv', 'w') as output_file:
    writer = csv.writer(output_file)
    writer.writerow(header) 
    writer.writerows(selected_rows) 

print("250 random rows have been written to output.csv")