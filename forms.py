"""
Gantabya Travel Booking System - Form Definitions
This file contains all WTForms for validation and CSRF protection.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, TextAreaField, 
    IntegerField, FloatField, SelectField, DateField, 
    BooleanField, FileField, HiddenField, TelField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, 
    NumberRange, ValidationError, Regexp
)
from wtforms.validators import InputRequired


# ==================== CUSTOM VALIDATORS ====================

def validate_phone_number(form, field):
    """Custom validator for phone numbers"""
    if field.data:
        import re
        # Phone number regex for Nepal and international numbers
        pattern = r'^[\+\d\s\-\(\)]{8,20}$'
        if not re.match(pattern, field.data):
            raise ValidationError('Please enter a valid phone number')


def validate_booking_number(form, field):
    """Custom validator for booking number format"""
    if field.data:
        import re
        pattern = r'^[A-Z0-9]{8}$'
        if not re.match(pattern, field.data.upper()):
            raise ValidationError('Booking number must be 8 characters (letters and numbers only)')


# ==================== CUSTOMER FORMS ====================

class SignupForm(FlaskForm):
    """Customer registration form"""
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(message='Full name is required'),
            Length(min=3, max=100, message='Name must be between 3 and 100 characters')
        ]
    )
    
    email = EmailField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120)
        ]
    )
    
    phone = TelField(
        'Phone Number',
        validators=[
            Optional(),
            validate_phone_number
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=6, max=100, message='Password must be at least 6 characters')
        ]
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ]
    )
    
    address = TextAreaField(
        'Address',
        validators=[
            Optional(),
            Length(max=200)
        ]
    )


class LoginForm(FlaskForm):
    """Customer login form"""
    email = EmailField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ]
    )
    
    remember_me = BooleanField('Remember Me')


# ==================== ADMIN FORMS ====================

class AdminLoginForm(FlaskForm):
    """Admin login form"""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=50)
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ]
    )


class PackageForm(FlaskForm):
    """Package management form for admin"""
    title = StringField(
        'Package Title',
        validators=[
            DataRequired(message='Package title is required'),
            Length(min=3, max=100)
        ]
    )
    
    country = StringField(
        'Country',
        validators=[
            DataRequired(message='Country is required'),
            Length(min=2, max=100)
        ]
    )
    
    city = StringField(
        'City',
        validators=[
            Optional(),
            Length(max=100)
        ]
    )
    
    price = FloatField(
        'Price (per person)',
        validators=[
            DataRequired(message='Price is required'),
            NumberRange(min=0, message='Price must be positive')
        ]
    )
    
    discount_price = FloatField(
        'Discounted Price',
        validators=[
            Optional(),
            NumberRange(min=0, message='Discount price must be positive')
        ]
    )
    
    duration_days = IntegerField(
        'Duration (Days)',
        validators=[
            Optional(),
            NumberRange(min=1, max=365)
        ]
    )
    
    duration_nights = IntegerField(
        'Duration (Nights)',
        validators=[
            Optional(),
            NumberRange(min=0, max=364)
        ]
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=2000)
        ]
    )
    
    includes = TextAreaField(
        'What\'s Included',
        validators=[
            Optional(),
            Length(max=1000)
        ]
    )
    
    excludes = TextAreaField(
        'What\'s Excluded',
        validators=[
            Optional(),
            Length(max=1000)
        ]
    )
    
    image = FileField(
        'Package Image',
        validators=[
            Optional()
        ]
    )
    
    is_featured = BooleanField('Feature this package')
    is_active = BooleanField('Active', default=True)


# ==================== INQUIRY FORMS ====================

class ContactForm(FlaskForm):
    """Contact form for customer inquiries"""
    name = StringField(
        'Full Name',
        validators=[
            DataRequired(message='Name is required'),
            Length(min=2, max=100)
        ]
    )
    
    email = EmailField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ]
    )
    
    phone = TelField(
        'Phone Number',
        validators=[
            Optional(),
            validate_phone_number
        ]
    )
    
    subject = SelectField(
        'Subject',
        choices=[
            ('', 'Select a subject'),
            ('Booking Inquiry', 'Booking Inquiry'),
            ('Package Information', 'Package Information'),
            ('Custom Tour', 'Custom Tour Request'),
            ('Group Travel', 'Group Travel'),
            ('Support', 'Customer Support'),
            ('Feedback', 'Feedback'),
            ('Other', 'Other')
        ],
        validators=[
            Optional()
        ]
    )
    
    message = TextAreaField(
        'Message',
        validators=[
            DataRequired(message='Message is required'),
            Length(min=10, max=2000, message='Message must be between 10 and 2000 characters')
        ]
    )


class QuickInquiryForm(FlaskForm):
    """Quick inquiry form from packages page"""
    name = StringField(
        'Name',
        validators=[DataRequired(message='Name is required')]
    )
    
    email = EmailField(
        'Email',
        validators=[DataRequired(message='Email is required'), Email()]
    )
    
    phone = TelField('Phone')
    package_name = HiddenField('Package Name')
    departure_date = DateField('Preferred Date', validators=[Optional()])
    travelers = IntegerField(
        'Travelers',
        validators=[Optional(), NumberRange(min=1, max=50)]
    )
    message = TextAreaField('Message', validators=[Optional()])


# ==================== BOOKING FORMS ====================

class BookingForm(FlaskForm):
    """Booking confirmation form"""
    first_name = StringField(
        'First Name',
        validators=[DataRequired(message='First name is required')]
    )
    
    last_name = StringField(
        'Last Name',
        validators=[DataRequired(message='Last name is required')]
    )
    
    email = EmailField(
        'Email',
        validators=[DataRequired(message='Email is required'), Email()]
    )
    
    phone = TelField(
        'Phone',
        validators=[DataRequired(message='Phone number is required')]
    )
    
    travelers = SelectField(
        'Number of Travelers',
        choices=[(str(i), f'{i} Traveler{"s" if i > 1 else ""}') for i in range(1, 11)],
        validators=[DataRequired()]
    )
    
    travel_date = DateField(
        'Travel Date',
        validators=[DataRequired(message='Travel date is required')]
    )
    
    special_requests = TextAreaField(
        'Special Requests',
        validators=[Optional(), Length(max=500)]
    )
    
    package_name = HiddenField('Package Name')
    package_price = HiddenField('Package Price')
    total_amount = HiddenField('Total Amount')


# ==================== TRACKING FORMS ====================

class TrackBookingForm(FlaskForm):
    """Track booking by reference number"""
    booking_number = StringField(
        'Booking Number',
        validators=[
            DataRequired(message='Booking number is required'),
            Length(min=8, max=8, message='Booking number must be 8 characters'),
            Regexp(r'^[A-Z0-9]+$', message='Use only letters and numbers')
        ]
    )


# ==================== ADMIN MANAGEMENT FORMS ====================

class AdminUserForm(FlaskForm):
    """Create/Edit admin user form"""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=50),
            Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscore')
        ]
    )
    
    email = EmailField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email()
        ]
    )
    
    full_name = StringField(
        'Full Name',
        validators=[
            Optional(),
            Length(max=100)
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            Optional(),
            Length(min=6, message='Password must be at least 6 characters')
        ]
    )
    
    is_super_admin = BooleanField('Super Admin')


class UpdateInquiryStatusForm(FlaskForm):
    """Update inquiry status form"""
    status = SelectField(
        'Status',
        choices=[
            ('Pending', 'Pending'),
            ('Reviewed', 'Reviewed'),
            ('Quotation Sent', 'Quotation Sent'),
            ('Confirmed', 'Confirmed'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled')
        ],
        validators=[DataRequired()]
    )
    
    admin_notes = TextAreaField(
        'Admin Notes',
        validators=[Optional(), Length(max=500)]
    )


class UpdateBookingStatusForm(FlaskForm):
    """Update booking status form"""
    booking_status = SelectField(
        'Booking Status',
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Cancelled', 'Cancelled'),
            ('Completed', 'Completed')
        ],
        validators=[DataRequired()]
    )
    
    payment_status = SelectField(
        'Payment Status',
        choices=[
            ('Pending', 'Pending'),
            ('Partial', 'Partial'),
            ('Paid', 'Paid')
        ],
        validators=[DataRequired()]
    )


# ==================== REPORT FORMS ====================

class DateRangeForm(FlaskForm):
    """Date range filter for reports"""
    start_date = DateField(
        'Start Date',
        validators=[DataRequired(message='Start date is required')]
    )
    
    end_date = DateField(
        'End Date',
        validators=[DataRequired(message='End date is required')]
    )
    
    report_type = SelectField(
        'Report Type',
        choices=[
            ('bookings', 'Bookings Report'),
            ('inquiries', 'Inquiries Report'),
            ('revenue', 'Revenue Report'),
            ('customers', 'Customers Report')
        ],
        validators=[DataRequired()]
    )


# ==================== SEARCH FORMS ====================

class SearchForm(FlaskForm):
    """Global search form"""
    query = StringField(
        'Search',
        validators=[
            DataRequired(message='Please enter search term'),
            Length(min=2, max=100)
        ]
    )
    
    search_type = SelectField(
        'Search In',
        choices=[
            ('packages', 'Packages'),
            ('destinations', 'Destinations'),
            ('all', 'All')
        ],
        default='all'
    )