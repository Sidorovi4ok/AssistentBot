import os
import hashlib
from sqlalchemy import create_engine, Column, Integer, String, Boolean
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
    inn = Column(String(12), unique=True, nullable=False)  # ИНН (12 цифр)
    password = Column(String, nullable=False)               # Хэш пароля
    user_type = Column(Integer, default=2, nullable=False)    # Тип пользователя: 1 – менеджер, 2,3,4 – клиенты
    telegram_id = Column(Integer, unique=True, nullable=True)
    is_authenticated = Column(Boolean, default=False)       # Флаг авторизации

class UserManager:
    def __init__(self, db_path: str = os.path.join("data", "db", "users.db")):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def register_user(self, inn: str, password: str, telegram_id: int, user_type: int = 2) -> bool:
        """
        Регистрирует нового пользователя. Хранит хэш пароля.
        По умолчанию тип – клиент (2). Если ID есть в ALLOWED_MANAGERS, устанавливается тип 1 (менеджер).
        """
        session = self.Session()
        try:
            # Проверяем — если ID есть в списке менеджеров, меняем тип
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
        """
        Производит авторизацию пользователя по ИНН и паролю.
        Если пользователь найден и пароль корректный – обновляет telegram_id и ставит флаг авторизации.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(inn=inn).first()
            if user and verify_password(password, user.password):
                user.telegram_id = telegram_id
                user.is_authenticated = True
                session.commit()
                return True
            else:
                return False
        finally:
            session.close()

    def change_user_type(self, inn: str, new_type: int) -> bool:
        """
        Меняет тип пользователя (для менеджера).
        Допустимые типы для клиентов: 2, 3, 4.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(inn=inn).first()
            if user:
                user.user_type = new_type
                session.commit()
                return True
            else:
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
        """
        Возвращает пользователя по telegram_id.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            return user
        finally:
            session.close()

    def get_discount(self, user_type: int) -> float:
        """
        Возвращает процент скидки в зависимости от типа пользователя.
        Например, для типов 2, 3, 4 скидки 10%, 20%, 30%.
        """
        discounts = {2: 0.1, 3: 0.2, 4: 0.3}
        return discounts.get(user_type, 0)


    @staticmethod
    def get_user_type_name(user_type: int) -> str:
        """
        Возвращает строковое представление типа пользователя.
        """
        return {
            1: "Менеджер",
            2: "Клиент (Базовый)",
            3: "Клиент (Средний)",
            4: "Клиент (VIP)"
        }.get(user_type, "Неизвестно")