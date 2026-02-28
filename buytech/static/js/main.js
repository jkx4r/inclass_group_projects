// ============================================================
// BuyTech — main.js
// Custom JavaScript for UI enhancements
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // ── AUTO-DISMISS FLASH ALERTS ──
    // Alerts disappear automatically after 4 seconds
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 4000);
    });

    // ── NAVBAR SCROLL SHADOW ──
    // Add extra shadow to navbar when user scrolls down
    const navbar = document.querySelector('.bt-navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 30) {
                navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.12)';
            } else {
                navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.06)';
            }
        });
    }

    // ── QUANTITY INPUT GUARD ──
    // Prevent quantity from going below 1 in cart form
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            if (parseInt(this.value) < 1 || isNaN(parseInt(this.value))) {
                this.value = 1;
            }
        });
    });

    // ── PRODUCT IMAGE HOVER ZOOM ──
    // CSS already handles this via transform, but JS adds a class for extra effects
    const productCards = document.querySelectorAll('.bt-product-card');
    productCards.forEach(function (card) {
        card.addEventListener('mouseenter', function () {
            this.style.zIndex = '2';
        });
        card.addEventListener('mouseleave', function () {
            this.style.zIndex = '1';
        });
    });

    // ── SMOOTH SCROLL TO TOP ──
    // If a #top anchor exists, smooth scroll
    const scrollLinks = document.querySelectorAll('a[href="#top"]');
    scrollLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    console.log('✅ BuyTech JS loaded successfully!');
});
