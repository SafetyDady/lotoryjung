/**
 * Improved Frontend JavaScript for LotoJung Order Form
 * ปรับปรุง frontend JavaScript เพื่อใช้กับ validation flow ใหม่
 * 
 * Key Improvements:
 * 1. Simplified API calls
 * 2. Better error handling
 * 3. Optimized validation logic
 * 4. Mobile-friendly interactions
 * 5. Enhanced user feedback
 */

class LotoJungOrderForm {
    constructor() {
        this.orderRows = [];
        this.maxRows = 20;
        this.isValidated = false;
        this.validationResults = [];
        this.blockedNumbers = {};
        this.payoutRates = {};
        
        this.init();
    }
    
    async init() {
        // Load initial data
        await this.loadBlockedNumbers();
        await this.loadPayoutRates();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Add initial row
        this.addOrderRow();
        
        // Update lottery date
        this.updateLotteryDate();
    }
    
    async loadBlockedNumbers() {
        try {
            const response = await fetch('/api/v2/blocked_numbers');
            const data = await response.json();
            
            if (data.success) {
                this.blockedNumbers = data.blocked_numbers;
            }
        } catch (error) {
            console.warn('Failed to load blocked numbers:', error);
            // Use fallback data
            this.blockedNumbers = {
                '2_top': ['00', '11', '22', '33'],
                '2_bottom': ['00', '11', '22', '33'],
                '3_top': ['123', '456', '789'],
                'tote': ['123', '456', '789']
            };
        }
    }
    
    async loadPayoutRates() {
        try {
            const response = await fetch('/api/v2/payout_rates');
            const data = await response.json();
            
            if (data.success) {
                this.payoutRates = data.payout_rates;
                this.updatePayoutRateDisplay();
            }
        } catch (error) {
            console.warn('Failed to load payout rates:', error);
            // Use fallback data
            this.payoutRates = {
                '2_top': 90,
                '2_bottom': 90,
                '3_top': 900,
                'tote': 150
            };
        }
    }
    
    updatePayoutRateDisplay() {
        // Update payout rate display in UI if exists
        const rateElements = {
            '2_top': document.getElementById('rate-2-top'),
            '2_bottom': document.getElementById('rate-2-bottom'),
            '3_top': document.getElementById('rate-3-top'),
            'tote': document.getElementById('rate-tote')
        };
        
        Object.entries(rateElements).forEach(([field, element]) => {
            if (element && this.payoutRates[field]) {
                element.textContent = `${this.payoutRates[field]}x`;
            }
        });
    }
    
    setupEventListeners() {
        // Prevent form submission on Enter
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
                e.preventDefault();
                this.handleEnterKey(e.target);
            }
        });
        
        // Auto-format inputs
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('number-input')) {
                this.formatNumberInput(e.target);
            } else if (e.target.classList.contains('amount-input')) {
                this.formatAmountInput(e.target);
            }
        });
        
        // Real-time validation for number inputs
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('number-input')) {
                this.validateNumberInput(e.target);
            }
        });
    }
    
    handleEnterKey(currentInput) {
        const inputs = Array.from(document.querySelectorAll('input:not([readonly])'));
        const currentIndex = inputs.indexOf(currentInput);
        
        if (currentIndex < inputs.length - 1) {
            inputs[currentIndex + 1].focus();
        } else {
            this.validateOrder();
        }
    }
    
    formatNumberInput(input) {
        // Only allow digits, max 3 characters
        let value = input.value.replace(/[^0-9]/g, '');
        if (value.length > 3) {
            value = value.substring(0, 3);
        }
        input.value = value;
        
        // Update row data
        const rowId = this.getRowIdFromInput(input);
        this.updateRowData(rowId, 'number', value);
    }
    
    formatAmountInput(input) {
        // Only allow digits
        let value = input.value.replace(/[^0-9]/g, '');
        input.value = value;
        
        // Update row data
        const rowId = this.getRowIdFromInput(input);
        const field = this.getFieldFromInput(input);
        this.updateRowData(rowId, field, value);
    }
    
    validateNumberInput(input) {
        const number = input.value.trim();
        const rowId = this.getRowIdFromInput(input);
        const row = this.orderRows.find(r => r.id === rowId);
        
        if (!row || !number) {
            this.updateRowStatus(rowId, 'normal');
            return;
        }
        
        // Check if number is blocked (real-time validation)
        const numberLength = number.length;
        let isBlocked = false;
        
        if (numberLength === 2) {
            isBlocked = this.blockedNumbers['2_top']?.includes(number) || 
                       this.blockedNumbers['2_bottom']?.includes(number);
        } else if (numberLength === 3) {
            isBlocked = this.blockedNumbers['3_top']?.includes(number) || 
                       this.blockedNumbers['tote']?.includes(number);
        }
        
        if (isBlocked) {
            this.updateRowStatus(rowId, 'blocked');
        } else {
            this.updateRowStatus(rowId, 'normal');
        }
    }
    
    getRowIdFromInput(input) {
        const id = input.id;
        return id.substring(0, id.lastIndexOf('_'));
    }
    
    getFieldFromInput(input) {
        const id = input.id;
        const parts = id.split('_');
        return parts.slice(1).join('_'); // Remove row ID part
    }
    
    updateRowData(rowId, field, value) {
        const row = this.orderRows.find(r => r.id === rowId);
        if (row) {
            row[field] = value;
            
            // Reset validation when data changes
            this.isValidated = false;
            this.updateSubmitButton(false);
            this.hideSummary();
        }
    }
    
    updateRowStatus(rowId, status) {
        const statusElement = document.getElementById(`${rowId}_status`);
        if (statusElement) {
            statusElement.className = `status-cell ${this.getStatusClass(status)}`;
            statusElement.textContent = this.getStatusText(status);
        }
        
        // Update row data
        const row = this.orderRows.find(r => r.id === rowId);
        if (row) {
            row.status = status;
        }
    }
    
    getStatusClass(status) {
        const classes = {
            'blocked': 'status-blocked',
            'warning': 'status-warning',
            'normal': 'status-normal'
        };
        return classes[status] || 'status-normal';
    }
    
    getStatusText(status) {
        const texts = {
            'blocked': '🔴 เลขอั้น',
            'warning': '⚠️ เตือน',
            'normal': '✅ ปกติ'
        };
        return texts[status] || '✅ ปกติ';
    }
    
    addOrderRow() {
        if (this.orderRows.length >= this.maxRows) {
            this.showAlert(`ไม่สามารถเพิ่มรายการได้ เกินจำนวนสูงสุด ${this.maxRows} รายการ`, 'warning');
            return;
        }
        
        const rowId = 'row_' + Date.now();
        const row = {
            id: rowId,
            number: '',
            amount_top: '',
            amount_bottom: '',
            amount_tote: '',
            status: 'normal'
        };
        
        this.orderRows.push(row);
        this.renderOrderTable();
        
        // Focus on the number input of the new row
        setTimeout(() => {
            const numberInput = document.querySelector(`#${rowId}_number`);
            if (numberInput) numberInput.focus();
        }, 100);
    }
    
    removeOrderRow(rowId) {
        this.orderRows = this.orderRows.filter(row => row.id !== rowId);
        this.renderOrderTable();
        
        // Add a new row if all rows are deleted
        if (this.orderRows.length === 0) {
            this.addOrderRow();
        }
        
        // Reset validation state
        this.isValidated = false;
        this.updateSubmitButton(false);
        this.hideSummary();
    }
    
    renderOrderTable() {
        const tbody = document.getElementById('orderTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        this.orderRows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <input type="text" 
                           class="number-input" 
                           id="${row.id}_number"
                           value="${row.number}"
                           placeholder="12"
                           inputmode="numeric"
                           pattern="[0-9]*"
                           maxlength="3">
                </td>
                <td>
                    <input type="text" 
                           class="amount-input" 
                           id="${row.id}_amount_top"
                           value="${row.amount_top}"
                           placeholder="100"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </td>
                <td>
                    <input type="text" 
                           class="amount-input" 
                           id="${row.id}_amount_bottom"
                           value="${row.amount_bottom}"
                           placeholder="200"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </td>
                <td>
                    <input type="text" 
                           class="amount-input" 
                           id="${row.id}_amount_tote"
                           value="${row.amount_tote}"
                           placeholder="150"
                           inputmode="numeric"
                           pattern="[0-9]*">
                </td>
                <td>
                    <span class="status-cell ${this.getStatusClass(row.status)}" id="${row.id}_status">
                        ${this.getStatusText(row.status)}
                    </span>
                </td>
                <td>
                    <button class="delete-btn" onclick="orderForm.removeOrderRow('${row.id}')" title="ลบรายการ">
                        ✕
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    async validateAndSubmitOrder() {
        
        const submitBtn = document.querySelector('.btn-submit');
        const spinner = document.getElementById('submitSpinner');
        
        if (!submitBtn || !spinner) return;
        
        // Show loading
        submitBtn.disabled = true;
        spinner.classList.remove('hidden');
        
        try {
            // Prepare order data
            const customerName = document.getElementById('customerName')?.value || '';
            const items = this.orderRows.map(row => ({
                number: row.number,
                amount_top: row.amount_top || '0',
                amount_bottom: row.amount_bottom || '0',
                amount_tote: row.amount_tote || '0'
            }));
            
            // Submit order
            const response = await fetch('/api/v2/submit_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    items: items
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.handleOrderSuccess(data);
            } else {
                this.showAlert(data.error || 'เกิดข้อผิดพลาดในการสั่งซื้อ', 'error');
            }
            
        } catch (error) {
            console.error('Submit error:', error);
            this.showAlert('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
        } finally {
            // Hide loading
            submitBtn.disabled = false;
            spinner.classList.add('hidden');
        }
    }
    
    handleValidationSuccess(data) {
        this.validationResults = data.validation_results;
        const summary = data.summary;
        
        // Update row statuses based on validation results
        this.validationResults.forEach((result, index) => {
            if (index < this.orderRows.length) {
                const row = this.orderRows[index];
                let status = 'normal';
                
                if (result.status === 'blocked' || result.has_blocked) {
                    status = 'blocked';
                } else if (result.status === 'warning' || result.has_warning) {
                    status = 'warning';
                }
                
                this.updateRowStatus(row.id, status);
            }
        });
        
        // Check if there are valid items
        if (summary.valid_items > 0 || summary.warning_items > 0 || summary.blocked_items > 0) {
            this.showAlert('ตรวจสอบเรียบร้อย พร้อมสั่งซื้อ', 'success');
            this.isValidated = true;
            this.updateSubmitButton(true);
            this.showSummary(summary);
        } else {
            this.showAlert('กรุณากรอกข้อมูลอย่างน้อย 1 รายการ', 'warning');
        }
    }
    
    async validateAndSubmitOrder() {
        
        
        const submitBtn = document.querySelector('.btn-submit');
        const spinner = document.getElementById('submitSpinner');
        
        if (!submitBtn || !spinner) return;
        
        // Show loading
        submitBtn.disabled = true;
        spinner.classList.remove('hidden');
        
        try {
            // Prepare order data
            const customerName = document.getElementById('customerName')?.value || '';
            const items = this.orderRows.map(row => ({
                number: row.number,
                amount_top: row.amount_top || '0',
                amount_bottom: row.amount_bottom || '0',
                amount_tote: row.amount_tote || '0'
            }));
            
            // Submit order
            const response = await fetch('/api/v2/submit_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    items: items
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.handleOrderSuccess(data);
            } else {
                this.showAlert(data.error || 'เกิดข้อผิดพลาดในการสั่งซื้อ', 'error');
            }
            
        } catch (error) {
            console.error('Submit error:', error);
            this.showAlert('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
        } finally {
            // Hide loading
            submitBtn.disabled = false;
            spinner.classList.add('hidden');
        }
    }
    
    handleOrderSuccess(data) {
        let message = `✅ สั่งซื้อสำเร็จ!\n`;
        message += `หมายเลขคำสั่งซื้อ: ${data.order_id}\n`;
        message += `ยอดรวม: ${data.total_amount.toLocaleString()} บาท\n`;
        
        const limitProcessing = data.limit_processing;
        if (limitProcessing.has_adjustments) {
            message += `\n⚠️ มีการปรับยอดเนื่องจาก Limit:\n`;
            limitProcessing.adjustments.forEach(adj => {
                message += `เลข ${adj.number}: ซื้อได้ ${adj.adjusted_amount} บาท (คืน ${adj.total_refund} บาท)\n`;
            });
            message += `\nเงินคืนจะแสดงในใบเสร็จ`;
        }
        
        alert(message);
        
        // Reset form
        this.resetForm();
    }
    
    resetForm() {
        this.orderRows = [];
        this.addOrderRow();
        
        const customerNameInput = document.getElementById('customerName');
        if (customerNameInput) {
            customerNameInput.value = '';
        }
        
        this.isValidated = false;
        this.updateSubmitButton(false);
        this.hideSummary();
        this.clearAlert();
    }
    
    showSummary(summary) {
        const summarySection = document.getElementById('summarySection');
        const summaryContent = document.getElementById('summaryContent');
        
        if (!summarySection || !summaryContent) return;
        
        summaryContent.innerHTML = `
            <div class="summary-item">
                <span>จำนวนรายการ:</span>
                <span>${summary.total_items} รายการ</span>
            </div>
            <div class="summary-item">
                <span>รายการถูกต้อง:</span>
                <span>${summary.valid_items} รายการ</span>
            </div>
            ${summary.blocked_items > 0 ? `
            <div class="summary-item">
                <span>เลขอั้น:</span>
                <span>${summary.blocked_items} รายการ</span>
            </div>
            ` : ''}
            ${summary.warning_items > 0 ? `
            <div class="summary-item">
                <span>มีเตือน:</span>
                <span>${summary.warning_items} รายการ</span>
            </div>
            ` : ''}
            <div class="summary-item">
                <span>ยอดรวม:</span>
                <span>${summary.total_amount.toLocaleString()} บาท</span>
            </div>
        `;
        
        summarySection.style.display = 'block';
    }
    
    hideSummary() {
        const summarySection = document.getElementById('summarySection');
        if (summarySection) {
            summarySection.style.display = 'none';
        }
    }
    
    updateSubmitButton(enabled) {
        const submitBtn = document.querySelector('.btn-submit');
        if (submitBtn) {
            submitBtn.disabled = !enabled;
        }
    }
    
    showAlert(message, type) {
        const alertArea = document.getElementById('alertArea');
        if (!alertArea) return;
        
        alertArea.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            this.clearAlert();
        }, 5000);
    }
    
    clearAlert() {
        const alertArea = document.getElementById('alertArea');
        if (alertArea) {
            alertArea.innerHTML = '';
        }
    }
    
    updateLotteryDate() {
        const dateElement = document.getElementById('lotteryDate');
        if (dateElement) {
            const today = new Date();
            const options = { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric'
            };
            dateElement.textContent = today.toLocaleDateString('th-TH', options);
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        return token || '';
    }
    
    clearAll() {
        this.orderRows = [];
        this.renderOrderTable();
        this.addOrderRow(); // Add one empty row
        this.isValidated = false;
        this.updateSubmitButton(false);
        this.hideSummary();
        
        // Clear customer name
        const customerName = document.getElementById('customerName');
        if (customerName) customerName.value = '';
        
        this.showAlert('ล้างข้อมูลทั้งหมดแล้ว', 'info');
    }
    
    fillSampleData() {
        this.clearAll();
        
        // Add sample data
        const sampleData = [
            { number: '12', amount_top: '100', amount_bottom: '200', amount_tote: '' },
            { number: '123', amount_top: '300', amount_bottom: '', amount_tote: '150' },
            { number: '00', amount_top: '50', amount_bottom: '100', amount_tote: '' }
        ];
        
        sampleData.forEach((data, index) => {
            if (index > 0) this.addOrderRow();
            const row = this.orderRows[index];
            if (row) {
                row.number = data.number;
                row.amount_top = data.amount_top;
                row.amount_bottom = data.amount_bottom;
                row.amount_tote = data.amount_tote;
            }
        });
        
        this.renderOrderTable();
        
        // Set customer name
        const customerName = document.getElementById('customerName');
        if (customerName) customerName.value = 'ลูกค้าตัวอย่าง';
        
        this.showAlert('กรอกข้อมูลตัวอย่างแล้ว', 'info');
    }
    
    showAlert(message, type = 'info') {
        const alertTypes = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };
        
        const alertClass = alertTypes[type] || 'alert-info';
        
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.order-form-container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    hideSummary() {
        const summaryPanel = document.getElementById('summaryPanel');
        if (summaryPanel) {
            summaryPanel.style.display = 'none';
        }
    }
    
    showSummary(summary) {
        const summaryPanel = document.getElementById('summaryPanel');
        const summaryContent = document.getElementById('summaryContent');
        
        if (summaryPanel && summaryContent) {
            summaryContent.innerHTML = `
                <div class="row">
                    <div class="col-md-3 col-6 text-center">
                        <div class="border rounded p-2 mb-2">
                            <small class="text-muted">รายการทั้งหมด</small><br>
                            <strong class="text-primary">${summary.total_items}</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6 text-center">
                        <div class="border rounded p-2 mb-2">
                            <small class="text-muted">รายการปกติ</small><br>
                            <strong class="text-success">${summary.valid_items}</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6 text-center">
                        <div class="border rounded p-2 mb-2">
                            <small class="text-muted">รายการเตือน</small><br>
                            <strong class="text-warning">${summary.warning_items}</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6 text-center">
                        <div class="border rounded p-2 mb-2">
                            <small class="text-muted">รายการอั้น</small><br>
                            <strong class="text-danger">${summary.blocked_items}</strong>
                        </div>
                    </div>
                </div>
                <hr>
                <div class="text-center">
                    <h5>ยอดรวม: <span class="text-success">${summary.total_amount.toLocaleString()} บาท</span></h5>
                </div>
            `;
            summaryPanel.style.display = 'block';
        }
    }
    
    updateSubmitButton(enabled) {
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = !enabled;
            if (enabled) {
                submitBtn.classList.remove('btn-secondary');
                submitBtn.classList.add('btn-success');
            } else {
                submitBtn.classList.remove('btn-success');
                submitBtn.classList.add('btn-secondary');
            }
        }
    }
    
    updateLotteryDate() {
        // This function can be used to update lottery date display
        // Implementation depends on your date format requirements
    }
}

