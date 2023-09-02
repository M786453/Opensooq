import json
from OpensooqApp.models import Product

with open('OpensooqCleanData.json',"r") as file:

    products = json.loads(file.read())

counter = 1
for product in products:
    print("Product#", counter)
    prod = Product(name=product["name"],description=product["description"],price=str(product["price"]),category=product["category"],subcategory=product["subcategory"],phone=str(product["phone"]),post_url=product["post_url"],currency=product["currency"],city=product["city"],neighborhood=product["neighborhood"],attributes=json.dumps(product["product_attributes"]),seller_data=json.dumps(product["seller_data"]),media=json.dumps(product["media"]))
    prod.save()

    counter += 1