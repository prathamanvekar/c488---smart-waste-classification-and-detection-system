"""
Eco-Points Calculation Module
Calculate eco-points based on waste detection and classification
"""


# Eco-Points Configuration
# Easy to modify - just update this dictionary
# Points based on recycling priority and environmental impact
ECO_POINTS_MAP = {
    # Hazardous waste - highest priority (requires special handling)
    'battery': 50,
    'light_bulb': 40,
    'chemical_container': 45,
    'chemical_spray_can': 45,

    # Metals - high value recyclables
    'can': 15,

    # Plastics - medium to high value (sorted by quality/recyclability)
    'plastic_bottle': 20,  # PET bottles - highly recyclable
    'plastic_box': 18,     # Hard plastics - good recyclability
    'plastic_bag': 12,     # Soft plastics - harder to recycle
    'plastic_cup': 10,     # Mixed plastics
    'plastic_cultery': 8,  # Often contaminated
    'scrap_plastic': 10,   # General plastic waste

    # Paper products - medium value
    'cardboard': 10,
    'reuseable_paper': 8,
    'scrap_paper': 5,

    # Packaging waste - low value
    'snack_bag': 8,

    # Legacy/generic classes for backward compatibility
    'e-waste': 50,
    'medical': 50,
    'metal': 15,
    'glass': 12,
    'plastic': 10,
    'paper': 8,
    'organic': 5,
    'food-waste': 5,
    'trash': 2,
    'other': 2,

    # Add more classes as needed
    # 'class-name': points
}

# Default points for unknown classes
DEFAULT_POINTS = 5

# Confidence multiplier thresholds
CONFIDENCE_BONUS = {
    'high': {'min': 0.9, 'multiplier': 1.2},    # >90% confidence: +20% bonus
    'medium': {'min': 0.7, 'multiplier': 1.0},  # 70-90%: normal points
    'low': {'min': 0.5, 'multiplier': 0.8}      # 50-70%: -20% penalty
}


def calculate_points(waste_class, confidence=1.0):
    """
    Calculate eco-points for a single detection

    Args:
        waste_class (str): Detected waste class name
        confidence (float): Detection confidence (0.0 - 1.0)

    Returns:
        int: Calculated eco-points
    """
    # Normalize waste class to lowercase for matching
    waste_class_lower = waste_class.lower().strip()

    # Get base points for this waste class
    base_points = ECO_POINTS_MAP.get(waste_class_lower, DEFAULT_POINTS)

    # Apply confidence multiplier
    multiplier = get_confidence_multiplier(confidence)

    # Calculate final points (rounded to integer)
    final_points = int(base_points * multiplier)

    # Ensure minimum 1 point per detection
    return max(1, final_points)


def calculate_total_points(detections):
    """
    Calculate total eco-points for multiple detections (from one image)

    Args:
        detections (list): List of detection dictionaries
            Each detection should have 'class_name' and 'confidence'

    Returns:
        int: Total eco-points for all detections
    """
    total_points = 0

    for detection in detections:
        waste_class = detection.get('class_name', 'unknown')
        confidence = detection.get('confidence', 0.0)

        points = calculate_points(waste_class, confidence)
        total_points += points

    return total_points


def get_confidence_multiplier(confidence):
    """
    Get point multiplier based on confidence level

    Args:
        confidence (float): Detection confidence (0.0 - 1.0)

    Returns:
        float: Point multiplier
    """
    if confidence >= CONFIDENCE_BONUS['high']['min']:
        return CONFIDENCE_BONUS['high']['multiplier']
    elif confidence >= CONFIDENCE_BONUS['medium']['min']:
        return CONFIDENCE_BONUS['medium']['multiplier']
    elif confidence >= CONFIDENCE_BONUS['low']['min']:
        return CONFIDENCE_BONUS['low']['multiplier']
    else:
        # Very low confidence (<50%): reduced points
        return 0.5


def get_points_for_class(waste_class):
    """
    Get base points for a specific waste class (without confidence)

    Args:
        waste_class (str): Waste class name

    Returns:
        int: Base points for this class
    """
    waste_class_lower = waste_class.lower().strip()
    return ECO_POINTS_MAP.get(waste_class_lower, DEFAULT_POINTS)


def get_all_point_rules():
    """
    Get all eco-points rules for display/configuration

    Returns:
        dict: All point rules
    """
    return {
        'point_map': ECO_POINTS_MAP.copy(),
        'default_points': DEFAULT_POINTS,
        'confidence_bonuses': CONFIDENCE_BONUS.copy()
    }


def update_point_rule(waste_class, points):
    """
    Update points for a specific waste class
    Allows dynamic configuration without code changes

    Args:
        waste_class (str): Waste class name
        points (int): New point value

    Returns:
        bool: Success status
    """
    try:
        waste_class_lower = waste_class.lower().strip()
        ECO_POINTS_MAP[waste_class_lower] = int(points)
        return True
    except:
        return False


def get_points_breakdown(detections):
    """
    Get detailed breakdown of points calculation
    Useful for showing users how points were earned

    Args:
        detections (list): List of detection dictionaries

    Returns:
        dict: Breakdown with per-detection details and total
    """
    breakdown = {
        'detections': [],
        'total_points': 0
    }

    for i, detection in enumerate(detections):
        waste_class = detection.get('class_name', 'unknown')
        confidence = detection.get('confidence', 0.0)

        base_points = get_points_for_class(waste_class)
        multiplier = get_confidence_multiplier(confidence)
        final_points = calculate_points(waste_class, confidence)

        breakdown['detections'].append({
            'detection_id': i,
            'waste_class': waste_class,
            'confidence': round(confidence, 4),
            'base_points': base_points,
            'multiplier': multiplier,
            'final_points': final_points
        })

        breakdown['total_points'] += final_points

    return breakdown


# Utility function for backward compatibility
def calculate_eco_points(waste_class, confidence=1.0):
    """
    Alias for calculate_points() for backward compatibility

    Args:
        waste_class (str): Detected waste class
        confidence (float): Detection confidence

    Returns:
        int: Eco-points
    """
    return calculate_points(waste_class, confidence)
