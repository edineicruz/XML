#!/usr/bin/env python3
"""
Professional Authentication Dialog for XML Fiscal Manager Pro
Modern, secure license key validation interface with loading states and error handling
"""

import logging
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QThread
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QProgressBar, QCheckBox, QTextEdit, QGroupBox, QGridLayout,
    QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)


class LoadingWidget(QFrame):
    """Custom loading widget with animated progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        self.status_label = QLabel("Preparando...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                text-align: center;
                background-color: #ffffff;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                                stop: 0 #007bff, stop: 1 #0056b3);
                border-radius: 6px;
            }
        """)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        self.hide()
    
    def show_loading(self, message: str):
        """Show loading state with message"""
        self.status_label.setText(message)
        self.show()
    
    def hide_loading(self):
        """Hide loading state"""
        self.hide()


class AuthenticationDialog(QDialog):
    """Professional authentication dialog with modern UI"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.auth_config = config_manager.get_auth_config()
        
        self.setWindowTitle("XML Fiscal Manager Pro - Autenticação")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        
        # Apply modern styling
        self._setup_styles()
        self._setup_ui()
        self._setup_connections()
        
        # Center on screen
        self._center_on_screen()
    
    def _setup_styles(self):
        """Setup modern styling for the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
            
            QLabel {
                color: #343a40;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 14px;
                background-color: #ffffff;
                selection-background-color: #007bff;
            }
            
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            
            QLineEdit:invalid {
                border-color: #dc3545;
            }
            
            QPushButton {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }
            
            QPushButton#primary {
                background-color: #007bff;
                color: white;
            }
            
            QPushButton#primary:hover {
                background-color: #0056b3;
            }
            
            QPushButton#primary:pressed {
                background-color: #004085;
            }
            
            QPushButton#primary:disabled {
                background-color: #6c757d;
            }
            
            QPushButton#secondary {
                background-color: #6c757d;
                color: white;
            }
            
            QPushButton#secondary:hover {
                background-color: #545b62;
            }
            
            QCheckBox {
                color: #495057;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 3px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDMuNUw0IDZMMTEgMSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjwvc3ZnPgo=);
            }
            
            QGroupBox {
                font-weight: 600;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
            }
            
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: #f8f9fa;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #495057;
            }
        """)
    
    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header section
        self._create_header(main_layout)
        
        # Main form
        self._create_form(main_layout)
        
        # Loading widget
        self.loading_widget = LoadingWidget()
        main_layout.addWidget(self.loading_widget)
        
        # Info section
        self._create_info_section(main_layout)
        
        # Button section
        self._create_buttons(main_layout)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def _create_header(self, layout):
        """Create header section with logo and title"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # App title
        title_label = QLabel("XML Fiscal Manager Pro")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 5px;
            }
        """)
        
        # Subtitle
        subtitle_label = QLabel("Sistema Profissional de Gestão Fiscal")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6c757d;
                margin-bottom: 15px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
    
    def _create_form(self, layout):
        """Create the main form"""
        form_group = QGroupBox("Autenticação de Licença")
        form_layout = QVBoxLayout(form_group)
        form_layout.setContentsMargins(20, 25, 20, 20)
        form_layout.setSpacing(15)
        
        # License key input
        license_label = QLabel("Chave de Licença:")
        license_label.setStyleSheet("font-weight: 600; margin-bottom: 5px;")
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Digite sua chave de licença...")
        self.license_input.setFont(QFont("Courier New", 12))
        
        # Remember license checkbox
        self.remember_checkbox = QCheckBox("Lembrar desta licença")
        self.remember_checkbox.setChecked(self._load_saved_license())
        
        form_layout.addWidget(license_label)
        form_layout.addWidget(self.license_input)
        form_layout.addWidget(self.remember_checkbox)
        
        layout.addWidget(form_group)
    
    def _create_info_section(self, layout):
        """Create information section"""
        info_group = QGroupBox("Informações do Sistema")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(20, 25, 20, 20)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        
        # Get system info
        import platform
        import uuid
        
        system_info = f"""Versão: 2.0.0
Sistema: {platform.system()} {platform.version()}
Identificador da Máquina: {str(uuid.getnode())[:12]}...
Data/Hora: {self._get_current_datetime()}"""
        
        info_text.setPlainText(system_info)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
    
    def _create_buttons(self, layout):
        """Create button section"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Add stretch to center buttons
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("secondary")
        self.cancel_button.clicked.connect(self.reject)
        
        # Login button
        self.login_button = QPushButton("Autenticar")
        self.login_button.setObjectName("primary")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _setup_connections(self):
        """Setup signal connections"""
        # Enable/disable login button based on input
        self.license_input.textChanged.connect(self._validate_input)
        
        # Enter key handling
        self.license_input.returnPressed.connect(self.accept)
    
    def _validate_input(self):
        """Validate input and update UI state"""
        license_key = self.license_input.text().strip()
        
        # Basic validation
        is_valid = len(license_key) >= 10  # Minimum length
        
        self.login_button.setEnabled(is_valid)
        
        # Visual feedback
        if license_key and not is_valid:
            self.license_input.setStyleSheet(self.license_input.styleSheet() + "border-color: #dc3545;")
        else:
            # Reset style
            self.license_input.setStyleSheet("")
    
    def _load_saved_license(self) -> bool:
        """Load saved license if available"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("XMLFiscalManagerPro", "Auth")
            
            if settings.contains("remember_license") and settings.value("remember_license", False):
                saved_license = settings.value("saved_license", "")
                if saved_license:
                    self.license_input.setText(saved_license)
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error loading saved license: {e}")
            return False
    
    def _save_license(self):
        """Save license if remember is checked"""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("XMLFiscalManagerPro", "Auth")
            
            if self.remember_checkbox.isChecked():
                settings.setValue("remember_license", True)
                settings.setValue("saved_license", self.license_input.text().strip())
            else:
                settings.remove("remember_license")
                settings.remove("saved_license")
                
        except Exception as e:
            logging.error(f"Error saving license: {e}")
    
    def _get_current_datetime(self) -> str:
        """Get formatted current datetime"""
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    def _center_on_screen(self):
        """Center dialog on screen"""
        from PySide6.QtGui import QGuiApplication
        
        screen = QGuiApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        
        x = (screen.width() - dialog_geometry.width()) // 2
        y = (screen.height() - dialog_geometry.height()) // 2
        
        self.move(x, y)
    
    def set_loading(self, loading: bool, message: str = ""):
        """Set loading state"""
        if loading:
            self.loading_widget.show_loading(message)
            self.login_button.setEnabled(False)
            self.license_input.setEnabled(False)
        else:
            self.loading_widget.hide_loading()
            self.login_button.setEnabled(True)
            self.license_input.setEnabled(True)
            self._validate_input()  # Re-validate input
    
    def get_license_key(self) -> str:
        """Get entered license key"""
        return self.license_input.text().strip()
    
    def accept(self):
        """Override accept to save license"""
        self._save_license()
        super().accept()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Prevent escape key from closing dialog while loading
        if event.key() == Qt.Key_Escape and self.loading_widget.isVisible():
            return
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event"""
        # Prevent closing while loading
        if self.loading_widget.isVisible():
            event.ignore()
            return
        
        super().closeEvent(event) 