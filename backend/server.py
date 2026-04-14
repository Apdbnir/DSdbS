"""
Educational Process Management System - HTTP Server
Provides REST API for database operations with role-based access control
"""

import json
import hashlib
import logging
import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'server.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Table configuration
TABLES = {
    'employees': {
        'table': 'employees',
        'primary_key': 'id',
        'lookup': False,
        'url': '/api/employees'
    },
    'students': {
        'table': 'students',
        'primary_key': 'id',
        'lookup': False,
        'url': '/api/students'
    },
    'groups': {
        'table': 'groups',
        'primary_key': 'id',
        'lookup': True,
        'url': '/api/groups'
    },
    'lessons': {
        'table': 'lessons',
        'primary_key': 'id',
        'lookup': False,
        'url': '/api/lessons'
    },
    'positions': {
        'table': 'positions',
        'primary_key': 'id',
        'lookup': True,
        'url': '/api/positions'
    },
    'locations': {
        'table': 'locations',
        'primary_key': 'id',
        'lookup': True,
        'url': '/api/locations'
    },
    'vehicles': {
        'table': 'vehicles',
        'primary_key': 'id',
        'lookup': True,
        'url': '/api/vehicles'
    },
    'lesson-formats': {
        'table': 'lesson_formats',
        'primary_key': 'id',
        'lookup': True,
        'url': '/api/lesson-formats'
    },
    'student-lessons': {
        'table': 'student_lessons',
        'primary_key': ('student_id', 'lesson_id'),
        'lookup': False,
        'url': '/api/student-lessons'
    },
    'group-lessons': {
        'table': 'group_lessons',
        'primary_key': ('group_id', 'lesson_id'),
        'lookup': False,
        'url': '/api/group-lessons'
    }
}


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.db_config = CONFIG['database']
        self.lookup_tables = CONFIG.get('lookup_tables', [])
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            dbname=self.db_config['name'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a database query"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                # Convert datetime and other non-serializable types
                result = [self._serialize_row(row) for row in result]
                cursor.close()
                conn.close()
                return result
            else:
                conn.commit()
                last_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
                cursor.close()
                conn.close()
                return last_id
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Database error: {e}")
            raise
    
    def _serialize_row(self, row):
        """Convert row to JSON-serializable format"""
        serialized = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):  # date objects
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
    
    def get_all(self, table_name, limit=100, offset=0, filters=None):
        """Get all records from a table"""
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        query = f"SELECT * FROM public.{table_info['table']}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY {table_info['primary_key'] if isinstance(table_info['primary_key'], str) else table_info['primary_key'][0]} LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.execute_query(query, params)
    
    def get_by_id(self, table_name, record_id):
        """Get a single record by ID"""
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        if isinstance(table_info['primary_key'], tuple):
            # Composite key (for association tables)
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"SELECT * FROM public.{table_info['table']} WHERE {conditions}"
            return self.execute_query(query, record_id)
        else:
            query = f"SELECT * FROM public.{table_info['table']} WHERE {table_info['primary_key']} = %s"
            result = self.execute_query(query, [record_id])
            return result[0] if result else None
    
    def create(self, table_name, data):
        """Create a new record"""
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO public.{table_info['table']} ({columns}) VALUES ({placeholders}) RETURNING *"
        
        result = self.execute_query(query, list(data.values()))
        return result[0] if result else None
    
    def update(self, table_name, record_id, data):
        """Update an existing record"""
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        
        if isinstance(table_info['primary_key'], tuple):
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"UPDATE public.{table_info['table']} SET {set_clause} WHERE {conditions} RETURNING *"
            params = list(data.values()) + list(record_id)
        else:
            query = f"UPDATE public.{table_info['table']} SET {set_clause} WHERE {table_info['primary_key']} = %s RETURNING *"
            params = list(data.values()) + [record_id]
        
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def delete(self, table_name, record_id):
        """Delete a record"""
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        if isinstance(table_info['primary_key'], tuple):
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"DELETE FROM public.{table_info['table']} WHERE {conditions} RETURNING *"
            params = list(record_id)
        else:
            query = f"DELETE FROM public.{table_info['table']} WHERE {table_info['primary_key']} = %s RETURNING *"
            params = [record_id]
        
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def get_statistics(self):
        """Get database statistics"""
        stats = {}
        for table_name, table_info in TABLES.items():
            count = self.execute_query(f"SELECT COUNT(*) as count FROM public.{table_info['table']}")
            stats[table_name] = count[0]['count'] if count else 0
        return stats
    
    def create_backup(self, backup_dir=None):
        """Create database backup"""
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
        
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"educational_process_{timestamp}.sql")
        
        try:
            db = self.db_config
            pg_bin = os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\16\bin')
            pg_dump = os.path.join(pg_bin, 'pg_dump.exe')
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db['password']
            
            cmd = [
                pg_dump,
                '-U', db['user'],
                '-h', db['host'],
                '-p', str(db['port']),
                '-d', db['name'],
                '-F', 'p',
                '-f', backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'status': 'success', 'file': backup_file}
            else:
                return {'status': 'error', 'message': result.stderr}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


# Initialize database manager
db_manager = DatabaseManager()


def authenticate_superuser(auth_header):
    """Authenticate superuser via Bearer token"""
    if not auth_header:
        return False
    
    try:
        token = auth_header.replace('Bearer ', '')
        # Hash the provided password and compare
        hashed = hashlib.sha256(token.encode()).hexdigest()
        stored_hash = hashlib.sha256(CONFIG['admin_password'].encode()).hexdigest()
        return hashed == stored_hash
    except Exception:
        return False


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for REST API"""
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _send_response(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def _send_error(self, message, status_code=400):
        """Send error response"""
        self._send_response({'error': message}, status_code)
    
    def _read_body(self):
        """Read request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        return {}
    
    def _parse_url(self):
        """Parse URL and return path and query params"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        return path, query
    
    def _get_table_from_path(self, path):
        """Extract table name from URL path"""
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'api':
            return parts[1], parts[2] if len(parts) > 2 else None
        return None, None
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers(200)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            path, query = self._parse_url()
            table_name, record_id = self._get_table_from_path(path)
            
            if not table_name or table_name not in TABLES:
                self._send_error('Unknown endpoint', 404)
                return
            
            # Get single record
            if record_id:
                # Handle composite keys
                if isinstance(TABLES[table_name]['primary_key'], tuple):
                    keys = TABLES[table_name]['primary_key']
                    record_id = tuple([record_id] + self.path.split('/')[-len(keys)+1:])
                
                record = db_manager.get_by_id(table_name, record_id)
                if record:
                    self._send_response(record)
                else:
                    self._send_error('Record not found', 404)
                return
            
            # Get all records with optional filters
            limit = int(query.get('limit', [100])[0])
            offset = int(query.get('offset', [0])[0])
            
            filters = {}
            for key, value in query.items():
                if key not in ['limit', 'offset']:
                    filters[key] = value[0]
            
            records = db_manager.get_all(table_name, limit, offset, filters if filters else None)
            self._send_response(records)
            
        except Exception as e:
            logger.error(f"GET error: {e}")
            self._send_error(str(e), 500)
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            path, _ = self._parse_url()
            table_name, _ = self._get_table_from_path(path)
            
            if not table_name or table_name not in TABLES:
                self._send_error('Unknown endpoint', 404)
                return
            
            # Check if it's a special operation
            if path == '/api/backup':
                auth_header = self.headers.get('Authorization')
                if not authenticate_superuser(auth_header):
                    self._send_error('Superuser authentication required', 403)
                    return
                
                result = db_manager.create_backup()
                self._send_response(result)
                return
            
            if path == '/api/statistics':
                stats = db_manager.get_statistics()
                self._send_response(stats)
                return
            
            # Check if table is lookup table (requires superuser)
            if TABLES[table_name].get('lookup', False):
                auth_header = self.headers.get('Authorization')
                if not authenticate_superuser(auth_header):
                    self._send_error('Superuser authentication required for lookup tables', 403)
                    return
            
            # Create new record
            data = self._read_body()
            record = db_manager.create(table_name, data)
            
            if record:
                self._send_response(record, 201)
            else:
                self._send_error('Failed to create record', 500)
            
        except Exception as e:
            logger.error(f"POST error: {e}")
            self._send_error(str(e), 500)
    
    def do_PUT(self):
        """Handle PUT requests"""
        try:
            path, _ = self._parse_url()
            table_name, record_id = self._get_table_from_path(path)
            
            if not table_name or table_name not in TABLES:
                self._send_error('Unknown endpoint', 404)
                return
            
            if not record_id:
                self._send_error('Record ID required', 400)
                return
            
            # Check if table is lookup table (requires superuser)
            if TABLES[table_name].get('lookup', False):
                auth_header = self.headers.get('Authorization')
                if not authenticate_superuser(auth_header):
                    self._send_error('Superuser authentication required for lookup tables', 403)
                    return
            
            # Update record
            data = self._read_body()
            
            # Handle composite keys
            if isinstance(TABLES[table_name]['primary_key'], tuple):
                keys = TABLES[table_name]['primary_key']
                record_id = tuple([record_id] + self.path.split('/')[-len(keys)+1:])
            
            record = db_manager.update(table_name, record_id, data)
            
            if record:
                self._send_response(record)
            else:
                self._send_error('Record not found', 404)
            
        except Exception as e:
            logger.error(f"PUT error: {e}")
            self._send_error(str(e), 500)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        try:
            path, _ = self._parse_url()
            table_name, record_id = self._get_table_from_path(path)
            
            if not table_name or table_name not in TABLES:
                self._send_error('Unknown endpoint', 404)
                return
            
            if not record_id:
                self._send_error('Record ID required', 400)
                return
            
            # Check if table is lookup table (requires superuser)
            if TABLES[table_name].get('lookup', False):
                auth_header = self.headers.get('Authorization')
                if not authenticate_superuser(auth_header):
                    self._send_error('Superuser authentication required for lookup tables', 403)
                    return
            
            # Delete record
            if isinstance(TABLES[table_name]['primary_key'], tuple):
                keys = TABLES[table_name]['primary_key']
                record_id = tuple([record_id] + self.path.split('/')[-len(keys)+1:])
            
            record = db_manager.delete(table_name, record_id)
            
            if record:
                self._send_response({'message': 'Record deleted successfully'})
            else:
                self._send_error('Record not found', 404)
            
        except Exception as e:
            logger.error(f"DELETE error: {e}")
            self._send_error(str(e), 500)
    
    def log_message(self, format, *args):
        """Override to use logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_server(port=None):
    """Start the HTTP server"""
    if port is None:
        port = CONFIG.get('port', 8080)
    
    server = HTTPServer((CONFIG.get('host', 'localhost'), port), RequestHandler)
    logger.info(f"Server starting on http://{CONFIG.get('host', 'localhost')}:{port}")
    logger.info("API Endpoints:")
    for table_name, table_info in TABLES.items():
        logger.info(f"  {table_info['url']} - {table_info['table']}")
    logger.info("Special endpoints:")
    logger.info("  POST /api/backup - Create backup (superuser only)")
    logger.info("  GET /api/statistics - Get database statistics")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.shutdown()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_server(port)
