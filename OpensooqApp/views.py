from django.shortcuts import render
from django.http import HttpResponse
from OpensooqApp.models import Product
# Create your views here.

def opensooq(request):

    with open("products_data.json", "r") as d:

        products_data = d.read()

    return HttpResponse(products_data)