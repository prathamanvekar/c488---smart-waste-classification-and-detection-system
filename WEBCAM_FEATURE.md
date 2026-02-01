# Live Webcam Detection Feature

## Overview

Added live webcam detection to the Smart Waste Classification app with proper eco-points handling and mode switching.

## Implementation Summary

### 1. HTML Changes (`frontend/index.html`)

- **Mode Toggle Section**: Added toggle buttons to switch between "Image Upload" and "Live Camera" modes
- **Camera Section**: Added new section with:
  - Start/Stop camera control buttons
  - Camera status indicator (ON/OFF with visual indicator)
  - Video element for live camera feed
  - Canvas element for frame capture (hidden)
  - Image element for displaying annotated frames
  - Info text explaining camera usage

### 2. CSS Changes (`frontend/css/style.css`)

Added styles for:

- **Mode toggle buttons**: Professional button styling with active states
- **Camera controls**: Start/Stop buttons with hover effects
- **Camera status indicator**: Animated pulsing dot for "ON" state
- **Camera feed container**: Responsive video display
- **Info section**: Helpful text display when camera is off

### 3. JavaScript Changes (`frontend/js/main.js`)

#### New State Variables

- `cameraStream`: MediaStream object for webcam
- `isCameraActive`: Boolean tracking camera state
- `detectionInterval`: Interval ID for periodic detection
- `cameraDetectionCount`: Counter for detections
- `sessionCameraEcoPoints`: Cumulative eco-points for camera session
- `lastDetectedClasses`: Set tracking unique waste classes detected (prevents duplicate points)

#### Key Functions

**Mode Switching:**

- `switchToUploadMode()`: Switches to image upload mode, stops camera if active
- `switchToCameraMode()`: Switches to live camera mode, shows camera controls

**Camera Control:**

- `startCamera()`:
  - Requests webcam access via `navigator.mediaDevices.getUserMedia()`
  - Starts video stream at 1280x720 resolution
  - Initiates detection loop (every 2 seconds)
  - Resets session tracking (eco-points, detected classes)
  - Updates UI to show camera is ON

- `stopCamera()`:
  - Stops all media tracks
  - Clears detection interval
  - Releases webcam access
  - Updates UI to show camera is OFF

**Detection Processing:**

- `captureAndDetect()`:
  - Captures current video frame to canvas
  - Converts to base64 JPEG
  - Sends to backend `/api/detect/camera` endpoint
  - Processes response and updates UI

- `processCameraDetection(data)`:
  - Displays annotated frame from backend
  - Updates detection list with current frame results
  - **Smart eco-points handling**:
    - Tracks unique waste classes in `lastDetectedClasses` Set
    - Only awards points for NEW classes not seen before in session
    - Prevents runaway point accumulation from same items
  - Updates recommendations every 5 detections (reduces API load)

**Helper Functions:**

- `getBaseEcoPoints(className)`: Maps waste class to base point value (matches backend logic)
- `updateCameraRecommendations(detections)`: Provides context-aware disposal instructions

## Eco-Points Logic (Prevents Haywire Behavior)

### Problem

Without tracking, detecting the same bottle 50 times = 50x eco-points for one item.

### Solution

1. Maintain `lastDetectedClasses` Set for current camera session
2. For each frame, identify unique classes detected
3. Only award eco-points for classes NOT in the Set (first-time detection)
4. Add newly detected classes to Set
5. Points accumulate only when NEW items appear in frame
6. Session resets when camera is stopped/restarted

### Example Scenario

- Frame 1: Detects "plastic_bottle" → Awards 20 points → Add to Set
- Frame 2-10: Still detects "plastic_bottle" → No new points (already in Set)
- Frame 11: New "can" appears → Awards 15 points → Add "can" to Set
- **Total**: 35 points (not 200+ from 10 frames)

## Backend Integration

### Existing API Endpoints Used

- `POST /api/detect/camera`: Frame-by-frame detection (no DB storage)
  - Accepts: `{ frame: "base64_image_data" }`
  - Returns: `{ success, detections, eco_points, annotated_frame, timestamp }`

### Optional Enhancement

- `POST /api/detect/camera/save`: Save specific frames to DB (not currently used)
  - Could add "Save Frame" button for users to save interesting detections

## User Experience

### Default State

- App loads in "Image Upload" mode
- Camera is OFF by default
- No webcam access requested until user clicks "Start Camera"

### Camera Mode Flow

1. User clicks "Live Camera" mode button
2. User clicks "Start Camera" button
3. Browser requests camera permission
4. Camera feed starts, detection begins every 2 seconds
5. Annotated frames display in real-time
6. Eco-points accumulate for unique items
7. User clicks "Stop Camera" to end session
8. Webcam access released immediately

### Mode Switching

- Can switch between Upload/Camera modes anytime
- Switching away from Camera mode automatically stops camera
- Upload mode preserves existing functionality unchanged

## Browser Compatibility

### Requirements

- Modern browser with `getUserMedia` support
- HTTPS or localhost (camera access requires secure context)
- Camera permission granted by user

### Tested Browsers

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS requires user gesture)

## Performance Considerations

1. **Detection Interval**: 2 seconds (adjustable if needed)
   - Balance between responsiveness and API load
   - Prevents overwhelming backend with requests

2. **Frame Quality**: JPEG at 80% quality
   - Reduces payload size
   - Maintains detection accuracy

3. **Recommendation Updates**: Every 5 detections
   - Reduces unnecessary Gemini API calls
   - Still provides relevant guidance

## Testing Checklist

- [x] Camera starts on button click
- [x] Camera stops on button click
- [x] Camera stops when switching to Upload mode
- [x] Webcam access released when camera stops
- [x] Annotated frames display correctly
- [x] Detections update every 2 seconds
- [x] Eco-points only increase for unique items
- [x] Status indicator shows correct state (ON/OFF)
- [x] Upload mode still works independently
- [x] No console errors during operation

## Future Enhancements

1. **Adjustable detection interval**: Let users control detection frequency
2. **Save frame button**: Allow saving interesting camera detections to DB
3. **Detection history**: Show history of items detected in camera session
4. **Session summary**: Display summary when camera session ends
5. **Multi-camera support**: Select different cameras if available
6. **Mobile optimization**: Better layout for mobile camera usage

## Files Modified

1. `frontend/index.html` - Added mode toggle and camera UI
2. `frontend/css/style.css` - Added camera styling (~130 lines)
3. `frontend/js/main.js` - Added camera logic (~250 lines)
4. `backend/app.py` - No changes (existing API used)

## No Breaking Changes

- Image upload functionality unchanged
- Existing detections preserved
- Admin dashboard unaffected
- Database schema unchanged
- Backend API endpoints unchanged
