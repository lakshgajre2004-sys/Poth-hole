# Backend API Server

This is the backend server for the Crowdsourced Pothole Reporting & Tracking System. It provides RESTful API endpoints for managing issues, users, and handling geospatial data.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp config.js .env
# Edit .env with your configuration

# Start MongoDB (if running locally)
mongod

# Start the server
npm run dev
```

## 📁 Project Structure

```
server/
├── models/
│   ├── Issue.js          # Issue data model with geospatial support
│   └── User.js           # User data model
├── routes/
│   ├── issues.js         # Issue-related API endpoints
│   └── users.js          # User-related API endpoints
├── middleware/
│   ├── duplicateDetection.js  # Smart duplicate detection algorithm
│   └── upload.js              # Image upload and processing
├── config.js             # Configuration settings
├── server.js             # Main server file
└── package.json          # Dependencies and scripts
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/pothole-reporting
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
JWT_SECRET=your_jwt_secret_key
```

### MongoDB Setup

1. Install MongoDB locally or use MongoDB Atlas
2. Create a database named `pothole-reporting`
3. The application will automatically create the necessary collections and indexes

### Cloudinary Setup

1. Create a Cloudinary account at https://cloudinary.com
2. Get your cloud name, API key, and API secret from the dashboard
3. Update the environment variables

## 📊 API Endpoints

### Issues

#### Report a New Issue
```http
POST /api/issues/report
Content-Type: multipart/form-data

{
  "type": "pothole",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "address": "MG Road, Bangalore",
  "severity": "high",
  "description": "Large pothole causing traffic issues",
  "roadType": "main_road",
  "ward": "Ward 1",
  "reporterId": "user_id_here",
  "photos": [file1, file2, ...]
}
```

#### Get Issues for Map Display
```http
GET /api/issues/map?minLat=12.8&maxLat=13.2&minLng=77.4&maxLng=77.8&types=pothole,road_construction&statuses=reported,verified&limit=100
```

#### Upvote an Issue
```http
POST /api/issues/:issueId/upvote
Content-Type: application/json

{
  "userId": "user_id_here"
}
```

#### Update Issue Status
```http
PATCH /api/issues/:issueId/status
Content-Type: application/json

{
  "status": "verified",
  "verifiedBy": "official_user_id",
  "estimatedRepairTime": 7
}
```

#### Get Issue Statistics
```http
GET /api/issues/stats?ward=Ward1&timeRange=30
```

#### Get Single Issue Details
```http
GET /api/issues/:issueId
```

### Users

#### Register a New User
```http
POST /api/users/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "role": "citizen"
}
```

#### Get User Profile
```http
GET /api/users/:userId
```

#### Update User Profile
```http
PATCH /api/users/:userId
Content-Type: application/json

{
  "username": "new_username",
  "email": "new_email@example.com"
}
```

#### Get Leaderboard
```http
GET /api/users/leaderboard/top-reporters?limit=10
```

## 🧠 Key Features

### Duplicate Detection Algorithm

The system implements a sophisticated duplicate detection algorithm that:

1. **Geographic Proximity**: Checks for issues within 50 meters
2. **Time Proximity**: Considers reports within 7 days
3. **Type Matching**: Ensures same issue type
4. **Severity Consideration**: Optionally matches severity levels
5. **Similarity Scoring**: Calculates similarity based on multiple factors

```javascript
// Example similarity calculation
const similarityScore = 
  (distanceScore * 0.4) +      // 40% weight for distance
  (severityMatch * 0.3) +      // 30% weight for severity
  (timeScore * 0.2) +          // 20% weight for time
  (descriptionScore * 0.1);    // 10% weight for description
```

### Priority Scoring System

Issues are automatically ranked using a multi-factor scoring system:

```javascript
const priorityScore = 
  severityScore +              // Base severity (1-5 points)
  (upvotes * 0.5) +           // Community validation
  roadTypeScore +             // Road importance (1-3 points)
  ageBonus;                   // Time factor (up to 2 points)
```

### Geospatial Queries

The system uses MongoDB's geospatial capabilities:

- **2dsphere Index**: For efficient location-based queries
- **GeoJSON Format**: Standard format for location data
- **Bounding Box Queries**: For map display optimization
- **Distance Calculations**: Using the geolib library

## 🗄️ Database Schema

### Issues Collection

```javascript
{
  _id: ObjectId,
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
  _id: ObjectId,
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

## 🔍 Database Indexes

The system creates several indexes for optimal performance:

```javascript
// Geospatial index for location queries
issueSchema.index({ location: '2dsphere' });

// Compound indexes for filtering
issueSchema.index({ status: 1, priority: -1 });
issueSchema.index({ type: 1, status: 1 });
```

## 🖼️ Image Processing

The system handles image uploads with:

- **Multer**: For handling multipart/form-data
- **Cloudinary**: For cloud storage and optimization
- **Sharp**: For server-side image processing
- **Automatic Optimization**: Resizing, compression, and format conversion

## 🚀 Deployment

### Local Development
```bash
npm run dev
```

### Production
```bash
npm start
```

### Docker Deployment
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## 🧪 Testing

```bash
# Run tests (when implemented)
npm test

# Run with coverage
npm run test:coverage
```

## 📈 Performance Considerations

- **Geospatial Indexing**: Optimized for location-based queries
- **Image Optimization**: Automatic compression and resizing
- **Pagination**: Limit results for large datasets
- **Caching**: Consider implementing Redis for frequently accessed data
- **CDN**: Use Cloudinary's CDN for fast image delivery

## 🔒 Security

- **Input Validation**: All inputs are validated and sanitized
- **File Upload Security**: Image type and size validation
- **CORS**: Configured for cross-origin requests
- **Rate Limiting**: Consider implementing rate limiting for production

## 🐛 Error Handling

The server includes comprehensive error handling:

- **Validation Errors**: Detailed error messages for invalid inputs
- **Database Errors**: Graceful handling of MongoDB errors
- **File Upload Errors**: Proper error handling for image uploads
- **Network Errors**: Retry logic for external service calls

## 📝 Logging

Consider implementing structured logging with:

- **Winston**: For application logging
- **Morgan**: For HTTP request logging
- **Error Tracking**: Services like Sentry for production monitoring

## 🔄 API Versioning

For future API changes, consider implementing versioning:

```javascript
app.use('/api/v1', routes);
```

## 📊 Monitoring

For production deployment, consider:

- **Health Checks**: `/health` endpoint for monitoring
- **Metrics**: Application performance monitoring
- **Uptime Monitoring**: External monitoring services
- **Log Aggregation**: Centralized logging system
