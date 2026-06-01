# Smart Bus Pass Management System

A comprehensive online bus pass management system built with Python Flask, featuring Razorpay payment integration, QR code verification, PDF pass generation, and responsive design.

## Features

### Core Features

- 🚌 **Online Bus Pass Application** – Apply for bus passes from anywhere with document upload
- 💳 **Secure Payment Integration** – Razorpay API for safe online transactions
- 📱 **QR Code Verification** – Each pass contains a scannable QR code for conductor verification
- 📄 **PDF Pass Generation** – Professional digitally-signed PDF bus passes with ReportLab
- 📱 **Mobile-Friendly Design** – Fully responsive UI for all devices
- 🔐 **User Authentication** – Secure login/signup with role-based access
- 🔍 **Smart Route Selection** – 200+ Mumbai bus stops with area-based grouping
- 💰 **Distance-Based Pricing** – Dynamic fare calculation based on route distance
- 🔔 **Real-time Notifications** – In-app alerts for pass approvals, rejections, and expiry reminders
- 📊 **Booking Management** – Track and manage all pass applications

### User Types

- **Passengers** – Apply, pay, download, and renew bus passes
- **Administrators** – Manage users, approve/reject passes, respond to tickets, and view analytics

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (easily upgradeable to PostgreSQL/MySQL)
- **Authentication**: Werkzeug Security (password hashing)
- **Payments**: Razorpay API
- **PDF Generation**: ReportLab
- **QR Code**: qrcode library with PIL
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Font Awesome

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Razorpay account (for payment processing)

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/sauravkarande48/BussPassSystem.git
cd BussPassSystem

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

Create a `.env` file in the root directory and add the following configuration variables:

```env
# Razorpay API Credentials
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'
```

### Step 3: Get API Keys

#### Razorpay Setup:

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Create an account or login
3. Go to **Settings → API Keys**
4. Generate your Key ID and Key Secret
5. Update the keys in your `.env` file

### Step 4: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### For Passengers

1. **Registration**: Create an account using the signup page
2. **Login**: Access your dashboard with email and password
3. **Apply for Pass**: Fill in personal details, select route (from/to), choose pass type, and upload ID proof
4. **Wait for Approval**: Admin reviews and approves/rejects your application
5. **Payment**: Once approved, pay securely using credit/debit cards via Razorpay
6. **Download Pass**: Download your professional PDF bus pass with QR code
7. **Renewal**: Renew expired passes directly from the dashboard

### For Administrators

1. **Login as Admin**: Use admin credentials to access the admin dashboard
2. **Dashboard**: View statistics – total users, passes, revenue, and open tickets
3. **Manage Passes**: Review, approve, or reject pass applications with ID proof verification
4. **Support Tickets**: Respond to user queries and resolve tickets
5. **View Payments**: Monitor all payment transactions and revenue

### Default Login Credentials

The system creates a default admin account on first run:

- **Admin**: email: `admin@buspass.com`, password: `admin123`

## Pass Types & Pricing

| Pass Type | Duration | Base Price (₹) |
|-----------|----------|----------------|
| Weekly Pass | 7 days | ₹150 |
| Monthly Pass | 30 days | ₹500 |
| 3-Month Pass | 90 days | ₹1,350 |
| 6-Month Pass | 180 days | ₹2,700 |
| Student Pass | 30 days | ₹400 |
| Senior Citizen Pass | 30 days | ₹350 |

> **Note**: Prices are dynamically adjusted based on route distance (short/medium/long/very long distance multipliers).

## Code Explanation

### app.py (Main Application)

- **Database Models**: Users, Passes, Payments, Support Tickets, Notifications, Contact Messages with relationships
- **Authentication**: Login/logout functionality with Werkzeug password hashing
- **Routes**: All page routes and API endpoints
- **Payment Processing**: Razorpay integration with order creation and signature verification
- **PDF Generation**: ReportLab-based professional bus pass PDF with QR codes and watermarks
- **Route Logic**: Mumbai bus stops mapping, area-based grouping, and distance-based fare calculation
- **Auto-Expiry**: Automatic pass expiry detection and status updates
- **Notifications**: In-app notification system with renewal reminders

### Templates

- **base.html**: Common layout with responsive navigation and authentication state
- **home.html**: Attractive landing page with features and call to action
- **login.html**: User authentication form with validation
- **register.html**: User registration form with password confirmation
- **dashboard.html**: User dashboard with pass overview, stats, notifications, and tickets
- **apply_pass.html**: Comprehensive pass application form with route selection and file upload
- **payment.html**: Secure Razorpay payment integration page
- **renew_pass.html**: Pass renewal form with pre-filled data
- **admin_dashboard.html**: Admin panel with tabs for users, passes, payments, tickets, and messages
- **admin_view_pass.html**: Detailed pass verification view for admin review
- **verify_pass_status.html**: Public QR code verification page for conductors
- **services.html**: Services overview page
- **about.html**: About the platform page
- **contact.html**: Contact form with database storage
- **help.html**: FAQ and help documentation
- **support.html**: Support ticket submission form
- **404.html / 500.html**: Custom error pages

### Static Assets

- **css/style.css**: Complete styling with responsive design
- **js/main.js**: Client-side JavaScript for interactivity
- **logo.png**: Application logo used in PDF generation
- **default_profile.png**: Default user profile placeholder

## Security Features

- 🔒 Password hashing with Werkzeug
- 🛡️ Role-based access control (user/admin decorators)
- 💳 Secure payment processing with Razorpay signature verification
- 🔑 Session management with Flask
- 📁 Secure file uploads with extension validation and size limits (5 MB)
- 🔐 Environment variables for sensitive API keys
- 🛡️ HMAC signature verification for payment callbacks

## Customization

### Adding New Features

- Extend database models in `app.py` (init_db function)
- Add new routes and templates as needed
- Update navigation in `base.html`

### Styling

- Modify CSS in `static/css/style.css`
- Update responsive breakpoints for different themes
- Add custom CSS files if needed

### Payment Methods

- Integrate additional payment gateways
- Add UPI, wallet, or other local payment options
- Modify `payment.html` template accordingly

### Route Configuration

- Update `MUMBAI_AREAS` and `MUMBAI_AREAS_MAP` in `app.py` for different cities
- Adjust distance multipliers in `get_distance_multiplier()` function
- Modify `PASS_PRICES` and `PASS_DURATIONS` for custom pricing

## Production Deployment

### Database

Replace SQLite with PostgreSQL or MySQL:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host:port/dbname'
```

### Environment Variables

Use environment variables for sensitive data:

```python
import os
app.secret_key = os.environ.get('SECRET_KEY')
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
```

### Web Server

Deploy with Gunicorn, uWSGI, or similar WSGI server:

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

## 🔧 Troubleshooting

### Common Issues

1. **Razorpay payments failing**: Check API keys and ensure test mode settings are correct
2. **Database errors**: Ensure SQLite file permissions are correct; delete `database.db` to reset
3. **PDF generation errors**: Verify ReportLab is installed correctly (`pip install reportlab`)
4. **QR code not generating**: Ensure `qrcode[pil]` is installed with Pillow support
5. **File upload errors**: Check `static/uploads` directory exists and has write permissions
6. **Import errors**: Verify all dependencies are installed in the virtual environment

### Getting Help

- Check Flask documentation: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- Razorpay documentation: [https://razorpay.com/docs/](https://razorpay.com/docs/)
- ReportLab documentation: [https://docs.reportlab.com/](https://docs.reportlab.com/)

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request with description

**Note**: This is a complete, functional bus pass management system suitable for learning and small-scale deployment. For production use, consider additional security measures, error handling, and scalability optimizations.
