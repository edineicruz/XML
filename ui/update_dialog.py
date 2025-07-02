#!/usr/bin/env python3
"""
Update Dialog for XML Fiscal Manager Pro
Modern dialog for displaying update information and options
"""

import logging
from typing import Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette


class UpdateDialog(QDialog):
    """Professional update notification dialog"""
    
    # Custom return codes
    VISIT_GITHUB = 100
    
    def __init__(self, update_info: Dict[str, Any], current_version: str, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        
        self.setWindowTitle("Atualização Disponível - XML Fiscal Manager Pro")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        self._setup_ui()
        self._apply_styles()
        self._center_on_screen()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header section
        self._create_header(layout)
        
        # Version information
        self._create_version_info(layout)
        
        # Release notes
        self._create_release_notes(layout)
        
        # Buttons
        self._create_buttons(layout)
    
    def _create_header(self, layout):
        """Create the header section"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon (you can add an update icon here)
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border-radius: 24px;
                color: #1976d2;
            }
        """)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel("Nova Versão Disponível!")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1976d2;")
        
        subtitle_label = QLabel("Uma atualização do XML Fiscal Manager Pro está disponível")
        subtitle_label.setFont(QFont("Segoe UI", 10))
        subtitle_label.setStyleSheet("color: #666666;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        text_layout.addStretch()
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(15)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
    
    def _create_version_info(self, layout):
        """Create version information section"""
        info_group = QGroupBox("Informações da Versão")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)
        
        # Current vs New version
        version_frame = QFrame()
        version_layout = QHBoxLayout(version_frame)
        version_layout.setContentsMargins(10, 10, 10, 10)
        
        # Current version
        current_layout = QVBoxLayout()
        current_label = QLabel("Versão Atual")
        current_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        current_label.setStyleSheet("color: #666666;")
        
        current_version_label = QLabel(self.current_version)
        current_version_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        current_version_label.setStyleSheet("color: #f57c00;")
        
        current_layout.addWidget(current_label)
        current_layout.addWidget(current_version_label)
        
        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        arrow_label.setStyleSheet("color: #4caf50;")
        arrow_label.setAlignment(Qt.AlignCenter)
        
        # New version
        new_layout = QVBoxLayout()
        new_label = QLabel("Nova Versão")
        new_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        new_label.setStyleSheet("color: #666666;")
        
        new_version_label = QLabel(self.update_info['version'])
        new_version_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        new_version_label.setStyleSheet("color: #4caf50;")
        
        new_layout.addWidget(new_label)
        new_layout.addWidget(new_version_label)
        
        version_layout.addLayout(current_layout)
        version_layout.addStretch()
        version_layout.addWidget(arrow_label)
        version_layout.addStretch()
        version_layout.addLayout(new_layout)
        
        version_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        info_layout.addWidget(version_frame)
        
        # Release name and date
        if self.update_info.get('name'):
            name_label = QLabel(f"📦 {self.update_info['name']}")
            name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            name_label.setStyleSheet("color: #333333; margin: 5px 0;")
            info_layout.addWidget(name_label)
        
        if self.update_info.get('published_at'):
            try:
                from datetime import datetime
                pub_date = datetime.fromisoformat(self.update_info['published_at'].replace('Z', '+00:00'))
                date_str = pub_date.strftime("%d/%m/%Y às %H:%M")
                date_label = QLabel(f"📅 Publicado em: {date_str}")
                date_label.setFont(QFont("Segoe UI", 9))
                date_label.setStyleSheet("color: #666666;")
                info_layout.addWidget(date_label)
            except:
                pass
        
        layout.addWidget(info_group)
    
    def _create_release_notes(self, layout):
        """Create release notes section"""
        notes_group = QGroupBox("Novidades e Melhorias")
        notes_layout = QVBoxLayout(notes_group)
        
        # Scroll area for notes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        notes_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Format release notes
        release_notes = self.update_info.get('notes', 'Sem notas de versão disponíveis.')
        if not release_notes.strip():
            release_notes = 'Sem notas de versão disponíveis.'
        
        # Convert markdown-style formatting to basic HTML
        formatted_notes = self._format_release_notes(release_notes)
        notes_text.setHtml(formatted_notes)
        
        notes_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 10pt;
                padding: 10px;
            }
        """)
        
        scroll_area.setWidget(notes_text)
        notes_layout.addWidget(scroll_area)
        
        layout.addWidget(notes_group)
    
    def _format_release_notes(self, notes: str) -> str:
        """Format release notes for display"""
        # Basic markdown to HTML conversion
        formatted = notes.replace('\n', '<br>')
        
        # Headers
        formatted = formatted.replace('### ', '<h4>')
        formatted = formatted.replace('## ', '<h3>')
        formatted = formatted.replace('# ', '<h2>')
        
        # Bold and italic
        import re
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted)
        formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted)
        
        # Lists
        formatted = re.sub(r'^- (.*?)$', r'• \1', formatted, flags=re.MULTILINE)
        
        return f"<div style='line-height: 1.4;'>{formatted}</div>"
    
    def _create_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Later button
        later_btn = QPushButton("Lembrar Depois")
        later_btn.setFixedSize(130, 35)
        later_btn.clicked.connect(self.reject)
        later_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 6px;
                font-weight: bold;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #eeeeee;
                border-color: #aaaaaa;
            }
        """)
        
        # Visit GitHub button
        github_btn = QPushButton("Ver no GitHub")
        github_btn.setFixedSize(130, 35)
        github_btn.clicked.connect(self._visit_github)
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
        # Download button
        download_btn = QPushButton("Baixar Agora")
        download_btn.setFixedSize(130, 35)
        download_btn.clicked.connect(self.accept)
        download_btn.setDefault(True)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # Check if download is available
        if not self.update_info.get('download_url'):
            download_btn.setEnabled(False)
            download_btn.setText("Download Indisponível")
            download_btn.setToolTip("Link de download não disponível para esta versão")
        
        button_layout.addStretch()
        button_layout.addWidget(later_btn)
        button_layout.addWidget(github_btn)
        button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)
    
    def _visit_github(self):
        """Handle visit GitHub button"""
        self.done(self.VISIT_GITHUB)
    
    def _apply_styles(self):
        """Apply dialog styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #333333;
            }
        """)
    
    def _center_on_screen(self):
        """Center dialog on screen"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        x = (screen.width() - dialog_geometry.width()) // 2
        y = (screen.height() - dialog_geometry.height()) // 2
        self.move(x, y) 