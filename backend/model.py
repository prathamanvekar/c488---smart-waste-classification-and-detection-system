"""
YOLO Model Inference Module
Handles loading and running the YOLO model for waste detection
"""

import os
import cv2
import numpy as np
from pathlib import Path, PureWindowsPath
from ultralytics import YOLO
import platform
import pathlib
import sys

# Fix for Windows PosixPath compatibility
if platform.system() == 'Windows':
    # Register PosixPath to WindowsPath conversion for pickle
    pathlib.PosixPath = pathlib.WindowsPath

    # Also patch for older Python versions
    if sys.version_info >= (3, 13):
        import pathlib._local
        pathlib._local.PosixPath = pathlib.WindowsPath


class WasteDetectionModel:
    """
    Singleton class for YOLO model inference
    Loads model once and provides inference methods
    """

    _instance = None
    _model = None

    def __new__(cls):
        """Singleton pattern to ensure model is loaded only once"""
        if cls._instance is None:
            cls._instance = super(WasteDetectionModel, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize and load YOLO model"""
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """
        Load YOLO model from best.pt file
        Handles Windows PosixPath issue
        """
        try:
            # Get model path relative to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            model_path = os.path.join(project_root, 'best.pt')

            # Convert to absolute path and handle Windows compatibility
            model_path = str(Path(model_path).resolve())

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at: {model_path}")

            print(f"Loading YOLO model from: {model_path}")
            self._model = YOLO(model_path)
            print(f"Model loaded successfully! Classes: {self._model.names}")

        except Exception as e:
            print(f"Error loading YOLO model: {str(e)}")
            raise

    def predict_from_file(self, image_path, conf_threshold=0.25):
        """
        Perform inference on an image file

        Args:
            image_path (str): Path to image file
            conf_threshold (float): Confidence threshold for detections

        Returns:
            dict: {
                'annotated_image': numpy array with drawn boxes,
                'detections': list of detection dicts,
                'success': bool,
                'message': str
            }
        """
        try:
            # Validate image path
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'message': f"Image file not found: {image_path}",
                    'detections': [],
                    'annotated_image': None
                }

            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'message': "Failed to read image file",
                    'detections': [],
                    'annotated_image': None
                }

            # Perform inference using the frame method
            return self.predict_from_frame(image, conf_threshold)

        except Exception as e:
            return {
                'success': False,
                'message': f"Error during inference: {str(e)}",
                'detections': [],
                'annotated_image': None
            }

    def predict_from_frame(self, frame, conf_threshold=0.25):
        """
        Perform inference on a numpy array (OpenCV frame)

        Args:
            frame (numpy.ndarray): OpenCV image frame (BGR format)
            conf_threshold (float): Confidence threshold for detections

        Returns:
            dict: {
                'annotated_image': numpy array with drawn boxes,
                'detections': list of detection dicts,
                'success': bool,
                'message': str
            }
        """
        try:
            if frame is None or not isinstance(frame, np.ndarray):
                return {
                    'success': False,
                    'message': "Invalid frame data",
                    'detections': [],
                    'annotated_image': None
                }

            # Perform inference
            results = self._model.predict(
                source=frame,
                conf=conf_threshold,
                verbose=False
            )

            # Get annotated image
            annotated_frame = results[0].plot()

            # Extract detections
            detections = []
            boxes = results[0].boxes

            for i, box in enumerate(boxes):
                # Get box coordinates (xyxy format)
                xyxy = box.xyxy[0].cpu().numpy().tolist()

                # Get confidence
                confidence = float(box.conf[0].cpu().numpy())

                # Get class
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self._model.names[class_id]

                detection = {
                    'id': i,
                    'class_name': class_name,
                    'class_id': class_id,
                    'confidence': round(confidence, 4),
                    'bbox': {
                        'x1': int(xyxy[0]),
                        'y1': int(xyxy[1]),
                        'x2': int(xyxy[2]),
                        'y2': int(xyxy[3])
                    }
                }
                detections.append(detection)

            return {
                'success': True,
                'message': f"Detected {len(detections)} object(s)",
                'detections': detections,
                'annotated_image': annotated_frame
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error during inference: {str(e)}",
                'detections': [],
                'annotated_image': None
            }

    def get_class_names(self):
        """
        Get list of class names the model can detect

        Returns:
            dict: Model class names
        """
        if self._model is not None:
            return self._model.names
        return {}

    def get_model_info(self):
        """
        Get model information

        Returns:
            dict: Model metadata
        """
        if self._model is not None:
            return {
                'num_classes': len(self._model.names),
                'class_names': list(self._model.names.values()),
                'model_type': 'YOLOv8',
                'loaded': True
            }
        return {'loaded': False}


# Create global model instance (loaded once)
detector = WasteDetectionModel()


def detect_waste_from_file(image_path, conf_threshold=0.25):
    """
    Convenience function for file-based detection

    Args:
        image_path (str): Path to image file
        conf_threshold (float): Confidence threshold

    Returns:
        dict: Detection results
    """
    return detector.predict_from_file(image_path, conf_threshold)


def detect_waste_from_frame(frame, conf_threshold=0.25):
    """
    Convenience function for frame-based detection (live camera)

    Args:
        frame (numpy.ndarray): OpenCV frame
        conf_threshold (float): Confidence threshold

    Returns:
        dict: Detection results
    """
    return detector.predict_from_frame(frame, conf_threshold)


def get_supported_classes():
    """
    Get list of waste classes the model can detect

    Returns:
        dict: Class names
    """
    return detector.get_class_names()


def get_model_metadata():
    """
    Get model information and metadata

    Returns:
        dict: Model info
    """
    return detector.get_model_info()
