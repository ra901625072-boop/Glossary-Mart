// ========== Utility Functions ==========

/**
 * Format currency to Indian Rupee format
 */
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}

/**
 * Show success toast notification
 */
function showToast(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Confirm action with custom modal
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ========== Image Preview ==========

/**
 * Preview image before upload
 */
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById(previewId).src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ========== Form Validation ==========

/**
 * Validate number input (positive numbers only)
 */
function validatePositiveNumber(input) {
    if (input.value < 0) {
        input.value = 0;
    }
}

/**
 * Validate stock before sale
 */
function validateStock(quantity, availableStock) {
    if (quantity > availableStock) {
        showToast(`Only ${availableStock} units available in stock!`, 'warning');
        return false;
    }
    return true;
}

// ========== Auto-dismiss alerts ==========
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// ========== Number Input Formatting ==========

/**
 * Format number inputs to 2 decimal places on blur
 */
document.addEventListener('DOMContentLoaded', function () {
    const priceInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    priceInputs.forEach(input => {
        input.addEventListener('blur', function () {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
});

// ========== Chart Utilities ==========

/**
 * Common Chart.js configuration
 */
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: 'top',
            labels: {
                usePointStyle: true,
                padding: 15,
                font: {
                    size: 12,
                    family: "'Inter', sans-serif"
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            cornerRadius: 8,
            titleFont: {
                size: 14,
                family: "'Inter', sans-serif"
            },
            bodyFont: {
                size: 13,
                family: "'Inter', sans-serif"
            }
        }
    }
};

// ========== Loading State ==========

/**
 * Show loading spinner on button
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

// ========== AJAX Helpers ==========

/**
 * Fetch product details via API
 */
async function fetchProductDetails(productId) {
    try {
        const response = await fetch(`/api/product/${productId}`);
        if (!response.ok) throw new Error('Product not found');
        return await response.json();
    } catch (error) {
        console.error('Error fetching product:', error);
        showToast('Error loading product details', 'danger');
        return null;
    }
}

// ========== Print Functionality ==========

/**
 * Print current page or element
 */
function printElement(elementId) {
    const printContent = document.getElementById(elementId);
    const windowUrl = 'about:blank';
    const windowName = 'Print';
    const printWindow = window.open(windowUrl, windowName);

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Print</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                @media print {
                    body { padding: 20px; }
                    .no-print { display: none; }
                }
            </style>
        </head>
        <body>
            ${printContent.innerHTML}
        </body>
        </html>
    `);

    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 500);
}

// ========== Local Storage Helpers ==========

/**
 * Save data to local storage
 */
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

/**
 * Get data from local storage
 */
function getFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return null;
    }
}

// ========== Console Welcome Message ==========
console.log('%c🏪 Jay Goga Kirana Store Management System', 'color: #667eea; font-size: 20px; font-weight: bold;');
console.log('%cWelcome! System loaded successfully.', 'color: #10b981; font-size: 14px;');
