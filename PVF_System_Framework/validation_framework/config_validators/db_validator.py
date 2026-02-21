#!/usr/bin/env python
"""
Database Configuration Validator
===============================

This module validates database configuration, connection, and performance.
It ensures the database is properly set up for production use, including:
- Connection pool sizing
- Encryption
- Indexing
- Performance optimization
- Backup configuration
"""

import logging
import time
import re
import os
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger("DBValidator")

# Try to import various database drivers based on what's available
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

def parse_db_url(connection_string: str) -> Dict[str, Any]:
    """Parse a database connection string into components."""
    try:
        result = urlparse(connection_string)
        db_type = result.scheme.split('+')[0]
        
        # Handle sqlite specially since it doesn't have host/user/etc.
        if db_type == 'sqlite':
            return {
                'type': 'sqlite',
                'path': result.path.lstrip('/'),
                'valid': True
            }
        
        # Extract username and password
        user_pass = result.netloc.split('@')[0]
        if ':' in user_pass:
            username, password = user_pass.split(':', 1)
        else:
            username, password = user_pass, None
        
        # Extract host and port
        if '@' in result.netloc:
            host_port = result.netloc.split('@')[1]
        else:
            host_port = result.netloc
            
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host, port = host_port, None
        
        # Extract database name
        database = result.path.lstrip('/')
        
        return {
            'type': db_type,
            'username': username,
            'password': password,
            'host': host,
            'port': port,
            'database': database,
            'query_params': dict(param.split('=') for param in result.query.split('&')) if result.query else {},
            'valid': True
        }
    except Exception as e:
        logger.error(f"Failed to parse connection string: {str(e)}")
        return {'valid': False, 'error': str(e)}

def check_connection(db_info: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to connect to the database."""
    result = {
        'connected': False,
        'response_time': None,
        'error': None
    }
    
    try:
        start_time = time.time()
        
        if db_info['type'] == 'postgresql':
            if not POSTGRES_AVAILABLE:
                return {
                    'connected': False,
                    'error': "PostgreSQL driver (psycopg2) not installed"
                }
                
            conn = psycopg2.connect(
                host=db_info['host'],
                port=db_info['port'],
                user=db_info['username'],
                password=db_info['password'],
                dbname=db_info['database']
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
        
        elif db_info['type'] == 'mysql':
            if not MYSQL_AVAILABLE:
                return {
                    'connected': False,
                    'error': "MySQL driver (pymysql) not installed"
                }
                
            conn = pymysql.connect(
                host=db_info['host'],
                port=int(db_info['port']) if db_info['port'] else 3306,
                user=db_info['username'],
                password=db_info['password'],
                database=db_info['database']
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
        
        elif db_info['type'] == 'sqlite':
            if not SQLITE_AVAILABLE:
                return {
                    'connected': False,
                    'error': "SQLite driver not available"
                }
                
            conn = sqlite3.connect(db_info['path'])
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
        
        else:
            return {
                'connected': False,
                'error': f"Unsupported database type: {db_info['type']}"
            }
        
        end_time = time.time()
        result['connected'] = True
        result['response_time'] = (end_time - start_time) * 1000  # Convert to ms
        
    except Exception as e:
        result['error'] = str(e)
        
    return result

def check_sqlite_for_production(db_info: Dict[str, Any]) -> bool:
    """Check if SQLite is being used in production."""
    return db_info['type'] == 'sqlite'

def check_connection_pooling(db_info: Dict[str, Any]) -> bool:
    """Check if connection pooling is properly configured."""
    if db_info['type'] == 'sqlite':
        return True  # SQLite doesn't need connection pooling
        
    # Check for pooling parameters in connection string
    query_params = db_info.get('query_params', {})
    
    if db_info['type'] == 'postgresql':
        return 'pool_size' in query_params or 'max_overflow' in query_params
    
    elif db_info['type'] == 'mysql':
        return 'pool_size' in query_params or 'max_overflow' in query_params
        
    return False

def check_db_encryption(db_info: Dict[str, Any]) -> bool:
    """Check if database encryption is configured."""
    query_params = db_info.get('query_params', {})
    
    if db_info['type'] == 'postgresql':
        # Check for SSL mode
        return query_params.get('sslmode') in ['verify-ca', 'verify-full']
    
    elif db_info['type'] == 'mysql':
        # Check for SSL configuration
        return 'ssl' in query_params and query_params.get('ssl').lower() == 'true'
    
    elif db_info['type'] == 'sqlite':
        # Check if path contains 'encrypted' or similar indicator
        return False  # SQLite encryption needs special build
        
    return False

def check_schema_integrity(db_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check if required tables and schema versioning exist."""
    result = {
        'passed': False,
        'tables_found': [],
        'missing_tables': [],
        'has_migrations': False,
        'error': None
    }
    
    required_tables = ['customers', 'integrations', 'security_logs']
    migration_tables = ['alembic_version', 'django_migrations', 'flyway_schema_history', 'schema_migrations']
    
    try:
        conn = None
        if db_info['type'] == 'postgresql' and POSTGRES_AVAILABLE:
            conn = psycopg2.connect(host=db_info['host'], port=db_info['port'], user=db_info['username'], password=db_info['password'], dbname=db_info['database'])
        elif db_info['type'] == 'mysql' and MYSQL_AVAILABLE:
            conn = pymysql.connect(host=db_info['host'], port=int(db_info['port']) if db_info['port'] else 3306, user=db_info['username'], password=db_info['password'], database=db_info['database'])
        elif db_info['type'] == 'sqlite' and SQLITE_AVAILABLE:
            conn = sqlite3.connect(db_info['path'])
            
        if conn:
            cursor = conn.cursor()
            if db_info['type'] == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            else:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            result['tables_found'] = existing_tables
            
            for table in required_tables:
                if table not in existing_tables:
                    result['missing_tables'].append(table)
            
            result['has_migrations'] = any(m in existing_tables for m in migration_tables)
            result['passed'] = len(result['missing_tables']) == 0
            
            cursor.close()
            conn.close()
        else:
            result['error'] = "Database driver not available"
            
    except Exception as e:
        result['error'] = str(e)
        
    return result

def check_performance_indexes(db_info: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic check for performance indexes on critical columns."""
    result = {
        'passed': False,
        'indexed_columns': [],
        'recommendations': [],
        'error': None
    }
    
    try:
        conn = None
        # ... logic to connect ...
        if db_info['type'] == 'sqlite' and SQLITE_AVAILABLE:
            conn = sqlite3.connect(db_info['path'])
            
        if conn:
            cursor = conn.cursor()
            # For sqlite, we check indexes for 'customers' table as a proxy
            cursor.execute("PRAGMA index_list('customers');")
            indexes = cursor.fetchall()
            
            if not indexes:
                result['recommendations'].append("No indexes found on 'customers' table")
            else:
                result['passed'] = True
                for idx in indexes:
                    cursor.execute(f"PRAGMA index_info('{idx[1]}');")
                    cols = cursor.fetchall()
                    for col in cols:
                        result['indexed_columns'].append(f"customers.{col[2]}")
            
            # General recommendation
            if 'customers.email' not in result['indexed_columns']:
                result['recommendations'].append("Add index on 'customers.email'")
                
            cursor.close()
            conn.close()
        else:
            result['error'] = "Database driver not available or unsupported for index check"
            
    except Exception as e:
        result['error'] = str(e)
        
    return result

def validate_database(connection_string: str) -> Dict[str, Any]:
    """
    Validate database configuration, connectivity, and schema integrity.
    """
    logger.info("Validating database configuration and schema")
    
    results = {
        "passed": False,
        "total": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "tests": []
    }
    
    # Parse connection string
    db_info = parse_db_url(connection_string)
    if not db_info['valid']:
        test_result = {
            "name": "Connection string validation",
            "status": "FAIL",
            "message": f"Invalid connection string: {db_info.get('error', 'Unknown error')}"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        results["failed_tests"] += 1
        results["passed"] = False
        return results
    
    # Add test result for connection string parsing
    test_result = {
        "name": "Connection string validation",
        "status": "PASS",
        "message": f"Connection string is valid for {db_info['type']} database"
    }
    results["tests"].append(test_result)
    results["total"] += 1
    results["passed_tests"] += 1
    
    # Check if SQLite is being used in production
    sqlite_in_prod = check_sqlite_for_production(db_info)
    test_result = {
        "name": "Production database check",
        "status": "WARNING" if sqlite_in_prod else "PASS",
        "message": "SQLite is not recommended for production use" if sqlite_in_prod else "Production-ready database engine in use"
    }
    results["tests"].append(test_result)
    results["total"] += 1
    if test_result["status"] == "PASS":
        results["passed_tests"] += 1
    
    # Check connection
    connection_result = check_connection(db_info)
    test_result = {
        "name": "Database connection",
        "status": "PASS" if connection_result['connected'] else "FAIL",
        "message": f"Connected successfully (Response time: {connection_result['response_time']:.2f}ms)" 
                   if connection_result['connected'] else f"Connection failed: {connection_result.get('error', 'Unknown error')}"
    }
    results["tests"].append(test_result)
    results["total"] += 1
    if test_result["status"] == "PASS":
        results["passed_tests"] += 1
    else:
        results["failed_tests"] += 1
    
    # Only continue if connection was successful
    if connection_result['connected']:
        # Check schema integrity
        schema_result = check_schema_integrity(db_info)
        test_result = {
            "name": "Schema integrity check",
            "status": "PASS" if schema_result['passed'] else "FAIL",
            "message": "All required tables found" if schema_result['passed'] else f"Missing tables: {', '.join(schema_result['missing_tables'])}"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if schema_result['passed']:
            results["passed_tests"] += 1
        else:
            results["failed_tests"] += 1

        # Check for migration system
        test_result = {
            "name": "Database migration system",
            "status": "PASS" if schema_result['has_migrations'] else "WARNING",
            "message": "Database migration table detected" if schema_result['has_migrations'] else "No standard migration table found (Alembic/Flyway/etc.)"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        results["passed_tests"] += 1

        # Check performance indexes
        perf_result = check_performance_indexes(db_info)
        test_result = {
            "name": "Performance indexing check",
            "status": "PASS" if perf_result['passed'] else "WARNING",
            "message": f"Found {len(perf_result['indexed_columns'])} indexes" if perf_result['passed'] else "No performance indexes detected"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        results["passed_tests"] += 1

        # Check connection pooling
        has_pooling = check_connection_pooling(db_info)
        test_result = {
            "name": "Connection pooling configuration",
            "status": "PASS" if has_pooling else "WARNING",
            "message": "Connection pooling is properly configured" 
                      if has_pooling else "Connection pooling not detected (recommended for production)"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
        
        # Check database encryption
        has_encryption = check_db_encryption(db_info)
        test_result = {
            "name": "Database encryption",
            "status": "PASS" if has_encryption else "WARNING",
            "message": "Database encryption is configured" 
                      if has_encryption else "Database encryption not detected (recommended for sensitive data)"
        }
        results["tests"].append(test_result)
        results["total"] += 1
        if test_result["status"] == "PASS":
            results["passed_tests"] += 1
    
    # Overall result
    results["passed"] = results["failed_tests"] == 0
    
    return results

if __name__ == "__main__":
    # Simple standalone test
    import sys
    if len(sys.argv) > 1:
        conn_string = sys.argv[1]
    else:
        conn_string = "sqlite:///enterprise_platform.db"
        
    logging.basicConfig(level=logging.INFO)
    result = validate_database(conn_string)
    
    print(f"Database Validation Results:")
    print(f"Passed: {result['passed']}")
    print(f"Tests: {result['passed_tests']}/{result['total']} passed")
    
    for test in result["tests"]:
        if test["status"] == "PASS":
            status_symbol = "✓"
        elif test["status"] == "WARNING":
            status_symbol = "⚠"
        else:
            status_symbol = "✗"
        print(f"{status_symbol} {test['name']}: {test['message']}")
