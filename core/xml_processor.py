#!/usr/bin/env python3
"""
XML Processor for XML Fiscal Manager Pro
Advanced XML parsing and processing for Brazilian fiscal documents
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import re
import hashlib
from lxml import etree
import xmltodict
import time
from models.xml_models import XMLModelManager


class XMLProcessor:
    """Professional XML processor for Brazilian fiscal documents"""
    
    def __init__(self, config_manager, database_manager):
        self.config = config_manager
        self.database_manager = database_manager
        self.xml_config = config_manager.get_section('xml_processing')
        self.xml_model_manager = XMLModelManager()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # XML namespaces for different document types
        self.namespaces = {
            'nfe': {
                'nfe': 'http://www.portalfiscal.inf.br/nfe',
                'sig': 'http://www.w3.org/2000/09/xmldsig#'
            },
            'nfce': {
                'nfe': 'http://www.portalfiscal.inf.br/nfe',
                'sig': 'http://www.w3.org/2000/09/xmldsig#'
            },
            'cte': {
                'cte': 'http://www.portalfiscal.inf.br/cte',
                'sig': 'http://www.w3.org/2000/09/xmldsig#'
            },
            'nfse': {
                'nfse': 'http://www.abrasf.org.br/nfse.xsd'
            }
        }
        
        # Document type patterns
        self.type_patterns = {
            'nfe': [r'nfeProc', r'NFe', r'infNFe'],
            'nfce': [r'nfeProc', r'NFe', r'infNFe'],
            'cte': [r'cteProc', r'CTe', r'infCte'],
            'nfse': [r'CompNfse', r'Nfse', r'InfNfse', r'RPS']
        }
    
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process a single XML file"""
        start_time = time.time()
        file_path = Path(file_path)
        
        self.logger.info(f"Processing file: {file_path}")
        
        try:
            # Validate file
            if not self._validate_file(file_path):
                raise ValueError(f"File validation failed: {file_path}")
            
            # Calculate file hash for deduplication
            file_hash = self.database_manager.calculate_file_hash(file_path)
            
            # Check if document already exists
            if self.database_manager.document_exists(file_hash):
                self.logger.info(f"Document already exists in database: {file_path}")
                return {
                    'status': 'skipped',
                    'message': 'Document already exists',
                    'file_path': str(file_path),
                    'processing_time': time.time() - start_time
                }
            
            # Read file content
            xml_content = self._read_file(file_path)
            
            # Parse XML
            parsed_data = self._parse_xml(xml_content)
            
            # Add file hash to parsed data
            parsed_data['file_hash'] = file_hash
            
            # Detect document type
            doc_type = self._detect_document_type(parsed_data, xml_content)
            
            # Extract document data based on type
            document_data = self._extract_document_data(parsed_data, doc_type, file_path)
            
            # Validate business rules
            validation_errors = self._validate_business_rules(document_data, doc_type)
            if validation_errors:
                self.logger.warning(f"Business rule violations for {file_path}: {validation_errors}")
                document_data['validation_errors'] = validation_errors
            
            # Insert into database
            document_id = self.database_manager.insert_document(document_data)
            
            if document_id:
                processing_time = time.time() - start_time
                self.logger.info(f"Successfully processed {file_path} in {processing_time:.2f}s")
                
                return {
                    'status': 'success',
                    'document_id': document_id,
                    'document_type': doc_type,
                    'file_path': str(file_path),
                    'processing_time': processing_time,
                    'document_data': document_data
                }
            else:
                raise ValueError("Failed to insert document into database")
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'status': 'error',
                'error': error_msg,
                'file_path': str(file_path),
                'processing_time': processing_time
            }
    
    def process_multiple_files(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """Process multiple XML files"""
        results = []
        
        for file_path in file_paths:
            result = self.process_file(file_path)
            results.append(result)
            
            # Optional: Add progress callback here
            
        return results
    
    def _validate_file(self, file_path: Path) -> bool:
        """Validate XML file"""
        try:
            if not file_path.exists():
                return False
            
            if file_path.suffix.lower() != '.xml':
                return False
            
            # Check file size
            max_size_mb = self.xml_config.get('max_file_size_mb', 50)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)")
            
            # Basic XML validation
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB
                if not content.strip().startswith('<?xml'):
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating file {file_path}: {e}")
            return False
    
    def _read_file(self, file_path: Path) -> str:
        """Read XML file with encoding detection"""
        try:
            # Try UTF-8 first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                pass
            
            # Try other encodings
            encodings = ['latin-1', 'iso-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        logging.warning(f"File {file_path} read with encoding: {encoding}")
                        return content
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"Could not decode file {file_path} with any supported encoding")
            
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")
    
    def _parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse XML content"""
        try:
            # Clean content
            xml_content = self._clean_xml_content(xml_content)
            
            # Parse with lxml
            parser = etree.XMLParser(recover=True, strip_cdata=False)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)
            
            # Convert to dictionary
            parsed_data = xmltodict.parse(xml_content)
            
            return {
                'dict': parsed_data,
                'root': root,
                'raw_content': xml_content
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing XML: {e}")
    
    def _clean_xml_content(self, content: str) -> str:
        """Clean XML content"""
        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Remove invalid characters
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # Fix common encoding issues
        content = content.replace('&', '&amp;')
        content = re.sub(r'&amp;(lt|gt|quot|apos|amp);', r'&\1;', content)
        
        return content
    
    def _detect_document_type(self, parsed_data: Dict, xml_content: str) -> str:
        """Detect document type using XML models"""
        try:
            # Use XML model manager to detect document type
            detected_model = self.xml_model_manager.detect_model(xml_content)
            if detected_model:
                self.logger.info(f"Detected document type using XML models: {detected_model.name}")
                return detected_model.name
            
            # Fallback to legacy pattern matching
            content_lower = xml_content.lower()
            
            # Check for NFCe first (more specific)
            if any(pattern in content_lower for pattern in ['nfce', 'nfc-e']):
                return 'nfce'
            
            # Check for NFe patterns
            for pattern in self.type_patterns.get('nfe', []):
                if re.search(pattern.lower(), content_lower):
                    return 'nfe'
            
            # Check for CTe patterns
            for pattern in self.type_patterns.get('cte', []):
                if re.search(pattern.lower(), content_lower):
                    return 'cte'
            
            # Check for NFSe patterns
            for pattern in self.type_patterns.get('nfse', []):
                if re.search(pattern.lower(), content_lower):
                    return 'nfse'
            
            self.logger.warning(f"Could not detect document type, defaulting to 'unknown'")
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error detecting document type: {e}")
            return 'unknown'
    
    def _extract_document_data(self, parsed_data: Dict, doc_type: str, file_path: Path) -> Dict[str, Any]:
        """Extract document data based on type using XML models"""
        try:
            # Try to use XML model for extraction
            xml_model = self.xml_model_manager.get_model(doc_type)
            if xml_model:
                return self._extract_with_model(xml_model, parsed_data, file_path)
            
            # Fallback to legacy extraction methods
            if doc_type == 'nfe' or doc_type == 'nfce':
                return self._extract_nfe_data(parsed_data, file_path)
            elif doc_type == 'cte':
                return self._extract_cte_data(parsed_data, file_path)
            elif doc_type == 'nfse':
                return self._extract_nfse_data(parsed_data, file_path)
            else:
                return self._extract_generic_data(parsed_data, file_path)
                
        except Exception as e:
            self.logger.error(f"Error extracting document data for type {doc_type}: {e}")
            return self._extract_generic_data(parsed_data, file_path)
    
    def _extract_with_model(self, xml_model, parsed_data: Dict, file_path: Path) -> Dict[str, Any]:
        """Extract document data using specific XML model"""
        try:
            xml_content = None
            
            # Get the raw XML content
            if 'raw_content' in parsed_data:
                xml_content = parsed_data['raw_content']
            else:
                # Read file again if needed
                with open(file_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
            
            # Use model to process the document
            processed_data = xml_model.process_document(xml_content, file_path)
            
            # Add common fields
            processed_data.update({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'processed_at': datetime.now().isoformat(),
                'document_type': xml_model.name,
                'processor_version': '2.0',
                'model_version': getattr(xml_model, 'version', '1.0')
            })
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error extracting with model {xml_model.name}: {e}")
            # Fallback to generic extraction
            return self._extract_generic_data(parsed_data, file_path)
    
    def _extract_nfe_data(self, parsed_data: Dict, file_path: Path) -> Dict[str, Any]:
        """Extract NFe/NFCe specific data using enhanced lxml approach"""
        try:
            # Helper functions for safe extraction
            def safe_xpath_text(xpath, default=''):
                try:
                    result = parsed_data['root'].xpath(xpath, namespaces=self.namespaces['nfe'])
                    return result[0] if result else default
                except:
                    return default
                    
            def safe_xpath_attr(xpath, attr, default=''):
                try:
                    result = parsed_data['root'].xpath(xpath, namespaces=self.namespaces['nfe'])
                    return result[0].get(attr, default) if result else default
                except:
                    return default
            
            # Basic NFe information
            nfe_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_hash': parsed_data['file_hash'],
                'file_size': file_path.stat().st_size,
                'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'document_type': 'nfe' if safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:mod/text()') != '65' else 'nfce',
                
                # NFe specific fields
                'nfe_number': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:nNF/text()'),
                'access_key': safe_xpath_text('//nfe:protNFe/nfe:infProt/nfe:chNFe/text()') or safe_xpath_attr('//nfe:infNFe', 'Id', '').replace('NFe', ''),
                'series': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:serie/text()'),
                'model': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:mod/text()'),
                'operation_type': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:tpNF/text()'),
                'operation_nature': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:natOp/text()'),
                'emission_date': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:dhEmi/text()'),
                'exit_date': safe_xpath_text('//nfe:infNFe/nfe:ide/nfe:dhSaiEnt/text()'),
                
                # Emitter information
                'emitter_cnpj': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:CNPJ/text()'),
                'emitter_name': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:xNome/text()'),
                'emitter_fantasy': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:xFant/text()'),
                'emitter_ie': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:IE/text()'),
                'emitter_address': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:xLgr/text()'),
                'emitter_number': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:nro/text()'),
                'emitter_district': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:xBairro/text()'),
                'emitter_city': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:xMun/text()'),
                'emitter_state': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:UF/text()'),
                'emitter_cep': safe_xpath_text('//nfe:infNFe/nfe:emit/nfe:enderEmit/nfe:CEP/text()'),
                
                # Recipient information
                'recipient_cnpj': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:CNPJ/text()'),
                'recipient_cpf': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:CPF/text()'),
                'recipient_name': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:xNome/text()'),
                'recipient_ie': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:IE/text()'),
                'recipient_address': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:xLgr/text()'),
                'recipient_number': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:nro/text()'),
                'recipient_district': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:xBairro/text()'),
                'recipient_city': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:xMun/text()'),
                'recipient_state': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:UF/text()'),
                'recipient_cep': safe_xpath_text('//nfe:infNFe/nfe:dest/nfe:enderDest/nfe:CEP/text()'),
                
                # Financial information
                'total_products': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vProd/text()') or '0'),
                'total_freight': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vFrete/text()') or '0'),
                'total_insurance': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vSeg/text()') or '0'),
                'total_discount': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vDesc/text()') or '0'),
                'total_other': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vOutro/text()') or '0'),
                'total_nfe': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vNF/text()') or '0'),
                
                # Tax information
                'icms_base': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vBC/text()') or '0'),
                'icms_value': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vICMS/text()') or '0'),
                'icms_st_base': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vBCST/text()') or '0'),
                'icms_st_value': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vST/text()') or '0'),
                'ipi_value': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vIPI/text()') or '0'),
                'pis_value': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vPIS/text()') or '0'),
                'cofins_value': float(safe_xpath_text('//nfe:infNFe/nfe:total/nfe:ICMSTot/nfe:vCOFINS/text()') or '0'),
                
                # Payment information
                'payment_method': safe_xpath_text('//nfe:infNFe/nfe:pag/nfe:detPag/nfe:tPag/text()'),
                'payment_value': float(safe_xpath_text('//nfe:infNFe/nfe:pag/nfe:detPag/nfe:vPag/text()') or '0'),
                
                # Transport information
                'transport_modality': safe_xpath_text('//nfe:infNFe/nfe:transp/nfe:modFrete/text()'),
                'transporter_cnpj': safe_xpath_text('//nfe:infNFe/nfe:transp/nfe:transporta/nfe:CNPJ/text()'),
                'transporter_name': safe_xpath_text('//nfe:infNFe/nfe:transp/nfe:transporta/nfe:xNome/text()'),
                
                # Additional information
                'additional_info': safe_xpath_text('//nfe:infNFe/nfe:infAdic/nfe:infCpl/text()'),
                'protocol_number': safe_xpath_text('//nfe:protNFe/nfe:infProt/nfe:nProt/text()'),
                'protocol_date': safe_xpath_text('//nfe:protNFe/nfe:infProt/nfe:dhRecbto/text()'),
                
                # Status
                'status': 'processed',
                'raw_xml': str(etree.tostring(parsed_data['root'], encoding='unicode', pretty_print=True))[:10000]  # Truncate for storage
            }
            
            # Extract items using enhanced method
            items = self._extract_nfe_items_enhanced(parsed_data['root'], self.namespaces['nfe'])
            nfe_data['items'] = items
            
            # Compatibility fields for existing code
            nfe_data['document_number'] = nfe_data['nfe_number']
            nfe_data['issue_date'] = nfe_data['emission_date']
            nfe_data['cnpj_issuer'] = nfe_data['emitter_cnpj']
            nfe_data['issuer_name'] = nfe_data['emitter_name']
            nfe_data['cnpj_recipient'] = nfe_data['recipient_cnpj']
            nfe_data['total_value'] = nfe_data['total_nfe']
            nfe_data['tax_value'] = nfe_data['icms_value'] + nfe_data['ipi_value'] + nfe_data['pis_value'] + nfe_data['cofins_value']
            
            return nfe_data
            
        except Exception as e:
            self.logger.error(f"Error extracting NFe data: {e}")
            raise
    
    def _extract_cte_data(self, parsed_data: Dict, file_path: Path) -> Dict[str, Any]:
        """Extract CTe specific data"""
        try:
            dict_data = parsed_data['dict']
            
            # Navigate to CTe data
            cte_data = None
            if 'cteProc' in dict_data:
                cte_data = dict_data['cteProc']['CTe']
            elif 'CTe' in dict_data:
                cte_data = dict_data['CTe']
            
            if not cte_data:
                raise ValueError("Could not find CTe data in XML")
            
            inf_cte = cte_data['infCte']
            
            # Basic document information
            document_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'document_type': 'cte',
                'document_number': self._safe_get(inf_cte, ['ide', 'nCT']),
                'document_series': self._safe_get(inf_cte, ['ide', 'serie']),
                'issue_date': self._parse_date(self._safe_get(inf_cte, ['ide', 'dhEmi'])),
                'access_key': self._safe_get(inf_cte, ['@Id'], '').replace('CTe', ''),
                'status': 'active'
            }
            
            # Issuer information
            emit = inf_cte.get('emit', {})
            document_data.update({
                'cnpj_issuer': self._clean_cnpj(self._safe_get(emit, 'CNPJ')),
                'issuer_name': self._safe_get(emit, 'xNome'),
                'issuer_ie': self._safe_get(emit, 'IE')
            })
            
            # Recipient information
            dest = inf_cte.get('dest', {})
            if dest:
                document_data.update({
                    'cnpj_recipient': self._clean_cnpj(self._safe_get(dest, 'CNPJ') or self._safe_get(dest, 'CPF')),
                    'recipient_name': self._safe_get(dest, 'xNome'),
                    'recipient_ie': self._safe_get(dest, 'IE')
                })
            
            # Financial totals
            vprest = inf_cte.get('vPrest', {})
            document_data.update({
                'total_value': self._parse_decimal(self._safe_get(vprest, 'vTPrest')),
                'tax_value': self._parse_decimal(self._safe_get(vprest, 'vTotTrib'))
            })
            
            # Transport specific data
            document_data['metadata'] = {
                'modal': self._safe_get(inf_cte, ['ide', 'modal']),
                'service_type': self._safe_get(inf_cte, ['ide', 'tpServ']),
                'cfop': self._safe_get(inf_cte, ['ide', 'CFOP']),
                'operation_nature': self._safe_get(inf_cte, ['ide', 'natOp'])
            }
            
            # Items (simplified for CTe)
            document_data['items'] = []
            
            document_data['raw_data'] = parsed_data['raw_content'][:50000]
            
            return document_data
            
        except Exception as e:
            raise ValueError(f"Error extracting CTe data: {e}")
    
    def _extract_nfse_data(self, parsed_data: Dict, file_path: Path) -> Dict[str, Any]:
        """Extract NFSe specific data"""
        try:
            dict_data = parsed_data['dict']
            
            # NFSe has multiple possible structures
            nfse_data = None
            if 'CompNfse' in dict_data:
                nfse_data = dict_data['CompNfse']['Nfse']
            elif 'Nfse' in dict_data:
                nfse_data = dict_data['Nfse']
            elif 'RPS' in dict_data:
                nfse_data = dict_data['RPS']
            
            if not nfse_data:
                raise ValueError("Could not find NFSe data in XML")
            
            inf_nfse = nfse_data.get('InfNfse', nfse_data)
            
            # Basic document information
            document_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'document_type': 'nfse',
                'document_number': self._safe_get(inf_nfse, ['Numero']),
                'issue_date': self._parse_date(self._safe_get(inf_nfse, ['DataEmissao'])),
                'status': 'active'
            }
            
            # Service provider
            prestador = inf_nfse.get('PrestadorServico', {})
            document_data.update({
                'cnpj_issuer': self._clean_cnpj(self._safe_get(prestador, ['IdentificacaoPrestador', 'Cnpj'])),
                'issuer_name': self._safe_get(prestador, ['RazaoSocial'])
            })
            
            # Service taker
            tomador = inf_nfse.get('TomadorServico', {})
            if tomador:
                document_data.update({
                    'cnpj_recipient': self._clean_cnpj(self._safe_get(tomador, ['IdentificacaoTomador', 'CpfCnpj', 'Cnpj'])),
                    'recipient_name': self._safe_get(tomador, ['RazaoSocial'])
                })
            
            # Service values
            servico = inf_nfse.get('Servico', {})
            valores = servico.get('Valores', {})
            document_data.update({
                'total_value': self._parse_decimal(self._safe_get(valores, 'ValorLiquidoNfse')),
                'tax_value': self._parse_decimal(self._safe_get(valores, 'ValorIss')),
                'service_value': self._parse_decimal(self._safe_get(valores, 'ValorServicos'))
            })
            
            document_data['metadata'] = {
                'service_code': self._safe_get(servico, ['ItemListaServico']),
                'service_description': self._safe_get(servico, ['Discriminacao']),
                'municipality_code': self._safe_get(servico, ['CodigoMunicipio'])
            }
            
            document_data['items'] = []
            document_data['raw_data'] = parsed_data['raw_content'][:50000]
            
            return document_data
            
        except Exception as e:
            raise ValueError(f"Error extracting NFSe data: {e}")
    
    def _extract_generic_data(self, parsed_data: Dict, file_path: Path) -> Dict[str, Any]:
        """Extract generic data for unknown document types"""
        return {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'document_type': 'unknown',
            'status': 'active',
            'total_value': 0.0,
            'tax_value': 0.0,
            'items': [],
            'metadata': {'parsing_method': 'generic'},
            'raw_data': parsed_data['raw_content'][:50000]
        }
    
    def _extract_nfe_items(self, det_data: Union[List, Dict]) -> List[Dict]:
        """Extract NFe items"""
        items = []
        
        try:
            # Handle different det structures
            if not det_data:
                return items
            
            # Ensure det_data is a list
            if isinstance(det_data, dict):
                det_list = [det_data]
            elif isinstance(det_data, list):
                det_list = det_data
            else:
                return items
            
            for det in det_list:
                if not isinstance(det, dict):
                    continue
                
                try:
                    prod = det.get('prod', {})
                    if not isinstance(prod, dict):
                        continue
                    
                    # Extract basic product information
                    item = {
                        'code': self._safe_get(prod, 'cProd', ''),
                        'ean': self._safe_get(prod, 'cEANTrib', '') or self._safe_get(prod, 'cEAN', ''),
                        'description': self._safe_get(prod, 'xProd', ''),
                        'ncm': self._safe_get(prod, 'NCM', ''),
                        'cfop': self._safe_get(prod, 'CFOP', ''),
                        'unit': self._safe_get(prod, 'uCom', ''),
                        'quantity': self._parse_decimal(self._safe_get(prod, 'qCom', 0)),
                        'unit_value': self._parse_decimal(self._safe_get(prod, 'vUnCom', 0)),
                        'total_value': self._parse_decimal(self._safe_get(prod, 'vProd', 0))
                    }
                    
                    # Extract tax information safely
                    imposto = det.get('imposto', {})
                    if isinstance(imposto, dict):
                        # ICMS
                        icms_data = imposto.get('ICMS', {})
                        if isinstance(icms_data, dict):
                            # ICMS can have different structures (ICMS00, ICMS10, etc.)
                            icms_value = 0
                            icms_rate = 0
                            for key, value in icms_data.items():
                                if isinstance(value, dict):
                                    icms_value = self._parse_decimal(value.get('vICMS', 0))
                                    icms_rate = self._parse_decimal(value.get('pICMS', 0))
                                    break
                            
                            item['icms_value'] = icms_value
                            item['icms_rate'] = icms_rate
                        
                        # IPI
                        ipi_data = imposto.get('IPI', {})
                        if isinstance(ipi_data, dict):
                            ipi_trib = ipi_data.get('IPITrib', {})
                            if isinstance(ipi_trib, dict):
                                item['ipi_value'] = self._parse_decimal(ipi_trib.get('vIPI', 0))
                                item['ipi_rate'] = self._parse_decimal(ipi_trib.get('pIPI', 0))
                            else:
                                item['ipi_value'] = 0
                                item['ipi_rate'] = 0
                        
                        # PIS
                        pis_data = imposto.get('PIS', {})
                        if isinstance(pis_data, dict):
                            # PIS can have different structures (PISAliq, PISNT, etc.)
                            pis_value = 0
                            pis_rate = 0
                            for key, value in pis_data.items():
                                if isinstance(value, dict):
                                    pis_value = self._parse_decimal(value.get('vPIS', 0))
                                    pis_rate = self._parse_decimal(value.get('pPIS', 0))
                                    break
                            
                            item['pis_value'] = pis_value
                            item['pis_rate'] = pis_rate
                        
                        # COFINS
                        cofins_data = imposto.get('COFINS', {})
                        if isinstance(cofins_data, dict):
                            # COFINS can have different structures (COFINSAliq, COFINSNT, etc.)
                            cofins_value = 0
                            cofins_rate = 0
                            for key, value in cofins_data.items():
                                if isinstance(value, dict):
                                    cofins_value = self._parse_decimal(value.get('vCOFINS', 0))
                                    cofins_rate = self._parse_decimal(value.get('pCOFINS', 0))
                                    break
                            
                            item['cofins_value'] = cofins_value
                            item['cofins_rate'] = cofins_rate
                    
                    # Set default values for missing tax information
                    for tax_field in ['icms_value', 'icms_rate', 'ipi_value', 'ipi_rate', 
                                    'pis_value', 'pis_rate', 'cofins_value', 'cofins_rate']:
                        if tax_field not in item:
                            item[tax_field] = 0.0
                    
                    # Calculate total tax value
                    item['tax_value'] = (item.get('icms_value', 0) + 
                                       item.get('ipi_value', 0) + 
                                       item.get('pis_value', 0) + 
                                       item.get('cofins_value', 0))
                    
                    # Calculate total tax rate (approximate)
                    if item.get('total_value', 0) > 0:
                        item['tax_rate'] = (item['tax_value'] / item['total_value']) * 100
                    else:
                        item['tax_rate'] = 0.0
                    
                    items.append(item)
                    
                except Exception as e:
                    logging.warning(f"Error extracting item data: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error extracting NFe items: {e}")
        
        return items
    
    def _is_nfce(self, inf_nfe: Dict) -> bool:
        """Check if document is NFCe based on model"""
        model = self._safe_get(inf_nfe, ['ide', 'mod'])
        return model == '65'
    
    def _extract_address(self, address_data: Dict) -> str:
        """Extract formatted address"""
        if not address_data or not isinstance(address_data, dict):
            return ''
        
        parts = []
        if address_data.get('xLgr'):
            parts.append(str(address_data['xLgr']))
        if address_data.get('nro'):
            parts.append(str(address_data['nro']))
        if address_data.get('xBairro'):
            parts.append(str(address_data['xBairro']))
        if address_data.get('xMun'):
            parts.append(str(address_data['xMun']))
        if address_data.get('UF'):
            parts.append(str(address_data['UF']))
        if address_data.get('CEP'):
            parts.append(str(address_data['CEP']))
        
        return ', '.join(parts)
    
    def _extract_payment_info(self, pag_data: Union[Dict, List]) -> str:
        """Extract payment information"""
        if not pag_data:
            return 'Não informado'
        
        try:
            if isinstance(pag_data, list):
                pag_data = pag_data[0] if pag_data else {}
            
            if isinstance(pag_data, dict):
                detpag = pag_data.get('detPag', pag_data)
                if isinstance(detpag, list):
                    detpag = detpag[0] if detpag else {}
                
                if isinstance(detpag, dict):
                    payment_types = {
                        '01': 'Dinheiro',
                        '02': 'Cheque',
                        '03': 'Cartão de Crédito',
                        '04': 'Cartão de Débito',
                        '05': 'Crédito Loja',
                        '10': 'Vale Alimentação',
                        '11': 'Vale Refeição',
                        '12': 'Vale Presente',
                        '13': 'Vale Combustível',
                        '14': 'Duplicata Mercantil',
                        '15': 'Boleto Bancário',
                        '90': 'Sem pagamento',
                        '99': 'Outros'
                    }
                    
                    tpag = detpag.get('tPag', '')
                    return payment_types.get(str(tpag), f'Tipo {tpag}')
        except Exception as e:
            logging.error(f"Error extracting payment info: {e}")
        
        return 'Não informado'
    
    def _validate_business_rules(self, document_data: Dict, doc_type: str) -> List[str]:
        """Validate business rules"""
        errors = []
        
        try:
            # Basic validations
            if not document_data.get('cnpj_issuer'):
                errors.append("CNPJ do emitente não encontrado")
            
            if not document_data.get('total_value') or document_data['total_value'] <= 0:
                errors.append("Valor total inválido ou zero")
            
            # Document-specific validations
            if doc_type in ['nfe', 'nfce']:
                if not document_data.get('document_number'):
                    errors.append("Número da nota fiscal não encontrado")
                
                if not document_data.get('access_key') or len(document_data['access_key']) != 44:
                    errors.append("Chave de acesso inválida")
            
            # CNPJ validation
            cnpj_issuer = document_data.get('cnpj_issuer', '')
            if cnpj_issuer and not self._validate_cnpj(cnpj_issuer):
                errors.append("CNPJ do emitente inválido")
            
            cnpj_recipient = document_data.get('cnpj_recipient', '')
            if cnpj_recipient and not self._validate_cnpj(cnpj_recipient):
                errors.append("CNPJ do destinatário inválido")
            
        except Exception as e:
            errors.append(f"Erro na validação: {str(e)}")
        
        return errors
    
    def _safe_get(self, data: Any, path: Union[str, List], default: Any = '') -> Any:
        """Safely get nested dictionary value"""
        if isinstance(path, str):
            path = [path]
        
        current = data
        for key in path:
            # Check if current is a dictionary-like object
            if hasattr(current, 'get') and callable(getattr(current, 'get')):
                current = current.get(key)
            elif isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                try:
                    current = current[int(key)]
                except (IndexError, ValueError):
                    return default
            else:
                return default
                
            # If we got None or a string when we expected a dict, return default
            if current is None:
                return default
        
        return current if current is not None else default
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format"""
        if not date_str:
            return None
        
        try:
            # Remove timezone info if present
            date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
            
            # Try different date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _parse_decimal(self, value: Any) -> float:
        """Parse decimal value safely"""
        if value is None or value == '':
            return 0.0
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            # Clean string value
            value_str = str(value).replace(',', '.')
            return float(Decimal(value_str))
            
        except (ValueError, InvalidOperation):
            return 0.0
    
    def _clean_cnpj(self, cnpj: str) -> str:
        """Clean CNPJ/CPF string"""
        if not cnpj:
            return ''
        
        # Remove non-digit characters
        return re.sub(r'\D', '', cnpj)
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """Validate CNPJ number"""
        if not cnpj:
            return False
        
        cnpj = self._clean_cnpj(cnpj)
        
        # Check length
        if len(cnpj) not in [11, 14]:  # CPF or CNPJ
            return False
        
        # Simple validation (not complete algorithm)
        if cnpj == cnpj[0] * len(cnpj):  # All same digits
            return False
        
        return True
    
    def _extract_nfe_items_enhanced(self, tree, nsmap) -> List[Dict]:
        """Extract NFe items with enhanced xpath-based extraction"""
        items = []
        
        try:
            # Get all product nodes
            product_nodes = tree.xpath('//nfe:infNFe/nfe:det', namespaces=nsmap)
            
            for i, product in enumerate(product_nodes):
                try:
                    # Helper function to safely extract text from current product context
                    def safe_xpath_text_item(xpath, default=''):
                        try:
                            result = product.xpath(xpath, namespaces=nsmap)
                            return result[0].text if result and result[0].text else default
                        except:
                            return default
                    
                    # Item number
                    item_number = product.get('nItem', str(i + 1))
                    
                    # Basic product information
                    product_code = safe_xpath_text_item('./nfe:prod/nfe:cProd', f'Item{i+1}')
                    
                    # Use cEANTrib for EAN as specified by user
                    product_ean = safe_xpath_text_item('./nfe:prod/nfe:cEANTrib', '')
                    if product_ean == 'SEM GTIN' or not product_ean:
                        # Fallback to cEAN if cEANTrib is not available
                        product_ean = safe_xpath_text_item('./nfe:prod/nfe:cEAN', '')
                        if product_ean == 'SEM GTIN' or not product_ean:
                            product_ean = ''
                    
                    # Use xProd for description as specified by user
                    product_description = safe_xpath_text_item('./nfe:prod/nfe:xProd', '')
                    
                    # Use NCM and CFOP as specified by user
                    product_ncm = safe_xpath_text_item('./nfe:prod/nfe:NCM', '')
                    product_cfop = safe_xpath_text_item('./nfe:prod/nfe:CFOP', '')
                    product_unit = safe_xpath_text_item('./nfe:prod/nfe:uCom', '')
                    
                    # Quantities and values
                    product_quantity = self._parse_decimal(safe_xpath_text_item('./nfe:prod/nfe:qCom', '0'))
                    product_unit_value = self._parse_decimal(safe_xpath_text_item('./nfe:prod/nfe:vUnCom', '0'))
                    product_total_value = self._parse_decimal(safe_xpath_text_item('./nfe:prod/nfe:vProd', '0'))
                    
                    # Tax information - ICMS
                    icms_cst = ''
                    icms_base = 0.0
                    icms_value = 0.0
                    icms_rate = 0.0
                    
                    try:
                        icms_cst_elements = product.xpath('./nfe:imposto/nfe:ICMS/*/nfe:CST', namespaces=nsmap)
                        icms_csosn_elements = product.xpath('./nfe:imposto/nfe:ICMS/*/nfe:CSOSN', namespaces=nsmap)
                        
                        if icms_cst_elements:
                            icms_cst = icms_cst_elements[0].text or ''
                        elif icms_csosn_elements:
                            icms_cst = icms_csosn_elements[0].text or ''
                        
                        icms_base_elements = product.xpath('./nfe:imposto/nfe:ICMS/*/nfe:vBC', namespaces=nsmap)
                        if icms_base_elements:
                            icms_base = self._parse_decimal(icms_base_elements[0].text or '0')
                        
                        icms_value_elements = product.xpath('./nfe:imposto/nfe:ICMS/*/nfe:vICMS', namespaces=nsmap)
                        if icms_value_elements:
                            icms_value = self._parse_decimal(icms_value_elements[0].text or '0')
                        
                        icms_rate_elements = product.xpath('./nfe:imposto/nfe:ICMS/*/nfe:pICMS', namespaces=nsmap)
                        if icms_rate_elements:
                            icms_rate = self._parse_decimal(icms_rate_elements[0].text or '0')
                    except:
                        pass
                    
                    # Tax information - IPI
                    ipi_cst = ''
                    ipi_base = 0.0
                    ipi_value = 0.0
                    ipi_rate = 0.0
                    
                    try:
                        ipi_cst_elements = product.xpath('./nfe:imposto/nfe:IPI/nfe:IPITrib/nfe:CST', namespaces=nsmap)
                        if ipi_cst_elements:
                            ipi_cst = ipi_cst_elements[0].text or ''
                        
                        ipi_base_elements = product.xpath('./nfe:imposto/nfe:IPI/nfe:IPITrib/nfe:vBC', namespaces=nsmap)
                        if ipi_base_elements:
                            ipi_base = self._parse_decimal(ipi_base_elements[0].text or '0')
                        
                        ipi_value_elements = product.xpath('./nfe:imposto/nfe:IPI/nfe:IPITrib/nfe:vIPI', namespaces=nsmap)
                        if ipi_value_elements:
                            ipi_value = self._parse_decimal(ipi_value_elements[0].text or '0')
                        
                        ipi_rate_elements = product.xpath('./nfe:imposto/nfe:IPI/nfe:IPITrib/nfe:pIPI', namespaces=nsmap)
                        if ipi_rate_elements:
                            ipi_rate = self._parse_decimal(ipi_rate_elements[0].text or '0')
                    except:
                        pass
                    
                    # Tax information - PIS
                    pis_cst = ''
                    pis_base = 0.0
                    pis_value = 0.0
                    pis_rate = 0.0
                    
                    try:
                        pis_cst_elements = product.xpath('./nfe:imposto/nfe:PIS/*/nfe:CST', namespaces=nsmap)
                        if pis_cst_elements:
                            pis_cst = pis_cst_elements[0].text or ''
                        
                        pis_base_elements = product.xpath('./nfe:imposto/nfe:PIS/*/nfe:vBC', namespaces=nsmap)
                        if pis_base_elements:
                            pis_base = self._parse_decimal(pis_base_elements[0].text or '0')
                        
                        pis_value_elements = product.xpath('./nfe:imposto/nfe:PIS/*/nfe:vPIS', namespaces=nsmap)
                        if pis_value_elements:
                            pis_value = self._parse_decimal(pis_value_elements[0].text or '0')
                        
                        pis_rate_elements = product.xpath('./nfe:imposto/nfe:PIS/*/nfe:pPIS', namespaces=nsmap)
                        if pis_rate_elements:
                            pis_rate = self._parse_decimal(pis_rate_elements[0].text or '0')
                    except:
                        pass
                    
                    # Tax information - COFINS
                    cofins_cst = ''
                    cofins_base = 0.0
                    cofins_value = 0.0
                    cofins_rate = 0.0
                    
                    try:
                        cofins_cst_elements = product.xpath('./nfe:imposto/nfe:COFINS/*/nfe:CST', namespaces=nsmap)
                        if cofins_cst_elements:
                            cofins_cst = cofins_cst_elements[0].text or ''
                        
                        cofins_base_elements = product.xpath('./nfe:imposto/nfe:COFINS/*/nfe:vBC', namespaces=nsmap)
                        if cofins_base_elements:
                            cofins_base = self._parse_decimal(cofins_base_elements[0].text or '0')
                        
                        cofins_value_elements = product.xpath('./nfe:imposto/nfe:COFINS/*/nfe:vCOFINS', namespaces=nsmap)
                        if cofins_value_elements:
                            cofins_value = self._parse_decimal(cofins_value_elements[0].text or '0')
                        
                        cofins_rate_elements = product.xpath('./nfe:imposto/nfe:COFINS/*/nfe:pCOFINS', namespaces=nsmap)
                        if cofins_rate_elements:
                            cofins_rate = self._parse_decimal(cofins_rate_elements[0].text or '0')
                    except:
                        pass
                    
                    # Create item data structure compatible with the database
                    item_data = {
                        # Basic product information
                        'item_number': item_number,
                        'item_code': product_code,
                        'item_ean': product_ean,
                        'item_description': product_description,
                        'ncm_code': product_ncm,
                        'cfop': product_cfop,
                        'commercial_unit': product_unit,
                        'quantity': product_quantity,
                        'unit_value': product_unit_value,
                        'total_value': product_total_value,
                        
                        # Tax information - ICMS
                        'icms_cst': icms_cst,
                        'icms_base': icms_base,
                        'icms_value': icms_value,
                        'icms_rate': icms_rate,
                        
                        # Tax information - IPI
                        'ipi_cst': ipi_cst,
                        'ipi_base': ipi_base,
                        'ipi_value': ipi_value,
                        'ipi_rate': ipi_rate,
                        
                        # Tax information - PIS
                        'pis_cst': pis_cst,
                        'pis_base': pis_base,
                        'pis_value': pis_value,
                        'pis_rate': pis_rate,
                        
                        # Tax information - COFINS
                        'cofins_cst': cofins_cst,
                        'cofins_base': cofins_base,
                        'cofins_value': cofins_value,
                        'cofins_rate': cofins_rate,
                        
                        # Calculated totals
                        'tax_value': icms_value + ipi_value + pis_value + cofins_value
                    }
                    
                    # Calculate total tax rate (approximate)
                    if product_total_value > 0:
                        item_data['tax_rate'] = (item_data['tax_value'] / product_total_value) * 100
                    else:
                        item_data['tax_rate'] = 0.0
                    
                    items.append(item_data)
                    
                except Exception as e:
                    logging.warning(f"Error extracting item {i+1}: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error extracting NFe items: {e}")
        
        return items 