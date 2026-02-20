# How to Connect Spotify (No API Key Needed for User)

## For Developers: Setting Up Spotify

To enable Spotify login for users, you need to:

1. Go to https://developer.spotify.com/dashboard/
2. Create a new app
3. Get Client ID and Client Secret
4. Add these to your .env file:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

## For Users: No Setup Required

Once the developer configures Spotify, users can simply:
1. Login/Register
2. Go to Settings
3. Select "Spotify" as music service
4. Click "Connect Spotify" 
5. Authorize the app

That's it! No API key needed from users.

## Note
Spotify integration requires the app developer to set up credentials first. Contact the app developer to enable Spotify.
