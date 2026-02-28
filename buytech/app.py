# ============================================================
# BuyTech - Electronics eCommerce Web App
# Built with Python Flask | University Project
# ============================================================

from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, uuid

# Pillow for server-side image resizing/compression
try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)

# Secret key for session management (change this in production!)
app.config['SECRET_KEY'] = 'buytech-secret-key-2024'

# SQLite database file path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///buytech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

# ── Upload Configuration ──────────────────────────────────
UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_IMAGE_SIZE   = (1200, 1200)   # Max dimensions before resizing
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB hard limit per upload

app.config['UPLOAD_FOLDER']     = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # Ensure folder exists


def allowed_file(filename):
    """Check if filename has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_product_image(file_obj, old_image_path=None):
    """
    Save an uploaded image file:
      - Validate extension
      - Resize down to MAX_IMAGE_SIZE using Pillow (preserves aspect ratio)
      - Convert to JPEG for consistent size/quality
      - Save with a unique UUID filename
      - Delete old uploaded image if it exists
    Returns the web-accessible URL path like /static/uploads/abc123.jpg
    """
    if not file_obj or file_obj.filename == '':
        return None

    if not allowed_file(file_obj.filename):
        return None

    # Generate a unique filename to avoid collisions
    ext      = file_obj.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.jpg"   # Always save as JPEG
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if PILLOW_AVAILABLE:
        # Open with Pillow, resize if too large, save as JPEG
        img = PILImage.open(file_obj.stream)

        # Convert RGBA/palette images to RGB so JPEG works
        if img.mode in ('RGBA', 'P', 'LA'):
            background = PILImage.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize only if image is larger than MAX_IMAGE_SIZE (maintain aspect ratio)
        img.thumbnail(MAX_IMAGE_SIZE, PILImage.LANCZOS)

        # Save with good quality — 85% strikes balance between size and quality
        img.save(filepath, 'JPEG', quality=85, optimize=True)
    else:
        # Pillow not available — save raw file as-is
        file_obj.seek(0)
        file_obj.save(filepath)

    # Delete the old uploaded image (only if it was a local upload, not a URL)
    if old_image_path and old_image_path.startswith('/static/uploads/'):
        old_filepath = os.path.join(
            os.path.dirname(__file__),
            old_image_path.lstrip('/')
        )
        if os.path.exists(old_filepath):
            os.remove(old_filepath)

    # Return the URL path usable in <img src="">
    return f"/static/uploads/{filename}"

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'          # Redirect here if not logged in
login_manager.login_message_category = 'warning'

# ─────────────────────────────────────────────
# DATABASE MODELS
# ─────────────────────────────────────────────

class User(UserMixin, db.Model):
    """User model — stores registered customers and admins."""
    __tablename__ = 'user'

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Unique login name
    password = db.Column(db.String(200), nullable=False)               # Hashed password
    is_admin = db.Column(db.Boolean, default=False)                    # Admin flag

    # Relationship: one user → many cart items
    cart_items = db.relationship('Cart', backref='user', lazy=True)


class Product(db.Model):
    """Product model — stores all electronics products."""
    __tablename__ = 'product'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price       = db.Column(db.Float, nullable=False)
    image       = db.Column(db.String(300), nullable=False)  # URL or file path
    category    = db.Column(db.String(50), nullable=False)   # Phones/Laptops/TVs/Accessories
    featured    = db.Column(db.Boolean, default=False)        # Show on homepage

    # Relationship: one product → many cart entries
    cart_items = db.relationship('Cart', backref='product', lazy=True)


class Cart(db.Model):
    """Cart model — links users to products they've added."""
    __tablename__ = 'cart'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity   = db.Column(db.Integer, default=1, nullable=False)


# ─────────────────────────────────────────────
# Flask-Login: Load user from session
# ─────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────
# Custom Decorator: Admin-only routes
# ─────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# SEED DATA — Default Products
# ─────────────────────────────────────────────
def seed_products():
    """
    Insert default products if the database is empty.
    Images use high-quality Unsplash photos (via picsum.photos for variety).
    This runs once on first startup.
    """
    if Product.query.count() > 0:
        return  # Already seeded — do nothing

    default_products = [
        # ── PHONES ──
        {
            'name': 'BuyTech Galaxy Pro 25',
            'description': 'Experience the future with our flagship smartphone. Features a 6.8" Dynamic AMOLED display, 200MP camera, 5000mAh battery, and blazing-fast Snapdragon 8 Gen 3 processor. Water-resistant with IP68 rating.',
            'price': 1199.99,
            'image': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&q=80',
            'category': 'Phones',
            'featured': True
        },
        {
            'name': 'BuyTech Lite Z6',
            'description': 'The perfect mid-range phone. 6.4" FHD+ display, 64MP triple camera system, 4500mAh battery with 25W fast charging. Available in 4 elegant colors.',
            'price': 499.99,
            'image': 'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=600&q=80',
            'category': 'Phones',
            'featured': True
        },
        {
            'name': 'BuyTech Flip 5',
            'description': 'Compact and stylish foldable phone. Unfolds to a 6.7" display with Flex Mode for hands-free video calls and photos. Fits in any pocket.',
            'price': 899.99,
            'image': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&q=80',
            'category': 'Phones',
            'featured': False
        },

        # ── LAPTOPS ──
        {
            'name': 'BuyTech Book Pro 15',
            'description': 'Thin, light, and powerful. Intel Core i7 13th Gen, 16GB RAM, 512GB NVMe SSD, 15.6" OLED touchscreen. All-day battery life up to 18 hours.',
            'price': 1499.99,
            'image': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80',
            'category': 'Laptops',
            'featured': True
        },
        {
            'name': 'BuyTech ChromeBook Air',
            'description': 'Lightweight Chromebook for students and professionals. 13.3" Full HD display, Intel Celeron, 8GB RAM, 128GB eMMC. Perfect for everyday tasks and cloud work.',
            'price': 349.99,
            'image': 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=600&q=80',
            'category': 'Laptops',
            'featured': False
        },
        {
            'name': 'BuyTech Gaming Beast X',
            'description': 'Dominate every game. AMD Ryzen 9, NVIDIA RTX 4070, 32GB DDR5 RAM, 1TB SSD, 17.3" 165Hz QHD display. RGB backlit keyboard included.',
            'price': 2199.99,
            'image': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&q=80',
            'category': 'Laptops',
            'featured': True
        },

        # ── TVs ──
        {
            'name': 'BuyTech QLED 55" 4K',
            'description': 'Stunning 55-inch QLED 4K display with Quantum HDR 32x, Object Tracking Sound, and 120Hz refresh rate. Smart TV with built-in Alexa and Google Assistant.',
            'price': 1099.99,
            'image': 'https://images.unsplash.com/photo-1593359677879-a4bb92f829e1?w=600&q=80',
            'category': 'TVs',
            'featured': True
        },
        {
            'name': 'BuyTech Crystal UHD 43"',
            'description': 'Crystal clear 43-inch 4K UHD smart TV. Purcolor technology delivers rich, detailed colours. Includes remote, wall mount kit, and HDMI 2.1 ports.',
            'price': 549.99,
            'image': 'https://images.unsplash.com/photo-1567690187548-f07b1d7bf5a9?w=600&q=80',
            'category': 'TVs',
            'featured': False
        },
        {
            'name': 'BuyTech Frame TV 65"',
            'description': 'When you\'re not watching, it\'s art. The Frame displays your favourite artworks and photos in stunning detail. 65" 4K QLED with no-gap wall mount.',
            'price': 1799.99,
            'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80',
            'category': 'TVs',
            'featured': False
        },

        # ── ACCESSORIES ──
        {
            'name': 'BuyTech Buds Pro 2',
            'description': 'True wireless earbuds with intelligent active noise cancellation. 29-hour total battery, IPX7 water resistance, and Hi-Fi sound with 10mm woofer.',
            'price': 229.99,
            'image': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&q=80',
            'category': 'Accessories',
            'featured': True
        },
        {
            'name': 'BuyTech Watch Ultra 6',
            'description': 'Advanced health monitoring smartwatch. ECG sensor, blood pressure monitor, sleep tracking, and built-in GPS. 3-day battery life, sapphire glass display.',
            'price': 399.99,
            'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80',
            'category': 'Accessories',
            'featured': True
        },
        {
            'name': 'BuyTech 65W Charger Kit',
            'description': 'Universal 65W super-fast charging kit. Includes USB-C cable, wall adapter, and portable 10,000mAh power bank. Compatible with all BuyTech devices.',
            'price': 79.99,
            'image': 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=600&q=80',
            'category': 'Accessories',
            'featured': False
        },
    ]

    # Insert all products into the database
    for item in default_products:
        product = Product(**item)
        db.session.add(product)

    db.session.commit()
    print(f"✅ Seeded {len(default_products)} default products into the database.")


def seed_admin():
    """Create a default admin account if none exists."""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            name='Admin',
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created: username=admin / password=admin123")


# ─────────────────────────────────────────────
# ROUTES — Public Pages
# ─────────────────────────────────────────────

@app.route('/')
def home():
    """Homepage — hero banner, categories, featured products."""
    # Fetch only featured products for the homepage
    featured_products = Product.query.filter_by(featured=True).limit(8).all()
    return render_template('index.html', products=featured_products)


@app.route('/shop')
def shop():
    """Shop page — all products with optional category filter."""
    category = request.args.get('category', '')  # Get ?category= from URL

    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()

    # Get unique categories for the filter buttons
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('shop.html', products=products,
                           categories=categories, selected_category=category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page — full info, add to cart."""
    product = Product.query.get_or_404(product_id)
    # Related products from same category (excluding current)
    related = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# ─────────────────────────────────────────────
# ROUTES — Authentication
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user account (username + name + password, no email needed)."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name     = request.form.get('name').strip()
        username = request.form.get('username').strip().lower()
        password = request.form.get('password')
        confirm  = request.form.get('confirm_password')

        # Basic validation
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'warning')
            return redirect(url_for('register'))

        # Hash password before storing
        hashed_pw = generate_password_hash(password)
        new_user  = User(name=name, username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login an existing user using username + password."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.name}! 👋', 'success')
            # Redirect to the page they originally tried to access
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ─────────────────────────────────────────────
# ROUTES — Cart
# ─────────────────────────────────────────────

@app.route('/cart')
@login_required
def cart():
    """Show current user's cart with total price."""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    # Calculate total price
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart — admins cannot add to cart."""
    # Admins manage products, they don't shop
    if current_user.is_admin:
        flash('Admins cannot add items to cart.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))

    product = Product.query.get_or_404(product_id)

    # Check if product is already in user's cart
    existing = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        existing.quantity += 1  # Increment quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash(f'"{product.name}" added to cart! 🛒', 'success')
    # Go back to wherever they clicked Add to Cart from
    next_page = request.form.get('next') or request.referrer or url_for('shop')
    return redirect(next_page)


@app.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    """Update quantity of a cart item."""
    cart_item = Cart.query.get_or_404(cart_id)

    # Security: ensure item belongs to current user
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart'))

    quantity = int(request.form.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    cart_item.quantity = quantity
    db.session.commit()
    flash('Cart updated.', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    """Remove a specific item from the cart."""
    cart_item = Cart.query.get_or_404(cart_id)

    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


@app.route('/checkout')
@login_required
def checkout():
    """Checkout page — show payment options (PromptPay / Card)."""
    if current_user.is_admin:
        return redirect(url_for('home'))

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    total     = sum(item.product.price * item.quantity for item in cart_items)
    shipping  = 0 if total >= 99 else 9.99
    tax       = total * 0.08
    grand_total = total + shipping + tax

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           shipping=shipping,
                           tax=tax,
                           grand_total=grand_total)


@app.route('/checkout/complete', methods=['POST'])
@login_required
def checkout_complete():
    """Process checkout — clear cart and show success page."""
    if current_user.is_admin:
        return redirect(url_for('home'))

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return redirect(url_for('cart'))

    # Capture order details before clearing cart
    total       = sum(item.product.price * item.quantity for item in cart_items)
    shipping    = 0 if total >= 99 else 9.99
    tax         = total * 0.08
    grand_total = total + shipping + tax
    item_count  = sum(item.quantity for item in cart_items)
    method      = request.form.get('payment_method', 'card')

    # Generate a fake order number
    import random, string
    order_num = 'BT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Clear the user's cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    return render_template('checkout_success.html',
                           order_num=order_num,
                           grand_total=grand_total,
                           item_count=item_count,
                           method=method)


# ─────────────────────────────────────────────
# ROUTES — Admin Panel
# ─────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard — overview of products grouped by category, users, cart stats."""
    all_products = Product.query.order_by(Product.category, Product.name).all()
    users        = User.query.filter_by(is_admin=False).all()   # Regular customers
    admins       = User.query.filter_by(is_admin=True).all()    # All admins
    total_orders = Cart.query.count()

    categories = ['Phones', 'Laptops', 'TVs', 'Accessories']
    products_by_category = {cat: [p for p in all_products if p.category == cat] for cat in categories}
    category_stats       = {cat: len(products_by_category[cat]) for cat in categories}

    return render_template('admin/dashboard.html',
                           all_products=all_products,
                           products_by_category=products_by_category,
                           category_stats=category_stats,
                           categories=categories,
                           users=users,
                           admins=admins,
                           total_orders=total_orders)


@app.route('/admin/add-admin', methods=['POST'])
@login_required
@admin_required
def admin_add_admin():
    """Admin: Create a new admin account."""
    name     = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not username or not password:
        flash('All fields are required to create an admin.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "@{username}" is already taken.', 'warning')
        return redirect(url_for('admin_dashboard'))

    new_admin = User(
        name=name,
        username=username,
        password=generate_password_hash(password),
        is_admin=True
    )
    db.session.add(new_admin)
    db.session.commit()
    flash(f'Admin "{name}" (@{username}) created successfully! 🛡️', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    """Admin: Add a new product — supports both image upload and URL."""
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price       = float(request.form.get('price', 0))
        category    = request.form.get('category', '').strip()
        featured    = 'featured' in request.form

        # ── Image: prefer file upload, fall back to URL ──
        image_url = request.form.get('image_url', '').strip()
        file      = request.files.get('image_file')

        if file and file.filename:
            # User uploaded a file — process and save it
            saved = save_product_image(file)
            if saved:
                image_url = saved
            else:
                flash('Invalid image file. Use PNG, JPG, WEBP, or GIF.', 'danger')
                return redirect(url_for('admin_add_product'))
        elif not image_url:
            flash('Please provide an image — either upload a file or paste a URL.', 'danger')
            return redirect(url_for('admin_add_product'))

        product = Product(name=name, description=description,
                          price=price, image=image_url,
                          category=category, featured=featured)
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{name}" added successfully! 🎉', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_product.html')


@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    """Admin: Edit an existing product — supports image upload or URL change."""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name        = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.price       = float(request.form.get('price', 0))
        product.category    = request.form.get('category', '').strip()
        product.featured    = 'featured' in request.form

        # ── Image: prefer file upload, fall back to URL ──
        file      = request.files.get('image_file')
        image_url = request.form.get('image_url', '').strip()

        if file and file.filename:
            # New file uploaded — resize, save, replace old
            saved = save_product_image(file, old_image_path=product.image)
            if saved:
                product.image = saved
            else:
                flash('Invalid image file. Use PNG, JPG, WEBP, or GIF.', 'danger')
                return redirect(url_for('admin_edit_product', product_id=product_id))
        elif image_url:
            # URL changed (or entered for first time)
            product.image = image_url
        # If neither: keep the existing image

        db.session.commit()
        flash(f'Product "{product.name}" updated! ✅', 'success')
        return redirect(url_for('admin_dashboard'))  # Always return to admin panel

    return render_template('admin/edit_product.html', product=product)


@app.route('/admin/delete/<int:product_id>')
@login_required
@admin_required
def admin_delete_product(product_id):
    """Admin: Delete a product (also removes from all carts)."""
    product = Product.query.get_or_404(product_id)

    # Remove related cart items first to avoid foreign key errors
    Cart.query.filter_by(product_id=product_id).delete()
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))


# ─────────────────────────────────────────────
# App Entry Point
# ─────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()       # Create tables if they don't exist
        seed_products()       # Insert default products
        seed_admin()          # Create default admin account

    app.run(debug=True)       # Run in debug mode for development
