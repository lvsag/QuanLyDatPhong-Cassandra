import uuid
from datetime import datetime
from cassandra_config import get_session


class CustomerRepository:
    """Quản lý khách hàng - bảng customers + customers_by_email"""

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        # Bảng customers
        self.insert_customer = self.session.prepare("""
            INSERT INTO customers 
            (customer_id, full_name, email, phone, id_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """)
        self.select_by_id = self.session.prepare("""
            SELECT * FROM customers WHERE customer_id = ?
        """)
        self.delete_customer = self.session.prepare("""
            DELETE FROM customers WHERE customer_id = ?
        """)

        # Bảng customers_by_email (dùng cho login)
        self.insert_by_email = self.session.prepare("""
            INSERT INTO customers_by_email 
            (email, customer_id, full_name, phone)
            VALUES (?, ?, ?, ?)
        """)
        self.select_by_email = self.session.prepare("""
            SELECT * FROM customers_by_email WHERE email = ?
        """)

    def create(self, full_name, email, phone, id_number=None):
        """Tạo khách hàng mới. Ghi vào cả 2 bảng (denormalized)."""
        customer_id = uuid.uuid4()
        now = datetime.now()

        # Bảng 1: customers
        self.session.execute(self.insert_customer, (
            customer_id, full_name, email, phone, id_number, now
        ))

        # Bảng 2: customers_by_email (để login)
        self.session.execute(self.insert_by_email, (
            email, customer_id, full_name, phone
        ))

        return customer_id

    def get_by_id(self, customer_id):
        row = self.session.execute(self.select_by_id, (customer_id,)).one()
        return dict(row._asdict()) if row else None

    def get_by_email(self, email):
        """Dùng cho chức năng login."""
        row = self.session.execute(self.select_by_email, (email,)).one()
        return dict(row._asdict()) if row else None

    def delete(self, customer_id):
        """Xóa khách - cần lấy email trước để xóa bảng email."""
        customer = self.get_by_id(customer_id)
        if customer:
            self.session.execute(
                "DELETE FROM customers_by_email WHERE email = %s",
                (customer['email'],)
            )
        self.session.execute(self.delete_customer, (customer_id,))

    def close(self):
        self.cluster.shutdown()


    def get_by_id_safe(self, customer_id):
        """Bọc ép kiểu UUID cho API người 2"""
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        return self.get_by_id(c_id)

    def delete_safe(self, customer_id):
        """Bọc ép kiểu UUID cho API người 2"""
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        self.delete(c_id)

    def update_customer(self, customer_id, full_name, phone, id_number=None):
        """Cập nhật thông tin khách hàng đồng bộ trên cả 2 bảng"""
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        current_data = self.get_by_id(c_id)
        if not current_data:
            return False, "❌ Không tìm thấy khách hàng"

        email = current_data['email']
        created_at = current_data['created_at']

        # Cập nhật bảng customers
        self.session.execute(self.insert_customer, (
            c_id, full_name, email, phone, id_number, created_at
        ))

        # Cập nhật bảng customers_by_email
        self.session.execute(self.insert_by_email, (
            email, c_id, full_name, phone
        ))

        return True, "✅ Cập nhật thông tin khách hàng thành công"