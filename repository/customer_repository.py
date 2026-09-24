import uuid
from datetime import datetime
from cassandra_config import get_session
from werkzeug.security import check_password_hash, generate_password_hash


class CustomerRepository:
    """Quản lý khách hàng - bảng customers + customers_by_email (LWT email uniqueness)"""

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        self.insert_customer = self.session.prepare("""
            INSERT INTO customers 
            (customer_id, full_name, email, phone, id_number, created_at, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        self.select_by_id = self.session.prepare("""
            SELECT * FROM customers WHERE customer_id = ?
        """)
        self.delete_customer = self.session.prepare("""
            DELETE FROM customers WHERE customer_id = ?
        """)

        # Bảng customers_by_email sử dụng LWT IF NOT EXISTS để bảo đảm duy nhất email
        self.insert_by_email_lwt = self.session.prepare("""
            INSERT INTO customers_by_email 
            (email, customer_id, full_name, phone, password_hash)
            VALUES (?, ?, ?, ?, ?)
            IF NOT EXISTS
        """)
        self.update_by_email = self.session.prepare("""
            INSERT INTO customers_by_email 
            (email, customer_id, full_name, phone, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """)
        self.select_by_email = self.session.prepare("""
            SELECT * FROM customers_by_email WHERE email = ?
        """)

    def create(self, full_name, email, phone, id_number=None, password=None):
        """
        Tạo khách hàng mới với LWT email uniqueness.
        Trả về customer_id nếu thành công, raise ValueError nếu email đã tồn tại.
        """
        norm_email = email.strip().lower() if email else ""
        customer_id = uuid.uuid4()
        now = datetime.now()
        password_hash = generate_password_hash(password) if password else None

        # Bước 1: Thử LWT insert vào customers_by_email
        res = self.session.execute(self.insert_by_email_lwt, (
            norm_email, customer_id, full_name, phone, password_hash
        ))
        row = res.one()
        if row is not None and not row.applied:
            raise ValueError(f"Email '{norm_email}' đã được sử dụng trong hệ thống.")

        # Bước 2: Thêm thông tin chi tiết vào bảng customers
        self.session.execute(self.insert_customer, (
            customer_id, full_name, norm_email, phone, id_number, now, password_hash
        ))

        return customer_id

    def get_by_id(self, customer_id):
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        row = self.session.execute(self.select_by_id, (c_id,)).one()
        return dict(row._asdict()) if row else None

    def get_by_email(self, email):
        """Dùng cho chức năng login & tra cứu."""
        if not email:
            return None
        norm_email = email.strip().lower()
        row = self.session.execute(self.select_by_email, (norm_email,)).one()
        return dict(row._asdict()) if row else None

    def verify_login(self, email, password):
        customer = self.get_by_email(email)
        if not customer:
            return None
        stored_hash = customer.get("password_hash")
        valid = check_password_hash(stored_hash, password) if stored_hash else password == customer.get("phone")
        return customer if valid else None

    def delete(self, customer_id):
        customer = self.get_by_id(customer_id)
        if customer and customer.get("email"):
            self.session.execute(
                "DELETE FROM customers_by_email WHERE email = %s",
                (customer['email'],)
            )
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        self.session.execute(self.delete_customer, (c_id,))

    def close(self):
        pass

    def get_by_id_safe(self, customer_id):
        return self.get_by_id(customer_id)

    def delete_safe(self, customer_id):
        self.delete(customer_id)

    def update_customer(self, customer_id, full_name, phone, id_number=None):
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        current_data = self.get_by_id(c_id)
        if not current_data:
            return False, "❌ Không tìm thấy khách hàng"

        email = current_data['email']
        created_at = current_data['created_at']

        self.session.execute(self.insert_customer, (
            c_id, full_name, email, phone, id_number, created_at, current_data.get("password_hash")
        ))
        self.session.execute(self.update_by_email, (
            email, c_id, full_name, phone, current_data.get("password_hash")
        ))

        return True, "✅ Cập nhật thông tin khách hàng thành công"