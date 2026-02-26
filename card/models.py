from django.db import models
from django.contrib.auth.models import User

class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, unique=True)
    pin_code = models.CharField(max_length=4)
    balance = models.FloatField(default=0.0)

    def __str__(self):
        return self.card_number