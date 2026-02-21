#!/usr/bin/env python3
"""
🗄️ REAL DATABASE MODULE
========================
Provides production-ready SQLite implementation for the validation framework.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

class RealDatabase:
    def __init__(self, db_url: str = None):
        if db_url and db_url.startswith('sqlite:///'):
            self.db_path = db_url.replace('sqlite:///', '')
        else:
            self.db_path = os.environ.get("DATABASE_PATH", "data/enterprise_platform.db")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> bool:
        """Initialize database tables"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create customers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    email TEXT,
                    health_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create integrations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS integrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    integration_type TEXT NOT NULL,
                    config TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            
            # Create security_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    severity TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    def create_customer(self, customer_data: Dict[str, Any]) -> int:
        """Create a new customer"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, tier, email) VALUES (?, ?, ?)",
            (customer_data['name'], customer_data['tier'], customer_data.get('email'))
        )
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return customer_id

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a customer by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_customer_health(self, customer_id: int, health_score: float) -> bool:
        """Update customer health score"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE customers SET health_score = ? WHERE id = ?",
            (health_score, customer_id)
        )
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0

    def create_integration(self, integration_data: Dict[str, Any]) -> int:
        """Create a new integration for a customer"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO integrations (customer_id, integration_type, config) VALUES (?, ?, ?)",
            (integration_data['customer_id'], integration_data['integration_type'], json.dumps(integration_data.get('config', {})))
        )
        integration_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return integration_id

    def get_customer_integrations(self, customer_id: int) -> List[Dict[str, Any]]:
        """Retrieve all integrations for a customer"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM integrations WHERE customer_id = ?", (customer_id,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            d = dict(row)
            if d['config']:
                try:
                    d['config'] = json.loads(d['config'])
                except json.JSONDecodeError:
                    pass
            results.append(d)
        return results

    def get_customer_dashboard(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Generate a dashboard summary for a customer"""
        customer = self.get_customer(customer_id)
        if not customer:
            return None
            
        integrations = self.get_customer_integrations(customer_id)
        
        return {
            "customer_info": customer,
            "health_score": customer['health_score'],
            "integrations": integrations,
            "recent_activity": [] # Functional structure for future expansion
        }

# Singleton instance
real_db = RealDatabase()
