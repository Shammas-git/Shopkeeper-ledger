# Standard library imports
from datetime import datetime  # For handling date and time functionality

# Third-party imports
from flask_login import UserMixin  # Provides user authentication functionality

# Local application imports
from app import db  # Import database connection from app.py


class User(UserMixin, db.Model):
    """
    User model that stores information about registered users.
    
    UserMixin provides Flask-Login with the required methods for user authentication.
    
    Attributes:
        id: Unique identifier for each user (auto-incremented)
        username: User's display name (must be unique)
        email: User's email address (must be unique)
        password_hash: Securely stored password hash (NOT the actual password)
        customers: All customers belonging to this user
    """
    id = db.Column(db.Integer, primary_key=True)  # Primary key, auto-increments
    username = db.Column(db.String(64), unique=True, nullable=False)  # Username must be unique and is required
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email must be unique and is required
    # Ensure password hash field has length of at least 256 for security
    password_hash = db.Column(db.String(256))  # Stores the hashed password, not the actual password
    
    # Relationships - this creates a connection to Customer model
    # 'backref' creates a property on Customer instances to access the owner (User)
    # 'lazy=True' means data will be loaded only when accessed
    customers = db.relationship('Customer', backref='owner', lazy=True)
    
    def __repr__(self):
        """
        Provides a readable representation of the User object for debugging.
        
        Returns:
            str: A string representation of the user
        """
        return f'<User {self.username}>'
    
    def get_total_balance(self):
        """
        Calculate total balance across all customers of this user.
        
        Positive balance means customers owe money to the user (credit).
        Negative balance means user owes money to customers (debit).
        
        Returns:
            dict: Dictionary containing total credit, total debit, and net balance
        """
        total_credit = 0  # Initialize total money owed to the user
        total_debit = 0   # Initialize total money the user owes to others
        
        # Loop through each customer of this user
        for customer in self.customers:
            customer_balance = customer.get_balance()  # Get individual customer balance
            if customer_balance > 0:  # Positive balance means customer owes money (credit)
                total_credit += customer_balance
            elif customer_balance < 0:  # Negative balance means you owe customer (debit)
                total_debit += abs(customer_balance)  # Use abs() to convert to positive number for sum
        
        # Return a dictionary with all balance information
        return {
            'total_credit': total_credit,  # Total money customers owe to the user
            'total_debit': total_debit,    # Total money the user owes to customers
            'net_balance': total_credit - total_debit  # Overall financial position
        }


class Customer(db.Model):
    """
    Customer model that stores information about each customer.
    
    A customer belongs to a specific user (shop owner) and can have many transactions.
    
    Attributes:
        id: Unique identifier for each customer
        name: Customer's name
        phone: Customer's phone number (optional)
        email: Customer's email address (optional)
        address: Customer's address (optional)
        created_at: When the customer was first added
        user_id: The ID of the user (shop owner) this customer belongs to
        transactions: All transactions associated with this customer
    """
    id = db.Column(db.Integer, primary_key=True)  # Primary key, auto-increments
    name = db.Column(db.String(100), nullable=False)  # Customer name is required
    phone = db.Column(db.String(20))  # Phone number is optional
    email = db.Column(db.String(120))  # Email is optional
    address = db.Column(db.String(200))  # Address is optional
    is_whatsapp = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set to current time when created
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Links to User model, required
    
    # Relationships - this creates a connection to Transaction model
    # 'cascade="all, delete"' means when customer is deleted, all their transactions are deleted too
    transactions = db.relationship('Transaction', backref='customer', lazy=True, cascade="all, delete")
    
    def __repr__(self):
        """
        Provides a readable representation of the Customer object for debugging.
        
        Returns:
            str: A string representation of the customer
        """
        return f'<Customer {self.name}>'
    
    def get_balance(self):
        """
        Calculate the current balance for this customer.
        
        Positive balance means the customer owes money to the shop owner.
        Negative balance means the shop owner owes money to the customer.
        
        Returns:
            float: The current balance (credit - debit)
        """
        # Sum all debit transactions (money given to customer)
        total_debit = sum(t.amount for t in self.transactions if t.transaction_type == 'debit')
        
        # Sum all credit transactions (money received from customer)
        total_credit = sum(t.amount for t in self.transactions if t.transaction_type == 'credit')
        
        # Return the difference (positive means customer owes money, negative means you owe money)
        return total_credit - total_debit


class Transaction(db.Model):
    """
    Transaction model that stores information about each financial transaction.
    
    Each transaction belongs to a specific customer and records money given or received.
    
    Attributes:
        id: Unique identifier for each transaction
        amount: The amount of money involved in the transaction
        description: Optional description of what the transaction was for
        transaction_type: Whether it was 'debit' (money given to customer) or 'credit' (money received)
        date: When the transaction occurred
        customer_id: The ID of the customer this transaction belongs to
    """
    id = db.Column(db.Integer, primary_key=True)  # Primary key, auto-increments
    amount = db.Column(db.Float, nullable=False)  # Transaction amount, required
    description = db.Column(db.String(200))  # Optional description of the transaction
    transaction_type = db.Column(db.String(10), nullable=False)  # 'debit' or 'credit', required
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set to current time when created
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  # Links to Customer model, required
    
    def __repr__(self):
        """
        Provides a readable representation of the Transaction object for debugging.
        
        Returns:
            str: A string representation of the transaction
        """
        return f'<Transaction {self.id} - {self.amount}>'
