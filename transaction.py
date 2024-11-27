from django.db import models
from uuid import uuid4
from invoice import Invoice, MerchantComplianceProfile
from rest_framework.views import APIView

class Transactions(models.Model):
    CURRENCY_CHOICES = [
        ("USD", "USD"),
        # ("NGN", "NGN"),
        # ("GHC", "GHC"),
    ]

    STATUS_CHOICES = [
        ("Successful", "Successful"),
        ("Failed", "Failed"),
        ("Pending", "Pending"),
    ]

    PAYMENT_METHOD_CHOICES = [

        ("Stripe", "Stripe"),
        ("SEPA", "SEPA"),

    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=256, null=True)
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, null=True, blank=True)
    # Foreign keys for Invoice and PaymentLink
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    payment_date = models.DateTimeField(null=True)





class ProceessTransaction(APIView):

    def get(self, request):
        event = "event from either SEPA or Stripe"
        self.update_marchant_compliance_profile(event)

    def update_marchant_compliance_profile(self, event):
        reference = event['reference']
        transaction = Transactions.objects.get(reference=reference)
        merchant_compliance_profile =  MerchantComplianceProfile.objects.get(merchant=transaction.invoice.merchant)
        if event['status'] == "success":
            merchant_compliance_profile.total_successful_transactions += 1
        elif event['status'] == "failed":
            merchant_compliance_profile.total_failed_transactions += 1

        merchant_compliance_profile.save()





    





