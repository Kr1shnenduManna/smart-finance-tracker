from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Transaction


@receiver(pre_save, sender=Transaction)
def store_old_transaction(sender, instance, **kwargs):
    """Store old transaction values before update"""
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_amount = old.amount
            instance._old_type = old.transaction_type
            instance._old_account = old.account
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def update_account_balance_on_save(sender, instance, created, **kwargs):
    """Update account balance when transaction is created or updated"""
    if created:
        # New transaction
        if instance.transaction_type == 'income':
            instance.account.balance += instance.amount
        else:
            instance.account.balance -= instance.amount
        instance.account.save()
    else:
        # Updated transaction - reverse old and apply new
        if hasattr(instance, '_old_amount') and hasattr(instance, '_old_type'):
            old_account = getattr(instance, '_old_account', instance.account)
            
            # Reverse old transaction
            if instance._old_type == 'income':
                old_account.balance -= instance._old_amount
            else:
                old_account.balance += instance._old_amount
            
            # Apply new transaction
            if instance.transaction_type == 'income':
                instance.account.balance += instance.amount
            else:
                instance.account.balance -= instance.amount
            
            # Save both accounts if they differ
            if old_account != instance.account:
                old_account.save()
            instance.account.save()


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_delete(sender, instance, **kwargs):
    """Update account balance when transaction is deleted"""
    # Reverse the transaction
    if instance.transaction_type == 'income':
        instance.account.balance -= instance.amount
    else:
        instance.account.balance += instance.amount
    instance.account.save()
