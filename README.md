# MoodMusic 🎵

A mood-based music player that uses facial recognition to detect your emotions and plays YouTube/Spotify music matching your mood in real-time.

## Features

- **Real-time Mood Detection**: Uses your webcam to detect facial expressions
- **7 Basic Emotions**: Happy, Sad, Angry, Fear, Surprise, Disgust, Neutral
- **AI-Powered Search**: Smart video search with dynamic queries - always gets fresh new results every time!
- **YouTube & Spotify Integration**: Plays songs based on your detected mood
- **Multiple Login Options**: Email/Password or Google OAuth (for personalized recommendations)
- **Smart Playlists**: Automatically searches for songs that match your mood

## Quick Start

### Prerequisites

- Python 3.8+
- Webcam
- YouTube Data API Key (optional - works with fallback videos too)

### Installation

```bash
cd moodmusic
pip install -r requirements.txt
```

### Configuration

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Add your YouTube API Key** (optional but recommended for best results):
   - Get a free API key from [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "YouTube Data API v3"
   - Add to `.env`:
```
YOUTUBE_API_KEY=your_api_key_here
```

### Run the Application

```bash
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

## How It Works

1. **Start the app**: Open `http://127.0.0.1:5000` in your browser
2. **Login or Continue as Guest**: Create an account or use the app without login
3. **Start Camera**: Click "Start Camera" to begin mood detection
4. **Allow Camera Access**: Grant permission for camera access when prompted
5. **Enjoy Music**: The app will detect your mood and play matching songs automatically

### AI-Powered Search

The app uses dynamic AI-powered search queries that:
- Change every time you search for new results
- Use multiple keyword variations for each mood
- Include trending and recent content filters
- Work even without API key (using curated fallback videos)

## Optional: Google OAuth

To allow users to login with Google and get personalized music recommendations:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "YouTube Data API v3"
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials (Web Application)
6. Set redirect URI to: `http://127.0.0.1:5000/google_callback`
7. Add to `.env`:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

**Note:** Google OAuth is completely optional. The app works perfectly without it!

## Publishing to Production

### For Railway/Render/Replit:

1. Set environment variables in your hosting dashboard:
   - `SECRET_KEY` - Generate a secure random key
   - `YOUTUBE_API_KEY` - Your YouTube API key

2. For Google OAuth (optional):
   - Update `GOOGLE_REDIRECT_URI` to your production URL
   - Add your domain to Google OAuth authorized origins

## Project Structure

```
moodmusic/
├── app.py              # Flask backend with mood detection
├── requirements.txt   # Python dependencies
├── static/
│   ├── style.css      # Styling
│   └── script.js      # Frontend JavaScript
├── templates/
│   ├── index.html    # Main HTML page
│   ├── login.html    # Login page
│   └── register.html # Registration page
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Troubleshooting

### Camera not working
- Ensure you're using HTTPS or localhost
- Check browser permissions for camera access

### Mood detection not accurate
- Ensure good lighting on your face
- Position your face centered in the camera frame

## Technologies Used

- **Backend**: Flask (Python)
- **Face Detection**: OpenCV
- **Mood Detection**: Image analysis with CNN
- **Music APIs**: YouTube Data API, Spotify Web API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## License

MIT License - Feel free to use and modify!
