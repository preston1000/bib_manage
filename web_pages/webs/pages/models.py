from django.db import models


# Create your models here.
class Publication(models.Model):
    author = models.CharField(max_length=100)
    venue = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    year = models.IntegerField()
    venue_type = models.CharField(max_length=10)
    issue = models.IntegerField()
    number = models.IntegerField()
    place = models.CharField(max_length=100)
    start_page = models.IntegerField()
    end_page = models.IntegerField()


class Person(models.Model):
    first_name = models.CharField(max_length=20)
    middle_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    current_affiliation = models.CharField(max_length=100)
    position = models.CharField(max_length=20)
    identifier = models.CharField(max_length=100)


class Venue(models.Model):
    name = models.CharField(max_length=100)
    start_year = models.IntegerField()
    type = models.CharField(max_length=10)
    publisher = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)


class Affiliation(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    place = models.CharField(max_length=100)


class Place(models.Model):
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)

