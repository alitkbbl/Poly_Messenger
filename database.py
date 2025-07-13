from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from passlib.hash import pbkdf2_sha256  # hashing password

# base setting database
Base = declarative_base()
DATABASE_URL = "sqlite:///poly_messenger.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# Database Models
class User(Base):
    """user model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # hash password
    phone_number = Column(String(15), unique=True, nullable=False)
    profile_picture = Column(String(200), default="default_profile.jpg")
    bio = Column(String(200), default="")

    # relationship
    contacts = relationship("Contact", foreign_keys="[Contact.user_id]", back_populates="user")
    sent_messages = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="[Message.receiver_id]", back_populates="receiver")


class Contact(Base):
    """user contact Model"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # relationship
    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact = relationship("User", foreign_keys=[contact_id])


class Message(Base):
    """message Model"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    is_file = Column(Boolean, default=False)
    file_path = Column(String(200), nullable=True)
    is_read = Column(Boolean, default=False)

    # relationship
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


# Database manager system
class DatabaseManager:
    def __init__(self):
        self.session = Session()
        Base.metadata.create_all(engine)  # create table

    # --- user manager ---
    def add_user(self, username, password, phone_number):
        """sign In"""
        try:
            hashed_password = pbkdf2_sha256.hash(password)
            new_user = User(
                username=username,
                password=hashed_password,
                phone_number=phone_number
            )
            self.session.add(new_user)
            self.session.commit()
            return new_user
        except Exception as error:
            self.session.rollback()
            raise Exception(str(error))

    def login_user(self, username, password):
        """sign Up"""
        user = self.session.query(User).filter_by(username=username).first()
        if user and pbkdf2_sha256.verify(password, user.password):  # compare password hash
            return user
        return None

    def get_user_by_username(self, username):
        return self.session.query(User).filter_by(username=username).first()

    def get_user_by_phone(self, phone_number):
        return self.session.query(User).filter_by(phone_number=phone_number).first()

    def verify_user(self, username, password):
        """Authentication user"""
        user = self.get_user_by_username(username)
        if user and pbkdf2_sha256.verify(password, user.password):
            return user
        return None

    # --- manager contact ---
    def add_contact(self, user_id, contact_username):
        """add new contact"""
        try:
            contact_user = self.get_user_by_username(contact_username)
            if not contact_user:
                raise Exception("user not exist")

            # check exist contact
            existing_contact = self.session.query(Contact).filter_by(
                user_id=user_id,
                contact_id=contact_user.id
            ).first()

            if existing_contact:
                raise Exception("this contact exist")

            new_contact = Contact(
                user_id=user_id,
                contact_id=contact_user.id
            )
            self.session.add(new_contact)
            self.session.commit()
            return contact_user
        except Exception as error:
            self.session.rollback()
            raise Exception(str(error))

    def get_user_contacts(self, user_id):
        return self.session.query(Contact).filter_by(user_id=user_id).all()

    # --- manager message ---
    def add_message(self, sender_id, receiver_id, content, is_file=False, file_path=None):
        """save new message"""
        try:
            new_message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                is_file=is_file,
                file_path=file_path
            )
            self.session.add(new_message)
            self.session.commit()
            return new_message
        except Exception as error:
            self.session.rollback()
            raise Exception(str(error))

    def get_messages_between_users(self, user1_id, user2_id, limit=100):
        """get history chat between two user"""
        return self.session.query(Message).filter(
            ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
        ).order_by(Message.timestamp.desc()).limit(limit).all()

    # --- manager profile ---
    def update_profile(self, user_id, **kwargs):
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                raise Exception("User not found")

            if 'username' in kwargs and kwargs['username']:
                existing = self.get_user_by_username(kwargs['username'])
                if existing and existing.id != user_id:
                    raise Exception("Username already exists")
                user.username = kwargs['username']

            if 'phone_number' in kwargs and kwargs['phone_number']:
                existing = self.get_user_by_phone(kwargs['phone_number'])
                if existing and existing.id != user_id:
                    raise Exception("Phone number already exists")
                user.phone_number = kwargs['phone_number']

            if 'password' in kwargs and kwargs['password']:
                user.password = pbkdf2_sha256.hash(kwargs['password'])

            self.session.commit()
            return user

        except Exception as e:
            self.session.rollback()
            raise Exception(str(e))

    def close(self):
        """close database connection"""
        self.session.close()


# db = DatabaseManager()

# db.add_user("aria", "Aria1234!", "09123456789")

# user = db.verify_user("aria", "Aria1234!")

# db.add_contact(user.id, "hamid")

# db.add_message(sender_id=user.id, receiver_id=2, content="hy hamid")

# messages = db.get_messages_between_users(user.id, 2)

# messages = db.get_messages_between_users(user.id, 2)

if __name__ == "__main__":
    db = DatabaseManager()


