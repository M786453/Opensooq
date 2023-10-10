import json
import csv

def convert(data):

    with open("products_data.csv", "w", newline="", encoding='utf-8') as csv_file:

        csv_writer = csv.writer(csv_file)

        csv_writer.writerow(data[0].keys())
        counter = 1
        for product in data:
            
            try:
                print("Product#", counter)
                csv_writer.writerow(product.values())
                counter += 1
            except Exception as e:
                print("Error:",product["name"])
                print(e)
            
