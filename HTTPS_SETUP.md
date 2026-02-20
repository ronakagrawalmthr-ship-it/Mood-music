# Setting up HTTPS for Camera Access on Any Device

## Option 1: Using ngrok (Recommended for testing on other devices)

### Step 1: Install ngrok
Download from https://ngrok.com/download

### Step 2: Run the Flask app
```bash
cd moodmusic
python app.py
```

### Step 3: In another terminal, start ngrok
```bash
ngrok http 5000
```

### Step 4: Access from any device
ngrok will give you an HTTPS URL like `https://abc123.ngrok-free.app`
- Open this URL on your phone/other device
- The camera will work because it's HTTPS!

## Option 2: Using Python's SSL (Local only)

The app now automatically generates an SSL certificate when you run it.
- It will create `cert.pem` and `key.pem` files
- Access via https://127.0.0.1:5000

Note: Self-signed certificates only work on the same computer.

## Option 3: Deploy to Render/Replit (Free HTTPS)

1. Push your code to GitHub
2. Deploy on Render.com or Replit
3. You'll get a free HTTPS URL
4. Camera will work on any device!

## Camera Access Requirements

For camera to work on any device:
1. **HTTPS is required** - Camera access is blocked on HTTP (except localhost)
2. **Browser permissions** - User must allow camera when prompted
3. **Secure context** - Modern browsers require HTTPS for camera/microphone

## Troubleshooting

### If camera still doesn't work:
1. Make sure you're using HTTPS URL
2. Check browser permissions (look for camera icon in address bar)
3. Make sure no other app is using the camera
4. Try Chrome - it has the best camera support
