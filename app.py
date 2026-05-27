"""
Smart Bus Pass Management System
================================
A full-stack web application for managing bus passes.
Built with Flask, SQLite, and ReportLab.

Run: python app.py
"""

import os
import uuid
import sqlite3
import hmac
import hashlib
import razorpay
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file, g, jsonify
)
import qrcode
import io
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'buspass-secret-key-2026-change-in-production'
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['PASSES_FOLDER'] = os.path.join(app.root_path, 'static', 'passes')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB upload limit

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'test_key_id')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'test_key_secret')

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PASSES_FOLDER'], exist_ok=True)

# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------
PASS_PRICES = {
    'weekly': 150,
    'monthly': 500,
    '3months': 1350,      # discounted from 1500
    '6months': 2700,      # discounted from 3000
    'student': 400,       # reduced rate
    'senior': 350,        # senior citizen discount
}

# Duration in days for each pass type
PASS_DURATIONS = {
    'weekly': 7,
    'monthly': 30,
    '3months': 90,
    '6months': 180,
    'student': 30,
    'senior': 30,
}

# Friendly label for each pass type
PASS_LABELS = {
    'weekly': 'Weekly Pass',
    'monthly': 'Monthly Pass',
    '3months': '3-Month Pass',
    '6months': '6-Month Pass',
    'student': 'Student Pass',
    'senior': 'Senior Citizen Pass',
}

# ---------------------------------------------------------------------------
# Mumbai Bus Stops (ordered geographically for distance calculation)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Mumbai Bus Areas & Stops Mapping
# ---------------------------------------------------------------------------

# Major Area/Station Order (used for distance calculation)
MUMBAI_AREAS = [
    'Colaba', 'Churchgate', 'Marine Lines', 'Charni Road', 'Grant Road',
    'Mumbai Central', 'Mahalaxmi', 'Lower Parel', 'Parel', 'Dadar',
    'Matunga', 'Sion', 'Kurla', 'Ghatkopar', 'Vikhroli', 'Kanjurmarg',
    'Bhandup', 'Mulund', 'Thane', 'Bandra', 'Khar Road', 'Santa Cruz',
    'Vile Parle', 'Andheri', 'Jogeshwari', 'Goregaon', 'Malad',
    'Kandivali', 'Borivali', 'Dahisar', 'Mira Road', 'Chembur',
    'Wadala', 'Worli', 'Powai', 'Airoli', 'Vashi', 'Nerul',
    'Belapur', 'Panvel'
]

# Detailed stops for each area
MUMBAI_AREAS_MAP = {
    'Colaba': ['Colaba Bus Station', 'Electric House', 'Regal Cinema', 'Sassoon Docks', 'Colaba'],
    'Churchgate': ['Churchgate Station', 'Mantralaya', 'Nariman Point', 'Marine Drive', 'Churchgate'],
    'Marine Lines': ['Marine Lines Station', 'Princess Street', 'Chandanwadi', 'Income Tax Office', 'Marine Lines'],
    'Charni Road': ['Charni Road Station', 'Opera House', 'Saifee Hospital', 'Girgaon Chowpatty', 'Charni Road'],
    'Grant Road': ['Grant Road Station', 'Nana Chowk', 'Tardeo Naka', 'Bhatia Hospital', 'Grant Road'],
    'Mumbai Central': ['Mumbai Central Station', 'Nair Hospital', 'Alexandra Cinema', 'Mahalaxmi Racecourse', 'Mumbai Central'],
    'Mahalaxmi': ['Mahalaxmi Station', 'Famous Studio', 'Nehru Planetarium', 'Mahalaxmi'],
    'Lower Parel': ['Lower Parel Station', 'High Street Phoenix', 'Kamala Mills', 'Deepak Cinema', 'Lower Parel'],
    'Parel': ['Parel Station', 'KEM Hospital', 'Tata Memorial Hospital', 'Parel'],
    'Dadar': ['Dadar West', 'Dadar East', 'Plaza Cinema', 'Shivaji Park', 'Siddhivinayak Temple', 'Dadar'],
    'Matunga': ['Matunga Station', 'Khalsa College', 'Five Gardens', 'Aurora Cinema', 'Matunga'],
    'Sion': ['Sion Station', 'Sion Circle', 'Chunabhatti', 'Somaiya College', 'Sion'],
    'Kurla': ['Kurla West', 'Kurla East', 'Phoenix Market City', 'BKC Connector', 'Kurla'],
    'Ghatkopar': ['Ghatkopar Station', 'R-City Mall', 'Pant Nagar', 'Sarvodaya Hospital', 'Ghatkopar'],
    'Vikhroli': ['Vikhroli Station', 'Godrej Colony', 'Kannamwar Nagar', 'Hiranandani Hospital', 'Vikhroli'],
    'Kanjurmarg': ['Kanjurmarg Station', 'Naval Dockyard Colony', 'IIT Main Gate', 'Kanjurmarg'],
    'Bhandup': ['Bhandup Station', 'Dreams Mall', 'Mangatram Petrol Pump', 'Bhandup'],
    'Mulund': ['Mulund West', 'Mulund East', 'Check Naka', 'Johnson & Johnson', 'Mulund'],
    'Thane': ['Thane Station', 'Teen Haath Naka', 'Viviana Mall', 'Cadbury Junction', 'Thane'],
    'Bandra': ['Bandra West', 'Bandra East', 'Bandra Reclamation', 'Lucky Hotel', 'Mount Mary Church', 'National College', 'BKC (G Block)', 'Bandra'],
    'Khar Road': ['Khar Road Station', 'Linking Road', 'Pali Hill', 'Khar Gymkhana', 'Khar Road'],
    'Santa Cruz': ['Santacruz West', 'Santacruz East', 'Milan Subway', 'Khira Nagar', 'Rizvi College', 'Vakola Police Station', 'Kalina Military Camp', 'Santa Cruz', 'Santacruz'],
    'Vile Parle': ['Vile Parle West', 'Vile Parle East', 'Mithibai College', 'Cooper Hospital', 'Juhu Beach', 'Vile Parle'],
    'Andheri': ['Andheri West', 'Andheri East', 'Shoppers Stop', 'Gilbert Hill', 'Seven Bungalows', 'Marol Naka', 'Saki Naka', 'Andheri'],
    'Jogeshwari': ['Jogeshwari West', 'Jogeshwari East', 'Oshiwara', 'Hub Mall', 'Jogeshwari'],
    'Goregaon': ['Goregaon West', 'Goregaon East', 'Film City Road', 'Oberoi Mall', 'Goregaon'],
    'Malad': ['Malad West', 'Malad East', 'Orlem', 'Infiniti Mall (Malad)', 'Marve Road', 'Malad'],
    'Kandivali': ['Kandivali West', 'Kandivali East', 'Thakur Village', 'Poisar', 'Kandivali'],
    'Borivali': ['Borivali West', 'Borivali East', 'Sanjay Gandhi National Park', 'Gorai Creek', 'Don Bosco School', 'Borivali'],
    'Dahisar': ['Dahisar West', 'Dahisar East', 'Anand Nagar', 'Kandarpada', 'Dahisar'],
    'Mira Road': ['Mira Road Station', 'Shanti Nagar', 'Beverly Park', 'Kashimira', 'Mira Road'],
    'Chembur': ['Chembur Station', 'Diamond Garden', 'Amar Mahal', 'Maitri Park', 'Chembur'],
    'Wadala': ['Wadala Station', 'Five Gardens (Wadala)', 'IMAX (Wadala)', 'Antop Hill', 'Wadala'],
    'Worli': ['Worli Naka', 'Worli Sea Face', 'Atria Mall', 'Nehru Centre', 'Worli'],
    'Powai': ['Powai Lake', 'IIT Bombay', 'Hiranandani Garden', 'Rambaug', 'Powai'],
    'Airoli': ['Airoli Station', 'Mindspace', 'Patni IT Park', 'Airoli'],
    'Vashi': ['Vashi Station', 'Sector 17', 'Inorbit Mall (Vashi)', 'APMC Market', 'Vashi'],
    'Nerul': ['Nerul Station', 'LP Bus Stop', 'DY Patil Stadium', 'Nerul'],
    'Belapur': ['Belapur Station', 'CBD Belapur', 'Uran Phata', 'Belapur'],
    'Panvel': ['Panvel Station', 'New Panvel', 'Old Panvel', 'Takka Colony', 'Panvel']
}

# Flatten for search functionality
MUMBAI_STOPS = sorted([stop for stops in MUMBAI_AREAS_MAP.values() for stop in stops])

# Grouping stops by line (mostly for reference/admin)
MUMBAI_STOPS_GROUPED = {
    'Western Line Area': ['Colaba', 'Churchgate', 'Marine Lines', 'Charni Road', 'Grant Road',
                          'Mumbai Central', 'Mahalaxmi', 'Lower Parel', 'Bandra', 'Khar Road',
                          'Santa Cruz', 'Vile Parle', 'Andheri', 'Jogeshwari', 'Goregaon',
                          'Malad', 'Kandivali', 'Borivali', 'Dahisar', 'Mira Road'],
    'Central Line Area': ['Parel', 'Dadar', 'Matunga', 'Sion', 'Kurla', 'Ghatkopar',
                          'Vikhroli', 'Kanjurmarg', 'Bhandup', 'Mulund', 'Thane'],
    'Harbour Line Area': ['Chembur', 'Wadala', 'Vashi', 'Nerul', 'Belapur', 'Panvel'],
    'Business & Others': ['Worli', 'Powai', 'Airoli']
}

def get_area_for_stop(stop_name):
    """Find which major area a specific local stop belongs to."""
    for area, stops in MUMBAI_AREAS_MAP.items():
        if stop_name in stops:
            return area
    return stop_name # Default to self


def get_distance_multiplier(route_from, route_to):
    """Calculate price multiplier based on distance between two stops, resolving their area first."""
    area_from = get_area_for_stop(route_from)
    area_to = get_area_for_stop(route_to)

    if area_from not in MUMBAI_AREAS or area_to not in MUMBAI_AREAS:
        return 1.0
        
    idx_from = MUMBAI_AREAS.index(area_from)
    idx_to = MUMBAI_AREAS.index(area_to)
    gap = abs(idx_to - idx_from)
    
    if gap == 0:
        return 0.8   # Within the same area area
    elif gap <= 4:
        return 1.0   # Medium distance
    elif gap <= 10:
        return 1.2   # Long distance
    else:
        return 1.5   # Very long distance

# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

# --- Custom Jinja Filters ---
@app.template_filter('datetime')
def format_datetime(value, format="%d %b %Y, %I:%M %p"):
    if not value:
        return ""
    try:
        from datetime import datetime, timedelta
        # SQLite CURRENT_TIMESTAMP is UTC "YYYY-MM-DD HH:MM:SS"
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        # Add IST (+5:30) offset for "Real Timing"
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime(format)
    except Exception:
        return value

@app.template_filter('time_ago')
def time_ago(value):
    if not value:
        return ""
    try:
        from datetime import datetime, timedelta
        # SQLite CURRENT_TIMESTAMP is UTC
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        # Add IST (+5:30) offset
        dt = dt + timedelta(hours=5, minutes=30)
        
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)}h ago"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 7:
            return f"{diff.days} days ago"
        return dt.strftime("%d %b")
    except Exception:
        return value

def get_db():
    """Open a database connection and attach it to the request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist and seed admin user."""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            route_from TEXT NOT NULL,
            route_to TEXT NOT NULL,
            pass_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            issue_date TEXT,
            expiry_date TEXT,
            photo TEXT,
            id_proof TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pass_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            order_id TEXT NOT NULL,
            razorpay_payment_id TEXT,
            signature TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pass_id) REFERENCES passes(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            admin_response TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            type TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Migrate: add Razorpay columns to payments if they don't exist
    columns = [
        ('order_id', 'TEXT'),
        ('razorpay_payment_id', 'TEXT'),
        ('signature', 'TEXT'),
        ('status', 'TEXT DEFAULT "pending"'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    for col_name, col_type in columns:
        try:
            db.execute(f"ALTER TABLE payments ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass # Column already exists
    
    # Migrate: add 'phone' column if it doesn't exist
    try:
        db.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except Exception:
        pass

    # Migrate: add 'user_id' and 'admin_response' to support_tickets
    try:
        db.execute("ALTER TABLE support_tickets ADD COLUMN user_id INTEGER")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE support_tickets ADD COLUMN admin_response TEXT")
    except Exception:
        pass

    # Seed default admin if not exists
    admin = db.execute("SELECT id FROM users WHERE email = ?", ('admin@buspass.com',)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ('Admin', 'admin@buspass.com', generate_password_hash('admin123'), 'admin')
        )
    db.commit()


# ---------------------------------------------------------------------------
# Auth Decorators
# ---------------------------------------------------------------------------

def login_required(f):
    """Ensure the user is logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Ensure the user is an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Utility Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    """Check file extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_pass_pdf(pass_data, user_name):
    """Generate a highly professional, realistic PDF bus pass with QR code and logo."""
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, white, black, transparent, Color
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    filename = f"pass_{pass_data['id']}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(app.config['PASSES_FOLDER'], filename)

    width, height = A5
    c = canvas.Canvas(filepath, pagesize=A5)

    # --- Background & Colors ---
    PRIMARY_BLUE = HexColor('#1E3A8A')
    LIGHT_BLUE = HexColor('#2563EB')
    ACCENT_BLUE = HexColor('#38BDF8')
    TEXT_DARK = HexColor('#1F2937')
    TEXT_MUTED = HexColor('#6B7280')

    # Top Header Bar
    c.setFillColor(PRIMARY_BLUE)
    c.rect(0, height - 85, width, 85, fill=True, stroke=False)
    
    # Secondary Accent Bar
    c.setFillColor(LIGHT_BLUE)
    c.rect(0, height - 100, width, 15, fill=True, stroke=False)

    # --- Logo & Title ---
    logo_path = os.path.join(app.root_path, 'static', 'logo.png')
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            # Draw logo at top center
            c.drawImage(logo, width/2 - 25, height - 45, width=50, height=40, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 62, "SMART BUS PASS")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 76, "Digital Transit Authority | Official Document")

    # --- Pass ID Badge ---
    c.setFillColor(ACCENT_BLUE)
    c.roundRect(width / 2 - 50, height - 120, 100, 24, 6, fill=True, stroke=False)
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 114, f"PASS  #{pass_data['id']}")

    # --- MAIN CONTENT AREA WITH BORDER ---
    c.setLineWidth(1)
    c.setStrokeColor(HexColor('#E5E7EB'))
    c.roundRect(15, 45, width - 30, height - 165, 10, fill=False, stroke=True)

    # --- MAIN CONTENT AREA ---
    
    # 1. Passenger Photo (Top Left)
    photo_path = None
    if pass_data['photo']:
        potential = os.path.join(app.config['UPLOAD_FOLDER'], pass_data['photo'])
        if os.path.exists(potential):
            photo_path = potential

    # Draw Photo Frame
    photo_x = 35
    photo_y = height - 225
    photo_w, photo_h = 80, 95
    
    c.setFillColor(HexColor('#F3F4F6'))
    c.roundRect(photo_x, photo_y, photo_w, photo_h, 4, fill=True, stroke=True)
    
    if photo_path:
        try:
            img = ImageReader(photo_path)
            c.drawImage(img, photo_x + 2, photo_y + 2, width=photo_w - 4, height=photo_h - 4, preserveAspectRatio=True, mask='auto')
        except Exception:
            c.setFillColor(TEXT_MUTED)
            c.setFont("Helvetica", 6)
            c.drawCentredString(photo_x + photo_w/2, photo_y + 10, "PHOTO ERROR")
    else:
        # User placeholder silhouette
        placeholder_path = os.path.join(app.root_path, 'static', 'default_profile.png')
        if os.path.exists(placeholder_path):
            try:
                c.drawImage(placeholder_path, photo_x + 10, photo_y + 10, width=photo_w - 20, height=photo_h - 20, preserveAspectRatio=True, mask='auto')
            except:
                pass
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(photo_x + photo_w/2, photo_y + 8, "NO PHOTO UPLOADED")

    # 2. QR Code (Top Right - Increased Size)
    try:
        # Generate verification URL (e.g., points to the public verification route)
        verify_url = url_for('verify_pass', pass_id=pass_data['id'], _external=True)
        
        qr = qrcode.QRCode(version=1, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to ReportLab-friendly image
        qr_io = io.BytesIO()
        img_qr.save(qr_io, format='PNG')
        qr_io.seek(0)
        qr_reader = ImageReader(qr_io)
        
        qr_x = width - 125
        qr_y = height - 225
        qr_size = 90  # Increased from 75
        
        c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(qr_x + qr_size/2, qr_y - 12, "SCAN TO VERIFY")
    except Exception as e:
        print(f"QR Error: {e}")

    # --- Details (2-Column Balanced Layout) ---
    y_start = height - 275
    left_col_x = 40
    right_col_x = width / 2 + 15
    row_height = 38

    def draw_detail(x, y, label, value, is_bold=False, custom_color=None):
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(x, y + 10, label.upper())
        
        if custom_color:
            c.setFillColor(custom_color)
        else:
            c.setFillColor(TEXT_DARK)
            
        if is_bold:
            c.setFont("Helvetica-Bold", 12)
        else:
            c.setFont("Helvetica", 11)
        c.drawString(x, y - 5, str(value))

    # Row 1
    draw_detail(left_col_x, y_start, "Passenger Name", pass_data['full_name'], is_bold=True)
    
    # Highlight Status with Color
    status_color = HexColor('#059669') if pass_data['status'] == 'Active' else HexColor('#DC2626')
    draw_detail(right_col_x, y_start, "Pass Status", pass_data['status'], is_bold=True, custom_color=status_color)

    # Row 2
    route_str = f"{pass_data['route_from']}  →  {pass_data['route_to']}"
    draw_detail(left_col_x, y_start - row_height, "Travel Route", route_str, is_bold=True)
    draw_detail(right_col_x, y_start - row_height, "Pass Category", PASS_LABELS.get(pass_data['pass_type'], pass_data['pass_type']))

    # Row 3
    draw_detail(left_col_x, y_start - row_height * 2, "Issue Date", pass_data['issue_date'] or 'N/A')
    draw_detail(right_col_x, y_start - row_height * 2, "Expiry Date", pass_data['expiry_date'] or 'N/A')

    # Row 4
    draw_detail(left_col_x, y_start - row_height * 3, "Age / Gender", f"{pass_data['age']} yrs / {pass_data['gender']}")
    
    # Realistic Reference ID Format: BP-YYYY-00ID
    year = datetime.now().year
    ref_id = f"BP-{year}-{pass_data['id']:04d}"
    draw_detail(right_col_x, y_start - row_height * 3, "Reference ID", ref_id)

    # --- Authorization Section ---
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 70, "Authorized by Digital Transit Authority")
    
    # --- Footer ---
    c.setFillColor(PRIMARY_BLUE)
    c.rect(0, 0, width, 45, fill=True, stroke=False)
    
    c.setFillColor(white)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 28, "Security Notice: This bus pass is unique, non-transferable, and digitally verified.")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, 16, "Digital Transit Authority | Verified 24×7")
    
    # Watermark
    c.setFillColor(Color(0, 0, 0, alpha=0.03))
    c.setFont("Helvetica-Bold", 40)
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.drawCentredString(0, 0, "VERIFIED PASS")
    c.restoreState()

    c.save()
    return filename


# ---------------------------------------------------------------------------
# Verification Route for QR Code
# ---------------------------------------------------------------------------
@app.route('/verify/<int:pass_id>')
def verify_pass(pass_id):
    """Public verification page for conductors scanning the QR code."""
    db = get_db()
    bus_pass = db.execute(
        "SELECT * FROM passes WHERE id = ?", (pass_id,)
    ).fetchone()

    if not bus_pass:
        return render_template('404.html'), 404

    return render_template('verify_pass_status.html', p=bus_pass)


# ---------------------------------------------------------------------------
# Context Processor – inject user info into all templates
# ---------------------------------------------------------------------------
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return dict(current_user=user)


# =========================================================================
#  PUBLIC ROUTES
# =========================================================================

@app.route('/')
def home():
    """Landing / Home page."""
    return render_template('home.html')


@app.route('/about')
def about():
    """About Us page."""
    return render_template('about.html')


@app.route('/services')
def services():
    """Services page."""
    return render_template('services.html')


@app.route('/help')
def help_page():
    """Help / FAQ page."""
    return render_template('help.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us page – stores message in DB."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, message]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('contact'))

        db = get_db()
        db.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        db.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


# =========================================================================
#  AUTHENTICATION ROUTES
# =========================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validation
        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        db.execute(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, generate_password_hash(password), 'user')
        )
        db.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User / Admin login."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not all([email, password]):
            flash('Please enter email and password.', 'danger')
            return redirect(url_for('login'))

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and log out."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# =========================================================================
#  USER DASHBOARD & FEATURES
# =========================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard – overview of passes & status."""
    db = get_db()
    uid = session['user_id']

    passes = db.execute(
        "SELECT * FROM passes WHERE user_id = ? ORDER BY created_at DESC", (uid,)
    ).fetchall()

    # Auto-expire passes
    today = datetime.now().strftime('%Y-%m-%d')
    for p in passes:
        if p['status'] == 'Active' and p['expiry_date'] and p['expiry_date'] < today:
            db.execute("UPDATE passes SET status = 'Expired' WHERE id = ?", (p['id'],))
    db.commit()

    # Re-fetch after update
    passes = db.execute(
        "SELECT * FROM passes WHERE user_id = ? ORDER BY created_at DESC", (uid,)
    ).fetchall()

    stats = {
        'pending': sum(1 for p in passes if p['status'] == 'Pending'),
        'approved': sum(1 for p in passes if p['status'] == 'Approved'),
        'active': sum(1 for p in passes if p['status'] == 'Active'),
        'expired': sum(1 for p in passes if p['status'] == 'Expired'),
        'rejected': sum(1 for p in passes if p['status'] == 'Rejected'),
    }

    # --- New: Renewal Reminders Logic ---
    for p in passes:
        if p['status'] == 'Active' and p['expiry_date']:
            try:
                exp_dt = datetime.strptime(p['expiry_date'], '%Y-%m-%d')
                days_left = (exp_dt - datetime.now()).days
                if 0 <= days_left <= 3:
                    # Check if already notified about this pass expiry
                    pass_label = PASS_LABELS.get(p['pass_type'], 'Pass')
                    msg = f"Your {pass_label} is expiring on {p['expiry_date']}. Please renew it soon!"
                    existing = db.execute(
                        "SELECT id FROM notifications WHERE user_id = ? AND message = ?", 
                        (uid, msg)
                    ).fetchone()
                    if not existing:
                        db.execute(
                            "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
                            (uid, msg, 'warning')
                        )
                        db.commit()
            except:
                pass

    # Fetch notifications (including new ones)
    notifications = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 15", (uid,)
    ).fetchall()
    unread_count = db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (uid,)
    ).fetchone()[0]

    # Re-fetch support tickets with responses if any
    tickets = db.execute(
        "SELECT * FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC", (uid,)
    ).fetchall()

    return render_template('dashboard.html', passes=passes, stats=stats, notifications=notifications, unread_count=unread_count, tickets=tickets)


@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_pass():
    """Apply for a new bus pass."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        route_from = request.form.get('route_from', '').strip()
        route_to = request.form.get('route_to', '').strip()
        pass_type = request.form.get('pass_type', '').strip()

        if not all([full_name, age, gender, route_from, route_to, pass_type]) or 'id_proof' not in request.files:
            flash('Please fill all required fields, including ID Proof.', 'danger')
            return redirect(url_for('apply_pass'))

        # Check if age is valid (10-80)
        try:
            age_val = int(age)
            if age_val < 10 or age_val > 80:
                flash('Age must be between 10 and 80.', 'danger')
                return redirect(url_for('apply_pass'))
        except ValueError:
            flash('Invalid age format.', 'danger')
            return redirect(url_for('apply_pass'))

        if pass_type not in PASS_PRICES:
            flash('Invalid pass type.', 'danger')
            return redirect(url_for('apply_pass'))

        price = PASS_PRICES[pass_type]

        # Apply distance-based pricing
        multiplier = get_distance_multiplier(route_from, route_to)
        price = round(price * multiplier)

        # Handle photo upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                photo_filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        # Handle ID proof upload
        id_proof_filename = None
        if 'id_proof' in request.files:
            id_proof = request.files['id_proof']
            if id_proof and id_proof.filename and allowed_file(id_proof.filename):
                id_proof_filename = f"{uuid.uuid4().hex}_{secure_filename(id_proof.filename)}"
                id_proof.save(os.path.join(app.config['UPLOAD_FOLDER'], id_proof_filename))

        db = get_db()
        db.execute(
            """INSERT INTO passes
               (user_id, full_name, age, gender, route_from, route_to, pass_type, price, status, photo, id_proof)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)""",
            (session['user_id'], full_name, age_val, gender, route_from, route_to,
             pass_type, price, photo_filename, id_proof_filename)
        )
        db.commit()
        flash('Bus pass application submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('apply_pass.html', prices=PASS_PRICES, stops=MUMBAI_STOPS, grouped_stops=MUMBAI_STOPS_GROUPED)


@app.route('/payment/<int:pass_id>')
@login_required
def payment(pass_id):
    """Payment page for an approved pass."""
    db = get_db()
    bus_pass = db.execute(
        "SELECT * FROM passes WHERE id = ? AND user_id = ?",
        (pass_id, session['user_id'])
    ).fetchone()

    if not bus_pass:
        flash('Pass not found.', 'danger')
        return redirect(url_for('dashboard'))

    if bus_pass['status'] != 'Approved':
        flash('This pass is not approved for payment yet.', 'warning')
        return redirect(url_for('dashboard'))

    return render_template('payment.html', bus_pass=bus_pass, key_id=RAZORPAY_KEY_ID)


@app.route('/download_pass/<int:pass_id>')
@login_required
def download_pass(pass_id):
    """Download the PDF pass."""
    db = get_db()
    bus_pass = db.execute(
        "SELECT * FROM passes WHERE id = ? AND user_id = ?",
        (pass_id, session['user_id'])
    ).fetchone()

    if not bus_pass or bus_pass['status'] not in ('Active', 'Expired'):
        flash('Pass not available for download.', 'warning')
        return redirect(url_for('dashboard'))

    # Always generate fresh to ensure updates are reflected
    passes_dir = app.config['PASSES_FOLDER']
    pass_data = dict(bus_pass)
    filename = generate_pass_pdf(pass_data, session.get('user_name', ''))

    return send_file(
        os.path.join(passes_dir, filename),
        as_attachment=True,
        download_name=f"BusPass_{pass_id}.pdf"
    )


@app.route('/renew/<int:pass_id>', methods=['GET', 'POST'])
@login_required
def renew_pass(pass_id):
    """Renew an expired pass."""
    db = get_db()
    bus_pass = db.execute(
        "SELECT * FROM passes WHERE id = ? AND user_id = ?",
        (pass_id, session['user_id'])
    ).fetchone()

    if not bus_pass:
        flash('Pass not found.', 'danger')
        return redirect(url_for('dashboard'))

    if bus_pass['status'] != 'Expired':
        flash('Only expired passes can be renewed.', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        pass_type = request.form.get('pass_type', 'monthly')
        if pass_type not in PASS_PRICES:
            pass_type = 'monthly'

        price = PASS_PRICES[pass_type]

        # Apply distance-based pricing for renewal
        multiplier = get_distance_multiplier(bus_pass['route_from'], bus_pass['route_to'])
        price = round(price * multiplier)

        # Create a new pass application based on old data
        db.execute(
            """INSERT INTO passes
               (user_id, full_name, age, gender, route_from, route_to, pass_type, price, status, photo, id_proof)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)""",
            (session['user_id'], bus_pass['full_name'], bus_pass['age'], bus_pass['gender'],
             bus_pass['route_from'], bus_pass['route_to'], pass_type, price,
             bus_pass['photo'], bus_pass['id_proof'])
        )
        db.commit()
        flash('Renewal application submitted! Awaiting admin approval.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('renew_pass.html', bus_pass=bus_pass, prices=PASS_PRICES, stops=MUMBAI_STOPS)


@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    """Submit a support ticket."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, subject, message]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('support'))

        db = get_db()
        db.execute(
            "INSERT INTO support_tickets (user_id, name, email, subject, message) VALUES (?, ?, ?, ?, ?)",
            (session['user_id'], name, email, subject, message)
        )
        db.commit()
        flash('Support ticket submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('support.html')


# =========================================================================
#  ADMIN ROUTES
# =========================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with overview statistics."""
    db = get_db()

    users = db.execute("SELECT * FROM users WHERE role = 'user' ORDER BY created_at DESC").fetchall()
    passes = db.execute(
        """SELECT p.*, u.name as user_name, u.email as user_email
           FROM passes p JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC"""
    ).fetchall()
    payments = db.execute(
        """SELECT pay.*, p.full_name, p.route_from, p.route_to, p.pass_type
           FROM payments pay JOIN passes p ON pay.pass_id = p.id
           ORDER BY pay.paid_at DESC"""
    ).fetchall()
    tickets = db.execute("SELECT * FROM support_tickets ORDER BY created_at DESC").fetchall()
    messages = db.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()

    # Auto-expire passes
    today = datetime.now().strftime('%Y-%m-%d')
    for p in passes:
        if p['status'] == 'Active' and p['expiry_date'] and p['expiry_date'] < today:
            db.execute("UPDATE passes SET status = 'Expired' WHERE id = ?", (p['id'],))
    db.commit()

    # Re-fetch passes after expiry update
    passes = db.execute(
        """SELECT p.*, u.name as user_name, u.email as user_email
           FROM passes p JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC"""
    ).fetchall()

    stats = {
        'total_users': len(users),
        'total_passes': len(passes),
        'pending_passes': sum(1 for p in passes if p['status'] == 'Pending'),
        'active_passes': sum(1 for p in passes if p['status'] == 'Active'),
        'total_revenue': sum(p['amount'] for p in payments),
        'open_tickets': sum(1 for t in tickets if t['status'] == 'Pending'),
    }

    return render_template(
        'admin_dashboard.html',
        users=users, passes=passes, payments=payments,
        tickets=tickets, messages=messages, stats=stats
    )


@app.route('/admin/view_pass/<int:pass_id>')
@admin_required
def admin_view_pass(pass_id):
    """View details of a single pass application for admin verification."""
    db = get_db()
    # Join with users to get applicant email
    bus_pass = db.execute(
        """SELECT p.*, u.name as user_name, u.email as user_email
           FROM passes p JOIN users u ON p.user_id = u.id
           WHERE p.id = ?""", (pass_id,)
    ).fetchone()

    if not bus_pass:
        flash('Pass not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_view_pass.html', p=bus_pass)


@app.route('/admin/approve/<int:pass_id>')
@admin_required
def admin_approve(pass_id):
    """Approve a pass application."""
    db = get_db()
    # Get pass details for notification
    p = db.execute("SELECT user_id, pass_type FROM passes WHERE id = ?", (pass_id,)).fetchone()
    
    db.execute("UPDATE passes SET status = 'Approved' WHERE id = ? AND status = 'Pending'", (pass_id,))
    
    if p:
        pass_label = PASS_LABELS.get(p['pass_type'], 'Bus Pass')
        msg = f"✅ Your {pass_label} application has been approved! Proceed to payment."
        db.execute(
            "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
            (p['user_id'], msg, 'success')
        )
    
    db.commit()
    flash(f'Pass #{pass_id} approved.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:pass_id>')
@admin_required
def admin_reject(pass_id):
    """Reject a pass application."""
    db = get_db()
    # Get pass details for notification
    p = db.execute("SELECT user_id, pass_type FROM passes WHERE id = ?", (pass_id,)).fetchone()
    
    db.execute("UPDATE passes SET status = 'Rejected' WHERE id = ? AND status = 'Pending'", (pass_id,))
    
    if p:
        pass_label = PASS_LABELS.get(p['pass_type'], 'Bus Pass')
        msg = f"❌ Your {pass_label} application has been rejected."
        db.execute(
            "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
            (p['user_id'], msg, 'danger')
        )
        
    db.commit()
    flash(f'Pass #{pass_id} rejected.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ticket/<int:ticket_id>/<status>')
@admin_required
def admin_update_ticket(ticket_id, status):
    """Update support ticket status."""
    valid_statuses = ['Pending', 'In Progress', 'Resolved']
    if status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    db.execute("UPDATE support_tickets SET status = ? WHERE id = ?", (status, ticket_id))
    db.commit()
    flash(f'Ticket #{ticket_id} updated to {status}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ticket/respond', methods=['POST'])
@admin_required
def admin_ticket_respond():
    """Admin responds to a support ticket and creates a user notification."""
    ticket_id = request.form.get('ticket_id')
    response_text = request.form.get('admin_response', '').strip()

    if not ticket_id or not response_text:
        flash('Ticket ID and response are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    ticket = db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()
    
    if not ticket:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Update ticket with response and mark as Resolved
    db.execute(
        "UPDATE support_tickets SET admin_response = ?, status = 'Resolved' WHERE id = ?",
        (response_text, ticket_id)
    )

    # Create notification for the user if user_id exists
    if ticket['user_id']:
        msg = f"Admin responded: '{response_text}' (Ticket: {ticket['subject']})"
        db.execute(
            "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
            (ticket['user_id'], msg, 'success')
        )

    db.commit()
    flash(f'Response sent for Ticket #{ticket_id}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ticket/delete/<int:ticket_id>')
@admin_required
def admin_delete_ticket(ticket_id):
    """Delete a support ticket."""
    db = get_db()
    db.execute("DELETE FROM support_tickets WHERE id = ?", (ticket_id,))
    db.commit()
    flash(f'Ticket #{ticket_id} deleted.', 'info')
    return redirect(url_for('admin_dashboard'))


# =========================================================================
#  API ENDPOINTS
# =========================================================================

@app.route('/api/route-price')
def api_route_price():
    """Calculate distance-based pricing for the frontend."""
    route_from = request.args.get('from')
    route_to = request.args.get('to')
    
    if not route_from or not route_to:
        return jsonify({'error': 'Missing locations'}), 400
        
    multiplier = get_distance_multiplier(route_from, route_to)
    
    # Determine distance category label
    if multiplier < 1.0:
        category = "Short Distance"
    elif multiplier == 1.0:
        category = "Medium Distance"
    elif multiplier <= 1.2:
        category = "Long Distance"
    else:
        category = "Very Long Distance"
    
    # Calculate adjusted prices for all pass types
    adjusted = {}
    for p_type, base in PASS_PRICES.items():
        adjusted[p_type] = round(base * multiplier)
        
    return jsonify({
        'multiplier': multiplier,
        'category': category,
        'prices': adjusted
    })


@app.route('/api/create_order/<int:pass_id>', methods=['POST'])
@login_required
def api_create_order(pass_id):
    """Generate a Razorpay order from the backend."""
    db = get_db()
    bus_pass = db.execute(
        "SELECT * FROM passes WHERE id = ? AND user_id = ?",
        (pass_id, session['user_id'])
    ).fetchone()

    if not bus_pass or bus_pass['status'] != 'Approved':
        return jsonify({'error': 'Unauthorized or invalid pass status'}), 400

    # Razorpay amount is in paise (1 INR = 100 paise)
    amount = int(bus_pass['price'] * 100)
    data = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"receipt_pass_{pass_id}",
        "payment_capture": 1  # 1 means automatic capture
    }

    try:
        order = client.order.create(data=data)
        
        # Store order info in DB
        db.execute(
            "INSERT INTO payments (pass_id, user_id, amount, order_id, status) VALUES (?, ?, ?, ?, ?)",
            (pass_id, session['user_id'], bus_pass['price'], order['id'], 'pending')
        )
        db.commit()
        
        return jsonify(order)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Razorpay Error: {str(e)}")
        return jsonify({'error': f'Failed to create order: {str(e)}'}), 500


@app.route('/api/verify_payment', methods=['POST'])
@login_required
def api_verify_payment():
    """Verify Razorpay payment signature."""
    data = request.get_json()
    
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    pass_id = data.get('pass_id')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, pass_id]):
        return jsonify({'error': 'Missing payment details'}), 400

    # Verification logic
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        # Verify signature
        client.utility.verify_payment_signature(params_dict)
        
        # Security passed, update DB
        db = get_db()
        bus_pass = db.execute("SELECT * FROM passes WHERE id = ?", (pass_id,)).fetchone()
        
        if not bus_pass:
            return jsonify({'error': 'Pass not found'}), 404

        # Calculate dates
        issue_date = datetime.now().strftime('%Y-%m-%d')
        duration_days = PASS_DURATIONS.get(bus_pass['pass_type'], 30)
        expiry_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')

        # Update payment record
        db.execute(
            """UPDATE payments 
               SET razorpay_payment_id = ?, signature = ?, status = 'success', paid_at = CURRENT_TIMESTAMP 
               WHERE order_id = ?""",
            (razorpay_payment_id, razorpay_signature, razorpay_order_id)
        )

        # Update pass status to Active
        db.execute(
            "UPDATE passes SET status = 'Active', issue_date = ?, expiry_date = ? WHERE id = ?",
            (issue_date, expiry_date, pass_id)
        )
        db.commit()

        # Generate PDF
        pass_data = db.execute("SELECT * FROM passes WHERE id = ?", (pass_id,)).fetchone()
        generate_pass_pdf(dict(pass_data), session.get('user_name', ''))

        return jsonify({'success': True, 'message': 'Payment verified and pass activated'})
        
    except razorpay.errors.SignatureVerificationError:
        print("Signature verification failed!")
        return jsonify({'error': 'Invalid payment signature'}), 400
    except Exception as e:
        print(f"Verification Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notifications/read', methods=['POST'])
@login_required
def api_notifications_read():
    """Mark all notifications as read for current user."""
    db = get_db()
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (session['user_id'],))
    db.commit()
    return jsonify({'success': True})


# =========================================================================
#  ERROR HANDLERS
# =========================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# =========================================================================
#  APP ENTRY POINT
# =========================================================================

# Always initialize DB (needed for gunicorn/Render deployment)
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("=" * 50)
    print("  Smart Bus Pass Management System")
    print("  Running at http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
