/**
 * Smart Bus Pass Management System – Main JavaScript
 * Handles: mobile nav, flash messages, accordion, tabs, scroll animations, form validation
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    //  MOBILE NAVBAR TOGGLE
    // =========================================================================
    const navToggle = document.querySelector('.navbar-toggle');
    const navLinks = document.querySelector('.navbar-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            const icon = navToggle.querySelector('span');
            if (icon) {
                icon.textContent = navLinks.classList.contains('open') ? '✕' : '☰';
            }
        });

        // Close nav when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => navLinks.classList.remove('open'));
        });
    }

    // =========================================================================
    //  NAVBAR SCROLL EFFECT
    // =========================================================================
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    // =========================================================================
    //  FLASH MESSAGE AUTO-DISMISS
    // =========================================================================
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((msg, index) => {
        // Auto dismiss after 5 seconds (staggered)
        setTimeout(() => {
            msg.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => msg.remove(), 400);
        }, 4000 + index * 800);

        // Close button
        const closeBtn = msg.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                msg.style.animation = 'slideOut 0.4s ease forwards';
                setTimeout(() => msg.remove(), 400);
            });
        }
    });

    // =========================================================================
    //  FAQ ACCORDION
    // =========================================================================
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.closest('.accordion-item');
            const body = item.querySelector('.accordion-body');
            const isActive = item.classList.contains('active');

            // Close all
            document.querySelectorAll('.accordion-item.active').forEach(active => {
                active.classList.remove('active');
                const activeBody = active.querySelector('.accordion-body');
                if (activeBody) activeBody.style.maxHeight = '0';
            });

            // Toggle current
            if (!isActive) {
                item.classList.add('active');
                body.style.maxHeight = body.scrollHeight + 'px';
            }
        });
    });

    // =========================================================================
    //  DASHBOARD TABS
    // =========================================================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            // Deactivate all
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Activate target
            btn.classList.add('active');
            const panel = document.getElementById(target);
            if (panel) panel.classList.add('active');
        });
    });

    // =========================================================================
    //  SCROLL ANIMATIONS
    // =========================================================================
    const animateElements = document.querySelectorAll('.animate-in');
    if (animateElements.length > 0) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry, i) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.classList.add('visible');
                        }, i * 100);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1 }
        );
        animateElements.forEach(el => observer.observe(el));
    }

    // =========================================================================
    //  PAYMENT CARD LIVE PREVIEW
    // =========================================================================
    const cardNumberInput = document.getElementById('card_number');
    const cardExpiryInput = document.getElementById('expiry');
    const cardHolderInput = document.getElementById('holder_name');
    const cardPreviewNumber = document.getElementById('preview-card-number');
    const cardPreviewHolder = document.getElementById('preview-card-holder');
    const cardPreviewExpiry = document.getElementById('preview-card-expiry');

    if (cardNumberInput && cardPreviewNumber) {
        cardNumberInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, '').substring(0, 16);
            let formatted = val.replace(/(.{4})/g, '$1 ').trim();
            e.target.value = formatted;
            cardPreviewNumber.textContent = formatted || '•••• •••• •••• ••••';
        });
    }

    if (cardHolderInput && cardPreviewHolder) {
        cardHolderInput.addEventListener('input', (e) => {
            cardPreviewHolder.textContent = e.target.value || 'CARD HOLDER';
        });
    }

    if (cardExpiryInput && cardPreviewExpiry) {
        cardExpiryInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, '').substring(0, 4);
            if (val.length > 2) val = val.substring(0, 2) + '/' + val.substring(2);
            e.target.value = val;
            cardPreviewExpiry.textContent = val || 'MM/YY';
        });
    }

    // CVV max length
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 3);
        });
    }

    // =========================================================================
    //  FORM VALIDATION FEEDBACK
    // =========================================================================
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            let valid = true;
            form.querySelectorAll('[required]').forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.style.borderColor = 'var(--danger)';
                    input.addEventListener('input', () => {
                        input.style.borderColor = '';
                    }, { once: true });
                }
            });
            if (!valid) {
                e.preventDefault();
                const firstInvalid = form.querySelector('[required]:invalid, [required][style*="border-color"]');
                if (firstInvalid) firstInvalid.focus();
            }
        });
    });

    // =========================================================================
    //  OLD CONFIRM ACTIONS (Removed in favor of new custom modal in base.html)
    // =========================================================================
    // The previous implementation used window.confirm() which looked unprofessional.
    // It has been replaced by the dynamic modal system in base.html.
});
