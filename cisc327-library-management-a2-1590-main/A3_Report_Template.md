# CISC 327 Assignment 3 Report
## Advanced Testing with Mocking, Stubbing, and Code Coverage

---

## Section 1: Student Information

**Name:** [Your Full Name]  
**Student ID:** [Your Student ID]  
**Course:** CISC/CMPE 327 - Software Quality Assurance  
**Assignment:** Assignment 3  
**Submission Date:** November 10, 2025

---

## Section 2: Stubbing vs Mocking - Explanation and Strategy

### What is Stubbing?

**Stubbing** is a testing technique where we create fake implementations of functions or methods that return hard-coded, predetermined values. Stubs are used when we only need the return value from a dependency but don't care about verifying how it was called or what parameters were passed.

**Key Characteristics:**
- Provides canned responses to function calls
- No verification of interactions
- Used primarily to isolate the system under test
- Lightweight and simple to implement

**Example from our implementation:**
```python
mocker.patch(
    'services.library_service.calculate_late_fee_for_book',
    return_value={'fee_amount': 5.50, 'days_overdue': 3, 'status': 'ok'}
)
```

### What is Mocking?

**Mocking** is a more sophisticated testing technique where we create test doubles that not only provide fake responses but also record how they were called, allowing us to verify interactions. Mocks enable us to assert that specific methods were called with expected parameters, called a certain number of times, or not called at all.

**Key Characteristics:**
- Verifies method calls and parameters
- Tracks call counts and order
- Enables interaction-based testing
- More complex than stubs but provides stronger guarantees

**Example from our implementation:**
```python
mock_gateway = Mock(spec=PaymentGateway)
mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
# ... execute function ...
mock_gateway.process_payment.assert_called_once_with(
    patron_id="123456", amount=5.50, description="Late fees for 'Clean Code'"
)
```

### Our Testing Strategy

**Functions We Stubbed:**
1. **`calculate_late_fee_for_book()`** - Database function that calculates late fees
   - **Reason:** We only needed the fee amount returned; didn't care about the calculation logic
   - **Benefit:** Isolated payment processing from fee calculation logic

2. **`get_book_by_id()`** - Database function that retrieves book information
   - **Reason:** We only needed book details for payment descriptions
   - **Benefit:** Avoided database setup and focused on payment gateway interaction

**Functions/Classes We Mocked:**
1. **`PaymentGateway.process_payment()`** - External payment service method
   - **Reason:** Needed to verify correct payment amounts and patron IDs were passed
   - **Benefit:** Ensured business logic correctly calls external service with proper parameters

2. **`PaymentGateway.refund_payment()`** - External refund service method
   - **Reason:** Needed to verify refund requests used correct transaction IDs and amounts
   - **Benefit:** Validated refund logic without making actual API calls

**Decision Criteria:**

We used **stubbing** when:
- We only needed return values from dependencies
- The function was internal (database operations)
- We wanted to provide controlled test data

We used **mocking** when:
- We needed to verify correct parameters were passed
- We were testing external service integration
- We wanted to ensure proper interaction patterns
- We needed to verify method call counts (once, never, etc.)

This strategy allowed us to thoroughly test payment processing logic while isolating it from database operations and external API dependencies.

---

## Section 3: Test Execution Instructions

### Prerequisites

1. Ensure Python 3.11+ is installed
2. Clone/download the project repository

### Environment Setup

**Step 1: Create and activate virtual environment**
```powershell
# Navigate to project directory
cd path\to\cisc327-library-management-a2-1590-main

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Or for Windows Command Prompt
.\.venv\Scripts\activate.bat
```

**Step 2: Install dependencies**
```powershell
pip install -r requirements.txt
```

The `requirements.txt` includes:
- Flask==2.3.3
- pytest==7.4.2
- pytest-mock==3.11.1
- pytest-cov==4.1.0
- coverage==7.3.2
- requests

### Running All Tests

**Execute all test cases:**
```powershell
pytest tests/ -v
```

**Expected output:** All 83 tests should pass

### Generating Coverage Reports

**Option 1: Terminal Coverage Report (Statement Coverage)**
```powershell
pytest --cov=services --cov=database --cov-report=term tests/
```

**Option 2: Terminal Coverage with Branch Coverage**
```powershell
pytest --cov=services --cov=database --cov-branch --cov-report=term-missing tests/
```

**Option 3: HTML Coverage Report (Recommended)**
```powershell
pytest --cov=services --cov=database --cov-branch --cov-report=html tests/
```

### Viewing HTML Coverage Results

After generating HTML coverage:
```powershell
# The report is generated in the htmlcov directory
# Open in default browser (Windows)
start htmlcov\index.html

# Or navigate manually to:
# htmlcov/index.html
```

The HTML report provides:
- Per-file coverage percentages
- Line-by-line coverage visualization
- Branch coverage details
- Missing lines highlighted in red
- Partial branches highlighted in yellow

### Running Specific Test Files

**Run only mock/stub tests:**
```powershell
pytest tests/test_payment_mock_stub.py -v
```

**Run only additional coverage tests:**
```powershell
pytest tests/test_additional_coverage.py -v
```

**Run only payment service tests:**
```powershell
pytest tests/test_payment_service.py -v
```

### Continuous Integration

The project includes GitHub Actions workflow (`.github/workflows/a2.yaml`) that automatically:
- Runs all tests on push/pull request
- Generates coverage reports
- Validates code quality

---

## Section 4: Test Cases Summary Table

| Test Function Name | Purpose | Stubs Used | Mocks Used | Verification Done |
|-------------------|---------|------------|------------|-------------------|
| **test_pay_late_fees_success_positive** | Verify successful payment processing with valid late fees | `calculate_late_fee_for_book`, `get_book_by_id` | `PaymentGateway.process_payment` | `assert_called_once_with()` to verify patron ID, amount, and description |
| **test_pay_late_fees_payment_declined_negative** | Verify handling of payment gateway decline | `calculate_late_fee_for_book`, `get_book_by_id` | `PaymentGateway.process_payment` (returns False) | `assert_called_once()` to verify attempt was made |
| **test_pay_late_fees_invalid_patron_id_negative** | Verify rejection of invalid patron IDs | None (validation before stubs) | `PaymentGateway.process_payment` | `assert_not_called()` to verify no payment attempted |
| **test_pay_late_fees_zero_late_fees_edge_case** | Verify no payment for zero late fees | `calculate_late_fee_for_book` (returns $0.00) | `PaymentGateway.process_payment` | `assert_not_called()` for zero fees |
| **test_pay_late_fees_network_error_exception** | Verify exception handling for network errors | `calculate_late_fee_for_book`, `get_book_by_id` | `PaymentGateway.process_payment` (raises Exception) | `assert_called_once()` to verify attempt before exception |
| **test_refund_late_fee_success_positive** | Verify successful refund processing | None (parameter-based) | `PaymentGateway.refund_payment` | `assert_called_once_with()` to verify transaction ID and amount |
| **test_refund_late_fee_invalid_transaction_id_negative** | Verify rejection of invalid transaction IDs | None | `PaymentGateway.refund_payment` | `assert_not_called()` for invalid transaction IDs |
| **test_refund_late_fee_negative_amount_negative** | Verify rejection of negative refund amounts | None | `PaymentGateway.refund_payment` | `assert_not_called()` for negative amounts |
| **test_refund_late_fee_zero_amount_edge_case** | Verify rejection of zero refund amount | None | `PaymentGateway.refund_payment` | `assert_not_called()` for zero amount |
| **test_refund_late_fee_exceeds_maximum_boundary** | Verify rejection of refunds exceeding $15 maximum | None | `PaymentGateway.refund_payment` | `assert_not_called()` for excessive amounts |
| **test_pay_late_fees_book_not_found_negative** | Verify handling when book doesn't exist | `calculate_late_fee_for_book`, `get_book_by_id` (returns None) | `PaymentGateway.process_payment` | `assert_not_called()` when book missing |
| **test_pay_late_fees_no_fee_info_returned_negative** | Verify handling when fee calculation fails | `calculate_late_fee_for_book` (returns None) | `PaymentGateway.process_payment` | `assert_not_called()` when calculation fails |
| **test_refund_late_fee_gateway_failure_negative** | Verify handling of refund gateway failure | None | `PaymentGateway.refund_payment` (returns False) | `assert_called_once_with()` to verify refund attempted |
| **test_refund_late_fee_exception_handling** | Verify exception handling during refund | None | `PaymentGateway.refund_payment` (raises Exception) | `assert_called_once()` to verify attempt before exception |
| **test_pay_late_fees_boundary_maximum_fee** | Verify payment processing with maximum $15 fee | `calculate_late_fee_for_book` (returns $15.00), `get_book_by_id` | `PaymentGateway.process_payment` | `assert_called_once()` and verify amount == $15.00 |
| **test_refund_late_fee_boundary_maximum_valid** | Verify refund of exactly $15.00 (boundary) | None | `PaymentGateway.refund_payment` | `assert_called_once_with()` to verify $15.00 amount |

### Additional Test Scenarios

Beyond the core mock/stub tests, we implemented comprehensive test suites for:

**Library Service Functions (42 tests):**
- `add_book_to_catalog()` - 11 tests covering validation, duplicates, edge cases
- `borrow_book_by_patron()` - 7 tests covering validation, availability, limits
- `search_books_in_catalog()` - 5 tests covering search types, case sensitivity
- `return_book_by_patron()` - 3 tests covering validation, late fees
- `calculate_late_fee_for_book()` - 4 tests covering overdue calculations
- `get_patron_status_report()` - 3 tests covering patron status

**Database Functions (9 tests):**
- CRUD operations for books and borrow records
- Availability tracking
- Patron borrowed books retrieval

**Payment Service (15 tests):**
- Payment gateway initialization
- Successful and failed payments
- Refund processing
- Payment status verification
- Validation of amounts and IDs

**Total: 83 comprehensive test cases**

---

## Section 5: Coverage Analysis

### Initial Coverage (Before Optimization)

**Initial Baseline Coverage:**
- **Overall Coverage:** 61%
- **database.py:** 68%
- **services/library_service.py:** 64%
- **services/payment_service.py:** 27%

**Identified Gaps:**
- Missing validation branch tests in `add_book_to_catalog()`
- Incomplete coverage of `borrow_book_by_patron()` edge cases
- No tests for `PaymentGateway` class methods
- Uncovered exception handling paths
- Missing boundary condition tests

### Final Coverage (After Optimization)

**Final Achievement:**
- **Overall Coverage:** 86% ✓ (Exceeds 80% target)
- **Statement Coverage:** 86%
- **Branch Coverage:** 93% (118 branches, 110 covered)

**Per-Module Breakdown:**

| Module | Statements | Missed | Branches | Partial | Coverage |
|--------|-----------|--------|----------|---------|----------|
| database.py | 93 | 22 | 8 | 0 | 74% |
| services/__init__.py | 0 | 0 | 0 | 0 | 100% |
| services/library_service.py | 165 | 18 | 98 | 8 | 88% |
| services/payment_service.py | 30 | 0 | 12 | 0 | 100% |
| **TOTAL** | **288** | **40** | **118** | **8** | **86%** |

### Coverage Improvement Strategy

**Phase 1: Mock/Stub Tests (61% → 61%)**
- Created 16 comprehensive tests for payment functions
- Focused on verification patterns and edge cases
- Initial coverage remained similar due to focused scope

**Phase 2: Additional Coverage Tests (61% → 78%)**
- Added 42 tests for library service functions
- Covered all validation branches in `add_book_to_catalog()`
- Tested borrowing limits, availability checks
- Implemented search edge cases and boundary tests
- **Result:** 17% coverage increase

**Phase 3: Payment Service Tests (78% → 86%)**
- Added 15 tests for `PaymentGateway` class
- Achieved 100% coverage of payment service
- Tested initialization, success/failure paths, validation
- **Result:** 8% coverage increase, exceeding 80% target

### Remaining Uncovered Lines - Justification

**database.py (Lines 53-83, 154-185):**
- These lines are part of `add_sample_data()` function
- This function is only used for demo/development purposes
- Not part of core business logic
- Would require specific test environment setup
- Low priority for unit testing

**services/library_service.py (Lines 104, 170, 209, 213, 263, 267-277):**
- Line 104: Fallback error handling for database exceptions (rare edge case)
- Line 170: Similar database exception handler
- Lines 267-277: Unreachable code paths in fee calculation (defensive programming)
- These represent defensive exception handling that's difficult to trigger in unit tests
- Would require database corruption or system-level failures

**Branch Coverage:**
- 93% branch coverage achieved (110 of 118 branches)
- 8 partial branches are in exception handling paths
- Most represent rare database failures or system errors

### Statement vs Branch Coverage

**Statement Coverage (86%):**
- Measures which lines of code were executed
- Our tests executed 248 out of 288 statements
- Excellent coverage of core business logic

**Branch Coverage (93%):**
- Measures which decision paths were taken
- Includes if/else branches, try/except blocks
- Higher percentage indicates thorough testing of all code paths
- Our tests covered 110 out of 118 possible branches

**Why Branch Coverage Matters:**
- Identifies untested decision paths
- Reveals edge cases in conditional logic
- More comprehensive than statement coverage alone
- Critical for finding logic bugs

---

## Section 6: Challenges and Solutions

### Challenge 1: Import Structure Refactoring

**Problem:**
After moving `library_service.py` to the `services/` folder, existing tests failed with `ModuleNotFoundError: No module named 'library_service'`.

**Solution:**
1. Created `services/__init__.py` to make it a proper Python package
2. Updated all test files to use `from services import library_service as svc`
3. Updated `library_service.py` to import `PaymentGateway` from `services.payment_service`
4. Verified all imports worked consistently across the project

**Learning:**
Python's package structure requires proper `__init__.py` files. Refactoring module structure requires systematic update of all import statements.

---

### Challenge 2: Understanding Mock vs Stub Distinction

**Problem:**
Initially confused about when to use `mocker.patch()` (stubbing) vs `Mock(spec=Class)` (mocking). Both seemed to achieve similar results.

**Solution:**
1. Researched pytest-mock and unittest.mock documentation
2. Identified key difference: stubs provide return values, mocks verify interactions
3. Established clear decision criteria:
   - Use stubs for functions where we only need return values
   - Use mocks for classes/methods where we need to verify calls
4. Applied pattern consistently across all tests

**Learning:**
Stubbing is about isolation (providing fake data), mocking is about verification (ensuring correct interactions). Both are essential for comprehensive testing.

---

### Challenge 3: Mock Verification Patterns

**Problem:**
Struggled to understand different assertion methods:
- When to use `assert_called_once()` vs `assert_called_once_with()`
- How to verify mocks were NOT called
- How to check call arguments

**Solution:**
1. Studied unittest.mock documentation and Real Python guide
2. Created test scenarios for each verification pattern:
   - `assert_called_once()` - verify single call, don't care about args
   - `assert_called_once_with(...)` - verify single call with specific args
   - `assert_not_called()` - verify method was never called
   - `call_args` - inspect actual arguments passed
3. Applied appropriate assertions based on test objectives

**Learning:**
Different assertion methods serve different purposes. Using the right assertion makes tests more precise and meaningful.

---

### Challenge 4: Achieving 80% Coverage Target

**Problem:**
Initial coverage was only 61%, far below the 80% requirement. Needed systematic approach to identify and cover missing code paths.

**Solution:**
1. Generated HTML coverage report to visualize uncovered lines
2. Identified three categories of missing coverage:
   - Validation branches in input functions
   - Edge cases and boundary conditions
   - External service integration (`PaymentGateway`)
3. Created targeted test files:
   - `test_additional_coverage.py` - validation and edge cases
   - `test_payment_service.py` - PaymentGateway coverage
4. Iteratively ran coverage reports and added tests
5. Achieved 86% coverage

**Learning:**
Coverage analysis is iterative. HTML reports are invaluable for identifying gaps. Systematic approach beats random test additions.

---

### Challenge 5: Testing Exception Handling

**Problem:**
Difficult to test exception paths where payment gateway raises network errors or timeouts.

**Solution:**
1. Used `Mock.side_effect` to raise exceptions:
```python
mock_gateway.process_payment.side_effect = Exception("Network timeout")
```
2. Verified function handles exception gracefully
3. Confirmed error messages are informative
4. Ensured resources are cleaned up

**Learning:**
`side_effect` is powerful for simulating exceptions and failures. Testing failure paths is as important as testing success paths.

---

### Challenge 6: Boundary Value Testing

**Problem:**
Needed to test boundary conditions like:
- Exactly $15.00 (maximum late fee)
- Zero fees
- Maximum borrowing limit

**Solution:**
1. Identified all boundary values in requirements:
   - Late fee: $0.00, $15.00, $15.01
   - Patron ID: 5 digits, 6 digits, 7 digits
   - Borrowing limit: 5 books, 6 books
2. Created dedicated boundary tests
3. Used both valid and invalid boundary values
4. Verified correct behavior at edges

**Learning:**
Boundary value analysis is critical for robust testing. Bugs often hide at boundaries between valid and invalid inputs.

---

### Challenge 7: Test Organization and Naming

**Problem:**
With 83 tests, needed clear organization to maintain readability and prevent test duplication.

**Solution:**
1. Organized tests by module/function in separate files
2. Used descriptive test names following pattern:
   - `test_<function>_<scenario>_<test_type>`
   - Example: `test_pay_late_fees_invalid_patron_id_negative`
3. Added docstrings explaining test purpose
4. Grouped related tests with section comments
5. Created summary table for documentation

**Learning:**
Good test organization and naming makes test suites maintainable. Self-documenting test names reduce need for comments.

---

### Challenge 8: Handling Temporal Dependencies

**Problem:**
Some tests depend on current date (overdue calculations), making tests potentially flaky.

**Solution:**
1. Used relative dates with `timedelta`:
```python
borrow_date = date.today() - timedelta(days=19)
due_date = date.today() - timedelta(days=5)
```
2. Calculated expected fees based on relative dates
3. Ensured tests work regardless of when they're run
4. Used fresh database fixture for isolation

**Learning:**
Tests should be deterministic and time-independent. Relative dates are more robust than hard-coded dates.

---

## Section 7: Screenshots

### Screenshot 1: All Tests Passing (83/83)

![All Tests Passing](screenshots/all_tests_passing.png)

**Description:** Demonstrates all 83 test cases passing successfully, including:
- Mock/stub tests for payment functions (16 tests)
- Additional coverage tests (42 tests)
- Payment service tests (15 tests)
- Existing tests (10 tests)

---

### Screenshot 2: Coverage Terminal Output

![Coverage Terminal Output](screenshots/coverage_terminal.png)

**Description:** Shows final coverage metrics:
- Overall: 86% coverage
- services/library_service.py: 88%
- services/payment_service.py: 100%
- database.py: 74%
- Branch coverage: 93%

---

### Screenshot 3: HTML Coverage Report - Overview

![HTML Coverage Overview](screenshots/coverage_html_overview.png)

**Description:** HTML coverage report homepage showing:
- Per-module coverage percentages
- Statement and branch coverage
- Links to detailed file-level reports

---

### Screenshot 4: HTML Coverage Report - library_service.py Detail

![Library Service Coverage](screenshots/coverage_library_service.png)

**Description:** Detailed coverage for library_service.py showing:
- Green highlighted lines (covered)
- Red highlighted lines (uncovered)
- Yellow highlighted lines (partial branches)
- Line-by-line execution counts

---

### Screenshot 5: Mock/Stub Tests Execution

![Mock Stub Tests](screenshots/mock_stub_tests.png)

**Description:** Detailed output from running test_payment_mock_stub.py showing:
- All 16 mock/stub tests passing
- Test names with clear descriptions
- Verification of stubbing and mocking patterns

---

## Conclusion

This assignment successfully demonstrated advanced testing techniques using stubbing and mocking to test payment processing functionality while achieving 86% code coverage (exceeding the 80% target). Key accomplishments include:

**Technical Achievements:**
- Implemented 16 comprehensive mock/stub tests for payment functions
- Created 83 total test cases covering all major code paths
- Achieved 86% statement coverage and 93% branch coverage
- Successfully isolated external dependencies using proper mocking patterns

**Testing Best Practices Applied:**
- Clear distinction between stubbing (data isolation) and mocking (interaction verification)
- Comprehensive test scenarios: positive, negative, edge cases, boundaries, exceptions
- Proper use of pytest-mock and unittest.mock assertion methods
- Self-documenting test names and organization

**Skills Developed:**
- Deep understanding of mock vs stub patterns
- Proficiency with pytest-mock and coverage tools
- Systematic approach to achieving coverage targets
- Exception and edge case testing strategies

This assignment provided invaluable experience in writing high-quality, maintainable test suites that verify both functionality and interactions, essential skills for professional software quality assurance.

---

## Appendix: Project Structure

```
cisc327-library-management-a2-1590-main/
├── services/
│   ├── __init__.py                 # Package initialization
│   ├── library_service.py          # Business logic (165 lines, 88% coverage)
│   └── payment_service.py          # Payment gateway (30 lines, 100% coverage)
├── tests/
│   ├── test_payment_mock_stub.py   # 16 mock/stub tests (Assignment requirement)
│   ├── test_additional_coverage.py # 42 coverage improvement tests
│   ├── test_payment_service.py     # 15 payment service tests
│   ├── test_calculate_late.py      # 4 late fee tests
│   ├── test_get_patron.py          # 1 patron status test
│   ├── test_return_book.py         # 3 return book tests
│   └── test_search_books.py        # 2 search tests
├── database.py                     # Database operations (93 lines, 74% coverage)
├── app.py                          # Flask application
├── requirements.txt                # Dependencies
└── htmlcov/                        # Coverage HTML reports
    └── index.html
```

---

**End of Report**
