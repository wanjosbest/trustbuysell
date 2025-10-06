from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s wallet - ₦{self.balance}"

    def credit(self, amount, description=""):
        """Add money to wallet"""
        self.balance += amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            description=description
        )

    def debit(self, amount, description=""):
        """Remove money from wallet"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            Transaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type='debit',
                description=description
            )
        else:
            raise ValueError("Insufficient balance")
        

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type.title()} ₦{self.amount} - {self.wallet.user.username}"
    
import secrets
from decimal import Decimal

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - ₦{self.amount} ({'Verified' if self.verified else 'Pending'})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = secrets.token_hex(8).upper()
        super().save(*args, **kwargs)

    def amount_value(self):
        """Convert amount to kobo (Paystack uses kobo)"""
        return int(self.amount * Decimal('100'))
    
import requests

class BankAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_account')
    account_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=15)
    bank_code = models.CharField(max_length=10)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.account_name} ({self.account_number})"


class Withdrawal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - ₦{self.amount} ({self.status})"

