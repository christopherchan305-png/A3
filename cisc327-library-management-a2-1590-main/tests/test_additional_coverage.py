"""
Additional tests to achieve 80%+ code coverage
Covers missing branches and edge cases in library_service and database modules
"""

import os
import pytest
from datetime import datetime, timedelta, date
from database import (
    init_database, insert_book, insert_borrow_record, 
    update_book_availability, get_book_by_id, get_book_by_isbn,
    get_patron_borrow_count, get_patron_borrowed_books,
    update_borrow_record_return_date, get_all_books
)
from services import library_service as svc


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Create a fresh database for each test."""
    os.chdir(tmp_path)
    init_database()
    yield


# ============================================================================
# TESTS FOR add_book_to_catalog() - Coverage for all validation branches
# ============================================================================

def test_add_book_success():
    """Test successfully adding a book to catalog"""
    success, message = svc.add_book_to_catalog(
        "Clean Code", "Robert Martin", "9780132350884", 5
    )
    assert success is True
    assert "successfully added" in message
    
    # Verify book was added
    book = get_book_by_isbn("9780132350884")
    assert book is not None
    assert book['title'] == "Clean Code"


def test_add_book_empty_title():
    """Test validation for empty title"""
    success, message = svc.add_book_to_catalog("", "Author", "1234567890123", 1)
    assert success is False
    assert "Title is required" in message


def test_add_book_title_too_long():
    """Test validation for title exceeding 200 characters"""
    long_title = "A" * 201
    success, message = svc.add_book_to_catalog(long_title, "Author", "1234567890123", 1)
    assert success is False
    assert "less than 200 characters" in message


def test_add_book_empty_author():
    """Test validation for empty author"""
    success, message = svc.add_book_to_catalog("Title", "", "1234567890123", 1)
    assert success is False
    assert "Author is required" in message


def test_add_book_author_too_long():
    """Test validation for author exceeding 100 characters"""
    long_author = "B" * 101
    success, message = svc.add_book_to_catalog("Title", long_author, "1234567890123", 1)
    assert success is False
    assert "less than 100 characters" in message


def test_add_book_isbn_not_13_digits():
    """Test validation for ISBN not exactly 13 digits"""
    success, message = svc.add_book_to_catalog("Title", "Author", "12345", 1)
    assert success is False
    assert "13 digits" in message


def test_add_book_isbn_contains_letters():
    """Test validation for ISBN containing non-digit characters"""
    success, message = svc.add_book_to_catalog("Title", "Author", "123456789012X", 1)
    assert success is False
    assert "13 digits" in message


def test_add_book_negative_copies():
    """Test validation for negative total copies"""
    success, message = svc.add_book_to_catalog("Title", "Author", "1234567890123", -1)
    assert success is False
    assert "positive integer" in message


def test_add_book_zero_copies():
    """Test validation for zero total copies"""
    success, message = svc.add_book_to_catalog("Title", "Author", "1234567890123", 0)
    assert success is False
    assert "positive integer" in message


def test_add_book_duplicate_isbn():
    """Test validation for duplicate ISBN"""
    # Add first book
    svc.add_book_to_catalog("First Book", "Author", "1234567890123", 1)
    
    # Try to add another book with same ISBN
    success, message = svc.add_book_to_catalog("Second Book", "Author", "1234567890123", 1)
    assert success is False
    assert "already exists" in message


def test_add_book_whitespace_trimming():
    """Test that whitespace is trimmed from title and author"""
    success, message = svc.add_book_to_catalog(
        "  Spaced Title  ", "  Spaced Author  ", "1234567890123", 2
    )
    assert success is True
    
    book = get_book_by_isbn("1234567890123")
    assert book['title'] == "Spaced Title"
    assert book['author'] == "Spaced Author"


# ============================================================================
# TESTS FOR borrow_book_by_patron() - Coverage for all branches
# ============================================================================

def test_borrow_book_success():
    """Test successfully borrowing a book"""
    insert_book("Test Book", "Test Author", "1234567890123", 3, 3)
    
    success, message = svc.borrow_book_by_patron("123456", 1)
    assert success is True
    assert "Successfully borrowed" in message
    assert "Due date:" in message
    
    # Verify availability decreased
    book = get_book_by_id(1)
    assert book['available_copies'] == 2


def test_borrow_book_invalid_patron_short():
    """Test borrowing with patron ID too short"""
    success, message = svc.borrow_book_by_patron("12345", 1)
    assert success is False
    assert "Invalid patron ID" in message


def test_borrow_book_invalid_patron_long():
    """Test borrowing with patron ID too long"""
    success, message = svc.borrow_book_by_patron("1234567", 1)
    assert success is False
    assert "Invalid patron ID" in message


def test_borrow_book_invalid_patron_letters():
    """Test borrowing with non-digit patron ID"""
    success, message = svc.borrow_book_by_patron("12345a", 1)
    assert success is False
    assert "Invalid patron ID" in message


def test_borrow_book_not_found():
    """Test borrowing non-existent book"""
    success, message = svc.borrow_book_by_patron("123456", 999)
    assert success is False
    assert "Book not found" in message


def test_borrow_book_not_available():
    """Test borrowing when no copies available"""
    insert_book("Unavailable Book", "Author", "1234567890123", 1, 0)
    
    success, message = svc.borrow_book_by_patron("123456", 1)
    assert success is False
    assert "not available" in message


def test_borrow_book_limit_exceeded():
    """Test borrowing when patron has reached limit"""
    # Create 6 books
    for i in range(6):
        isbn = f"123456789012{i}"
        insert_book(f"Book {i}", "Author", isbn, 1, 1)
        insert_borrow_record("123456", i+1, datetime.now(), datetime.now() + timedelta(days=14))
        update_book_availability(i+1, -1)
    
    # Try to borrow 7th book
    insert_book("Seventh Book", "Author", "9999999999999", 1, 1)
    success, message = svc.borrow_book_by_patron("123456", 7)
    assert success is False
    assert "maximum borrowing limit" in message


# ============================================================================
# TESTS FOR search_books_in_catalog() - Coverage for edge cases
# ============================================================================

def test_search_empty_term():
    """Test search with empty search term"""
    insert_book("Test Book", "Author", "1234567890123", 1, 1)
    
    results = svc.search_books_in_catalog("", "title")
    assert results == []


def test_search_invalid_type():
    """Test search with invalid search type"""
    insert_book("Test Book", "Author", "1234567890123", 1, 1)
    
    results = svc.search_books_in_catalog("Test", "invalid_type")
    assert results == []


def test_search_isbn_partial_match():
    """Test that ISBN search requires exact 13-digit match"""
    insert_book("Test Book", "Author", "1234567890123", 1, 1)
    
    # Partial ISBN should not match
    results = svc.search_books_in_catalog("123456789012", "isbn")
    assert results == []


def test_search_title_case_insensitive():
    """Test that title search is case-insensitive"""
    insert_book("The Great Book", "Author", "1234567890123", 1, 1)
    
    results = svc.search_books_in_catalog("GREAT", "title")
    assert len(results) == 1
    assert results[0]['title'] == "The Great Book"


def test_search_author_partial():
    """Test that author search supports partial matches"""
    insert_book("Book", "Stephen King", "1234567890123", 1, 1)
    
    results = svc.search_books_in_catalog("step", "author")
    assert len(results) == 1
    assert results[0]['author'] == "Stephen King"


# ============================================================================
# TESTS FOR return_book_by_patron() - Additional coverage
# ============================================================================

def test_return_book_invalid_patron_id():
    """Test return with invalid patron ID format"""
    success, message, fee = svc.return_book_by_patron("abc", 1)
    assert success is False
    assert "Invalid patron ID" in message
    assert fee == 0.0


def test_return_book_patron_id_wrong_length():
    """Test return with patron ID of wrong length"""
    success, message, fee = svc.return_book_by_patron("12345", 1)
    assert success is False
    assert "Invalid patron ID" in message


def test_return_book_not_found():
    """Test returning non-existent book"""
    success, message, fee = svc.return_book_by_patron("123456", 999)
    assert success is False
    assert "Book not found" in message
    assert fee == 0.0


# ============================================================================
# TESTS FOR calculate_late_fee_for_book() - Edge cases
# ============================================================================

def test_calculate_fee_invalid_patron_id_format():
    """Test late fee calculation with invalid patron ID"""
    result = svc.calculate_late_fee_for_book("invalid", 1)
    assert result['status'].startswith("error")
    assert result['fee_amount'] == 0.0


def test_calculate_fee_patron_id_wrong_length():
    """Test late fee calculation with wrong-length patron ID"""
    result = svc.calculate_late_fee_for_book("12345", 1)
    assert result['status'].startswith("error")


def test_calculate_fee_no_active_borrow():
    """Test late fee when no active borrow exists"""
    insert_book("Book", "Author", "1234567890123", 1, 1)
    
    result = svc.calculate_late_fee_for_book("123456", 1)
    assert result['status'].startswith("error")
    assert "active borrow not found" in result['status']


def test_calculate_fee_not_overdue():
    """Test late fee calculation for book not yet overdue"""
    insert_book("Book", "Author", "1234567890123", 1, 1)
    borrow_date = date.today() - timedelta(days=5)
    due_date = date.today() + timedelta(days=9)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    update_book_availability(1, -1)
    
    result = svc.calculate_late_fee_for_book("123456", 1)
    assert result['status'] == "ok"
    assert result['days_overdue'] == 0
    assert result['fee_amount'] == 0.0


# ============================================================================
# TESTS FOR get_patron_status_report() - Coverage
# ============================================================================

def test_patron_status_invalid_id():
    """Test patron status with invalid ID"""
    report = svc.get_patron_status_report("invalid")
    assert "error" in report
    assert "Invalid patron ID" in report['error']


def test_patron_status_empty_id():
    """Test patron status with empty ID"""
    report = svc.get_patron_status_report("")
    assert "error" in report


def test_patron_status_no_books():
    """Test patron status with no borrowed books"""
    report = svc.get_patron_status_report("999999")
    assert report['patron_id'] == "999999"
    assert report['number_currently_borrowed'] == 0
    assert report['total_late_fees_owed'] == 0.0
    assert len(report['currently_borrowed']) == 0


# ============================================================================
# DATABASE MODULE TESTS - Additional coverage
# ============================================================================

def test_get_all_books_empty():
    """Test getting all books when database is empty"""
    books = get_all_books()
    assert books == []


def test_get_all_books_multiple():
    """Test getting all books with multiple entries"""
    insert_book("Book A", "Author A", "1234567890123", 1, 1)
    insert_book("Book B", "Author B", "1234567890124", 2, 2)
    
    books = get_all_books()
    assert len(books) == 2


def test_get_book_by_id_not_found():
    """Test getting book by ID when it doesn't exist"""
    book = get_book_by_id(999)
    assert book is None


def test_get_book_by_isbn_not_found():
    """Test getting book by ISBN when it doesn't exist"""
    book = get_book_by_isbn("9999999999999")
    assert book is None


def test_get_patron_borrow_count_zero():
    """Test patron borrow count with no borrows"""
    count = get_patron_borrow_count("999999")
    assert count == 0


def test_get_patron_borrowed_books_empty():
    """Test getting borrowed books when patron has none"""
    books = get_patron_borrowed_books("999999")
    assert books == []


def test_get_patron_borrowed_books_with_overdue():
    """Test getting borrowed books including overdue status"""
    insert_book("Book", "Author", "1234567890123", 1, 1)
    borrow_date = datetime.now() - timedelta(days=20)
    due_date = datetime.now() - timedelta(days=6)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    update_book_availability(1, -1)
    
    books = get_patron_borrowed_books("123456")
    assert len(books) == 1
    assert books[0]['is_overdue'] is True


def test_update_book_availability_increase():
    """Test increasing book availability"""
    insert_book("Book", "Author", "1234567890123", 2, 0)
    
    success = update_book_availability(1, 1)
    assert success is True
    
    book = get_book_by_id(1)
    assert book['available_copies'] == 1


def test_update_book_availability_decrease():
    """Test decreasing book availability"""
    insert_book("Book", "Author", "1234567890123", 2, 2)
    
    success = update_book_availability(1, -1)
    assert success is True
    
    book = get_book_by_id(1)
    assert book['available_copies'] == 1
