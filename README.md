# Crowdsourced Pothole Reporting & Tracking System

A comprehensive civic tech platform that empowers citizens to report and track potholes, road construction, and road closures in their city. The system includes a mobile reporting app, a web-based map viewer, and a robust backend API with intelligent duplicate detection and priority scoring.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │   Web Map       │    │   Backend API   │
│   (Reporter)    │◄──►│   (Viewer)      │◄──►│   (Server)      │
│                 │    │                 │    │                 │
│ • GPS Location  │    │ • Interactive   │    │ • REST API      │
│ • Photo Upload  │    │   Map           │    │ • MongoDB       │
│ • Offline Sync  │    │ • Filtering     │    │ • Cloudinary    │
│ • Issue Types   │    │ • Statistics    │    │ • Duplicate     │
└─────────────────┘    └─────────────────┘    │   Detection     │
                                              │ • Priority      │
                                              │   Scoring       │
                                              └─────────────────┘
```

## 🚀 Features

### Core Functionality
- **One-Click Reporting**: Easy issue reporting with automatic GPS location capture
- **Photo Upload**: Support for multiple photos with cloud storage
- **Issue Types**: Potholes, Road Construction, Road Closures
- **Severity Levels**: Low, Medium, High, Critical
- **Status Tracking**: Reported → Verified → Repair Scheduled → Fixed

### Advanced Features
- **Smart Duplicate Detection**: Prevents duplicate reports using GPS proximity and similarity algorithms
- **Priority Scoring System**: Ranks issues based on severity, upvotes, road type, and age
- **Offline Capability**: Reports can be saved offline and synced when connection is restored
- **Interactive Map**: Real-time visualization with custom icons and filtering
- **Upvoting System**: Community verification through upvotes
- **Statistics Dashboard**: Comprehensive analytics and reporting

## 📱 Applications

### 1. Mobile Reporter App (React Native/Expo)
- **Location**: `client-reporter/`
- **Features**:
  - GPS-based location capture
  - Camera integration for photos
  - Offline report storage
  - Issue type selection with icons
  - Severity assessment
  - Automatic sync when online

### 2. Web Map Viewer (React)
- **Location**: `client-mapviewer/`
- **Features**:
  - Interactive map with Leaflet
  - Custom markers for different issue types
  - Real-time filtering and statistics
  - Detailed issue information
  - Responsive design

### 3. Backend API (Node.js/Express)
- **Location**: `server/`
- **Features**:
  - RESTful API endpoints
  - MongoDB with geospatial indexing
  - Cloudinary image storage
  - Duplicate detection algorithm
  - Priority scoring system

## 🛠️ Technology Stack

### Backend
- **Node.js** with Express.js
- **MongoDB** with Mongoose ODM
- **Cloudinary** for image storage
- **Geolib** for distance calculations
- **Sharp** for image processing

### Mobile App
- **React Native** with Expo
- **Expo Location** for GPS
- **Expo Camera** for photo capture
- **AsyncStorage** for offline storage
- **Axios** for API communication

### Web App
- **React** with Create React App
- **Leaflet** for interactive maps
- **React Bootstrap** for UI components
- **Axios** for API communication

## 🔧 Installation & Setup

### Prerequisites
- Node.js (v16 or higher)
- MongoDB (v4.4 or higher)
- Cloudinary account (for image storage)
- Expo CLI (for mobile app)

### 1. Backend Setup

```bash
cd server
npm install

# Create .env file with your configuration
cp config.js .env
# Edit .env with your MongoDB URI and Cloudinary credentials

# Start MongoDB (if running locally)
mongod

# Start the server
npm run dev
```

### 2. Mobile App Setup

```bash
cd client-reporter
npm install

# Install Expo CLI globally
npm install -g @expo/cli

# Start the development server
expo start
```

### 3. Web App Setup

```bash
cd client-mapviewer
npm install

# Start the development server
npm start
```

## 🔑 Configuration

### Environment Variables

Create a `.env` file in the server directory:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/pothole-reporting
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
JWT_SECRET=your_jwt_secret_key
```

### Cloudinary Setup
1. Create a Cloudinary account
2. Get your cloud name, API key, and API secret
3. Update the environment variables

## 📊 API Endpoints

### Issues
- `POST /api/issues/report` - Report a new issue
- `GET /api/issues/map` - Get issues for map display
- `POST /api/issues/:id/upvote` - Upvote an issue
- `PATCH /api/issues/:id/status` - Update issue status
- `GET /api/issues/stats` - Get statistics
- `GET /api/issues/:id` - Get issue details

### Users
- `POST /api/users/register` - Register a new user
- `GET /api/users/:id` - Get user profile
- `PATCH /api/users/:id` - Update user profile
- `GET /api/users/leaderboard/top-reporters` - Get leaderboard

## 🧠 Algorithm Details

### Duplicate Detection Algorithm

The system uses a sophisticated algorithm to detect potential duplicates:

1. **Geographic Proximity**: Issues within 50 meters are considered
2. **Time Proximity**: Reports within 7 days are evaluated
3. **Type Matching**: Same issue type required
4. **Severity Consideration**: Configurable severity matching
5. **Similarity Score**: Calculated based on distance, time, and description

```javascript
// Similarity calculation
const similarityScore = 
  (distanceScore * 0.4) +      // 40% weight for distance
  (severityMatch * 0.3) +      // 30% weight for severity
  (timeScore * 0.2) +          // 20% weight for time
  (descriptionScore * 0.1);    // 10% weight for description
```

### Priority Scoring System

Issues are ranked using a multi-factor scoring system:

```javascript
const priorityScore = 
  severityScore +              // Base severity (1-5 points)
  (upvotes * 0.5) +           // Community validation
  roadTypeScore +             // Road importance (1-3 points)
  ageBonus;                   // Time factor (up to 2 points)
```

## 🗄️ Database Schema

### Issues Collection
```javascript
{
  type: String,              // 'pothole', 'road_construction', 'road_closure'
  location: {
    type: 'Point',
    coordinates: [lng, lat]  // GeoJSON format
  },
  address: String,
  severity: String,          // 'low', 'medium', 'high', 'critical'
  description: String,
  photos: [{
    url: String,
    publicId: String,
    uploadedAt: Date
  }],
  status: String,            // 'reported', 'verified', 'repair_scheduled', 'fixed'
  priority: Number,          // Calculated priority score
  upvotes: Number,
  upvoters: [ObjectId],
  reporter: ObjectId,
  verifiedBy: ObjectId,
  verifiedAt: Date,
  fixedAt: Date,
  estimatedRepairTime: Number,
  ward: String,
  roadType: String,          // 'highway', 'main_road', 'residential', 'commercial', 'other'
  createdAt: Date,
  updatedAt: Date
}
```

### Users Collection
```javascript
{
  username: String,
  email: String,
  role: String,              // 'citizen', 'official', 'admin'
  reportsCount: Number,
  upvotesGiven: Number,
  reputation: Number,
  lastActive: Date,
  createdAt: Date,
  updatedAt: Date
}
```

## 🚀 Deployment

### Backend Deployment
1. Deploy to cloud platform (Heroku, AWS, DigitalOcean)
2. Set up MongoDB Atlas or cloud MongoDB instance
3. Configure environment variables
4. Set up Cloudinary account

### Mobile App Deployment
1. Build with Expo: `expo build:android` or `expo build:ios`
2. Deploy to app stores or distribute as APK/IPA

### Web App Deployment
1. Build: `npm run build`
2. Deploy to static hosting (Netlify, Vercel, GitHub Pages)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API endpoints

## 🔮 Future Enhancements

- Real-time notifications
- Machine learning for automatic severity detection
- Integration with municipal systems
- Mobile app for officials
- Advanced analytics dashboard
- Social media integration
- Multi-language support
