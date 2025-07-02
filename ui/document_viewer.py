#!/usr/bin/env python3
"""
Document Viewer Dialog for XML Fiscal Manager Pro
Professional document viewing with XML content display and metadata
"""

import logging
import json
from typing import Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTextEdit, QLabel, QGroupBox, QGridLayout, QPushButton,
    QScrollArea, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QTextOption, QIcon


class DocumentViewer(QDialog):
    """Professional document viewer dialog"""
    
    def __init__(self, document: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.document = document
        self.setup_ui()
        self.load_document_data()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle(f"Visualizar Documento - {self.document.get('document_number', 'N/A')}")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        # Center the dialog
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                font-weight: 600;
            }
            
            QGroupBox {
                font-weight: 600;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton#secondary {
                background-color: #6c757d;
            }
            
            QPushButton#secondary:hover {
                background-color: #545b62;
            }
            
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
            
            QTreeWidget, QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #f1f3f4;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                border: none;
                border-right: 1px solid #dee2e6;
                font-weight: 600;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Document header
        header_group = self.create_header_section()
        layout.addWidget(header_group)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_overview_tab()
        self.create_details_tab()
        self.create_items_tab()
        self.create_xml_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Exportar PDF")
        export_btn.clicked.connect(self.export_pdf)
        button_layout.addWidget(export_btn)
        
        copy_btn = QPushButton("Copiar Dados")
        copy_btn.setObjectName("secondary")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Fechar")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_header_section(self):
        """Create document header section"""
        group = QGroupBox("Informações do Documento")
        layout = QGridLayout(group)
        
        # Document basic info
        layout.addWidget(QLabel("Tipo:"), 0, 0)
        type_label = QLabel(self.document.get('document_type', 'N/A').upper())
        type_label.setStyleSheet("font-weight: bold; color: #007bff;")
        layout.addWidget(type_label, 0, 1)
        
        layout.addWidget(QLabel("Número:"), 0, 2)
        number_label = QLabel(self.document.get('document_number', 'N/A'))
        number_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(number_label, 0, 3)
        
        layout.addWidget(QLabel("Data:"), 0, 4)
        layout.addWidget(QLabel(self.document.get('issue_date', 'N/A')), 0, 5)
        
        layout.addWidget(QLabel("Chave de Acesso:"), 1, 0)
        key_label = QLabel(self.document.get('access_key', 'N/A'))
        key_label.setFont(QFont("Consolas", 9))
        layout.addWidget(key_label, 1, 1, 1, 5)
        
        return group
    
    def create_overview_tab(self):
        """Create overview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create splitter for two columns
        splitter = QSplitter(Qt.Horizontal)
        
        # Left column - Parties
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Issuer info
        issuer_group = QGroupBox("Emitente")
        issuer_layout = QGridLayout(issuer_group)
        
        issuer_fields = [
            ("Nome:", self.document.get('issuer_name', 'N/A')),
            ("CNPJ:", self.document.get('cnpj_issuer', 'N/A')),
            ("Endereço:", self.document.get('issuer_address', 'N/A')),
            ("Município:", self.document.get('issuer_city', 'N/A')),
            ("UF:", self.document.get('issuer_state', 'N/A')),
            ("CEP:", self.document.get('issuer_zip', 'N/A'))
        ]
        
        for i, (label, value) in enumerate(issuer_fields):
            issuer_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            issuer_layout.addWidget(value_label, i, 1)
        
        left_layout.addWidget(issuer_group)
        
        # Recipient info
        recipient_group = QGroupBox("Destinatário")
        recipient_layout = QGridLayout(recipient_group)
        
        recipient_fields = [
            ("Nome:", self.document.get('recipient_name', 'N/A')),
            ("CNPJ/CPF:", self.document.get('cnpj_recipient', 'N/A')),
            ("Endereço:", self.document.get('recipient_address', 'N/A')),
            ("Município:", self.document.get('recipient_city', 'N/A')),
            ("UF:", self.document.get('recipient_state', 'N/A')),
            ("CEP:", self.document.get('recipient_zip', 'N/A'))
        ]
        
        for i, (label, value) in enumerate(recipient_fields):
            recipient_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            recipient_layout.addWidget(value_label, i, 1)
        
        left_layout.addWidget(recipient_group)
        left_layout.addStretch()
        
        # Right column - Financial
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Financial info
        financial_group = QGroupBox("Informações Financeiras")
        financial_layout = QGridLayout(financial_group)
        
        financial_fields = [
            ("Valor Total:", f"R$ {self.document.get('total_value', 0):,.2f}"),
            ("Base de Cálculo ICMS:", f"R$ {self.document.get('icms_base', 0):,.2f}"),
            ("Valor ICMS:", f"R$ {self.document.get('icms_value', 0):,.2f}"),
            ("Base de Cálculo ICMS ST:", f"R$ {self.document.get('icms_st_base', 0):,.2f}"),
            ("Valor ICMS ST:", f"R$ {self.document.get('icms_st_value', 0):,.2f}"),
            ("Valor IPI:", f"R$ {self.document.get('ipi_value', 0):,.2f}"),
            ("Valor PIS:", f"R$ {self.document.get('pis_value', 0):,.2f}"),
            ("Valor COFINS:", f"R$ {self.document.get('cofins_value', 0):,.2f}"),
            ("Total de Impostos:", f"R$ {self.document.get('tax_value', 0):,.2f}")
        ]
        
        for i, (label, value) in enumerate(financial_fields):
            financial_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold; color: #28a745;")
            financial_layout.addWidget(value_label, i, 1)
        
        right_layout.addWidget(financial_group)
        
        # Transport info (if available)
        transport_group = QGroupBox("Informações de Transporte")
        transport_layout = QGridLayout(transport_group)
        
        transport_fields = [
            ("Modalidade:", self.document.get('transport_mode', 'N/A')),
            ("Transportadora:", self.document.get('carrier_name', 'N/A')),
            ("CNPJ Transportadora:", self.document.get('carrier_cnpj', 'N/A')),
            ("Veículo:", self.document.get('vehicle_plate', 'N/A')),
            ("Peso Bruto:", f"{self.document.get('gross_weight', 0):.3f} kg"),
            ("Peso Líquido:", f"{self.document.get('net_weight', 0):.3f} kg")
        ]
        
        for i, (label, value) in enumerate(transport_fields):
            transport_layout.addWidget(QLabel(label), i, 0)
            transport_layout.addWidget(QLabel(str(value)), i, 1)
        
        right_layout.addWidget(transport_group)
        right_layout.addStretch()
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([50, 50])
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(widget, "Resumo")
    
    def create_details_tab(self):
        """Create details tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Details as tree view
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["Campo", "Valor"])
        self.details_tree.setAlternatingRowColors(True)
        
        # Populate tree with all document data
        self.populate_details_tree()
        
        layout.addWidget(self.details_tree)
        
        self.tab_widget.addTab(widget, "Detalhes")
    
    def create_items_tab(self):
        """Create items tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Items table
        self.items_table = QTableWidget()
        headers = [
            "Item", "Código", "Descrição", "NCM", "CFOP", 
            "Unidade", "Quantidade", "Valor Unit.", "Valor Total"
        ]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSortingEnabled(True)
        
        # Auto-resize columns
        header = self.items_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers) - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Populate items
        self.populate_items_table()
        
        layout.addWidget(self.items_table)
        
        self.tab_widget.addTab(widget, "Itens")
    
    def create_xml_tab(self):
        """Create XML content tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # XML content viewer
        self.xml_viewer = QTextEdit()
        self.xml_viewer.setReadOnly(True)
        self.xml_viewer.setFont(QFont("Consolas", 10))
        self.xml_viewer.setWordWrapMode(QTextOption.NoWrap)
        
        # Load XML content if available
        xml_content = self.document.get('xml_content', '')
        if xml_content:
            self.xml_viewer.setPlainText(xml_content)
        else:
            self.xml_viewer.setPlainText("Conteúdo XML não disponível")
        
        layout.addWidget(self.xml_viewer)
        
        self.tab_widget.addTab(widget, "XML")
    
    def load_document_data(self):
        """Load document data into the interface"""
        # This method can be expanded to load additional data
        # from external sources if needed
        pass
    
    def populate_details_tree(self):
        """Populate details tree with document data"""
        # Group data by categories
        categories = {
            "Documento": {
                "ID": self.document.get('id', 'N/A'),
                "Tipo": self.document.get('document_type', 'N/A'),
                "Número": self.document.get('document_number', 'N/A'),
                "Série": self.document.get('series', 'N/A'),
                "Data de Emissão": self.document.get('issue_date', 'N/A'),
                "Chave de Acesso": self.document.get('access_key', 'N/A'),
                "Status": self.document.get('status', 'N/A')
            },
            "Emitente": {
                "Nome": self.document.get('issuer_name', 'N/A'),
                "CNPJ": self.document.get('cnpj_issuer', 'N/A'),
                "Inscrição Estadual": self.document.get('issuer_ie', 'N/A'),
                "Endereço": self.document.get('issuer_address', 'N/A'),
                "Município": self.document.get('issuer_city', 'N/A'),
                "UF": self.document.get('issuer_state', 'N/A'),
                "CEP": self.document.get('issuer_zip', 'N/A')
            },
            "Destinatário": {
                "Nome": self.document.get('recipient_name', 'N/A'),
                "CNPJ/CPF": self.document.get('cnpj_recipient', 'N/A'),
                "Inscrição Estadual": self.document.get('recipient_ie', 'N/A'),
                "Endereço": self.document.get('recipient_address', 'N/A'),
                "Município": self.document.get('recipient_city', 'N/A'),
                "UF": self.document.get('recipient_state', 'N/A'),
                "CEP": self.document.get('recipient_zip', 'N/A')
            },
            "Valores": {
                "Valor Total": f"R$ {self.document.get('total_value', 0):,.2f}",
                "Base ICMS": f"R$ {self.document.get('icms_base', 0):,.2f}",
                "Valor ICMS": f"R$ {self.document.get('icms_value', 0):,.2f}",
                "Valor IPI": f"R$ {self.document.get('ipi_value', 0):,.2f}",
                "Valor PIS": f"R$ {self.document.get('pis_value', 0):,.2f}",
                "Valor COFINS": f"R$ {self.document.get('cofins_value', 0):,.2f}",
                "Total Impostos": f"R$ {self.document.get('tax_value', 0):,.2f}"
            }
        }
        
        for category_name, fields in categories.items():
            category_item = QTreeWidgetItem([category_name, ""])
            category_item.setFont(0, QFont("", 10, QFont.Bold))
            
            for field_name, value in fields.items():
                field_item = QTreeWidgetItem([field_name, str(value)])
                category_item.addChild(field_item)
            
            self.details_tree.addTopLevelItem(category_item)
            category_item.setExpanded(True)
        
        # Auto-resize columns
        self.details_tree.resizeColumnToContents(0)
    
    def populate_items_table(self):
        """Populate items table"""
        items = self.document.get('items', [])
        
        if not items:
            # Show message if no items
            self.items_table.setRowCount(1)
            item = QTableWidgetItem("Nenhum item encontrado")
            item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(0, 0, item)
            self.items_table.setSpan(0, 0, 1, self.items_table.columnCount())
            return
        
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item.get('item_number', row + 1))))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get('code', 'N/A')))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('description', 'N/A')))
            self.items_table.setItem(row, 3, QTableWidgetItem(item.get('ncm', 'N/A')))
            self.items_table.setItem(row, 4, QTableWidgetItem(item.get('cfop', 'N/A')))
            self.items_table.setItem(row, 5, QTableWidgetItem(item.get('unit', 'N/A')))
            self.items_table.setItem(row, 6, QTableWidgetItem(f"{item.get('quantity', 0):,.3f}"))
            self.items_table.setItem(row, 7, QTableWidgetItem(f"R$ {item.get('unit_value', 0):,.2f}"))
            self.items_table.setItem(row, 8, QTableWidgetItem(f"R$ {item.get('total_value', 0):,.2f}"))
    
    def export_pdf(self):
        """Export document to PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar PDF", 
                f"documento_{self.document.get('document_number', 'unknown')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Here you would implement PDF generation
                # For now, just show a message
                QMessageBox.information(self, "Exportar PDF", 
                                      "Funcionalidade de exportação para PDF será implementada em breve.")
                
        except Exception as e:
            logging.error(f"Error exporting PDF: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF:\n{str(e)}")
    
    def copy_to_clipboard(self):
        """Copy document data to clipboard"""
        try:
            # Create a formatted text representation
            text_data = f"""DOCUMENTO FISCAL
Tipo: {self.document.get('document_type', 'N/A').upper()}
Número: {self.document.get('document_number', 'N/A')}
Data: {self.document.get('issue_date', 'N/A')}
Chave: {self.document.get('access_key', 'N/A')}

EMITENTE
Nome: {self.document.get('issuer_name', 'N/A')}
CNPJ: {self.document.get('cnpj_issuer', 'N/A')}

DESTINATÁRIO
Nome: {self.document.get('recipient_name', 'N/A')}
CNPJ/CPF: {self.document.get('cnpj_recipient', 'N/A')}

VALORES
Valor Total: R$ {self.document.get('total_value', 0):,.2f}
Total Impostos: R$ {self.document.get('tax_value', 0):,.2f}
"""
            
            clipboard = QApplication.clipboard()
            clipboard.setText(text_data)
            
            QMessageBox.information(self, "Copiado", "Dados copiados para a área de transferência!")
            
        except Exception as e:
            logging.error(f"Error copying to clipboard: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao copiar dados:\n{str(e)}") 