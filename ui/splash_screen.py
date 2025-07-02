#!/usr/bin/env python3
"""
Professional Splash Screen for XML Fiscal Manager Pro
Beautiful loading screen with progress indicators and branding
"""

import logging
import time
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QThread
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QLinearGradient, QBrush, 
    QPen, QRadialGradient, QFontMetrics
)
from PySide6.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout, QWidget


class LoadingWorker(QThread):
    """Worker thread for loading operations"""
    
    progress_updated = Signal(int, str)
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = [
            ("Inicializando sistema...", 200),
            ("Carregando configurações...", 300),
            ("Verificando dependências...", 400),
            ("Preparando interface...", 300),
            ("Configurando autenticação...", 500),
            ("Finalizando carregamento...", 300)
        ]
    
    def run(self):
        """Run loading simulation"""
        total_steps = len(self.tasks)
        
        for i, (task_name, duration) in enumerate(self.tasks):
            progress = int((i / total_steps) * 100)
            self.progress_updated.emit(progress, task_name)
            
            # Simulate work
            self.msleep(duration)
        
        # Complete
        self.progress_updated.emit(100, "Carregamento concluído!")
        self.msleep(200)
        self.finished.emit()


class ProfessionalSplashScreen(QSplashScreen):
    """Professional splash screen with modern design"""
    
    def __init__(self, app_version="2.0.0"):
        # Create a custom pixmap for the splash screen
        pixmap = self._create_splash_pixmap()
        super().__init__(pixmap)
        
        self.app_version = app_version
        self.current_message = "Iniciando..."
        self.progress_value = 0
        
        # Setup fonts
        self._setup_fonts()
        
        # Setup loading worker
        self.loading_worker = LoadingWorker()
        self.loading_worker.progress_updated.connect(self._update_progress)
        self.loading_worker.finished.connect(self.close)
        
        # Animation for fade effects
        self._setup_animations()
        
        # Set window properties
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def _create_splash_pixmap(self) -> QPixmap:
        """Create custom splash screen pixmap"""
        width, height = 600, 400
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(0, 123, 255))  # #007bff
        gradient.setColorAt(1, QColor(0, 86, 179))   # #0056b3
        
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        
        # Add subtle pattern overlay
        self._draw_pattern_overlay(painter, width, height)
        
        # Add company/product branding area
        self._draw_branding_area(painter, width, height)
        
        painter.end()
        return pixmap
    
    def _draw_pattern_overlay(self, painter: QPainter, width: int, height: int):
        """Draw subtle pattern overlay"""
        painter.save()
        
        # Semi-transparent overlay with geometric pattern
        overlay_color = QColor(255, 255, 255, 20)
        painter.setPen(QPen(overlay_color, 1))
        
        # Draw diagonal lines pattern
        spacing = 40
        for x in range(-height, width + height, spacing):
            painter.drawLine(x, 0, x + height, height)
        
        painter.restore()
    
    def _draw_branding_area(self, painter: QPainter, width: int, height: int):
        """Draw branding area with logo placeholder"""
        painter.save()
        
        # Logo area (placeholder - replace with actual logo)
        logo_rect_size = 80
        logo_x = (width - logo_rect_size) // 2
        logo_y = height // 3 - logo_rect_size // 2
        
        # Logo background circle
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(logo_x, logo_y, logo_rect_size, logo_rect_size)
        
        # Logo icon (XML symbol)
        painter.setPen(QPen(QColor(0, 123, 255), 4))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(logo_x, logo_y, logo_rect_size, logo_rect_size, 
                        Qt.AlignCenter, "XML")
        
        painter.restore()
    
    def _setup_fonts(self):
        """Setup fonts for different text elements"""
        self.title_font = QFont("Segoe UI", 20, QFont.Bold)
        self.subtitle_font = QFont("Segoe UI", 12, QFont.Normal)
        self.message_font = QFont("Segoe UI", 10, QFont.Normal)
        self.version_font = QFont("Segoe UI", 9, QFont.Normal)
    
    def _setup_animations(self):
        """Setup fade animations"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def show_with_fade(self):
        """Show splash screen with fade-in effect"""
        self.setWindowOpacity(0.0)
        self.show()
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def start_loading(self):
        """Start the loading process"""
        self.loading_worker.start()
    
    def _update_progress(self, progress: int, message: str):
        """Update progress and message"""
        self.progress_value = progress
        self.current_message = message
        self.repaint()
    
    def drawContents(self, painter: QPainter):
        """Override to draw custom content"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get dimensions
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Draw title
        self._draw_title(painter, width, height)
        
        # Draw subtitle
        self._draw_subtitle(painter, width, height)
        
        # Draw progress section
        self._draw_progress_section(painter, width, height)
        
        # Draw version info
        self._draw_version_info(painter, width, height)
    
    def _draw_title(self, painter: QPainter, width: int, height: int):
        """Draw main title"""
        painter.save()
        
        painter.setFont(self.title_font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        
        title_text = "XML Fiscal Manager Pro"
        title_y = height // 2 - 20
        
        # Add text shadow
        painter.setPen(QPen(QColor(0, 0, 0, 100)))
        painter.drawText(1, title_y + 1, width, 40, Qt.AlignCenter, title_text)
        
        # Draw main text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(0, title_y, width, 40, Qt.AlignCenter, title_text)
        
        painter.restore()
    
    def _draw_subtitle(self, painter: QPainter, width: int, height: int):
        """Draw subtitle"""
        painter.save()
        
        painter.setFont(self.subtitle_font)
        painter.setPen(QPen(QColor(255, 255, 255, 200)))
        
        subtitle_text = "Sistema Profissional de Gestão Fiscal"
        subtitle_y = height // 2 + 25
        
        painter.drawText(0, subtitle_y, width, 30, Qt.AlignCenter, subtitle_text)
        
        painter.restore()
    
    def _draw_progress_section(self, painter: QPainter, width: int, height: int):
        """Draw progress bar and message"""
        painter.save()
        
        # Progress bar area
        progress_y = height - 120
        progress_width = width - 100
        progress_x = 50
        progress_height = 8
        
        # Progress bar background
        bg_rect = painter.drawRoundedRect(progress_x, progress_y, progress_width, progress_height, 4, 4)
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, 
                        QBrush(QColor(255, 255, 255, 100)))
        
        # Progress bar fill
        if self.progress_value > 0:
            fill_width = int((self.progress_value / 100) * progress_width)
            painter.fillRect(progress_x, progress_y, fill_width, progress_height,
                           QBrush(QColor(255, 255, 255)))
        
        # Progress text
        painter.setFont(self.message_font)
        painter.setPen(QPen(QColor(255, 255, 255, 230)))
        
        message_y = progress_y + 25
        painter.drawText(0, message_y, width, 20, Qt.AlignCenter, self.current_message)
        
        # Progress percentage
        progress_text = f"{self.progress_value}%"
        painter.drawText(0, message_y + 20, width, 20, Qt.AlignCenter, progress_text)
        
        painter.restore()
    
    def _draw_version_info(self, painter: QPainter, width: int, height: int):
        """Draw version and copyright info"""
        painter.save()
        
        painter.setFont(self.version_font)
        painter.setPen(QPen(QColor(255, 255, 255, 150)))
        
        # Version
        version_text = f"Versão {self.app_version}"
        painter.drawText(10, height - 30, 200, 20, Qt.AlignLeft, version_text)
        
        # Copyright
        copyright_text = "© 2024 XML Fiscal Manager Pro"
        painter.drawText(width - 210, height - 30, 200, 20, Qt.AlignRight, copyright_text)
        
        painter.restore()
    
    def close_with_fade(self):
        """Close splash screen with fade-out effect"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
    
    def mousePressEvent(self, event):
        """Handle mouse press - allow click to speed up"""
        if self.loading_worker.isRunning():
            # Speed up loading on click
            self.loading_worker.terminate()
            self.loading_worker.wait()
            self._update_progress(100, "Carregamento acelerado!")
            QTimer.singleShot(300, self.close)
        
        super().mousePressEvent(event)


class SimpleSplashScreen(QSplashScreen):
    """Simplified splash screen for faster loading"""
    
    def __init__(self, message="Carregando...", app_version="2.0.0"):
        # Create simple pixmap
        pixmap = QPixmap(400, 200)
        pixmap.fill(QColor(0, 123, 255))
        
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        
        # Show message
        self.showMessage(
            f"XML Fiscal Manager Pro v{app_version}\n{message}",
            Qt.AlignCenter | Qt.AlignBottom,
            QColor(255, 255, 255)
        )
    
    def update_message(self, message: str):
        """Update splash message"""
        self.showMessage(
            f"XML Fiscal Manager Pro\n{message}",
            Qt.AlignCenter | Qt.AlignBottom,
            QColor(255, 255, 255)
        ) 