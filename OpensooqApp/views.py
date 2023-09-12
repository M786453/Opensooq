from django.shortcuts import render
from django.http import HttpResponse
from OpensooqApp.models import Product
# Create your views here.

def opensooq(request):

    try:

        with open("products_data.json", "r") as d:

            products_data = d.read()

        return HttpResponse(products_data)
    except:
        return HttpResponse("Data is currently being scraped. Wait...")