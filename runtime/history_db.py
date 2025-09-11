"""
Database module for storing conversation and execution history
"""

import sqlite3
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

class HistoryDB:
    """SQLite database for storing conversation and execution history"""

    def __init__(self, db_path: str = "./logs/history.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self._local = threading.local()
        # Create tables on first init
        with self._get_conn() as conn:
            self.create_tables(conn)

    def _get_conn(self):
        """Get a thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
        return self._local.conn

    def create_tables(self, conn):
        """Create necessary tables if they don't exist"""
        cursor = conn.cursor()
        
        # Sessions table for tracking each EDA run
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            csv_path TEXT,
            user_goal TEXT,
            max_items INTEGER,
            success BOOLEAN,
            profile TEXT,  -- JSON
            report_path TEXT,
            artifacts_dir TEXT,
            error TEXT
        )
        ''')

        # Plan versions table for tracking plan iterations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            version_number INTEGER,
            timestamp TEXT,
            plan_items TEXT,  -- JSON
            user_feedback TEXT,
            approved BOOLEAN,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        ''')

        # Execution results table for tracking each item's execution
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            item_id TEXT,
            timestamp TEXT,
            code_output TEXT,  -- JSON
            exec_result TEXT,  -- JSON
            critique_result TEXT,  -- JSON
            success BOOLEAN,
            retry_count INTEGER,
            error TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        ''')

        conn.commit()

    def start_session(self, csv_path: str, user_goal: str, max_items: int) -> int:
        """Start a new EDA session and return the session ID"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO sessions (timestamp, csv_path, user_goal, max_items)
            VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), csv_path, user_goal, max_items))
            conn.commit()
            return cursor.lastrowid

    def save_plan_version(self, session_id: int, version_number: int, 
                         plan_items: List[Dict[str, Any]], user_feedback: Optional[str] = None,
                         approved: bool = False) -> int:
        """Save a plan version for a session"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO plan_versions (session_id, version_number, timestamp, plan_items, user_feedback, approved)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, version_number, datetime.now().isoformat(), 
                  json.dumps(plan_items), user_feedback, approved))
            conn.commit()
            return cursor.lastrowid

    def save_execution_result(self, session_id: int, item_id: str, 
                            code_output: Dict[str, Any], exec_result: Dict[str, Any],
                            critique_result: Dict[str, Any], success: bool,
                            retry_count: int = 0, error: Optional[str] = None) -> int:
        """Save execution result for an item"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO execution_results 
            (session_id, item_id, timestamp, code_output, exec_result, critique_result, 
             success, retry_count, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, item_id, datetime.now().isoformat(),
                  json.dumps(code_output), json.dumps(exec_result),
                  json.dumps(critique_result), success, retry_count, error))
            conn.commit()
            return cursor.lastrowid

    def complete_session(self, session_id: int, success: bool, profile: Dict[str, Any],
                        report_path: Optional[str] = None, artifacts_dir: Optional[str] = None,
                        error: Optional[str] = None):
        """Update session with completion details"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE sessions 
            SET success = ?, profile = ?, report_path = ?, artifacts_dir = ?, error = ?
            WHERE session_id = ?
            ''', (success, json.dumps(profile), report_path, artifacts_dir, error, session_id))
            conn.commit()

    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent session history with their plans and results"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT s.*, 
                   COUNT(DISTINCT p.version_id) as plan_versions,
                   COUNT(DISTINCT e.result_id) as executions,
                   SUM(CASE WHEN e.success = 1 THEN 1 ELSE 0 END) as successful_executions
            FROM sessions s
            LEFT JOIN plan_versions p ON s.session_id = p.session_id
            LEFT JOIN execution_results e ON s.session_id = e.session_id
            GROUP BY s.session_id
            ORDER BY s.timestamp DESC
            LIMIT ?
            ''', (limit,))
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific session"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
            session = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
            
            # Get plan versions
            cursor.execute('SELECT * FROM plan_versions WHERE session_id = ? ORDER BY version_number', (session_id,))
            plan_columns = [col[0] for col in cursor.description]
            session['plan_versions'] = [dict(zip(plan_columns, row)) for row in cursor.fetchall()]
            
            # Get execution results
            cursor.execute('SELECT * FROM execution_results WHERE session_id = ? ORDER BY timestamp', (session_id,))
            exec_columns = [col[0] for col in cursor.description]
            session['execution_results'] = [dict(zip(exec_columns, row)) for row in cursor.fetchall()]
            
            return session

    def close(self):
        """Close the database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn
