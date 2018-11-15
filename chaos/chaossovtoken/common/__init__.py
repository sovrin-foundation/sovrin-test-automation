from enum import Enum

class SovtokenStrategy(Enum):
    """
    All supported sovtoken workflow strategies.
    """
    # CLI
    CLI = 1
    # SDK (Not Yet Implemented - NYI)
    SDK = 2

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

# Chaos defaults
# Please keep defaults in lexically acending order by name
DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_PATH="/usr/lib/libsovtoken.so"
DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_INITIALIZER="sovtoken_init"

DEFAULT_CHAOS_PAYMENT_DICT = {
    1: {
        "seed": "000000000000000000000000000Seed1",
        "payment_method": "sov",
        "address": "pay:sov:24AE7WLojJd3Z22L6CAY876cLbGskZd3N4ocaE9T1jwX6MXtvP"
    },
    2: {
        "seed": "000000000000000000000000000Seed2",
        "payment_method": "sov",
        "address": "pay:sov:2ViUZnYGwYxx2EztvxAYq8re9ysmCVbzF72jTCXMKzrxUqGqut"
    }
}
DEFAULT_CHAOS_PAYMENT_ADDRESS1=DEFAULT_CHAOS_PAYMENT_DICT[1]["address"]
DEFAULT_CHAOS_PAYMENT_ADDRESS_METHOD1=DEFAULT_CHAOS_PAYMENT_DICT[1]["payment_method"]
DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED1=DEFAULT_CHAOS_PAYMENT_DICT[1]["seed"]
DEFAULT_CHAOS_PAYMENT_ADDRESS2=DEFAULT_CHAOS_PAYMENT_DICT[2]["address"]
DEFAULT_CHAOS_PAYMENT_ADDRESS_METHOD2=DEFAULT_CHAOS_PAYMENT_DICT[2]["payment_method"]
DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED2=DEFAULT_CHAOS_PAYMENT_DICT[2]["seed"]
