/**
 * Main JavaScript file for Lotoryjung App
 */

// Global configuration
const AppConfig = {
    apiBaseUrl: '/api',
    csrfToken: null,
    currentUser: null,
    payoutRates: {
        '2_top': 90,
        '2_bottom': 90,
        '3_top': 900,
        'tote': 150
    }
};

// Utility functions
const Utils = {
    /**
     * Format number as Thai currency
     */
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('th-TH', {
            style: 'currency',
            currency: 'THB',
            minimumFractionDigits: 2
        }).format(amount);
    },

    /**
     * Format date as Thai format
     */
    formatDate: function(date, includeTime = false) {
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            timeZone: 'Asia/Bangkok'
        };
        
        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        
        return new Intl.DateTimeFormat('th-TH', options).format(new Date(date));
    },

    /**
     * Normalize lottery number
     */
    normalizeNumber: function(number, field) {
        const clean = number.replace(/\D/g, '');
        
        if (field === '2_top' || field === '2_bottom') {
            return clean.padStart(2, '0').slice(-2);
        } else if (field === '3_top') {
            return clean.padStart(3, '0').slice(-3);
        } else if (field === 'tote') {
            return clean.length <= 2 ? clean.padStart(2, '0') : clean.padStart(3, '0').slice(-3);
        }
        
        return clean;
    },

    /**
     * Validate number format
     */
    validateNumber: function(number, field) {
        const clean = number.replace(/\D/g, '');
        
        if (!clean) {
            return { valid: false, message: 'กรุณาใส่เลข' };
        }
        
        switch (field) {
            case '2_top':
            case '2_bottom':
                if (clean.length > 2) {
                    return { valid: false, message: 'เลข 2 ตัวต้องไม่เกิน 2 หลัก' };
                }
                break;
            case '3_top':
                if (clean.length > 3) {
                    return { valid: false, message: 'เลข 3 ตัวต้องไม่เกิน 3 หลัก' };
                }
                break;
            case 'tote':
                if (clean.length < 2 || clean.length > 3) {
                    return { valid: false, message: 'เลขโต๊ดต้องมี 2-3 หลัก' };
                }
                break;
        }
        
        return { valid: true };
    },

    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if not exists
        if (!$('#toastContainer').length) {
            $('body').append('<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }
        
        const $toast = $(toastHtml);
        $('#toastContainer').append($toast);
        
        const toast = new bootstrap.Toast($toast[0]);
        toast.show();
        
        // Remove toast element after hiding
        $toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    },

    /**
     * Show loading overlay
     */
    showLoading: function(message = 'กำลังโหลด...') {
        if (!$('#loadingOverlay').length) {
            $('body').append(`
                <div id="loadingOverlay" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
                     style="background: rgba(0,0,0,0.5); z-index: 9999;">
                    <div class="bg-white rounded p-4 text-center">
                        <div class="spinner-border text-primary mb-3" role="status"></div>
                        <div>${message}</div>
                    </div>
                </div>
            `);
        }
        $('#loadingOverlay').show();
    },

    /**
     * Hide loading overlay
     */
    hideLoading: function() {
        $('#loadingOverlay').hide();
    },

    /**
     * Debounce function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// API helper functions
const API = {
    /**
     * Make API request with CSRF protection
     */
    request: async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': AppConfig.csrfToken
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(AppConfig.apiBaseUrl + endpoint, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get rules for a specific field
     */
    getRules: async function(field) {
        return await this.request(`/rules/${field}`);
    },

    /**
     * Get blocked numbers for a specific field
     */
    getBlockedNumbers: async function(field) {
        return await this.request(`/blocked_numbers/${field}`);
    },

    /**
     * Get current total for a specific number
     */
    getNumberTotal: async function(field, number) {
        return await this.request(`/number_totals/${field}/${number}`);
    },

    /**
     * Validate order before submission
     */
    validateOrder: async function(orderData) {
        return await this.request('/validate_order', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }
};

// Form validation helpers
const FormValidation = {
    /**
     * Add validation to form fields
     */
    init: function() {
        // Add real-time validation to number inputs
        $(document).on('input', '.number-input', function() {
            const $input = $(this);
            const field = $input.closest('.order-item').find('select').val();
            const number = $input.val();
            
            if (field && number) {
                const validation = Utils.validateNumber(number, field);
                FormValidation.showFieldValidation($input, validation);
            }
        });
        
        // Add real-time validation to amount inputs
        $(document).on('input', '.amount-input', function() {
            const $input = $(this);
            const amount = parseFloat($input.val());
            
            if (amount <= 0) {
                FormValidation.showFieldValidation($input, {
                    valid: false,
                    message: 'จำนวนเงินต้องมากกว่า 0'
                });
            } else {
                FormValidation.clearFieldValidation($input);
            }
        });
    },

    /**
     * Show field validation message
     */
    showFieldValidation: function($field, validation) {
        $field.removeClass('is-valid is-invalid');
        $field.siblings('.invalid-feedback, .valid-feedback').remove();
        
        if (!validation.valid) {
            $field.addClass('is-invalid');
            $field.after(`<div class="invalid-feedback">${validation.message}</div>`);
        } else {
            $field.addClass('is-valid');
        }
    },

    /**
     * Clear field validation
     */
    clearFieldValidation: function($field) {
        $field.removeClass('is-valid is-invalid');
        $field.siblings('.invalid-feedback, .valid-feedback').remove();
    }
};

// Number checking functionality
const NumberChecker = {
    cache: new Map(),
    
    /**
     * Check if number is blocked
     */
    checkBlocked: Utils.debounce(async function(field, number, callback) {
        const cacheKey = `blocked_${field}_${number}`;
        
        if (NumberChecker.cache.has(cacheKey)) {
            callback(NumberChecker.cache.get(cacheKey));
            return;
        }
        
        try {
            const result = await API.getBlockedNumbers(field);
            const isBlocked = result.blocked_numbers.includes(number);
            
            NumberChecker.cache.set(cacheKey, isBlocked);
            callback(isBlocked);
        } catch (error) {
            console.error('Error checking blocked numbers:', error);
            callback(false);
        }
    }, 300),

    /**
     * Check current total for number
     */
    checkTotal: Utils.debounce(async function(field, number, callback) {
        const cacheKey = `total_${field}_${number}`;
        
        if (NumberChecker.cache.has(cacheKey)) {
            callback(NumberChecker.cache.get(cacheKey));
            return;
        }
        
        try {
            const result = await API.getNumberTotal(field, number);
            
            NumberChecker.cache.set(cacheKey, result);
            callback(result);
        } catch (error) {
            console.error('Error checking number total:', error);
            callback({ current_total: 0, order_count: 0 });
        }
    }, 300),

    /**
     * Clear cache
     */
    clearCache: function() {
        NumberChecker.cache.clear();
    }
};

// Auto-save functionality for forms
const AutoSave = {
    interval: null,
    
    /**
     * Start auto-save for form
     */
    start: function(formId, saveCallback, interval = 30000) {
        AutoSave.stop(); // Stop any existing auto-save
        
        AutoSave.interval = setInterval(() => {
            const formData = AutoSave.getFormData(formId);
            if (formData) {
                saveCallback(formData);
            }
        }, interval);
    },

    /**
     * Stop auto-save
     */
    stop: function() {
        if (AutoSave.interval) {
            clearInterval(AutoSave.interval);
            AutoSave.interval = null;
        }
    },

    /**
     * Get form data
     */
    getFormData: function(formId) {
        const $form = $(formId);
        if (!$form.length) return null;
        
        const formData = {};
        $form.find('input, select, textarea').each(function() {
            const $field = $(this);
            const name = $field.attr('name');
            const value = $field.val();
            
            if (name && value) {
                formData[name] = value;
            }
        });
        
        return Object.keys(formData).length > 0 ? formData : null;
    },

    /**
     * Save to localStorage
     */
    saveToLocal: function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    /**
     * Load from localStorage
     */
    loadFromLocal: function(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return null;
        }
    }
};

// Initialize app when DOM is ready
$(document).ready(function() {
    // Initialize form validation
    FormValidation.init();
    
    // Get CSRF token
    AppConfig.csrfToken = $('meta[name=csrf-token]').attr('content');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    $('.alert:not(.alert-permanent)').delay(5000).fadeOut();
    
    // Confirm dialogs for dangerous actions
    $(document).on('click', '[data-confirm]', function(e) {
        const message = $(this).data('confirm');
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });
    
    // Auto-format number inputs
    $(document).on('input', '.number-input', function() {
        let value = $(this).val().replace(/\D/g, '');
        const maxLength = $(this).attr('maxlength') || 3;
        value = value.slice(0, maxLength);
        $(this).val(value);
    });
    
    // Auto-format amount inputs
    $(document).on('blur', '.amount-input', function() {
        const value = parseFloat($(this).val());
        if (!isNaN(value)) {
            $(this).val(value.toFixed(2));
        }
    });
    
    // Prevent form submission on Enter key in number/amount inputs
    $(document).on('keypress', '.number-input, .amount-input', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            $(this).blur();
        }
    });
    
    console.log('Lotoryjung App initialized');
});

// Cleanup on page unload
$(window).on('beforeunload', function() {
    AutoSave.stop();
});

// Export to global scope
window.AppConfig = AppConfig;
window.Utils = Utils;
window.API = API;
window.FormValidation = FormValidation;
window.NumberChecker = NumberChecker;
window.AutoSave = AutoSave;

