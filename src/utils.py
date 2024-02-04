from enum import Enum


class EntryTypes(Enum):
    """
    Enum to represent the different types of entries
    """
    SCHEDULE_OF_NOTICES_OF_LEASES = "Schedule of Notices of Leases"
    CANCELLED_ITEM_SCHEDULE_OF_NOTICES_OF_LEASES = "Cancelled Item - Schedule of Notices of Leases"


class LeaseEntryError(ValueError, TypeError, AttributeError):
    def __init__(self, message="Invalid data received"):
        self.message = message
        super().__init__(self.message)