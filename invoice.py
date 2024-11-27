from django.db import models
import uuid
from compliance import InvoiceComplianceManager, MerchantComplianceProfile

class Invoice(models.Model):
    Status = []

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_title = models.CharField(max_length=255, null=True)
    invoice_number = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, null=True)
    # service_fee_payer = models.CharField(max_length=20, choices=Service_Fee_Payer.choices, default=Service_Fee_Payer.MERCHANT, null=True)
    merchant = models.IntegerField(null=True)
    # business_id = models.ForeignKey(TempBusiness, on_delete=models.CASCADE, null=True)
    is_paid = models.BooleanField(default=False)
    payment_due_date = models.DateField(null=True, blank=True)
    customer_notes = models.TextField(null=True)
    # projects = models.ManyToManyField(Project,related_name="invoice_projects", blank=True)
    # customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_link = models.URLField(null=True, blank=True)
    currency = models.CharField(max_length=5, default="USD")
    send_date = models.DateField(null=True, blank=True)
    reason_for_rejection = models.TextField(null=True,blank=True)

    # new fields to track flagging and review
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(null=True, blank=True)
    compliance_review_required = models.BooleanField(default=False)
    
    objects = InvoiceComplianceManager()
    
    def run_compliance_checks(self):

        #  New Account (0 transactions): Manual review for first 10 transactions
        #  Low Trust (Score < 2 or < 11 transactions): Manual review for all transactions
        #  Medium Trust (Score 2-3.5, >= 11 transactions): Auto approve up to $1000, manual review above
        #  High Trust (Score > 3.5, >= 11 transactions): Auto approve up to $5000, manual review above
        try:
            merchant_profile, created = MerchantComplianceProfile.objects.get_or_create(
                merchant_id=self.merchant
            )
            merchant_profile.update_trust_score()
            if merchant_profile.trust_score <= 0 and merchant_profile.total_successful_transactions < 10:
                self.compliance_review_required = True
                self.status = self.status.IN_REVIEW
            # Determine review requirements based on trust score
            elif merchant_profile.trust_score < 2 and merchant_profile.total_successful_transactions < 11 :
                self.compliance_review_required = True
                self.status = self.status.IN_REVIEW
            elif ( merchant_profile.trust_score > 2 and merchant_profile.trust_score <= 3.5)and merchant_profile.total_successful_transactions > 11:
                if self.total_amount <= 1000:
                    self.compliance_review_required= False
                    self.status = "Approved"
                else:
                    self.compliance_review_required = True
                    self.status = self.status.IN_REVIEW
            else:
                if self.total_amount <= 5000:
                    self.compliance_review_required= False
                    self.status = "Approved"
                else:
                    self.compliance_review_required = True
                    self.status = self.status.IN_REVIEW

        except Exception as e:
            print(f"Trust score calculation error: {e}")
        
        # 2. Invoice Amount Flagging
        merchant_stats = self.objects.calculate_merchant_invoice_statistics(self.merchant)
        
        if merchant_stats:
            # Flag logic based on statistical deviation
            mean = merchant_stats['mean']
            std_dev = merchant_stats['std_dev']
            
            if (self.total_amount > mean + (2 * std_dev) or 
                self.total_amount < mean - (2 * std_dev)):
                self.is_flagged = True
                self.flag_reason = "Invoice amount deviates significantly from merchant's typical transactions"
                self.status = self.status.IN_REVIEW
            
    
    def save(self, *args, **kwargs):

        # Run compliance checks before saving
        self.run_compliance_checks()
        
        # Generate invoice number if not exists
        if not self.invoice_number:
            self.invoice_number = self.generate_unique_invoice_number()
        
        super().save(*args, **kwargs)
    
    def get_compliance_status(self):
        """
        Return detailed compliance information
        """
        return {
            'is_flagged': self.is_flagged,
            'flag_reason': self.flag_reason,
            'review_required': self.compliance_review_required,
            'current_status': self.status
        }
