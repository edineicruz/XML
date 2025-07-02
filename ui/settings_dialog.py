#!/usr/bin/env python3
"""
Settings Dialog for XML Fiscal Manager Pro
Configure application settings including database, export, and UI options
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QSpinBox, QFileDialog, QMessageBox, QGridLayout,
    QFormLayout, QDialogButtonBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging


class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.settings = config.get_all_settings()
        
        self._setup_dialog()
        self._create_tabs()
        self._create_buttons()
        self._load_settings()
    
    def _setup_dialog(self):
        """Setup dialog properties"""
        self.setWindowTitle("Configurações")
        self.setModal(True)
        self.resize(600, 500)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
    
    def _create_tabs(self):
        """Create settings tabs"""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create individual tabs
        self._create_general_tab()
        self._create_database_tab()
        self._create_export_tab()
        self._create_ui_tab()
        self._create_advanced_tab()
    
    def _create_general_tab(self):
        """Create general settings tab"""
        general_widget = QFrame()
        layout = QVBoxLayout(general_widget)
        
        # Application settings
        app_group = QGroupBox("Configurações Gerais")
        app_layout = QFormLayout(app_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        app_layout.addRow("Nível de Log:", self.log_level_combo)
        
        self.auto_backup_check = QCheckBox("Backup automático do banco de dados")
        app_layout.addRow(self.auto_backup_check)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setSuffix(" dias")
        app_layout.addRow("Intervalo de backup:", self.backup_interval_spin)
        
        self.max_backup_files_spin = QSpinBox()
        self.max_backup_files_spin.setRange(1, 100)
        app_layout.addRow("Máximo de arquivos de backup:", self.max_backup_files_spin)
        
        layout.addWidget(app_group)
        
        # Processing settings
        processing_group = QGroupBox("Processamento")
        processing_layout = QFormLayout(processing_group)
        
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 16)
        processing_layout.addRow("Máximo de threads:", self.max_threads_spin)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 1000)
        processing_layout.addRow("Tamanho do lote:", self.batch_size_spin)
        
        self.validate_xml_check = QCheckBox("Validar XML durante importação")
        processing_layout.addRow(self.validate_xml_check)
        
        self.strict_validation_check = QCheckBox("Validação rigorosa de esquema")
        processing_layout.addRow(self.strict_validation_check)
        
        layout.addWidget(processing_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(general_widget, "Geral")
    
    def _create_database_tab(self):
        """Create database settings tab"""
        db_widget = QFrame()
        layout = QVBoxLayout(db_widget)
        
        # Database settings
        db_group = QGroupBox("Configurações do Banco de Dados")
        db_layout = QFormLayout(db_group)
        
        # Database path
        db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_path_browse_btn = QPushButton("Procurar...")
        db_path_browse_btn.clicked.connect(self._browse_db_path)
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(db_path_browse_btn)
        db_layout.addRow("Caminho do banco:", db_path_layout)
        
        self.connection_timeout_spin = QSpinBox()
        self.connection_timeout_spin.setRange(5, 300)
        self.connection_timeout_spin.setSuffix(" segundos")
        db_layout.addRow("Timeout de conexão:", self.connection_timeout_spin)
        
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 50)
        db_layout.addRow("Máximo de conexões:", self.max_connections_spin)
        
        self.enable_wal_check = QCheckBox("Habilitar WAL mode (recomendado)")
        db_layout.addRow(self.enable_wal_check)
        
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(1000, 100000)
        self.cache_size_spin.setSuffix(" KB")
        db_layout.addRow("Tamanho do cache:", self.cache_size_spin)
        
        layout.addWidget(db_group)
        
        # Maintenance settings
        maintenance_group = QGroupBox("Manutenção")
        maintenance_layout = QFormLayout(maintenance_group)
        
        self.auto_vacuum_check = QCheckBox("Vacuum automático")
        maintenance_layout.addRow(self.auto_vacuum_check)
        
        self.vacuum_interval_spin = QSpinBox()
        self.vacuum_interval_spin.setRange(1, 90)
        self.vacuum_interval_spin.setSuffix(" dias")
        maintenance_layout.addRow("Intervalo do vacuum:", self.vacuum_interval_spin)
        
        self.analyze_db_check = QCheckBox("Analisar estatísticas automaticamente")
        maintenance_layout.addRow(self.analyze_db_check)
        
        layout.addWidget(maintenance_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(db_widget, "Banco de Dados")
    
    def _create_export_tab(self):
        """Create export settings tab"""
        export_widget = QFrame()
        layout = QVBoxLayout(export_widget)
        
        # Export settings
        export_group = QGroupBox("Configurações de Exportação")
        export_layout = QFormLayout(export_group)
        
        # Default export path
        export_path_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        export_path_browse_btn = QPushButton("Procurar...")
        export_path_browse_btn.clicked.connect(self._browse_export_path)
        export_path_layout.addWidget(self.export_path_edit)
        export_path_layout.addWidget(export_path_browse_btn)
        export_layout.addRow("Pasta padrão:", export_path_layout)
        
        self.default_format_combo = QComboBox()
        self.default_format_combo.addItems(["Excel (.xlsx)", "CSV", "JSON"])
        export_layout.addRow("Formato padrão:", self.default_format_combo)
        
        self.include_header_check = QCheckBox("Incluir cabeçalho nos arquivos")
        export_layout.addRow(self.include_header_check)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["DD/MM/AAAA", "AAAA-MM-DD", "MM/DD/AAAA"])
        export_layout.addRow("Formato de data:", self.date_format_combo)
        
        self.decimal_separator_combo = QComboBox()
        self.decimal_separator_combo.addItems([",", "."])
        export_layout.addRow("Separador decimal:", self.decimal_separator_combo)
        
        layout.addWidget(export_group)
        
        # Excel specific settings
        excel_group = QGroupBox("Configurações do Excel")
        excel_layout = QFormLayout(excel_group)
        
        self.excel_password_check = QCheckBox("Proteger arquivo com senha")
        excel_layout.addRow(self.excel_password_check)
        
        self.excel_autofit_check = QCheckBox("Ajustar largura das colunas automaticamente")
        excel_layout.addRow(self.excel_autofit_check)
        
        self.excel_freeze_header_check = QCheckBox("Congelar linha de cabeçalho")
        excel_layout.addRow(self.excel_freeze_header_check)
        
        layout.addWidget(excel_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(export_widget, "Exportação")
    
    def _create_ui_tab(self):
        """Create UI settings tab"""
        ui_widget = QFrame()
        layout = QVBoxLayout(ui_widget)
        
        # Appearance settings
        appearance_group = QGroupBox("Aparência")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Escuro", "Sistema"])
        appearance_layout.addRow("Tema:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        appearance_layout.addRow("Tamanho da fonte:", self.font_size_spin)
        
        self.show_tooltips_check = QCheckBox("Mostrar dicas de ferramentas")
        appearance_layout.addRow(self.show_tooltips_check)
        
        self.show_status_bar_check = QCheckBox("Mostrar barra de status")
        appearance_layout.addRow(self.show_status_bar_check)
        
        layout.addWidget(appearance_group)
        
        # Window settings
        window_group = QGroupBox("Janela")
        window_layout = QFormLayout(window_group)
        
        self.remember_size_check = QCheckBox("Lembrar tamanho da janela")
        window_layout.addRow(self.remember_size_check)
        
        self.center_on_screen_check = QCheckBox("Centralizar ao iniciar")
        window_layout.addRow(self.center_on_screen_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimizar para bandeja do sistema")
        window_layout.addRow(self.minimize_to_tray_check)
        
        self.start_maximized_check = QCheckBox("Iniciar maximizada")
        window_layout.addRow(self.start_maximized_check)
        
        layout.addWidget(window_group)
        
        # Table settings
        table_group = QGroupBox("Tabelas")
        table_layout = QFormLayout(table_group)
        
        self.rows_per_page_spin = QSpinBox()
        self.rows_per_page_spin.setRange(10, 1000)
        table_layout.addRow("Linhas por página:", self.rows_per_page_spin)
        
        self.alternate_row_colors_check = QCheckBox("Cores alternadas nas linhas")
        table_layout.addRow(self.alternate_row_colors_check)
        
        self.auto_resize_columns_check = QCheckBox("Redimensionar colunas automaticamente")
        table_layout.addRow(self.auto_resize_columns_check)
        
        layout.addWidget(table_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(ui_widget, "Interface")
    
    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        advanced_widget = QFrame()
        layout = QVBoxLayout(advanced_widget)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(128, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addRow("Limite de memória:", self.memory_limit_spin)
        
        self.cache_enabled_check = QCheckBox("Habilitar cache em memória")
        performance_layout.addRow(self.cache_enabled_check)
        
        self.preload_data_check = QCheckBox("Pré-carregar dados na inicialização")
        performance_layout.addRow(self.preload_data_check)
        
        self.lazy_loading_check = QCheckBox("Carregamento sob demanda")
        performance_layout.addRow(self.lazy_loading_check)
        
        layout.addWidget(performance_group)
        
        # Security settings
        security_group = QGroupBox("Segurança")
        security_layout = QFormLayout(security_group)
        
        self.encrypt_exports_check = QCheckBox("Criptografar exportações")
        security_layout.addRow(self.encrypt_exports_check)
        
        self.session_timeout_spin = QSpinBox()
        self.session_timeout_spin.setRange(5, 480)
        self.session_timeout_spin.setSuffix(" minutos")
        security_layout.addRow("Timeout da sessão:", self.session_timeout_spin)
        
        self.audit_log_check = QCheckBox("Log de auditoria")
        security_layout.addRow(self.audit_log_check)
        
        layout.addWidget(security_group)
        
        # Debug settings
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_mode_check = QCheckBox("Modo de debug")
        debug_layout.addRow(self.debug_mode_check)
        
        self.verbose_logging_check = QCheckBox("Log detalhado")
        debug_layout.addRow(self.verbose_logging_check)
        
        self.save_temp_files_check = QCheckBox("Manter arquivos temporários")
        debug_layout.addRow(self.save_temp_files_check)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(advanced_widget, "Avançado")
    
    def _create_buttons(self):
        """Create dialog buttons"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults,
            Qt.Horizontal, self
        )
        
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        
        self.main_layout.addWidget(buttons)
    
    def _load_settings(self):
        """Load current settings into UI"""
        try:
            # General settings
            general = self.settings.get('general', {})
            self.log_level_combo.setCurrentText(general.get('log_level', 'INFO'))
            self.auto_backup_check.setChecked(general.get('auto_backup', True))
            self.backup_interval_spin.setValue(general.get('backup_interval_days', 7))
            self.max_backup_files_spin.setValue(general.get('max_backup_files', 10))
            
            # Processing settings
            processing = self.settings.get('processing', {})
            self.max_threads_spin.setValue(processing.get('max_threads', 4))
            self.batch_size_spin.setValue(processing.get('batch_size', 100))
            self.validate_xml_check.setChecked(processing.get('validate_xml', True))
            self.strict_validation_check.setChecked(processing.get('strict_validation', False))
            
            # Database settings
            database = self.settings.get('database', {})
            self.db_path_edit.setText(database.get('path', ''))
            self.connection_timeout_spin.setValue(database.get('timeout', 30))
            self.max_connections_spin.setValue(database.get('max_connections', 10))
            self.enable_wal_check.setChecked(database.get('enable_wal', True))
            self.cache_size_spin.setValue(database.get('cache_size', 10000))
            self.auto_vacuum_check.setChecked(database.get('auto_vacuum', True))
            self.vacuum_interval_spin.setValue(database.get('vacuum_interval_days', 30))
            self.analyze_db_check.setChecked(database.get('analyze_stats', True))
            
            # Export settings
            export = self.settings.get('export', {})
            self.export_path_edit.setText(export.get('default_path', ''))
            self.default_format_combo.setCurrentText(export.get('default_format', 'Excel (.xlsx)'))
            self.include_header_check.setChecked(export.get('include_header', True))
            self.date_format_combo.setCurrentText(export.get('date_format', 'DD/MM/AAAA'))
            self.decimal_separator_combo.setCurrentText(export.get('decimal_separator', ','))
            self.excel_password_check.setChecked(export.get('excel_password_protect', False))
            self.excel_autofit_check.setChecked(export.get('excel_autofit_columns', True))
            self.excel_freeze_header_check.setChecked(export.get('excel_freeze_header', True))
            
            # UI settings
            ui = self.settings.get('ui', {})
            appearance = ui.get('appearance', {})
            self.theme_combo.setCurrentText(appearance.get('theme', 'Claro'))
            self.font_size_spin.setValue(appearance.get('font_size', 10))
            self.show_tooltips_check.setChecked(appearance.get('show_tooltips', True))
            self.show_status_bar_check.setChecked(appearance.get('show_status_bar', True))
            
            startup = ui.get('startup', {})
            self.remember_size_check.setChecked(startup.get('remember_size', True))
            self.center_on_screen_check.setChecked(startup.get('center_on_screen', True))
            self.minimize_to_tray_check.setChecked(startup.get('minimize_to_tray', False))
            self.start_maximized_check.setChecked(startup.get('start_maximized', False))
            
            table = ui.get('table', {})
            self.rows_per_page_spin.setValue(table.get('rows_per_page', 100))
            self.alternate_row_colors_check.setChecked(table.get('alternate_row_colors', True))
            self.auto_resize_columns_check.setChecked(table.get('auto_resize_columns', True))
            
            # Advanced settings
            advanced = self.settings.get('advanced', {})
            performance = advanced.get('performance', {})
            self.memory_limit_spin.setValue(performance.get('memory_limit_mb', 512))
            self.cache_enabled_check.setChecked(performance.get('cache_enabled', True))
            self.preload_data_check.setChecked(performance.get('preload_data', False))
            self.lazy_loading_check.setChecked(performance.get('lazy_loading', True))
            
            security = advanced.get('security', {})
            self.encrypt_exports_check.setChecked(security.get('encrypt_exports', False))
            self.session_timeout_spin.setValue(security.get('session_timeout_minutes', 60))
            self.audit_log_check.setChecked(security.get('audit_log', True))
            
            debug = advanced.get('debug', {})
            self.debug_mode_check.setChecked(debug.get('debug_mode', False))
            self.verbose_logging_check.setChecked(debug.get('verbose_logging', False))
            self.save_temp_files_check.setChecked(debug.get('save_temp_files', False))
            
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Aviso", "Erro ao carregar configurações. Usando padrões.")
    
    def _save_settings(self):
        """Save settings and accept dialog"""
        try:
            # Build new settings dictionary
            new_settings = {
                'general': {
                    'log_level': self.log_level_combo.currentText(),
                    'auto_backup': self.auto_backup_check.isChecked(),
                    'backup_interval_days': self.backup_interval_spin.value(),
                    'max_backup_files': self.max_backup_files_spin.value()
                },
                'processing': {
                    'max_threads': self.max_threads_spin.value(),
                    'batch_size': self.batch_size_spin.value(),
                    'validate_xml': self.validate_xml_check.isChecked(),
                    'strict_validation': self.strict_validation_check.isChecked()
                },
                'database': {
                    'path': self.db_path_edit.text(),
                    'timeout': self.connection_timeout_spin.value(),
                    'max_connections': self.max_connections_spin.value(),
                    'enable_wal': self.enable_wal_check.isChecked(),
                    'cache_size': self.cache_size_spin.value(),
                    'auto_vacuum': self.auto_vacuum_check.isChecked(),
                    'vacuum_interval_days': self.vacuum_interval_spin.value(),
                    'analyze_stats': self.analyze_db_check.isChecked()
                },
                'export': {
                    'default_path': self.export_path_edit.text(),
                    'default_format': self.default_format_combo.currentText(),
                    'include_header': self.include_header_check.isChecked(),
                    'date_format': self.date_format_combo.currentText(),
                    'decimal_separator': self.decimal_separator_combo.currentText(),
                    'excel_password_protect': self.excel_password_check.isChecked(),
                    'excel_autofit_columns': self.excel_autofit_check.isChecked(),
                    'excel_freeze_header': self.excel_freeze_header_check.isChecked()
                },
                'ui': {
                    'appearance': {
                        'theme': self.theme_combo.currentText(),
                        'font_size': self.font_size_spin.value(),
                        'show_tooltips': self.show_tooltips_check.isChecked(),
                        'show_status_bar': self.show_status_bar_check.isChecked()
                    },
                    'startup': {
                        'remember_size': self.remember_size_check.isChecked(),
                        'center_on_screen': self.center_on_screen_check.isChecked(),
                        'minimize_to_tray': self.minimize_to_tray_check.isChecked(),
                        'start_maximized': self.start_maximized_check.isChecked()
                    },
                    'table': {
                        'rows_per_page': self.rows_per_page_spin.value(),
                        'alternate_row_colors': self.alternate_row_colors_check.isChecked(),
                        'auto_resize_columns': self.auto_resize_columns_check.isChecked()
                    }
                },
                'advanced': {
                    'performance': {
                        'memory_limit_mb': self.memory_limit_spin.value(),
                        'cache_enabled': self.cache_enabled_check.isChecked(),
                        'preload_data': self.preload_data_check.isChecked(),
                        'lazy_loading': self.lazy_loading_check.isChecked()
                    },
                    'security': {
                        'encrypt_exports': self.encrypt_exports_check.isChecked(),
                        'session_timeout_minutes': self.session_timeout_spin.value(),
                        'audit_log': self.audit_log_check.isChecked()
                    },
                    'debug': {
                        'debug_mode': self.debug_mode_check.isChecked(),
                        'verbose_logging': self.verbose_logging_check.isChecked(),
                        'save_temp_files': self.save_temp_files_check.isChecked()
                    }
                }
            }
            
            # Save settings
            if self.config.update_settings(new_settings):
                QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar configurações!")
            
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações:\n{str(e)}")
    
    def _restore_defaults(self):
        """Restore default settings"""
        reply = QMessageBox.question(
            self, "Confirmar",
            "Tem certeza que deseja restaurar as configurações padrão?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.config.reset_to_defaults()
                self.settings = self.config.get_all_settings()
                self._load_settings()
                QMessageBox.information(self, "Sucesso", "Configurações restauradas!")
            except Exception as e:
                logging.error(f"Error restoring defaults: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao restaurar configurações:\n{str(e)}")
    
    def _browse_db_path(self):
        """Browse for database path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Selecionar Arquivo do Banco de Dados",
            self.db_path_edit.text(),
            "SQLite Database (*.db *.sqlite);;All Files (*)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def _browse_export_path(self):
        """Browse for export path"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Exportação",
            self.export_path_edit.text()
        )
        
        if folder_path:
            self.export_path_edit.setText(folder_path) 