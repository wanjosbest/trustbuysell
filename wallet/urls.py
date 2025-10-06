from django.urls import path
from . import views

urlpatterns = [
    path('wallet-dashboard/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/fund/', views.fund_wallet, name='fund_wallet'),
    path('wallet/verify-payment/', views.verify_payment, name='verify-payment'),
    path('withdraw/', views.withdraw_wallet, name='withdraw_wallet'),

]
