import sys
import socket
import os
import shutil
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from databasem import DatabaseManager

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


class ProfileDialog(QDialog):
    def __init__(self, parent=None, username="", phone="", avatar=None):
        super().__init__(parent)
        self.setWindowTitle("Profile")
        self.setFixedSize(320, 350)
        self.setStyleSheet("""
            QDialog {background:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1849a6, stop: 1 #191622);}
            QLabel {color:white; font-size:16px;}
        """)
        layout = QVBoxLayout()
        avatar_label = QLabel()
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if avatar:
            avatar_pixmap = QPixmap(avatar).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
        else:
            avatar_pixmap = QPixmap(110, 110)
            avatar_pixmap.fill(Qt.GlobalColor.darkGray)
        avatar_label.setPixmap(avatar_pixmap)
        avatar_label.setFixedHeight(120)
        layout.addWidget(avatar_label)
        layout.addSpacing(18)
        uname = QLabel(f"Username: {username}")
        uname.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phone_label = QLabel(f"Phone: {phone}")
        phone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(uname)
        layout.addWidget(phone_label)
        layout.addStretch()
        hdi_lbl = QLabel("HDI")
        hdi_lbl.setFont(QFont("Arial Black", 20))
        hdi_lbl.setStyleSheet("color:#ddd;")
        hdi_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(hdi_lbl)
        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(self, user, db, parent=None):
        super().__init__(parent)
        self.user = user
        self.db = db
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 450)
        self.setStyleSheet("""
            QDialog {background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #840202, stop:1 #400000);}
            QLineEdit {background: #222; color:white; border-radius:5px; padding:8px; font-size:13px; border:1px solid #222;}
            QPushButton {background: #444; color:white; border-radius:6px; padding:10px;}
            QPushButton:hover {background: #bb4444;}
            QLabel {color:white; margin-top: 12px;}
        """)
        layout = QVBoxLayout()
        self.username_input = QLineEdit(self.user.username)
        self.username_input.setReadOnly(True)
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        self.phone_input = QLineEdit(self.user.phone_number)
        layout.addWidget(QLabel("Phone Number:"))
        layout.addWidget(self.phone_input)
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("New Password:"))
        layout.addWidget(self.pass_input)
        self.conf_pass_input = QLineEdit()
        self.conf_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Confirm New Password:"))
        layout.addWidget(self.conf_pass_input)
        self.change_pic_btn = QPushButton("Change Profile Picture")
        layout.addWidget(self.change_pic_btn)
        self.save_btn = QPushButton("Save Changes")
        layout.addWidget(self.save_btn)
        self.setLayout(layout)
        self.change_pic_btn.clicked.connect(self.choose_image)
        self.save_btn.clicked.connect(self.save_settings)

    def choose_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            filename = f"profile_{self.user.username}.jpg"
            profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_pics")
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            dest = os.path.join(profile_dir, filename)
            try:
                shutil.copyfile(file_path, dest)
                self.db.update_profile(user_id=self.user.id, profile_picture=filename)
                QMessageBox.information(self, "Success", "Profile picture updated!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not update picture:\n{e}")

    def save_settings(self):
        phone = self.phone_input.text().strip()
        password = self.pass_input.text()
        conf_password = self.conf_pass_input.text()
        if password and password != conf_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        self.db.update_profile(user_id=self.user.id, phone_number=phone, password=password if password else None)
        QMessageBox.information(self, "Saved", "Changes saved")
        self.accept()

    def logout(self):
        self.accept()
        if self.mainwin:
            self.mainwin.logout_and_return()


class ContactCard(QWidget):
    clicked = pyqtSignal(str, str)

    def __init__(self, username, phone, avatar=None):
        super().__init__()
        self.username = username
        self.phone = phone

        if avatar is None or not os.path.exists(avatar):
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            avatar = os.path.join(BASE_DIR, "Contact.png")
            if not os.path.exists(avatar):
                avatar = None
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
        set_btn.setIcon(QIcon("setting.png"))
        set_btn.setIconSize(QtCore.QSize(32, 32))
        set_btn.setToolTip("Settings")
        set_btn.clicked.connect(self.openSettingsDialog)
        contact_btn = QToolButton()
        contact_btn.setIcon(QIcon("Contact.png"))
        contact_btn.setIconSize(QtCore.QSize(32, 32))
        contact_btn.setToolTip("Contacts")
        contact_btn.clicked.connect(self.open_contacts)
        add_btn = QToolButton()
        add_btn.setIcon(QIcon.fromTheme("list-add"))
        add_btn.setText("➕")
        add_btn.setIconSize(QtCore.QSize(25, 25))
        add_btn.setToolTip("Add Contact")
        add_btn.clicked.connect(self.openAddContactDialog)
        row_icons.addWidget(set_btn)
        row_icons.addWidget(contact_btn)
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
        SettingsDialog(self, self.username).exec()

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


class PrivateChatWindow(QWidget):
    def __init__(self, db, current_user, contact_user):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.contact_user = contact_user
        self.setWindowTitle(f"Chat with {self.contact_user.username}")

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")

        layout = QVBoxLayout()
        layout.addWidget(self.chat_display)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        self.setLayout(layout)

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
