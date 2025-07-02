import sqlite3
import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """Database manager for XML document processing"""

    def __init__(self, config_manager):
        self.config = config_manager
        self.db_config = config_manager.get_section('database')
        # Use the configured db_file from config, fallback to data/documents.db
        db_file = self.db_config.get('db_file', 'data/documents.db')
        if not db_file.startswith(('/', 'C:', 'D:', 'E:')):  # If not absolute path
            self.db_path = Path(db_file)
        else:
            self.db_path = Path(db_file)
        
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = self.db_config.get('cache_ttl', 3600)  # 1 hour default
        
        # Initialize database
        self._initialize_database()
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()

    def _initialize_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create xml_documents table with comprehensive fields
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS xml_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_hash TEXT UNIQUE NOT NULL,
                        file_size REAL DEFAULT 0,
                        processing_date TEXT,
                        document_type TEXT NOT NULL,
                        document_number TEXT,
                        series TEXT,
                        model TEXT,
                        issue_date TEXT,
                        exit_date TEXT,
                        access_key TEXT,
                        protocol_number TEXT,
                        protocol_date TEXT,
                        operation_nature TEXT,
                        
                        -- Emitter information
                        cnpj_issuer TEXT,
                        issuer_name TEXT,
                        emitter_fantasy TEXT,
                        emitter_ie TEXT,
                        emitter_address TEXT,
                        emitter_city TEXT,
                        emitter_state TEXT,
                        emitter_cep TEXT,
                        
                        -- Recipient information
                        cnpj_recipient TEXT,
                        recipient_name TEXT,
                        recipient_ie TEXT,
                        recipient_address TEXT,
                        recipient_city TEXT,
                        recipient_state TEXT,
                        recipient_cep TEXT,
                        
                        -- Financial totals
                        total_products REAL DEFAULT 0,
                        total_freight REAL DEFAULT 0,
                        total_insurance REAL DEFAULT 0,
                        total_discount REAL DEFAULT 0,
                        total_other REAL DEFAULT 0,
                        total_nfe REAL DEFAULT 0,
                        icms_st_value REAL DEFAULT 0,
                        
                        -- Tax totals
                        icms_base REAL DEFAULT 0,
                        icms_value REAL DEFAULT 0,
                        ipi_value REAL DEFAULT 0,
                        pis_value REAL DEFAULT 0,
                        cofins_value REAL DEFAULT 0,
                        total_value REAL DEFAULT 0,
                        tax_value REAL DEFAULT 0,
                        
                        -- Transport and payment
                        transport_modality TEXT,
                        transporter_name TEXT,
                        payment_method TEXT,
                        
                        -- Additional information
                        additional_info TEXT,
                        
                        -- System fields
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check existing columns
                cursor.execute("PRAGMA table_info(xml_documents)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                # Define new columns to add
                new_columns = [
                    'model TEXT',
                    'exit_date TEXT',
                    'protocol_number TEXT',
                    'protocol_date TEXT',
                    'operation_nature TEXT',
                    'emitter_fantasy TEXT',
                    'emitter_ie TEXT',
                    'emitter_address TEXT',
                    'emitter_city TEXT',
                    'emitter_state TEXT',
                    'emitter_cep TEXT',
                    'recipient_ie TEXT',
                    'recipient_address TEXT',
                    'recipient_city TEXT',
                    'recipient_state TEXT',
                    'recipient_cep TEXT',
                    'total_freight REAL',
                    'total_insurance REAL',
                    'total_discount REAL',
                    'total_other REAL',
                    'total_nfe REAL',
                    'transport_modality TEXT',
                    'transporter_name TEXT',
                    'payment_method TEXT',
                    'additional_info TEXT',
                    'file_size INTEGER',
                    'processed_at TEXT',
                    'processor_version TEXT',
                    'model_version TEXT',
                    'processing_date TEXT'
                ]
                
                # Add new columns to xml_documents table
                for column_def in new_columns:
                    try:
                        # Split column definition into name and type
                        parts = column_def.strip().split()
                        column_name = parts[0]
                        column_type = ' '.join(parts[1:])
                        
                        # Check if column exists
                        cursor.execute("PRAGMA table_info(xml_documents)")
                        existing_columns = [column[1] for column in cursor.fetchall()]
                        
                        if column_name not in existing_columns:
                            cursor.execute(f"ALTER TABLE xml_documents ADD COLUMN {column_name} {column_type}")
                            self.logger.info(f"Added column {column_name} to xml_documents table")
                    except Exception as e:
                        self.logger.warning(f"Could not add column {column_def}: {e}")
                
                # Create document_items table with enhanced fields
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER NOT NULL,
                        item_number TEXT,
                        item_code TEXT,
                        item_ean TEXT,
                        item_description TEXT,
                        ncm_code TEXT,
                        cfop TEXT,
                        commercial_unit TEXT,
                        quantity REAL DEFAULT 0,
                        unit_value REAL DEFAULT 0,
                        total_value REAL DEFAULT 0,
                        icms_cst TEXT,
                        icms_base REAL DEFAULT 0,
                        icms_value REAL DEFAULT 0,
                        icms_rate REAL DEFAULT 0,
                        ipi_cst TEXT,
                        ipi_base REAL DEFAULT 0,
                        ipi_value REAL DEFAULT 0,
                        ipi_rate REAL DEFAULT 0,
                        pis_cst TEXT,
                        pis_base REAL DEFAULT 0,
                        pis_value REAL DEFAULT 0,
                        pis_rate REAL DEFAULT 0,
                        cofins_cst TEXT,
                        cofins_base REAL DEFAULT 0,
                        cofins_value REAL DEFAULT 0,
                        cofins_rate REAL DEFAULT 0,
                        tax_rate REAL DEFAULT 0,
                        tax_value REAL DEFAULT 0,
                        additional_info TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES xml_documents (id) ON DELETE CASCADE
                    )
                """)
                
                # Create processing_log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processing_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        processing_time REAL,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create export_history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS export_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        export_type TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        document_count INTEGER DEFAULT 0,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create user_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id TEXT PRIMARY KEY,
                        user_name TEXT NOT NULL,
                        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address TEXT,
                        user_agent TEXT
                    )
                """)
                
                # Create app_cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                self._setup_indexes()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    def _setup_indexes(self):
        """Create database indexes for better performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if new columns exist
                cursor.execute("PRAGMA table_info(document_items)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Indexes for xml_documents
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON xml_documents(file_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON xml_documents(document_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_date ON xml_documents(issue_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_cnpj_issuer ON xml_documents(cnpj_issuer)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON xml_documents(status)")
                
                # Indexes for document_items (only if columns exist)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_document_id ON document_items(document_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_code ON document_items(item_code)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_description ON document_items(item_description)")
                
                # Create new indexes only if columns exist
                if 'ncm_code' in columns:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_ncm ON document_items(ncm_code)")
                if 'cfop' in columns:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_cfop ON document_items(cfop)")
                
                # Indexes for processing_log
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_operation ON processing_log(operation)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_status ON processing_log(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_date ON processing_log(created_at)")
                
                conn.commit()
                self.logger.info("Database indexes created successfully")
                
        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def calculate_file_hash(self, file_path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            # Convert to Path if string
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}")
            raise

    def document_exists(self, file_hash: str = None, access_key: str = None) -> bool:
        """Check if document exists in database using file_hash or access_key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if file_hash:
                    cursor.execute("""
                        SELECT COUNT(*) FROM xml_documents WHERE file_hash = ?
                    """, (file_hash,))
                elif access_key:
                    cursor.execute("""
                        SELECT COUNT(*) FROM xml_documents WHERE access_key = ?
                    """, (access_key,))
                else:
                    return False
                    
                return cursor.fetchone()[0] > 0
        except Exception as e:
            self.logger.error(f"Error checking document existence: {e}")
            return False

    def insert_document(self, document_data: Dict[str, Any]) -> Optional[int]:
        """Insert document into database with comprehensive XML data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current timestamp
                current_time = datetime.now().isoformat()
                
                # Ensure we have a unique identifier
                file_hash = document_data.get('file_hash', '')
                if not file_hash:
                    # Generate a hash from file path + access key + file size as fallback
                    unique_string = f"{document_data.get('file_path', '')}{document_data.get('access_key', '')}{document_data.get('file_size', 0)}"
                    file_hash = hashlib.sha256(unique_string.encode()).hexdigest()
                    document_data['file_hash'] = file_hash
                
                # Check if document already exists
                if self.document_exists(file_hash=file_hash) or self.document_exists(access_key=document_data.get('access_key')):
                    self.logger.info(f"Document already exists: {document_data.get('file_name', 'Unknown')}")
                    return None
                
                # Insert document data into xml_documents table
                insert_query = """
                    INSERT INTO xml_documents (
                        file_name, file_path, file_hash, file_size, document_type, document_number, series, model,
                        issue_date, exit_date, access_key, operation_nature, cnpj_issuer, issuer_name, emitter_fantasy,
                        emitter_ie, emitter_address, emitter_city, emitter_state, emitter_cep, cnpj_recipient,
                        recipient_name, recipient_ie, recipient_address, recipient_city, recipient_state, recipient_cep,
                        total_products, total_freight, total_insurance, total_discount, total_other, total_nfe, total_value,
                        icms_value, ipi_value, pis_value, cofins_value, icms_st_value, icms_base, transport_modality,
                        transporter_name, payment_method, additional_info, protocol_number, protocol_date,
                        status, tax_value, created_at, updated_at, processed_at, processor_version, model_version, processing_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                values = (
                    document_data.get('file_name', ''),
                    document_data.get('file_path', ''),
                    file_hash,  # Use the guaranteed file_hash
                    document_data.get('file_size', 0),
                    document_data.get('document_type', ''),
                    document_data.get('document_number', ''),
                    document_data.get('series', ''),
                    document_data.get('model', ''),
                    document_data.get('issue_date', ''),
                    document_data.get('exit_date', ''),
                    document_data.get('access_key', ''),
                    document_data.get('operation_nature', ''),
                    document_data.get('cnpj_issuer', ''),
                    document_data.get('issuer_name', ''),
                    document_data.get('emitter_fantasy', ''),
                    document_data.get('emitter_ie', ''),
                    document_data.get('emitter_address', ''),
                    document_data.get('emitter_city', ''),
                    document_data.get('emitter_state', ''),
                    document_data.get('emitter_cep', ''),
                    document_data.get('cnpj_recipient', ''),
                    document_data.get('recipient_name', ''),
                    document_data.get('recipient_ie', ''),
                    document_data.get('recipient_address', ''),
                    document_data.get('recipient_city', ''),
                    document_data.get('recipient_state', ''),
                    document_data.get('recipient_cep', ''),
                    float(document_data.get('total_products', 0)) if document_data.get('total_products') else 0.0,
                    float(document_data.get('total_freight', 0)) if document_data.get('total_freight') else 0.0,
                    float(document_data.get('total_insurance', 0)) if document_data.get('total_insurance') else 0.0,
                    float(document_data.get('total_discount', 0)) if document_data.get('total_discount') else 0.0,
                    float(document_data.get('total_other', 0)) if document_data.get('total_other') else 0.0,
                    float(document_data.get('total_nfe', 0)) if document_data.get('total_nfe') else 0.0,
                    float(document_data.get('total_value', 0)) if document_data.get('total_value') else 0.0,
                    float(document_data.get('icms_value', 0)) if document_data.get('icms_value') else 0.0,
                    float(document_data.get('ipi_value', 0)) if document_data.get('ipi_value') else 0.0,
                    float(document_data.get('pis_value', 0)) if document_data.get('pis_value') else 0.0,
                    float(document_data.get('cofins_value', 0)) if document_data.get('cofins_value') else 0.0,
                    float(document_data.get('icms_st_value', 0)) if document_data.get('icms_st_value') else 0.0,
                    float(document_data.get('icms_base', 0)) if document_data.get('icms_base') else 0.0,
                    document_data.get('transport_modality', ''),
                    document_data.get('transporter_name', ''),
                    document_data.get('payment_method', ''),
                    document_data.get('additional_info', ''),
                    document_data.get('protocol_number', ''),
                    document_data.get('protocol_date', ''),
                    document_data.get('status', 'active'),
                    float(document_data.get('tax_value', 0)) if document_data.get('tax_value') else 0.0,
                    current_time,  # created_at
                    current_time,  # updated_at
                    document_data.get('processed_at', current_time),
                    document_data.get('processor_version', '2.0'),
                    document_data.get('model_version', '1.0'),
                    current_time   # processing_date
                )
                
                cursor.execute(insert_query, values)
                
                document_id = cursor.lastrowid
                
                # Insert items if available
                items = document_data.get('items', [])
                if items:
                    self._insert_document_items(cursor, document_id, items)
                
                conn.commit()
                self.logger.info(f"Document inserted successfully with ID: {document_id}")
                return document_id
                
        except Exception as e:
            self.logger.error(f"Error inserting document: {e}")
            self.logger.error(f"Document data: {document_data}")
            return None

    def _insert_document_items(self, cursor, document_id: int, items: List[Dict]):
        """Insert document items into the database with comprehensive fields"""
        try:
            for item in items:
                cursor.execute('''
                    INSERT INTO document_items (
                        document_id, item_number, item_code, item_ean, item_description,
                        ncm_code, cfop, quantity, unit_value, total_value, commercial_unit,
                        icms_cst, icms_base, icms_value, icms_rate,
                        ipi_cst, ipi_base, ipi_value, ipi_rate,
                        pis_cst, pis_base, pis_value, pis_rate,
                        cofins_cst, cofins_base, cofins_value, cofins_rate,
                        tax_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    item.get('item_number', ''),
                    item.get('item_code', ''),
                    item.get('item_ean', ''),
                    item.get('item_description', ''),
                    item.get('ncm_code', ''),
                    item.get('cfop', ''),
                    float(item.get('quantity', 0)) if item.get('quantity') else 0,
                    float(item.get('unit_value', 0)) if item.get('unit_value') else 0,
                    float(item.get('total_value', 0)) if item.get('total_value') else 0,
                    item.get('commercial_unit', ''),
                    item.get('icms_cst', ''),
                    float(item.get('icms_base', 0)) if item.get('icms_base') else 0,
                    float(item.get('icms_value', 0)) if item.get('icms_value') else 0,
                    float(item.get('icms_rate', 0)) if item.get('icms_rate') else 0,
                    item.get('ipi_cst', ''),
                    float(item.get('ipi_base', 0)) if item.get('ipi_base') else 0,
                    float(item.get('ipi_value', 0)) if item.get('ipi_value') else 0,
                    float(item.get('ipi_rate', 0)) if item.get('ipi_rate') else 0,
                    item.get('pis_cst', ''),
                    float(item.get('pis_base', 0)) if item.get('pis_base') else 0,
                    float(item.get('pis_value', 0)) if item.get('pis_value') else 0,
                    float(item.get('pis_rate', 0)) if item.get('pis_rate') else 0,
                    item.get('cofins_cst', ''),
                    float(item.get('cofins_base', 0)) if item.get('cofins_base') else 0,
                    float(item.get('cofins_value', 0)) if item.get('cofins_value') else 0,
                    float(item.get('cofins_rate', 0)) if item.get('cofins_rate') else 0,
                    float(item.get('tax_value', 0)) if item.get('tax_value') else 0
                ))
            
            self.logger.info(f"Items inseridos: {len(items)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir items: {e}")
            raise

    def get_documents(self, filters: Dict = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """Get documents with optional filters and pagination"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM xml_documents"
                params = []
                
                if filters:
                    conditions = []
                    if 'status' in filters:
                        conditions.append("status = ?")
                        params.append(filters['status'])
                    if 'document_type' in filters:
                        conditions.append("document_type = ?")
                        params.append(filters['document_type'])
                    if 'date_from' in filters:
                        conditions.append("issue_date >= ?")
                        params.append(filters['date_from'])
                    if 'date_to' in filters:
                        conditions.append("issue_date <= ?")
                        params.append(filters['date_to'])
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                    if offset:
                        query += f" OFFSET {offset}"
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting documents: {e}")
            return []

    def get_document_items(self, document_id: int) -> List[Dict]:
        """Get document items by document ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM document_items WHERE document_id = ?
                """, (document_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting document items: {e}")
            return []

    def _clear_cache(self):
        """Clear cache"""
        with self.cache_lock:
            self.cache.clear()

    def _start_cleanup_scheduler(self):
        """Start background cleanup scheduler"""
        threading.Thread(target=self._cleanup_scheduler, daemon=True).start()

    def _cleanup_scheduler(self):
        """Cleanup expired documents and cache"""
        while True:
            time.sleep(self.cache_ttl)
            self._clear_cache()
            self._cleanup_expired_documents()

    def _cleanup_expired_documents(self):
        """Cleanup expired documents"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM xml_documents WHERE updated_at < datetime('now', 'localtime', '-? days')
                """, (self.cache_ttl / 86400,))
                conn.commit()
                logging.info(f"Cleanup: {cursor.rowcount} expired documents removed")
        except Exception as e:
            logging.error(f"Error cleaning up expired documents: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total documents
                cursor.execute("SELECT COUNT(*) FROM xml_documents")
                total_documents = cursor.fetchone()[0]
                
                # Documents by type
                cursor.execute("""
                    SELECT document_type, COUNT(*) 
                    FROM xml_documents 
                    GROUP BY document_type
                """)
                documents_by_type = dict(cursor.fetchall())
                
                # Total value
                cursor.execute("SELECT SUM(total_value) FROM xml_documents")
                total_value = cursor.fetchone()[0] or 0
                
                # Total items
                cursor.execute("SELECT COUNT(*) FROM document_items")
                total_items = cursor.fetchone()[0]
                
                # Recent activity (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) FROM xml_documents 
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                recent_documents = cursor.fetchone()[0]
                
                return {
                    'total_documents': total_documents,
                    'documents_by_type': documents_by_type,
                    'total_value': total_value,
                    'total_items': total_items,
                    'recent_documents': recent_documents
                }
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {
                'total_documents': 0,
                'documents_by_type': {},
                'total_value': 0,
                'total_items': 0,
                'recent_documents': 0
            }

    def close(self):
        """Close database connection"""
        try:
            # Clear cache
            self._clear_cache()
            self.logger.info("Database manager closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")

    def clear_all_data(self):
        """Clear all data from database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # List of tables to clear (in order to respect foreign key constraints)
                tables_to_clear = [
                    'document_items',
                    'xml_documents'
                ]
                
                # Clear each table
                for table in tables_to_clear:
                    cursor.execute(f'DELETE FROM {table}')
                    
                # Reset AUTO_INCREMENT counters
                for table in tables_to_clear:
                    cursor.execute(f'DELETE FROM sqlite_sequence WHERE name="{table}"')
                
                # Commit changes
                conn.commit()
                
                self.logger.info("All data cleared from database")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing all data: {e}")
            return False

    def get_enhanced_products(self, filters: Dict = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """Get enhanced product data with comprehensive XML information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        -- Document item fields
                        di.item_number,
                        di.item_code,
                        di.item_ean,
                        di.item_description,
                        di.ncm_code,
                        di.cfop,
                        di.commercial_unit,
                        di.quantity,
                        di.unit_value,
                        di.total_value,
                        di.icms_cst,
                        di.icms_base,
                        di.icms_value,
                        di.icms_rate,
                        di.ipi_cst,
                        di.ipi_base,
                        di.ipi_value,
                        di.ipi_rate,
                        di.pis_cst,
                        di.pis_base,
                        di.pis_value,
                        di.pis_rate,
                        di.cofins_cst,
                        di.cofins_base,
                        di.cofins_value,
                        di.cofins_rate,
                        di.tax_value,
                        
                        -- Document header fields
                        xd.document_type,
                        xd.document_number,
                        xd.series,
                        xd.model,
                        xd.issue_date,
                        xd.exit_date,
                        xd.access_key,
                        xd.protocol_number,
                        xd.protocol_date,
                        xd.operation_nature,
                        
                        -- Emitter information
                        xd.cnpj_issuer,
                        xd.issuer_name,
                        xd.emitter_fantasy,
                        xd.emitter_ie,
                        xd.emitter_address,
                        xd.emitter_city,
                        xd.emitter_state,
                        xd.emitter_cep,
                        
                        -- Recipient information
                        xd.cnpj_recipient,
                        xd.recipient_name,
                        xd.recipient_ie,
                        xd.recipient_address,
                        xd.recipient_city,
                        xd.recipient_state,
                        xd.recipient_cep,
                        
                        -- Financial totals
                        xd.total_products,
                        xd.total_freight,
                        xd.total_insurance,
                        xd.total_discount,
                        xd.total_other,
                        xd.total_nfe,
                        xd.icms_st_value,
                        
                        -- Transport and payment
                        xd.transport_modality,
                        xd.transporter_name,
                        xd.payment_method,
                        
                        -- Additional information
                        xd.additional_info,
                        xd.file_name
                        
                    FROM document_items di
                    LEFT JOIN xml_documents xd ON di.document_id = xd.id
                    WHERE xd.status = 'active'
                """
                
                params = []
                additional_conditions = []
                
                if filters:
                    if 'document_type' in filters and filters['document_type'] != 'Todos':
                        additional_conditions.append("xd.document_type = ?")
                        params.append(filters['document_type'].lower())
                    if 'model' in filters and filters['model']:
                        additional_conditions.append("xd.model = ?")
                        params.append(filters['model'])
                    if 'item_description' in filters:
                        additional_conditions.append("di.item_description LIKE ?")
                        params.append(f"%{filters['item_description']}%")
                    if 'ncm_code' in filters:
                        additional_conditions.append("di.ncm_code = ?")
                        params.append(filters['ncm_code'])
                    if 'cfop' in filters:
                        additional_conditions.append("di.cfop = ?")
                        params.append(filters['cfop'])
                    if 'date_from' in filters:
                        additional_conditions.append("xd.issue_date >= ?")
                        params.append(filters['date_from'])
                    if 'date_to' in filters:
                        additional_conditions.append("xd.issue_date <= ?")
                        params.append(filters['date_to'])
                
                if additional_conditions:
                    query += " AND " + " AND ".join(additional_conditions)
                
                query += " ORDER BY xd.issue_date DESC, di.id DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                    if offset:
                        query += f" OFFSET {offset}"
                
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # Ensure all required fields exist with default values
                    for field in ['document_type', 'document_number', 'series', 'model', 'issue_date', 'exit_date',
                                'access_key', 'protocol_number', 'protocol_date', 'operation_nature',
                                'cnpj_issuer', 'issuer_name', 'emitter_fantasy', 'emitter_ie',
                                'emitter_address', 'emitter_city', 'emitter_state', 'emitter_cep',
                                'cnpj_recipient', 'recipient_name', 'recipient_ie',
                                'recipient_address', 'recipient_city', 'recipient_state',
                                'item_number', 'item_code', 'item_description', 'ncm_code', 'cfop', 'item_ean',
                                'quantity', 'commercial_unit', 'unit_value', 'total_value',
                                'icms_cst', 'icms_base', 'icms_value', 'icms_rate',
                                'ipi_cst', 'ipi_base', 'ipi_value', 'ipi_rate',
                                'pis_cst', 'pis_base', 'pis_value', 'pis_rate',
                                'cofins_cst', 'cofins_base', 'cofins_value', 'cofins_rate',
                                'total_products', 'total_freight', 'total_insurance', 'total_discount',
                                'total_other', 'total_nfe', 'tax_value', 'icms_st_value',
                                'transport_modality', 'transporter_name', 'payment_method',
                                'additional_info', 'file_name']:
                        if field not in row_dict:
                            row_dict[field] = '' if field in ['document_type', 'document_number', 'series', 'model',
                                                            'access_key', 'protocol_number', 'operation_nature',
                                                            'cnpj_issuer', 'issuer_name', 'emitter_fantasy', 'emitter_ie',
                                                            'emitter_address', 'emitter_city', 'emitter_state', 'emitter_cep',
                                                            'cnpj_recipient', 'recipient_name', 'recipient_ie',
                                                            'recipient_address', 'recipient_city', 'recipient_state',
                                                            'item_number', 'item_code', 'item_description', 'ncm_code', 
                                                            'cfop', 'item_ean', 'commercial_unit',
                                                            'icms_cst', 'ipi_cst', 'pis_cst', 'cofins_cst',
                                                            'transport_modality', 'transporter_name', 'payment_method',
                                                            'additional_info', 'file_name'] else 0.0
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting enhanced products: {e}")
            return []

    def get_product_statistics(self) -> Dict[str, Any]:
        """Get product statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total products
                cursor.execute("SELECT COUNT(*) FROM document_items")
                total_products = cursor.fetchone()[0]
                
                # Products by NCM
                cursor.execute("""
                    SELECT ncm_code, COUNT(*) 
                    FROM document_items 
                    WHERE ncm_code IS NOT NULL AND ncm_code != ''
                    GROUP BY ncm_code 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """)
                products_by_ncm = dict(cursor.fetchall())
                
                # Products by CFOP
                cursor.execute("""
                    SELECT cfop, COUNT(*) 
                    FROM document_items 
                    WHERE cfop IS NOT NULL AND cfop != ''
                    GROUP BY cfop 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """)
                products_by_cfop = dict(cursor.fetchall())
                
                # Total value
                cursor.execute("SELECT SUM(total_value) FROM document_items")
                total_value = cursor.fetchone()[0] or 0
                
                return {
                    'total_products': total_products,
                    'products_by_ncm': products_by_ncm,
                    'products_by_cfop': products_by_cfop,
                    'total_value': total_value
                }
                
        except Exception as e:
            self.logger.error(f"Error getting product statistics: {e}")
            return {
                'total_products': 0,
                'products_by_ncm': {},
                'products_by_cfop': {},
                'total_value': 0
            } 