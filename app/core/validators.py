"""Security validators for input sanitization and validation"""

import html
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


class InputSanitizer:
    """Sanitizer for text input to prevent XSS and injection attacks"""

    # Dangerous patterns that should be removed
    # Updated to handle malformed tags like </script > with spaces
    SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
    TAG_PATTERN = re.compile(r"<[^>]+>")
    JAVASCRIPT_PATTERN = re.compile(
        r"javascript:|on\w+\s*=", re.IGNORECASE
    )

    @classmethod
    def sanitize_text(cls, text: Optional[str], max_length: Optional[int] = None) -> Optional[str]:
        """
        Sanitize text input by:
        1. Removing script tags
        2. Removing javascript: URLs and event handlers
        3. Removing HTML tags
        4. Escaping HTML entities (done last to preserve patterns for removal)
        5. Trimming whitespace
        6. Enforcing max length

        Args:
            text: The text to sanitize
            max_length: Maximum allowed length for the text

        Returns:
            Sanitized text or None if input is None
        """
        if text is None:
            return None

        # Convert to string if not already
        text = str(text)

        # Remove script tags first (before escaping)
        text = cls.SCRIPT_PATTERN.sub("", text)

        # Remove javascript: URLs and event handlers (before escaping)
        text = cls.JAVASCRIPT_PATTERN.sub("", text)

        # Remove HTML tags (before escaping)
        text = cls.TAG_PATTERN.sub("", text)

        # Escape HTML entities (done last to ensure patterns can match)
        text = html.escape(text, quote=True)

        # Trim whitespace
        text = text.strip()

        # Enforce max length
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text


class DecimalValidator:
    """Validator for decimal amounts to prevent precision-based attacks"""

    # Maximum allowed values for financial amounts
    MAX_TOTAL_DIGITS = 15  # Maximum total digits (e.g., 9,999,999,999.99)
    MAX_DECIMAL_PLACES = 2  # Maximum decimal places for currency
    MAX_AMOUNT = Decimal("9999999999.99")  # ~10 billion
    MIN_AMOUNT = Decimal("0.00")

    @classmethod
    def validate_financial_amount(
        cls,
        amount: Decimal,
        field_name: str = "amount",
        allow_zero: bool = True,
        max_amount: Optional[Decimal] = None,
    ) -> Decimal:
        """
        Validate a financial amount for:
        1. Correct type (Decimal)
        2. Non-negative value
        3. Maximum decimal places (2)
        4. Maximum total digits
        5. Reasonable maximum value

        Args:
            amount: The amount to validate
            field_name: Name of the field for error messages
            allow_zero: Whether to allow zero values
            max_amount: Custom maximum amount (overrides default)

        Returns:
            The validated amount

        Raises:
            ValueError: If validation fails
        """
        # Check type
        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except (InvalidOperation, ValueError, TypeError) as e:
                raise ValueError(
                    f"{field_name} must be a valid decimal number: {str(e)}"
                )

        # Check for special values
        if amount.is_nan() or amount.is_infinite():
            raise ValueError(f"{field_name} cannot be NaN or infinite")

        # Check minimum value
        if not allow_zero and amount <= cls.MIN_AMOUNT:
            raise ValueError(f"{field_name} must be greater than 0")
        elif amount < cls.MIN_AMOUNT:
            raise ValueError(f"{field_name} cannot be negative")

        # Check maximum value
        max_val = max_amount if max_amount is not None else cls.MAX_AMOUNT
        if amount > max_val:
            raise ValueError(
                f"{field_name} cannot exceed {max_val}"
            )

        # Check decimal places
        # Convert to tuple representation to check decimal places
        sign, digits, exponent = amount.as_tuple()

        # If exponent is negative, it represents decimal places
        if exponent < 0:
            decimal_places = abs(exponent)
            if decimal_places > cls.MAX_DECIMAL_PLACES:
                raise ValueError(
                    f"{field_name} cannot have more than {cls.MAX_DECIMAL_PLACES} decimal places"
                )

        # Check total digits
        total_digits = len(digits)
        if total_digits > cls.MAX_TOTAL_DIGITS:
            raise ValueError(
                f"{field_name} cannot have more than {cls.MAX_TOTAL_DIGITS} total digits"
            )

        # Normalize to exactly 2 decimal places
        return amount.quantize(Decimal("0.01"))

    @classmethod
    def validate_unit_price(cls, price: Decimal) -> Decimal:
        """Validate a unit price (must be > 0)"""
        return cls.validate_financial_amount(
            price, field_name="unit_price", allow_zero=False
        )

    @classmethod
    def validate_total_amount(cls, amount: Decimal) -> Decimal:
        """Validate a total amount (can be 0 for discounts, etc.)"""
        return cls.validate_financial_amount(
            amount, field_name="total_amount", allow_zero=True
        )

    @classmethod
    def validate_quantity(cls, quantity: int, field_name: str = "quantity") -> int:
        """
        Validate a quantity value

        Args:
            quantity: The quantity to validate
            field_name: Name of the field for error messages

        Returns:
            The validated quantity

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(quantity, int):
            raise ValueError(f"{field_name} must be an integer")

        if quantity < 1:
            raise ValueError(f"{field_name} must be at least 1")

        if quantity > 10000:
            raise ValueError(f"{field_name} cannot exceed 10,000")

        return quantity
