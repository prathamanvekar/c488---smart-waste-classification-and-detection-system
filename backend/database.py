"""
Database Module
SQLite database models and CRUD operations
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
import json


# Database path
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'waste.db')


def get_db_connection():
    """
    Get SQLite database connection

    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """
    Initialize database and create tables if they don't exist
    Automatically called on first import
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            waste_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            eco_points INTEGER DEFAULT 0,
            image_path TEXT,
            bbox TEXT
        )
    ''')

    # Create analytics table (aggregated stats per waste class)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            waste_class TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            total_confidence REAL DEFAULT 0,
            last_detected DATETIME
        )
    ''')

    # Create system_stats table (overall statistics)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_stats (
            stat_key TEXT PRIMARY KEY,
            stat_value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Initialize system stats if not exists
    cursor.execute('''
        INSERT OR IGNORE INTO system_stats (stat_key, stat_value)
        VALUES ('total_detections', '0'),
               ('total_eco_points', '0'),
               ('avg_confidence', '0')
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


def insert_detection(waste_class, confidence, eco_points=0, image_path=None, bbox=None):
    """
    Insert a new detection record into the database

    Args:
        waste_class (str): Detected waste class name
        confidence (float): Detection confidence score
        eco_points (int): Eco-points earned for this detection
        image_path (str, optional): Path to detected image
        bbox (dict, optional): Bounding box coordinates

    Returns:
        int: ID of inserted detection, or None on failure
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convert bbox dict to JSON string if provided
        bbox_json = json.dumps(bbox) if bbox else None

        # Insert detection
        cursor.execute('''
            INSERT INTO detections (waste_class, confidence, eco_points, image_path, bbox)
            VALUES (?, ?, ?, ?, ?)
        ''', (waste_class, confidence, eco_points, image_path, bbox_json))

        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update analytics after successful insertion
        update_analytics(waste_class, confidence)

        return detection_id

    except Exception as e:
        print(f"Error inserting detection: {str(e)}")
        return None


def update_analytics(waste_class, confidence):
    """
    Update analytics table with new detection data
    Increments count and updates running totals

    Args:
        waste_class (str): Detected waste class
        confidence (float): Detection confidence
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update or insert analytics for this class
        cursor.execute('''
            INSERT INTO analytics (waste_class, count, total_confidence, last_detected)
            VALUES (?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(waste_class) DO UPDATE SET
                count = count + 1,
                total_confidence = total_confidence + ?,
                last_detected = CURRENT_TIMESTAMP
        ''', (waste_class, confidence, confidence))

        # Update system-wide statistics
        cursor.execute('''
            UPDATE system_stats
            SET stat_value = CAST(CAST(stat_value AS INTEGER) + 1 AS TEXT),
                updated_at = CURRENT_TIMESTAMP
            WHERE stat_key = 'total_detections'
        ''')

        # Update average confidence
        cursor.execute('''
            SELECT AVG(confidence) as avg_conf FROM detections
        ''')
        avg_conf = cursor.fetchone()['avg_conf']

        cursor.execute('''
            UPDATE system_stats
            SET stat_value = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE stat_key = 'avg_confidence'
        ''', (str(round(avg_conf, 4)),))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error updating analytics: {str(e)}")


def get_detection_history(limit=50, offset=0, waste_class=None):
    """
    Get detection history from database

    Args:
        limit (int): Maximum number of records to return
        offset (int): Offset for pagination
        waste_class (str, optional): Filter by specific waste class

    Returns:
        list: List of detection records as dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if waste_class:
            cursor.execute('''
                SELECT * FROM detections
                WHERE waste_class = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (waste_class, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM detections
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        # Convert rows to list of dictionaries
        detections = []
        for row in rows:
            detection = dict(row)
            # Parse bbox JSON if exists
            if detection['bbox']:
                detection['bbox'] = json.loads(detection['bbox'])
            detections.append(detection)

        return detections

    except Exception as e:
        print(f"Error getting detection history: {str(e)}")
        return []


def get_analytics_summary():
    """
    Get comprehensive analytics summary

    Returns:
        dict: Analytics data including:
            - total_detections
            - avg_confidence
            - class_distribution
            - recent_activity
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get system stats
        cursor.execute('SELECT * FROM system_stats')
        system_stats_rows = cursor.fetchall()
        system_stats = {row['stat_key']: row['stat_value'] for row in system_stats_rows}

        # Get class distribution
        cursor.execute('''
            SELECT
                waste_class,
                count,
                ROUND(total_confidence / count, 4) as avg_confidence,
                last_detected
            FROM analytics
            ORDER BY count DESC
        ''')
        class_dist_rows = cursor.fetchall()
        class_distribution = [dict(row) for row in class_dist_rows]

        # Get recent activity (last 24 hours)
        cursor.execute('''
            SELECT
                COUNT(*) as count,
                AVG(confidence) as avg_conf
            FROM detections
            WHERE timestamp >= datetime('now', '-1 day')
        ''')
        recent = cursor.fetchone()

        # Get total eco-points
        cursor.execute('SELECT SUM(eco_points) as total FROM detections')
        total_points_row = cursor.fetchone()
        total_eco_points = total_points_row['total'] or 0

        conn.close()

        return {
            'total_detections': int(system_stats.get('total_detections', 0)),
            'avg_confidence': float(system_stats.get('avg_confidence', 0)),
            'total_eco_points': total_eco_points,
            'class_distribution': class_distribution,
            'recent_activity': {
                'last_24h_count': recent['count'] or 0,
                'last_24h_avg_confidence': round(recent['avg_conf'] or 0, 4)
            }
        }

    except Exception as e:
        print(f"Error getting analytics summary: {str(e)}")
        return {
            'total_detections': 0,
            'avg_confidence': 0,
            'total_eco_points': 0,
            'class_distribution': [],
            'recent_activity': {
                'last_24h_count': 0,
                'last_24h_avg_confidence': 0
            }
        }


def get_total_detections():
    """Get total number of detections"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM detections')
        result = cursor.fetchone()
        conn.close()
        return result['count']
    except:
        return 0


def get_total_eco_points():
    """Get total eco-points earned"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(eco_points) as total FROM detections')
        result = cursor.fetchone()
        conn.close()
        return result['total'] or 0
    except:
        return 0


def clear_all_data():
    """
    Clear all data from database (for testing/reset)
    WARNING: This deletes all records!
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM detections')
        cursor.execute('DELETE FROM analytics')
        cursor.execute('UPDATE system_stats SET stat_value = "0"')

        conn.commit()
        conn.close()
        print("All data cleared from database")
        return True
    except Exception as e:
        print(f"Error clearing data: {str(e)}")
        return False


# Initialize database on module import
init_db()
