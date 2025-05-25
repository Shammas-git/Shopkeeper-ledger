# Standard library imports
import os  # For accessing environment variables
from datetime import datetime  # For handling dates and times

# Third-party imports
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify  # Core Flask functionality
from flask_login import login_user, logout_user, login_required, current_user  # Authentication tools
from werkzeug.security import generate_password_hash, check_password_hash  # Password security
from wtforms import SelectField  # Form field for selections/dropdowns
from wtforms.validators import DataRequired  # Form validation

# Local application imports
from app import db, app  # Database and Flask app instances
from models import User, Customer, Transaction  # Database models
from forms import LoginForm, RegistrationForm, CustomerForm, TransactionForm, UserSwitchForm, EditUserForm  # Forms for data entry


# Helper function to check if a request is AJAX (Asynchronous JavaScript And XML)
def is_ajax_request():
    """
    Determines if the current request is an AJAX request.

    AJAX requests are sent by JavaScript and expect data rather than full HTML pages.
    This function checks for a special header that JavaScript libraries typically set.

    Returns:
        bool: True if it's an AJAX request, False otherwise
    """
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def handle_response(template=None, redirect_url=None, **context):
    """
    Handle responses for both regular and AJAX requests.

    This function provides a consistent way to handle responses based on request type.
    For AJAX requests, it sends JSON responses.
    For regular requests, it sends full HTML page responses.

    Args:
        template (str, optional): HTML template to render for regular requests
        redirect_url (str, optional): URL to redirect to
        **context: Additional data to pass to the template

    Returns:
        Response: Either a redirect, JSON response, or rendered HTML template
    """
    # For redirects - when we want to send the user to a different page
    if redirect_url:
        if is_ajax_request():
            # For AJAX requests, send a JSON response with the redirect URL
            # The JavaScript will handle the actual redirect
            return jsonify({"redirect": redirect_url})
        # For regular requests, use Flask's redirect function
        return redirect(redirect_url)

    # For template rendering - when we want to display a page
    if template:
        # Render the template with all the data passed in context
        return render_template(template, **context)


# Create a Blueprint for organizing routes
# Blueprints help organize large Flask applications into smaller components
routes = Blueprint('routes', __name__)


# Add current date and other context variables to all templates
@app.context_processor
def inject_context():
    """
    Inject common data into all templates automatically.

    This function runs before rendering any template and adds useful data
    that multiple pages need, such as current date and user-specific information.

    Returns:
        dict: Context data to be available in all templates
    """
    # Create a dictionary with basic context data
    context = {
        'now': datetime.now()  # Current date and time for displaying on pages
    }

    # Add data for logged in users only
    if current_user.is_authenticated:
        # Get 3 most recent customers for quick access in navigation menu
        recent_customers = Customer.query.filter_by(
            user_id=current_user.id).order_by(
                Customer.created_at.desc()  # Sort by newest first
            ).limit(3).all()  # Get only 3 results
        context['recent_customers'] = recent_customers

        # Add total balance information (how much money is owed overall)
        context['balance_summary'] = current_user.get_total_balance()

        # All registered users (for user switching) - only when authenticated
        context['all_users'] = User.query.all()
        context['user_switch_form'] = UserSwitchForm()
    else:
        # Don't add any data when not logged in - use empty values or None
        pass

    return context


@routes.route('/logout')
@login_required  # This decorator ensures only logged-in users can access this route
def logout():
    """
    Logout the current user.

    This route ends the user's session and redirects them to the home page.
    The @login_required decorator ensures only logged-in users can access this route.

    Returns:
        Response: Redirect to the home page
    """
    logout_user()  # End the user session (provided by Flask-Login)
    flash('You have been logged out.', 'info')  # Show a notification message
    return redirect(url_for('routes.index'))  # Redirect to the home page


@routes.route('/')
def index():
    """
    Home page route.

    This is the landing page of the application. If the user is already logged in,
    they are automatically redirected to the dashboard. Otherwise, they see the 
    welcome page with login/register options.

    Returns:
        Response: Either a redirect to dashboard (if logged in) or the index template
    """
    # If user is already logged in, send them to the dashboard
    if current_user.is_authenticated:
        return handle_response(redirect_url=url_for('routes.dashboard'))

    # Otherwise show the welcome page
    return handle_response(template='index.html')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.

    This route handles both displaying the login form (GET request)
    and processing the login attempt (POST request).

    Returns:
        Response: Either the login form or a redirect after login attempt
    """
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return handle_response(redirect_url=url_for('routes.dashboard'))

    # Create login form instance
    form = LoginForm()

    # Check if this is a form submission (POST request)
    if request.method == 'POST':
        # Get email and password directly from the form data
        email = request.form.get('email')  # Get the email field value
        password = request.form.get('password')  # Get the password field value

        # Make sure both fields were filled in
        if not email or not password:
            flash('Please enter both email and password',
                  'danger')  # Show error message
            return handle_response(template='login.html',
                                   form=form)  # Return to login page

        # Try to find a user with this email in the database
        user = User.query.filter_by(email=email).first()

        # If no user was found with this email
        if not user:
            # Suggest registration instead
            flash('No account found with this email. Please register first.',
                  'info')
            return handle_response(redirect_url=url_for('routes.register'))

        # If the user account doesn't have a password (perhaps created another way)
        if not user.password_hash:
            flash(
                'This account does not have a password set. Please contact the administrator.',
                'info')
            return handle_response(template='login.html', form=form)

        # Check if the password is correct using secure hash comparison
        if check_password_hash(user.password_hash, password):
            # Password is correct, log the user in
            login_user(user)  # This creates a login session for the user
            flash('Login successful!', 'success')  # Show success message

            # Check if the user was trying to access a protected page before login
            next_page = request.args.get(
                'next')  # Get the 'next' URL parameter if it exists

            # Redirect to that page, or to the dashboard if no specific page was requested
            return handle_response(
                redirect_url=next_page or url_for('routes.dashboard'))
        else:
            # Password is incorrect
            flash('Incorrect password. Please try again.', 'warning')

    # For a GET request or failed login, display the login form
    return handle_response(template='login.html', form=form)


@routes.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page.

    This route handles both displaying the registration form (GET request)
    and processing new user registration (POST request).

    Returns:
        Response: Either the registration form or a redirect after registration
    """
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return handle_response(redirect_url=url_for('routes.dashboard'))

    # Create registration form instance
    form = RegistrationForm()

    # Check if this is a form submission (POST request)
    if request.method == 'POST':
        # Get form data directly from the request
        username = request.form.get('username')  # Get the username field value
        email = request.form.get('email')  # Get the email field value
        password = request.form.get('password')  # Get the password field value
        password2 = request.form.get(
            'password2')  # Get the password confirmation value

        # Make sure all required fields were filled in
        if not username or not email or not password or not password2:
            flash('Please fill out all required fields',
                  'danger')  # Show error message
            return handle_response(template='register.html',
                                   form=form)  # Return to registration page

        # Make sure passwords match
        if password != password2:
            flash('Passwords do not match', 'danger')  # Show error message
            return handle_response(template='register.html',
                                   form=form)  # Return to registration page

        try:
            # Check if a user with this email or username already exists
            user_email = User.query.filter_by(
                email=email).first()  # Look for existing email
            user_name = User.query.filter_by(
                username=username).first()  # Look for existing username

            if user_email:
                # If email is already registered, suggest login instead
                flash(
                    'Email already registered. Please use a different email or login.',
                    'info')
                return handle_response(redirect_url=url_for('routes.login'))

            elif user_name:
                # If username is taken, ask for a different one
                flash(
                    'Username already taken. Please choose a different username.',
                    'info')
                return handle_response(template='register.html', form=form)
            else:
                # All checks passed, create the new user account
                # Convert the plain text password to a secure hash
                password_hash = generate_password_hash(password)

                # Create new user object with the provided data
                user = User(username=username,
                            email=email,
                            password_hash=password_hash)

                # Add to database and save changes
                db.session.add(user)
                db.session.commit()

                # Auto-login the user so they don't have to login again right after registration
                login_user(user)

                # Show success message
                flash('Registration successful! You are now logged in.',
                      'success')

                # Redirect to the dashboard
                return handle_response(
                    redirect_url=url_for('routes.dashboard'))
        except Exception as e:
            # If any error occurs during registration
            db.session.rollback()  # Undo any database changes
            app.logger.error(f"Registration error: {str(e)}")  # Log the error
            flash('An error occurred during registration. Please try again.',
                  'danger')  # Show error message

    # For a GET request or failed registration, display the registration form
    return handle_response(template='register.html', form=form)


@app.context_processor
def inject_my_var():
    return dict(is_mobile=any(
        device in request.headers.get("User-Agent")
        for device in ["Android", "iPhone", "iPad", "iPod", "Windows Phone"]))


@routes.route('/dashboard')
@login_required  # This decorator ensures only logged-in users can access this route
def dashboard():
    """
    User dashboard showing customers with optional search functionality.

    This is the main page users see after logging in. It displays a list of
    all customers with their balances, and allows searching for specific customers.

    Returns:
        Response: Rendered dashboard template with customer data
    """
    # Get search query from URL parameters, default to empty string if not provided
    search_query = request.args.get('search', '')

    # Start with a base query that only shows customers belonging to the current user
    query = Customer.query.filter_by(user_id=current_user.id)

    # If a search term was provided, filter results to match that term
    if search_query:
        # Add % wildcards for SQL LIKE query (finds partial matches)
        search_term = f"%{search_query}%"

        # Search across multiple fields using the OR operator (|)
        query = query.filter(
            (Customer.name.ilike(search_term)) |  # Search in customer name
            (Customer.phone.ilike(search_term)) |  # Search in phone number
            (Customer.address.ilike(search_term))  # Search in address
        )

    # Get all matching customers sorted alphabetically by name
    customers = query.order_by(Customer.name).all()

    # For each customer, load their most recent transactions to display in dashboard
    for customer in customers:
        # Get all transactions for this customer ordered by date (newest first)
        customer.transactions = Transaction.query.filter_by(
            customer_id=customer.id).order_by(Transaction.date.desc()).all()

    # Get additional statistics for the dashboard
    # Count how many customers the current user has
    customers_count = Customer.query.filter_by(user_id=current_user.id).count()

    # Find the first customer (by ID) for quick navigation
    first_customer = Customer.query.filter_by(
        user_id=current_user.id).order_by(Customer.id).first()
    first_customer_id = first_customer.id if first_customer else None

    # Render the dashboard template with all the data
    return handle_response(
        template=
        'customers.html',  # Using customers.html as the dashboard template
        customers=customers,  # Pass the list of customers
        search_query=search_query,  # Pass the search term (for form value)
        customers_count=customers_count,  # Pass total customer count
        first_customer_id=first_customer_id)  # Pass ID of first customer


@routes.route('/customers/add', methods=['GET', 'POST'])
@login_required  # This decorator ensures only logged-in users can access this route
def add_customer():
    """
    Add a new customer to the system.

    This route handles both displaying the customer form (GET request)
    and creating a new customer (POST request).

    Returns:
        Response: Either the customer form or a redirect after successful creation
    """
    # Create a blank customer form
    form = CustomerForm()

    # Process form submission only if it passed validation (POST with valid data)
    if form.validate_on_submit():
        # Check if this is an AJAX request (might be an auto-save from the frontend)
        is_ajax = is_ajax_request()

        # Only create a new customer if:
        # 1. It's not an AJAX request (regular form submission), OR
        # 2. It's an AJAX request with an explicit submit parameter
        # This prevents accidental creation from auto-save functionality
        if not is_ajax or request.form.get('submit'):
            # Create a new Customer object with form data
            customer = Customer(
                name=form.name.data,  # Customer name from form
                phone=form.phone.data,  # Phone number from form
                address=form.address.data,  # Address from form
                user_id=current_user.id,  # Link to current logged-in user
                is_whatsapp=form.is_whatsapp.data)

            # Save to database
            db.session.add(customer)  # Add new customer to database
            db.session.commit()  # Save the changes permanently

            # Show success message
            flash('Customer added successfully!', 'success')

            # Redirect to dashboard to see all customers
            return handle_response(redirect_url=url_for('routes.dashboard'))

    # For GET requests or invalid form submissions, display the customer form
    return handle_response(template='customer_detail.html',
                           form=form,
                           title="Add Customer")


@routes.route('/customers/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def customer_detail(customer_id):
    """View and edit customer details with auto-save functionality"""
    customer = Customer.query.get_or_404(customer_id)

    # Ensure the customer belongs to the current user
    if customer.user_id != current_user.id:
        abort(403)  # Forbidden

    form = CustomerForm(obj=customer)

    # Handle form submission - auto-save on any change
    if form.validate_on_submit():
        # Check if this is a manual save (submitted by the form button)
        is_manual_save = request.form.get('submit') == '1'
        is_ajax = is_ajax_request()

        # Apply form changes to customer
        form.populate_obj(customer)
        db.session.commit()

        # For AJAX requests (auto-save), return JSON response
        if is_ajax and not is_manual_save:
            # Get updated total balance
            balance_summary = current_user.get_total_balance()

            return jsonify({
                'success': True,
                'message': 'Customer details updated',
                'message_type': 'success',
                'balance_summary': balance_summary
            })

        # For regular form submissions or manual AJAX saves
        flash('Customer details updated', 'success')
        return handle_response(redirect_url=url_for('routes.customer_detail',
                                                    customer_id=customer_id))

    # For GET requests
    transactions = Transaction.query.filter_by(
        customer_id=customer.id).order_by(Transaction.date.desc()).all()
    balance = customer.get_balance()

    return handle_response(template='customer_detail.html',
                           form=form,
                           customer=customer,
                           transactions=transactions,
                           balance=balance,
                           title="Edit Customer")


@routes.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    """Delete a customer and all their transactions"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        # Ensure the customer belongs to the current user
        if customer.user_id != current_user.id:
            abort(403)  # Forbidden

        # Store customer name before deleting for message
        customer_name = customer.name

        # Delete all transactions first to avoid any cascade issues
        Transaction.query.filter_by(customer_id=customer_id).delete()

        # Now delete the customer
        db.session.delete(customer)
        db.session.commit()

        flash(f'Customer {customer_name} deleted successfully', 'success')

        # Always redirect to dashboard after deletion, regardless of request type
        if is_ajax_request():
            # Get updated total balance
            balance_summary = current_user.get_total_balance()

            # Return a JSON response with a redirect
            return jsonify({
                'success': True,
                'message': f'Customer {customer_name} deleted successfully',
                'message_type': 'success',
                'redirect': url_for('routes.dashboard'),
                'balance_summary': balance_summary
            })

        # For non-AJAX requests, redirect directly to dashboard
        return redirect(url_for('routes.dashboard'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting customer {customer_id}: {str(e)}")
        flash(
            'An error occurred while deleting the customer. Please try again.',
            'danger')
        return handle_response(redirect_url=url_for('routes.dashboard'))


@routes.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction_global():
    """Add a new transaction with customer selection"""
    # Get list of customers for the dropdown
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(
        Customer.name).all()

    if not customers:
        flash('Please add a customer first before adding a transaction',
              'warning')
        return handle_response(redirect_url=url_for('routes.add_customer'))

    # Enhanced form with customer selection
    class GlobalTransactionForm(TransactionForm):
        customer_id = SelectField('Customer',
                                  choices=[],
                                  coerce=int,
                                  validators=[DataRequired()])

    form = GlobalTransactionForm()

    # Populate the customer choices
    form.customer_id.choices = [(c.id, c.name) for c in customers]

    if form.validate_on_submit():
        # Ensure amount is not None before applying abs()
        amount = form.amount.data or 0

        # Create transaction
        transaction = Transaction(
            amount=abs(amount),  # Store as positive value
            description=form.description.data,
            transaction_type=form.transaction_type.data,
            customer_id=form.customer_id.data)

        db.session.add(transaction)
        db.session.commit()

        # Get the customer for redirect
        customer = Customer.query.get(form.customer_id.data)

        # Show success message for transaction
        flash('Transaction recorded successfully', 'success')

        # For AJAX requests, include balance summary in the response
        if is_ajax_request():
            # Get updated total balance
            balance_summary = current_user.get_total_balance()

            return jsonify({
                'success': True,
                'message': 'Transaction recorded successfully',
                'message_type': 'success',
                'redirect': url_for('routes.all_transactions'),
                'balance_summary': balance_summary
            })

        return handle_response(redirect_url=url_for('routes.all_transactions'))

    return handle_response(template='add_transaction_global.html',
                           form=form,
                           customers=customers)


@routes.route('/customers/<int:customer_id>/add_transaction',
              methods=['GET', 'POST'])
@login_required
def add_transaction(customer_id):
    """Add a new transaction for a customer"""
    customer = Customer.query.get_or_404(customer_id)

    # Ensure the customer belongs to the current user
    if customer.user_id != current_user.id:
        abort(403)  # Forbidden

    form = TransactionForm()

    if form.validate_on_submit():
        # Ensure amount is not None before applying abs()
        amount = form.amount.data or 0

        # Create transaction
        transaction = Transaction(
            amount=abs(amount),  # Store as positive value
            description=form.description.data,
            transaction_type=form.transaction_type.data,
            customer_id=customer.id)

        db.session.add(transaction)
        db.session.commit()

        # Show success message for transaction
        flash('Transaction recorded successfully', 'success')

        # For AJAX requests, include balance summary in the response
        if is_ajax_request():
            # Get updated total balance
            balance_summary = current_user.get_total_balance()

            return jsonify({
                'success':
                True,
                'message':
                'Transaction recorded successfully',
                'message_type':
                'success',
                'redirect':
                url_for('routes.customer_detail', customer_id=customer.id),
                'balance_summary':
                balance_summary
            })

        return handle_response(redirect_url=url_for('routes.customer_detail',
                                                    customer_id=customer.id))

    return handle_response(template='add_transaction.html',
                           form=form,
                           customer=customer)


@routes.route('/transactions/<int:transaction_id>/delete', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        customer_id = transaction.customer_id

        # Ensure the transaction belongs to a customer owned by the current user
        customer = Customer.query.get(customer_id)
        if customer.user_id != current_user.id:
            abort(403)  # Forbidden

        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully', 'success')

        # For AJAX/SPA requests, return JSON with updated balance
        if is_ajax_request():
            # Get updated total balance
            balance_summary = current_user.get_total_balance()

            return jsonify({
                'success':
                True,
                'message':
                'Transaction deleted successfully',
                'message_type':
                'success',
                'redirect':
                url_for('routes.customer_detail', customer_id=customer_id),
                'balance_summary':
                balance_summary
            })

        # For non-AJAX requests, redirect directly
        return redirect(
            url_for('routes.customer_detail', customer_id=customer_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Error deleting transaction {transaction_id}: {str(e)}")
        flash(
            'An error occurred while deleting the transaction. Please try again.',
            'danger')
        return redirect(url_for('routes.all_transactions'))


@routes.route('/transactions')
@login_required
def all_transactions():
    """View all transactions across all customers"""

    # Get query parameters
    search_query = request.args.get('search', '')

    # Base query - get all transactions for the current user's customers
    query = Transaction.query.join(
        Customer, Transaction.customer_id == Customer.id).filter(
            Customer.user_id == current_user.id)

    # Apply search if provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter((Transaction.description.ilike(search_term))
                             | (Customer.name.ilike(search_term)))
    # Get sorted results - most recent first
    transactions = query.order_by(Transaction.date.desc()).all()
    return handle_response(template='transactions.html',
                           transactions=transactions,
                           search_query=search_query,
                           title="All Transactions")


@routes.route('/accounts', methods=['GET', 'POST'])
@login_required
def view_accounts():
    """View all registered accounts"""
    # Get all user accounts, including all their customer relationships
    user = User.query.options(db.joinedload(
        User.customers)).filter(User.id == current_user.id).first()

    # Create form for CSRF protection in switch user buttons
    user_switch_form = UserSwitchForm()

    return handle_response(template='accounts.html',
                           user=user,
                           user_switch_form=user_switch_form)


@routes.route('/accounts/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_account(user_id):
    """Delete a user account"""
    try:
        logout_user()  # End the user session (provided by Flask-Login)
        flash('You have been logged out.',
              'info')  # Show a notification message
        # Get the user to delete
        user = User.query.get_or_404(user_id)
        username = user.username
        # Delete all associated customers and transactions
        for customer in user.customers:
            Transaction.query.filter_by(customer_id=customer.id).delete()

        # Delete the customers associated with this user
        Customer.query.filter_by(user_id=user_id).delete()

        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        flash(
            f'Account {username} has been deleted along with all associated data',
            'success')
        return redirect(url_for('routes.index'))  # Redirect to the home page

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting account {user_id}: {str(e)}")
        flash(
            'An error occurred while deleting the account. Please try again.',
            'danger')
        return redirect(url_for('routes.view_accounts'))


@routes.route('/switch_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def switch_user(user_id):
    """Switch to a different user account with password verification"""
    try:
        # Get the user to switch to
        user = User.query.get_or_404(user_id)

        # Create a form for password verification
        form = UserSwitchForm()

        # Show password form for GET requests
        if request.method == 'GET':
            return render_template('switch_user.html',
                                   user=user,
                                   form=form,
                                   title=f"Edit account for {user.username}")

        # Validate the form if POST request
        if form.validate_on_submit():
            # Verify the password for the account being switched to
            if user.password_hash and not check_password_hash(
                    user.password_hash, form.password.data):
                flash('Incorrect password. Please try again.', 'danger')
                return render_template(
                    'switch_user.html',
                    user=user,
                    form=form,
                    title=f"Edit account for {user.username}")
            # Always use direct redirect for user switching
            flash(f'Now editing account for {user.username}', 'success')
            return redirect(url_for('routes.edit_account', user_id=user.id))
        else:
            # If form validation fails
            return render_template('switch_user.html',
                                   user=user,
                                   form=form,
                                   title=f"Edit account for {user.username}")

    except Exception as e:
        app.logger.error(f"Error editing user {user_id}: {str(e)}")
        flash('An error occurred while editing user. Please try again.',
              'danger')
        return redirect(url_for('routes.view_accounts'))


@routes.route('/edit_account', methods=['GET', 'POST'])
@login_required
def edit_account():

    user_id = current_user.id
    user = User.query.get_or_404(user_id)
    form = EditUserForm(request.form)

    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        return render_template('edit_account.html', form=form)

    if form.validate_on_submit():
        # Check if new password is provided and confirmation matches
        if form.new_password.data:

            if form.new_password.data != form.confirm_password.data:
                flash('New passwords do not match', 'danger')
                return render_template('edit_account.html', form=form)

        try:
            user.username = form.username.data
            user.email = form.email.data
            password = form.new_password.data
            user.password_hash = generate_password_hash(password)

            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('routes.edit_account'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your account.', 'danger')
            app.logger.error(f"Error updating account: {str(e)}")
            return render_template('edit_account.html', form=form)
    return render_template('edit_account.html', form=form)
