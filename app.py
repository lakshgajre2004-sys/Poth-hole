#!/usr/bin/env python3
"""
Pothole Reporting System - Backend Server
A Flask-based backend with all the functionality of the original Node.js system
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime, timedelta
import math
import geopy.distance
from sqlalchemy import func, and_, or_
import base64
from io import BytesIO
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pothole_reporting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='citizen')
    reports_count = db.Column(db.Integer, default=0)
    upvotes_given = db.Column(db.Integer, default=0)
    reputation = db.Column(db.Float, default=0.0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'reports_count': self.reports_count,
            'upvotes_given': self.upvotes_given,
            'reputation': self.reputation,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = db.Column(db.String(20), nullable=False)  # pothole, road_construction, road_closure
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='reported')  # reported, verified, repair_scheduled, fixed
    priority = db.Column(db.Float, default=0.0)
    upvotes = db.Column(db.Integer, default=0)
    road_type = db.Column(db.String(20), default='other')  # highway, main_road, residential, commercial, other
    ward = db.Column(db.String(100))
    estimated_repair_time = db.Column(db.Integer)  # in days
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    verified_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    fixed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_issues')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_issues')
    photos = db.relationship('Photo', backref='issue', lazy=True, cascade='all, delete-orphan')
    upvoters = db.relationship('User', secondary='issue_upvotes', backref='upvoted_issues')

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'location': {
                'type': 'Point',
                'coordinates': [self.longitude, self.latitude]
            },
            'address': self.address,
            'severity': self.severity,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'upvotes': self.upvotes,
            'road_type': self.road_type,
            'ward': self.ward,
            'estimated_repair_time': self.estimated_repair_time,
            'reporter_id': self.reporter_id,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'fixed_at': self.fixed_at.isoformat() if self.fixed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'photos': [photo.to_dict() for photo in self.photos],
            'upvoters': [user.id for user in self.upvoters]
        }

class Photo(db.Model):
    __tablename__ = 'photos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(db.String(36), db.ForeignKey('issues.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'url': f'/uploads/{self.filename}',
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

# Association table for issue upvotes
issue_upvotes = db.Table('issue_upvotes',
    db.Column('issue_id', db.String(36), db.ForeignKey('issues.id'), primary_key=True),
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True)
)

# Duplicate Detection Algorithm
class DuplicateDetector:
    def __init__(self):
        self.DISTANCE_THRESHOLD = 50  # meters
        self.TIME_THRESHOLD = 7  # days
        self.SIMILARITY_THRESHOLD = 0.7

    def find_potential_duplicates(self, new_issue):
        """Find potential duplicate issues"""
        time_threshold = datetime.utcnow() - timedelta(days=self.TIME_THRESHOLD)
        
        # Find issues within time threshold and same type
        nearby_issues = Issue.query.filter(
            and_(
                Issue.type == new_issue['type'],
                Issue.created_at >= time_threshold,
                Issue.status.in_(['reported', 'verified'])
            )
        ).all()

        potential_duplicates = []
        
        for existing_issue in nearby_issues:
            # Calculate distance
            distance = self.calculate_distance(
                new_issue['latitude'], new_issue['longitude'],
                existing_issue.latitude, existing_issue.longitude
            )
            
            if distance <= self.DISTANCE_THRESHOLD:
                similarity_score = self.calculate_similarity(new_issue, existing_issue, distance)
                
                potential_duplicates.append({
                    'issue': existing_issue,
                    'distance': distance,
                    'similarity_score': similarity_score,
                    'is_duplicate': similarity_score > self.SIMILARITY_THRESHOLD
                })
        
        # Sort by similarity score
        potential_duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)
        return potential_duplicates

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        return geopy.distance.distance(point1, point2).meters

    def calculate_similarity(self, new_issue, existing_issue, distance):
        """Calculate similarity score between issues"""
        score = 0
        
        # Distance factor (closer = higher score)
        distance_score = max(0, (self.DISTANCE_THRESHOLD - distance) / self.DISTANCE_THRESHOLD)
        score += distance_score * 0.4  # 40% weight
        
        # Severity match
        if new_issue['severity'] == existing_issue.severity:
            score += 0.3  # 30% weight
        
        # Time proximity
        time_diff = abs((datetime.utcnow() - existing_issue.created_at).total_seconds())
        max_time_diff = self.TIME_THRESHOLD * 24 * 60 * 60
        time_score = max(0, (max_time_diff - time_diff) / max_time_diff)
        score += time_score * 0.2  # 20% weight
        
        # Description similarity (basic keyword matching)
        description_score = self.calculate_description_similarity(
            new_issue['description'], existing_issue.description
        )
        score += description_score * 0.1  # 10% weight
        
        return min(score, 1.0)

    def calculate_description_similarity(self, desc1, desc2):
        """Calculate similarity between descriptions"""
        if not desc1 or not desc2:
            return 0
        
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        common_words = words1.intersection(words2)
        total_words = words1.union(words2)
        
        return len(common_words) / len(total_words) if total_words else 0

# Priority Scoring System
class PriorityCalculator:
    def __init__(self):
        self.severity_scores = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 5
        }
        self.road_type_scores = {
            'highway': 3,
            'main_road': 2,
            'commercial': 2,
            'residential': 1,
            'other': 1
        }

    def calculate_priority(self, issue):
        """Calculate priority score for an issue"""
        score = 0
        
        # Base severity score
        score += self.severity_scores.get(issue.severity, 2)
        
        # Upvotes boost
        score += issue.upvotes * 0.5
        
        # Road type importance
        score += self.road_type_scores.get(issue.road_type, 1)
        
        # Age factor (older issues get higher priority)
        days_since_reported = (datetime.utcnow() - issue.created_at).days
        score += min(days_since_reported * 0.1, 2)  # Cap at 2 points
        
        return round(score, 1)

# Initialize services
duplicate_detector = DuplicateDetector()
priority_calculator = PriorityCalculator()

# API Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        # Check if user already exists
        existing_user = User.query.filter(
            or_(User.username == data.get('username'), User.email == data.get('email'))
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'User with this username or email already exists'
            }), 400
        
        # Create new user
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            role=data.get('role', 'citizen')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/report', methods=['POST'])
def report_issue():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'latitude', 'longitude', 'address', 'description', 'reporter_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Check for duplicates
        potential_duplicates = duplicate_detector.find_potential_duplicates(data)
        best_match = next((dup for dup in potential_duplicates if dup['is_duplicate']), None)
        
        if best_match:
            # Merge with existing issue
            existing_issue = best_match['issue']
            existing_issue.upvotes += 1
            
            # Update severity if new one is higher
            severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            if severity_levels.get(data['severity'], 2) > severity_levels.get(existing_issue.severity, 2):
                existing_issue.severity = data['severity']
            
            # Recalculate priority
            existing_issue.priority = priority_calculator.calculate_priority(existing_issue)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Issue merged with existing report',
                'merged_with': existing_issue.id,
                'is_duplicate': True
            })
        
        # Create new issue
        issue = Issue(
            type=data['type'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            address=data['address'],
            severity=data.get('severity', 'medium'),
            description=data['description'],
            road_type=data.get('road_type', 'other'),
            ward=data.get('ward'),
            reporter_id=data['reporter_id']
        )
        
        # Calculate initial priority
        issue.priority = priority_calculator.calculate_priority(issue)
        
        db.session.add(issue)
        db.session.commit()
        
        # Update user stats
        user = User.query.get(data['reporter_id'])
        if user:
            user.reports_count += 1
            user.last_active = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Issue reported successfully',
            'issue': issue.to_dict(),
            'is_duplicate': False
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/map', methods=['GET'])
def get_issues_map():
    try:
        min_lat = float(request.args.get('minLat', 12.8))
        max_lat = float(request.args.get('maxLat', 13.2))
        min_lng = float(request.args.get('minLng', 77.4))
        max_lng = float(request.args.get('maxLng', 77.8))
        types = request.args.get('types', '').split(',') if request.args.get('types') else []
        statuses = request.args.get('statuses', '').split(',') if request.args.get('statuses') else []
        limit = int(request.args.get('limit', 1000))
        
        # Build query
        query = Issue.query.filter(
            and_(
                Issue.latitude >= min_lat,
                Issue.latitude <= max_lat,
                Issue.longitude >= min_lng,
                Issue.longitude <= max_lng
            )
        )
        
        if types:
            query = query.filter(Issue.type.in_(types))
        
        if statuses:
            query = query.filter(Issue.status.in_(statuses))
        
        issues = query.order_by(Issue.priority.desc(), Issue.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'issues': [issue.to_dict() for issue in issues],
            'count': len(issues)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/<issue_id>/upvote', methods=['POST'])
def upvote_issue(issue_id):
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Check if user already upvoted
        if any(user.id == user_id for user in issue.upvoters):
            return jsonify({'error': 'Already upvoted this issue'}), 400
        
        # Add upvote
        user = User.query.get(user_id)
        if user:
            issue.upvotes += 1
            issue.upvoters.append(user)
            issue.priority = priority_calculator.calculate_priority(issue)
            
            # Update user stats
            user.upvotes_given += 1
            user.last_active = datetime.utcnow()
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Issue upvoted successfully',
            'upvotes': issue.upvotes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/<issue_id>/status', methods=['PATCH'])
def update_issue_status(issue_id):
    try:
        data = request.get_json()
        status = data.get('status')
        verified_by = data.get('verifiedBy')
        estimated_repair_time = data.get('estimatedRepairTime')
        
        valid_statuses = ['reported', 'verified', 'repair_scheduled', 'fixed']
        if status not in valid_statuses:
            return jsonify({
                'error': 'Invalid status',
                'valid_statuses': valid_statuses
            }), 400
        
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        issue.status = status
        
        if status == 'verified' and verified_by:
            issue.verified_by = verified_by
            issue.verified_at = datetime.utcnow()
        
        if status == 'fixed':
            issue.fixed_at = datetime.utcnow()
        
        if estimated_repair_time:
            issue.estimated_repair_time = int(estimated_repair_time)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Issue status updated successfully',
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/stats', methods=['GET'])
def get_stats():
    try:
        ward = request.args.get('ward')
        time_range = int(request.args.get('timeRange', 30))
        
        time_threshold = datetime.utcnow() - timedelta(days=time_range)
        
        # Build query
        query = Issue.query.filter(Issue.created_at >= time_threshold)
        if ward:
            query = query.filter(Issue.ward == ward)
        
        issues = query.all()
        
        if not issues:
            return jsonify({
                'success': True,
                'stats': {
                    'totalIssues': 0,
                    'avgPriority': 0,
                    'avgUpvotes': 0,
                    'avgRepairTime': 0,
                    'typeBreakdown': {},
                    'severityBreakdown': {},
                    'statusBreakdown': {}
                }
            })
        
        # Calculate statistics
        total_issues = len(issues)
        avg_priority = sum(issue.priority for issue in issues) / total_issues
        avg_upvotes = sum(issue.upvotes for issue in issues) / total_issues
        avg_repair_time = sum(issue.estimated_repair_time or 0 for issue in issues) / total_issues
        
        # Breakdowns
        type_breakdown = {}
        severity_breakdown = {}
        status_breakdown = {}
        
        for issue in issues:
            type_breakdown[issue.type] = type_breakdown.get(issue.type, 0) + 1
            severity_breakdown[issue.severity] = severity_breakdown.get(issue.severity, 0) + 1
            status_breakdown[issue.status] = status_breakdown.get(issue.status, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'totalIssues': total_issues,
                'avgPriority': round(avg_priority, 1),
                'avgUpvotes': round(avg_upvotes, 1),
                'avgRepairTime': round(avg_repair_time, 1),
                'typeBreakdown': type_breakdown,
                'severityBreakdown': severity_breakdown,
                'statusBreakdown': status_breakdown
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/issues/<issue_id>', methods=['GET'])
def get_issue(issue_id):
    try:
        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        return jsonify({
            'success': True,
            'issue': issue.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': 'N/A'
    })

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample data if database is empty
        if User.query.count() == 0:
            # Create demo user
            demo_user = User(
                username='demo_user',
                email='demo@example.com',
                role='citizen'
            )
            db.session.add(demo_user)
            db.session.commit()
            
            # Create sample issues
            sample_issues = [
                {
                    'type': 'pothole',
                    'latitude': 12.9716,
                    'longitude': 77.5946,
                    'address': 'MG Road, Bangalore',
                    'severity': 'high',
                    'description': 'Large pothole causing traffic issues',
                    'reporter_id': demo_user.id
                },
                {
                    'type': 'road_construction',
                    'latitude': 12.9800,
                    'longitude': 77.6100,
                    'address': 'Brigade Road, Bangalore',
                    'severity': 'medium',
                    'description': 'Road construction blocking traffic',
                    'reporter_id': demo_user.id
                },
                {
                    'type': 'road_closure',
                    'latitude': 12.9600,
                    'longitude': 77.5800,
                    'address': 'Residency Road, Bangalore',
                    'severity': 'critical',
                    'description': 'Complete road closure due to maintenance',
                    'reporter_id': demo_user.id
                }
            ]
            
            for issue_data in sample_issues:
                issue = Issue(**issue_data)
                issue.priority = priority_calculator.calculate_priority(issue)
                db.session.add(issue)
            
            db.session.commit()
            print("✅ Sample data created successfully!")

if __name__ == '__main__':
    print("🚀 Starting Pothole Reporting System - Python Backend...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🗄️  Database: SQLite (pothole_reporting.db)")
    print("🔄 Initializing database...")
    
    init_db()
    
    print("✅ Database initialized!")
    print("🌐 Starting Flask server...")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
