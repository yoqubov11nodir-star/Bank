from django.db import models
from django.contrib.auth.models import User

class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class AdminAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Transaction(models.Model):
    sender = models.ForeignKey(User, related_name='sent_transactions', on_delete=models.SET_NULL, null=True)
    receiver_card = models.CharField(max_length=16)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.type}: {self.amount} UZS"