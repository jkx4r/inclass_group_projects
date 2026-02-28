# ⚡ BuyTech — Electronics eCommerce Website
> A Samsung-inspired premium electronics store built with Python Flask

---

## 📁 Project Structure

```
buytech/
├── app.py                    # Main Flask app (routes, models, logic)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base layout (navbar + footer)
│   ├── index.html            # Homepage
│   ├── shop.html             # Shop / product listing
│   ├── product_detail.html   # Single product page
│   ├── cart.html             # Shopping cart
│   ├── login.html            # Login form
│   ├── register.html         # Register form
│   ├── about.html            # About page
│   ├── contact.html          # Contact page
│   └── admin/
│       ├── dashboard.html    # Admin overview
│       ├── add_product.html  # Add new product
│       └── edit_product.html # Edit existing product
│
└── static/
    ├── css/
    │   └── style.css         # Custom styles (Samsung-inspired)
    └── js/
        └── main.js           # Custom JavaScript
```

---

## 🚀 Setup & Run Instructions

### Step 1 — Make sure Python is installed
```bash
python --version      # Should be 3.8 or higher
```

### Step 2 — Create a virtual environment (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
pip install Pillow
```

### Step 4 — Run the app
```bash
python app.py
```

### Step 5 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🗄️ Database

- SQLite database file: `instance/buytech.db` (auto-created on first run)
- **12 default products** are seeded automatically on first startup
- Categories: Phones, Laptops, TVs, Accessories

---

## 🔐 Admin Account (Auto-created)

| Field    | Value               |
|----------|---------------------|
| Email    | admin@buytech.com   |
| Password | admin123            |
| Access   | /admin              |

> ⚠️ Change these credentials in `app.py` before deploying!

---

## 📄 Pages

| URL                        | Page                |
|----------------------------|---------------------|
| `/`                        | Homepage            |
| `/shop`                    | All Products        |
| `/shop?category=Phones`    | Filtered Products   |
| `/product/<id>`            | Product Detail      |
| `/cart`                    | Shopping Cart       |
| `/login`                   | Login               |
| `/register`                | Register            |
| `/about`                   | About               |
| `/contact`                 | Contact             |
| `/admin`                   | Admin Dashboard     |
| `/admin/add`               | Add Product         |
| `/admin/edit/<id>`         | Edit Product        |
| `/admin/delete/<id>`       | Delete Product      |

---

## 🛠️ Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python 3 + Flask        |
| Database   | SQLite + Flask-SQLAlchemy |
| Auth       | Flask-Login             |
| Frontend   | HTML5, CSS3, Bootstrap 5 |
| Templates  | Jinja2                  |
| Fonts      | Google Fonts — Inter    |
| Icons      | Bootstrap Icons         |

---

## ✨ Features

- ✅ Samsung-inspired clean, modern UI
- ✅ Responsive — works on mobile, tablet, desktop
- ✅ Hero carousel banner
- ✅ Category filter on shop page
- ✅ Product detail with related products
- ✅ Shopping cart with quantity update & remove
- ✅ User authentication (login/register/logout)
- ✅ Admin panel (add/edit/delete products)
- ✅ Auto-seeded database (12 products on first run)
- ✅ Flash messages for user feedback
- ✅ Hover animations and smooth transitions

---

*University Project — Built with Flask & Bootstrap 5*
