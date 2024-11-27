# # Signal to update merchant compliance profile after successful invoice payment
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .invoice import Invoice, MerchantComplianceProfile

# @receiver(post_save, sender=Invoice)
# def update_merchant_compliance(sender, instance, created, **kwargs):
#     """
#     Update merchant compliance profile after invoice save
#     """
#     if not created and instance.status == instance.Status.PAID:
#         try:
#             merchant_profile, _ = MerchantComplianceProfile.objects.get_or_create(
#                 merchant_id=instance.merchant
#             )
#             merchant_profile.total_successful_transactions += 1
#             merchant_profile.save()
#         except Exception as e:
#             # Log the error
#             print(f"Merchant compliance update error: {e}")