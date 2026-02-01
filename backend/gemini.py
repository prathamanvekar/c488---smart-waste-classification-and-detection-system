"""
Gemini API Integration Module
Generate sustainability recommendations using Gemini LLM
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize Gemini client
client = None

def init_gemini():
    """
    Initialize Gemini API with API key
    Called automatically on first use
    """
    global client

    if client is not None:
        return True

    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        return False

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini API initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Gemini API: {str(e)}")
        return False


def generate_recommendations(waste_classes):
    """
    Generate comprehensive waste disposal recommendations

    Args:
        waste_classes (list): List of detected waste class names

    Returns:
        dict: {
            'disposal_instructions': str,
            'safety_warnings': str,
            'eco_tips': str,
            'success': bool
        }
    """
    if not init_gemini():
        return {
            'disposal_instructions': 'Gemini API not configured.',
            'safety_warnings': '',
            'eco_tips': 'Please configure GEMINI_API_KEY in .env file.',
            'success': False
        }

    try:
        # Create unique list of waste classes
        unique_classes = list(set(waste_classes))
        waste_list = ', '.join(unique_classes)

        # Create prompt for concise, structured response
        prompt = f"""You detected the following waste items: {waste_list}

Please provide SHORT, actionable guidance in 3 sections:

1. DISPOSAL INSTRUCTIONS (2-3 sentences max):
How to properly dispose of these items.

2. SAFETY WARNINGS (1-2 sentences, only if applicable):
Any safety concerns or hazards. If none, write "None."

3. ECO-FRIENDLY TIPS (2-3 sentences max):
Quick tips to reduce environmental impact.

Keep responses concise and practical for everyday users."""

        # Generate response
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        text = response.text.strip()

        # Parse response into sections
        sections = parse_gemini_response(text)

        return {
            'disposal_instructions': sections.get('disposal', 'Follow local waste disposal guidelines.'),
            'safety_warnings': sections.get('safety', 'None'),
            'eco_tips': sections.get('eco_tips', 'Reduce, reuse, and recycle whenever possible.'),
            'success': True
        }

    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return {
            'disposal_instructions': 'Unable to generate recommendations at this time.',
            'safety_warnings': '',
            'eco_tips': 'Try to reduce waste and recycle when possible.',
            'success': False,
            'error': str(e)
        }


def parse_gemini_response(text):
    """
    Parse Gemini response into structured sections

    Args:
        text (str): Raw Gemini response text

    Returns:
        dict: Parsed sections
    """
    sections = {
        'disposal': '',
        'safety': '',
        'eco_tips': ''
    }

    # Split by common section markers
    lines = text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Identify sections by keywords
        lower_line = line.lower()

        if 'disposal' in lower_line or '1.' in line:
            current_section = 'disposal'
            continue
        elif 'safety' in lower_line or 'warning' in lower_line or '2.' in line:
            current_section = 'safety'
            continue
        elif 'eco' in lower_line or 'tip' in lower_line or '3.' in line:
            current_section = 'eco_tips'
            continue

        # Append content to current section
        if current_section and line and not line.endswith(':'):
            if sections[current_section]:
                sections[current_section] += ' ' + line
            else:
                sections[current_section] = line

    return sections


def get_recycling_tips(waste_class):
    """
    Get specific recycling tips for a single waste type

    Args:
        waste_class (str): Waste class name

    Returns:
        str: Recycling tips
    """
    if not init_gemini():
        return "Gemini API not configured. Please add GEMINI_API_KEY to .env file."

    try:
        prompt = f"""Provide 3 SHORT, practical recycling tips for: {waste_class}

Keep each tip to one sentence. Focus on actionable advice."""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print(f"Error getting recycling tips: {str(e)}")
        return f"Follow local recycling guidelines for {waste_class}."


def generate_impact_report(analytics_data):
    """
    Generate environmental impact report based on detection analytics

    Args:
        analytics_data (dict): Analytics summary with class distribution

    Returns:
        str: Environmental impact narrative
    """
    if not init_gemini():
        return "Environmental impact report unavailable. Configure GEMINI_API_KEY."

    try:
        # Extract key statistics
        total_detections = analytics_data.get('total_detections', 0)
        class_dist = analytics_data.get('class_distribution', [])

        # Format class distribution for prompt
        class_summary = ', '.join([
            f"{item['waste_class']} ({item['count']})"
            for item in class_dist[:5]  # Top 5
        ])

        prompt = f"""Based on waste detection data:
- Total items detected: {total_detections}
- Most common: {class_summary}

Write a SHORT (3-4 sentences) positive environmental impact message:
1. Acknowledge their waste awareness
2. Highlight potential environmental benefit
3. Encourage continued efforts

Keep it motivational and concise."""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print(f"Error generating impact report: {str(e)}")
        return "Great job being mindful of waste! Every small action contributes to a healthier planet."


def get_quick_tip(waste_class):
    """
    Get a single quick tip for a waste class (very short)

    Args:
        waste_class (str): Waste class name

    Returns:
        str: One-sentence tip
    """
    if not init_gemini():
        return f"Sort {waste_class} properly for recycling."

    try:
        prompt = f"""Give ONE sentence tip for properly handling: {waste_class}
Maximum 15 words. Be specific and actionable."""

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        return f"Dispose of {waste_class} according to local guidelines."


def chat_with_gemini(user_message, context=None):
    """
    Interactive chat about waste management and sustainability

    Args:
        user_message (str): User's question or message
        context (str, optional): Additional context (detected classes, etc.)

    Returns:
        str: Gemini's response
    """
    if not init_gemini():
        return "Chat unavailable. Please configure GEMINI_API_KEY in .env file."

    try:
        # Build prompt with context
        if context:
            prompt = f"""Context: The user has detected waste items: {context}

User question: {user_message}

Provide a helpful, concise answer about waste management or sustainability. Keep it under 100 words."""
        else:
            prompt = f"""Answer this question about waste management or sustainability:

{user_message}

Keep your answer concise and practical (under 100 words)."""

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return "Sorry, I couldn't process your question. Please try again."


def get_safety_info(waste_class):
    """
    Get specific safety information for a waste type

    Args:
        waste_class (str): Waste class name

    Returns:
        str: Safety information or "Safe to handle" if no concerns
    """
    if not init_gemini():
        return "Safety information unavailable."

    try:
        prompt = f"""Is {waste_class} safe to handle?

If YES: Reply "Safe to handle with normal precautions."
If NO: Provide ONE sentence with the specific safety concern.

Be concise."""

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        return "Use caution when handling. Wear gloves if unsure."


# Test function to verify API connection
def test_gemini_connection():
    """
    Test Gemini API connection

    Returns:
        bool: True if connection successful
    """
    try:
        if not init_gemini():
            return False

        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents="Say 'Connected' if you can read this."
        )
        return 'connect' in response.text.lower()
    except:
        return False
