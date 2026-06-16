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
    """Ensure database has all required columns"""
    customer_columns = {
        "password": "ALTER TABLE customer ADD COLUMN password VARCHAR(200) DEFAULT ''",
        "phone": "ALTER TABLE customer ADD COLUMN phone VARCHAR(20)",
        "address": "ALTER TABLE customer ADD COLUMN address VARCHAR(200)",
        "created_at": "ALTER TABLE customer ADD COLUMN created_at DATETIME",
    }

    booking_columns = {
        "customer_phone": "ALTER TABLE booking ADD COLUMN customer_phone VARCHAR(20)",
        "special_requests": "ALTER TABLE booking ADD COLUMN special_requests TEXT",
        "booking_status": "ALTER TABLE booking ADD COLUMN booking_status VARCHAR(50) DEFAULT 'Pending'",
        "payment_status": "ALTER TABLE booking ADD COLUMN payment_status VARCHAR(50) DEFAULT 'Pending'",
        "paid_amount": "ALTER TABLE booking ADD COLUMN paid_amount FLOAT DEFAULT 0",
        "created_at": "ALTER TABLE booking ADD COLUMN created_at DATETIME",
    }

    inquiry_columns = {
        "phone": "ALTER TABLE inquiry ADD COLUMN phone VARCHAR(20)",
        "departure_date": "ALTER TABLE inquiry ADD COLUMN departure_date VARCHAR(50)",
        "travelers": "ALTER TABLE inquiry ADD COLUMN travelers INTEGER DEFAULT 1",
        "created_at": "ALTER TABLE inquiry ADD COLUMN created_at DATETIME",
    }

    with db.engine.begin() as connection:
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
        
        if "customer" in tables:
            existing_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(customer)")}
            for column, statement in customer_columns.items():
                if column not in existing_columns:
                    try:
                        connection.exec_driver_sql(statement)
                    except:
                        pass
        
        if "booking" in tables:
            existing_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(booking)")}
            for column, statement in booking_columns.items():
                if column not in existing_columns:
                    try:
                        connection.exec_driver_sql(statement)
                    except:
                        pass
        
        if "inquiry" in tables:
            existing_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(inquiry)")}
            for column, statement in inquiry_columns.items():
                if column not in existing_columns:
                    try:
                        connection.exec_driver_sql(statement)
                    except:
                        pass

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
            message=request.form['message'],
            status="Pending"
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Thank you! We will contact you soon.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/track_booking")
def track_booking():
    booking = None
    booking_id = request.args.get('booking_id', '')
    
    if booking_id:
        # Search by booking number
        booking = Booking.query.filter_by(booking_number=booking_id.upper()).first()
        
        if not booking:
            # Also try searching by ID if booking number not found
            if booking_id.isdigit():
                booking = Booking.query.get(int(booking_id))
            if not booking:
                flash("Booking not found. Please check your booking number.", "error")
    
    return render_template("track_booking.html", booking=booking, booking_id=booking_id)

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
            address=request.form.get('address', ''),
            created_at=datetime.utcnow()
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
            session['customer_email'] = customer.email
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
    bookings = Booking.query.filter_by(customer_email=customer.email).order_by(Booking.id.desc()).all()
    inquiries = Inquiry.query.filter_by(email=customer.email).order_by(Inquiry.id.desc()).all()
    
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
        # Generate unique booking number
        booking_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        booking = Booking(
            booking_number=booking_num,
            customer_name=request.form.get('first_name') + ' ' + request.form.get('last_name'),
            customer_email=request.form.get('email'),
            customer_phone=request.form.get('phone'),
            package_name=request.form.get('package_name'),
            travel_date=request.form.get('travel_date'),
            travelers=int(request.form.get('travelers')),
            total_amount=float(request.form.get('total_amount')),
            special_requests=request.form.get('special_requests', ''),
            booking_status="Confirmed",
            status="Confirmed",
            created_at=datetime.utcnow()
        )
        db.session.add(booking)
        db.session.commit()
        
        flash(f"Booking confirmed! Your booking number is {booking_num}", "success")
        return redirect(url_for("profile"))
    
    return render_template("booking_confirm.html")

# ==================== INQUIRY ROUTES ====================

@app.route("/submit_inquiry", methods=["POST"])
def submit_inquiry():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    package_name = request.form.get('package_name', '')
    departure_date = request.form.get('departure_date', '')
    travelers = request.form.get('travelers', 1)
    message = request.form.get('message', '')
    
    # Create new inquiry
    inquiry = Inquiry(
        name=name,
        email=email,
        phone=phone,
        service_type="Package Inquiry",
        destination=package_name,
        departure_date=departure_date,
        travelers=int(travelers) if travelers else 1,
        message=f"Package: {package_name}\n\n{message}" if message else f"Package: {package_name}",
        status="Pending",
        created_at=datetime.utcnow()
    )
    
    db.session.add(inquiry)
    db.session.commit()
    
    flash("Thank you! Your inquiry has been sent. We'll contact you soon.", "success")
    
    # Redirect back to packages page
    return redirect(url_for("packages"))

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
        'confirmed_bookings': Booking.query.filter_by(booking_status="Confirmed").count(),
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
            is_featured='is_featured' in request.form,
            created_at=datetime.utcnow()
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
    allowed_statuses = {"Pending", "Reviewed", "Quotation Sent", "Confirmed", "Completed", "Cancelled"}
    if status not in allowed_statuses:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin_inquiries"))
    
    inquiry = Inquiry.query.get_or_404(id)
    inquiry.status = status
    db.session.commit()
    flash(f"Inquiry status updated to: {status}", "success")
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
    booking.booking_status = status
    booking.status = status
    db.session.commit()
    flash(f"Booking marked as {status}.", "success")
    return redirect(url_for("admin_bookings"))

@app.route("/admin/reports")
@admin_required
def admin_reports():
    status_rows = db.session.query(Booking.booking_status, db.func.count(Booking.id)).group_by(Booking.booking_status).all()
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
    """Create default admin and sample packages"""
    # Create default admin
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(
            username="admin",
            email="admin@gantabya.com",
            password=hashlib.md5("admin123".encode()).hexdigest(),
            full_name="Super Admin",
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
    
    # Create sample packages if none exist
    if Package.query.count() == 0:
        sample_packages = [
            Package(title="Dubai Adventure", country="UAE", price=89999, duration="5 Days", 
                   description="Visit Burj Khalifa, Desert Safari with dinner, Dubai Frame, Miracle Garden, and luxury shopping. Includes 5-star hotel accommodation and daily breakfast.", 
                   is_featured=True, created_at=datetime.utcnow()),
            Package(title="Paris Romance", country="France", price=129999, duration="7 Days",
                   description="Eiffel Tower, Louvre Museum, Seine River cruise, Montmartre, Versailles Palace. Romantic getaway with charming hotel in city center.", 
                   is_featured=True, created_at=datetime.utcnow()),
            Package(title="Bali Paradise", country="Indonesia", price=69999, duration="4 Days",
                   description="Beautiful beaches, Ubud temples, rice terraces, water sports, and cultural shows. Includes private villa stay.", 
                   is_featured=True, created_at=datetime.utcnow()),
            Package(title="Swiss Alps", country="Switzerland", price=159999, duration="6 Days",
                   description="Matterhorn view, Jungfraujoch, Interlaken, Lucerne, scenic train rides. Alpine adventure with cozy mountain lodges.", 
                   is_featured=False, created_at=datetime.utcnow()),
            Package(title="Thailand Explorer", country="Thailand", price=49999, duration="5 Days",
                   description="Bangkok temples, Pattaya beaches, Phi Phi Islands, Thai cuisine tour. Perfect budget-friendly tropical escape.", 
                   is_featured=False, created_at=datetime.utcnow()),
            Package(title="Japan Discovery", country="Japan", price=189999, duration="8 Days",
                   description="Tokyo, Osaka, Kyoto, Mount Fuji, bullet train experience, cherry blossoms, sushi making class.", 
                   is_featured=False, created_at=datetime.utcnow()),
        ]
        for p in sample_packages:
            db.session.add(p)
    
    db.session.commit()

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_user():
    return dict(
        is_logged_in='customer_id' in session,
        customer_name=session.get('customer_name'),
        is_admin='admin_id' in session
    )

# ==================== RUN APP ====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_database_schema()
        create_default_data()
        
        print("\n" + "="*60)
        print("🌟 GANTABYA TRAVEL BOOKING SYSTEM - READY! 🌟")
        print("="*60)
        print(f"✅ Database Tables: Customer, Admin, Package, Inquiry, Booking")
        print(f"✅ Packages Loaded: {Package.query.count()} packages")
        print(f"✅ Customers Registered: {Customer.query.count()}")
        print(f"✅ Total Bookings: {Booking.query.count()}")
        print("\n" + "🔐" + "="*58)
        print("🔐 ADMIN LOGIN CREDENTIALS")
        print("="*60)
        print("   📍 URL: http://127.0.0.1:5000/admin/login")
        print("   👤 Username: admin")
        print("   🔑 Password: admin123")
        print("\n" + "👥" + "="*58)
        print("👥 CUSTOMER ACCESS")
        print("="*60)
        print("   📍 Signup: http://127.0.0.1:5000/signup")
        print("   📍 Login:  http://127.0.0.1:5000/login")
        print("\n" + "📱" + "="*58)
        print("📱 FRONTEND PAGES")
        print("="*60)
        print("   🏠 Home:        http://127.0.0.1:5000/")
        print("   ✈️ Packages:    http://127.0.0.1:5000/packages")
        print("   📍 Destinations: http://127.0.0.1:5000/destination")
        print("   🛠️ Services:    http://127.0.0.1:5000/services")
        print("   📞 Contact:     http://127.0.0.1:5000/contact")
        print("   🔍 Track Booking: http://127.0.0.1:5000/track_booking")
        print("="*60 + "\n")
    
    app.run(debug=True, use_reloader=False)