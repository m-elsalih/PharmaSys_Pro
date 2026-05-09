from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from models.sales_dao import SalesDAO


class POSPage(QWidget):
    def __init__(self):
        super().__init__()
        self.dao = SalesDAO()
        self.cart = []  # قائمة لتخزين الأدوية المضافة للفاتورة الحالية
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()  # تقسيم الشاشة لعمودين (يمين ويسار)

        # --- القسم الأيمن: الفاتورة والبحث ---
        right_panel = QVBoxLayout()

        # 1. حقل البحث (الباركود)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ادخل اسم الدواء أو امسح الباركود واضغط Enter...")
        self.search_input.setStyleSheet(
            "padding: 15px; font-size: 16px; border: 2px solid #3498DB; border-radius: 10px;")
        self.search_input.returnPressed.connect(self.add_to_cart)  # عند ضغط Enter
        right_panel.addWidget(self.search_input)

        # 2. جدول الفاتورة (السلة)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "اسم الدواء", "سعر الوحدة", "الكمية", "الإجمالي"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setLayoutDirection(Qt.RightToLeft)
        right_panel.addWidget(self.table)

        # 3. أزرار التحكم بالسلة
        actions_layout = QHBoxLayout()
        self.btn_remove = QPushButton("❌ حذف صنف")
        self.btn_remove.clicked.connect(self.remove_item)
        self.btn_remove.setStyleSheet("background-color: #E74C3C; color: white; padding: 10px;")

        self.btn_clear = QPushButton("🗑️ تفريغ السلة")
        self.btn_clear.clicked.connect(self.clear_cart)

        actions_layout.addWidget(self.btn_remove)
        actions_layout.addWidget(self.btn_clear)
        right_panel.addLayout(actions_layout)

        layout.addLayout(right_panel, stretch=2)  # يأخذ مساحة أكبر

        # --- القسم الأيسر: الحساب والدفع ---
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #2C3E50; border-radius: 15px; color: white;")
        left_layout = QVBoxLayout(left_panel)

        title = QLabel("إجمالي الفاتورة")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        left_layout.addWidget(title)

        self.total_label = QLabel("0.00")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("font-size: 40px; color: #2ECC71; font-weight: bold;")
        left_layout.addWidget(self.total_label)

        left_layout.addStretch()

        self.btn_checkout = QPushButton("💰 إتمام البيع (دفع)")
        self.btn_checkout.setCursor(Qt.PointingHandCursor)
        self.btn_checkout.clicked.connect(self.checkout)
        self.btn_checkout.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-size: 20px;
                padding: 20px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #219150; }
        """)
        left_layout.addWidget(self.btn_checkout)

        layout.addWidget(left_panel, stretch=1)

        self.setLayout(layout)

    def add_to_cart(self):
        text = self.search_input.text().strip()
        if not text:
            return

        medicine = self.dao.get_medicine_by_barcode_or_name(text)

        if medicine:
            med_id, name, price, stock, barcode = medicine

            # التحقق هل الدواء موجود مسبقاً في السلة؟
            for item in self.cart:
                if item['id'] == med_id:
                    if item['qty'] < stock:
                        item['qty'] += 1
                        self.update_table()
                        self.search_input.clear()
                    else:
                        QMessageBox.warning(self, "تنبيه", "الكمية المطلوبة غير متوفرة في المخزون!")
                    return

            # إذا لم يكن موجوداً، أضفه كعنصر جديد
            self.cart.append({
                'id': med_id,
                'name': name,
                'price': price,
                'qty': 1,
                'total': price
            })
            self.update_table()
            self.search_input.clear()
        else:
            QMessageBox.warning(self, "خطأ", "دواء غير موجود أو الكمية نفدت!")

    def update_table(self):
        """تحديث عرض الجدول وحساب المجموع"""
        self.table.setRowCount(0)
        total_bill = 0

        for row, item in enumerate(self.cart):
            self.table.insertRow(row)
            item['total'] = item['qty'] * item['price']
            total_bill += item['total']

            self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.table.setItem(row, 2, QTableWidgetItem(str(item['price'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item['qty'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(item['total'])))

        self.total_label.setText(f"{total_bill:,.2f}")

    def remove_item(self):
        row = self.table.currentRow()
        if row >= 0:
            del self.cart[row]
            self.update_table()

    def clear_cart(self):
        self.cart = []
        self.update_table()

    def checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة!")
            return

        total_amount = float(self.total_label.text().replace(',', ''))

        # ملاحظة: هنا نفترض أن user_id = 1 (المدير) مؤقتاً
        # في النسخة النهائية يمكننا تمرير معرف المستخدم عند تسجيل الدخول
        success, msg = self.dao.process_sale(1, self.cart, total_amount)

        if success:
            QMessageBox.information(self, "نجاح", msg)
            self.clear_cart()
        else:
            QMessageBox.critical(self, "فشل", msg)