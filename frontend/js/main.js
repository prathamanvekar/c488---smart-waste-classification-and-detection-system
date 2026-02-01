/**
 * User Dashboard JavaScript
 * Handles image upload, camera detection, and UI interactions
 */

// API Configuration
const API_BASE_URL = "http://localhost:5001/api";

// DOM Elements
let uploadArea, fileInput, loadingIndicator, resultsSection;
let annotatedImage, detectionsList, sessionEcoPoints;
let disposalInstructions, safetyWarnings, ecoTips;
let totalDetections, totalEcoPoints, avgConfidence;
let notification, notificationText;

// Mode toggle elements
let uploadModeBtn, cameraModeBtn;
let uploadSection, cameraSection;

// Camera elements
let startCameraBtn, stopCameraBtn, cameraStatus;
let cameraFeed, detectionCanvas, cameraAnnotatedFrame;
let cameraFeedContainer, cameraInfo;

// Camera state
let cameraStream = null;
let isCameraActive = false;
let detectionInterval = null;
let cameraDetectionCount = 0;
let sessionCameraEcoPoints = 0;
let lastDetectedClasses = new Set(); // Track unique classes detected in camera session

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initializeElements();
  setupEventListeners();
  loadUserStats();
});

/**
 * Initialize DOM elements
 */
function initializeElements() {
  uploadArea = document.getElementById("uploadArea");
  fileInput = document.getElementById("fileInput");
  loadingIndicator = document.getElementById("loadingIndicator");
  resultsSection = document.getElementById("resultsSection");

  annotatedImage = document.getElementById("annotatedImage");
  detectionsList = document.getElementById("detectionsList");
  sessionEcoPoints = document.getElementById("sessionEcoPoints");

  disposalInstructions = document.getElementById("disposalInstructions");
  safetyWarnings = document.getElementById("safetyWarnings");
  ecoTips = document.getElementById("ecoTips");

  totalDetections = document.getElementById("totalDetections");
  totalEcoPoints = document.getElementById("totalEcoPoints");
  avgConfidence = document.getElementById("avgConfidence");

  notification = document.getElementById("notification");
  notificationText = document.getElementById("notificationText");

  // Mode toggle elements
  uploadModeBtn = document.getElementById("uploadModeBtn");
  cameraModeBtn = document.getElementById("cameraModeBtn");
  uploadSection = document.getElementById("uploadSection");
  cameraSection = document.getElementById("cameraSection");

  // Camera elements
  startCameraBtn = document.getElementById("startCameraBtn");
  stopCameraBtn = document.getElementById("stopCameraBtn");
  cameraStatus = document.getElementById("cameraStatus");
  cameraFeed = document.getElementById("cameraFeed");
  detectionCanvas = document.getElementById("detectionCanvas");
  cameraAnnotatedFrame = document.getElementById("cameraAnnotatedFrame");
  cameraFeedContainer = document.getElementById("cameraFeedContainer");
  cameraInfo = document.getElementById("cameraInfo");
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // File input change
  fileInput.addEventListener("change", handleFileSelect);

  // Click upload area to trigger file input
  uploadArea.addEventListener("click", () => fileInput.click());

  // Drag and drop
  uploadArea.addEventListener("dragover", handleDragOver);
  uploadArea.addEventListener("dragleave", handleDragLeave);
  uploadArea.addEventListener("drop", handleDrop);

  // Prevent default drag behavior on document
  document.addEventListener("dragover", (e) => e.preventDefault());
  document.addEventListener("drop", (e) => e.preventDefault());

  // Mode toggle buttons
  uploadModeBtn.addEventListener("click", switchToUploadMode);
  cameraModeBtn.addEventListener("click", switchToCameraMode);

  // Camera control buttons
  startCameraBtn.addEventListener("click", startCamera);
  stopCameraBtn.addEventListener("click", stopCamera);
}

/**
 * Handle file selection from input
 */
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    uploadImage(file);
  }
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
  event.preventDefault();
  event.stopPropagation();
  uploadArea.classList.add("dragover");
}

/**
 * Handle drag leave event
 */
function handleDragLeave(event) {
  event.preventDefault();
  event.stopPropagation();
  uploadArea.classList.remove("dragover");
}

/**
 * Handle drop event
 */
function handleDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  uploadArea.classList.remove("dragover");

  const file = event.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    uploadImage(file);
  } else {
    showNotification("Please drop a valid image file", "error");
  }
}

/**
 * Upload image to backend for detection
 */
async function uploadImage(file) {
  // Validate file size (16MB max)
  if (file.size > 16 * 1024 * 1024) {
    showNotification("File too large. Maximum size is 16MB", "error");
    return;
  }

  // Show loading
  loadingIndicator.style.display = "block";
  resultsSection.style.display = "none";

  // Create form data
  const formData = new FormData();
  formData.append("image", file);

  try {
    // Send to backend
    const response = await fetch(`${API_BASE_URL}/detect/image`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      displayDetectionResults(data);
      showNotification("Detection completed successfully!", "success");
      // Refresh stats
      loadUserStats();
    } else {
      showNotification(data.error || "Detection failed", "error");
    }
  } catch (error) {
    console.error("Upload error:", error);
    showNotification(
      "Network error. Please check if backend is running.",
      "error",
    );
  } finally {
    loadingIndicator.style.display = "none";
  }
}

/**
 * Display detection results
 */
function displayDetectionResults(data) {
  // Show results section
  resultsSection.style.display = "block";

  // Display annotated image
  annotatedImage.src = `data:image/jpeg;base64,${data.annotated_image}`;

  // Display detections list
  detectionsList.innerHTML = "";

  if (data.detections && data.detections.length > 0) {
    data.detections.forEach((detection, index) => {
      const detectionItem = document.createElement("div");
      detectionItem.className = "detection-item";

      const confidencePercent = (detection.confidence * 100).toFixed(1);
      const points =
        data.eco_points.breakdown.detections[index]?.final_points || 0;

      detectionItem.innerHTML = `
        <div class="detection-header">
          <span class="detection-class">${detection.class_name}</span>
          <span class="detection-confidence">${confidencePercent}%</span>
        </div>
        <div class="detection-points">+${points} eco-points</div>
      `;

      detectionsList.appendChild(detectionItem);
    });
  } else {
    detectionsList.innerHTML =
      '<p style="color: var(--text-secondary);">No waste detected in the image.</p>';
  }

  // Display eco-points
  sessionEcoPoints.textContent = data.eco_points.total || 0;

  // Display recommendations
  const recommendations = data.recommendations;

  disposalInstructions.textContent =
    recommendations.disposal_instructions ||
    "No disposal instructions available.";
  safetyWarnings.textContent = recommendations.safety_warnings || "None";
  ecoTips.textContent = recommendations.eco_tips || "Keep up the good work!";

  // Scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Load user statistics
 */
async function loadUserStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/summary`);
    const data = await response.json();

    if (data.success) {
      const summary = data.data;

      totalDetections.textContent = summary.total_detections || 0;
      totalEcoPoints.textContent = summary.total_eco_points || 0;
      avgConfidence.textContent =
        ((summary.avg_confidence || 0) * 100).toFixed(1) + "%";
    }
  } catch (error) {
    console.error("Error loading stats:", error);
  }
}

/**
 * Show notification toast
 */
function showNotification(message, type = "info") {
  notificationText.textContent = message;
  notification.className = "notification show";

  if (type === "error") {
    notification.classList.add("error");
  } else if (type === "success") {
    notification.classList.add("success");
  }

  // Auto-hide after 4 seconds
  setTimeout(() => {
    notification.classList.remove("show");
  }, 4000);
}

/**
 * Format timestamp to readable date
 */
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

// Auto-refresh stats every 30 seconds
setInterval(loadUserStats, 30000);

// ===== CAMERA MODE FUNCTIONS =====

/**
 * Switch to Upload Mode
 */
function switchToUploadMode() {
  // Stop camera if active
  if (isCameraActive) {
    stopCamera();
  }

  // Update button states
  uploadModeBtn.classList.add("active");
  cameraModeBtn.classList.remove("active");

  // Show upload section, hide camera section
  uploadSection.style.display = "block";
  cameraSection.style.display = "none";
}

/**
 * Switch to Camera Mode
 */
function switchToCameraMode() {
  // Update button states
  cameraModeBtn.classList.add("active");
  uploadModeBtn.classList.remove("active");

  // Show camera section, hide upload section
  cameraSection.style.display = "block";
  uploadSection.style.display = "none";

  // Hide results section when switching modes
  resultsSection.style.display = "none";
}

/**
 * Start Camera Stream
 */
async function startCamera() {
  try {
    // Request camera access with getUserMedia
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "environment", // Use back camera on mobile if available
      },
    });

    // Set video source to camera stream
    cameraFeed.srcObject = cameraStream;

    // Update UI
    isCameraActive = true;
    startCameraBtn.style.display = "none";
    stopCameraBtn.style.display = "flex";
    cameraFeedContainer.style.display = "block";
    cameraInfo.style.display = "none";

    // Update camera status indicator
    const statusIndicator = cameraStatus.querySelector(".status-indicator");
    const statusText = cameraStatus.querySelector(".status-text");
    statusIndicator.classList.remove("off");
    statusIndicator.classList.add("on");
    statusText.textContent = "Camera ON";

    // Reset camera session tracking
    cameraDetectionCount = 0;
    sessionCameraEcoPoints = 0;
    lastDetectedClasses.clear();

    // Show results section for live updates
    resultsSection.style.display = "block";
    sessionEcoPoints.textContent = "0";

    // Start detection loop (detect every 2 seconds)
    detectionInterval = setInterval(captureAndDetect, 2000);

    showNotification("Camera started successfully", "success");
  } catch (error) {
    console.error("Camera access error:", error);
    showNotification(
      "Failed to access camera. Please ensure camera permissions are granted.",
      "error",
    );
  }
}

/**
 * Stop Camera Stream
 */
function stopCamera() {
  // Stop all camera tracks
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }

  // Clear detection interval
  if (detectionInterval) {
    clearInterval(detectionInterval);
    detectionInterval = null;
  }

  // Update UI
  isCameraActive = false;
  startCameraBtn.style.display = "flex";
  stopCameraBtn.style.display = "none";
  cameraFeedContainer.style.display = "none";
  cameraInfo.style.display = "block";

  // Update camera status indicator
  const statusIndicator = cameraStatus.querySelector(".status-indicator");
  const statusText = cameraStatus.querySelector(".status-text");
  statusIndicator.classList.remove("on");
  statusIndicator.classList.add("off");
  statusText.textContent = "Camera OFF";

  // Clear video feed
  cameraFeed.srcObject = null;
  cameraAnnotatedFrame.style.display = "none";

  showNotification("Camera stopped", "info");
}

/**
 * Capture frame from camera and send for detection
 */
async function captureAndDetect() {
  if (!isCameraActive || !cameraFeed) return;

  try {
    // Create canvas to capture frame
    if (!detectionCanvas.getContext) return;

    const context = detectionCanvas.getContext("2d");
    detectionCanvas.width = cameraFeed.videoWidth;
    detectionCanvas.height = cameraFeed.videoHeight;

    // Draw current video frame to canvas
    context.drawImage(
      cameraFeed,
      0,
      0,
      detectionCanvas.width,
      detectionCanvas.height,
    );

    // Convert canvas to base64
    const frameBase64 = detectionCanvas.toDataURL("image/jpeg", 0.8);

    // Send frame to backend for detection
    const response = await fetch(`${API_BASE_URL}/detect/camera`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ frame: frameBase64 }),
    });

    const data = await response.json();

    if (data.success) {
      processCameraDetection(data);
    } else {
      console.error("Detection failed:", data.error);
    }
  } catch (error) {
    console.error("Camera detection error:", error);
  }
}

/**
 * Process camera detection results
 * Handles eco-points carefully to avoid accumulation issues
 */
function processCameraDetection(data) {
  // Display annotated frame
  if (data.annotated_frame) {
    cameraAnnotatedFrame.src = `data:image/jpeg;base64,${data.annotated_frame}`;
    cameraAnnotatedFrame.style.display = "block";
    cameraFeed.style.display = "none"; // Hide raw feed, show annotated
  }

  // Update detections list
  if (data.detections && data.detections.length > 0) {
    detectionsList.innerHTML = "";

    // Track unique classes in this frame
    const currentFrameClasses = new Set();

    data.detections.forEach((detection) => {
      const detectionItem = document.createElement("div");
      detectionItem.className = "detection-item";

      const confidencePercent = (detection.confidence * 100).toFixed(1);
      const className = detection.class_name;

      // Add to current frame classes
      currentFrameClasses.add(className);

      // Calculate eco-points for this detection (for display)
      const basePoints = getBaseEcoPoints(className);
      // Apply confidence multiplier (matches backend logic)
      const multiplier = getConfidenceMultiplier(detection.confidence);
      const points = Math.round(basePoints * multiplier);

      detectionItem.innerHTML = `
        <div class="detection-header">
          <span class="detection-class">${className}</span>
          <span class="detection-confidence">${confidencePercent}%</span>
        </div>
        <div class="detection-points">+${points} eco-points</div>
      `;

      detectionsList.appendChild(detectionItem);
    });

    // Only award eco-points for NEW classes not seen before in this camera session
    const newClassesDetected = [];
    currentFrameClasses.forEach((className) => {
      if (!lastDetectedClasses.has(className)) {
        // This is a new class, award points
        const basePoints = getBaseEcoPoints(className);
        // Use average confidence for new class
        const avgConfidence =
          data.detections
            .filter((d) => d.class_name === className)
            .reduce((sum, d) => sum + d.confidence, 0) /
          data.detections.filter((d) => d.class_name === className).length;

        // Apply confidence multiplier (matches backend logic)
        const multiplier = getConfidenceMultiplier(avgConfidence);
        const points = Math.round(basePoints * multiplier);
        sessionCameraEcoPoints += points;
        lastDetectedClasses.add(className);
        newClassesDetected.push(className);
      }
    });

    // Update session eco-points display (cumulative for unique classes only)
    sessionEcoPoints.textContent = sessionCameraEcoPoints;

    // Update detection count
    cameraDetectionCount++;

    // Save to database when NEW unique items are detected
    if (newClassesDetected.length > 0) {
      saveCameraDetectionToDatabase(data.detections, newClassesDetected);
    }
  } else {
    detectionsList.innerHTML =
      '<p style="color: var(--text-secondary);">No waste detected in current frame.</p>';
  }

  // Generate recommendations for current detections (optional, could be expensive)
  // Only update recommendations every 5 detections to reduce API calls
  if (
    cameraDetectionCount % 5 === 0 &&
    data.detections &&
    data.detections.length > 0
  ) {
    updateCameraRecommendations(data.detections);
  }
}

/**
 * Get base eco-points for a waste class
 * MUST match backend eco_points.py ECO_POINTS_MAP exactly
 */
function getBaseEcoPoints(className) {
  // This mapping MUST stay in sync with backend/eco_points.py
  const ecoPointsMap = {
    // Hazardous waste - highest priority
    battery: 50,
    light_bulb: 40,
    chemical_container: 45,
    chemical_spray_can: 45,

    // Metals - high value recyclables
    can: 15,

    // Plastics - sorted by recyclability
    plastic_bottle: 20,
    plastic_box: 18,
    plastic_bag: 12,
    plastic_cup: 10,
    plastic_cultery: 8,
    scrap_plastic: 10,

    // Paper products
    cardboard: 10,
    reuseable_paper: 8,
    scrap_paper: 5,

    // Packaging waste
    snack_bag: 8,

    // Legacy/generic classes
    "e-waste": 50,
    medical: 50,
    metal: 15,
    glass: 12,
    plastic: 10,
    paper: 8,
    organic: 5,
    "food-waste": 5,
    trash: 2,
    other: 2,
  };

  return ecoPointsMap[className] || 5; // Default 5 points (matches backend)
}

/**
 * Get confidence multiplier based on detection confidence
 * MUST match backend eco_points.py confidence logic exactly
 */
function getConfidenceMultiplier(confidence) {
  // Matches backend CONFIDENCE_BONUS configuration
  if (confidence >= 0.9) {
    return 1.2; // >90% confidence: +20% bonus
  } else if (confidence >= 0.7) {
    return 1.0; // 70-90%: normal points
  } else if (confidence >= 0.5) {
    return 0.8; // 50-70%: -20% penalty
  } else {
    return 0.5; // <50%: very low confidence
  }
}

/**
 * Save camera detection to database (for unique new items only)
 * This ensures detections appear in analytics and admin dashboard
 */
async function saveCameraDetectionToDatabase(
  allDetections,
  newClassesDetected,
) {
  try {
    // Filter detections to only include new classes
    const detectionsToSave = allDetections.filter((d) =>
      newClassesDetected.includes(d.class_name),
    );

    // Capture current frame again to save
    const context = detectionCanvas.getContext("2d");
    const frameBase64 = detectionCanvas.toDataURL("image/jpeg", 0.8);

    // Send to save endpoint
    const response = await fetch(`${API_BASE_URL}/detect/camera/save`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ frame: frameBase64 }),
    });

    const data = await response.json();

    if (data.success) {
      console.log(
        `Saved ${detectionsToSave.length} new detection(s) to database:`,
        newClassesDetected.join(", "),
      );

      // Update recommendations from saved response if available
      if (data.recommendations) {
        disposalInstructions.textContent =
          data.recommendations.disposal_instructions ||
          "Follow local recycling guidelines for proper disposal.";
        safetyWarnings.textContent =
          data.recommendations.safety_warnings ||
          "Sort waste properly to maximize recycling efficiency.";
        ecoTips.textContent =
          data.recommendations.eco_tips ||
          "Live detection active! Keep sorting to earn more eco-points for unique items.";
      }

      // Refresh global stats to reflect new detections
      loadUserStats();
    } else {
      console.error("Failed to save detection:", data.error);
    }
  } catch (error) {
    console.error("Error saving camera detection:", error);
  }
}

/**
 * Update recommendations for camera detections
 */
async function updateCameraRecommendations(detections) {
  try {
    // Get unique waste classes
    const wasteClasses = [...new Set(detections.map((d) => d.class_name))];

    // Create a simple prompt for recommendations
    // Note: In production, you might want to call the backend with the frame
    // For now, we'll just show generic recommendations based on classes

    if (
      wasteClasses.includes("battery") ||
      wasteClasses.includes("light_bulb")
    ) {
      disposalInstructions.textContent =
        "Hazardous waste detected. Take to designated e-waste collection point.";
      safetyWarnings.textContent =
        "Do not dispose in regular trash. Contains hazardous materials.";
    } else if (wasteClasses.some((c) => c.includes("plastic"))) {
      disposalInstructions.textContent =
        "Recyclable plastic detected. Clean and place in recycling bin.";
      safetyWarnings.textContent =
        "Rinse containers before recycling to avoid contamination.";
    } else if (
      wasteClasses.includes("cardboard") ||
      wasteClasses.includes("paper")
    ) {
      disposalInstructions.textContent =
        "Paper products detected. Flatten and place in paper recycling.";
      safetyWarnings.textContent = "Keep dry to maintain recyclability.";
    } else {
      disposalInstructions.textContent =
        "Follow local recycling guidelines for proper disposal.";
      safetyWarnings.textContent =
        "Sort waste properly to maximize recycling efficiency.";
    }

    ecoTips.textContent =
      "Live detection active! Keep sorting to earn more eco-points for unique items.";
  } catch (error) {
    console.error("Error updating recommendations:", error);
  }
}
