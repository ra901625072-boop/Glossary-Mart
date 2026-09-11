"""
Application-wide constants, enumerations, and shared configuration values.

Import from here instead of hardcoding strings throughout the codebase.
"""
import enum


# ---------------------------------------------------------------------------
# Order & Payment Enumerations
# ---------------------------------------------------------------------------

class OrderStatus(str, enum.Enum):
    """Valid order lifecycle states."""
    PENDING = "Pending"
    PROCESSING = "Processing"
    PACKED = "Packed"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    RETURNED = "Returned"


class PaymentStatus(str, enum.Enum):
    """Valid payment states for an order."""
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class PaymentMethod(str, enum.Enum):
    """Supported payment methods."""
    COD = "COD"        # Cash on Delivery
    UPI = "UPI"        # Unified Payments Interface
    CARD = "CARD"      # Credit / Debit card (Stripe)
    UDHAR = "UDHAR"    # Store credit (Udhar / credit tab)


# ---------------------------------------------------------------------------
# Order State Machine — defines valid forward transitions
# ---------------------------------------------------------------------------

ORDER_STATUS_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING:          {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING:       {OrderStatus.PACKED, OrderStatus.CANCELLED},
    OrderStatus.PACKED:           {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED, OrderStatus.RETURNED},
    OrderStatus.DELIVERED:        {OrderStatus.RETURNED},
    OrderStatus.CANCELLED:        set(),   # Terminal state
    OrderStatus.RETURNED:         set(),   # Terminal state
}

# ---------------------------------------------------------------------------
# Query / Pagination Limits
# ---------------------------------------------------------------------------

MAX_SALES_HISTORY = 100      # Max rows returned in sales history
MAX_ACTIVITY_LOG = 200       # Max rows returned in activity log
MAX_NOTIFICATIONS = 20       # Max notifications returned in bell dropdown
MIN_SEARCH_LENGTH = 2        # Min characters before live-search fires
MAX_SEARCH_RESULTS = 5       # Max results for live-search suggestions

# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_CUSTOMER = "customer"
