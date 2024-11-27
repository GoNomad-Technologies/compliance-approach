import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count
from statistics import mean, stdev

class MerchantComplianceProfile(models.Model):
    """
    Tracks merchant's compliance and transaction history
    """
    merchant = models.IntegerField()
    total_successful_transactions = models.IntegerField(default=0)
    total_failed_transactions = models.IntegerField(default=0)
    account_created_date = models.DateField(auto_now_add=True)
    trust_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.0
    )
    
    @property
    def account_age_months(self):
        """Calculate account age in months"""
        return (timezone.now().date() - self.account_created_date).days / 30

    def update_trust_score(self):
        """
        Calculate and update merchant's trust score
        """
        # Transaction History (50% weight)
        transaction_history_score = (
            self.total_successful_transactions * 1 - 
            self.total_failed_transactions * 2
        )
        
        # Active Account Age (15% weight)
        account_age_score = 0
        if self.account_age_months <= 3 and self.total_successful_transactions >= 1:
            account_age_score = 1
        elif 3 < self.account_age_months <= 6 and self.total_successful_transactions >= 3:
            account_age_score = 2
        elif 6 < self.account_age_months <= 12 and self.total_successful_transactions >= 6:
            account_age_score = 3
        elif self.account_age_months > 12 and self.total_successful_transactions >= 12:
            account_age_score = 4
        
        # Additional scoring factors would be implemented here
        
        # Calculate Total Trust Score
        trust_score = (
            transaction_history_score * 0.5 + 
            account_age_score * 0.15
        )
        
        self.trust_score = max(0, min(trust_score, 5))  # Normalize to 0-5 range
        self.save()
        return self.trust_score



class InvoiceComplianceManager(models.Manager):
    """
    Custom manager for Invoice model to handle compliance-related operations
    """
    def calculate_merchant_invoice_statistics(self, merchant_id):
        """
        Calculate statistical metrics for a merchant's invoices
        """
        invoices = self.filter(merchant=merchant_id)
        
        if invoices.count() < 10:
            return None
        
        amounts = list(invoices.values_list('total_amount', flat=True))
        
        return {
            'mean': mean(amounts),
            'std_dev': stdev(amounts) if len(amounts) > 1 else 0,
            'frequency': invoices.count(),
            'max_invoice': max(amounts)
        }

