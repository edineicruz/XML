#!/usr/bin/env python3
"""
XML Models for XML Fiscal Manager Pro
Define document models and their specific processing logic
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import re
from lxml import etree


class XMLModel(ABC):
    """Base class for XML document models"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Model name/identifier"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable model name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Model description"""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Model icon name"""
        pass
    
    @property
    @abstractmethod
    def color(self) -> str:
        """Model color (CSS color)"""
        pass
    
    @property
    @abstractmethod
    def patterns(self) -> List[str]:
        """Regex patterns to identify this document type"""
        pass
    
    @abstractmethod
    def get_sql_schema(self) -> Dict[str, str]:
        """Return SQL schema for this model"""
        pass
    
    @abstractmethod
    def get_extraction_rules(self) -> Dict[str, str]:
        """Return XPath extraction rules"""
        pass
    
    @abstractmethod
    def process_document(self, xml_content: str, file_path: Path) -> Dict[str, Any]:
        """Process XML document and extract data"""
        pass
    
    @abstractmethod
    def get_display_fields(self) -> List[Dict[str, str]]:
        """Return fields for UI display"""
        pass
    
    def matches_document(self, xml_content: str) -> bool:
        """Check if this model matches the given XML document"""
        try:
            content_lower = xml_content.lower()
            for pattern in self.patterns:
                if re.search(pattern.lower(), content_lower):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error matching document: {e}")
            return False


class NFEModel(XMLModel):
    """Model for NFe (Nota Fiscal Eletrônica) documents"""
    
    @property
    def name(self) -> str:
        return "nfe"
    
    @property
    def display_name(self) -> str:
        return "NFe - Nota Fiscal Eletrônica"
    
    @property
    def description(self) -> str:
        return "Nota Fiscal Eletrônica de produtos"
    
    @property
    def icon(self) -> str:
        return "📄"
    
    @property
    def color(self) -> str:
        return "#28a745"  # Green
    
    @property
    def patterns(self) -> List[str]:
        return [
            r'<infNFe',
            r'xmlns.*nfe',
            r'mod>55</mod',
            r'procnfe'
        ]
    
    def get_sql_schema(self) -> Dict[str, str]:
        """SQL schema for NFe documents - compatible with DatabaseManager structure"""
        return {
            'nfe_documents': '''
                CREATE TABLE IF NOT EXISTS nfe_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    access_key TEXT,
                    nfe_number TEXT,
                    series TEXT,
                    model TEXT,
                    emission_date TEXT,
                    FOREIGN KEY (document_id) REFERENCES xml_documents (id)
                )
            ''',
            'nfe_items': '''
                CREATE TABLE IF NOT EXISTS nfe_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    item_number TEXT,
                    item_code TEXT,
                    item_description TEXT,
                    ncm_code TEXT,
                    quantity REAL DEFAULT 0,
                    unit_value REAL DEFAULT 0,
                    total_value REAL DEFAULT 0,
                    FOREIGN KEY (document_id) REFERENCES xml_documents (id)
                )
            '''
        }
    
    def get_extraction_rules(self) -> Dict[str, str]:
        """XPath extraction rules for NFe"""
        return {
            'access_key': "//nfe:protNFe/nfe:infProt/nfe:chNFe/text() | //*[@Id[contains(., 'NFe')]]/@Id",
            'document_number': "//nfe:infNFe/nfe:ide/nfe:nNF/text()",
            'series': "//nfe:infNFe/nfe:ide/nfe:serie/text()",
            'model': "//nfe:infNFe/nfe:ide/nfe:mod/text()",
            'issue_date': "//nfe:infNFe/nfe:ide/nfe:dhEmi/text()",
            'operation_nature': "//nfe:infNFe/nfe:ide/nfe:natOp/text()",
            'cnpj_issuer': "//nfe:infNFe/nfe:emit/nfe:CNPJ/text()",
            'issuer_name': "//nfe:infNFe/nfe:emit/nfe:xNome/text()",
            'cnpj_recipient': "//nfe:infNFe/nfe:dest/nfe:CNPJ/text() | //nfe:infNFe/nfe:dest/nfe:CPF/text()",
            'recipient_name': "//nfe:infNFe/nfe:dest/nfe:xNome/text()",
            'total_value': "//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF/text()",
            'icms_value': "//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vICMS/text()",
            'items': "//nfe:infNFe/nfe:det"
        }
    
    def process_document(self, xml_content: str, file_path: Path) -> Dict[str, Any]:
        """Process NFe document and extract data compatible with DatabaseManager"""
        try:
            # Parse XML
            tree = etree.fromstring(xml_content.encode() if isinstance(xml_content, str) else xml_content)
            
            # Define namespaces
            namespaces = {
                'nfe': 'http://www.portalfiscal.inf.br/nfe'
            }
            
            def safe_xpath(xpath: str, default: str = '') -> str:
                try:
                    result = tree.xpath(xpath, namespaces=namespaces)
                    if result:
                        return str(result[0]).strip() if hasattr(result[0], 'strip') else str(result[0])
                    return default
                except Exception:
                    return default
            
            def safe_float(value: str, default: float = 0.0) -> float:
                try:
                    return float(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            # Extract basic document data compatible with xml_documents table
            document_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_hash': '',  # Will be calculated by DatabaseManager
                'document_type': 'nfe',
                'document_number': safe_xpath("//nfe:infNFe/nfe:ide/nfe:nNF/text()"),
                'series': safe_xpath("//nfe:infNFe/nfe:ide/nfe:serie/text()"),
                'model': safe_xpath("//nfe:infNFe/nfe:ide/nfe:mod/text()"),
                'issue_date': safe_xpath("//nfe:infNFe/nfe:ide/nfe:dhEmi/text()"),
                'access_key': safe_xpath("//nfe:protNFe/nfe:infProt/nfe:chNFe/text()") or 
                             safe_xpath("//*[@Id[contains(., 'NFe')]]/@Id").replace('NFe', ''),
                'operation_nature': safe_xpath("//nfe:infNFe/nfe:ide/nfe:natOp/text()"),
                
                # Issuer information
                'cnpj_issuer': safe_xpath("//nfe:infNFe/nfe:emit/nfe:CNPJ/text()"),
                'issuer_name': safe_xpath("//nfe:infNFe/nfe:emit/nfe:xNome/text()"),
                'emitter_fantasy': safe_xpath("//nfe:infNFe/nfe:emit/nfe:xFant/text()"),
                'emitter_ie': safe_xpath("//nfe:infNFe/nfe:emit/nfe:IE/text()"),
                'emitter_address': safe_xpath("//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:xLgr/text()"),
                'emitter_city': safe_xpath("//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:xMun/text()"),
                'emitter_state': safe_xpath("//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:UF/text()"),
                'emitter_cep': safe_xpath("//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:CEP/text()"),
                
                # Recipient information
                'cnpj_recipient': safe_xpath("//nfe:infNFe/nfe:dest/nfe:CNPJ/text()") or 
                                safe_xpath("//nfe:infNFe/nfe:dest/nfe:CPF/text()"),
                'recipient_name': safe_xpath("//nfe:infNFe/nfe:dest/nfe:xNome/text()"),
                'recipient_ie': safe_xpath("//nfe:infNFe/nfe:dest/nfe:IE/text()"),
                'recipient_address': safe_xpath("//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:xLgr/text()"),
                'recipient_city': safe_xpath("//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:xMun/text()"),
                'recipient_state': safe_xpath("//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:UF/text()"),
                'recipient_cep': safe_xpath("//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:CEP/text()"),
                
                # Financial totals
                'total_products': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vProd/text()")),
                'total_freight': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vFrete/text()")),
                'total_insurance': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vSeg/text()")),
                'total_discount': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vDesc/text()")),
                'total_other': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vOutro/text()")),
                'total_nfe': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF/text()")),
                'total_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF/text()")),
                
                # Tax information
                'icms_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vICMS/text()")),
                'ipi_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vIPI/text()")),
                'pis_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vPIS/text()")),
                'cofins_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vCOFINS/text()")),
                'icms_st_value': safe_float(safe_xpath("//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vST/text()")),
                
                # Transport information
                'transport_modality': safe_xpath("//nfe:infNFe/nfe:transp/nfe:modFrete/text()"),
                'transporter_name': safe_xpath("//nfe:infNFe/nfe:transp/nfe:transporta/nfe:xNome/text()"),
                
                # Payment information
                'payment_method': safe_xpath("//nfe:infNFe/nfe:pag/nfe:detPag/nfe:tPag/text()"),
                
                # Additional information
                'additional_info': safe_xpath("//nfe:infNFe/nfe:infAdic/nfe:infCpl/text()"),
                'protocol_number': safe_xpath("//nfe:protNFe/nfe:infProt/nfe:nProt/text()"),
                'protocol_date': safe_xpath("//nfe:protNFe/nfe:infProt/nfe:dhRecbto/text()"),
                
                # Status
                'status': 'active'
            }
            
            # Calculate tax_value
            document_data['tax_value'] = (
                document_data['icms_value'] + 
                document_data['ipi_value'] + 
                document_data['pis_value'] + 
                document_data['cofins_value']
            )
            
            # Extract items
            items = []
            try:
                item_nodes = tree.xpath("//nfe:infNFe/nfe:det", namespaces=namespaces)
                for i, item_node in enumerate(item_nodes, 1):
                    item_data = {
                        'item_number': str(i),
                        'item_code': safe_xpath(".//nfe:prod/nfe:cProd/text()", '') if item_node is not None else '',
                        'item_description': safe_xpath(".//nfe:prod/nfe:xProd/text()", '') if item_node is not None else '',
                        'ncm_code': safe_xpath(".//nfe:prod/nfe:NCM/text()", '') if item_node is not None else '',
                        'cfop': safe_xpath(".//nfe:prod/nfe:CFOP/text()", '') if item_node is not None else '',
                        'commercial_unit': safe_xpath(".//nfe:prod/nfe:uCom/text()", '') if item_node is not None else '',
                        'quantity': safe_float(safe_xpath(".//nfe:prod/nfe:qCom/text()", '0') if item_node is not None else '0'),
                        'unit_value': safe_float(safe_xpath(".//nfe:prod/nfe:vUnCom/text()", '0') if item_node is not None else '0'),
                        'total_value': safe_float(safe_xpath(".//nfe:prod/nfe:vProd/text()", '0') if item_node is not None else '0'),
                        'icms_value': safe_float(safe_xpath(".//nfe:imposto/nfe:ICMS//nfe:vICMS/text()", '0') if item_node is not None else '0'),
                        'ipi_value': safe_float(safe_xpath(".//nfe:imposto/nfe:IPI//nfe:vIPI/text()", '0') if item_node is not None else '0'),
                        'pis_value': safe_float(safe_xpath(".//nfe:imposto/nfe:PIS//nfe:vPIS/text()", '0') if item_node is not None else '0'),
                        'cofins_value': safe_float(safe_xpath(".//nfe:imposto/nfe:COFINS//nfe:vCOFINS/text()", '0') if item_node is not None else '0')
                    }
                    items.append(item_data)
            except Exception as e:
                self.logger.warning(f"Error extracting items: {e}")
            
            document_data['items'] = items
            
            return document_data
            
        except Exception as e:
            self.logger.error(f"Error processing NFe document: {e}")
            raise
    
    def get_display_fields(self) -> List[Dict[str, str]]:
        """Fields for UI display"""
        return [
            {'name': 'document_number', 'label': 'Número da NFe', 'type': 'text'},
            {'name': 'series', 'label': 'Série', 'type': 'text'},
            {'name': 'issue_date', 'label': 'Data de Emissão', 'type': 'date'},
            {'name': 'issuer_name', 'label': 'Emitente', 'type': 'text'},
            {'name': 'recipient_name', 'label': 'Destinatário', 'type': 'text'},
            {'name': 'total_value', 'label': 'Valor Total', 'type': 'currency'},
            {'name': 'access_key', 'label': 'Chave de Acesso', 'type': 'text'}
        ]


class NFCEModel(XMLModel):
    """Model for NFCe (Nota Fiscal de Consumidor Eletrônica) documents"""
    
    @property
    def name(self) -> str:
        return "nfce"
    
    @property
    def display_name(self) -> str:
        return "NFCe - Nota Fiscal de Consumidor Eletrônica"
    
    @property
    def description(self) -> str:
        return "Nota Fiscal de Consumidor Eletrônica"
    
    @property
    def icon(self) -> str:
        return "🧾"
    
    @property
    def color(self) -> str:
        return "#007bff"  # Blue
    
    @property
    def patterns(self) -> List[str]:
        return [
            r'<infNFe',
            r'mod>65</mod',
            r'nfce',
            r'procnfce'
        ]
    
    def get_sql_schema(self) -> Dict[str, str]:
        """SQL schema for NFCe documents"""
        return {
            'nfce_documents': '''
                CREATE TABLE IF NOT EXISTS nfce_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    access_key TEXT,
                    nfce_number TEXT,
                    series TEXT,
                    qr_code TEXT,
                    FOREIGN KEY (document_id) REFERENCES xml_documents (id)
                )
            '''
        }
    
    def get_extraction_rules(self) -> Dict[str, str]:
        """XPath extraction rules for NFCe"""
        return {
            'access_key': "//nfe:protNFe/nfe:infProt/nfe:chNFe/text() | //*[@Id[contains(., 'NFe')]]/@Id",
            'document_number': "//nfe:infNFe/nfe:ide/nfe:nNF/text()",
            'series': "//nfe:infNFe/nfe:ide/nfe:serie/text()",
            'qr_code': "//nfe:infNFeSupl/nfe:qrCode/text()"
        }
    
    def process_document(self, xml_content: str, file_path: Path) -> Dict[str, Any]:
        """Process NFCe document - reuse NFe logic with model adjustment"""
        nfe_model = NFEModel()
        document_data = nfe_model.process_document(xml_content, file_path)
        document_data['document_type'] = 'nfce'
        return document_data
    
    def get_display_fields(self) -> List[Dict[str, str]]:
        """Fields for UI display"""
        return [
            {'name': 'document_number', 'label': 'Número da NFCe', 'type': 'text'},
            {'name': 'series', 'label': 'Série', 'type': 'text'},
            {'name': 'issue_date', 'label': 'Data de Emissão', 'type': 'date'},
            {'name': 'issuer_name', 'label': 'Emitente', 'type': 'text'},
            {'name': 'total_value', 'label': 'Valor Total', 'type': 'currency'},
            {'name': 'access_key', 'label': 'Chave de Acesso', 'type': 'text'}
        ]


class CTEModel(XMLModel):
    """Model for CTe (Conhecimento de Transporte Eletrônico) documents"""
    
    @property
    def name(self) -> str:
        return "cte"
    
    @property
    def display_name(self) -> str:
        return "CTe - Conhecimento de Transporte Eletrônico"
    
    @property
    def description(self) -> str:
        return "Conhecimento de Transporte Eletrônico"
    
    @property
    def icon(self) -> str:
        return "🚛"
    
    @property
    def color(self) -> str:
        return "#ffc107"  # Yellow
    
    @property
    def patterns(self) -> List[str]:
        return [
            r'<infCte',
            r'xmlns.*cte',
            r'proccte',
            r'conhecimento.*transporte'
        ]
    
    def get_sql_schema(self) -> Dict[str, str]:
        """SQL schema for CTe documents"""
        return {
            'cte_documents': '''
                CREATE TABLE IF NOT EXISTS cte_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    access_key TEXT,
                    cte_number TEXT,
                    modal TEXT,
                    service_type TEXT,
                    FOREIGN KEY (document_id) REFERENCES xml_documents (id)
                )
            '''
        }
    
    def get_extraction_rules(self) -> Dict[str, str]:
        """XPath extraction rules for CTe"""
        return {
            'access_key': "//cte:protCTe/cte:infProt/cte:chCTe/text()",
            'document_number': "//cte:infCte/cte:ide/cte:nCT/text()",
            'modal': "//cte:infCte/cte:ide/cte:modal/text()",
            'service_type': "//cte:infCte/cte:ide/cte:tpServ/text()"
        }
    
    def process_document(self, xml_content: str, file_path: Path) -> Dict[str, Any]:
        """Process CTe document"""
        try:
            tree = etree.fromstring(xml_content.encode() if isinstance(xml_content, str) else xml_content)
            
            namespaces = {
                'cte': 'http://www.portalfiscal.inf.br/cte'
            }
            
            def safe_xpath(xpath: str, default: str = '') -> str:
                try:
                    result = tree.xpath(xpath, namespaces=namespaces)
                    return str(result[0]).strip() if result else default
                except Exception:
                    return default
            
            def safe_float(value: str, default: float = 0.0) -> float:
                try:
                    return float(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            document_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_hash': '',
                'document_type': 'cte',
                'document_number': safe_xpath("//cte:infCte/cte:ide/cte:nCT/text()"),
                'series': safe_xpath("//cte:infCte/cte:ide/cte:serie/text()"),
                'model': safe_xpath("//cte:infCte/cte:ide/cte:mod/text()"),
                'issue_date': safe_xpath("//cte:infCte/cte:ide/cte:dhEmi/text()"),
                'access_key': safe_xpath("//cte:protCTe/cte:infProt/cte:chCTe/text()"),
                'operation_nature': safe_xpath("//cte:infCte/cte:ide/cte:natOp/text()"),
                
                # Emitter information
                'cnpj_issuer': safe_xpath("//cte:infCte/cte:emit/cte:CNPJ/text()"),
                'issuer_name': safe_xpath("//cte:infCte/cte:emit/cte:xNome/text()"),
                'emitter_ie': safe_xpath("//cte:infCte/cte:emit/cte:IE/text()"),
                
                # Recipient information  
                'cnpj_recipient': safe_xpath("//cte:infCte/cte:dest/cte:CNPJ/text()"),
                'recipient_name': safe_xpath("//cte:infCte/cte:dest/cte:xNome/text()"),
                
                # Service values
                'total_value': safe_float(safe_xpath("//cte:infCte/cte:vPrest/cte:vTPrest/text()")),
                'tax_value': safe_float(safe_xpath("//cte:infCte/cte:imp/cte:ICMS//cte:vICMS/text()")),
                
                # Transport information
                'transport_modality': safe_xpath("//cte:infCte/cte:ide/cte:modal/text()"),
                
                'status': 'active'
            }
            
            return document_data
            
        except Exception as e:
            self.logger.error(f"Error processing CTe document: {e}")
            raise
    
    def get_display_fields(self) -> List[Dict[str, str]]:
        """Fields for UI display"""
        return [
            {'name': 'document_number', 'label': 'Número do CTe', 'type': 'text'},
            {'name': 'series', 'label': 'Série', 'type': 'text'},
            {'name': 'issue_date', 'label': 'Data de Emissão', 'type': 'date'},
            {'name': 'issuer_name', 'label': 'Emitente', 'type': 'text'},
            {'name': 'recipient_name', 'label': 'Destinatário', 'type': 'text'},
            {'name': 'total_value', 'label': 'Valor Total', 'type': 'currency'},
            {'name': 'transport_modality', 'label': 'Modal de Transporte', 'type': 'text'}
        ]


class NFSEModel(XMLModel):
    """Model for NFSe (Nota Fiscal de Serviços Eletrônica) documents"""
    
    @property
    def name(self) -> str:
        return "nfse"
    
    @property
    def display_name(self) -> str:
        return "NFSe - Nota Fiscal de Serviços Eletrônica"
    
    @property
    def description(self) -> str:
        return "Nota Fiscal de Serviços Eletrônica"
    
    @property
    def icon(self) -> str:
        return "⚙️"
    
    @property
    def color(self) -> str:
        return "#6f42c1"  # Purple
    
    @property
    def patterns(self) -> List[str]:
        return [
            r'<infNfse',
            r'nfse',
            r'servico',
            r'prestadorservico'
        ]
    
    def get_sql_schema(self) -> Dict[str, str]:
        """SQL schema for NFSe documents"""
        return {
            'nfse_documents': '''
                CREATE TABLE IF NOT EXISTS nfse_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    nfse_number TEXT,
                    verification_code TEXT,
                    service_description TEXT,
                    iss_rate REAL DEFAULT 0,
                    FOREIGN KEY (document_id) REFERENCES xml_documents (id)
                )
            '''
        }
    
    def get_extraction_rules(self) -> Dict[str, str]:
        """XPath extraction rules for NFSe"""
        return {
            'document_number': "//numero/text() | //*[contains(local-name(), 'numero')]/text()",
            'verification_code': "//codigoVerificacao/text() | //*[contains(local-name(), 'codigoVerificacao')]/text()",
            'service_description': "//discriminacao/text() | //*[contains(local-name(), 'discriminacao')]/text()",
            'iss_rate': "//aliquota/text() | //*[contains(local-name(), 'aliquota')]/text()"
        }
    
    def process_document(self, xml_content: str, file_path: Path) -> Dict[str, Any]:
        """Process NFSe document"""
        try:
            tree = etree.fromstring(xml_content.encode() if isinstance(xml_content, str) else xml_content)
            
            def safe_xpath(xpath: str, default: str = '') -> str:
                try:
                    result = tree.xpath(xpath)
                    return str(result[0]).strip() if result else default
                except Exception:
                    return default
            
            def safe_float(value: str, default: float = 0.0) -> float:
                try:
                    return float(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            document_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_hash': '',
                'document_type': 'nfse',
                'document_number': safe_xpath("//numero/text() | //*[contains(local-name(), 'numero')]/text()"),
                'issue_date': safe_xpath("//dataEmissao/text() | //*[contains(local-name(), 'dataEmissao')]/text()"),
                
                # Provider information
                'cnpj_issuer': safe_xpath("//prestadorServico//cnpj/text() | //*[contains(local-name(), 'prestador')]//cnpj/text()"),
                'issuer_name': safe_xpath("//prestadorServico//razaoSocial/text() | //*[contains(local-name(), 'prestador')]//razaoSocial/text()"),
                
                # Taker information
                'cnpj_recipient': safe_xpath("//tomadorServico//cnpj/text() | //*[contains(local-name(), 'tomador')]//cnpj/text()"),
                'recipient_name': safe_xpath("//tomadorServico//razaoSocial/text() | //*[contains(local-name(), 'tomador')]//razaoSocial/text()"),
                
                # Service values
                'total_value': safe_float(safe_xpath("//valorServicos/text() | //*[contains(local-name(), 'valorServicos')]/text()")),
                'tax_value': safe_float(safe_xpath("//valorIss/text() | //*[contains(local-name(), 'valorIss')]/text()")),
                
                # Service information
                'additional_info': safe_xpath("//discriminacao/text() | //*[contains(local-name(), 'discriminacao')]/text()"),
                
                'status': 'active'
            }
            
            return document_data
            
        except Exception as e:
            self.logger.error(f"Error processing NFSe document: {e}")
            raise
    
    def get_display_fields(self) -> List[Dict[str, str]]:
        """Fields for UI display"""
        return [
            {'name': 'document_number', 'label': 'Número da NFSe', 'type': 'text'},
            {'name': 'issue_date', 'label': 'Data de Emissão', 'type': 'date'},
            {'name': 'issuer_name', 'label': 'Prestador', 'type': 'text'},
            {'name': 'recipient_name', 'label': 'Tomador', 'type': 'text'},
            {'name': 'total_value', 'label': 'Valor dos Serviços', 'type': 'currency'},
            {'name': 'tax_value', 'label': 'Valor ISS', 'type': 'currency'}
        ]


class XMLModelManager:
    """Manager for XML document models"""
    
    def __init__(self):
        self.models = {
            'nfe': NFEModel(),
            'nfce': NFCEModel(),
            'cte': CTEModel(),
            'nfse': NFSEModel()
        }
        self.logger = logging.getLogger(__name__)
    
    def get_model(self, model_name: str) -> Optional[XMLModel]:
        """Get model by name"""
        return self.models.get(model_name)
    
    def get_all_models(self) -> Dict[str, XMLModel]:
        """Get all available models"""
        return self.models.copy()
    
    def detect_model(self, xml_content: str) -> Optional[XMLModel]:
        """Detect appropriate model based on XML content"""
        try:
            for model in self.models.values():
                if model.matches_document(xml_content):
                    return model
            return None
        except Exception as e:
            self.logger.error(f"Error detecting model: {e}")
            return None
    
    def initialize_databases(self, database_manager) -> bool:
        """Initialize database schemas for all models"""
        try:
            for model_name, model in self.models.items():
                try:
                    schemas = model.get_sql_schema()
                    for table_name, schema_sql in schemas.items():
                        # Execute schema creation using database manager
                        with database_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(schema_sql)
                            conn.commit()
                    
                    self.logger.info(f"Initialized database schema for {model_name}")
                except Exception as e:
                    self.logger.error(f"Error initializing schema for {model_name}: {e}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing databases: {e}")
            return False 