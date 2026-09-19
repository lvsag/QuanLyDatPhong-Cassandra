import uuid
from datetime import datetime, timezone
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

        # Bảng customers_by_email (dùng cho login và là ràng buộc UNIQUE của email)
        # IF NOT EXISTS: email đã có người dùng thì không ghi đè
        self.insert_by_email = self.session.prepare("""
            INSERT INTO customers_by_email 
            (email, customer_id, full_name, phone)
            VALUES (?, ?, ?, ?)
            IF NOT EXISTS
        """)
        self.select_by_email = self.session.prepare("""
            SELECT * FROM customers_by_email WHERE email = ?
        """)
        # Chỉ xóa nếu dòng email đó thuộc về đúng customer_id này
        self.delete_by_email = self.session.prepare("""
            DELETE FROM customers_by_email WHERE email = ? IF customer_id = ?
        """)

    @staticmethod
    def _normalize_email(email):
        return email.strip().lower()

    def create(self, full_name, email, phone, id_number=None):
        """
        Tạo khách hàng mới. Ghi vào cả 2 bảng (denormalized).
        Raise ValueError nếu email đã được đăng ký.
        """
        email = self._normalize_email(email)
        customer_id = uuid.uuid4()

        # Bước 1: giữ chỗ email bằng LWT. Email là khóa duy nhất nên phải làm trước
        row = self.session.execute(self.insert_by_email, (
            email, customer_id, full_name, phone
        )).one()
        if not row.applied:
            raise ValueError(f"Email {email} đã được đăng ký")

        # Bước 2: ghi bảng customers. Nếu lỗi thì nhả lại email để khỏi bị kẹt
        try:
            self.session.execute(self.insert_customer, (
                customer_id, full_name, email, phone, id_number,
                datetime.now(timezone.utc)
            ))
        except Exception:
            self.session.execute(self.delete_by_email, (email, customer_id))
            raise

        return customer_id

    def get_by_id(self, customer_id):
        row = self.session.execute(self.select_by_id, (customer_id,)).one()
        return dict(row._asdict()) if row else None

    def get_by_email(self, email):
        """Dùng cho chức năng login."""
        row = self.session.execute(
            self.select_by_email, (self._normalize_email(email),)
        ).one()
        return dict(row._asdict()) if row else None

    def delete(self, customer_id):
        """Xóa khách - cần lấy email trước để xóa bảng email."""
        customer = self.get_by_id(customer_id)
        if customer:
            self.session.execute(
                self.delete_by_email, (customer['email'], customer_id)
            )
        self.session.execute(self.delete_customer, (customer_id,))

    def close(self):
        self.cluster.shutdown()
