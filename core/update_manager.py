#!/usr/bin/env python3
"""
Update Manager for XML Fiscal Manager Pro
Handles automatic update checking from GitHub releases
"""

import json
import logging
import requests
import os
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from packaging import version
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication


class GitHubUpdateChecker(QThread):
    """Thread for checking GitHub updates"""
    
    update_available = Signal(dict)
    no_update = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, current_version: str, github_repo: str):
        super().__init__()
        self.current_version = current_version
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    
    def run(self):
        """Check for updates on GitHub"""
        try:
            logging.info(f"Checking for updates from: {self.api_url}")
            
            # Make request to GitHub API
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            
            # Extract version information
            latest_version = release_data.get('tag_name', '').lstrip('v')
            release_name = release_data.get('name', 'Nova Versão')
            release_notes = release_data.get('body', 'Sem notas de versão disponíveis.')
            download_url = None
            
            # Find the main download asset (usually a zip file)
            for asset in release_data.get('assets', []):
                if asset['name'].endswith(('.zip', '.exe', '.msi')):
                    download_url = asset['browser_download_url']
                    break
            
            # If no asset found, use the source code zip
            if not download_url:
                download_url = release_data.get('zipball_url')
            
            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                update_info = {
                    'version': latest_version,
                    'name': release_name,
                    'notes': release_notes,
                    'download_url': download_url,
                    'html_url': release_data.get('html_url', ''),
                    'published_at': release_data.get('published_at', ''),
                    'prerelease': release_data.get('prerelease', False)
                }
                self.update_available.emit(update_info)
            else:
                self.no_update.emit(f"Você está usando a versão mais recente ({self.current_version})")
                
        except requests.RequestException as e:
            self.error_occurred.emit(f"Erro de conexão: {str(e)}")
        except json.JSONDecodeError as e:
            self.error_occurred.emit(f"Erro ao processar resposta: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Erro inesperado: {str(e)}")
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings"""
        try:
            # Clean version strings (remove 'v' prefix and any suffixes)
            latest_clean = latest.split('-')[0].split('+')[0].lstrip('v')
            current_clean = current.split('-')[0].split('+')[0].lstrip('v')
            
            return version.parse(latest_clean) > version.parse(current_clean)
        except Exception as e:
            logging.error(f"Error comparing versions: {e}")
            return False


class UpdateDownloader(QThread):
    """Thread for downloading updates"""
    
    progress_updated = Signal(int, str)
    download_completed = Signal(str)
    download_failed = Signal(str)
    
    def __init__(self, download_url: str, filename: str):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.download_path = None
    
    def run(self):
        """Download the update file"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="xml_fiscal_update_")
            self.download_path = os.path.join(temp_dir, self.filename)
            
            self.progress_updated.emit(0, "Iniciando download...")
            
            # Download with progress
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.download_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_updated.emit(
                                progress, 
                                f"Baixando... {downloaded_size // 1024} KB / {total_size // 1024} KB"
                            )
            
            self.progress_updated.emit(100, "Download concluído!")
            self.download_completed.emit(self.download_path)
            
        except Exception as e:
            self.download_failed.emit(f"Erro no download: {str(e)}")


class UpdateManager(QObject):
    """Main update manager class"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.current_version = self.config.get('app_info.version', '2.0.0')
        self.github_repo = self.config.get('update_settings.github_repo', 'edineicruz/XML')
        self.auto_check = self.config.get('update_settings.auto_check', True)
        self.check_interval = self.config.get('update_settings.check_interval_hours', 24)
        
        self.checker_thread = None
        self.downloader_thread = None
    
    def check_for_updates(self, silent: bool = False) -> None:
        """Check for updates (can be silent or with UI)"""
        if self.checker_thread and self.checker_thread.isRunning():
            if not silent:
                QMessageBox.information(None, "Verificação em Andamento", 
                                      "Uma verificação de atualização já está em andamento.")
            return
        
        self.checker_thread = GitHubUpdateChecker(self.current_version, self.github_repo)
        self.checker_thread.update_available.connect(
            lambda info: self._handle_update_available(info, silent)
        )
        self.checker_thread.no_update.connect(
            lambda msg: self._handle_no_update(msg, silent)
        )
        self.checker_thread.error_occurred.connect(
            lambda error: self._handle_error(error, silent)
        )
        
        self.checker_thread.start()
    
    def _handle_update_available(self, update_info: Dict[str, Any], silent: bool):
        """Handle when an update is available"""
        if silent:
            # For silent checks, maybe just log or store for later notification
            logging.info(f"Update available: {update_info['version']}")
            self._show_update_notification(update_info)
        else:
            self._show_update_dialog(update_info)
    
    def _handle_no_update(self, message: str, silent: bool):
        """Handle when no update is available"""
        if not silent:
            QMessageBox.information(None, "Verificação de Atualizações", message)
    
    def _handle_error(self, error: str, silent: bool):
        """Handle update check errors"""
        logging.error(f"Update check failed: {error}")
        if not silent:
            QMessageBox.warning(None, "Erro na Verificação", 
                              f"Não foi possível verificar atualizações:\n{error}")
    
    def _show_update_notification(self, update_info: Dict[str, Any]):
        """Show a subtle notification about available update"""
        # This could be implemented as a system tray notification
        # or a status bar message in the main window
        logging.info(f"New version {update_info['version']} is available")
    
    def _show_update_dialog(self, update_info: Dict[str, Any]):
        """Show detailed update dialog"""
        from ui.update_dialog import UpdateDialog
        
        dialog = UpdateDialog(update_info, self.current_version)
        result = dialog.exec_()
        
        if result == QMessageBox.StandardButton.Yes:
            # User wants to download
            self._download_update(update_info)
        elif result == UpdateDialog.VISIT_GITHUB:
            # User wants to visit GitHub page
            import webbrowser
            webbrowser.open(update_info['html_url'])
    
    def _download_update(self, update_info: Dict[str, Any]):
        """Download the update"""
        if not update_info.get('download_url'):
            QMessageBox.warning(None, "Download Indisponível", 
                              "Link de download não disponível. Visite a página do GitHub.")
            return
        
        # Determine filename
        filename = f"XML_Fiscal_Manager_Pro_v{update_info['version']}.zip"
        
        # Create progress dialog
        progress_dialog = QProgressDialog("Baixando atualização...", "Cancelar", 0, 100)
        progress_dialog.setWindowTitle("Download de Atualização")
        progress_dialog.setModal(True)
        progress_dialog.setMinimumDuration(0)
        
        # Start download
        self.downloader_thread = UpdateDownloader(update_info['download_url'], filename)
        
        self.downloader_thread.progress_updated.connect(
            lambda progress, text: self._update_download_progress(progress_dialog, progress, text)
        )
        self.downloader_thread.download_completed.connect(
            lambda path: self._handle_download_completed(progress_dialog, path, update_info)
        )
        self.downloader_thread.download_failed.connect(
            lambda error: self._handle_download_failed(progress_dialog, error)
        )
        
        # Handle cancel
        progress_dialog.canceled.connect(self._cancel_download)
        
        self.downloader_thread.start()
        progress_dialog.show()
    
    def _update_download_progress(self, dialog, progress: int, text: str):
        """Update download progress"""
        dialog.setValue(progress)
        dialog.setLabelText(text)
        QApplication.processEvents()
    
    def _handle_download_completed(self, dialog, file_path: str, update_info: Dict[str, Any]):
        """Handle completed download"""
        dialog.close()
        
        reply = QMessageBox.question(
            None,
            "Download Concluído",
            f"A atualização foi baixada com sucesso!\n\n"
            f"Arquivo: {os.path.basename(file_path)}\n"
            f"Versão: {update_info['version']}\n\n"
            f"Deseja abrir a pasta onde o arquivo foi salvo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Open file location
            import subprocess
            import platform
            
            folder_path = os.path.dirname(file_path)
            
            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{file_path}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
    
    def _handle_download_failed(self, dialog, error: str):
        """Handle failed download"""
        dialog.close()
        QMessageBox.critical(None, "Erro no Download", 
                           f"Falha ao baixar a atualização:\n{error}")
    
    def _cancel_download(self):
        """Cancel the download"""
        if self.downloader_thread and self.downloader_thread.isRunning():
            self.downloader_thread.terminate()
            self.downloader_thread.wait()
    
    def should_check_automatically(self) -> bool:
        """Check if automatic update checking is due"""
        if not self.auto_check:
            return False
        
        from datetime import datetime, timedelta
        
        last_check = self.config.get('update_settings.last_check', '')
        if not last_check:
            return True
        
        try:
            last_check_time = datetime.fromisoformat(last_check)
            next_check_time = last_check_time + timedelta(hours=self.check_interval)
            return datetime.now() >= next_check_time
        except:
            return True
    
    def update_last_check_time(self):
        """Update the last check timestamp"""
        from datetime import datetime
        self.config.set('update_settings.last_check', datetime.now().isoformat())
        self.config.save_config()
    
    def get_update_settings(self) -> Dict[str, Any]:
        """Get current update settings"""
        return {
            'auto_check': self.auto_check,
            'check_interval_hours': self.check_interval,
            'github_repo': self.github_repo,
            'current_version': self.current_version
        }
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update settings"""
        self.auto_check = new_settings.get('auto_check', self.auto_check)
        self.check_interval = new_settings.get('check_interval_hours', self.check_interval)
        self.github_repo = new_settings.get('github_repo', self.github_repo)
        
        # Save to config
        self.config.set('update_settings.auto_check', self.auto_check)
        self.config.set('update_settings.check_interval_hours', self.check_interval)
        self.config.set('update_settings.github_repo', self.github_repo)
        self.config.save_config() 