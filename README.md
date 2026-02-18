# Smart Finance Tracker

AI-powered Django finance tracker with multi-account support, REST APIs, and predictive budgeting.

## Overview

Smart Finance Tracker is a comprehensive Django-based personal finance management system that empowers users to take control of their financial life. The application offers:

- **Multi-Account Management**: Track multiple financial accounts (checking, savings, credit cards, cash, investments)
- **Income & Expense Tracking**: Log and categorize all financial transactions
- **Budget Management**: Set and monitor budgets with intelligent alerts
- **RESTful API**: Full Django REST Framework API for third-party integrations
- **Machine Learning Features**:
  - Automatic transaction categorization using NLP
  - Predictive budgeting based on historical spending patterns
- **Interactive Dashboard**: Visualize spending patterns and financial insights

## Features

### Core Functionality

1. **User Authentication & Authorization**
   - Secure user registration and login
   - Custom user model with profile management
   - Session-based authentication for web
   - Token-based authentication for API

2. **Account Management**
   - Support for multiple account types (checking, savings, credit card, cash, investment, other)
   - Real-time balance tracking
   - Multi-currency support
   - Account activation/deactivation

3. **Transaction Management**
   - Income and expense tracking
   - Transaction categorization (21 default categories)
   - Date-based filtering and search
   - Receipt image upload
   - Recurring transaction support
   - Auto-categorization using ML

4. **Budget Management**
   - Create budgets by category
   - Support for different periods (daily, weekly, monthly, yearly)
   - Real-time spending tracking
   - Customizable alert thresholds
   - ML-powered predictive budgeting

5. **REST API**
   - Complete CRUD operations for all resources
   - Filtering and pagination
   - Transaction summaries and analytics
   - Budget alerts endpoint

### Machine Learning Features

#### Automatic Transaction Categorization
- Uses TF-IDF vectorization and Naive Bayes classification
- Learns from user's transaction history
- Automatically suggests categories for new transactions
- Confidence scoring for predictions

#### Predictive Budgeting
- Analyzes historical spending patterns
- Suggests optimal budget amounts
- Adapts to user's spending habits
- Helps prevent overspending

## Technology Stack

- **Backend**: Django 4.2+
- **API**: Django REST Framework 3.14+
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Machine Learning**: scikit-learn, pandas, numpy
- **Data Visualization**: matplotlib, seaborn
- **CORS**: django-cors-headers

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kr1shnenduManna/smart-finance-tracker.git
   cd smart-finance-tracker
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Populate default categories**
   ```bash
   python manage.py populate_categories
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Admin panel: http://127.0.0.1:8000/admin/
   - API root: http://127.0.0.1:8000/api/

## API Documentation

### Authentication

All API endpoints require authentication. Use session authentication for browser-based access or token authentication for programmatic access.

### Endpoints

#### Accounts
- `GET /api/accounts/users/` - List all users
- `GET /api/accounts/users/me/` - Get current user
- `GET /api/accounts/accounts/` - List user's accounts
- `POST /api/accounts/accounts/` - Create new account
- `GET /api/accounts/accounts/{id}/` - Get account details
- `PUT /api/accounts/accounts/{id}/` - Update account
- `DELETE /api/accounts/accounts/{id}/` - Delete account

#### Transactions
- `GET /api/transactions/categories/` - List all categories
- `GET /api/transactions/categories/income/` - List income categories
- `GET /api/transactions/categories/expense/` - List expense categories
- `POST /api/transactions/categories/` - Create category
- `GET /api/transactions/transactions/` - List transactions
  - Query params: `type`, `start_date`, `end_date`, `category`
- `POST /api/transactions/transactions/` - Create transaction
- `GET /api/transactions/transactions/summary/` - Get transaction summary
- `GET /api/transactions/transactions/by_category/` - Group by category

#### Budgets
- `GET /api/budgets/budgets/` - List budgets
- `POST /api/budgets/budgets/` - Create budget
- `GET /api/budgets/budgets/{id}/` - Get budget details
- `PUT /api/budgets/budgets/{id}/` - Update budget
- `DELETE /api/budgets/budgets/{id}/` - Delete budget
- `GET /api/budgets/budgets/active/` - List active budgets
- `GET /api/budgets/budgets/alerts/` - Get budget alerts

### API Examples

#### Create a Transaction
```bash
curl -X POST http://127.0.0.1:8000/api/transactions/transactions/ \
  -H "Content-Type: application/json" \
  -u username:password \
  -d '{
    "account": 1,
    "category": 5,
    "transaction_type": "expense",
    "amount": "50.00",
    "description": "Grocery shopping at Whole Foods",
    "date": "2024-02-15"
  }'
```

#### Get Transaction Summary
```bash
curl http://127.0.0.1:8000/api/transactions/transactions/summary/ \
  -u username:password
```

## Project Structure

```
smart-finance-tracker/
├── accounts/              # User and account management
│   ├── models.py         # User and Account models
│   ├── serializers.py    # API serializers
│   ├── views.py          # API viewsets
│   └── admin.py          # Admin configuration
├── transactions/          # Transaction management
│   ├── models.py         # Category and Transaction models
│   ├── serializers.py    # API serializers
│   ├── views.py          # API viewsets
│   └── management/       # Custom management commands
├── budgets/               # Budget management
│   ├── models.py         # Budget model
│   ├── serializers.py    # API serializers
│   └── views.py          # API viewsets
├── ml_features/           # Machine learning features
│   ├── models.py         # ML model metadata
│   ├── ml_utils.py       # ML utilities and algorithms
│   └── admin.py          # Admin configuration
├── finance_tracker/       # Project configuration
│   ├── settings.py       # Django settings
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Machine Learning Details

### Transaction Categorization

The system uses a machine learning pipeline consisting of:
- **TF-IDF Vectorizer**: Converts transaction descriptions to numerical features
- **Multinomial Naive Bayes**: Classifies transactions into categories
- **Confidence Scoring**: Only applies predictions with >60% confidence

Training occurs automatically as users categorize transactions manually. The model improves over time with more data.

### Budget Prediction

The budget predictor analyzes:
- Historical spending patterns (last 90 days)
- Category-specific trends
- Spending frequency
- Average transaction amounts

It suggests optimal budget amounts based on:
- Period type (daily, weekly, monthly, yearly)
- Historical averages
- Spending variance

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Custom Categories
```python
from transactions.models import Category

Category.objects.create(
    name='Custom Category',
    category_type='expense',
    icon='custom-icon',
    color='#FF5733'
)
```

### Training ML Models
The ML models train automatically as data is added. To manually retrain:
```python
from ml_features.ml_utils import get_categorizer
from transactions.models import Transaction

categorizer = get_categorizer()
transactions = Transaction.objects.filter(category__isnull=False)
descriptions = [t.description for t in transactions]
categories = [t.category.name for t in transactions]
categorizer.train(descriptions, categories)
categorizer.save_model('ml_models/categorizer.pkl')
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

- [ ] Add data export functionality (CSV, PDF)
- [ ] Implement recurring transaction automation
- [ ] Add bill reminders and notifications
- [ ] Create mobile-responsive dashboard
- [ ] Implement investment portfolio tracking
- [ ] Add multi-language support
- [ ] Integrate with banking APIs for automatic transaction import
- [ ] Add advanced data visualizations and reports
- [ ] Implement goal-setting and tracking features
- [ ] Add expense splitting for shared expenses
