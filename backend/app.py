"""
Main Flask Application
Handles routing, API endpoints, and application initialization
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import cv2
import base64
import numpy as np
from werkzeug.utils import secure_filename
from datetime import datetime
import json

# Import custom modules
from config import Config
import model
import database
import analytics
import eco_points
import gemini


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})


# Utility Functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """
    Save uploaded file to uploads folder

    Args:
        file: FileStorage object from request

    Returns:
        str: Saved file path or None
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to prevent overwrites
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"

        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        return filepath
    return None


def encode_image_to_base64(image_array):
    """
    Encode numpy image array to base64 string

    Args:
        image_array: OpenCV image (numpy array)

    Returns:
        str: Base64 encoded image
    """
    _, buffer = cv2.imencode('.jpg', image_array)
    return base64.b64encode(buffer).decode('utf-8')


# API Routes

@app.route('/')
def home():
    """Serve frontend index page"""
    frontend_dir = os.path.join(os.path.dirname(Config.BASE_DIR), 'frontend')
    return send_from_directory(frontend_dir, 'index.html')


@app.route('/<path:path>')
def serve_frontend(path):
    """Serve static frontend files"""
    frontend_dir = os.path.join(os.path.dirname(Config.BASE_DIR), 'frontend')
    return send_from_directory(frontend_dir, path)


@app.route('/api/detect/image', methods=['POST'])
def detect_image():
    """
    Handle image upload and waste detection

    Expected: multipart/form-data with 'image' file

    Returns:
        JSON with detection results, eco-points, and recommendations
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Save uploaded file
        filepath = save_uploaded_file(file)
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed: jpg, jpeg, png, bmp'
            }), 400

        # Run YOLO detection
        detection_result = model.detect_waste_from_file(
            filepath,
            conf_threshold=Config.CONFIDENCE_THRESHOLD
        )

        if not detection_result['success']:
            return jsonify({
                'success': False,
                'error': detection_result['message']
            }), 500

        detections = detection_result['detections']

        # Calculate eco-points
        total_eco_points = eco_points.calculate_total_points(detections)
        points_breakdown = eco_points.get_points_breakdown(detections)

        # Store detections in database
        detection_ids = []
        for detection in detections:
            det_id = database.insert_detection(
                waste_class=detection['class_name'],
                confidence=detection['confidence'],
                eco_points=eco_points.calculate_points(
                    detection['class_name'],
                    detection['confidence']
                ),
                image_path=filepath,
                bbox=detection['bbox']
            )
            if det_id:
                detection_ids.append(det_id)

        # Generate Gemini recommendations
        waste_classes = [d['class_name'] for d in detections]
        recommendations = gemini.generate_recommendations(waste_classes)

        # Encode annotated image to base64
        annotated_image_b64 = encode_image_to_base64(detection_result['annotated_image'])

        # Prepare response
        response = {
            'success': True,
            'message': f"Detected {len(detections)} waste item(s)",
            'detections': detections,
            'eco_points': {
                'total': total_eco_points,
                'breakdown': points_breakdown
            },
            'recommendations': recommendations,
            'annotated_image': annotated_image_b64,
            'detection_ids': detection_ids,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in detect_image: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500


@app.route('/api/detect/camera', methods=['POST'])
def detect_camera():
    """
    Handle camera frame detection (base64 encoded image)

    Expected JSON: {
        'frame': 'base64_encoded_image_string'
    }

    Returns:
        JSON with detection results
    """
    try:
        data = request.get_json()

        if not data or 'frame' not in data:
            return jsonify({
                'success': False,
                'error': 'No frame data provided'
            }), 400

        # Decode base64 image
        frame_b64 = data['frame'].split(',')[-1]  # Remove data:image/jpeg;base64, prefix if present
        frame_bytes = base64.b64decode(frame_b64)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                'success': False,
                'error': 'Invalid frame data'
            }), 400

        # Run YOLO detection on frame
        detection_result = model.detect_waste_from_frame(
            frame,
            conf_threshold=Config.CONFIDENCE_THRESHOLD
        )

        if not detection_result['success']:
            return jsonify({
                'success': False,
                'error': detection_result['message']
            }), 500

        detections = detection_result['detections']

        # Calculate eco-points (without storing)
        total_eco_points = eco_points.calculate_total_points(detections)

        # Encode annotated frame
        annotated_frame_b64 = encode_image_to_base64(detection_result['annotated_image'])

        response = {
            'success': True,
            'detections': detections,
            'eco_points': total_eco_points,
            'annotated_frame': annotated_frame_b64,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in detect_camera: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500


@app.route('/api/detect/camera/save', methods=['POST'])
def save_camera_detection():
    """
    Save a camera detection to database
    Same as detect_camera but also stores in database and generates recommendations
    """
    try:
        data = request.get_json()

        if not data or 'frame' not in data:
            return jsonify({
                'success': False,
                'error': 'No frame data provided'
            }), 400

        # Decode base64 image
        frame_b64 = data['frame'].split(',')[-1]
        frame_bytes = base64.b64decode(frame_b64)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        # Run detection
        detection_result = model.detect_waste_from_frame(frame, Config.CONFIDENCE_THRESHOLD)

        if not detection_result['success']:
            return jsonify({
                'success': False,
                'error': detection_result['message']
            }), 500

        detections = detection_result['detections']

        # Save frame to uploads folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        frame_filename = f"camera_{timestamp}.jpg"
        frame_path = os.path.join(Config.UPLOAD_FOLDER, frame_filename)
        cv2.imwrite(frame_path, frame)

        # Calculate eco-points
        total_eco_points = eco_points.calculate_total_points(detections)

        # Store in database
        detection_ids = []
        for detection in detections:
            det_id = database.insert_detection(
                waste_class=detection['class_name'],
                confidence=detection['confidence'],
                eco_points=eco_points.calculate_points(
                    detection['class_name'],
                    detection['confidence']
                ),
                image_path=frame_path,
                bbox=detection['bbox']
            )
            if det_id:
                detection_ids.append(det_id)

        # Generate recommendations
        waste_classes = [d['class_name'] for d in detections]
        recommendations = gemini.generate_recommendations(waste_classes)

        # Encode annotated frame
        annotated_frame_b64 = encode_image_to_base64(detection_result['annotated_image'])

        response = {
            'success': True,
            'message': 'Camera detection saved',
            'detections': detections,
            'eco_points': total_eco_points,
            'recommendations': recommendations,
            'annotated_frame': annotated_frame_b64,
            'detection_ids': detection_ids,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in save_camera_detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500


@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """
    Get comprehensive analytics for admin dashboard

    Returns:
        JSON with analytics summary
    """
    try:
        # Get summary statistics
        summary = analytics.get_summary_stats()

        # Get class distribution
        class_distribution = analytics.get_class_distribution()

        # Get daily stats (last 7 days)
        daily_stats = analytics.calculate_daily_stats(days=7)

        # Get detection trends
        trends = analytics.get_detection_trends(period='day', limit=30)

        # Get top detected classes
        top_classes = analytics.get_top_detected_classes(limit=10)

        # Get accuracy metrics
        accuracy = analytics.calculate_accuracy_metrics()

        # Get recent detections
        recent = analytics.get_recent_detections(limit=20)

        response = {
            'success': True,
            'summary': summary,
            'class_distribution': class_distribution,
            'daily_stats': daily_stats,
            'trends': trends,
            'top_classes': top_classes,
            'accuracy_metrics': accuracy,
            'recent_detections': recent,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in get_admin_stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500


@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get basic analytics summary for user dashboard"""
    try:
        summary = database.get_analytics_summary()
        return jsonify({
            'success': True,
            'data': summary
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get detection history with pagination

    Query params:
        - limit (int): Number of records (default: 20)
        - offset (int): Offset for pagination (default: 0)
        - waste_class (str): Filter by waste class (optional)
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        waste_class = request.args.get('waste_class', None)

        history = database.get_detection_history(
            limit=limit,
            offset=offset,
            waste_class=waste_class
        )

        total_count = database.get_total_detections()

        return jsonify({
            'success': True,
            'history': history,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Get YOLO model information"""
    try:
        info = model.get_model_metadata()
        return jsonify({
            'success': True,
            'model_info': info
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/eco-points/rules', methods=['GET'])
def get_eco_points_rules():
    """Get eco-points calculation rules"""
    try:
        rules = eco_points.get_all_point_rules()
        return jsonify({
            'success': True,
            'rules': rules
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini/tip', methods=['GET'])
def get_gemini_tip():
    """
    Get quick tip for a waste class

    Query param:
        - waste_class (str): Waste class name
    """
    try:
        waste_class = request.args.get('waste_class', 'general waste')
        tip = gemini.get_quick_tip(waste_class)

        return jsonify({
            'success': True,
            'waste_class': waste_class,
            'tip': tip
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model.detector._model is not None,
        'database_connected': True
    }), 200


@app.route('/api/analytics/reset', methods=['POST'])
def reset_analytics():
    """
    Reset all analytics data (clear database)
    WARNING: This deletes all detection records!

    Returns:
        JSON with success status
    """
    try:
        # Clear all data from database
        success = database.clear_all_data()

        if success:
            return jsonify({
                'success': True,
                'message': 'All analytics data has been reset successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset analytics data'
            }), 500

    except Exception as e:
        print(f"Error resetting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500


# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Max size: {Config.MAX_FILE_SIZE / (1024*1024)}MB'
    }), 413


# Run Flask app
if __name__ == '__main__':
    print("=" * 60)
    print("Smart Waste Classification System - Backend Server")
    print("=" * 60)
    print(f"Server running on: http://{Config.HOST}:{Config.PORT}")
    print(f"Model loaded: {model.detector._model is not None}")
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"Uploads folder: {Config.UPLOAD_FOLDER}")
    print("=" * 60)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
