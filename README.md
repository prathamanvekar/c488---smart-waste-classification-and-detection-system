# Smart Waste Classification System

**AI-powered waste detection and classification system with eco-points tracking and sustainability recommendations.**

---

## 📋 System Overview

- **15 Waste Classes**: battery, can, cardboard, chemical_container, chemical_spray_can, light_bulb, plastic_bag, plastic_bottle, plastic_box, plastic_cultery, plastic_cup, reuseable_paper, scrap_paper, scrap_plastic, snack_bag
- **Dual Input Modes**: Image upload + Live webcam detection
- **AI Integration**: YOLOv8 object detection + Gemini 2.0 Flash recommendations
- **Analytics Dashboard**: Real-time statistics, charts, and detection history
- **Eco-Points System**: Confidence-based scoring with unique item tracking

---

## 🚀 Quick Setup (Windows)

### Prerequisites

- Python 3.10 - 3.13
- Webcam (optional, for live detection)

### Step 1: Extract & Navigate

```powershell
# Extract the ZIP file to any location
# Open PowerShell/Command Prompt and navigate to project folder
cd path\to\project
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

# Install all packages
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables

```powershell
# Edit .env file (already included)
notepad .env
```

**Add your Gemini API key:**

```env
GEMINI_API_KEY=your_actual_api_key_here
```

**Get Gemini API Key:**

1. Go to: https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and paste into `.env` file

### Step 5: Run the Application

```powershell
python backend/app.py
```

**Expected output:**

```
============================================================
Smart Waste Classification System - Backend Server
============================================================
Server running on: http://127.0.0.1:5001
Model loaded: True
...
```

### Step 6: Access the Application

Open your browser and visit:

- **User Dashboard**: http://localhost:5001
- **Admin Dashboard**: http://localhost:5001/admin.html

---

## 📁 Project Structure

```
project/
├── .env                          # Environment variables (CONFIGURE THIS!)
├── best.pt                       # Trained YOLO model (15 classes)
├── README.md                     # This file
├── backend/
│   ├── app.py                   # Flask server
│   ├── config.py                # Configuration loader
│   ├── model.py                 # YOLO detection logic
│   ├── database.py              # SQLite operations
│   ├── analytics.py             # Analytics calculations
│   ├── eco_points.py            # Eco-points system
│   ├── gemini.py                # Gemini API integration
│   ├── requirements.txt         # Python dependencies
│   ├── waste.db                 # SQLite database (auto-created)
│   └── uploads/                 # Uploaded images (auto-created)
└── frontend/
    ├── index.html               # User dashboard
    ├── admin.html               # Admin analytics
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js              # User dashboard logic
        └── admin.js             # Admin dashboard logic
```

---

## 🎯 Usage Guide

### Image Upload Mode

1. Click **"Image Upload"** button
2. Drag & drop an image or click **"Choose File"**
3. View detection results with:
   - Annotated image with bounding boxes
   - Detected waste classes and confidence scores
   - Eco-points earned
   - Gemini AI recommendations

### Live Camera Mode

1. Click **"Live Camera"** button
2. Click **"Start Camera"** and grant permissions
3. Show waste items to the camera
4. Real-time detection with eco-points for unique items
5. Click **"Stop Camera"** when done

### Admin Dashboard

1. Navigate to http://localhost:5001/admin.html
2. View comprehensive analytics:
   - Total detections and eco-points
   - Detection trends (charts)
   - Class distribution
   - Recent detections table
3. Click **"Refresh Data"** to update
4. Click **"Reset All Data"** to clear database (requires confirmation)

---

## 🔧 Configuration

### .env File Options

```env
# Gemini API (REQUIRED)
GEMINI_API_KEY=your_key_here

# Flask Settings
FLASK_SECRET_KEY=wastedev123
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_PATH=backend/waste.db

# Model
MODEL_PATH=best.pt

# Upload Settings
UPLOAD_FOLDER=backend/uploads
MAX_FILE_SIZE=16777216          # 16MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp

# Server
HOST=127.0.0.1
PORT=5001
```

---

## 🧪 Testing the System

### Test Detection Accuracy

1. Upload images containing waste items
2. Check confidence scores (should be > 70%)
3. Verify correct classification

### Test Eco-Points

- **High confidence (>90%)**: +20% bonus
- **Medium (70-89%)**: Normal points
- **Low (<70%)**: Reduced points

### Test Live Camera

1. Start camera mode
2. Show multiple unique items
3. Verify points only increase for NEW items
4. Check admin dashboard reflects camera detections

---

## 📊 Eco-Points System

| Waste Class        | Base Points | Category  |
| ------------------ | ----------- | --------- |
| battery            | 50          | Hazardous |
| chemical_container | 45          | Hazardous |
| chemical_spray_can | 45          | Hazardous |
| light_bulb         | 40          | Hazardous |
| plastic_bottle     | 20          | Plastic   |
| plastic_box        | 18          | Plastic   |
| can                | 15          | Metal     |
| plastic_bag        | 12          | Plastic   |
| cardboard          | 10          | Paper     |
| plastic_cup        | 10          | Plastic   |
| scrap_plastic      | 10          | Plastic   |
| reuseable_paper    | 8           | Paper     |
| plastic_cultery    | 8           | Plastic   |
| snack_bag          | 8           | Packaging |
| scrap_paper        | 5           | Paper     |

**Confidence Multipliers:**

- ≥90%: ×1.2 (bonus)
- 70-89%: ×1.0 (normal)
- 50-69%: ×0.8 (penalty)
- <50%: ×0.5 (low confidence)

---

## 🛠️ Troubleshooting

### "Port already in use" Error

```powershell
# Change PORT in .env file
PORT=5002
```

### Model Loading Error

- Ensure `best.pt` is in project root
- Check file is not corrupted

### Camera Not Working

- Grant browser camera permissions
- Check webcam is connected and not used by other apps
- Try different browser (Chrome recommended)

### Gemini API Errors

- Verify API key is correct in `.env`
- Check internet connection
- Ensure API key has not expired

### Database Issues

```powershell
# Delete database to reset
del backend\waste.db

# Restart server (new database auto-created)
python backend/app.py
```

---

## 📦 Dependencies

**Core:**

- Flask 3.0+ (web framework)
- Ultralytics 8.1+ (YOLOv8)
- OpenCV 4.8+ (image processing)
- Google Genai 0.2+ (Gemini API)

**Data & Analytics:**

- SQLite3 (built-in)
- NumPy 1.26+
- Pillow 11.0+

**Full list:** See `backend/requirements.txt`

---

## 🔒 Security Notes

- **.env file**: Contains sensitive API keys - **DO NOT SHARE**
- **Uploads folder**: Contains user images - handle according to privacy policies
- **Database**: Contains detection history - protect appropriately

---

## 📞 Support

If you encounter issues:

1. Check terminal output for error messages
2. Verify all setup steps completed
3. Ensure Python version 3.10-3.13
4. Check `.env` file configuration

---

## 📄 License

Proprietary - All rights reserved.

---

**Ready to detect waste! 🌱♻️**
