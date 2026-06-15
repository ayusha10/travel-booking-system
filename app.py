from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Customer, Admin, Package, Inquiry, Booking
from datetime import datetime
from functools import wraps
import hashlib
import random
import string
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    FileSystemLoader(app.root_path),
])

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gantabya.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "gantabya-secret-key-2024"

# Initialize DB
db.init_app(app)

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Please login to access the admin panel.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapper

def ensure_database_schema():
    customer_columns = {
        "password": "ALTER TABLE customer ADD COLUMN password VARCHAR(200) DEFAULT ''",
        "phone": "ALTER TABLE customer ADD COLUMN phone VARCHAR(20)",
        "address": "ALTER TABLE customer ADD COLUMN address VARCHAR(200)",
        "created_at": "ALTER TABLE customer ADD COLUMN created_at DATETIME",
    }

    with db.engine.begin() as connection:
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
        if "customer" not in tables:
            return

        existing_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(customer)")
        }
        for column, statement in customer_columns.items():
            if column not in existing_columns:
                connection.exec_driver_sql(statement)

# ==================== FRONTEND ROUTES ====================

@app.route("/")
def home():
    featured_packages = Package.query.filter_by(is_featured=True).limit(6).all()
    return render_template("home_page.html", packages=featured_packages)

@app.route("/destination")
def destination():
    packages = Package.query.all()
    return render_template("destination.html", packages=packages)

@app.route("/packages")
def packages():
    all_packages = Package.query.all()
    return render_template("packages.html", packages=all_packages)

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        inquiry = Inquiry(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form.get('phone', ''),
            service_type="Contact",
            message=request.form['message']
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Thank you! We will contact you soon.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/track_booking")
def track_booking():
    booking = None
    booking_number = request.args.get("booking_number", "").strip()
    if booking_number:
        booking = Booking.query.filter_by(booking_number=booking_number.upper()).first()
        if not booking:
            flash("No booking found for that number.", "warning")
    return render_template("track_booking.html", booking=booking, booking_number=booking_number)

# ==================== AUTHENTICATION ====================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        hashed_password = hashlib.md5(request.form['password'].encode()).hexdigest()
        
        existing = Customer.query.filter_by(email=request.form['email']).first()
        if existing:
            flash("Email already registered!", "danger")
            return redirect(url_for("signup"))
        
        customer = Customer(
            full_name=request.form['full_name'],
            email=request.form['email'],
            password=hashed_password,
            phone=request.form.get('phone', ''),
            address=request.form.get('address', '')
        )
        db.session.add(customer)
        db.session.commit()
        
        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        
        customer = Customer.query.filter_by(email=email, password=password).first()
        
        if customer:
            session['customer_id'] = customer.id
            session['customer_name'] = customer.full_name
            session['user_type'] = 'customer'
            flash(f"Welcome back {customer.full_name}!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Invalid email or password!", "danger")
    
    return render_template("login.html")

@app.route("/profile")
def profile():
    if 'customer_id' not in session:
        return redirect(url_for("login"))
    
    customer = Customer.query.get(session['customer_id'])
    bookings = Booking.query.filter_by(customer_email=customer.email).all()
    inquiries = Inquiry.query.filter_by(email=customer.email).all()
    
    return render_template("profile.html", customer=customer, bookings=bookings, inquiries=inquiries)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))

# ==================== BOOKING ====================

@app.route("/booking_confirm", methods=["GET", "POST"])
def booking_confirm():
    if request.method == "POST":
        # Generate booking number
        booking_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        booking = Booking(
            booking_number=booking_num,
            customer_name=request.form['customer_name'],
            customer_email=request.form['customer_email'],
            package_name=request.form['package_name'],
            travel_date=request.form['travel_date'],
            travelers=int(request.form['travelers']),
            total_amount=float(request.form['total_amount']),
            status="Confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        flash(f"Booking confirmed! Your booking number is {booking_num}", "success")
        return redirect(url_for("profile"))
    
    return render_template("booking_confirmation.html")

# ==================== ADMIN ROUTES ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        
        admin = Admin.query.filter_by(username=username, password=password).first()
        
        if admin:
            session['admin_id'] = admin.id
            session['admin_name'] = admin.username
            session['user_type'] = 'admin'
            flash(f"Welcome Admin {admin.username}!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template("admin/login.html")

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = {
        'total_customers': Customer.query.count(),
        'total_packages': Package.query.count(),
        'total_bookings': Booking.query.count(),
        'total_inquiries': Inquiry.query.count(),
        'pending_inquiries': Inquiry.query.filter_by(status="Pending").count(),
        'confirmed_bookings': Booking.query.filter_by(status="Confirmed").count(),
        'total_revenue': db.session.query(db.func.coalesce(db.func.sum(Booking.total_amount), 0)).scalar()
    }
    
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    recent_inquiries = Inquiry.query.order_by(Inquiry.id.desc()).limit(5).all()
    
    return render_template("admin/dashboard.html", stats=stats, 
                         recent_bookings=recent_bookings, 
                         recent_inquiries=recent_inquiries)

@app.route("/admin/customers")
@admin_required
def admin_customers():
    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template("admin/customers.html", customers=customers)

@app.route("/admin/packages")
@admin_required
def admin_packages():
    packages = Package.query.order_by(Package.id.desc()).all()
    return render_template("admin/packages.html", packages=packages)

@app.route("/admin/add_package", methods=["GET", "POST"])
@admin_required
def admin_add_package():
    if request.method == "POST":
        package = Package(
            title=request.form['title'],
            country=request.form['country'],
            price=float(request.form['price']),
            duration=request.form.get('duration', ''),
            description=request.form.get('description', ''),
            image=request.form.get('image', ''),
            is_featured='is_featured' in request.form
        )
        db.session.add(package)
        db.session.commit()
        flash("Package added successfully!", "success")
        return redirect(url_for("admin_packages"))
    
    return render_template("admin/add_package.html")

@app.route("/admin/edit_package/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_edit_package(id):
    package = Package.query.get_or_404(id)
    
    if request.method == "POST":
        package.title = request.form['title']
        package.country = request.form['country']
        package.price = float(request.form['price'])
        package.duration = request.form.get('duration', '')
        package.description = request.form.get('description', '')
        package.image = request.form.get('image', '')
        package.is_featured = 'is_featured' in request.form
        db.session.commit()
        flash("Package updated!", "success")
        return redirect(url_for("admin_packages"))
    
    return render_template("admin/edit_package.html", package=package)

@app.route("/admin/delete_package/<int:id>")
@admin_required
def admin_delete_package(id):
    package = Package.query.get_or_404(id)
    db.session.delete(package)
    db.session.commit()
    flash("Package deleted!", "success")
    return redirect(url_for("admin_packages"))

@app.route("/admin/inquiries")
@admin_required
def admin_inquiries():
    inquiries = Inquiry.query.order_by(Inquiry.id.desc()).all()
    return render_template("admin/inquiries.html", inquiries=inquiries)

@app.route("/admin/update_status/<int:id>/<status>")
@admin_required
def admin_update_status(id, status):
    allowed_statuses = {"Pending", "Contacted", "Resolved", "Cancelled", "Confirmed"}
    if status not in allowed_statuses:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin_inquiries"))
    
    inquiry = Inquiry.query.get_or_404(id)
    inquiry.status = status
    db.session.commit()
    flash(f"Inquiry status: {status}", "success")
    return redirect(url_for("admin_inquiries"))

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)

@app.route("/admin/update_booking/<int:id>/<status>")
@admin_required
def admin_update_booking(id, status):
    allowed_statuses = {"Pending", "Confirmed", "Cancelled", "Completed"}
    if status not in allowed_statuses:
        flash("Invalid booking status.", "danger")
        return redirect(url_for("admin_bookings"))

    booking = Booking.query.get_or_404(id)
    booking.status = status
    db.session.commit()
    flash(f"Booking marked as {status}.", "success")
    return redirect(url_for("admin_bookings"))

@app.route("/admin/reports")
@admin_required
def admin_reports():
    status_rows = db.session.query(Booking.status, db.func.count(Booking.id)).group_by(Booking.status).all()
    top_packages = (
        db.session.query(Booking.package_name, db.func.count(Booking.id), db.func.coalesce(db.func.sum(Booking.total_amount), 0))
        .group_by(Booking.package_name)
        .order_by(db.func.count(Booking.id).desc())
        .limit(5)
        .all()
    )
    stats = {
        "revenue": db.session.query(db.func.coalesce(db.func.sum(Booking.total_amount), 0)).scalar(),
        "customers": Customer.query.count(),
        "packages": Package.query.count(),
        "bookings": Booking.query.count(),
        "inquiries": Inquiry.query.count(),
    }
    return render_template("admin/reports.html", stats=stats, status_rows=status_rows, top_packages=top_packages)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    flash("Logged out!", "success")
    return redirect(url_for("admin_login"))

# ==================== CREATE DEFAULT DATA ====================

def create_default_data():
    # Create default admin
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(
            username="admin",
            email="admin@gantabya.com",
            password=hashlib.md5("admin123".encode()).hexdigest(),
            full_name="Super Admin"
        )
        db.session.add(admin)
    
    # Create sample packages
    if Package.query.count() == 0:
        sample_packages = [
            Package(title="Dubai Adventure", country="UAE", price=89999, duration="5 Days", 
                   description="Visit Burj Khalifa, Desert Safari", is_featured=True),
            Package(title="Paris Romance", country="France", price=129999, duration="7 Days",
                   description="Eiffel Tower, Louvre Museum", is_featured=True),
            Package(title="Bali Paradise", country="Indonesia", price=69999, duration="4 Days",
                   description="Beaches, temples, and culture", is_featured=True),
            Package(title="Swiss Alps", country="Switzerland", price=159999, duration="6 Days",
                   description="Mountain views, train rides"),
        ]
        for p in sample_packages:
            db.session.add(p)
    
    db.session.commit()

# ==================== RUN APP ====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_database_schema()
        create_default_data()
        
        print("\n" + "="*50)
        print("GANTABYA DATABASE READY!")
        print("="*50)
        print(f"Tables: Customer, Admin, Package, Inquiry, Booking")
        print(f"Packages: {Package.query.count()} packages loaded")
        print("\nAdmin Login:")
        print("   URL: http://127.0.0.1:5000/admin/login")
        print("   Username: admin")
        print("   Password: admin123")
        print("\nCustomer Signup:")
        print("   URL: http://127.0.0.1:5000/signup")
        print("="*50 + "\n")
    
    app.run(debug=True, use_reloader=False)
