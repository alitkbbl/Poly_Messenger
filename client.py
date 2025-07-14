import sys
import socket
import os
import shutil
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6 import QtCore
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from database import DatabaseManager

print(os.path.abspath("Contact.png"))
print(os.path.abspath("setting.png"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234


class ReceiverThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.running = True

    def run(self):
        while self.running:
            try:
                msg = self.sock.recv(1024).decode('utf-8')
                if msg:
                    self.message_received.emit(msg.strip())
                else:
                    break
            except:
                break

    def stop(self):
        self.running = False
        self.quit()


class AddContactDialog(QDialog):
    def __init__(self, parent=None, on_add=None):
        super().__init__(parent)
        self.setWindowTitle("Add Contact")
        self.setFixedSize(340, 200)
        self.setStyleSheet("""
            QDialog {background:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #E8BC05, stop: 1 #191622);}
            QLineEdit {background:#222; color:white; border-radius:5px; padding:10px; font-size:14px; border:1px solid #666;}
            QPushButton {background:#222; color:white; padding:8px; border-radius:5px;}
            QPushButton:hover {background:#38a;}
        """)
        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(lambda: on_add(self.username_input.text(), self.phone_input.text(), self))
        layout.addWidget(self.username_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.add_btn)
        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(self, user, db, parent=None):
        super().__init__(parent)
        try:
            if user is None or db is None:
                raise ValueError("User or db object is None")
            self.user = user
            self.db = db
            self.setWindowTitle("Settings")
            self.setFixedSize(410, 490)
            self.setStyleSheet("""
                QDialog {
                    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0,y2:1, stop:0 #a10000, stop:1 #400000);
                    border-radius: 17px;
                }
                QLineEdit {
                    background: #222;
                    color: #eee;
                    border-radius: 7px;
                    border: 1.7px solid #343434;
                    padding: 9px;
                    font-size: 16px;
                    font-family: Consolas;
                }
                QPushButton {
                    background: #444;
                    color:#fff;
                    border-radius: 7px;
                    padding:12px;
                    font-size:16px;
                    font-weight: 600;
                }
                QPushButton:hover {background: #b14040;}
                QLabel {color:#fff; font-size:15.5px; font-family: Calibri; margin-top:7px;}
            """)
            layout = QVBoxLayout()
            layout.setContentsMargins(36, 24, 36, 19)
            layout.setSpacing(9)

            uname = getattr(self.user, "username", "")
            uphone = getattr(self.user, "phone_number", "")
            layout.addWidget(QLabel("Username:"))
            self.username_input = QLineEdit(uname)
            self.username_input.setStyleSheet("color:#eee;background:#333;font-weight:bold;")
            layout.addWidget(self.username_input)
            layout.addWidget(QLabel("Phone Number:"))
            self.phone_input = QLineEdit(str(uphone))
            layout.addWidget(self.phone_input)
            layout.addWidget(QLabel("New Password:"))
            self.pass_input = QLineEdit()
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.pass_input)
            layout.addWidget(QLabel("Confirm New Password:"))
            self.conf_pass_input = QLineEdit()
            self.conf_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.conf_pass_input)
            self.change_pic_btn = QPushButton("Change Profile Picture")
            self.change_pic_btn.setStyleSheet("""
                QPushButton {background:#676060;color:#fff;font-weight:500;}
                QPushButton:hover {background:#b14040;}
            """)
            layout.addWidget(self.change_pic_btn)
            self.save_btn = QPushButton("Save Changes")
            self.save_btn.setStyleSheet("""
                QPushButton {background:#676060;color:#fff;font-weight:600;}
                QPushButton:hover {background:#b14040;}
            """)
            layout.addWidget(self.save_btn)
            logo = QLabel("HDI")
            logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            logo.setFont(QFont("Arial Black", 54, QFont.Weight.Bold))
            logo.setStyleSheet("""
                color:white;
                margin-top:13px; 
                font-weight: bold;
                letter-spacing: 13px;
            """)
            layout.addStretch(1)
            layout.addWidget(logo)
            self.setLayout(layout)
            self.change_pic_btn.clicked.connect(self.choose_image)
            self.save_btn.clicked.connect(self.save_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"SettingsDialog init failed:{e}")
            self.close()

    def choose_image(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Profile Picture",
                "",
                "Image Files (*.png *.jpg *.jpeg)"
            )

            if file_path:

                profile_dir = os.path.join(BASE_DIR, "profile_pics")
                os.makedirs(profile_dir, exist_ok=True)

                if not os.access(profile_dir, os.W_OK):
                    raise Exception("Cannot write to profile directory")

                filename = f"profile_{self.user.username}.jpg"
                dest = os.path.join(profile_dir, filename)

                try:
                    shutil.copyfile(file_path, dest)
                    self.db.update_profile(
                        user_id=self.user.id,
                        profile_picture=filename
                    )
                    QMessageBox.information(
                        self,
                        "Success",
                        "Profile picture updated!"
                    )
                except PermissionError:
                    raise Exception("Permission denied when saving image")
                except OSError as e:
                    raise Exception(f"File system error: {str(e)}")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not update picture: {str(e)}"
            )

    def save_settings(self):
        try:
            uname = self.username_input.text().strip()
            phone = self.phone_input.text().strip()
            password = self.pass_input.text()
            conf_password = self.conf_pass_input.text()

            if not uname:
                QMessageBox.warning(self, "Error", "Username cannot be empty.")
                return
            if not phone:
                QMessageBox.warning(self, "Error", "Phone number cannot be empty.")
                return
            if password and password != conf_password:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return

            try:
                updated_user = self.db.update_profile(
                    user_id=self.user.id,
                    username=uname,
                    phone_number=phone,
                    password=password if password else None
                )
                QMessageBox.information(self, "Success", "Profile updated successfully!")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update profile: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


class ContactCard(QWidget):
    clicked = pyqtSignal(str, str)
    CONTACTS_FILE = "contacts.json"

    def __init__(self, username, phone, avatar=None):
        super().__init__()
        self.username = username
        self.phone = phone



        if avatar is None or not os.path.exists(avatar):
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            profile_pics_dir = os.path.join(BASE_DIR, "profile_pics")
            os.makedirs(profile_pics_dir, exist_ok=True)

            avatar_filename = f"profile_{self.username}.jpg"
            avatar_path = os.path.join(profile_pics_dir, avatar_filename)

            if os.path.exists(avatar_path):
                avatar = avatar_path
            else:
                avatar_filename2 = "Contact.jpg"
                default_avatar = os.path.join(profile_pics_dir, avatar_filename2)
                avatar = default_avatar if os.path.exists(default_avatar) else None

        self.avatar = avatar

        self.setFixedHeight(68)
        self.setStyleSheet("""
            QWidget {
                background:rgba(21,198,214,0.14);
                border-radius:14px;
                margin-bottom:7px;
            }
            QLabel {color:white;}
        """)

        lyt = QHBoxLayout(self)
        img = QLabel()
        if self.avatar and os.path.exists(self.avatar):
            img.setPixmap(QPixmap(self.avatar).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation))
        else:
            blank = QPixmap(48, 48)
            blank.fill(Qt.GlobalColor.darkCyan)
            img.setPixmap(blank)
        lyt.addWidget(img)

        vtxt = QVBoxLayout()
        vtxt.addWidget(QLabel(username))
        vtxt.addWidget(QLabel(phone))
        lyt.addLayout(vtxt)

    def mousePressEvent(self, event):
        self.clicked.emit(self.username, self.phone)


class ChatWindow(QWidget):
    current_theme = "Dark"

    def __init__(self, sock, username, phone=""):
        super().__init__()
        self.sock = sock
        self.username = username
        self.phone = phone
        self.contacts = []
        self.db = DatabaseManager()
        self.current_user = self.db.get_user_by_username(self.username)
        self.setWindowTitle(f"Welcome {username}")

        sidebar = QWidget()
        sidebar.setFixedWidth(145)
        sidebar.setStyleSheet("""
            QWidget {
                background:qlineargradient(spread:pad, x1:0,y1:0, x2:0,y2:1, stop:0 #33457a, stop:1 #0c192e);
                border-top-left-radius:7px;
                border-bottom-left-radius:7px;
            }
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setSpacing(13)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        row_icons = QHBoxLayout()
        set_btn = QToolButton()
        icon = QIcon("setting.png")
        set_btn.setIcon(icon)
        set_btn.setIconSize(QSize(32, 32))
        set_btn.setToolTip("Settings")
        set_btn.clicked.connect(self.openSettingsDialog)

        add_btn = QToolButton()
        icon = QIcon("Contact.png")
        add_btn.setIcon(icon)
        add_btn.setIconSize(QSize(32, 32))
        add_btn.setToolTip("Add Contact")
        add_btn.clicked.connect(self.openAddContactDialog)
        row_icons.addWidget(add_btn)
        row_icons.addWidget(set_btn)

        profile_btn = QToolButton()
        profile_icon = QIcon("profile.png")
        profile_btn.setIcon(profile_icon)
        profile_btn.setIconSize(QSize(32, 32))
        profile_btn.setToolTip("Profile")
        profile_btn.clicked.connect(self.openProfileWindow)
        row_icons.addWidget(profile_btn)

        row_icons.addWidget(add_btn)
        sb_layout.addLayout(row_icons)
        self.contacts_layout = QVBoxLayout()
        self.contacts_layout.setSpacing(5)
        sb_layout.addSpacing(20)
        sb_layout.addLayout(self.contacts_layout)
        sb_layout.addStretch()
        hdi_lbl = QLabel("HDI")
        hdi_lbl.setStyleSheet("color:#fff;font-family:Arial Black;font-size:20px;")
        hdi_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        sb_layout.addWidget(hdi_lbl)
        center_panel = QWidget()
        center_panel.setStyleSheet("""
            QWidget {
                background:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #20936b, stop:1 #17222e);
                border-top-right-radius:7px;
                border-bottom-right-radius:7px;
            }
        """)
        center_ly = QVBoxLayout(center_panel)
        hdilogo = QLabel("HDI")
        hdilogo.setFont(QFont("Arial Black", 70))
        hdilogo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdilogo.setStyleSheet("color:rgba(255,255,255,0.15);")
        center_ly.addWidget(hdilogo)
        center_ly.addStretch()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        center_ly.insertWidget(0, self.chat_display)
        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        input_row.addWidget(self.message_input)
        self.send_button = QPushButton("Send")
        input_row.addWidget(self.send_button)
        center_ly.addLayout(input_row)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sidebar)
        layout.addWidget(center_panel)
        self.setMinimumSize(730, 500)
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.apply_theme("Dark")
        self.open_chats = []
        self.receiver = ReceiverThread(self.sock)
        self.receiver.message_received.connect(self.display_message)
        self.receiver.start()

    def openSettingsDialog(self, evt):
        SettingsDialog(self.current_user, self.db, self).exec()

    def open_contacts(self, evt):
        QMessageBox.information(self, "Contacts", f"{len(self.contacts)} Contacts added.")

    def openAddContactDialog(self, evt=None):
        AddContactDialog(self, self.on_add_contact).exec()

    def on_add_contact(self, uname, phone, dlg):
        if uname.strip() and phone.strip():
            self.contacts.append((uname, phone, "Contact.png"))
            self.update_contacts_gui()
            dlg.accept()

    def update_contacts_gui(self):
        while self.contacts_layout.count():
            item = self.contacts_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for c in self.contacts:
            card = ContactCard(c[0], c[1], c[2])
            card.clicked.connect(self.open_private_chat)
            self.contacts_layout.addWidget(card)

    def apply_theme(self, theme):
        self.current_theme = theme

    def set_username(self, uname):
        self.username = uname
        self.setWindowTitle(f"Welcome {uname}")
        self.current_user = self.db.get_user_by_username(self.username)

    def send_message(self):
        msg = self.message_input.text().strip()
        if msg:
            try:
                self.sock.sendall((msg + '\n').encode('utf-8'))
                self.message_input.clear()
            except:
                QMessageBox.critical(self, "Error", "Disconnected from server.")

    def display_message(self, msg):
        if hasattr(self, "chat_display") and self.chat_display:
            self.chat_display.append(msg)

    def logout_and_return(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def closeEvent(self, event):
        try:
            if hasattr(self, "receiver") and self.receiver.isRunning():
                self.receiver.stop()
                self.receiver.wait(100)
            if hasattr(self, "sock"):
                self.sock.close()
        except Exception as e:
            print("Error in closeEvent:", e)
        event.accept()

    def open_private_chat(self, username, phone):
        contact_user = self.db.get_user_by_username(username)
        if contact_user is None:
            QMessageBox.warning(self, "Error", f"User {username} not found in database.")
            return
        chat = PrivateChatWindow(self.db, self.current_user, contact_user)
        chat.show()
        self.open_chats.append(chat)

    def openProfileWindow(self, evt=None):
        dlg = ProfileDialog(self.current_user, self)
        dlg.exec()


class ProfileDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profile")
        vbox = QVBoxLayout(self)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if isinstance(user, dict):
            username = user.get("username", "")
            phone = user.get("phone", "")
            avatar = user.get("avatar", "Contact.png")
        else:
            username = getattr(user, 'username', "")
            phone = getattr(user, 'phone', "")
            avatar = getattr(user, 'avatar', "Contact.png")
        if not avatar or not isinstance(avatar, str) or not os.path.exists(avatar):
            avatar = "Contact.png"
        lbl_img = QLabel()
        pix = QPixmap(avatar)
        lbl_img.setPixmap(
            pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        vbox.addWidget(lbl_img)

        lbl_name = QLabel(f"Username: {username}")
        lbl_name.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setStyleSheet("color:white;")
        vbox.addWidget(lbl_name)

        lbl_phone = QLabel(f"Phone: {phone}")
        lbl_phone.setFont(QFont("Arial", 12))
        lbl_phone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_phone.setStyleSheet("color:white;")
        vbox.addWidget(lbl_phone)
        self.setStyleSheet("""
            QDialog {background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d4b8d, stop:1 #153051); border-radius:16px;}
        """)
        self.setFixedSize(330, 350)


class PrivateChatWindow(QWidget):
    def __init__(self, db, current_user, contact_user):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.contact_user = contact_user
        self.setWindowTitle(f"Chat with {self.contact_user.username}")
        self.setMinimumSize(650, 500)

        center_panel = QWidget()
        center_panel.setStyleSheet("""
            QWidget {
                background:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #20936b, stop:1 #17222e);
                border-radius:12px;
            }
        """)

        chat_layout = QVBoxLayout(center_panel)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(20, 18, 20, 18)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #fff;
                font-size:15px;
                border:none;
            }
        """)

        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background: #272727;
                color: #fff;
                border-radius: 9px;
                padding: 9px;
                font-size:14px;
                border: 1px solid #313131;
            }
        """)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #00897B;
                color: #fff;
                border-radius: 7px;
                padding: 8px 22px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #00BFAE;
            }
        """)
        input_row.addWidget(self.message_input)
        input_row.addWidget(self.send_button)

        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_row)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(center_panel)

        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.load_messages()

    def load_messages(self):
        messages = self.db.get_messages_between_users(self.current_user.id, self.contact_user.id)
        self.chat_display.clear()
        for msg in messages:
            sender = "You" if msg.sender_id == self.current_user.id else self.contact_user.username
            self.chat_display.append(f"<b>{sender}:</b> {msg.content}")

    def send_message(self):
        content = self.message_input.text().strip()
        if content:
            self.db.add_message(self.current_user.id, self.contact_user.id, content)
            self.message_input.clear()
            self.load_messages()


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign In")
        self.setFixedSize(700, 490)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1b3bb2, stop:1 #000);
            }
            QLineEdit {
                background: #262626;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 13px;
                font-size: 17px;
                margin-bottom: 14px;
            }
            QLabel#logo {
                color: #fff;
                font-family: Arial Black;
                font-size: 41px;
                margin-bottom: 17px;
                letter-spacing: 4px;
            }
            QLabel, QPushButton {color:white;}
            QPushButton {
                background: #3a3a3a;
                border-radius: 8px;
                font-size: 16px;
                padding: 14px 0;
                margin: 12px 13px 0 0;
            }
            QPushButton:hover {background:#2049c2;}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(30)

        logo = QLabel("Messenger")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        rowbtn = QHBoxLayout()
        rowbtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signin_btn = QPushButton("Sign In")
        signup_btn = QPushButton("Go to Sign Up")
        signin_btn.setFixedWidth(180)
        signup_btn.setFixedWidth(180)
        signin_btn.clicked.connect(self.handle_signin)
        signup_btn.clicked.connect(self.goto_signup)
        rowbtn.addWidget(signin_btn)
        rowbtn.addWidget(signup_btn)
        layout.addLayout(rowbtn)
        layout.addStretch()

        hdi_lbl = QLabel("HDI")
        hdi_lbl.setStyleSheet("font-family:Arial Black;font-size:22px;color:#fff;margin:0px 25px 14px 0;")
        hdi_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hdi_lbl)

    def handle_signin(self):
        def handle_signin(self):
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            if not username or not password:
                QMessageBox.warning(self, "Input Error", "Please enter username & password.")
                return
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((SERVER_HOST, SERVER_PORT))
                import json
                data = {
                    "type": "login",
                    "username": username,
                    "password": password
                }
                sock.sendall((json.dumps(data) + '\n').encode('utf-8'))
                resp = sock.recv(2048).decode('utf-8')
                for line in resp.strip().split("\n"):
                    answer = json.loads(line)
                    if answer.get("status") == "ok":
                        self.chat_window = ChatWindow(sock, username)
                        self.chat_window.show()
                        self.close()
                        return
                    else:
                        QMessageBox.critical(self, "Login Failed", answer.get("message", "Unknown error"))
                        sock.close()
                        return
            except Exception as e:
                QMessageBox.critical(self, "Connection Failed", str(e))

    def handle_signin(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter username & password.")
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_HOST, SERVER_PORT))
            import json
            data = {
                "type": "login",
                "username": username,
                "password": password
            }
            sock.sendall((json.dumps(data) + '\n').encode('utf-8'))
            resp = sock.recv(2048).decode('utf-8')
            for line in resp.strip().split("\n"):
                answer = json.loads(line)
                if answer.get("status") == "ok":
                    self.chat_window = ChatWindow(sock, username)
                    self.chat_window.show()
                    self.close()
                    return
                else:
                    QMessageBox.critical(self, "Login Failed", answer.get("message", "Unknown error"))
                    sock.close()
                    return
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", str(e))

    def goto_signup(self):
        self.signupwindow = SignupWindow()
        self.signupwindow.show()
        self.close()


class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Up")
        self.setFixedSize(700, 490)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1b3bb2, stop:1 #000);
            }
            QLineEdit {
                background: #262626;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 13px;
                font-size: 17px;
                margin-bottom: 14px;
            }
            QLabel#logo {
                color: #fff;
                font-family: Arial Black;
                font-size: 41px;
                margin-bottom: 17px;
                letter-spacing: 4px;
            }
            QLabel, QPushButton {color:white;}
            QPushButton {
                background: #3a3a3a;
                border-radius: 8px;
                font-size: 16px;
                padding: 14px 0;
                margin: 12px 13px 0 0;
            }
            QPushButton:hover {background:#2049c2;}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(30)

        logo = QLabel("Messenger")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        layout.addWidget(self.phone_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_input)

        rowbtn = QHBoxLayout()
        rowbtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signup_btn = QPushButton("Sign Up")
        signin_btn = QPushButton("Go to Sign In")
        signup_btn.setFixedWidth(180)
        signin_btn.setFixedWidth(180)
        rowbtn.addWidget(signup_btn)
        rowbtn.addWidget(signin_btn)
        layout.addLayout(rowbtn)
        layout.addStretch()

        hdi_lbl = QLabel("HDI")
        hdi_lbl.setStyleSheet("font-family:Arial Black;font-size:22px;color:#fff;margin:0px 25px 14px 0;")
        hdi_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hdi_lbl)

        signup_btn.clicked.connect(self.handle_signup)
        signin_btn.clicked.connect(self.goto_login)

    def goto_login(self):
        self.loginwindow = LoginWindow()
        self.loginwindow.show()
        self.close()

    def handle_signup(self):
        username = self.username_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        if not username or not password or not confirm or not phone:
            QMessageBox.warning(self, "Input Error", "Please fill all fields.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Register Error", "Passwords do not match.")
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_HOST, SERVER_PORT))
            import json
            data = {
                "type": "signup",
                "username": username,
                "password": password,
                "phone": phone
            }
            sock.sendall((json.dumps(data) + '\n').encode('utf-8'))
            resp = sock.recv(2048).decode('utf-8')
            for line in resp.strip().split("\n"):
                answer = json.loads(line)
                if answer.get("status") == "ok":
                    QMessageBox.information(self, "Registered", "Account created. Now sign in.")
                    sock.close()
                    self.goto_login()
                    return
                else:
                    QMessageBox.critical(self, "Signup Failed", answer.get("message", "Unknown error"))
                    sock.close()
                    return
        except Exception as e:
            QMessageBox.critical(self, "Signup Failed", str(e))


def main():
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
