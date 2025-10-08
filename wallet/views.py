import requests
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, Payment
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required
def wallet_dashboard(request):
    wallet = request.user.wallet  # Each user automatically has a wallet
    transactions = wallet.transactions.order_by('-created_at')  # Recent first
    return render(request, 'wallet/dashboard.html', {
        'wallet': wallet,
        'transactions': transactions
    })


@login_required
def fund_wallet(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        wallet = request.user.wallet

        # Create payment record
        payment = Payment.objects.create(user=request.user, wallet=wallet, amount=amount)

        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        data = {
            'email': request.user.email,
            'amount': payment.amount_value(),
            'reference': payment.reference,
            'callback_url': request.build_absolute_uri('/wallet/verify-payment/')
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=data)
        res = response.json()

        if res.get('status'):
            return redirect(res['data']['authorization_url'])
        else:
            messages.error(request, "Payment initialization failed.")
            return redirect('wallet_dashboard')

    return render(request, 'wallet/fund.html')


@login_required
def verify_payment(request):
    reference = request.GET.get('reference')
    if not reference:
        return render(request, 'wallet/payment_failed.html', {"error": "Missing payment reference."})

    payment = get_object_or_404(Payment, reference=reference, user=request.user)

    if payment.verified:
        return render(request, 'wallet/payment_success.html', {"payment": payment})

    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    verify_url = f'https://api.paystack.co/transaction/verify/{reference}'
    response = requests.get(verify_url, headers=headers)
    res = response.json()

    if res.get('status') and res['data']['status'] == 'success':
        payment.verified = True
        payment.save()

        # Credit wallet automatically
        wallet = payment.wallet
        wallet.credit(payment.amount, description=f"Paystack Funding ({reference})")

        return render(request, 'wallet/payment_success.html', {"payment": payment})
    else:
        return render(request, 'wallet/payment_failed.html', {"error": "Verification failed."})

import secrets
from django.contrib import messages
from .models import Wallet, BankAccount, Withdrawal

@login_required
def withdraw_wallet(request):
    wallet = request.user.wallet
    bank_account = getattr(request.user, 'bank_account', None)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        if not bank_account or not bank_account.verified:
            messages.error(request, "You must verify your bank account first.")
            return redirect('withdraw_wallet')

        if amount > wallet.balance:
            messages.error(request, "Insufficient balance.")
            return redirect('withdraw_wallet')

        # Create withdrawal record
        withdrawal = Withdrawal.objects.create(
            user=request.user,
            wallet=wallet,
            amount=amount,
            reference=secrets.token_hex(8).upper(),
            status='processing'
        )

        # Debit user wallet
        wallet.debit(amount, description="Withdrawal to bank")

        # Call Paystack Transfer API
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}

        # 1. Create recipient
        recipient_url = f'https://api.paystack.co/transferrecipient'
        recipient_data = {
            "type": "nuban",
            "name": bank_account.account_name,
            "account_number": bank_account.account_number,
            "bank_code": bank_account.bank_code,
            "currency": "NGN"
        }
        r = requests.post(recipient_url, headers=headers, data=recipient_data).json()

        if not r.get('status'):
            withdrawal.status = 'failed'
            withdrawal.reason = "Recipient creation failed"
            withdrawal.save()
            messages.error(request, "Failed to create transfer recipient.")
            return redirect('wallet_dashboard')

        recipient_code = r['data']['recipient_code']

        # 2. Initiate transfer
        transfer_url = f'https://api.paystack.co/transfer'
        transfer_data = {
            "source": "balance",
            "amount": int(amount * 100),  # kobo
            "recipient": recipient_code,
            "reason": "Wallet withdrawal",
            "reference": withdrawal.reference
        }
        t = requests.post(transfer_url, headers=headers, data=transfer_data).json()

        if t.get('status'):
            withdrawal.status = 'success'
            withdrawal.save()
            messages.success(request, f"₦{amount} withdrawn successfully to {bank_account.account_name}.")
        else:
            withdrawal.status = 'failed'
            withdrawal.reason = "Transfer failed"
            withdrawal.save()
            messages.error(request, "Withdrawal failed. Please contact support.")

        return redirect('wallet_dashboard')

    return render(request, 'wallet/withdraw.html', {'wallet': wallet, 'bank_account': bank_account})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BankAccount

@login_required
def add_bank_account(request):
    """Allow user to add or update their bank account"""
    try:
        bank_account = request.user.bank_account  # via related_name
    except BankAccount.DoesNotExist:
        bank_account = None

    if request.method == "POST":
        account_name = request.POST.get("account_name")
        account_number = request.POST.get("account_number")
        bank_code = request.POST.get("bank_code")

        if not (account_name and account_number and bank_code):
            messages.error(request, "All fields are required.")
            return redirect("add_bank_account")

        if bank_account:
            # Update existing account
            bank_account.account_name = account_name
            bank_account.account_number = account_number
            bank_account.bank_code = bank_code
            bank_account.save()
            messages.success(request, "Bank account updated successfully.")
        else:
            # Create new account
            BankAccount.objects.create(
                user=request.user,
                account_name=account_name,
                account_number=account_number,
                bank_code=bank_code,
                verified = True,
            )
            messages.success(request, "Bank account added successfully.")
        return redirect("add_bank_account")

    context = {
        "bank_account": bank_account,
    }
    return render(request, "wallet/add_bank_account.html", context)
