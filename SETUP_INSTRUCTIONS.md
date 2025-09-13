# Setup Instructions for Pothole Reporting System

## Prerequisites

### 1. Install Node.js
1. Go to https://nodejs.org/
2. Download the LTS version (recommended)
3. Run the installer and follow the setup wizard
4. **Important**: Make sure to check "Add to PATH" during installation
5. Restart your terminal/PowerShell after installation

### 2. Verify Installation
Open a new PowerShell window and run:
```bash
node --version
npm --version
```

Both commands should return version numbers.

### 3. Install MongoDB (Optional - for full functionality)
For the complete system, you'll need MongoDB:
1. Go to https://www.mongodb.com/try/download/community
2. Download and install MongoDB Community Server
3. Start MongoDB service

## Running the System

### Option 1: Full System (Node.js + MongoDB)

#### 1. Start the Backend Server
```bash
cd server
npm install
npm run dev
```
The server will start on http://localhost:3000

#### 2. Start the Web Map Viewer
Open a new terminal:
```bash
cd client-mapviewer
npm install
npm start
```
The web app will start on http://localhost:3001

#### 3. Start the Mobile Reporter App
Open a new terminal:
```bash
cd client-reporter
npm install
expo start
```

### Option 2: Demo System (Python - Already Running!)

The demo system is already running on http://localhost:5000

## Quick Start Commands

Once Node.js is installed, run these commands in order:

```bash
# Terminal 1 - Backend Server
cd server
npm install
npm run dev

# Terminal 2 - Web App
cd client-mapviewer
npm install
npm start

# Terminal 3 - Mobile App (optional)
cd client-reporter
npm install
expo start
```

## Troubleshooting

### Node.js not found
- Restart your terminal after installing Node.js
- Check if Node.js is in your PATH: `echo $env:PATH`
- Try running from the Node.js installation directory

### MongoDB connection issues
- Make sure MongoDB is running
- Check the connection string in server/config.js
- For demo purposes, you can use the Python demo server instead

### Port conflicts
- Backend server: Change PORT in server/config.js
- Web app: Change port in client-mapviewer/package.json
- Demo server: Change port in demo_server.py

## Current Status

✅ **Demo Server Running**: http://localhost:5000
- Interactive map with sample data
- Report new issues
- View statistics
- All features working

⏳ **Full System**: Waiting for Node.js installation
- Backend API with MongoDB
- React web application
- React Native mobile app

## Features Available in Demo

- 🗺️ Interactive map with Leaflet
- 📍 Custom markers for different issue types
- 🎨 Color-coded severity levels
- 📊 Real-time statistics
- 📝 Issue reporting form
- 🔄 Live updates

## Next Steps

1. Install Node.js from https://nodejs.org/
2. Restart your terminal
3. Run the setup commands above
4. Enjoy the full system!

The demo server at http://localhost:5000 is fully functional and shows all the system capabilities.
