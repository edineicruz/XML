#!/usr/bin/env python3
"""
XML Fiscal Manager Pro - Main Application Entry Point
Professional XML fiscal document management system with subscription-based licensing

Author: Auditoria Notebook Team
Version: 2.0.0
License: Commercial - Subscription Based
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient

from core.config_manager import ConfigManager
from core.auth_manager import AuthManager
from core.database_manager import DatabaseManager
from core.update_manager import UpdateManager
from ui.main_window import MainWindow
from ui.splash_screen import ProfessionalSplashScreen
from utils.logger import setup_logging


class XMLFiscalManagerApp:
    """Main application class"""
    
    def __init__(self):
        self.app = None
        self.config = None
        self.auth_manager = None
        self.db_manager = None
        self.update_manager = None
        self.main_window = None
        
    def initialize(self):
        """Initialize application components"""
        try:
            # Setup logging
            setup_logging()
            logging.info("Starting XML Fiscal Manager Pro v2.0.0")
            
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("XML Fiscal Manager Pro")
            self.app.setApplicationVersion("2.0.0")
            self.app.setOrganizationName("Auditoria Notebook")
            self.app.setOrganizationDomain("auditorianotebook.com")
            
            # Load configuration
            self.config = ConfigManager()
            
            # Initialize update manager
            self.update_manager = UpdateManager(self.config)
            
            # Initialize authentication
            self.auth_manager = AuthManager(self.config)
            
            # Verify subscription on startup
            if not self.auth_manager.auto_validate_subscription():
                logging.warning("Subscription validation failed, exiting application")
                sys.exit(1)
            
            # Initialize database
            self.db_manager = DatabaseManager(self.config)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            if self.app:
                QMessageBox.critical(None, "Erro de Inicialização", 
                                   f"Falha ao inicializar a aplicação:\n{str(e)}")
            return False
    
    def authenticate(self):
        """Handle user authentication"""
        try:
            # Check for saved credentials
            if self.auth_manager.has_valid_session():
                return True
            
            # Show authentication dialog
            return self.auth_manager.authenticate()
            
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            QMessageBox.critical(None, "Erro de Autenticação", 
                               f"Falha na autenticação:\n{str(e)}")
            return False
    
    def show_splash(self):
        """Show splash screen during initialization"""
        try:
            splash = ProfessionalSplashScreen()
            splash.show()
            
            # Process events to show splash
            self.app.processEvents()
            
            # Simulate loading process
            import time
            for i in range(101):
                splash._update_progress(i, f"Carregando componentes... {i}%")
                self.app.processEvents()
                time.sleep(0.02)  # Simulate work
            
            splash.close()
            
        except Exception as e:
            logging.error(f"Error showing splash screen: {e}")
    
    def check_for_updates_on_startup(self):
        """Check for updates automatically on startup if enabled"""
        try:
            if self.update_manager.should_check_automatically():
                logging.info("Performing automatic update check on startup")
                self.update_manager.check_for_updates(silent=True)
                self.update_manager.update_last_check_time()
            else:
                logging.info("Automatic update check skipped (not due yet or disabled)")
        except Exception as e:
            logging.error(f"Error during startup update check: {e}")
    
    def run(self):
        """Main application run method"""
        try:
            # Initialize application
            if not self.initialize():
                return 1
            
            # Show splash screen
            self.show_splash()
            
            # Authenticate user
            if not self.authenticate():
                logging.info("Authentication cancelled or failed")
                return 1
            
            # Create and show main window
            self.main_window = MainWindow(
                config=self.config,
                auth_manager=self.auth_manager,
                db_manager=self.db_manager,
                update_manager=self.update_manager
            )
            
            self.main_window.show()
            
            # Setup application icon
            if os.path.exists("assets/icon.ico"):
                self.app.setWindowIcon(self.main_window.windowIcon())
            
            # Check for updates after the main window is shown
            QTimer.singleShot(2000, self.check_for_updates_on_startup)
            
            # Run application
            logging.info("Application started successfully")
            return self.app.exec()
            
        except Exception as e:
            logging.error(f"Application runtime error: {e}")
            QMessageBox.critical(None, "Erro da Aplicação", 
                               f"Erro durante execução:\n{str(e)}")
            return 1
        
        finally:
            # Cleanup
            if self.db_manager:
                self.db_manager.close()
            logging.info("Application shutdown complete")


def main():
    """Main entry point"""
    try:
        app = XMLFiscalManagerApp()
        return app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
        
    except Exception as e:
        print(f"Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 