class ProfileDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profile")
        vbox = QVBoxLayout(self)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- پشتیبانی هم آبجکت هم دیکشنری user
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
        lbl_img.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
