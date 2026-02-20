"""
MoodMusic - A mood-based music player that uses facial recognition
to detect user emotions and plays YouTube/Spotify music matching the mood.
"""

import os
import base64
import json
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import cv2
import numpy as np
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'moodmusic-secret-key-2024')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moodmusic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enable CORS for mobile access
CORS(app)

# Spotify API Configuration
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://api.spotify.com/v1'

# YouTube API Configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/google_callback')
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

# Fallback videos (works without API key) - Extended with more variety for each mood
FALLBACK_VIDEOS = {
    'happy': [
        {'id': 'hwklZ35jkns', 'title': 'Diljit Dosanjh - G.O.A.T', 'channel': 'Diljit Dosanjh', 'thumbnail': 'https://img.youtube.com/vi/hwklZ35jkns/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'jCbM-98tKjA', 'title': 'Badshah - DJ Waley Babu', 'channel': 'Speed Records', 'thumbnail': 'https://img.youtube.com/vi/jCbM-98tKjA/hqdefault.jpg', 'type': 'youtube'},
        {'id': '5s3R_Oc4Dvw', 'title': 'Punjabi Mashup 2024', 'channel': 'Mxrci', 'thumbnail': 'https://img.youtube.com/vi/5s3R_Oc4Dvw/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'K4TOrB7at0Y', 'title': 'Mundian To Bach Ke', 'channel': 'Panjabi MC', 'thumbnail': 'https://img.youtube.com/vi/K4TOrB7at0Y/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'xQ_IQS3vkYA', 'title': 'Ainvayi Ainvayi - Band Baaja Baaraat', 'channel': 'YRF', 'thumbnail': 'https://img.youtube.com/vi/xQ_IQS3vkYA/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'kU0GMGO0Lms', 'title': 'Kala Chashma - Baar Baar Dekho', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/kU0GMGO0Lms/hqdefault.jpg', 'type': 'youtube'},
        {'id': '6poZ3c1y5fE', 'title': 'Nachdi Phira - Secret Superstar', 'channel': 'Zee Music Company', 'thumbnail': 'https://img.youtube.com/vi/6poZ3c1y5fE/hqdefault.jpg', 'type': 'youtube'},
        {'id': '2Vv-BfVoq4g', 'title': 'Ed Sheeran - Perfect', 'channel': 'Ed Sheeran', 'thumbnail': 'https://img.youtube.com/vi/2Vv-BfVoq4g/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'fC7oUOUEEiY', 'title': 'One Direction - Best Song Ever', 'channel': 'One Direction', 'thumbnail': 'https://img.youtube.com/vi/fC7oUOUEEiY/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'JYdZw2fLhWk', 'title': 'Nacho Nacho - Sita Ramam', 'channel': 'Sagarika Music', 'thumbnail': 'https://img.youtube.com/vi/JYdZw2fLhWk/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'M4sEcIHG3jc', 'title': 'Tere Bin - Simmba', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/M4sEcIHG3jc/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'Ybw2HPBWjMs', 'title': 'Emiway Bantai - Har Ghar Me', 'channel': 'Emiway Bantai', 'thumbnail': 'https://img.youtube.com/vi/Ybw2HPBWjMs/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hT_nvWreIhg', 'title': 'Katy Perry - Roar', 'channel': 'Katy Perry', 'thumbnail': 'https://img.youtube.com/vi/hT_nvWreIhg/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'CevxZvSJLk8', 'title': 'Miley Cyrus - Wrecking Ball', 'channel': 'Miley Cyrus', 'thumbnail': 'https://img.youtube.com/vi/CevxZvSJLk8/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'lYBUbBu4W08', 'title': 'Pharrell Williams - Happy', 'channel': 'Pharrell Williams', 'thumbnail': 'https://img.youtube.com/vi/lYBUbBu4W08/hqdefault.jpg', 'type': 'youtube'},
    ],
    'sad': [
        {'id': 'hoNb6HuNmU0', 'title': 'Tum Hi Ho - Aashiqui 2', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/hoNb6HuNmU0/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'Ram5hNvqujU', 'title': 'Tum Mile', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/Ram5hNvqujU/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'OPXmU5F9qTA', 'title': 'Mere Naam Tu - Zero', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/OPXmU5F9qTA/hqdefault.jpg', 'type': 'youtube'},
        {'id': '9E8klnamorM', 'title': 'Tum Hi Ho', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/9E8klnamorM/hqdefault.jpg', 'type': 'youtube'},
        {'id': '6n3pFFPSlW4', 'title': 'Channa Mereya', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/6n3pFFPSlW4/hqdefault.jpg', 'type': 'youtube'},
        {'id': 's0e-9F8f15o', 'title': 'Agar Tum Saath Ho - Tamasha', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/s0e-9F8f15o/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'VidurV8DaSc', 'title': 'Nazar Laaye - Raanjhanaa', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/VidurV8DaSc/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'r7X3bX3jj9U', 'title': 'Alan Walker - The Spectre', 'channel': 'Alan Walker', 'thumbnail': 'https://img.youtube.com/vi/r7X3bX3jj9U/hqdefault.jpg', 'type': 'youtube'},
        {'id': '3DdpN2_5GQs', 'title': 'Kyun/Din - Laal Singh Chaddha', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/3DdpN2_5GQs/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'v7MPG8e0D2w', 'title': 'Tere Bina - Simmba', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/v7MPG8e0D2w/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'J6L5bU3v6kQ', 'title': 'Safarnama - Tamasha', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/J6L5bU3v6kQ/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'kY2D7c4mocM', 'title': 'Alan Walker - Alone', 'channel': 'Alan Walker', 'thumbnail': 'https://img.youtube.com/vi/kY2D7c4mocM/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'YQHsXMglC9A', 'title': 'Adele - Hello', 'channel': 'Adele', 'thumbnail': 'https://img.youtube.com/vi/YQHsXMglC9A/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hcBWT4zMwvU', 'title': 'Sam Smith - Stay With Me', 'channel': 'Sam Smith', 'thumbnail': 'https://img.youtube.com/vi/hcBWT4zMwvU/hqdefault.jpg', 'type': 'youtube'},
        {'id': '0E0lqL4vL3Y', 'title': 'Ed Sheeran - Photograph', 'channel': 'Ed Sheeran', 'thumbnail': 'https://img.youtube.com/vi/0E0lqL4vL3Y/hqdefault.jpg', 'type': 'youtube'},
    ],
    'angry': [
        {'id': 'UYzLvmxkgGE', 'title': 'Mukkabaaz - Zinda', 'channel': 'FoxStarHindi', 'thumbnail': 'https://img.youtube.com/vi/UYzLvmxkgGE/hqdefault.jpg', 'type': 'youtube'},
        {'id': '8t0pp5v9Ln4', 'title': 'Bhaag Milkha Bhaag', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/8t0pp5v9Ln4/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'GJ-X7bjEfio', 'title': 'Malharini - Angry Indian Goddess', 'channel': 'Saregama', 'thumbnail': 'https://img.youtube.com/vi/GJ-X7bjEfio/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'BuD0X2N6p8M', 'title': 'Bhaag Johnny - Title Track', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/BuD0X2N6p8M/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'TG4GPd2mKc8', 'title': 'Pollichi Po - Thuppakki', 'channel': 'SonyMusicIndia', 'thumbnail': 'https://img.youtube.com/vi/TG4GPd2mKc8/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'ZNCz5nB4b6M', 'title': 'Rise Up - UFC', 'channel': 'UFC', 'thumbnail': 'https://img.youtube.com/vi/ZNCz5nB4b6M/hqdefault.jpg', 'type': 'youtube'},
        {'id': '7wtfhZwyrcc', 'title': 'Adele - Rolling in the Deep', 'channel': 'Adele', 'thumbnail': 'https://img.youtube.com/vi/7wtfhZwyrcc/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'kXYiU_JCYtU', 'title': 'Linkin Park - Numb', 'channel': 'Linkin Park', 'thumbnail': 'https://img.youtube.com/vi/kXYiU_JCYtU/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'b8-mt2JwlK4', 'title': 'System of a Down - Chop Suey', 'channel': 'System of a Down', 'thumbnail': 'https://img.youtube.com/vi/b8-mt2JwlK4/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'y6Sxv-sUYtM', 'title': 'Nirvana - Smells Like Teen Spirit', 'channel': 'Nirvana', 'thumbnail': 'https://img.youtube.com/vi/y6Sxv-sUYtM/hqdefault.jpg', 'type': 'youtube'},
        {'id': '4-AnNhWlz4M', 'title': 'Red Hot Chili Peppers - Californication', 'channel': 'Red Hot Chili Peppers', 'thumbnail': 'https://img.youtube.com/vi/4-AnNhWlz4M/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hsm4poTWjMs', 'title': 'Green Day - Boulevard of Broken Dreams', 'channel': 'Green Day', 'thumbnail': 'https://img.youtube.com/vi/hsm4poTWjMs/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'C6J1J5f0lB4', 'title': 'Eminem - Lose Yourself', 'channel': 'Eminem', 'thumbnail': 'https://img.youtube.com/vi/C6J1J5f0lB4/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'DVv8t5z8k5w', 'title': '2Pac - Hit Em Up', 'channel': '2Pac', 'thumbnail': 'https://img.youtube.com/vi/DVv8t5z8k5w/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'xM4K7B8mW7s', 'title': '50 Cent - In Da Club', 'channel': '50 Cent', 'thumbnail': 'https://img.youtube.com/vi/xM4K7B8mW7s/hqdefault.jpg', 'type': 'youtube'},
    ],
    'fear': [
        {'id': '8nW-IPrzM1g', 'title': 'The Neighbourhood - Sweater Weather', 'channel': 'The Neighbourhood', 'thumbnail': 'https://img.youtube.com/vi/8nW-IPrzM1g/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'yY-viFIvx9E', 'title': 'Lana Del Rey - Summertime Sadness', 'channel': 'Lana Del Rey', 'thumbnail': 'https://img.youtube.com/vi/yY-viFIvx9E/hqdefault.jpg', 'type': 'youtube'},
        {'id': '8J2lrGiAKGw', 'title': 'Radiohead - Creep', 'channel': 'Radiohead', 'thumbnail': 'https://img.youtube.com/vi/8J2lrGiAKGw/hqdefault.jpg', 'type': 'youtube'},
        {'id': '4NRXx6U8ABQ', 'title': 'The Weeknd - Blinding Lights', 'channel': 'The Weeknd', 'thumbnail': 'https://img.youtube.com/vi/4NRXx6U8ABQ/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'j3-D2igOTqA', 'title': 'Billie Eilish - Bad Guy', 'channel': 'Billie Eilish', 'thumbnail': 'https://img.youtube.com/vi/j3-D2igOTqA/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'h9n2WBmJ1pE', 'title': 'Hans Zimmer - Time', 'channel': 'Hans Zimmer', 'thumbnail': 'https://img.youtube.com/vi/h9n2WBmJ1pE/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'U93z2u7lW1w', 'title': 'Pink Floyd - Hey You', 'channel': 'Pink Floyd', 'thumbnail': 'https://img.youtube.com/vi/U93z2u7lW1w/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'X7K3bQw3pNk', 'title': 'The Weeknd - Save Your Tears', 'channel': 'The Weeknd', 'thumbnail': 'https://img.youtube.com/vi/X7K3bQw3pNk/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'VBFH4kL6KiE', 'title': 'A Quiet Life - The Suicide Squad', 'channel': 'Various', 'thumbnail': 'https://img.youtube.com/vi/VBFH4kL6KiE/hqdefault.jpg', 'type': 'youtube'},
        {'id': '7E2a7V7Xj0w', 'title': 'Dramatic Epic Music', 'channel': 'Epic Music', 'thumbnail': 'https://img.youtube.com/vi/7E2a7V7Xj0w/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'nfWlotL6aDM', 'title': 'Scary Sound Effects', 'channel': 'Sound Effects', 'thumbnail': 'https://img.youtube.com/vi/nfWlotL6aDM/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'K4TOrB7at0Y', 'title': 'Panjabi MC - Mundian To Bach Ke', 'channel': 'Panjabi MC', 'thumbnail': 'https://img.youtube.com/vi/K4TOrB7at0Y/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'LsoLEjrDogU', 'title': 'The Beatles - Help', 'channel': 'The Beatles', 'thumbnail': 'https://img.youtube.com/vi/LsoLEjrDogU/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'yJ3L3K4X3Qw', 'title': 'Horror Background Music', 'channel': 'Dark Music', 'thumbnail': 'https://img.youtube.com/vi/yJ3L3K4X3Qw/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'k4V3Mo9f2jA', 'title': 'Mysterious Music', 'channel': 'Ambient', 'thumbnail': 'https://img.youtube.com/vi/k4V3Mo9f2jA/hqdefault.jpg', 'type': 'youtube'},
    ],
    'surprise': [
        {'id': 'fJ9rUzIMcZQ', 'title': 'Queen - Bohemian Rhapsody', 'channel': 'Queen Official', 'thumbnail': 'https://img.youtube.com/vi/fJ9rUzIMcZQ/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'L_jWHffIx5E', 'title': 'Smash Mouth - All Star', 'channel': 'Smash Mouth', 'thumbnail': 'https://img.youtube.com/vi/L_jWHffIx5E/hqdefault.jpg', 'type': 'youtube'},
        {'id': '60ItHLz5WEA', 'title': 'Led Zeppelin - Stairway to Heaven', 'channel': 'Led Zeppelin', 'thumbnail': 'https://img.youtube.com/vi/60ItHLz5WEA/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'CevxZvSJLk8', 'title': 'Miley Cyrus - Wrecking Ball', 'channel': 'Miley Cyrus', 'thumbnail': 'https://img.youtube.com/vi/CevxZvSJLk8/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'EE-xtCF3T94', 'title': 'Tame Impala - The Less I Know The Better', 'channel': 'Tame Impala', 'thumbnail': 'https://img.youtube.com/vi/EE-xtCF3T94/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'k85mRPqvMbE', 'title': 'DJ Snake - Let Me Love You', 'channel': 'DJ Snake', 'thumbnail': 'https://img.youtube.com/vi/k85mRPqvMbE/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hT_nvWreIhg', 'title': 'Katy Perry - Roar', 'channel': 'Katy Perry', 'thumbnail': 'https://img.youtube.com/vi/hT_nvWreIhg/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'YQHsXMglC9A', 'title': 'Adele - Hello', 'channel': 'Adele', 'thumbnail': 'https://img.youtube.com/vi/YQHsXMglC9A/hqdefault.jpg', 'type': 'youtube'},
        {'id': '2Vv-BfVoq4g', 'title': 'Ed Sheeran - Perfect', 'channel': 'Ed Sheeran', 'thumbnail': 'https://img.youtube.com/vi/2Vv-BfVoq4g/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'Lw3Hn/b3VjM', 'title': 'Party Hits 2024', 'channel': 'Various', 'thumbnail': 'https://img.youtube.com/vi/Lw3Hn/b3VjM/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'dP15zlyra3c', 'title': 'Khalid - Young', 'channel': 'Khalid', 'thumbnail': 'https://img.youtube.com/vi/dP15zlyra3c/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'kXYiU_JCYtU', 'title': 'Linkin Park - Numb', 'channel': 'Linkin Park', 'thumbnail': 'https://img.youtube.com/vi/kXYiU_JCYtU/hqdefault.jpg', 'type': 'youtube'},
        {'id': '9bZkp7q19f0', 'title': 'PSY - Gangnam Style', 'channel': 'Official PSY', 'thumbnail': 'https://img.youtube.com/vi/9bZkp7q19f0/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'fJ9rUzIMcZQ', 'title': 'Queen - Bohemian Rhapsody', 'channel': 'Queen', 'thumbnail': 'https://img.youtube.com/vi/fJ9rUzIMcZQ/hqdefault.jpg', 'type': 'youtube'},
        {'id': '3JZ4pnNtycQ', 'title': 'Mark Ronson - Uptown Funk', 'channel': 'Mark Ronson', 'thumbnail': 'https://img.youtube.com/vi/3JZ4pnNtycQ/hqdefault.jpg', 'type': 'youtube'},
    ],
    'disgust': [
        {'id': 'kXYiU_JCYtU', 'title': 'Linkin Park - Numb', 'channel': 'Linkin Park', 'thumbnail': 'https://img.youtube.com/vi/kXYiU_JCYtU/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'b8-mt2JwlK4', 'title': 'System of a Down - Chop Suey', 'channel': 'System of a Down', 'thumbnail': 'https://img.youtube.com/vi/b8-mt2JwlK4/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'y6Sxv-sUYtM', 'title': 'Nirvana - Smells Like Teen Spirit', 'channel': 'Nirvana', 'thumbnail': 'https://img.youtube.com/vi/y6Sxv-sUYtM/hqdefault.jpg', 'type': 'youtube'},
        {'id': '4-AnNhWlz4M', 'title': 'Red Hot Chili Peppers - Californication', 'channel': 'Red Hot Chili Peppers', 'thumbnail': 'https://img.youtube.com/vi/4-AnNhWlz4M/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hsm4poTWjMs', 'title': 'Green Day - Boulevard of Broken Dreams', 'channel': 'Green Day', 'thumbnail': 'https://img.youtube.com/vi/hsm4poTWjMs/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'C6J1J5f0lB4', 'title': 'Eminem - Lose Yourself', 'channel': 'Eminem', 'thumbnail': 'https://img.youtube.com/vi/C6J1J5f0lB4/hqdefault.jpg', 'type': 'youtube'},
        {'id': '7wtfhZwyrcc', 'title': 'Adele - Rolling in the Deep', 'channel': 'Adele', 'thumbnail': 'https://img.youtube.com/vi/7wtfhZwyrcc/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'j3-D2igOTqA', 'title': 'Billie Eilish - Bad Guy', 'channel': 'Billie Eilish', 'thumbnail': 'https://img.youtube.com/vi/j3-D2igOTqA/hqdefault.jpg', 'type': 'youtube'},
        {'id': '8J2lrGiAKGw', 'title': 'Radiohead - Creep', 'channel': 'Radiohead', 'thumbnail': 'https://img.youtube.com/vi/8J2lrGiAKGw/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'r7X3bX3jj9U', 'title': 'Alan Walker - The Spectre', 'channel': 'Alan Walker', 'thumbnail': 'https://img.youtube.com/vi/r7X3bX3jj9U/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'kY2D7c4mocM', 'title': 'Alan Walker - Alone', 'channel': 'Alan Walker', 'thumbnail': 'https://img.youtube.com/vi/kY2D7c4mocM/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'YQHsXMglC9A', 'title': 'Adele - Hello', 'channel': 'Adele', 'thumbnail': 'https://img.youtube.com/vi/YQHsXMglC9A/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'tAGnKpE4NCI', 'title': 'Eminem - Without Me', 'channel': 'Eminem', 'thumbnail': 'https://img.youtube.com/vi/tAGnKpE4NCI/hqdefault.jpg', 'type': 'youtube'},
        {'id': 's0e-9F8f15o', 'title': 'Agar Tum Saath Ho', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/s0e-9F8f15o/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hoNb6HuNmU0', 'title': 'Tum Hi Ho', 'channel': 'T-Series', 'thumbnail': 'https://img.youtube.com/vi/hoNb6HuNmU0/hqdefault.jpg', 'type': 'youtube'},
    ],
    'neutral': [
        {'id': 'jfKfPfyJRdk', 'title': 'Lofi Hip Hop Radio', 'channel': 'Lofi Girl', 'thumbnail': 'https://img.youtube.com/vi/jfKfPfyJRdk/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'DWcJFNfaw9c', 'title': 'Calm Piano Music', 'channel': 'Relaxing Music', 'thumbnail': 'https://img.youtube.com/vi/DWcJFNfaw9c/hqdefault.jpg', 'type': 'youtube'},
        {'id': '5qap5aO4i9A', 'title': 'Lofi Hip Hop Radio', 'channel': 'Lofi Girl', 'thumbnail': 'https://img.youtube.com/vi/5qap5aO4i9A/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'u0Fo8yKErWA', 'title': 'Relaxing Jazz Music', 'channel': 'BGM channel', 'thumbnail': 'https://img.youtube.com/vi/u0Fo8yKErWA/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'V1bFr2SWP1I', 'title': 'Ambient Music for Focus', 'channel': 'Yellow Brick Cinema', 'thumbnail': 'https://img.youtube.com/vi/V1bFr2SWP1I/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'h9n2WBmJ1pE', 'title': 'Hans Zimmer - Time', 'channel': 'Hans Zimmer', 'thumbnail': 'https://img.youtube.com/vi/h9n2WBmJ1pE/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'DuerxT_m4_A', 'title': 'Relaxing Study Music', 'channel': 'Music for Study', 'thumbnail': 'https://img.youtube.com/vi/DuerxT_m4_A/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'E4D1M3K0_Hw', 'title': 'Peaceful Piano', 'channel': 'Relaxing Music', 'thumbnail': 'https://img.youtube.com/vi/E4D1M3K0_Hw/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'KgXK1K3P_kY', 'title': 'Focus Music', 'channel': 'Study Music', 'thumbnail': 'https://img.youtube.com/vi/KgXK1K3P_kY/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'Q0CbN8sfihY', 'title': 'Star Sky - Two Steps From Hell', 'channel': 'Two Steps From Hell', 'thumbnail': 'https://img.youtube.com/vi/Q0CbN8sfihY/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'N1Z9E4e1B7Y', 'title': 'Ambient Relaxing Music', 'channel': 'Relaxation', 'thumbnail': 'https://img.youtube.com/vi/N1Z9E4e1B7Y/hqdefault.jpg', 'type': 'youtube'},
        {'id': '2Vv-BfVoq4g', 'title': 'Ed Sheeran - Perfect', 'channel': 'Ed Sheeran', 'thumbnail': 'https://img.youtube.com/vi/2Vv-BfVoq4g/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'lYBUbBu4W08', 'title': 'Pharrell Williams - Happy', 'channel': 'Pharrell Williams', 'thumbnail': 'https://img.youtube.com/vi/lYBUbBu4W08/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'k85mRPqvMbE', 'title': 'DJ Snake - Let Me Love You', 'channel': 'DJ Snake', 'thumbnail': 'https://img.youtube.com/vi/k85mRPqvMbE/hqdefault.jpg', 'type': 'youtube'},
        {'id': 'hT_nvWreIhg', 'title': 'Katy Perry - Roar', 'channel': 'Katy Perry', 'thumbnail': 'https://img.youtube.com/vi/hT_nvWreIhg/hqdefault.jpg', 'type': 'youtube'},
    ]
}

# Dynamic AI-powered search queries - variations for each mood to get different results
# Each mood has multiple query variations that change based on random parameters

MOOD_QUERY_VARIATIONS = {
    'happy': [
        'happy Indian songs Bollywood 2026 latest trending',
        'Punjabi party mashup 2026 new hits',
        'dance Bollywood songs 2026 popular',
        'feel good Indian music trending',
        'celebration songs Hindi 2026',
        'upbeat Bollywood 2026 latest',
        'happy vibes Indian songs new',
        'festive Punjabi hits 2026',
        'cheerful desi music trending',
        'joyful Bollywood 2026 top songs'
    ],
    'sad': [
        'sad Indian songs Bollywood heartbreak 2026',
        'emotional Hindi songs 2026 latest',
        'melancholy Punjabi sad songs 2026',
        'heartbreak Bollywood 2026 new',
        'tearful Indian music trending',
        'lonely sad songs Hindi 2026',
        'painful Bollywood 2026 latest',
        'emotional breakdown Hindi songs',
        'sad vibes Indian 2026 trending',
        'cry songs Bollywood 2026'
    ],
    'angry': [
        'rock metal Indian songs 2026 latest',
        'aggressive Punjabi hip hop 2026',
        'hardcore Indian rock 2026 trending',
        'intense metal songs India 2026',
        'high energy rock Bollywood 2026',
        'angry rap Indian 2026 new',
        'powerful rock India 2026 trending',
        'furious metal Indian songs',
        'rage rock India 2026 latest',
        'intense desi rock 2026'
    ],
    'fear': [
        'dark suspense Indian background music',
        'horror movie songs Hindi 2026',
        'mysterious Indian music 2026',
        'eerie Bollywood background score',
        'scary Indian songs 2026 latest',
        'dark ambient Indian music 2026',
        'suspenseful Bollywood songs',
        'thriller Indian music 2026',
        'creepy Hindi songs 2026',
        'fearful Indian background music'
    ],
    'surprise': [
        'Bollywood party dance hits 2026 trending',
        'shock party songs Indian 2026',
        'unexpected hit songs Bollywood 2026',
        'surprise dance hits India 2026',
        'mind blown Bollywood songs',
        'unexpected popular songs 2026',
        'trending party Indian 2026',
        'viral Bollywood songs 2026',
        'amazing Indian hits 2026 latest',
        'wow songs Bollywood 2026'
    ],
    'disgust': [
        'alternative rock Indian metal 2026',
        'underground Indian songs 2026',
        'grunge India 2026 latest',
        'punk rock Indian 2026 trending',
        'rebellious Indian songs 2026',
        'dark alternative India 2026',
        'edgy Indian music 2026 latest',
        'counterculture Indian songs',
        'nonconformist Indian music 2026',
        'rebellion rock India 2026'
    ],
    'neutral': [
        'lofi Indian beats chill vibes 2026',
        'relaxing Hindi songs 2026 latest',
        'calm Punjabi music 2026 trending',
        'peaceful Indian songs 2026',
        'focus music Indian 2026 latest',
        'chill Bollywood 2026 trending',
        'ambient Indian music 2026',
        'study music Indian 2026',
        'soothing Hindi songs 2026',
        'trending lofi India 2026'
    ]
}

# Additional search modifiers for variety
SEARCH_MODIFIERS = [
    '',
    'lyrical video',
    'official video',
    'audio',
    'status video',
    'full song',
    'juke box',
    'mix',
    'medley',
    'non-stop',
    'best of',
    'superhit',
    ' blockbuster',
    'chartbuster',
    'trending now'
]

# Time-based parameters to get fresh content
TIME_PERIODS = [
    '2026-01-01T00:00:00Z',  # This year
    '2025-10-01T00:00:00Z',  # Last 4 months
    '2025-06-01T00:00:00Z',  # Last 8 months
    '2025-01-01T00:00:00Z',  # This year so far
]


def generate_dynamic_query(mood):
    """Generate a dynamic AI-powered query for YouTube search."""
    import random
    import time
    
    # Get current timestamp for randomness
    current_time = int(time.time())
    
    # Get mood variations
    variations = MOOD_QUERY_VARIATIONS.get(mood, MOOD_QUERY_VARIATIONS['neutral'])
    
    # Use time-based seed for variety but ensure different results each time
    # Use current minute as part of seed for variety
    minute_of_day = (current_time // 60) % (24 * 60)
    
    # Select base query based on time for variety
    base_index = (current_time // 300) % len(variations)  # Changes every 5 minutes
    base_query = variations[base_index]
    
    # Add random modifier
    modifier = SEARCH_MODIFIERS[current_time % len(SEARCH_MODIFIERS)]
    
    # Build final query
    if modifier:
        query = f"{base_query} {modifier}"
    else:
        query = base_query
    
    return query


def get_search_params(mood):
    """Get search parameters with dynamic query and time period."""
    import random
    import time
    
    current_time = int(time.time())
    
    # Generate dynamic query
    query = generate_dynamic_query(mood)
    
    # Randomly select time period for freshness (70% chance of recent content)
    if random.random() < 0.7:
        time_period = TIME_PERIODS[current_time % len(TIME_PERIODS)]
    else:
        time_period = None  # No time restriction for maximum variety
    
    return query, time_period

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  # Nullable for OAuth users
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # Google OAuth ID
    youtube_api_key = db.Column(db.String(200), nullable=True)
    spotify_token = db.Column(db.Text, nullable=True)
    spotify_refresh_token = db.Column(db.Text, nullable=True)
    preferred_mood = db.Column(db.String(50), default='neutral')
    music_service = db.Column(db.String(20), default='youtube')  # 'youtube' or 'spotify'
    user_interests = db.Column(db.Text, nullable=True)  # JSON string of user's YouTube interests
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    playlists = db.relationship('Playlist', backref='user', lazy=True)

# Playlist Model
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    videos = db.Column(db.Text, nullable=True)  # JSON string of video IDs
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Simple emotion detection using facial landmarks
class MoodDetector:
    """Mood detector using OpenCV and facial analysis."""
    
    def __init__(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        self.emotions = ['neutral', 'happy', 'sad', 'angry', 'fear', 'surprise', 'disgust']
        self.last_mood = 'neutral'
        self.mood_confidence = 0.5
        self.mood_history = []
        self.history_size = 5
        
    def detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return faces, gray
    
    def detect_eyes(self, face_region, gray_face):
        eyes = self.eye_cascade.detectMultiScale(gray_face, 1.1, 3)
        return eyes
    
    def analyze_emotion(self, face_region, gray):
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_face = gray
            
        resized = cv2.resize(gray_face, (48, 48))
        normalized = resized / 255.0
        
        mean_brightness = np.mean(normalized)
        std_brightness = np.std(normalized)
        
        h, w = gray_face.shape
        upper_half = gray_face[:h//2, :]
        lower_half = gray_face[h//2:, :]
        
        upper_mean = np.mean(upper_half)
        lower_mean = np.mean(lower_half)
        contrast = upper_mean - lower_mean
        
        edges = cv2.Canny(gray_face, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        mouth_region = gray_face[h*3//4:, w//4:3*w//4]
        mouth_mean = np.mean(mouth_region)
        
        mood = 'neutral'
        confidence = 0.5
        
        if mean_brightness > 0.65 and upper_mean > lower_mean:
            mood = 'happy'
            confidence = 0.75
        elif mean_brightness < 0.4 and std_brightness < 0.15:
            mood = 'sad'
            confidence = 0.65
        elif edge_density > 0.15 and contrast < -20:
            mood = 'surprise'
            confidence = 0.6
        elif mouth_mean < 80 and contrast > 30:
            mood = 'angry'
            confidence = 0.6
        elif mean_brightness < 0.35 and edge_density > 0.1:
            mood = 'fear'
            confidence = 0.55
        else:
            mood = 'neutral'
            confidence = 0.6
        
        self.mood_history.append(mood)
        if len(self.mood_history) > self.history_size:
            self.mood_history.pop(0)
        
        if len(self.mood_history) >= 3:
            from collections import Counter
            mood_counts = Counter(self.mood_history)
            most_common = mood_counts.most_common(1)[0][0]
            if mood_counts[most_common] >= 2:
                mood = most_common
        
        self.last_mood = mood
        self.mood_confidence = confidence
        
        return {'mood': mood, 'confidence': confidence}
    
    def detect_mood(self, frame):
        faces, gray = self.detect_face(frame)
        
        if len(faces) == 0:
            return {'mood': self.last_mood, 'confidence': 0.3, 'face_detected': False}
        
        face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = face
        
        face_region = frame[y:y+h, x:x+w]
        gray_face = gray[y:y+h, x:x+w]
        
        eyes = self.detect_eyes(face_region, gray_face)
        
        emotion_data = self.analyze_emotion(face_region, gray_face)
        emotion_data['face_detected'] = True
        emotion_data['face_coords'] = {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
        emotion_data['eyes_detected'] = len(eyes) > 0
        
        return emotion_data

# Initialize mood detector
mood_detector = MoodDetector()

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', logged_in=current_user.is_authenticated)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already taken')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/save_api_key', methods=['POST'])
@login_required
def save_api_key():
    """Save user's YouTube API key."""
    data = request.get_json()
    api_key = data.get('api_key', '')
    
    current_user.youtube_api_key = api_key
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'API key saved successfully'})

@app.route('/get_user_settings')
@login_required
def get_user_settings():
    """Get user's saved settings."""
    return jsonify({
        'youtube_api_key': current_user.youtube_api_key or '',
        'music_service': current_user.music_service,
        'preferred_mood': current_user.preferred_mood
    })

@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    """Save user's preferences."""
    data = request.get_json()
    
    current_user.music_service = data.get('music_service', 'youtube')
    current_user.preferred_mood = data.get('preferred_mood', 'neutral')
    
    db.session.commit()
    
    return jsonify({'success': True})

# Spotify OAuth routes
@app.route('/spotify_login')
@login_required
def spotify_login():
    """Start Spotify OAuth flow."""
    if not SPOTIFY_CLIENT_ID:
        return jsonify({'error': 'Spotify not configured. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env file'}), 400
    
    scope = 'user-read-private user-read-email playlist-read-private'
    # Use a fixed redirect URI that matches what's configured in Spotify Dashboard
    redirect_uri = 'http://127.0.0.1:5000/spotify_callback'
    auth_url = f"{SPOTIFY_AUTH_URL}?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    
    return jsonify({'auth_url': auth_url})

@app.route('/spotify_callback')
def spotify_callback():
    """Handle Spotify OAuth callback."""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return render_template('index.html', error=f'Spotify authorization failed: {error}')
    
    if not code:
        return render_template('index.html', error='Spotify authorization failed - no code received')
    
    # Exchange code for token
    redirect_uri = 'http://127.0.0.1:5000/spotify_callback'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)
    
    if response.status_code != 200:
        return render_template('index.html', error=f'Spotify token exchange failed: {response.status_code}')
    
    tokens = response.json()
    current_user.spotify_token = tokens.get('access_token')
    current_user.spotify_refresh_token = tokens.get('refresh_token')
    current_user.music_service = 'spotify'
    db.session.commit()
    
    return redirect(url_for('index'))

# Google OAuth Routes
@app.route('/google_login')
def google_login():
    """Start Google OAuth flow for Gmail login."""
    if not GOOGLE_CLIENT_ID:
        return jsonify({'error': 'Google OAuth not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env file'}), 400
    
    # Request scopes for YouTube data access
    scope = 'openid email profile https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl'
    
    # Generate state for security
    import secrets
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    auth_url = f"{GOOGLE_AUTH_URL}?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope={scope}&state={state}&access_type=offline&prompt=consent"
    
    return jsonify({'auth_url': auth_url})

@app.route('/google_callback')
def google_callback():
    """Handle Google OAuth callback."""
    error = request.args.get('error')
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state
    if state != session.get('oauth_state'):
        return render_template('index.html', error='OAuth state mismatch. Please try again.')
    
    if error:
        return render_template('index.html', error=f'Google authorization failed: {error}')
    
    if not code:
        return render_template('index.html', error='Google authorization failed - no code received')
    
    # Exchange code for tokens
    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': GOOGLE_REDIRECT_URI
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
    
    if response.status_code != 200:
        return render_template('index.html', error=f'Google token exchange failed: {response.status_code}')
    
    tokens = response.json()
    access_token = tokens.get('access_token')
    
    # Get user info
    userinfo_response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if userinfo_response.status_code != 200:
        return render_template('index.html', error='Failed to get user info')
    
    userinfo = userinfo_response.json()
    google_id = userinfo.get('id')
    email = userinfo.get('email')
    name = userinfo.get('name')
    
    # Check if user exists
    user = User.query.filter_by(google_id=google_id).first()
    
    if not user:
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Link Google account to existing user
            existing_user.google_id = google_id
            user = existing_user
        else:
            # Create new user
            user = User(
                username=name or email.split('@')[0],
                email=email,
                google_id=google_id,
                password=None  # No password for OAuth users
            )
            db.session.add(user)
    
    db.session.commit()
    
    # Fetch user's YouTube interests
    fetch_youtube_interests(user, access_token)
    
    login_user(user)
    return redirect(url_for('index'))

def fetch_youtube_interests(user, access_token):
    """Fetch user's YouTube subscriptions and liked videos to determine interests."""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        interests = []
        
        # Get user subscriptions (channels they follow)
        subs_url = f"https://www.googleapis.com/youtube/v3/subscriptions?part=snippet&mine=true&maxResults=50"
        subs_response = requests.get(subs_url, headers=headers)
        
        if subs_response.status_code == 200:
            subs_data = subs_response.json()
            for item in subs_data.get('items', []):
                channel_title = item['snippet']['title']
                # Extract keywords from channel names
                words = channel_title.lower().split()
                interests.extend([w for w in words if len(w) > 2])
        
        # Get user's liked videos
        likes_url = "https://www.googleapis.com/youtube/v3/videos?part=snippet&myRating=like&maxResults=50"
        likes_response = requests.get(likes_url, headers=headers)
        
        if likes_response.status_code == 200:
            likes_data = likes_response.json()
            for item in likes_data.get('items', []):
                title = item['snippet']['title']
                tags = item['snippet'].get('tags', [])
                # Extract keywords from title
                words = title.lower().replace('-', ' ').replace('|', ' ').split()
                interests.extend([w for w in words if len(w) > 2])
                interests.extend([t.lower() for t in tags])
        
        # Get user's playlist (watch history)
        playlist_url = "https://www.googleapis.com/youtube/v3/playlists?part=snippet&mine=true&maxResults=20"
        playlist_response = requests.get(playlist_url, headers=headers)
        
        if playlist_response.status_code == 200:
            playlist_data = playlist_response.json()
            for item in playlist_data.get('items', []):
                playlist_title = item['snippet']['title']
                words = playlist_title.lower().split()
                interests.extend([w for w in words if len(w) > 2])
        
        # Count and get most common interests
        from collections import Counter
        interest_counts = Counter(interests)
        
        # Filter out common words
        common_words = {'the', 'and', 'for', 'with', 'from', 'your', 'this', 'that', 'video', 'music', 'song', 'official', 'lyric', 'lyrics', 'video', 'hd', 'full', 'new', 'best', 'top', 'mix', '2024', '2025', '2026'}
        filtered_interests = {k: v for k, v in interest_counts.items() if k not in common_words}
        
        # Get top interests
        top_interests = sorted(filtered_interests.items(), key=lambda x: x[1], reverse=True)[:20]
        user_interests = json.dumps([item[0] for item in top_interests])
        
        user.user_interests = user_interests
        db.session.commit()
        
        print(f"User interests fetched: {user_interests}")
        
    except Exception as e:
        print(f"Error fetching YouTube interests: {e}")

@app.route('/get_user_interests')
@login_required
def get_user_interests():
    """Get user's YouTube interests."""
    if not current_user.google_id:
        return jsonify({'error': 'Not connected to Google/YouTube', 'interests': []})
    
    if current_user.user_interests:
        try:
            interests = json.loads(current_user.user_interests)
            return jsonify({'interests': interests})
        except:
            pass
    
    return jsonify({'interests': [], 'message': 'No interests found. Login with Google to fetch your YouTube interests.'})

@app.route('/search_based_on_interests', methods=['POST'])
def search_based_on_interests():
    """Search YouTube videos based on user's interests."""
    import random
    
    try:
        data = request.get_json()
        mood = data.get('mood', 'neutral')
        shuffle = data.get('shuffle', False)
        
        # Get API key
        api_key = YOUTUBE_API_KEY
        if current_user.is_authenticated and current_user.youtube_api_key:
            api_key = current_user.youtube_api_key
        
        # Check if user has Google/YouTube connection and interests
        if current_user.is_authenticated and current_user.google_id and current_user.user_interests:
            try:
                interests = json.loads(current_user.user_interests)
                if interests:
                    # Generate search query from interests
                    interest_query = ' '.join(interests[:5])
                    
                    # Combine with mood
                    mood_query = MOOD_QUERY_VARIATIONS.get(mood, MOOD_QUERY_VARIATIONS['neutral'])[0]
                    
                    # Create hybrid query
                    combined_query = f"{interest_query} {mood_query}"
                    
                    # Search with combined query
                    if api_key and api_key != 'YOUR_YOUTUBE_API_KEY_HERE':
                        params = {
                            'part': 'snippet',
                            'q': combined_query,
                            'type': 'video',
                            'videoCategoryId': '10',
                            'maxResults': 15,
                            'key': api_key,
                            'order': 'relevance'
                        }
                        
                        response = requests.get(YOUTUBE_SEARCH_URL, params=params)
                        
                        if response.status_code == 200:
                            results = response.json()
                            videos = []
                            for item in results.get('items', []):
                                video_id = item['id']['videoId']
                                snippet = item['snippet']
                                videos.append({
                                    'id': video_id,
                                    'title': snippet['title'],
                                    'channel': snippet['channelTitle'],
                                    'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
                                    'youtube_url': f'https://www.youtube.com/watch?v={video_id}',
                                    'embed_url': f'https://www.youtube.com/embed/{video_id}',
                                    'type': 'youtube'
                                })
                            
                            if shuffle:
                                random.shuffle(videos)
                            
                            return jsonify({'videos': videos, 'mood': mood, 'mode': 'interests'})
            except Exception as e:
                print(f"Error using interests: {e}")
        
        # Fallback to regular search
        return search_youtube(mood, shuffle)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Routes
@app.route('/detect_mood', methods=['POST'])
def detect_mood():
    """Detect mood from base64 encoded image."""
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Could not decode image'}), 400
        
        mood_data = mood_detector.detect_mood(frame)
        
        return jsonify(mood_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/set_mood', methods=['POST'])
def set_mood():
    """Set mood manually."""
    try:
        data = request.get_json()
        mood = data.get('mood', 'neutral')
        
        valid_moods = ['happy', 'sad', 'angry', 'fear', 'surprise', 'disgust', 'neutral']
        if mood not in valid_moods:
            return jsonify({'error': 'Invalid mood'}), 400
        
        mood_detector.last_mood = mood
        mood_detector.mood_confidence = 1.0
        
        # Save to user preferences if logged in
        if current_user.is_authenticated:
            current_user.preferred_mood = mood
            db.session.commit()
        
        return jsonify({
            'mood': mood,
            'confidence': 1.0,
            'manual': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_videos', methods=['POST'])
def search_videos():
    """Search for YouTube/Spotify videos based on mood."""
    try:
        data = request.get_json()
        mood = data.get('mood', 'neutral')
        shuffle = data.get('shuffle', False)
        
        # Check user's preferred music service
        music_service = 'youtube'
        if current_user.is_authenticated:
            music_service = current_user.music_service
        
        # If using Spotify with valid token, search Spotify
        if music_service == 'spotify' and current_user.is_authenticated and current_user.spotify_token:
            return search_spotify(mood, shuffle)
        
        # Otherwise use YouTube
        return search_youtube(mood, shuffle)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def search_youtube(mood, shuffle=False):
    """Search YouTube for mood-based videos with dynamic AI-powered queries."""
    import random
    
    # Get API key (from user if logged in, otherwise from env)
    api_key = YOUTUBE_API_KEY
    if current_user.is_authenticated and current_user.youtube_api_key:
        api_key = current_user.youtube_api_key
    
    # If no API key, use dynamic fallback with random selection
    if not api_key or api_key == 'YOUR_YOUTUBE_API_KEY_HERE':
        # Use dynamic query selection for fallback too
        fallback_videos = FALLBACK_VIDEOS.get(mood, FALLBACK_VIDEOS['neutral'])
        # Shuffle and return varied results
        random.shuffle(fallback_videos)
        videos = format_videos(fallback_videos)
        # Add some randomness to which videos are returned
        if len(videos) > 10:
            videos = videos[:10]
        return jsonify({'videos': videos, 'mood': mood, 'mode': 'fallback'})
    
    # Get dynamic search parameters
    query, time_period = get_search_params(mood)
    
    params = {
        'part': 'snippet',
        'q': query + ' music',
        'type': 'video',
        'videoCategoryId': '10',
        'maxResults': 15,
        'key': api_key
    }
    
    # Add time period for fresh content if available
    if time_period:
        params['publishedAfter'] = time_period
    
    # Add variety in ordering - use relevance or viewCount randomly
    ordering = 'relevance' if random.random() < 0.7 else 'viewCount'
    params['order'] = ordering
    
    response = requests.get(YOUTUBE_SEARCH_URL, params=params)
    
    if response.status_code != 200:
        videos = FALLBACK_VIDEOS.get(mood, FALLBACK_VIDEOS['neutral'])
        if shuffle:
            random.shuffle(videos)
        videos = format_videos(videos)
        return jsonify({'videos': videos, 'mood': mood, 'mode': 'fallback'})
    
    results = response.json()
    
    if 'error' in results:
        videos = FALLBACK_VIDEOS.get(mood, FALLBACK_VIDEOS['neutral'])
        if shuffle:
            random.shuffle(videos)
        videos = format_videos(videos)
        return jsonify({'videos': videos, 'mood': mood, 'mode': 'fallback'})
    
    videos = []
    for item in results.get('items', []):
        video_id = item['id']['videoId']
        snippet = item['snippet']
        videos.append({
            'id': video_id,
            'title': snippet['title'],
            'channel': snippet['channelTitle'],
            'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
            'youtube_url': f'https://www.youtube.com/watch?v={video_id}',
            'embed_url': f'https://www.youtube.com/embed/{video_id}',
            'type': 'youtube'
        })
    
    if shuffle:
        random.shuffle(videos)
    
    return jsonify({'videos': videos, 'mood': mood, 'mode': 'api'})

def search_spotify(mood):
    """Search Spotify for mood-based tracks."""
    if not current_user.spotify_token:
        return search_youtube(mood)
    
    # Spotify mood-based playlists/seed tracks
    spotify_queries = {
        'happy': 'happy bollywood party',
        'sad': 'sad bollywood heartbreak',
        'angry': 'rock metal punk',
        'fear': 'dark ambient',
        'surprise': 'party dance',
        'disgust': 'alternative rock',
        'neutral': 'chill lofi'
    }
    
    query = spotify_queries.get(mood, spotify_queries['neutral'])
    
    headers = {'Authorization': f'Bearer {current_user.spotify_token}'}
    
    # Search for tracks
    search_url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=10"
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        return search_youtube(mood)
    
    results = response.json()
    
    videos = []
    for item in results.get('tracks', {}).get('items', []):
        # Get album art
        thumbnail = item['album']['images'][0]['url'] if item['album']['images'] else ''
        
        videos.append({
            'id': item['id'],
            'title': item['name'],
            'channel': item['artists'][0]['name'] if item['artists'] else 'Unknown',
            'thumbnail': thumbnail,
            'preview_url': item.get('preview_url'),
            'spotify_url': item['external_urls']['spotify'],
            'type': 'spotify'
        })
    
    return jsonify({'videos': videos, 'mood': mood, 'mode': 'spotify'})

def format_videos(videos):
    """Format video data for frontend."""
    formatted = []
    for v in videos:
        formatted.append({
            'id': v['id'],
            'title': v['title'],
            'channel': v['channel'],
            'thumbnail': v['thumbnail'],
            'youtube_url': f"https://www.youtube.com/watch?v={v['id']}",
            'embed_url': f"https://www.youtube.com/embed/{v['id']}",
            'type': 'youtube'
        })
    return formatted

@app.route('/search_by_text', methods=['POST'])
def search_by_text():
    """Search for videos based on text description with AI-powered dynamic queries."""
    try:
        import random
        data = request.get_json()
        text = data.get('text', '').lower().strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Detect mood from text
        detected_mood = 'neutral'
        
        text_mood_map = {
            'breakup': 'sad', 'heartbroken': 'sad', 'sad': 'sad', 'depressed': 'sad',
            'happy': 'happy', 'excited': 'happy', 'party': 'happy', 'celebration': 'happy',
            'angry': 'angry', 'mad': 'angry', 'frustrated': 'angry',
            'fear': 'fear', 'scared': 'fear',
            'surprise': 'surprise', 'shocked': 'surprise',
            'disgust': 'disgust', 'gross': 'disgust',
            'neutral': 'neutral', 'bored': 'neutral', 'tired': 'neutral',
            'relaxing': 'neutral', 'chill': 'neutral', 'focus': 'neutral',
            'workout': 'happy', 'gym': 'happy',
            'romantic': 'happy', 'love': 'happy', 'in love': 'happy',
            'lonely': 'sad', 'nostalgic': 'sad',
            'motivated': 'happy', 'energetic': 'happy',
            'sleepy': 'neutral', 'peaceful': 'neutral'
        }
        
        for key, value in text_mood_map.items():
            if key in text:
                detected_mood = value
                break
        
        # Use dynamic AI-powered search for the detected mood
        return search_youtube(detected_mood)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_api_key_status')
def get_api_key_status():
    """Check if API key is configured."""
    has_key = bool(YOUTUBE_API_KEY and YOUTUBE_API_KEY != 'YOUR_YOUTUBE_API_KEY_HERE')
    
    if current_user.is_authenticated and current_user.youtube_api_key:
        has_key = True
    
    # Check if Google OAuth is configured
    google_oauth_configured = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    
    return jsonify({'configured': has_key, 'google_oauth': google_oauth_configured})

# Playlist Routes
@app.route('/create_playlist', methods=['POST'])
@login_required
def create_playlist():
    """Create a new playlist for a mood."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        mood = data.get('mood', 'neutral')
        
        if not name:
            return jsonify({'error': 'Playlist name is required'}), 400
        
        # Create new playlist
        playlist = Playlist(
            name=name,
            mood=mood,
            user_id=current_user.id,
            videos='[]'
        )
        db.session.add(playlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'mood': playlist.mood,
                'videos': []
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_playlists', methods=['GET'])
@login_required
def get_playlists():
    """Get all playlists for the current user."""
    try:
        playlists = Playlist.query.filter_by(user_id=current_user.id).all()
        result = []
        for p in playlists:
            videos = []
            if p.videos:
                try:
                    videos = json.loads(p.videos)
                except:
                    videos = []
            result.append({
                'id': p.id,
                'name': p.name,
                'mood': p.mood,
                'videos': videos,
                'created_at': p.created_at.isoformat() if p.created_at else None
            })
        return jsonify({'playlists': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_to_playlist', methods=['POST'])
@login_required
def add_to_playlist():
    """Add a video to a playlist."""
    try:
        data = request.get_json()
        playlist_id = data.get('playlist_id')
        video = data.get('video')
        
        if not playlist_id or not video:
            return jsonify({'error': 'Playlist ID and video are required'}), 400
        
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        # Add video to playlist
        videos = []
        if playlist.videos:
            try:
                videos = json.loads(playlist.videos)
            except:
                videos = []
        
        # Check if video already exists
        if not any(v.get('id') == video.get('id') for v in videos):
            videos.append(video)
            playlist.videos = json.dumps(videos)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'videos': videos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_from_playlist', methods=['POST'])
@login_required
def remove_from_playlist():
    """Remove a video from a playlist."""
    try:
        data = request.get_json()
        playlist_id = data.get('playlist_id')
        video_id = data.get('video_id')
        
        if not playlist_id or not video_id:
            return jsonify({'error': 'Playlist ID and video ID are required'}), 400
        
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        # Remove video from playlist
        videos = []
        if playlist.videos:
            try:
                videos = json.loads(playlist.videos)
            except:
                videos = []
        
        videos = [v for v in videos if v.get('id') != video_id]
        playlist.videos = json.dumps(videos)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'videos': videos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_playlist', methods=['POST'])
@login_required
def delete_playlist():
    """Delete a playlist."""
    try:
        data = request.get_json()
        playlist_id = data.get('playlist_id')
        
        if not playlist_id:
            return jsonify({'error': 'Playlist ID is required'}), 400
        
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        db.session.delete(playlist)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play_playlist/<int:playlist_id>')
@login_required
def play_playlist(playlist_id):
    """Get videos from a playlist to play."""
    try:
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        videos = []
        if playlist.videos:
            try:
                videos = json.loads(playlist.videos)
            except:
                videos = []
        
        return jsonify({
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'mood': playlist.mood
            },
            'videos': videos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on plain HTTP for simplicity - works without SSL certificates
    print("Starting MoodMusic on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
