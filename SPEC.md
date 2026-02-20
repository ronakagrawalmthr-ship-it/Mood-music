# MoodMusic - Specification Document

## Project Overview
- **Project Name**: MoodMusic
- **Type**: Web Application
- **Core Functionality**: A website that accesses the user's camera, detects their facial mood in real-time, and plays Spotify songs matching their detected mood
- **Target Users**: Music enthusiasts who want an immersive, mood-based music experience

## Technology Stack
- **Backend**: Python with Flask
- **Face Detection**: OpenCV + face_recognition library
- **Mood Detection**: Deep learning model (pre-trained FER2013 dataset model)
- **Music Streaming**: Spotify Web API
- **Frontend**: HTML5, CSS3, JavaScript (WebRTC for camera)

## Functionality Specification

### 1. Camera Access
- Access user's webcam via browser getUserMedia API
- Display real-time video feed on the webpage
- Capture frames for mood analysis

### 2. Mood Detection
- Use OpenCV to detect faces in video frames
- Process facial expressions through a pre-trained emotion classifier
- Detect 7 basic emotions: Happy, Sad, Angry, Fear, Surprise, Disgust, Neutral
- Update mood detection every 2 seconds for stability

### 3. Spotify Integration
- OAuth 2.0 authentication with Spotify
- Search for songs based on detected mood
- Mood-to-Playlist mapping:
  - Happy → Upbeat, pop, dance music
  - Sad → Melancholic, acoustic, ballad playlists
  - Angry → Rock, metal, punk
  - Fear → Ambient, electronic, dark
  - Surprise → Electronic, experimental
  - Disgust → Grunge, alternative
  - Neutral → Chill, lo-fi, pop

### 4. Music Player
- Display current playing track info
- Play/Pause controls
- Next track functionality
- Volume control

## UI/UX Specification

### Layout Structure
- **Header**: App title and Spotify connection status
- **Main Content**:
  - Left: Camera feed with mood overlay
  - Right: Music player and playlist
- **Footer**: Controls and status

### Visual Design
- **Color Palette**: 
  - Primary: #1DB954 (Spotify Green)
  - Secondary: #191414 (Dark background)
  - Accent: #535353 (Gray)
  - Text: #FFFFFF (White)
- **Typography**: 
  - Font: Circular, Helvetica, Arial
  - Headings: 24px bold
  - Body: 14px regular
- **Spacing**: 16px base unit

### Components
- Camera preview with face detection bounding box
- Mood indicator badge
- Spotify player embed
- Connect to Spotify button

## Acceptance Criteria
1. ✓ Camera access works and displays video feed
2. ✓ Face detection highlights faces in real-time
3. ✓ Mood detection correctly identifies 7 emotions
4. ✓ Spotify authentication flow works
5. ✓ Songs play based on detected mood
6. ✓ UI is responsive and visually appealing
