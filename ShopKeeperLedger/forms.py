# Third-party imports
from flask_wtf import FlaskForm  # Base form class with CSRF protection
from wtforms import (  # Import field types for forms
    StringField,  # For text input
    PasswordField,  # For password input (masks the text)
    SubmitField,  # For submit buttons
    FloatField,  # For decimal numbers like prices
    TextAreaField,  # For multi-line text input
    SelectField,  # For dropdown selection
    TelField,  # For telephone numbers
    EmailField,  # For email addresses with validation
    BooleanField)
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Email  # Form validation helpers


class LoginForm(FlaskForm):
    """
    Form for user login.

    This form collects user credentials (email and password) for authentication.

    Fields:
        email: User's email address (required)
        password: User's password (required)
        submit: Button to submit the form
    """
    email = EmailField('Email',
                       validators=[DataRequired()])  # Email field is required
    password = PasswordField('Password',
                             validators=[DataRequired()
                                         ])  # Password field is required
    submit = SubmitField('Sign In')  # Submit button with "Sign In" label


class RegistrationForm(FlaskForm):
    # Username with validation (required and length between 2-64 characters)
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=2, max=64)])

    # Email field (required)
    email = EmailField('Email', validators=[DataRequired()])

    # Password field (required and minimum 8 characters)
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         Length(min=8)])

    # Password confirmation field (must match password field)
    # EqualTo validator ensures both password fields have the same value
    password2 = PasswordField('Repeat Password',
                              validators=[DataRequired(),
                                          EqualTo('password')])

    submit = SubmitField('Register')  # Submit button with "Register" label


class CustomerForm(FlaskForm):
    """
    Form for adding or editing customer information.

    This form collects customer details for the shop's records.

    Fields:
        name: Customer's name (required, max 100 characters)
        phone: Customer's phone number (optional, max 20 characters)
        email: Customer's email address (optional, max 120 characters)
        address: Customer's physical address (optional, max 200 characters)
        submit: Button to submit the form
    """
    # Customer name (required, maximum 100 characters)
    name = StringField('Customer Name',
                       validators=[DataRequired(),
                                   Length(max=100)])

    # Phone number (optional, maximum 20 characters)
    phone = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Length(min=12,
                   max=12,
                   message="Incomplete number. Must be exactly 12 digits.")
        ])

    # Address field (optional, maximum 200 characters)
    # TextAreaField allows for multi-line input
    address = TextAreaField('Address',
                            validators=[Optional(),
                                        Length(max=200)])

    is_whatsapp = BooleanField('WhatsApp', default=False)

    submit = SubmitField(
        'Save Customer')  # Submit button with "Save Customer" label


class TransactionForm(FlaskForm):
    """
    Form for recording financial transactions with customers.

    This form collects details about money exchanged between the shop owner and customers.

    Fields:
        amount: Money amount in the transaction (required)
        description: What the transaction was for (optional, max 200 characters)
        transaction_type: Whether money was received or given (required dropdown)
        submit: Button to submit the form
    """
    # Amount field for the transaction value (required)
    amount = FloatField('Total Amount', validators=[DataRequired()])

    # Description of what the transaction was for (optional, maximum 200 characters)
    description = TextAreaField('Description',
                                validators=[Optional(),
                                            Length(max=200)])

    # Dropdown selection for transaction type with two options:
    # - credit: money received from customer (customer owes you)
    # - debit: money given to customer (you owe customer)
    transaction_type = SelectField('Transaction Type',
                                   choices=[
                                       ('credit',
                                        'Received from customer (Credit)'),
                                       ('debit', 'Given to customer (Debit)')
                                   ],
                                   validators=[DataRequired()])

    submit = SubmitField(
        'Record Transaction')  # Submit button with "Record Transaction" label


class UserSwitchForm(FlaskForm):
    """
    Form for the user switcher dropdown with password verification.

    This form is used when switching between different user accounts.
    It requires password verification to prevent unauthorized access.

    Fields:
        password: Password for the account being switched to (required)
        submit: Button to submit the form
    """
    # Password field to verify user identity (required)
    password = PasswordField('Password', validators=[DataRequired()])

    # Submit button with "Switch User" label
    submit = SubmitField('Proceed to Edit')


class EditUserForm(FlaskForm):
    # Username with validation (required and length between 2-64 characters)
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=2, max=64)])

    # Email field with validation (required and must be valid email format)
    email = EmailField('Email', validators=[DataRequired(), Email()])

    # New password field (optional - only validate if provided)
    new_password = PasswordField('New Password',
                                 validators=[Length(min=8, max=128)])

    # Password confirmation field (must match if new_password is provided)
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[EqualTo('new_password', message='Passwords must match')])

    submit = SubmitField('Update Profile')
