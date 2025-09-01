# P1 Implementation: Dashboard Filters and Services

## ภาพรวม
เอกสารนี้กำหนดการ implement P1 requirements สำหรับ Dashboard Filters และ Services ต่างๆ ในระบบ Lotoryjung ตาม Review Report รวมถึงการปรับปรุง User Interface และการเพิ่มฟีเจอร์ที่จำเป็น

## 1. Advanced Dashboard Filters

### 1.1 User Dashboard Enhancements
การปรับปรุง User Dashboard ให้มีตัวกรองข้อมูลที่ครบถ้วนและใช้งานง่าย เพื่อให้ผู้ใช้สามารถค้นหาและวิเคราะห์ข้อมูลการซื้อของตนเองได้อย่างมีประสิทธิภาพ

```html
<!-- templates/user/dashboard.html -->
<div class="dashboard-container">
    <!-- Filter Panel -->
    <div class="filter-panel card mb-4">
        <div class="card-header">
            <h5 class="mb-0">
                <i class="fas fa-filter"></i> ตัวกรองข้อมูล
                <button class="btn btn-sm btn-outline-secondary float-right" id="resetFilters">
                    <i class="fas fa-undo"></i> รีเซ็ต
                </button>
            </h5>
        </div>
        <div class="card-body">
            <form id="filterForm">
                <div class="row">
                    <!-- Date Range Filter -->
                    <div class="col-md-3">
                        <label for="dateRange">ช่วงวันที่:</label>
                        <select class="form-control" id="dateRange" name="date_range">
                            <option value="">ทั้งหมด</option>
                            <option value="today">วันนี้</option>
                            <option value="yesterday">เมื่อวาน</option>
                            <option value="this_week">สัปดาห์นี้</option>
                            <option value="last_week">สัปดาห์ที่แล้ว</option>
                            <option value="this_month">เดือนนี้</option>
                            <option value="last_month">เดือนที่แล้ว</option>
                            <option value="custom">กำหนดเอง</option>
                        </select>
                    </div>
                    
                    <!-- Custom Date Range -->
                    <div class="col-md-3" id="customDateRange" style="display: none;">
                        <label for="startDate">จาก:</label>
                        <input type="date" class="form-control" id="startDate" name="start_date">
                        <label for="endDate" class="mt-2">ถึง:</label>
                        <input type="date" class="form-control" id="endDate" name="end_date">
                    </div>
                    
                    <!-- Lottery Period Filter -->
                    <div class="col-md-3">
                        <label for="lotteryPeriod">งวดวันที่:</label>
                        <select class="form-control" id="lotteryPeriod" name="lottery_period">
                            <option value="">ทั้งหมด</option>
                            <!-- จะถูกโหลดจาก JavaScript -->
                        </select>
                    </div>
                    
                    <!-- Number Type Filter -->
                    <div class="col-md-3">
                        <label for="numberType">ประเภทเลข:</label>
                        <select class="form-control" id="numberType" name="number_type">
                            <option value="">ทั้งหมด</option>
                            <option value="2_top">2 ตัวบน</option>
                            <option value="2_bottom">2 ตัวล่าง</option>
                            <option value="3_top">3 ตัวบน</option>
                            <option value="tote">โต๊ด</option>
                        </select>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <!-- Number Filter -->
                    <div class="col-md-3">
                        <label for="numberFilter">เลข:</label>
                        <input type="text" class="form-control" id="numberFilter" name="number" 
                               placeholder="ระบุเลขที่ต้องการค้นหา">
                    </div>
                    
                    <!-- Amount Range Filter -->
                    <div class="col-md-3">
                        <label for="minAmount">จำนวนเงินขั้นต่ำ:</label>
                        <input type="number" class="form-control" id="minAmount" name="min_amount" 
                               min="0" step="0.01" placeholder="0.00">
                    </div>
                    
                    <div class="col-md-3">
                        <label for="maxAmount">จำนวนเงินสูงสุด:</label>
                        <input type="number" class="form-control" id="maxAmount" name="max_amount" 
                               min="0" step="0.01" placeholder="ไม่จำกัด">
                    </div>
                    
                    <!-- Status Filter -->
                    <div class="col-md-3">
                        <label for="statusFilter">สถานะ:</label>
                        <select class="form-control" id="statusFilter" name="status">
                            <option value="">ทั้งหมด</option>
                            <option value="pending">รอดำเนินการ</option>
                            <option value="confirmed">ยืนยันแล้ว</option>
                            <option value="cancelled">ยกเลิก</option>
                        </select>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-12">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> ค้นหา
                        </button>
                        <button type="button" class="btn btn-secondary ml-2" id="exportFiltered">
                            <i class="fas fa-download"></i> Export ข้อมูลที่กรอง
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Results Summary -->
    <div class="results-summary card mb-4" id="resultsSummary" style="display: none;">
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-3">
                    <h4 class="text-primary" id="totalOrders">0</h4>
                    <p class="mb-0">คำสั่งซื้อ</p>
                </div>
                <div class="col-md-3">
                    <h4 class="text-success" id="totalAmount">0</h4>
                    <p class="mb-0">จำนวนเงินรวม</p>
                </div>
                <div class="col-md-3">
                    <h4 class="text-info" id="totalItems">0</h4>
                    <p class="mb-0">รายการทั้งหมด</p>
                </div>
                <div class="col-md-3">
                    <h4 class="text-warning" id="avgAmount">0</h4>
                    <p class="mb-0">จำนวนเงินเฉลี่ย</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Orders Table -->
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">
                <i class="fas fa-list"></i> รายการคำสั่งซื้อ
                <span class="badge badge-secondary" id="recordCount">0</span>
            </h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped" id="ordersTable">
                    <thead>
                        <tr>
                            <th>หมายเลขคำสั่งซื้อ</th>
                            <th>วันที่สั่งซื้อ</th>
                            <th>งวดวันที่</th>
                            <th>จำนวนรายการ</th>
                            <th>จำนวนเงินรวม</th>
                            <th>สถานะ</th>
                            <th>การดำเนินการ</th>
                        </tr>
                    </thead>
                    <tbody id="ordersTableBody">
                        <!-- จะถูกโหลดจาก AJAX -->
                    </tbody>
                </table>
            </div>
            
            <!-- Pagination -->
            <nav aria-label="Page navigation" id="paginationNav">
                <ul class="pagination justify-content-center" id="pagination">
                    <!-- จะถูกสร้างจาก JavaScript -->
                </ul>
            </nav>
        </div>
    </div>
</div>
```

```javascript
// static/js/dashboard-filters.js
class DashboardFilters {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.currentFilters = {};
        
        this.initializeEventListeners();
        this.loadInitialData();
        this.loadLotteryPeriods();
    }
    
    initializeEventListeners() {
        // Form submission
        $('#filterForm').on('submit', (e) => {
            e.preventDefault();
            this.applyFilters();
        });
        
        // Reset filters
        $('#resetFilters').on('click', () => {
            this.resetFilters();
        });
        
        // Date range change
        $('#dateRange').on('change', (e) => {
            this.handleDateRangeChange(e.target.value);
        });
        
        // Export filtered data
        $('#exportFiltered').on('click', () => {
            this.exportFilteredData();
        });
        
        // Real-time number validation
        $('#numberFilter').on('input', (e) => {
            this.validateNumberInput(e.target);
        });
        
        // Amount validation
        $('#minAmount, #maxAmount').on('input', (e) => {
            this.validateAmountInput(e.target);
        });
    }
    
    handleDateRangeChange(value) {
        const customDateRange = $('#customDateRange');
        
        if (value === 'custom') {
            customDateRange.show();
        } else {
            customDateRange.hide();
            
            // Set predefined date ranges
            const today = new Date();
            let startDate, endDate;
            
            switch (value) {
                case 'today':
                    startDate = endDate = today;
                    break;
                case 'yesterday':
                    startDate = endDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case 'this_week':
                    const startOfWeek = new Date(today);
                    startOfWeek.setDate(today.getDate() - today.getDay());
                    startDate = startOfWeek;
                    endDate = today;
                    break;
                case 'last_week':
                    const lastWeekEnd = new Date(today);
                    lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
                    const lastWeekStart = new Date(lastWeekEnd);
                    lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
                    startDate = lastWeekStart;
                    endDate = lastWeekEnd;
                    break;
                case 'this_month':
                    startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    endDate = today;
                    break;
                case 'last_month':
                    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                    startDate = lastMonth;
                    endDate = lastMonthEnd;
                    break;
            }
            
            if (startDate && endDate) {
                $('#startDate').val(this.formatDate(startDate));
                $('#endDate').val(this.formatDate(endDate));
            }
        }
    }
    
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }
    
    validateNumberInput(input) {
        const value = input.value.trim();
        const numberType = $('#numberType').val();
        
        if (!value) {
            this.clearValidation(input);
            return;
        }
        
        let isValid = false;
        let errorMessage = '';
        
        if (numberType === '2_top' || numberType === '2_bottom') {
            isValid = /^\d{1,2}$/.test(value) && parseInt(value) <= 99;
            errorMessage = 'เลข 2 หลัก (00-99)';
        } else if (numberType === '3_top') {
            isValid = /^\d{1,3}$/.test(value) && parseInt(value) <= 999;
            errorMessage = 'เลข 3 หลัก (000-999)';
        } else if (numberType === 'tote') {
            isValid = /^\d{3}$/.test(value);
            errorMessage = 'โต๊ดต้องเป็นเลข 3 หลัก';
        } else {
            // ไม่ได้เลือกประเภท ให้ตรวจสอบแบบทั่วไป
            isValid = /^\d{1,3}$/.test(value);
            errorMessage = 'เลขต้องเป็นตัวเลข 1-3 หลัก';
        }
        
        if (isValid) {
            this.setValidation(input, true);
        } else {
            this.setValidation(input, false, errorMessage);
        }
    }
    
    validateAmountInput(input) {
        const value = parseFloat(input.value);
        const minAmount = parseFloat($('#minAmount').val()) || 0;
        const maxAmount = parseFloat($('#maxAmount').val()) || Infinity;
        
        if (input.id === 'minAmount' && maxAmount < Infinity && value > maxAmount) {
            this.setValidation(input, false, 'จำนวนขั้นต่ำต้องไม่เกินจำนวนสูงสุด');
        } else if (input.id === 'maxAmount' && value < minAmount) {
            this.setValidation(input, false, 'จำนวนสูงสุดต้องไม่น้อยกว่าจำนวนขั้นต่ำ');
        } else if (value < 0) {
            this.setValidation(input, false, 'จำนวนเงินต้องไม่น้อยกว่า 0');
        } else {
            this.setValidation(input, true);
        }
    }
    
    setValidation(input, isValid, message = '') {
        const $input = $(input);
        const $feedback = $input.siblings('.invalid-feedback');
        
        if (isValid) {
            $input.removeClass('is-invalid').addClass('is-valid');
            $feedback.remove();
        } else {
            $input.removeClass('is-valid').addClass('is-invalid');
            
            if ($feedback.length === 0) {
                $input.after(`<div class="invalid-feedback">${message}</div>`);
            } else {
                $feedback.text(message);
            }
        }
    }
    
    clearValidation(input) {
        const $input = $(input);
        $input.removeClass('is-valid is-invalid');
        $input.siblings('.invalid-feedback').remove();
    }
    
    async loadLotteryPeriods() {
        try {
            const response = await fetch('/api/lottery-periods');
            const periods = await response.json();
            
            const $select = $('#lotteryPeriod');
            $select.empty().append('<option value="">ทั้งหมด</option>');
            
            periods.forEach(period => {
                const option = new Option(
                    this.formatLotteryPeriod(period.date),
                    period.date
                );
                $select.append(option);
            });
            
        } catch (error) {
            console.error('Error loading lottery periods:', error);
        }
    }
    
    formatLotteryPeriod(dateString) {
        const date = new Date(dateString);
        const day = date.getDate();
        const month = date.getMonth() + 1;
        const year = date.getFullYear() + 543; // พ.ศ.
        
        return `${day}/${month}/${year}`;
    }
    
    applyFilters() {
        // Validate form first
        if (!this.validateForm()) {
            return;
        }
        
        // Collect filter values
        this.currentFilters = {
            date_range: $('#dateRange').val(),
            start_date: $('#startDate').val(),
            end_date: $('#endDate').val(),
            lottery_period: $('#lotteryPeriod').val(),
            number_type: $('#numberType').val(),
            number: $('#numberFilter').val(),
            min_amount: $('#minAmount').val(),
            max_amount: $('#maxAmount').val(),
            status: $('#statusFilter').val()
        };
        
        // Reset to first page
        this.currentPage = 1;
        
        // Load filtered data
        this.loadOrders();
    }
    
    validateForm() {
        let isValid = true;
        
        // Check all inputs with validation classes
        $('.is-invalid').each(function() {
            isValid = false;
        });
        
        // Check date range
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        if (startDate && endDate && startDate > endDate) {
            this.setValidation($('#endDate')[0], false, 'วันที่สิ้นสุดต้องไม่น้อยกว่าวันที่เริ่มต้น');
            isValid = false;
        }
        
        return isValid;
    }
    
    resetFilters() {
        // Clear form
        $('#filterForm')[0].reset();
        
        // Hide custom date range
        $('#customDateRange').hide();
        
        // Clear validation
        $('.is-valid, .is-invalid').removeClass('is-valid is-invalid');
        $('.invalid-feedback').remove();
        
        // Reset filters and reload
        this.currentFilters = {};
        this.currentPage = 1;
        this.loadOrders();
        
        // Hide results summary
        $('#resultsSummary').hide();
    }
    
    async loadOrders() {
        try {
            // Show loading
            this.showLoading();
            
            // Prepare parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                ...this.currentFilters
            });
            
            // Remove empty values
            for (const [key, value] of params.entries()) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            const response = await fetch(`/api/user/orders?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderOrders(data.orders);
                this.renderPagination(data.pagination);
                this.updateSummary(data.summary);
                $('#recordCount').text(data.pagination.total);
            } else {
                this.showError(data.error);
            }
            
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showError('เกิดข้อผิดพลาดในการโหลดข้อมูล');
        } finally {
            this.hideLoading();
        }
    }
    
    renderOrders(orders) {
        const tbody = $('#ordersTableBody');
        tbody.empty();
        
        if (orders.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i><br>
                        ไม่พบข้อมูลตามเงื่อนไขที่กำหนด
                    </td>
                </tr>
            `);
            return;
        }
        
        orders.forEach(order => {
            const row = `
                <tr>
                    <td>
                        <strong>${order.order_number}</strong>
                        ${order.customer_name ? `<br><small class="text-muted">${order.customer_name}</small>` : ''}
                    </td>
                    <td>${this.formatDateTime(order.created_at)}</td>
                    <td>${this.formatLotteryPeriod(order.lottery_period)}</td>
                    <td>
                        <span class="badge badge-info">${order.item_count}</span>
                    </td>
                    <td>
                        <strong class="text-success">฿${this.formatAmount(order.total_amount)}</strong>
                    </td>
                    <td>
                        <span class="badge badge-${this.getStatusColor(order.status)}">
                            ${this.getStatusText(order.status)}
                        </span>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewOrder('${order.order_number}')">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${order.pdf_path ? `
                                <button class="btn btn-outline-success" onclick="downloadReceipt('${order.order_number}')">
                                    <i class="fas fa-download"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
            tbody.append(row);
        });
    }
    
    renderPagination(pagination) {
        const nav = $('#pagination');
        nav.empty();
        
        if (pagination.total_pages <= 1) {
            $('#paginationNav').hide();
            return;
        }
        
        $('#paginationNav').show();
        
        // Previous button
        const prevDisabled = pagination.current_page === 1 ? 'disabled' : '';
        nav.append(`
            <li class="page-item ${prevDisabled}">
                <a class="page-link" href="#" data-page="${pagination.current_page - 1}">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `);
        
        // Page numbers
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
        
        if (startPage > 1) {
            nav.append(`<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`);
            if (startPage > 2) {
                nav.append(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const active = i === pagination.current_page ? 'active' : '';
            nav.append(`
                <li class="page-item ${active}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        if (endPage < pagination.total_pages) {
            if (endPage < pagination.total_pages - 1) {
                nav.append(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
            }
            nav.append(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.total_pages}">${pagination.total_pages}</a>
                </li>
            `);
        }
        
        // Next button
        const nextDisabled = pagination.current_page === pagination.total_pages ? 'disabled' : '';
        nav.append(`
            <li class="page-item ${nextDisabled}">
                <a class="page-link" href="#" data-page="${pagination.current_page + 1}">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `);
        
        // Add click handlers
        nav.find('a[data-page]').on('click', (e) => {
            e.preventDefault();
            const page = parseInt($(e.target).closest('a').data('page'));
            if (page && page !== this.currentPage) {
                this.currentPage = page;
                this.loadOrders();
            }
        });
    }
    
    updateSummary(summary) {
        if (summary) {
            $('#totalOrders').text(summary.total_orders.toLocaleString());
            $('#totalAmount').text('฿' + this.formatAmount(summary.total_amount));
            $('#totalItems').text(summary.total_items.toLocaleString());
            $('#avgAmount').text('฿' + this.formatAmount(summary.avg_amount));
            $('#resultsSummary').show();
        } else {
            $('#resultsSummary').hide();
        }
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('th-TH', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    formatAmount(amount) {
        return parseFloat(amount).toFixed(2);
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    getStatusText(status) {
        const texts = {
            'pending': 'รอดำเนินการ',
            'confirmed': 'ยืนยันแล้ว',
            'cancelled': 'ยกเลิก'
        };
        return texts[status] || status;
    }
    
    showLoading() {
        $('#ordersTableBody').html(`
            <tr>
                <td colspan="7" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">กำลังโหลด...</span>
                    </div>
                    <br>กำลังโหลดข้อมูล...
                </td>
            </tr>
        `);
    }
    
    hideLoading() {
        // Loading will be replaced by actual data
    }
    
    showError(message) {
        $('#ordersTableBody').html(`
            <tr>
                <td colspan="7" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>
                    ${message}
                </td>
            </tr>
        `);
    }
    
    async exportFilteredData() {
        try {
            // Prepare parameters
            const params = new URLSearchParams({
                export: 'csv',
                ...this.currentFilters
            });
            
            // Remove empty values
            for (const [key, value] of params.entries()) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            // Create download link
            const url = `/api/user/orders/export?${params}`;
            
            // Show loading
            const $btn = $('#exportFiltered');
            const originalText = $btn.html();
            $btn.html('<i class="fas fa-spinner fa-spin"></i> กำลัง Export...').prop('disabled', true);
            
            // Trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Restore button
            setTimeout(() => {
                $btn.html(originalText).prop('disabled', false);
            }, 2000);
            
        } catch (error) {
            console.error('Error exporting data:', error);
            alert('เกิดข้อผิดพลาดในการ export ข้อมูล');
        }
    }
    
    loadInitialData() {
        this.loadOrders();
    }
}

// Initialize when DOM is ready
$(document).ready(() => {
    window.dashboardFilters = new DashboardFilters();
});

// Global functions for buttons
function viewOrder(orderNumber) {
    window.location.href = `/user/orders/${orderNumber}`;
}

function downloadReceipt(orderNumber) {
    window.open(`/user/orders/${orderNumber}/receipt`, '_blank');
}
```

### 1.2 Admin Dashboard Advanced Filters
```python
# routes/admin_dashboard.py
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from utils.timezone_utils import get_thai_time, calculate_lottery_period_with_cutoff

admin_dashboard = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

@admin_dashboard.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard หลัก"""
    
    # ดึงข้อมูลสรุปเบื้องต้น
    current_time = get_thai_time()
    period_info = calculate_lottery_period_with_cutoff()
    
    # สถิติพื้นฐาน
    today_orders = db.session.query(Order).filter(
        func.date(Order.created_at) == current_time.date()
    ).count()
    
    today_amount = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == current_time.date()
    ).scalar() or 0
    
    current_batch_orders = db.session.query(Order).filter_by(
        batch_id=get_current_batch_id()
    ).count()
    
    current_batch_amount = db.session.query(func.sum(Order.total_amount)).filter_by(
        batch_id=get_current_batch_id()
    ).scalar() or 0
    
    # ข้อมูลผู้ใช้
    total_users = db.session.query(User).filter_by(role='user').count()
    active_users_today = db.session.query(func.distinct(Order.user_id)).filter(
        func.date(Order.created_at) == current_time.date()
    ).count()
    
    return render_template('admin/dashboard.html', {
        'current_time': current_time,
        'period_info': period_info,
        'stats': {
            'today_orders': today_orders,
            'today_amount': float(today_amount),
            'current_batch_orders': current_batch_orders,
            'current_batch_amount': float(current_batch_amount),
            'total_users': total_users,
            'active_users_today': active_users_today
        }
    })

@admin_dashboard.route('/api/orders')
@admin_required
@rate_limit_by_user("100 per minute")
def get_orders():
    """API สำหรับดึงข้อมูล orders พร้อม filters"""
    
    try:
        # ดึงพารามิเตอร์
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # Filters
        filters = {
            'date_range': request.args.get('date_range'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'lottery_period': request.args.get('lottery_period'),
            'batch_id': request.args.get('batch_id'),
            'user_id': request.args.get('user_id'),
            'status': request.args.get('status'),
            'min_amount': request.args.get('min_amount'),
            'max_amount': request.args.get('max_amount'),
            'order_number': request.args.get('order_number'),
            'customer_name': request.args.get('customer_name')
        }
        
        # สร้าง query
        query = db.session.query(Order).join(User)
        
        # Apply filters
        query = apply_order_filters(query, filters)
        
        # นับจำนวนทั้งหมด
        total_count = query.count()
        
        # Apply pagination
        orders = query.order_by(Order.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # สร้างผลลัพธ์
        result_orders = []
        for order in orders:
            user = db.session.query(User).get(order.user_id)
            item_count = db.session.query(OrderItem).filter_by(order_id=order.id).count()
            
            result_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'user_name': user.name if user else '',
                'user_username': user.username if user else '',
                'total_amount': float(order.total_amount),
                'status': order.status,
                'lottery_period': order.lottery_period.strftime('%Y-%m-%d') if order.lottery_period else None,
                'batch_id': order.batch_id,
                'item_count': item_count,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'pdf_path': order.pdf_path,
                'notes': order.notes
            })
        
        # สร้างข้อมูล pagination
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
        
        # สร้างสรุปข้อมูล
        summary = None
        if result_orders:
            total_amount = sum(order['total_amount'] for order in result_orders)
            total_items = sum(order['item_count'] for order in result_orders)
            
            summary = {
                'total_orders': len(result_orders),
                'total_amount': total_amount,
                'total_items': total_items,
                'avg_amount': total_amount / len(result_orders) if result_orders else 0
            }
        
        return jsonify({
            'success': True,
            'orders': result_orders,
            'pagination': pagination,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def apply_order_filters(query, filters):
    """Apply filters to order query"""
    
    # Date range filter
    if filters['date_range']:
        today = get_thai_time().date()
        
        if filters['date_range'] == 'today':
            query = query.filter(func.date(Order.created_at) == today)
        elif filters['date_range'] == 'yesterday':
            yesterday = today - timedelta(days=1)
            query = query.filter(func.date(Order.created_at) == yesterday)
        elif filters['date_range'] == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())
            query = query.filter(Order.created_at >= start_of_week)
        elif filters['date_range'] == 'last_week':
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            query = query.filter(
                and_(
                    Order.created_at >= start_of_last_week,
                    Order.created_at <= end_of_last_week
                )
            )
        elif filters['date_range'] == 'this_month':
            start_of_month = today.replace(day=1)
            query = query.filter(Order.created_at >= start_of_month)
        elif filters['date_range'] == 'last_month':
            start_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
            query = query.filter(
                and_(
                    Order.created_at >= start_of_last_month,
                    Order.created_at <= end_of_last_month
                )
            )
    
    # Custom date range
    if filters['start_date']:
        try:
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
            query = query.filter(func.date(Order.created_at) >= start_date)
        except ValueError:
            pass
    
    if filters['end_date']:
        try:
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
            query = query.filter(func.date(Order.created_at) <= end_date)
        except ValueError:
            pass
    
    # Lottery period filter
    if filters['lottery_period']:
        try:
            lottery_date = datetime.strptime(filters['lottery_period'], '%Y-%m-%d').date()
            query = query.filter(Order.lottery_period == lottery_date)
        except ValueError:
            pass
    
    # Batch ID filter
    if filters['batch_id']:
        query = query.filter(Order.batch_id == filters['batch_id'])
    
    # User filter
    if filters['user_id']:
        try:
            user_id = int(filters['user_id'])
            query = query.filter(Order.user_id == user_id)
        except ValueError:
            pass
    
    # Status filter
    if filters['status']:
        query = query.filter(Order.status == filters['status'])
    
    # Amount range filters
    if filters['min_amount']:
        try:
            min_amount = float(filters['min_amount'])
            query = query.filter(Order.total_amount >= min_amount)
        except ValueError:
            pass
    
    if filters['max_amount']:
        try:
            max_amount = float(filters['max_amount'])
            query = query.filter(Order.total_amount <= max_amount)
        except ValueError:
            pass
    
    # Order number filter
    if filters['order_number']:
        query = query.filter(Order.order_number.ilike(f"%{filters['order_number']}%"))
    
    # Customer name filter
    if filters['customer_name']:
        query = query.filter(Order.customer_name.ilike(f"%{filters['customer_name']}%"))
    
    return query

@admin_dashboard.route('/api/number-analysis')
@admin_required
@rate_limit_by_user("50 per minute")
def get_number_analysis():
    """API สำหรับวิเคราะห์ตัวเลข"""
    
    try:
        # ดึงพารามิเตอร์
        batch_id = request.args.get('batch_id', get_current_batch_id())
        field = request.args.get('field')
        limit = min(int(request.args.get('limit', 50)), 100)
        sort_by = request.args.get('sort_by', 'total_amount')  # total_amount, order_count, avg_amount
        
        # สร้าง query
        query = db.session.query(
            OrderItem.number_norm,
            OrderItem.field,
            func.count(OrderItem.id).label('order_count'),
            func.sum(OrderItem.buy_amount).label('total_amount'),
            func.avg(OrderItem.buy_amount).label('avg_amount'),
            func.max(OrderItem.buy_amount).label('max_amount'),
            func.min(OrderItem.buy_amount).label('min_amount'),
            func.count(func.distinct(Order.user_id)).label('unique_users')
        ).join(Order).filter(
            Order.batch_id == batch_id
        )
        
        # Apply field filter
        if field and field != 'all':
            query = query.filter(OrderItem.field == field)
        
        # Group by
        query = query.group_by(OrderItem.number_norm, OrderItem.field)
        
        # Sort
        if sort_by == 'order_count':
            query = query.order_by(func.count(OrderItem.id).desc())
        elif sort_by == 'avg_amount':
            query = query.order_by(func.avg(OrderItem.buy_amount).desc())
        else:  # total_amount
            query = query.order_by(func.sum(OrderItem.buy_amount).desc())
        
        # Apply limit
        results = query.limit(limit).all()
        
        # Format results
        analysis_data = []
        for result in results:
            analysis_data.append({
                'number_norm': result.number_norm,
                'field': result.field,
                'order_count': result.order_count,
                'total_amount': float(result.total_amount),
                'avg_amount': float(result.avg_amount),
                'max_amount': float(result.max_amount),
                'min_amount': float(result.min_amount),
                'unique_users': result.unique_users
            })
        
        return jsonify({
            'success': True,
            'analysis': analysis_data,
            'batch_id': batch_id,
            'field': field,
            'sort_by': sort_by,
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_dashboard.route('/api/user-analysis')
@admin_required
@rate_limit_by_user("30 per minute")
def get_user_analysis():
    """API สำหรับวิเคราะห์ผู้ใช้"""
    
    try:
        # ดึงพารามิเตอร์
        batch_id = request.args.get('batch_id', get_current_batch_id())
        limit = min(int(request.args.get('limit', 20)), 50)
        sort_by = request.args.get('sort_by', 'total_amount')
        
        # สร้าง query
        query = db.session.query(
            User.id,
            User.name,
            User.username,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_amount'),
            func.avg(Order.total_amount).label('avg_amount'),
            func.max(Order.total_amount).label('max_amount'),
            func.count(OrderItem.id).label('total_items'),
            func.max(Order.created_at).label('last_order_date')
        ).join(Order).join(OrderItem).filter(
            Order.batch_id == batch_id
        ).group_by(User.id, User.name, User.username)
        
        # Sort
        if sort_by == 'order_count':
            query = query.order_by(func.count(Order.id).desc())
        elif sort_by == 'avg_amount':
            query = query.order_by(func.avg(Order.total_amount).desc())
        elif sort_by == 'total_items':
            query = query.order_by(func.count(OrderItem.id).desc())
        else:  # total_amount
            query = query.order_by(func.sum(Order.total_amount).desc())
        
        # Apply limit
        results = query.limit(limit).all()
        
        # Format results
        user_analysis = []
        for result in results:
            user_analysis.append({
                'user_id': result.id,
                'name': result.name,
                'username': result.username,
                'order_count': result.order_count,
                'total_amount': float(result.total_amount),
                'avg_amount': float(result.avg_amount),
                'max_amount': float(result.max_amount),
                'total_items': result.total_items,
                'last_order_date': result.last_order_date.isoformat()
            })
        
        return jsonify({
            'success': True,
            'user_analysis': user_analysis,
            'batch_id': batch_id,
            'sort_by': sort_by,
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

## 2. Enhanced Services

### 2.1 Real-time Notification Service
```python
# services/notification_service.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json

socketio = SocketIO()

class NotificationService:
    """บริการแจ้งเตือนแบบ real-time"""
    
    def __init__(self):
        self.active_connections = {}  # user_id -> session_id
        self.admin_connections = set()  # admin session_ids
    
    def connect_user(self, user_id, session_id):
        """เชื่อมต่อผู้ใช้"""
        self.active_connections[user_id] = session_id
        join_room(f'user_{user_id}')
        
        # ส่งข้อมูลเริ่มต้น
        self.send_initial_data(user_id)
    
    def connect_admin(self, session_id):
        """เชื่อมต่อ admin"""
        self.admin_connections.add(session_id)
        join_room('admin')
        
        # ส่งสถิติเริ่มต้น
        self.send_admin_stats()
    
    def disconnect_user(self, user_id, session_id):
        """ตัดการเชื่อมต่อผู้ใช้"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        leave_room(f'user_{user_id}')
    
    def disconnect_admin(self, session_id):
        """ตัดการเชื่อมต่อ admin"""
        self.admin_connections.discard(session_id)
        leave_room('admin')
    
    def send_initial_data(self, user_id):
        """ส่งข้อมูลเริ่มต้นให้ผู้ใช้"""
        
        # ดึงข้อมูลงวดปัจจุบัน
        period_info = calculate_lottery_period_with_cutoff()
        
        # ดึงคำสั่งซื้อล่าสุด
        recent_orders = db.session.query(Order).filter_by(
            user_id=user_id
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        orders_data = []
        for order in recent_orders:
            orders_data.append({
                'order_number': order.order_number,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'created_at': order.created_at.isoformat()
            })
        
        socketio.emit('initial_data', {
            'period_info': period_info,
            'recent_orders': orders_data,
            'timestamp': datetime.now().isoformat()
        }, room=f'user_{user_id}')
    
    def send_admin_stats(self):
        """ส่งสถิติให้ admin"""
        
        current_batch = get_current_batch_id()
        
        # สถิติวันนี้
        today = get_thai_time().date()
        today_stats = {
            'orders': db.session.query(Order).filter(
                func.date(Order.created_at) == today
            ).count(),
            'amount': float(db.session.query(func.sum(Order.total_amount)).filter(
                func.date(Order.created_at) == today
            ).scalar() or 0),
            'users': db.session.query(func.distinct(Order.user_id)).filter(
                func.date(Order.created_at) == today
            ).count()
        }
        
        # สถิติงวดปัจจุบัน
        batch_stats = {
            'orders': db.session.query(Order).filter_by(batch_id=current_batch).count(),
            'amount': float(db.session.query(func.sum(Order.total_amount)).filter_by(
                batch_id=current_batch
            ).scalar() or 0),
            'users': db.session.query(func.distinct(Order.user_id)).filter_by(
                batch_id=current_batch
            ).count()
        }
        
        socketio.emit('admin_stats', {
            'today': today_stats,
            'current_batch': batch_stats,
            'batch_id': current_batch,
            'timestamp': datetime.now().isoformat()
        }, room='admin')
    
    def notify_order_created(self, order):
        """แจ้งเตือนเมื่อมีคำสั่งซื้อใหม่"""
        
        # แจ้งผู้ใช้
        socketio.emit('order_created', {
            'order_number': order.order_number,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'message': f'สร้างคำสั่งซื้อ {order.order_number} สำเร็จ'
        }, room=f'user_{order.user_id}')
        
        # แจ้ง admin
        user = db.session.query(User).get(order.user_id)
        socketio.emit('new_order', {
            'order_number': order.order_number,
            'user_name': user.name if user else 'Unknown',
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat(),
            'message': f'คำสั่งซื้อใหม่จาก {user.name if user else "Unknown"}'
        }, room='admin')
        
        # อัพเดทสถิติ admin
        self.send_admin_stats()
    
    def notify_order_status_changed(self, order, old_status, new_status):
        """แจ้งเตือนเมื่อสถานะคำสั่งซื้อเปลี่ยน"""
        
        status_messages = {
            'confirmed': 'ยืนยันคำสั่งซื้อแล้ว',
            'cancelled': 'ยกเลิกคำสั่งซื้อแล้ว',
            'completed': 'คำสั่งซื้อเสร็จสมบูรณ์'
        }
        
        message = status_messages.get(new_status, f'เปลี่ยนสถานะเป็น {new_status}')
        
        socketio.emit('order_status_changed', {
            'order_number': order.order_number,
            'old_status': old_status,
            'new_status': new_status,
            'message': f'{order.order_number}: {message}'
        }, room=f'user_{order.user_id}')
    
    def notify_cutoff_warning(self, minutes_remaining):
        """แจ้งเตือนเมื่อใกล้หมดเวลา cut-off"""
        
        message = f'เหลือเวลาสั่งซื้อ {minutes_remaining} นาที'
        
        # แจ้งผู้ใช้ทุกคน
        for user_id in self.active_connections.keys():
            socketio.emit('cutoff_warning', {
                'minutes_remaining': minutes_remaining,
                'message': message,
                'type': 'warning' if minutes_remaining > 5 else 'danger'
            }, room=f'user_{user_id}')
        
        # แจ้ง admin
        socketio.emit('cutoff_warning', {
            'minutes_remaining': minutes_remaining,
            'message': message,
            'active_users': len(self.active_connections)
        }, room='admin')
    
    def notify_system_maintenance(self, message, start_time=None, duration=None):
        """แจ้งเตือนการปิดปรุงระบบ"""
        
        notification = {
            'message': message,
            'type': 'maintenance',
            'timestamp': datetime.now().isoformat()
        }
        
        if start_time:
            notification['start_time'] = start_time.isoformat()
        
        if duration:
            notification['duration_minutes'] = duration
        
        # แจ้งทุกคน
        socketio.emit('system_notification', notification, broadcast=True)
    
    def get_online_users_count(self):
        """ดึงจำนวนผู้ใช้ออนไลน์"""
        return len(self.active_connections)
    
    def get_online_admins_count(self):
        """ดึงจำนวน admin ออนไลน์"""
        return len(self.admin_connections)

# SocketIO event handlers
notification_service = NotificationService()

@socketio.on('connect')
def handle_connect():
    """จัดการการเชื่อมต่อ"""
    
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if user_role == 'admin':
        notification_service.connect_admin(request.sid)
        emit('connected', {'role': 'admin'})
    elif user_id:
        notification_service.connect_user(user_id, request.sid)
        emit('connected', {'role': 'user', 'user_id': user_id})
    else:
        emit('error', {'message': 'Unauthorized'})
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """จัดการการตัดการเชื่อมต่อ"""
    
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if user_role == 'admin':
        notification_service.disconnect_admin(request.sid)
    elif user_id:
        notification_service.disconnect_user(user_id, request.sid)

@socketio.on('request_stats')
def handle_request_stats():
    """จัดการคำขอสถิติ"""
    
    user_role = session.get('user_role')
    
    if user_role == 'admin':
        notification_service.send_admin_stats()
    else:
        emit('error', {'message': 'Unauthorized'})

@socketio.on('ping')
def handle_ping():
    """จัดการ ping เพื่อรักษาการเชื่อมต่อ"""
    emit('pong', {'timestamp': datetime.now().isoformat()})
```

### 2.2 Advanced Analytics Service
```python
# services/analytics_service.py
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np

class AnalyticsService:
    """บริการวิเคราะห์ข้อมูลขั้นสูง"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_sales_trend(self, days=30, batch_id=None):
        """วิเคราะห์แนวโน้มการขาย"""
        
        end_date = get_thai_time().date()
        start_date = end_date - timedelta(days=days)
        
        # สร้าง query
        query = self.db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_amount'),
            func.count(func.distinct(Order.user_id)).label('unique_users')
        ).filter(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        
        if batch_id:
            query = query.filter(Order.batch_id == batch_id)
        
        results = query.group_by(func.date(Order.created_at)).all()
        
        # สร้าง DataFrame
        data = []
        for result in results:
            data.append({
                'date': result.date,
                'order_count': result.order_count,
                'total_amount': float(result.total_amount),
                'unique_users': result.unique_users,
                'avg_amount_per_order': float(result.total_amount) / result.order_count
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return {
                'trend_data': [],
                'summary': {
                    'total_days': days,
                    'total_orders': 0,
                    'total_amount': 0,
                    'avg_daily_orders': 0,
                    'avg_daily_amount': 0,
                    'growth_rate': 0
                }
            }
        
        # คำนวณแนวโน้ม
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # คำนวณ moving average
        df['order_count_ma'] = df['order_count'].rolling(window=7, min_periods=1).mean()
        df['total_amount_ma'] = df['total_amount'].rolling(window=7, min_periods=1).mean()
        
        # คำนวณ growth rate
        if len(df) > 1:
            first_week_avg = df.head(7)['total_amount'].mean()
            last_week_avg = df.tail(7)['total_amount'].mean()
            growth_rate = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
        else:
            growth_rate = 0
        
        # แปลงกลับเป็น dict
        trend_data = df.to_dict('records')
        for item in trend_data:
            item['date'] = item['date'].strftime('%Y-%m-%d')
        
        summary = {
            'total_days': days,
            'total_orders': int(df['order_count'].sum()),
            'total_amount': float(df['total_amount'].sum()),
            'avg_daily_orders': float(df['order_count'].mean()),
            'avg_daily_amount': float(df['total_amount'].mean()),
            'growth_rate': round(growth_rate, 2)
        }
        
        return {
            'trend_data': trend_data,
            'summary': summary
        }
    
    def get_number_popularity(self, batch_id=None, field=None, limit=50):
        """วิเคราะห์ความนิยมของตัวเลข"""
        
        query = self.db.query(
            OrderItem.number_norm,
            OrderItem.field,
            func.count(OrderItem.id).label('order_count'),
            func.sum(OrderItem.buy_amount).label('total_amount'),
            func.count(func.distinct(Order.user_id)).label('unique_users'),
            func.avg(OrderItem.buy_amount).label('avg_amount'),
            func.max(OrderItem.buy_amount).label('max_amount')
        ).join(Order)
        
        if batch_id:
            query = query.filter(Order.batch_id == batch_id)
        
        if field:
            query = query.filter(OrderItem.field == field)
        
        results = query.group_by(
            OrderItem.number_norm,
            OrderItem.field
        ).order_by(
            func.count(OrderItem.id).desc()
        ).limit(limit).all()
        
        popularity_data = []
        for result in results:
            popularity_data.append({
                'number_norm': result.number_norm,
                'field': result.field,
                'order_count': result.order_count,
                'total_amount': float(result.total_amount),
                'unique_users': result.unique_users,
                'avg_amount': float(result.avg_amount),
                'max_amount': float(result.max_amount),
                'popularity_score': result.order_count * result.unique_users  # คะแนนความนิยม
            })
        
        return popularity_data
    
    def get_user_behavior_analysis(self, batch_id=None, limit=20):
        """วิเคราะห์พฤติกรรมผู้ใช้"""
        
        query = self.db.query(
            User.id,
            User.name,
            User.username,
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_spent'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.max(Order.total_amount).label('max_order_value'),
            func.min(Order.total_amount).label('min_order_value'),
            func.count(OrderItem.id).label('total_items'),
            func.min(Order.created_at).label('first_order_date'),
            func.max(Order.created_at).label('last_order_date')
        ).join(Order).join(OrderItem)
        
        if batch_id:
            query = query.filter(Order.batch_id == batch_id)
        
        results = query.group_by(
            User.id, User.name, User.username
        ).order_by(
            func.sum(Order.total_amount).desc()
        ).limit(limit).all()
        
        user_analysis = []
        for result in results:
            # คำนวณจำนวนวันที่ใช้งาน
            days_active = (result.last_order_date - result.first_order_date).days + 1
            
            # คำนวณความถี่ในการสั่งซื้อ
            order_frequency = result.total_orders / days_active if days_active > 0 else 0
            
            # จัดประเภทผู้ใช้
            if result.total_spent >= 10000:
                user_type = 'VIP'
            elif result.total_spent >= 5000:
                user_type = 'Premium'
            elif result.total_orders >= 10:
                user_type = 'Regular'
            else:
                user_type = 'New'
            
            user_analysis.append({
                'user_id': result.id,
                'name': result.name,
                'username': result.username,
                'total_orders': result.total_orders,
                'total_spent': float(result.total_spent),
                'avg_order_value': float(result.avg_order_value),
                'max_order_value': float(result.max_order_value),
                'min_order_value': float(result.min_order_value),
                'total_items': result.total_items,
                'avg_items_per_order': result.total_items / result.total_orders,
                'days_active': days_active,
                'order_frequency': round(order_frequency, 2),
                'user_type': user_type,
                'first_order_date': result.first_order_date.isoformat(),
                'last_order_date': result.last_order_date.isoformat()
            })
        
        return user_analysis
    
    def get_hourly_pattern(self, batch_id=None, days=7):
        """วิเคราะห์รูปแบบการสั่งซื้อตามชั่วโมง"""
        
        end_date = get_thai_time().date()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(
            func.extract('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_amount')
        ).filter(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            )
        )
        
        if batch_id:
            query = query.filter(Order.batch_id == batch_id)
        
        results = query.group_by(
            func.extract('hour', Order.created_at)
        ).all()
        
        # สร้างข้อมูลสำหรับทุกชั่วโมง (0-23)
        hourly_data = {}
        for hour in range(24):
            hourly_data[hour] = {
                'hour': hour,
                'order_count': 0,
                'total_amount': 0.0
            }
        
        # เติมข้อมูลจริง
        for result in results:
            hour = int(result.hour)
            hourly_data[hour] = {
                'hour': hour,
                'order_count': result.order_count,
                'total_amount': float(result.total_amount)
            }
        
        # แปลงเป็น list และเรียงตามชั่วโมง
        pattern_data = list(hourly_data.values())
        pattern_data.sort(key=lambda x: x['hour'])
        
        # หาช่วงเวลาที่มีการสั่งซื้อมากที่สุด
        peak_hour = max(pattern_data, key=lambda x: x['order_count'])
        
        return {
            'hourly_pattern': pattern_data,
            'peak_hour': peak_hour['hour'],
            'peak_orders': peak_hour['order_count'],
            'analysis_period_days': days
        }
    
    def get_field_distribution(self, batch_id=None):
        """วิเคราะห์การกระจายตัวของประเภทเลข"""
        
        query = self.db.query(
            OrderItem.field,
            func.count(OrderItem.id).label('item_count'),
            func.sum(OrderItem.buy_amount).label('total_amount'),
            func.count(func.distinct(Order.user_id)).label('unique_users'),
            func.avg(OrderItem.buy_amount).label('avg_amount')
        ).join(Order)
        
        if batch_id:
            query = query.filter(Order.batch_id == batch_id)
        
        results = query.group_by(OrderItem.field).all()
        
        field_names = {
            '2_top': '2 ตัวบน',
            '2_bottom': '2 ตัวล่าง',
            '3_top': '3 ตัวบน',
            'tote': 'โต๊ด'
        }
        
        distribution_data = []
        total_amount = sum(float(result.total_amount) for result in results)
        total_items = sum(result.item_count for result in results)
        
        for result in results:
            amount_percentage = (float(result.total_amount) / total_amount * 100) if total_amount > 0 else 0
            item_percentage = (result.item_count / total_items * 100) if total_items > 0 else 0
            
            distribution_data.append({
                'field': result.field,
                'field_name': field_names.get(result.field, result.field),
                'item_count': result.item_count,
                'total_amount': float(result.total_amount),
                'unique_users': result.unique_users,
                'avg_amount': float(result.avg_amount),
                'amount_percentage': round(amount_percentage, 2),
                'item_percentage': round(item_percentage, 2)
            })
        
        # เรียงตามจำนวนเงิน
        distribution_data.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return {
            'field_distribution': distribution_data,
            'total_amount': total_amount,
            'total_items': total_items
        }
    
    def generate_comprehensive_report(self, batch_id=None, days=30):
        """สร้างรายงานวิเคราะห์ครบถ้วน"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'batch_id': batch_id,
            'analysis_period_days': days,
            'sales_trend': self.get_sales_trend(days, batch_id),
            'number_popularity': self.get_number_popularity(batch_id, limit=20),
            'user_behavior': self.get_user_behavior_analysis(batch_id, limit=10),
            'hourly_pattern': self.get_hourly_pattern(batch_id, days),
            'field_distribution': self.get_field_distribution(batch_id)
        }
        
        return report
```

## สรุป
การ implement P1 Dashboard และ Services นี้จะช่วยให้ระบบมีความสมบูรณ์และใช้งานได้จริงมากขึ้น ผ่านการเพิ่มตัวกรองข้อมูลที่ครบถ้วน การแจ้งเตือนแบบ real-time และการวิเคราะห์ข้อมูลขั้นสูง ระบบเหล่านี้จะช่วยให้ผู้ใช้และผู้ดูแลระบบสามารถจัดการและติดตามข้อมูลได้อย่างมีประสิทธิภาพ

