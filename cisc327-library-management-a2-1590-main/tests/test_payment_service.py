"""
Tests for PaymentGateway service
These tests verify the external payment service behavior
"""

import pytest
from services.payment_service import PaymentGateway


def test_payment_gateway_init_default():
    """Test PaymentGateway initialization with default API key"""
    gateway = PaymentGateway()
    assert gateway.api_key == "test_key_12345"
    assert gateway.base_url == "https://api.payment-gateway.example.com"


def test_payment_gateway_init_custom_key():
    """Test PaymentGateway initialization with custom API key"""
    gateway = PaymentGateway(api_key="custom_key_789")
    assert gateway.api_key == "custom_key_789"


def test_process_payment_success():
    """Test successful payment processing"""
    gateway = PaymentGateway()
    success, txn_id, message = gateway.process_payment("123456", 10.50, "Test payment")
    
    assert success is True
    assert txn_id.startswith("txn_123456")
    assert "processed successfully" in message


def test_process_payment_zero_amount():
    """Test payment with zero amount"""
    gateway = PaymentGateway()
    success, txn_id, message = gateway.process_payment("123456", 0.0, "Test")
    
    assert success is False
    assert txn_id == ""
    assert "Invalid amount" in message


def test_process_payment_negative_amount():
    """Test payment with negative amount"""
    gateway = PaymentGateway()
    success, txn_id, message = gateway.process_payment("123456", -5.00, "Test")
    
    assert success is False
    assert "Invalid amount" in message


def test_process_payment_exceeds_limit():
    """Test payment exceeding limit"""
    gateway = PaymentGateway()
    success, txn_id, message = gateway.process_payment("123456", 1500.00, "Large payment")
    
    assert success is False
    assert "exceeds limit" in message


def test_process_payment_invalid_patron_id():
    """Test payment with invalid patron ID format"""
    gateway = PaymentGateway()
    success, txn_id, message = gateway.process_payment("12345", 10.00, "Test")
    
    assert success is False
    assert "Invalid patron ID" in message


def test_refund_payment_success():
    """Test successful refund"""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_123456_1234567890", 5.00)
    
    assert success is True
    assert "processed successfully" in message
    assert "refund_" in message


def test_refund_payment_invalid_transaction_id():
    """Test refund with invalid transaction ID"""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("invalid_id", 5.00)
    
    assert success is False
    assert "Invalid transaction ID" in message


def test_refund_payment_empty_transaction_id():
    """Test refund with empty transaction ID"""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("", 5.00)
    
    assert success is False
    assert "Invalid transaction ID" in message


def test_refund_payment_zero_amount():
    """Test refund with zero amount"""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_123456", 0.0)
    
    assert success is False
    assert "Invalid refund amount" in message


def test_refund_payment_negative_amount():
    """Test refund with negative amount"""
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_123456", -10.00)
    
    assert success is False
    assert "Invalid refund amount" in message


def test_verify_payment_status_valid():
    """Test verifying payment status with valid transaction"""
    gateway = PaymentGateway()
    status = gateway.verify_payment_status("txn_123456_1234567890")
    
    assert status['status'] == "completed"
    assert status['transaction_id'] == "txn_123456_1234567890"
    assert 'amount' in status
    assert 'timestamp' in status


def test_verify_payment_status_invalid():
    """Test verifying payment status with invalid transaction ID"""
    gateway = PaymentGateway()
    status = gateway.verify_payment_status("invalid_id")
    
    assert status['status'] == "not_found"
    assert "not found" in status['message']


def test_verify_payment_status_empty():
    """Test verifying payment status with empty transaction ID"""
    gateway = PaymentGateway()
    status = gateway.verify_payment_status("")
    
    assert status['status'] == "not_found"
