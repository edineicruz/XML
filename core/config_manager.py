#!/usr/bin/env python3
"""
Configuration Manager for XML Fiscal Manager Pro
Handles all application configuration including user preferences and system settings
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from PySide6.QtCore import QSettings


class ConfigManager:
    """Advanced configuration management system"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.settings = QSettings("XMLFiscalManagerPro", "Settings")
        self._config_data = {}
        self._default_config = self._get_default_config()
        
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "app_info": {
                "name": "XML Fiscal Manager Pro",
                "version": "2.0.0",
                "organization": "Auditoria Notebook",
                "description": "Sistema profissional de gerenciamento de XMLs fiscais",
                "license_type": "subscription",
                "support_email": "suporte@auditorianotebook.com"
            },
            "authentication": {
                "google_sheets_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQr8ajoftgS1iffF9NpQqZzUu-s5xkrawGLLUm6KWk9CZ2KVz6UreNpoV2L_5mQm55ydAxMdqb6aWFo/edit?gid=0#gid=0",
                "license_validation": True,
                "auto_login": False,
                "session_timeout": 8,  # hours
                "max_login_attempts": 3,
                "password_encryption": True,
                "remember_license": True,
                "auto_logout_on_idle": True,
                "idle_timeout_minutes": 30
            },
            "update_settings": {
                "auto_check": True,
                "check_interval_hours": 24,
                "github_repo": "edineicruz/XML",
                "notify_beta": False,
                "auto_download": False,
                "last_check": "",
                "dismissed_versions": []
            },
            "ui_settings": {
                "theme": "modern_dark",
                "language": "pt_BR",
                "window_size": {
                    "width": 1400,
                    "height": 900
                },
                "window_position": {
                    "x": 100,
                    "y": 100
                },
                "auto_save_settings": True,
                "show_splash": True,
                "animations_enabled": True,
                "toolbar_style": "modern",
                "grid_style": "alternating"
            },
            "xml_processing": {
                "supported_formats": ["nfe", "nfce", "cte", "nfse", "mdfe"],
                "validation_enabled": True,
                "auto_backup": True,
                "backup_folder": "./backups",
                "max_file_size_mb": 50,
                "parallel_processing": True,
                "max_threads": 4,
                "auto_detect_encoding": True,
                "preserve_original": True
            },
            "export_settings": {
                "default_format": "xlsx",
                "include_timestamp": True,
                "auto_open_file": False,
                "compression_enabled": True,
                "include_charts": True,
                "custom_templates": [],
                "watermark_enabled": True,
                "password_protect": False
            },
            "database": {
                "use_local_db": True,
                "db_file": "xml_fiscal_data.db",
                "auto_cleanup_days": 90,
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "compression_enabled": True,
                "encryption_enabled": False,
                "max_db_size_mb": 1000
            },
            "performance": {
                "cache_enabled": True,
                "cache_size_mb": 256,
                "preload_data": True,
                "lazy_loading": True,
                "memory_limit_mb": 2048,
                "gc_interval": 60  # seconds
            },
            "security": {
                "audit_logging": True,
                "data_encryption": False,
                "secure_delete": True,
                "access_logging": True,
                "session_encryption": True
            },
            "integrations": {
                "sefaz_integration": True,
                "api_timeout": 30,
                "retry_attempts": 3,
                "rate_limit": 10,  # requests per minute
                "proxy_enabled": False,
                "proxy_settings": {
                    "host": "",
                    "port": 8080,
                    "username": "",
                    "password": ""
                }
            },
            "notifications": {
                "enabled": True,
                "show_system_notifications": True,
                "email_notifications": False,
                "email_settings": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "use_tls": True
                }
            },
            "customization": {
                "custom_fields": [],
                "custom_reports": [],
                "custom_filters": [],
                "plugins_enabled": True,
                "plugin_directory": "./plugins"
            },
            "startup": {
                "remember_size": True,
                "center_on_screen": True,
                "minimize_to_tray": False,
                "start_maximized": True
            }
        }
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge with defaults
                self._config_data = self._merge_configs(self._default_config, file_config)
            else:
                self._config_data = self._default_config.copy()
                self.save_config()
                
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self._config_data = self._default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Merge user config with default config"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'ui_settings.theme')"""
        try:
            keys = key_path.split('.')
            value = self._config_data
            
            for key in keys:
                value = value[key]
                
            return value
            
        except KeyError:
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        try:
            keys = key_path.split('.')
            config = self._config_data
            
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            config[keys[-1]] = value
            
            if self.get('ui_settings.auto_save_settings', True):
                self.save_config()
                
        except Exception as e:
            logging.error(f"Error setting config value: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config_data.get(section, {})
    
    def update_section(self, section: str, data: Dict[str, Any]):
        """Update entire configuration section"""
        if section in self._config_data:
            self._config_data[section].update(data)
        else:
            self._config_data[section] = data
            
        if self.get('ui_settings.auto_save_settings', True):
            self.save_config()
    
    def reset_to_defaults(self, section: Optional[str] = None):
        """Reset configuration to defaults"""
        if section:
            if section in self._default_config:
                self._config_data[section] = self._default_config[section].copy()
        else:
            self._config_data = self._default_config.copy()
            
        self.save_config()
    
    def export_config(self, file_path: str):
        """Export configuration to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=4, ensure_ascii=False)
            return True
            
        except Exception as e:
            logging.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate and merge
            self._config_data = self._merge_configs(self._default_config, imported_config)
            self.save_config()
            return True
            
        except Exception as e:
            logging.error(f"Error importing config: {e}")
            return False
    
    def validate_config(self) -> Dict[str, str]:
        """Validate current configuration and return errors"""
        errors = {}
        
        # Validate authentication settings
        auth_config = self.get_section('authentication')
        if not auth_config.get('google_sheets_url'):
            errors['authentication.google_sheets_url'] = "URL da planilha do Google é obrigatória"
        
        # Validate UI settings
        ui_config = self.get_section('ui_settings')
        window_size = ui_config.get('window_size', {})
        if window_size.get('width', 0) < 800:
            errors['ui_settings.window_size.width'] = "Largura mínima da janela é 800px"
        if window_size.get('height', 0) < 600:
            errors['ui_settings.window_size.height'] = "Altura mínima da janela é 600px"
        
        # Validate database settings
        db_config = self.get_section('database')
        if db_config.get('auto_cleanup_days', 0) < 1:
            errors['database.auto_cleanup_days'] = "Período de limpeza deve ser pelo menos 1 dia"
        
        return errors
    
    def get_app_info(self) -> Dict[str, str]:
        """Get application information"""
        return self.get_section('app_info')
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return self.get_section('authentication')
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get_section('ui_settings')
    
    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get_section('database')
    
    def get_export_config(self) -> Dict[str, Any]:
        """Get export configuration"""
        return self.get_section('export_settings')
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        feature_map = {
            'animations': 'ui_settings.animations_enabled',
            'auto_backup': 'xml_processing.auto_backup',
            'validation': 'xml_processing.validation_enabled',
            'notifications': 'notifications.enabled',
            'audit_logging': 'security.audit_logging',
            'plugins': 'customization.plugins_enabled'
        }
        
        return self.get(feature_map.get(feature, feature), False)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return self._config_data.copy()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update multiple settings at once"""
        try:
            # Merge new settings with existing ones
            for section, settings in new_settings.items():
                if section in self._config_data:
                    if isinstance(self._config_data[section], dict) and isinstance(settings, dict):
                        self._config_data[section].update(settings)
                    else:
                        self._config_data[section] = settings
                else:
                    self._config_data[section] = settings
            
            self.save_config()
            return True
            
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
            return False 