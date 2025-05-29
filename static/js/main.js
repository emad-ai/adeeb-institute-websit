// نظام إدارة الطلاب - الوظائف الرئيسية
(function() {
    'use strict';

    // تهيئة التطبيق عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
    });

    // تهيئة التطبيق
    function initializeApp() {
        initializeTooltips();
        initializeModals();
        initializeFormValidation();
        initializeDataTables();
        initializeCharts();
        initializeFileUpload();
        initializeNotifications();
        initializeDatePickers();
        initializeSearchAndFilter();
        initializeConfirmDialogs();
    }

    // تهيئة التلميحات
    function initializeTooltips() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // تهيئة النوافذ المنبثقة
    function initializeModals() {
        // إغلاق النوافذ المنبثقة عند النقر خارجها
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal')) {
                var modal = bootstrap.Modal.getInstance(e.target);
                if (modal) {
                    modal.hide();
                }
            }
        });
    }

    // تحقق من صحة النماذج
    function initializeFormValidation() {
        var forms = document.querySelectorAll('.needs-validation');
        
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });

        // التحقق من كلمات المرور المطابقة
        var passwordFields = document.querySelectorAll('input[type="password"]');
        passwordFields.forEach(function(field) {
            if (field.name.includes('confirm') || field.name.includes('password2')) {
                field.addEventListener('input', validatePasswordMatch);
            }
        });
    }

    // التحقق من تطابق كلمات المرور
    function validatePasswordMatch() {
        var password = document.querySelector('input[name="password"]') || 
                      document.querySelector('input[name="new_password"]');
        var confirmPassword = this;
        
        if (password && confirmPassword.value !== password.value) {
            confirmPassword.setCustomValidity('كلمات المرور غير متطابقة');
        } else {
            confirmPassword.setCustomValidity('');
        }
    }

    // تهيئة الجداول التفاعلية
    function initializeDataTables() {
        var tables = document.querySelectorAll('.data-table');
        tables.forEach(function(table) {
            // إضافة وظائف البحث والفرز للجداول
            if (table.querySelector('thead')) {
                addTableSearch(table);
                addTableSort(table);
            }
        });
    }

    // إضافة البحث للجداول
    function addTableSearch(table) {
        var searchInput = table.parentElement.querySelector('.table-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                var searchTerm = this.value.toLowerCase();
                var rows = table.querySelector('tbody').querySelectorAll('tr');
                
                rows.forEach(function(row) {
                    var text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    }

    // إضافة الفرز للجداول
    function addTableSort(table) {
        var headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, this.dataset.sort);
            });
        });
    }

    // فرز الجدول
    function sortTable(table, column) {
        var tbody = table.querySelector('tbody');
        var rows = Array.from(tbody.querySelectorAll('tr'));
        var isAscending = table.dataset.sortOrder !== 'asc';
        
        rows.sort(function(a, b) {
            var aVal = a.querySelector('[data-sort="' + column + '"]').textContent.trim();
            var bVal = b.querySelector('[data-sort="' + column + '"]').textContent.trim();
            
            // تحويل للأرقام إذا كانت رقمية
            if (!isNaN(aVal) && !isNaN(bVal)) {
                aVal = parseFloat(aVal);
                bVal = parseFloat(bVal);
            }
            
            if (isAscending) {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        // إعادة ترتيب الصفوف
        rows.forEach(function(row) {
            tbody.appendChild(row);
        });
        
        table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    }

    // تهيئة المخططات
    function initializeCharts() {
        // مخطط الإحصائيات الشهرية
        var monthlyChart = document.getElementById('monthlyChart');
        if (monthlyChart && typeof Chart !== 'undefined') {
            createMonthlyChart(monthlyChart);
        }

        // مخطط الحضور
        var attendanceChart = document.getElementById('attendanceChart');
        if (attendanceChart && typeof Chart !== 'undefined') {
            createAttendanceChart(attendanceChart);
        }

        // مخطط الدرجات
        var gradesChart = document.getElementById('gradesChart');
        if (gradesChart && typeof Chart !== 'undefined') {
            createGradesChart(gradesChart);
        }
    }

    // إنشاء مخطط الإحصائيات الشهرية
    function createMonthlyChart(canvas) {
        var ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                datasets: [{
                    label: 'التسجيلات الجديدة',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // إنشاء مخطط الحضور
    function createAttendanceChart(canvas) {
        var ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['حاضر', 'غائب', 'متأخر', 'معذور'],
                datasets: [{
                    data: [65, 20, 10, 5],
                    backgroundColor: [
                        '#28a745',
                        '#dc3545',
                        '#ffc107',
                        '#17a2b8'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }

    // إنشاء مخطط الدرجات
    function createGradesChart(canvas) {
        var ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['ممتاز', 'جيد جداً', 'جيد', 'مقبول', 'ضعيف'],
                datasets: [{
                    label: 'عدد الطلاب',
                    data: [25, 35, 20, 15, 5],
                    backgroundColor: [
                        '#28a745',
                        '#17a2b8',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // تهيئة رفع الملفات
    function initializeFileUpload() {
        var fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function(input) {
            input.addEventListener('change', function(e) {
                var file = e.target.files[0];
                if (file) {
                    validateFile(file, input);
                    previewFile(file, input);
                }
            });
        });
    }

    // التحقق من صحة الملف
    function validateFile(file, input) {
        var maxSize = 5 * 1024 * 1024; // 5MB
        var allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
        
        if (file.size > maxSize) {
            showAlert('حجم الملف كبير جداً. الحد الأقصى 5 ميجابايت', 'danger');
            input.value = '';
            return false;
        }
        
        if (input.accept && !allowedTypes.includes(file.type)) {
            showAlert('نوع الملف غير مدعوم', 'danger');
            input.value = '';
            return false;
        }
        
        return true;
    }

    // معاينة الملف
    function previewFile(file, input) {
        if (file.type.startsWith('image/')) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var preview = input.parentElement.querySelector('.file-preview');
                if (!preview) {
                    preview = document.createElement('div');
                    preview.className = 'file-preview mt-2';
                    input.parentElement.appendChild(preview);
                }
                preview.innerHTML = '<img src="' + e.target.result + '" class="img-thumbnail" style="max-width: 150px; max-height: 150px;">';
            };
            reader.readAsDataURL(file);
        }
    }

    // تهيئة الإشعارات
    function initializeNotifications() {
        // إخفاء الإشعارات تلقائياً بعد 5 ثوان
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, 5000);
        });

        // زر إغلاق الإشعارات
        var closeButtons = document.querySelectorAll('.alert .btn-close');
        closeButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                var alert = this.closest('.alert');
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            });
        });
    }

    // تهيئة منتقي التواريخ
    function initializeDatePickers() {
        var dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(function(input) {
            // تعيين التاريخ الحالي كحد أقصى للتواريخ الماضية
            if (input.name.includes('birth') || input.name.includes('date_of_birth')) {
                var today = new Date();
                var maxDate = new Date(today.getFullYear() - 10, today.getMonth(), today.getDate());
                input.max = maxDate.toISOString().split('T')[0];
            }
        });
    }

    // تهيئة البحث والفلترة
    function initializeSearchAndFilter() {
        // البحث السريع
        var searchInputs = document.querySelectorAll('.quick-search');
        searchInputs.forEach(function(input) {
            var debounceTimer;
            input.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function() {
                    performQuickSearch(input.value, input.dataset.target);
                }, 300);
            });
        });

        // فلاتر الصفحة
        var filterSelects = document.querySelectorAll('.page-filter');
        filterSelects.forEach(function(select) {
            select.addEventListener('change', function() {
                applyPageFilter(this.value, this.dataset.filter);
            });
        });
    }

    // تنفيذ البحث السريع
    function performQuickSearch(query, target) {
        var elements = document.querySelectorAll(target || '.searchable');
        elements.forEach(function(element) {
            var text = element.textContent.toLowerCase();
            var match = text.includes(query.toLowerCase());
            element.style.display = match ? '' : 'none';
        });
    }

    // تطبيق الفلاتر
    function applyPageFilter(value, filterType) {
        var elements = document.querySelectorAll('[data-filter-' + filterType + ']');
        elements.forEach(function(element) {
            var elementValue = element.dataset['filter' + filterType.charAt(0).toUpperCase() + filterType.slice(1)];
            var match = !value || elementValue === value;
            element.style.display = match ? '' : 'none';
        });
    }

    // تهيئة حوارات التأكيد
    function initializeConfirmDialogs() {
        var confirmButtons = document.querySelectorAll('[data-confirm]');
        confirmButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                var message = this.dataset.confirm || 'هل أنت متأكد من هذا الإجراء؟';
                if (!confirm(message)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }

    // وظائف مساعدة عامة
    window.StudentManagement = {
        // عرض رسالة تنبيه
        showAlert: function(message, type) {
            showAlert(message, type);
        },

        // تحديث الصفحة
        refreshPage: function() {
            window.location.reload();
        },

        // تأكيد الحذف
        confirmDelete: function(itemName) {
            return confirm('هل أنت متأكد من حذف "' + itemName + '"؟ لا يمكن التراجع عن هذا الإجراء.');
        },

        // طباعة الصفحة
        printPage: function() {
            window.print();
        },

        // تصدير البيانات
        exportData: function(format, url) {
            window.open(url + '?format=' + format, '_blank');
        }
    };

    // عرض رسالة تنبيه
    function showAlert(message, type) {
        var alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-' + (type || 'info') + ' alert-dismissible fade show position-fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // إزالة التنبيه بعد 5 ثوان
        setTimeout(function() {
            alertDiv.remove();
        }, 5000);
    }

    // وظائف خاصة بالحضور
    window.AttendanceManager = {
        // تحديث حالة الحضور
        updateAttendance: function(sessionId, studentId, status) {
            var formData = new FormData();
            formData.append('session_id', sessionId);
            formData.append('attendance_' + studentId, status);
            
            fetch('/teacher/attendance/update', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('تم تحديث الحضور بنجاح', 'success');
                } else {
                    showAlert('حدث خطأ في تحديث الحضور', 'danger');
                }
            })
            .catch(error => {
                showAlert('حدث خطأ في الاتصال', 'danger');
            });
        },

        // تحديد الكل كحاضر
        markAllPresent: function(sessionId) {
            var checkboxes = document.querySelectorAll('input[name^="attendance_"][value="present"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = true;
            });
            showAlert('تم تحديد جميع الطلاب كحاضرين', 'info');
        },

        // تحديد الكل كغائب
        markAllAbsent: function(sessionId) {
            var checkboxes = document.querySelectorAll('input[name^="attendance_"][value="absent"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = true;
            });
            showAlert('تم تحديد جميع الطلاب كغائبين', 'info');
        }
    };

    // وظائف خاصة بالدرجات
    window.GradesManager = {
        // حساب المتوسط
        calculateAverage: function(grades) {
            if (!grades || grades.length === 0) return 0;
            var sum = grades.reduce(function(a, b) { return a + b; }, 0);
            return Math.round((sum / grades.length) * 100) / 100;
        },

        // تحديد نوع التقدير
        getGradeLevel: function(percentage) {
            if (percentage >= 90) return 'ممتاز';
            if (percentage >= 80) return 'جيد جداً';
            if (percentage >= 70) return 'جيد';
            if (percentage >= 60) return 'مقبول';
            return 'ضعيف';
        },

        // تلوين الدرجات
        colorizeGrade: function(element, percentage) {
            element.classList.remove('grade-excellent', 'grade-good', 'grade-average', 'grade-poor');
            
            if (percentage >= 90) {
                element.classList.add('grade-excellent');
            } else if (percentage >= 80) {
                element.classList.add('grade-good');
            } else if (percentage >= 60) {
                element.classList.add('grade-average');
            } else {
                element.classList.add('grade-poor');
            }
        }
    };

    // تهيئة وظائف خاصة بكل صفحة
    var currentPage = document.body.dataset.page;
    if (currentPage) {
        switch (currentPage) {
            case 'dashboard':
                initializeDashboard();
                break;
            case 'students':
                initializeStudentsPage();
                break;
            case 'courses':
                initializeCoursesPage();
                break;
            case 'attendance':
                initializeAttendancePage();
                break;
            case 'grades':
                initializeGradesPage();
                break;
        }
    }

    // تهيئة لوحة التحكم
    function initializeDashboard() {
        // تحديث الإحصائيات كل 5 دقائق
        setInterval(function() {
            updateDashboardStats();
        }, 300000); // 5 دقائق
    }

    // تحديث إحصائيات لوحة التحكم
    function updateDashboardStats() {
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                updateStatsCards(data);
            })
            .catch(error => {
                console.log('خطأ في تحديث الإحصائيات:', error);
            });
    }

    // تحديث بطاقات الإحصائيات
    function updateStatsCards(data) {
        Object.keys(data).forEach(function(key) {
            var element = document.querySelector('[data-stat="' + key + '"]');
            if (element) {
                element.textContent = data[key];
                element.classList.add('fade-in');
            }
        });
    }

    // تهيئة صفحة الطلاب
    function initializeStudentsPage() {
        // تصدير قائمة الطلاب
        var exportBtn = document.getElementById('exportStudents');
        if (exportBtn) {
            exportBtn.addEventListener('click', function() {
                window.open('/admin/export/students', '_blank');
            });
        }
    }

    // تهيئة صفحة الدورات
    function initializeCoursesPage() {
        // تصدير قائمة الدورات
        var exportBtn = document.getElementById('exportCourses');
        if (exportBtn) {
            exportBtn.addEventListener('click', function() {
                window.open('/admin/export/courses', '_blank');
            });
        }
    }

    // تهيئة صفحة الحضور
    function initializeAttendancePage() {
        // تحديد الكل كحاضر/غائب
        var markAllPresentBtn = document.getElementById('markAllPresent');
        var markAllAbsentBtn = document.getElementById('markAllAbsent');
        
        if (markAllPresentBtn) {
            markAllPresentBtn.addEventListener('click', function() {
                AttendanceManager.markAllPresent();
            });
        }
        
        if (markAllAbsentBtn) {
            markAllAbsentBtn.addEventListener('click', function() {
                AttendanceManager.markAllAbsent();
            });
        }
    }

    // تهيئة صفحة الدرجات
    function initializeGradesPage() {
        // تلوين الدرجات تلقائياً
        var gradeElements = document.querySelectorAll('.grade-value');
        gradeElements.forEach(function(element) {
            var percentage = parseFloat(element.textContent);
            if (!isNaN(percentage)) {
                GradesManager.colorizeGrade(element, percentage);
            }
        });
    }

})();
