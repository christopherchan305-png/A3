"""
Test Payment Mock and Stub Module - CISC 327 Assignment 3
Testing pay_late_fees() and refund_late_fee_payment() using stubbing and mocking

This module demonstrates:
1. Stubbing database functions (calculate_late_fee_for_book, get_book_by_id)
2. Mocking PaymentGateway class and its methods
3. Verifying mock interactions using assert_called_once(), assert_called_with(), assert_not_called()
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
from database import init_database
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Create a fresh database for each test."""
    os.chdir(tmp_path)
    init_database()
    yield


# ============================================================================
# TESTS FOR pay_late_fees() - 5 Test Scenarios
# ============================================================================

def test_pay_late_fees_success_positive(mocker):
    """
    Test 1: Successful payment processing (positive test)
    
    Stubs: calculate_late_fee_for_book, get_book_by_id
    Mocks: PaymentGateway.process_payment
    Verification: assert_called_once_with() to verify correct parameters
    """
    # STUB: Mock calculate_late_fee_for_book to return fake late fee data
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 5.50, 'days_overdue': 3, 'status': 'ok'}
    )
    
    # STUB: Mock get_book_by_id to return fake book data
    mocker.patch(
        'services.library_service.get_book_by_id',
        return_value={'id': 1, 'title': 'Clean Code', 'author': 'Martin', 'isbn': '1234567890123'}
    )
    
    # MOCK: Create mock PaymentGateway with spec
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123456", "Payment processed")
    
    # Execute function
    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)
    
    # Assertions
    assert success is True
    assert "Payment successful!" in message
    assert txn_id == "txn_123456"
    
    # VERIFICATION: Verify payment gateway was called exactly once with correct parameters
    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=5.50,
        description="Late fees for 'Clean Code'"
    )


def test_pay_late_fees_payment_declined_negative(mocker):
    """
    Test 2: Payment declined by gateway (negative test)
    
    Stubs: calculate_late_fee_for_book, get_book_by_id
    Mocks: PaymentGateway.process_payment (returns failure)
    Verification: assert_called_once() to verify payment was attempted
    """
    # STUB: Return late fees
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 10.00, 'days_overdue': 10, 'status': 'ok'}
    )
    
    # STUB: Return book data
    mocker.patch(
        'services.library_service.get_book_by_id',
        return_value={'id': 2, 'title': 'The Pragmatic Programmer', 'author': 'Hunt'}
    )
    
    # MOCK: PaymentGateway that declines payment
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, None, "Insufficient funds")
    
    # Execute
    success, message, txn_id = pay_late_fees("654321", 2, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Payment failed" in message
    assert "Insufficient funds" in message
    assert txn_id is None
    
    # VERIFICATION: Payment was attempted
    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_invalid_patron_id_negative(mocker):
    """
    Test 3: Invalid patron ID - verify mock NOT called (negative test)
    
    Stubs: None (validation happens before database calls)
    Mocks: PaymentGateway
    Verification: assert_not_called() to verify payment was never attempted
    """
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Test various invalid patron IDs
    invalid_ids = ["12345", "1234567", "abc123", "", None, "12345a"]
    
    for invalid_id in invalid_ids:
        mock_gateway.reset_mock()  # Reset call count for each iteration
        
        success, message, txn_id = pay_late_fees(invalid_id, 1, mock_gateway)
        
        # Assertions
        assert success is False
        assert "Invalid patron ID" in message
        assert txn_id is None
        
        # VERIFICATION: Payment gateway should NOT be called for invalid patron ID
        mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_zero_late_fees_edge_case(mocker):
    """
    Test 4: Zero late fees - verify mock NOT called (edge case)
    
    Stubs: calculate_late_fee_for_book (returns zero fee)
    Mocks: PaymentGateway
    Verification: assert_not_called() to verify payment wasn't attempted for zero fees
    """
    # STUB: Return zero late fees
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 0.0, 'days_overdue': 0, 'status': 'ok'}
    )
    
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Execute
    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)
    
    # Assertions
    assert success is False
    assert "No late fees to pay" in message
    assert txn_id is None
    
    # VERIFICATION: Payment should NOT be processed for zero fees
    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_network_error_exception(mocker):
    """
    Test 5: Network error exception handling (exception test)
    
    Stubs: calculate_late_fee_for_book, get_book_by_id
    Mocks: PaymentGateway.process_payment (raises exception)
    Verification: assert_called_once() to verify attempt was made before exception
    """
    # STUB: Return late fees
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 7.50, 'days_overdue': 5, 'status': 'ok'}
    )
    
    # STUB: Return book data
    mocker.patch(
        'services.library_service.get_book_by_id',
        return_value={'id': 3, 'title': '1984', 'author': 'Orwell'}
    )
    
    # MOCK: PaymentGateway that raises network error
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network timeout")
    
    # Execute
    success, message, txn_id = pay_late_fees("111111", 3, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Payment processing error" in message
    assert "Network timeout" in message
    assert txn_id is None
    
    # VERIFICATION: Payment was attempted before exception
    mock_gateway.process_payment.assert_called_once()


# ============================================================================
# TESTS FOR refund_late_fee_payment() - 5 Test Scenarios
# ============================================================================

def test_refund_late_fee_success_positive():
    """
    Test 6: Successful refund (positive test)
    
    Stubs: None (all validation is parameter-based)
    Mocks: PaymentGateway.refund_payment
    Verification: assert_called_once_with() to verify correct refund parameters
    """
    # MOCK: PaymentGateway with successful refund
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund of $5.00 processed successfully")
    
    # Execute
    success, message = refund_late_fee_payment("txn_123456", 5.00, mock_gateway)
    
    # Assertions
    assert success is True
    assert "processed successfully" in message
    
    # VERIFICATION: Refund was called with correct parameters
    mock_gateway.refund_payment.assert_called_once_with("txn_123456", 5.00)


def test_refund_late_fee_invalid_transaction_id_negative():
    """
    Test 7: Invalid transaction ID rejection (negative test)
    
    Stubs: None
    Mocks: PaymentGateway
    Verification: assert_not_called() for invalid transaction IDs
    """
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Test various invalid transaction IDs
    invalid_txn_ids = ["", "abc123", "transaction_123", None, "12345"]
    
    for invalid_id in invalid_txn_ids:
        mock_gateway.reset_mock()
        
        success, message = refund_late_fee_payment(invalid_id, 5.00, mock_gateway)
        
        # Assertions
        assert success is False
        assert "Invalid transaction ID" in message
        
        # VERIFICATION: Gateway should NOT be called for invalid transaction ID
        mock_gateway.refund_payment.assert_not_called()


def test_refund_late_fee_negative_amount_negative():
    """
    Test 8: Invalid refund amount - negative value (negative test)
    
    Stubs: None
    Mocks: PaymentGateway
    Verification: assert_not_called() for negative amounts
    """
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Execute with negative amount
    success, message = refund_late_fee_payment("txn_789012", -5.00, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Refund amount must be greater than 0" in message
    
    # VERIFICATION: No refund should be attempted for negative amounts
    mock_gateway.refund_payment.assert_not_called()


def test_refund_late_fee_zero_amount_edge_case():
    """
    Test 9: Invalid refund amount - zero value (edge case)
    
    Stubs: None
    Mocks: PaymentGateway
    Verification: assert_not_called() for zero amount
    """
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Execute with zero amount
    success, message = refund_late_fee_payment("txn_345678", 0.0, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Refund amount must be greater than 0" in message
    
    # VERIFICATION: No refund for zero amount
    mock_gateway.refund_payment.assert_not_called()


def test_refund_late_fee_exceeds_maximum_boundary():
    """
    Test 10: Invalid refund amount - exceeds $15 maximum (boundary test)
    
    Stubs: None
    Mocks: PaymentGateway
    Verification: assert_not_called() for amounts exceeding maximum
    """
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Test amounts exceeding maximum late fee
    excessive_amounts = [15.01, 20.00, 100.00]
    
    for amount in excessive_amounts:
        mock_gateway.reset_mock()
        
        success, message = refund_late_fee_payment("txn_999999", amount, mock_gateway)
        
        # Assertions
        assert success is False
        assert "exceeds maximum late fee" in message
        
        # VERIFICATION: No refund for excessive amounts
        mock_gateway.refund_payment.assert_not_called()


# ============================================================================
# ADDITIONAL EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_pay_late_fees_book_not_found_negative(mocker):
    """
    Test 11: Book not found in database (negative test)
    
    Stubs: calculate_late_fee_for_book, get_book_by_id (returns None)
    Mocks: PaymentGateway
    Verification: assert_not_called() when book doesn't exist
    """
    # STUB: Return late fees
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 3.00, 'days_overdue': 2, 'status': 'ok'}
    )
    
    # STUB: Book not found
    mocker.patch(
        'services.library_service.get_book_by_id',
        return_value=None
    )
    
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Execute
    success, message, txn_id = pay_late_fees("123456", 999, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Book not found" in message
    assert txn_id is None
    
    # VERIFICATION: Payment should not be attempted for non-existent book
    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_no_fee_info_returned_negative(mocker):
    """
    Test 12: calculate_late_fee_for_book returns None/invalid data (negative test)
    
    Stubs: calculate_late_fee_for_book (returns None)
    Mocks: PaymentGateway
    Verification: assert_not_called() when fee calculation fails
    """
    # STUB: Return None (calculation failed)
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value=None
    )
    
    # MOCK: PaymentGateway (should not be called)
    mock_gateway = Mock(spec=PaymentGateway)
    
    # Execute
    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Unable to calculate late fees" in message
    assert txn_id is None
    
    # VERIFICATION: Payment should not be attempted when fee calc fails
    mock_gateway.process_payment.assert_not_called()


def test_refund_late_fee_gateway_failure_negative():
    """
    Test 13: Refund gateway returns failure (negative test)
    
    Stubs: None
    Mocks: PaymentGateway.refund_payment (returns failure)
    Verification: assert_called_once() to verify refund was attempted
    """
    # MOCK: PaymentGateway that fails refund
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (False, "Transaction already refunded")
    
    # Execute
    success, message = refund_late_fee_payment("txn_111222", 8.00, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Refund failed" in message
    assert "Transaction already refunded" in message
    
    # VERIFICATION: Refund was attempted
    mock_gateway.refund_payment.assert_called_once_with("txn_111222", 8.00)


def test_refund_late_fee_exception_handling():
    """
    Test 14: Refund gateway raises exception (exception test)
    
    Stubs: None
    Mocks: PaymentGateway.refund_payment (raises exception)
    Verification: assert_called_once() to verify attempt before exception
    """
    # MOCK: PaymentGateway that raises exception
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("Connection refused")
    
    # Execute
    success, message = refund_late_fee_payment("txn_333444", 12.50, mock_gateway)
    
    # Assertions
    assert success is False
    assert "Refund processing error" in message
    assert "Connection refused" in message
    
    # VERIFICATION: Refund was attempted before exception
    mock_gateway.refund_payment.assert_called_once()


def test_pay_late_fees_boundary_maximum_fee(mocker):
    """
    Test 15: Maximum late fee boundary ($15.00) - positive test
    
    Stubs: calculate_late_fee_for_book (returns max fee), get_book_by_id
    Mocks: PaymentGateway.process_payment
    Verification: assert_called_with() to verify exact amount
    """
    # STUB: Return maximum late fee
    mocker.patch(
        'services.library_service.calculate_late_fee_for_book',
        return_value={'fee_amount': 15.00, 'days_overdue': 15, 'status': 'ok'}
    )
    
    # STUB: Return book data
    mocker.patch(
        'services.library_service.get_book_by_id',
        return_value={'id': 5, 'title': 'Design Patterns', 'author': 'Gamma'}
    )
    
    # MOCK: PaymentGateway
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_max", "Success")
    
    # Execute
    success, message, txn_id = pay_late_fees("999999", 5, mock_gateway)
    
    # Assertions
    assert success is True
    
    # VERIFICATION: Verify maximum fee amount was passed
    mock_gateway.process_payment.assert_called_once()
    call_args = mock_gateway.process_payment.call_args
    assert call_args[1]['amount'] == 15.00  # Maximum late fee


def test_refund_late_fee_boundary_maximum_valid(mocker):
    """
    Test 16: Refund exactly $15.00 (maximum valid amount) - boundary test
    
    Stubs: None
    Mocks: PaymentGateway.refund_payment
    Verification: assert_called_once_with() for exact boundary value
    """
    # MOCK: PaymentGateway
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund successful")
    
    # Execute with maximum valid amount
    success, message = refund_late_fee_payment("txn_max15", 15.00, mock_gateway)
    
    # Assertions
    assert success is True
    
    # VERIFICATION: Refund should succeed for exactly $15.00
    mock_gateway.refund_payment.assert_called_once_with("txn_max15", 15.00)
