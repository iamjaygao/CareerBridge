from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('create-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('confirm/', views.confirm_payment, name='confirm_payment'),
    path('list/', views.PaymentListView.as_view(), name='payment_list'),
    path('detail/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('refund/<int:payment_id>/', views.process_refund, name='process_refund'),
    
    # Payment methods
    path('methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='payment_method_detail'),
    path('methods/<int:method_id>/delete/', views.delete_payment_method, name='delete_payment_method'),
    
    # Refunds
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('refunds/<int:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),
    
    # Statistics
    path('statistics/', views.payment_statistics, name='payment_statistics'),
    
    # Webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('webhooks/paypal/', views.paypal_webhook, name='paypal_webhook'),
] 