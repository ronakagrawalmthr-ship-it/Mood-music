# Deploy to Render.com (Free)

## Steps:

### 1. Prepare Your Code
Make sure you have these files in your moodmusic folder:
- app.py
- requirements.txt
- Procfile (created)
- templates/ folder
- static/ folder

### 2. Upload to GitHub
1. Create a new repository on GitHub
2. Upload all your moodmusic files to it
3. Make sure to include .env but NOT your actual API keys

### 3. Deploy to Render
1. Go to https://render.com and sign up
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - Name: moodmusic
   - Environment: Python
   - Build Command: (leave blank)
   - Start Command: `python app.py`
5. Add Environment Variables:
   - `SECRET_KEY` = any random string (e.g., "moodmusic2024")
   - `YOUTUBE_API_KEY` = your YouTube API key
   - `SPOTIFY_CLIENT_ID` = your Spotify client ID (optional)
   - `SPOTIFY_CLIENT_SECRET` = your Spotify secret (optional)
6. Click "Deploy"

### 4. Your App is Live!
Once deployed, Render will give you a URL like:
`https://moodmusic.onrender.com`

### 5. Custom Domain (MoodMusic.com)
To use MoodMusic.com:
1. Buy the domain from GoDaddy/Namecheap
2. In Render, go to your web service → "Settings"
3. Click "Custom Domains" → "Add Custom Domain"
4. Enter your domain and follow the instructions

## That's It! 🎉
Your MoodMusic app is now live on the internet!
