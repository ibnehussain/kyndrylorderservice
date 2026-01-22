"""Unit tests for security validators"""

from decimal import Decimal

import pytest

from app.core.validators import DecimalValidator, InputSanitizer


class TestInputSanitizer:
    """Test cases for InputSanitizer"""

    def test_sanitize_text_basic(self):
        """Test basic text sanitization"""
        text = "Hello World"
        result = InputSanitizer.sanitize_text(text)
        assert result == "Hello World"

    def test_sanitize_text_with_html_tags(self):
        """Test sanitization removes HTML tags"""
        text = "<div>Hello World</div>"
        result = InputSanitizer.sanitize_text(text)
        assert "<div>" not in result
        assert "</div>" not in result
        # HTML entities should be escaped
        assert result == "&lt;div&gt;Hello World&lt;/div&gt;"

    def test_sanitize_text_with_script_tags(self):
        """Test sanitization removes script tags"""
        text = "<script>alert('XSS')</script>Hello"
        result = InputSanitizer.sanitize_text(text)
        assert "<script>" not in result
        assert "</script>" not in result
        # After HTML escaping, the text is safe even if 'alert' remains as text
        assert "Hello" in result

    def test_sanitize_text_with_javascript_url(self):
        """Test sanitization removes javascript: URLs"""
        text = "javascript:alert('XSS')"
        result = InputSanitizer.sanitize_text(text)
        assert "javascript:" not in result

    def test_sanitize_text_with_event_handlers(self):
        """Test sanitization removes event handlers"""
        text = "onclick=alert('XSS')"
        result = InputSanitizer.sanitize_text(text)
        assert "onclick=" not in result

    def test_sanitize_text_with_mixed_attacks(self):
        """Test sanitization with multiple attack vectors"""
        text = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
        result = InputSanitizer.sanitize_text(text)
        assert "<script>" not in result
        assert "</script>" not in result
        assert "onerror=" not in result
        # Tags are escaped/removed, text may remain but is safe

    def test_sanitize_text_preserves_safe_content(self):
        """Test that safe content is preserved"""
        text = "Product: Widget 2000"
        result = InputSanitizer.sanitize_text(text)
        assert result == "Product: Widget 2000"

    def test_sanitize_text_with_special_chars(self):
        """Test sanitization with special characters"""
        text = "Price: $29.99 & Free Shipping!"
        result = InputSanitizer.sanitize_text(text)
        # HTML entities should be escaped
        assert "&amp;" in result  # & becomes &amp;
        assert "Price:" in result
        assert "29.99" in result

    def test_sanitize_text_trims_whitespace(self):
        """Test that leading/trailing whitespace is trimmed"""
        text = "  Hello World  "
        result = InputSanitizer.sanitize_text(text)
        assert result == "Hello World"

    def test_sanitize_text_max_length(self):
        """Test max length enforcement"""
        text = "A" * 100
        result = InputSanitizer.sanitize_text(text, max_length=50)
        assert len(result) == 50

    def test_sanitize_text_none_input(self):
        """Test sanitization with None input"""
        result = InputSanitizer.sanitize_text(None)
        assert result is None

    def test_sanitize_text_empty_string(self):
        """Test sanitization with empty string"""
        result = InputSanitizer.sanitize_text("")
        assert result == ""

    def test_sanitize_text_converts_to_string(self):
        """Test that non-string input is converted"""
        result = InputSanitizer.sanitize_text(12345)
        assert result == "12345"


class TestDecimalValidator:
    """Test cases for DecimalValidator"""

    def test_validate_financial_amount_valid(self):
        """Test validation of valid financial amount"""
        amount = Decimal("29.99")
        result = DecimalValidator.validate_financial_amount(amount)
        assert result == Decimal("29.99")

    def test_validate_financial_amount_zero(self):
        """Test validation allows zero when allow_zero=True"""
        amount = Decimal("0.00")
        result = DecimalValidator.validate_financial_amount(amount, allow_zero=True)
        assert result == Decimal("0.00")

    def test_validate_financial_amount_zero_not_allowed(self):
        """Test validation rejects zero when allow_zero=False"""
        amount = Decimal("0.00")
        with pytest.raises(ValueError, match="must be greater than 0"):
            DecimalValidator.validate_financial_amount(amount, allow_zero=False)

    def test_validate_financial_amount_negative(self):
        """Test validation rejects negative amounts"""
        amount = Decimal("-10.00")
        with pytest.raises(ValueError, match="cannot be negative"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_too_many_decimals(self):
        """Test validation rejects amounts with too many decimal places"""
        amount = Decimal("29.999")
        with pytest.raises(ValueError, match="cannot have more than 2 decimal places"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_normalizes(self):
        """Test validation normalizes to 2 decimal places"""
        amount = Decimal("29.9")
        result = DecimalValidator.validate_financial_amount(amount)
        assert result == Decimal("29.90")

    def test_validate_financial_amount_exceeds_max(self):
        """Test validation rejects amounts exceeding maximum"""
        amount = Decimal("99999999999.99")
        with pytest.raises(ValueError, match="cannot exceed"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_too_many_digits(self):
        """Test validation rejects amounts with too many total digits"""
        # 16 digits total (exceeds limit of 15)
        amount = Decimal("9999999999999.99")
        with pytest.raises(ValueError, match="cannot exceed"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_nan(self):
        """Test validation rejects NaN values"""
        amount = Decimal("NaN")
        with pytest.raises(ValueError, match="cannot be NaN or infinite"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_infinity(self):
        """Test validation rejects infinite values"""
        amount = Decimal("Infinity")
        with pytest.raises(ValueError, match="cannot be NaN or infinite"):
            DecimalValidator.validate_financial_amount(amount)

    def test_validate_financial_amount_from_string(self):
        """Test validation can convert from string"""
        result = DecimalValidator.validate_financial_amount("29.99")
        assert result == Decimal("29.99")

    def test_validate_financial_amount_from_float(self):
        """Test validation can convert from float"""
        result = DecimalValidator.validate_financial_amount(29.99)
        assert result == Decimal("29.99")

    def test_validate_financial_amount_invalid_string(self):
        """Test validation rejects invalid string"""
        with pytest.raises(ValueError, match="must be a valid decimal number"):
            DecimalValidator.validate_financial_amount("not_a_number")

    def test_validate_financial_amount_custom_max(self):
        """Test validation with custom maximum"""
        amount = Decimal("1000.00")
        with pytest.raises(ValueError, match="cannot exceed 500.00"):
            DecimalValidator.validate_financial_amount(
                amount, max_amount=Decimal("500.00")
            )

    def test_validate_unit_price_valid(self):
        """Test unit price validation for valid price"""
        price = Decimal("29.99")
        result = DecimalValidator.validate_unit_price(price)
        assert result == Decimal("29.99")

    def test_validate_unit_price_zero(self):
        """Test unit price validation rejects zero"""
        price = Decimal("0.00")
        with pytest.raises(ValueError, match="must be greater than 0"):
            DecimalValidator.validate_unit_price(price)

    def test_validate_total_amount_valid(self):
        """Test total amount validation for valid amount"""
        amount = Decimal("99.99")
        result = DecimalValidator.validate_total_amount(amount)
        assert result == Decimal("99.99")

    def test_validate_total_amount_zero(self):
        """Test total amount validation allows zero"""
        amount = Decimal("0.00")
        result = DecimalValidator.validate_total_amount(amount)
        assert result == Decimal("0.00")

    def test_validate_quantity_valid(self):
        """Test quantity validation for valid quantity"""
        quantity = 5
        result = DecimalValidator.validate_quantity(quantity)
        assert result == 5

    def test_validate_quantity_zero(self):
        """Test quantity validation rejects zero"""
        with pytest.raises(ValueError, match="must be at least 1"):
            DecimalValidator.validate_quantity(0)

    def test_validate_quantity_negative(self):
        """Test quantity validation rejects negative"""
        with pytest.raises(ValueError, match="must be at least 1"):
            DecimalValidator.validate_quantity(-1)

    def test_validate_quantity_too_large(self):
        """Test quantity validation rejects extremely large values"""
        with pytest.raises(ValueError, match="cannot exceed 10,000"):
            DecimalValidator.validate_quantity(10001)

    def test_validate_quantity_not_integer(self):
        """Test quantity validation rejects non-integers"""
        with pytest.raises(ValueError, match="must be an integer"):
            DecimalValidator.validate_quantity(5.5)
