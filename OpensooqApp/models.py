from django.db import models

class Product(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.CharField(max_length=20)
    category = models.CharField(max_length=255)
    subcategory = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    post_url = models.URLField()
    currency = models.CharField(max_length=10)
    city = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=255, null= True)
    attributes = models.TextField()
    seller_data = models.TextField()
    media = models.TextField()
    
