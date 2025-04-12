import os
import hashlib
import threading
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from config.settings import ALLOWED_MANAGERS

Base = declarative_base()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    inn = Column(String(12), unique=True, nullable=False)
    password = Column(String, nullable=False)
    user_type = Column(Integer, default=2, nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=True)
    is_authenticated = Column(Boolean, default=False)


class Discount(Base):
    __tablename__ = 'discounts'
    user_type = Column(Integer, ForeignKey('users.user_type'), primary_key=True)
    discount_value = Column(Float, nullable=False, default=0.0)


class UserManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False
            return cls._instance

    def __init__(self, db_path: str = os.path.join("data", "db", "users.db")):
        if self.__initialized:
            return
        self.__initialized = True

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._init_default_discounts()

    def _init_default_discounts(self):
        default_discounts = {2: 0.1, 3: 0.2, 4: 0.3}
        session = self.Session()
        try:
            for user_type, discount in default_discounts.items():
                if not session.get(Discount, user_type):
                    new_discount = Discount(
                        user_type=user_type,
                        discount_value=discount
                    )
                    session.add(new_discount)
            session.commit()
        finally:
            session.close()

    def register_user(self, inn: str, password: str, telegram_id: int, user_type: int = 2) -> bool:
        session = self.Session()
        try:
            if telegram_id in ALLOWED_MANAGERS:
                user_type = 1

            new_user = User(
                inn=inn,
                password=hash_password(password),
                telegram_id=telegram_id,
                user_type=user_type,
                is_authenticated=False
            )
            session.add(new_user)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        finally:
            session.close()

    def login_user(self, inn: str, password: str, telegram_id: int) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter_by(inn=inn).first()
            if user and verify_password(password, user.password):
                user.telegram_id = telegram_id
                user.is_authenticated = True
                session.commit()
                return True
            return False
        finally:
            session.close()

    def change_user_type(self, inn: str, new_type: int) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter_by(inn=inn).first()
            if user:
                user.user_type = new_type
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_user_by_inn(self, inn: str) -> User:
        session = self.Session()
        try:
            return session.query(User).filter_by(inn=inn).first()
        finally:
            session.close()

    def get_user_by_telegram(self, telegram_id: int) -> User:
        session = self.Session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        finally:
            session.close()

    def get_discount(self, user_type: int) -> float:
        session = self.Session()
        try:
            discount = session.get(Discount, user_type)
            return discount.discount_value if discount else 0.0
        finally:
            session.close()

    def set_discount(self, user_type: int, new_discount: float) -> bool:
        if not 0 <= new_discount <= 1:
            return False

        session = self.Session()
        try:
            discount = session.get(Discount, user_type)
            if discount:
                discount.discount_value = new_discount
            else:
                session.add(Discount(
                    user_type=user_type,
                    discount_value=new_discount
                ))
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    @staticmethod
    def get_user_type_name(user_type: int) -> str:
        return {
            1: "Менеджер",
            2: "Клиент (Базовый)",
            3: "Клиент (Средний)",
            4: "Клиент (VIP)"
        }.get(user_type, "Неизвестно")