
__all__ = ["Receipt"]


class Receipt:
    """This class holds the receipt for a provisional transaction. This is sent
       by the credited account to receipt that the service has been performed,
       and thus payment that is held as liability should now be paid. OR it
       sends back the fact that the service was not performed, and so the
       refund should be issued
    """
    def __init__(self, transaction_uid=None, authorisation=None,
                 receipted_value=None):
        """Create a receipt for the transaction with the passed UID. This will
           receipt the full value of the transaction, unless 'receipted_value'
           is passed, in which case only that value will be receipted (and the
           rest of the liability will be cancelled). Note that you cannot
           receipt for more than the value of the original transaction
        """
        # lots to do here!