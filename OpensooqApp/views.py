from django.shortcuts import render
from django.http import HttpResponse
from OpensooqApp.models import Product
# Create your views here.

def opensooq(request):

    return HttpResponse(Product.objects.all().values())