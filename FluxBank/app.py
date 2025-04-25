from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import json
from datetime import datetime, timedelta
import requests
import time
import functools

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL Configuration
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'pool_name': 'mypool',
    'pool_size': 5
}

# Create connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
except Error as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

# Alpha Vantage API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Razorpay Configuration


def get_db_connection():
    try:
        if connection_pool:
            return connection_pool.get_connection()
        return None
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        return None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    user_id=user_data['id'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    user_id=user_data['id'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
            return None
        finally:
            cursor.close()
            conn.close()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('login'))
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
            user_data = cursor.fetchone()
            
            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(
                    user_id=user_data['id'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Invalid email or password')
        finally:
            cursor.close()
            conn.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('register'))
        
        cursor = conn.cursor()
        try:
            # Check if email exists
            cursor.execute("SELECT id FROM user WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered')
                return redirect(url_for('register'))
            
            # Insert new user
            cursor.execute(
                "INSERT INTO user (email, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
                (email, generate_password_hash(password), first_name, last_name)
            )
            user_id = cursor.lastrowid
            
            # Create default savings account
            account_number = f"SAV{user_id:06d}"
            cursor.execute(
                "INSERT INTO account (account_number, account_type, user_id, balance) VALUES (%s, %s, %s, %s)",
                (account_number, 'Savings', user_id, 100.00)  # Initial balance of $100
            )
            account_id = cursor.lastrowid
            
            # Record initial deposit transaction
            cursor.execute("""
                INSERT INTO transaction (amount, transaction_type, description, account_id)
                VALUES (%s, %s, %s, %s)
            """, (100.00, 'credit', 'Welcome bonus deposit', account_id))
            
            conn.commit()
            
            user = User(user_id, email, first_name, last_name)
            login_user(user)
            return redirect(url_for('dashboard'))
        except Error as e:
            conn.rollback()
            flash('Error creating account')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

# Cache for market data
market_data_cache = {
    'data': None,
    'timestamp': None,
    'expiry': timedelta(minutes=5)  # Cache expiry time
}

def get_cached_market_data():
    current_time = datetime.now()
    if (market_data_cache['data'] is not None and 
        market_data_cache['timestamp'] is not None and 
        current_time - market_data_cache['timestamp'] < market_data_cache['expiry']):
        return market_data_cache['data']
    
    # If cache is expired or empty, fetch new data
    market_data = get_market_data()
    market_data_cache['data'] = market_data
    market_data_cache['timestamp'] = current_time
    return market_data

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('index'))
        
        cursor = conn.cursor(dictionary=True)
        try:
            # 1. Get user accounts and recent transactions in a single query
            user_id = current_user.id
            cursor.execute("""
                SELECT a.*, 
                    (SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'id', t.id,
                            'amount', t.amount,
                            'transaction_type', t.transaction_type,
                            'description', t.description,
                            'timestamp', t.timestamp
                        )
                    )
                    FROM transaction t 
                    WHERE t.account_id = a.id 
                    ORDER BY t.timestamp DESC 
                    LIMIT 5
                    ) as recent_transactions
                FROM account a 
                WHERE a.user_id = %s
            """, (user_id,))
            accounts = cursor.fetchall()
            
            if not accounts:
                flash('No accounts found')
                return redirect(url_for('index'))
            
            # Convert JSON string to Python objects
            for account in accounts:
                if account['recent_transactions']:
                    account['transactions'] = json.loads(account['recent_transactions'])
                else:
                    account['transactions'] = []
                del account['recent_transactions']
            
            # 2. Get spending categories data in a single query
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN LOWER(description) LIKE '%shopping%' THEN 'Shopping'
                        WHEN LOWER(description) LIKE '%bill%' THEN 'Bills'
                        WHEN LOWER(description) LIKE '%food%' THEN 'Food'
                        WHEN LOWER(description) LIKE '%transport%' THEN 'Transport'
                        ELSE 'Other'
                    END AS category,
                    COALESCE(SUM(amount), 0) AS total_amount
                FROM transaction t
                JOIN account a ON t.account_id = a.id
                WHERE a.user_id = %s 
                    AND t.transaction_type = 'debit'
                GROUP BY category
                ORDER BY total_amount DESC
            """, (user_id,))
            spending_categories = cursor.fetchall()
            
            # 3. Get monthly data in a single query
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(timestamp, '%Y-%m') AS month,
                    COALESCE(SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END), 0) AS expenses
                FROM transaction t
                JOIN account a ON t.account_id = a.id
                WHERE a.user_id = %s
                GROUP BY DATE_FORMAT(timestamp, '%Y-%m')
                ORDER BY month DESC
                LIMIT 6
            """, (user_id,))
            monthly_data = cursor.fetchall()
            
            # Get market data from cache
            market_data = get_cached_market_data()
            
            return render_template('dashboard.html', 
                                accounts=accounts, 
                                spending_categories=spending_categories,
                                monthly_data=monthly_data,
                                market_data=market_data)
                                
        except Error as e:
            print(f"Database error in dashboard: {e}")
            flash(f'Error loading dashboard data: {str(e)}')
            return redirect(url_for('index'))
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Unexpected error in dashboard: {e}")
        flash(f'An unexpected error occurred: {str(e)}')
        return redirect(url_for('index'))

def process_loan_approval(loan_id, account_id, loan_amount):
    """Background task to process loan approval after 1 minute"""
    time.sleep(60)  # Wait for 1 minute
    
    conn = get_db_connection()
    if not conn:
        print("Database connection error in loan approval")
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Start transaction
        conn.start_transaction()
        
        # Update loan status to Approved
        cursor.execute("""
            UPDATE loan 
            SET status = 'APPROVED'  
            WHERE loan_id = %s
        """, (loan_id,))
        
        # Add loan amount to user's account
        cursor.execute("""
            UPDATE account 
            SET balance = balance + %s 
            WHERE id = %s
        """, (float(loan_amount), account_id))
        
        # Record the loan disbursement transaction
        cursor.execute("""
            INSERT INTO transaction (amount, transaction_type, description, account_id)
            VALUES (%s, 'credit', %s, %s)
        """, (float(loan_amount), f"Loan disbursement - Loan ID: {loan_id}", account_id))
        
        conn.commit()
        print(f"Loan {loan_id} approved and amount {loan_amount} added to account {account_id}")
    except Error as e:
        conn.rollback()
        print(f"Error processing loan approval: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route('/loan', methods=['GET', 'POST'])
@login_required
def loan():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Get user's accounts
            cursor.execute("SELECT * FROM account WHERE user_id = %s", (current_user.id,))
            accounts = cursor.fetchall()
            
            # Get loan requirements for each loan type
            cursor.execute("SELECT DISTINCT loan_type FROM loan_requirements")
            loan_types = [row['loan_type'] for row in cursor.fetchall()]
            
            # Get recent loans
            cursor.execute("""
                SELECT * FROM loan 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (current_user.id,))
            loans = cursor.fetchall()
            
            return render_template('loan.html', 
                                accounts=accounts, 
                                loans=loans,
                                loan_types=loan_types)
        finally:
            cursor.close()
            conn.close()
    
    elif request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Get form data
            account_number = request.form['account']
            loan_type = request.form['loan_type']
            amount = float(request.form['amount'])
            tenure = int(request.form['tenure'])
            description = request.form['description']
            
            # Get loan requirements for the selected loan type
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM loan_requirements 
                WHERE loan_type = %s
            """, (loan_type,))
            requirements = cursor.fetchall()
            
            # Validate all required fields
            for req in requirements:
                if req['is_required'] and not request.form.get(req['requirement_name']):
                    flash(f"Please provide {req['requirement_name']}")
                    return redirect(url_for('loan'))
            
            # Get account_id
            cursor.execute("SELECT id FROM account WHERE account_number = %s AND user_id = %s",
                         (account_number, current_user.id))
            account = cursor.fetchone()
            
            if not account:
                flash('Invalid account selected')
                return redirect(url_for('loan'))
            
            # Insert loan application
            cursor.execute("""
                INSERT INTO loan (user_id, account_id, loan_type, loan_amount, tenure_months, 
                                description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'PENDING', NOW())
            """, (current_user.id, account['id'], loan_type, amount, tenure, description))
            
            loan_id = cursor.lastrowid
            
            # Insert loan requirements data
            for req in requirements:
                cursor.execute("""
                    INSERT INTO loan_requirement_data (loan_id, requirement_name, value)
                    VALUES (%s, %s, %s)
                """, (loan_id, req['requirement_name'], request.form[req['requirement_name']]))
            
            conn.commit()
            flash('Loan application submitted successfully!')
            return redirect(url_for('dashboard'))
            
        except Error as e:
            conn.rollback()
            flash('Error submitting loan application')
            print(f"Error: {e}")
            return redirect(url_for('loan'))
        finally:
            cursor.close()
            conn.close()

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        from_account_number = request.form.get('from_account')
        to_account_number = request.form.get('to_account')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('transfer'))
        
        cursor = conn.cursor()
        try:
            # Start transaction
            conn.start_transaction()
            
            # Get source account ID from account number
            cursor.execute("SELECT id, balance FROM account WHERE account_number = %s AND user_id = %s", 
                         (from_account_number, current_user.id))
            source_account = cursor.fetchone()
            
            if not source_account:
                flash('Invalid source account number')
                return redirect(url_for('transfer'))
            
            source_account_id = source_account[0]
            source_balance = source_account[1]
            
            # Check if source account has sufficient balance
            if source_balance < amount:
                flash('Insufficient balance')
                return redirect(url_for('transfer'))
            
            # Get destination account ID from account number
            cursor.execute("SELECT id FROM account WHERE account_number = %s", (to_account_number,))
            dest_account = cursor.fetchone()
            
            if not dest_account:
                flash('Invalid destination account number')
                return redirect(url_for('transfer'))
            
            dest_account_id = dest_account[0]
            
            # Update source account balance
            cursor.execute("UPDATE account SET balance = balance - %s WHERE id = %s", 
                         (amount, source_account_id))
            
            # Update destination account balance
            cursor.execute("UPDATE account SET balance = balance + %s WHERE id = %s", 
                         (amount, dest_account_id))
            
            # Record transaction for source account
            cursor.execute("""
                INSERT INTO transaction (amount, transaction_type, description, account_id)
                VALUES (%s, 'debit', %s, %s)
            """, (amount, description, source_account_id))
            
            # Record transaction for destination account
            cursor.execute("""
                INSERT INTO transaction (amount, transaction_type, description, account_id)
                VALUES (%s, 'credit', %s, %s)
            """, (amount, description, dest_account_id))
            
            conn.commit()
            flash('Transfer successful!')
            return redirect(url_for('dashboard'))
        except Error as e:
            conn.rollback()
            flash('Error processing transfer')
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    # GET request - show transfer form
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM account WHERE user_id = %s", (current_user.id,))
        accounts = cursor.fetchall()
        
        # Get recent transactions for each account
        for account in accounts:
            cursor.execute("""
                SELECT * FROM transaction 
                WHERE account_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (account['id'],))
            account['transactions'] = cursor.fetchall()
            
        return render_template('transfer.html', accounts=accounts)
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/gototransfer')
def gototransfer():
    return render_template('transfer.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/fetchaccounts')
def fetchaccounts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM account WHERE user_id = %s", (current_user.id,))
        accounts = cursor.fetchall()
        return jsonify(accounts)
    finally:
        cursor.close()
        conn.close()

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        try:
            account_id = request.form.get('account')
            amount = float(request.form.get('amount'))
            description = request.form.get('description')
            
            if not account_id or amount <= 0:
                flash('Invalid deposit amount or account selected')
                return redirect(url_for('deposit'))
            
            conn = get_db_connection()
            if not conn:
                flash('Database connection error')
                return redirect(url_for('deposit'))
            
            cursor = conn.cursor()
            try:
                # Verify account belongs to current user
                cursor.execute("SELECT id, account_number FROM account WHERE id = %s AND user_id = %s", 
                             (account_id, current_user.id))
                account = cursor.fetchone()
                
                if not account:
                    flash('Invalid account selected')
                    return redirect(url_for('deposit'))
                
                # Update account balance
                cursor.execute("UPDATE account SET balance = balance + %s WHERE id = %s", 
                             (amount, account_id))
                
                # Record transaction
                cursor.execute("""
                    INSERT INTO transaction (amount, transaction_type, description, account_id)
                    VALUES (%s, %s, %s, %s)
                """, (amount, 'credit', description or f"Deposit to {account[1]}", account_id))
                
                conn.commit()
                flash('Deposit successful!')
                return redirect(url_for('dashboard'))
            except Error as e:
                conn.rollback()
                flash('Error processing deposit')
                print(f"Database error: {e}")
                return redirect(url_for('deposit'))
            finally:
                cursor.close()
                conn.close()
        except ValueError as e:
            flash('Invalid amount entered')
            print(f"Value error: {e}")
            return redirect(url_for('deposit'))
        except Exception as e:
            flash('An unexpected error occurred')
            print(f"Unexpected error: {e}")
            return redirect(url_for('deposit'))
    
    # GET request - show deposit form
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error')
            return redirect(url_for('dashboard'))
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM account WHERE user_id = %s", (current_user.id,))
            accounts = cursor.fetchall()
            
            # Get recent transactions for each account
            for account in accounts:
                cursor.execute("""
                    SELECT * FROM transaction 
                    WHERE account_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """, (account['id'],))
                account['transactions'] = cursor.fetchall()
                
            return render_template('deposit.html', accounts=accounts)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        flash('Error loading deposit page')
        print(f"Error loading deposit page: {e}")
        return redirect(url_for('dashboard'))

# Alpha Vantage API functions
def get_stock_quote(symbol):
    """Get real-time stock quote from Alpha Vantage API"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": float(quote.get("10. change percent", "0%").replace("%", "")),
                "volume": int(quote.get("06. volume", 0)),
                "latest_trading_day": quote.get("07. latest trading day", "")
            }
        return None
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

def get_forex_rate(from_currency, to_currency):
    """Get real-time forex rate from Alpha Vantage API"""
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Realtime Currency Exchange Rate" in data:
            rate = data["Realtime Currency Exchange Rate"]
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": float(rate.get("5. Exchange Rate", 0)),
                "timestamp": rate.get("6. Last Refreshed", "")
            }
        return None
    except Exception as e:
        print(f"Error fetching forex data: {e}")
        return None

def get_market_data():
    """Get market data for dashboard"""
    market_data = {
        "stocks": [],
        "forex": []
    }
    
    # Get stock data for major indices
    stock_symbols = ["SPY", "DIA", "QQQ"]  # ETFs tracking S&P 500, Dow Jones, NASDAQ
    for symbol in stock_symbols:
        stock_data = get_stock_quote(symbol)
        if stock_data:
            market_data["stocks"].append(stock_data)
    
    # Get forex data
    forex_pairs = [("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY")]
    for from_curr, to_curr in forex_pairs:
        forex_data = get_forex_rate(from_curr, to_curr)
        if forex_data:
            market_data["forex"].append(forex_data)
    
    return market_data

# Custom template filters
@app.template_filter('format_number')
def format_number(value):
    """Format large numbers with K, M, B suffixes"""
    try:
        value = int(value)
        if value >= 1000000000:
            return f"{value/1000000000:.1f}B"
        elif value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return str(value)
    except (ValueError, TypeError):
        return value

# Add this after the existing tables
def create_loan_requirements_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_requirements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                loan_type VARCHAR(50) NOT NULL,
                requirement_name VARCHAR(100) NOT NULL,
                requirement_type VARCHAR(50) NOT NULL,
                is_required BOOLEAN DEFAULT TRUE,
                description TEXT,
                UNIQUE KEY unique_loan_requirement (loan_type, requirement_name)
            )
        """)
        
        # Insert default requirements for different loan types
        requirements = [
            # Home Loan Requirements
            ('Home Loan', 'age', 'number', True, 'Applicant must be at least 18 years old'),
            ('Home Loan', 'property_value', 'number', True, 'Estimated value of the property'),
            ('Home Loan', 'property_address', 'text', True, 'Address of the property'),
            ('Home Loan', 'employment_status', 'select', True, 'Current employment status'),
            ('Home Loan', 'annual_income', 'number', True, 'Annual income in USD'),
            ('Home Loan', 'credit_score', 'number', True, 'Current credit score'),
            
            # Student Loan Requirements
            ('Education Loan', 'student_id', 'text', True, 'Valid student ID number'),
            ('Education Loan', 'institution_name', 'text', True, 'Name of educational institution'),
            ('Education Loan', 'course_name', 'text', True, 'Name of the course/program'),
            ('Education Loan', 'course_duration', 'number', True, 'Duration of course in months'),
            ('Education Loan', 'expected_graduation', 'date', True, 'Expected graduation date'),
            ('Education Loan', 'parent_income', 'number', True, 'Parent/Guardian annual income'),
            
            # Personal Loan Requirements
            ('Personal Loan', 'purpose', 'text', True, 'Purpose of the loan'),
            ('Personal Loan', 'employment_status', 'select', True, 'Current employment status'),
            ('Personal Loan', 'monthly_income', 'number', True, 'Monthly income in USD'),
            ('Personal Loan', 'credit_score', 'number', True, 'Current credit score'),
            
            # Car Loan Requirements
            ('Car Loan', 'car_model', 'text', True, 'Model of the car'),
            ('Car Loan', 'car_year', 'number', True, 'Year of manufacture'),
            ('Car Loan', 'car_price', 'number', True, 'Price of the car'),
            ('Car Loan', 'down_payment', 'number', True, 'Down payment amount'),
            ('Car Loan', 'employment_status', 'select', True, 'Current employment status')
        ]
        
        cursor.executemany("""
            INSERT IGNORE INTO loan_requirements 
            (loan_type, requirement_name, requirement_type, is_required, description)
            VALUES (%s, %s, %s, %s, %s)
        """, requirements)
        
        conn.commit()
    except Error as e:
        print(f"Error creating loan requirements table: {e}")
    finally:
        cursor.close()
        conn.close()

# Add this after the existing tables
def create_loan_requirement_data_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_requirement_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                loan_id INT NOT NULL,
                requirement_name VARCHAR(100) NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (loan_id) REFERENCES loan(id) ON DELETE CASCADE,
                UNIQUE KEY unique_loan_requirement (loan_id, requirement_name)
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Error creating loan requirement data table: {e}")
    finally:
        cursor.close()
        conn.close()

# Call these functions when initializing the app
create_loan_requirements_table()
create_loan_requirement_data_table()

@app.route('/card', methods=['GET'])
def card():
    return render_template('card.html')

@app.route('/get_loan_requirements', methods=['GET'])
@login_required
def get_loan_requirements():
    loan_type = request.args.get('loan_type')
    if not loan_type:
        return jsonify([])
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM loan_requirements 
            WHERE loan_type = %s
        """, (loan_type,))
        requirements = cursor.fetchall()
        return jsonify(requirements)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True) 