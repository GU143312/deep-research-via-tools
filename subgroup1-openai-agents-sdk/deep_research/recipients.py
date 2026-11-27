"""Validate the recipient supplied for this research run."""

from email.errors import HeaderParseError
from email.headerregistry import Address


class RecipientError(ValueError):
    pass


def validate_recipient(value: str, *, required: bool = False) -> str:
    if "\r" in value or "\n" in value:
        raise RecipientError("Enter one valid recipient email address.")
    value = value.strip()
    if not value:
        if required:
            raise RecipientError("Email delivery is enabled. Enter a recipient in Email settings.")
        return ""
    try:
        address = Address(addr_spec=value)
        if not address.username or not address.domain or len(value) > 254:
            raise ValueError
        value.encode("ascii")
    except (ValueError, IndexError, UnicodeError, HeaderParseError):
        raise RecipientError("Enter one valid recipient email address.") from None
    return address.addr_spec
