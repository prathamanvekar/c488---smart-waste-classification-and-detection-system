"""
Analytics Module
Calculate and aggregate detection statistics
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
from database import get_db_connection


def calculate_daily_stats(days=7):
    """
    Calculate daily detection statistics for the past N days

    Args:
        days (int): Number of days to analyze (default: 7)

    Returns:
        list: Daily statistics with date, count, and avg_confidence
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as count,
                ROUND(AVG(confidence), 4) as avg_confidence,
                SUM(eco_points) as total_points
            FROM detections
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (days,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error calculating daily stats: {str(e)}")
        return []


def get_class_distribution():
    """
    Get distribution of waste classes detected

    Returns:
        list: List of classes with their counts and percentages
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total detections for percentage calculation
        cursor.execute('SELECT COUNT(*) as total FROM detections')
        total = cursor.fetchone()['total']

        if total == 0:
            return []

        # Get class distribution
        cursor.execute('''
            SELECT
                waste_class,
                count,
                ROUND(total_confidence / count, 4) as avg_confidence,
                ROUND((CAST(count AS REAL) / ?) * 100, 2) as percentage
            FROM analytics
            ORDER BY count DESC
        ''', (total,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error getting class distribution: {str(e)}")
        return []


def get_detection_trends(period='day', limit=30):
    """
    Get detection trends over time

    Args:
        period (str): Time period - 'day', 'week', 'month'
        limit (int): Number of periods to return

    Returns:
        list: Trend data with timestamps and counts
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Determine SQL grouping based on period
        if period == 'day':
            group_by = "DATE(timestamp)"
            days_back = limit
        elif period == 'week':
            group_by = "strftime('%Y-%W', timestamp)"
            days_back = limit * 7
        elif period == 'month':
            group_by = "strftime('%Y-%m', timestamp)"
            days_back = limit * 30
        else:
            group_by = "DATE(timestamp)"
            days_back = limit

        cursor.execute(f'''
            SELECT
                {group_by} as period,
                COUNT(*) as count,
                ROUND(AVG(confidence), 4) as avg_confidence
            FROM detections
            WHERE timestamp >= datetime('now', '-{days_back} days')
            GROUP BY {group_by}
            ORDER BY period DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Reverse to show chronological order
        return [dict(row) for row in reversed(rows)]

    except Exception as e:
        print(f"Error getting detection trends: {str(e)}")
        return []


def get_top_detected_classes(limit=10):
    """
    Get most frequently detected waste types

    Args:
        limit (int): Number of top classes to return

    Returns:
        list: Top detected classes with counts
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                waste_class,
                count,
                ROUND(total_confidence / count, 4) as avg_confidence,
                last_detected
            FROM analytics
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error getting top detected classes: {str(e)}")
        return []


def calculate_accuracy_metrics():
    """
    Calculate model performance metrics

    Returns:
        dict: Accuracy metrics including average confidence, confidence distribution
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Overall statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_detections,
                ROUND(AVG(confidence), 4) as avg_confidence,
                ROUND(MIN(confidence), 4) as min_confidence,
                ROUND(MAX(confidence), 4) as max_confidence
            FROM detections
        ''')
        overall = dict(cursor.fetchone())

        # Confidence distribution (buckets)
        cursor.execute('''
            SELECT
                CASE
                    WHEN confidence >= 0.9 THEN '0.9-1.0'
                    WHEN confidence >= 0.8 THEN '0.8-0.9'
                    WHEN confidence >= 0.7 THEN '0.7-0.8'
                    WHEN confidence >= 0.6 THEN '0.6-0.7'
                    WHEN confidence >= 0.5 THEN '0.5-0.6'
                    ELSE '<0.5'
                END as confidence_range,
                COUNT(*) as count
            FROM detections
            GROUP BY confidence_range
            ORDER BY confidence_range DESC
        ''')

        confidence_dist = [dict(row) for row in cursor.fetchall()]

        # High confidence detections (>= 0.8)
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM detections
            WHERE confidence >= 0.8
        ''')
        high_conf = cursor.fetchone()['count']

        conn.close()

        return {
            'overall': overall,
            'confidence_distribution': confidence_dist,
            'high_confidence_count': high_conf,
            'high_confidence_percentage': round(
                (high_conf / overall['total_detections'] * 100) if overall['total_detections'] > 0 else 0,
                2
            )
        }

    except Exception as e:
        print(f"Error calculating accuracy metrics: {str(e)}")
        return {
            'overall': {
                'total_detections': 0,
                'avg_confidence': 0,
                'min_confidence': 0,
                'max_confidence': 0
            },
            'confidence_distribution': [],
            'high_confidence_count': 0,
            'high_confidence_percentage': 0
        }


def get_hourly_activity(hours=24):
    """
    Get detection activity by hour

    Args:
        hours (int): Number of hours to analyze

    Returns:
        list: Hourly detection counts
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                strftime('%H', timestamp) as hour,
                COUNT(*) as count
            FROM detections
            WHERE timestamp >= datetime('now', '-' || ? || ' hours')
            GROUP BY hour
            ORDER BY hour
        ''', (hours,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error getting hourly activity: {str(e)}")
        return []


def get_recent_detections(limit=10):
    """
    Get most recent detections with details

    Args:
        limit (int): Number of recent detections to return

    Returns:
        list: Recent detections
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id,
                timestamp,
                waste_class,
                confidence,
                eco_points,
                image_path
            FROM detections
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error getting recent detections: {str(e)}")
        return []


def get_summary_stats():
    """
    Get comprehensive summary statistics for dashboard

    Returns:
        dict: Complete summary including all key metrics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total detections
        cursor.execute('SELECT COUNT(*) as total FROM detections')
        total = cursor.fetchone()['total']

        # Total eco-points
        cursor.execute('SELECT SUM(eco_points) as total FROM detections')
        eco_points = cursor.fetchone()['total'] or 0

        # Average confidence
        cursor.execute('SELECT ROUND(AVG(confidence), 4) as avg FROM detections')
        avg_conf = cursor.fetchone()['avg'] or 0

        # Unique classes detected
        cursor.execute('SELECT COUNT(DISTINCT waste_class) as count FROM detections')
        unique_classes = cursor.fetchone()['count']

        # Today's detections
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM detections
            WHERE DATE(timestamp) = DATE('now')
        ''')
        today_count = cursor.fetchone()['count']

        conn.close()

        return {
            'total_detections': total,
            'total_eco_points': eco_points,
            'avg_confidence': avg_conf,
            'unique_classes': unique_classes,
            'today_detections': today_count
        }

    except Exception as e:
        print(f"Error getting summary stats: {str(e)}")
        return {
            'total_detections': 0,
            'total_eco_points': 0,
            'avg_confidence': 0,
            'unique_classes': 0,
            'today_detections': 0
        }
