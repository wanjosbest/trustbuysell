from django.contrib import admin
from .models import Wallet, Transaction, Payment, BankAccount, Withdrawal


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__username', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet', 'amount', 'reference', 'verified', 'created_at')
    list_filter = ('verified', 'created_at')
    search_fields = ('user__username', 'reference')
    readonly_fields = ('reference', 'created_at')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_name', 'account_number', 'bank_code', 'verified')
    list_filter = ('verified',)
    search_fields = ('user__username', 'account_number', 'account_name')


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet', 'amount', 'status', 'created_at', 'reference')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'reference')
    readonly_fields = ('reference', 'created_at')
