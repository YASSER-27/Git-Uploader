import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

# 🎨 تعريف متغيرات الألوان (Sonic Style - Blue & Black)
COLOR_BACKGROUND = "#000000"  # أسود
COLOR_FOREGROUND = "#F0F0F0"  # أبيض خفيف
COLOR_ACCENT = "#007BFF"      # أزرق ساطع (Sonic Blue)
COLOR_BUTTON_HOVER = "#0056B3"
COLOR_INPUT_BG = "#1A1A1A"
COLOR_SUCCESS = "#28A745"     # أخضر للنجاح

class GitUploaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Git Uploader - Easy Push Tool")
        self.setMinimumSize(QSize(400, 400)) 
        
        self.project_path = ""
        self.repo_url = ""
        self.pat_token = ""
        self.git_name = ""
        self.git_email = ""

        self.apply_style()
        self.setup_ui()

    def apply_style(self):
        """تطبيق النمط الأزرق والأسود على الواجهة."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BACKGROUND};
                color: {COLOR_FOREGROUND};
            }}
            QLabel {{
                color: {COLOR_FOREGROUND};
                font-size: 10pt;
            }}
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_FOREGROUND};
                border: 1px solid {COLOR_ACCENT};
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FOREGROUND};
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BUTTON_HOVER};
            }}
            QGroupBox {{
                border: 2px solid {COLOR_ACCENT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: {COLOR_ACCENT};
                font-weight: bold;
            }}
            #TokenInput {{ 
                line-edit-password-character: 9679;
                line-edit-password-mask-delay: 500;
            }}
        """)

    def setup_ui(self):
        """بناء عناصر الواجهة (Labels, Inputs, Buttons)."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. اختيار مجلد المشروع (Folder Picker)
        folder_group = QGroupBox("1. مجلد المشروع المحلي")
        folder_layout = QHBoxLayout(folder_group)
        
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        self.path_display.setPlaceholderText("اختر مجلد مشروعك...")
        
        folder_button = QPushButton("... تصفح")
        folder_button.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.path_display)
        folder_layout.addWidget(folder_button)
        main_layout.addWidget(folder_group)

        # 2. إعدادات Git (الاسم والبريد)
        config_group = QGroupBox("2. هوية المستخدم (Global Git Config)")
        config_layout = QVBoxLayout(config_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسمك الكامل (لـ git config user.name)")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("أدخل بريدك الإلكتروني (لـ git config user.email)")
        
        config_layout.addWidget(self.name_input)
        config_layout.addWidget(self.email_input)
        main_layout.addWidget(config_group)


        # 3. رابط GitHub (URL Input)
        url_group = QGroupBox("3. رابط مستودع GitHub (URL)")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("أدخل رابط المستودع البعيد (ينتهي بـ .git)")
        url_layout.addWidget(self.url_input)
        main_layout.addWidget(url_group)
        
        # 4. رمز الوصول الشخصي (PAT Input)
        token_group = QGroupBox("4. رمز الوصول الشخصي (PAT/Token)")
        token_layout = QVBoxLayout(token_group)
        
        self.token_input = QLineEdit()
        self.token_input.setObjectName("TokenInput") 
        self.token_input.setEchoMode(QLineEdit.Password) 
        self.token_input.setPlaceholderText("ألصق رمز PAT الذي أنشأته على GitHub هنا...")
        token_layout.addWidget(self.token_input)
        main_layout.addWidget(token_group)
        
        # 5. زر الإرسال (SEND Button)
        send_button = QPushButton("🚀 إرسال المشروع بالكامل إلى GitHub (SEND)")
        send_button.clicked.connect(self.send_to_github)
        main_layout.addWidget(send_button)
        
        # 6. رسالة الحالة
        self.status_label = QLabel("الحالة: في انتظار الإعداد...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet(f"color: {COLOR_ACCENT}; padding-top: 10px;")
        main_layout.addWidget(self.status_label)

    def select_folder(self):
        """فتح مربع حوار لاختيار مجلد المشروع."""
        folder_path = QFileDialog.getExistingDirectory(self, "اختر مجلد مشروعك")
        if folder_path:
            self.project_path = folder_path
            self.path_display.setText(self.project_path)
            self.status_label.setText("الحالة: تم تحديد المجلد. جاهز للربط والمصادقة.")

    def run_git_command(self, command, error_message, cwd=None):
        """ينفذ أمراً واحداً لـ Git باستخدام subprocess. تم إضافة متغير cwd."""
        try:
            # يستخدم cwd الافتراضي (مجلد المشروع) ما لم يُحدد خلاف ذلك (لأوامر --global)
            result = subprocess.run(
                command,
                cwd=cwd if cwd is not None else self.project_path,
                check=True,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8' 
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_details = f"{error_message}\n\nخطأ Git الأصلي:\n{e.stderr.strip()}"
            
            # عرض الخطأ بتنسيق مقروء (لحل مشكلة الخلفية البيضاء)
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setWindowTitle("خطأ Git")
            error_box.setText("حدث فشل أثناء تنفيذ أمر Git.")
            error_box.setDetailedText(error_details)
            error_box.setStyleSheet("QMessageBox { background-color: #f0f0f0; color: black; } QLabel { color: black; }")
            error_box.exec()
            
            self.status_label.setText(f"فشل: {error_message}")
            return None
        except FileNotFoundError:
            QMessageBox.critical(self, "خطأ في النظام", "لم يتم العثور على أمر 'git'. تأكد من تثبيت Git وإضافته إلى متغيرات PATH.")
            self.status_label.setText("فشل: لم يتم العثور على Git.")
            return None

    def send_to_github(self):
        """تنفيذ التسلسل الكامل لأوامر Git."""
        self.repo_url = self.url_input.text().strip()
        self.pat_token = self.token_input.text().strip()
        self.git_name = self.name_input.text().strip()
        self.git_email = self.email_input.text().strip()
        
        if not all([self.project_path, self.repo_url, self.pat_token, self.git_name, self.git_email]):
            QMessageBox.warning(self, "بيانات مفقودة", "الرجاء إكمال جميع الحقول: المجلد، الاسم، البريد، الرابط، والرمز (PAT).")
            return

        self.status_label.setText("الحالة: بدء عملية الرفع...")
        
        # --- 0. إعداد الهوية (Git Config Global) --- 
        self.status_label.setText("الحالة: تعيين هوية المستخدم العالمية (Name & Email)...")
        if self.run_git_command(["git", "config", "--global", "user.name", self.git_name], "فشل تعيين اسم المستخدم", cwd=os.path.expanduser('~')) is None: return
        if self.run_git_command(["git", "config", "--global", "user.email", self.git_email], "فشل تعيين البريد الإلكتروني", cwd=os.path.expanduser('~')) is None: return

        # --- 0. بناء رابط URL المصادق عليه ---
        if self.repo_url.startswith("https://"):
            base_url = self.repo_url[8:] 
            auth_url = f"https://{self.pat_token}@{base_url}"
        else:
            QMessageBox.critical(self, "خطأ في الرابط", "الرجاء استخدام رابط HTTPS (يبدأ بـ https://) لمستودع GitHub.")
            return

        # --- 1. التهيئة (git init) ---
        if not os.path.isdir(os.path.join(self.project_path, '.git')):
            self.status_label.setText("الحالة: تهيئة المستودع...")
            if self.run_git_command(["git", "init"], "فشل التهيئة") is None: return
        
        # --- 2. الإضافة (git add .) ---
        self.status_label.setText("الحالة: إضافة الملفات...")
        if self.run_git_command(["git", "add", "."], "فشل إضافة الملفات") is None: return

        # --- 3. الحفظ (git commit) ---
        self.status_label.setText("الحالة: حفظ التغييرات...")
        commit_result = self.run_git_command(["git", "commit", "-m", "Initial upload via GUI"], "فشل الحفظ (تأكد من وجود ملفات جديدة)")
        
        if commit_result is None or ("nothing to commit" in commit_result):
            if commit_result is None: return
            # لا توجد تغييرات للحفظ، نواصل العملية
        
        # --- 4. تعيين الفرع (git branch -M main) ---
        self.status_label.setText("الحالة: تعيين الفرع الرئيسي...")
        if self.run_git_command(["git", "branch", "-M", "main"], "فشل تعيين الفرع") is None: return

        # --- 5. ربط المستودع البعيد برابط المصادقة (git remote add / set-url) ---
        self.status_label.setText("الحالة: ربط المستودع برابط المصادقة...")
        try:
            remotes = self.run_git_command(["git", "remote"], "فشل التحقق من الريموت")
            if remotes and "origin" in remotes.split():
                if self.run_git_command(["git", "remote", "set-url", "origin", auth_url], "فشل تحديث الرابط البعيد") is None: return
            else:
                if self.run_git_command(["git", "remote", "add", "origin", auth_url], "فشل ربط الريموت") is None: return
        except Exception:
             if self.run_git_command(["git", "remote", "add", "origin", auth_url], "فشل ربط الريموت") is None: return

        # --- 6. مزامنة التغييرات من GitHub (git pull --rebase) --- **الإضافة الجديدة**
        self.status_label.setText("الحالة: مزامنة التغييرات من GitHub (سحب/Pull)...")
        # هذا الأمر يسحب ملف README.md من الريموت ويدمجه محليًا
        if self.run_git_command(["git", "pull", "--rebase", "origin", "main"], "فشل مزامنة التغييرات (Pull). تحقق من الاتصال.") is None: return
        
        # --- 7. الرفع (git push) ---
        self.status_label.setText("الحالة: رفع الملفات إلى GitHub...")
        push_result = self.run_git_command(["git", "push", "-u", "origin", "main"], "فشل الرفع. تحقق من صلاحية رمز PAT.")

        if push_result is not None:
            QMessageBox.information(
                self, 
                "نجاح الإرسال", 
                "✅ تم رفع المشروع بالكامل بنجاح إلى GitHub!"
            )
            self.status_label.setText("✅ نجاح! تم الرفع إلى GitHub.")
            self.status_label.setStyleSheet(f"color: {COLOR_SUCCESS}; padding-top: 10px;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GitUploaderApp()
    window.show()
    sys.exit(app.exec())