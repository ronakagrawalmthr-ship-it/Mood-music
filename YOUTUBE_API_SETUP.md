# How to Get YouTube API Key for Full Access

## Step 1: Get YouTube Data API Key

1. Go to: https://console.cloud.google.com/

2. Create a new project:
   - Click "Select Project" at the top
   - Click "New Project"
   - Name it "MoodMusic"

3. Enable YouTube Data API:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click it and click "Enable"

4. Create API Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key

## Step 2: Use the API Key

### Option A: Set in Environment
Add to your .env file:
```
YOUTUBE_API_KEY=your_api_key_here
```

### Option B: Enter via Website
1. Go to http://127.0.0.1:5000
2. Register/Login
3. Click "Setup YouTube" button
4. Enter your API key
5. Click Save

## Step 3: Test
After adding the API key, refresh the page and select a mood - you'll now have access to millions of YouTube videos!

## Note
The free YouTube API has a daily limit of 10,000 queries. For personal use, this is usually enough.
