#!/usr/bin/env python3
"""
Demo Server for Pothole Reporting System
A simple Python Flask server to demonstrate the system functionality
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import math

app = Flask(__name__)
CORS(app)

# In-memory storage for demo purposes
issues_db = []
users_db = []

# Sample data for demonstration
sample_issues = [
    {
        "id": str(uuid.uuid4()),
        "type": "pothole",
        "location": {"type": "Point", "coordinates": [77.5946, 12.9716]},
        "address": "MG Road, Bangalore",
        "severity": "high",
        "description": "Large pothole causing traffic issues",
        "photos": [],
        "status": "reported",
        "priority": 4.5,
        "upvotes": 3,
        "upvoters": [],
        "reporter": "demo_user",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "type": "road_construction",
        "location": {"type": "Point", "coordinates": [77.6100, 12.9800]},
        "address": "Brigade Road, Bangalore",
        "severity": "medium",
        "description": "Road construction blocking traffic",
        "photos": [],
        "status": "verified",
        "priority": 3.2,
        "upvotes": 1,
        "upvoters": [],
        "reporter": "demo_user",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "type": "road_closure",
        "location": {"type": "Point", "coordinates": [77.5800, 12.9600]},
        "address": "Residency Road, Bangalore",
        "severity": "critical",
        "description": "Complete road closure due to maintenance",
        "photos": [],
        "status": "repair_scheduled",
        "priority": 5.8,
        "upvotes": 5,
        "upvoters": [],
        "reporter": "demo_user",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
]

# Initialize with sample data
issues_db.extend(sample_issues)

# HTML template for the demo interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pothole Reporting System - Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100%; }
        .sidebar { 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 300px; 
            height: 100vh; 
            background: white; 
            z-index: 1000; 
            overflow-y: auto; 
            padding: 20px;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }
        .map-container { margin-left: 300px; }
        .issue-card { margin-bottom: 10px; }
        .issue-type { font-weight: bold; }
        .pothole { color: #dc3545; }
        .road_construction { color: #fd7e14; }
        .road_closure { color: #6f42c1; }
        .severity-low { color: #28a745; }
        .severity-medium { color: #ffc107; }
        .severity-high { color: #fd7e14; }
        .severity-critical { color: #dc3545; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🕳️ Pothole Reporting System</h2>
        <p class="text-muted">Demo Interface</p>
        
        <div class="mb-3">
            <h5>Report New Issue</h5>
            <form id="reportForm">
                <div class="mb-2">
                    <label class="form-label">Issue Type:</label>
                    <select class="form-select" id="issueType" required>
                        <option value="pothole">🕳️ Pothole</option>
                        <option value="road_construction">🚧 Road Construction</option>
                        <option value="road_closure">🚫 Road Closure</option>
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label">Severity:</label>
                    <select class="form-select" id="severity" required>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label">Description:</label>
                    <textarea class="form-control" id="description" rows="3" required></textarea>
                </div>
                <div class="mb-2">
                    <label class="form-label">Address:</label>
                    <input type="text" class="form-control" id="address" value="Bangalore, India" required>
                </div>
                <button type="submit" class="btn btn-primary">Report Issue</button>
            </form>
        </div>
        
        <div class="mb-3">
            <h5>Statistics</h5>
            <div id="stats">
                <p>Total Issues: <span id="totalIssues">0</span></p>
                <p>Avg Priority: <span id="avgPriority">0</span></p>
                <p>Avg Upvotes: <span id="avgUpvotes">0</span></p>
            </div>
        </div>
        
        <div>
            <h5>Recent Issues</h5>
            <div id="issuesList"></div>
        </div>
    </div>
    
    <div class="map-container">
        <div id="map"></div>
    </div>

    <script>
        // Initialize map
        const map = L.map('map').setView([12.9716, 77.5946], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Custom icons
        function createIcon(type, severity) {
            const colors = {
                low: '#28a745',
                medium: '#ffc107',
                high: '#fd7e14',
                critical: '#dc3545'
            };
            
            const icons = {
                pothole: '🕳️',
                road_construction: '🚧',
                road_closure: '🚫'
            };
            
            return L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="
                    background-color: ${colors[severity]};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 2px solid white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">${icons[type]}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
        }

        // Load and display issues
        function loadIssues() {
            fetch('/api/issues/map?minLat=12.8&maxLat=13.2&minLng=77.4&maxLng=77.8')
                .then(response => response.json())
                .then(data => {
                    displayIssues(data.issues);
                    updateStats(data.issues);
                });
        }

        function displayIssues(issues) {
            // Clear existing markers
            map.eachLayer(layer => {
                if (layer instanceof L.Marker) {
                    map.removeLayer(layer);
                }
            });

            // Add markers for each issue
            issues.forEach(issue => {
                const [lng, lat] = issue.location.coordinates;
                const marker = L.marker([lat, lng], {
                    icon: createIcon(issue.type, issue.severity)
                }).addTo(map);

                marker.bindPopup(`
                    <div>
                        <h6>${getTypeIcon(issue.type)} ${issue.type.replace('_', ' ')}</h6>
                        <p><strong>Severity:</strong> <span class="severity-${issue.severity}">${issue.severity}</span></p>
                        <p><strong>Status:</strong> ${issue.status.replace('_', ' ')}</p>
                        <p><strong>Upvotes:</strong> ${issue.upvotes}</p>
                        <p><strong>Priority:</strong> ${issue.priority}</p>
                        <p><strong>Description:</strong> ${issue.description}</p>
                        <p><strong>Address:</strong> ${issue.address}</p>
                    </div>
                `);
            });
        }

        function updateStats(issues) {
            const total = issues.length;
            const avgPriority = issues.reduce((sum, issue) => sum + issue.priority, 0) / total || 0;
            const avgUpvotes = issues.reduce((sum, issue) => sum + issue.upvotes, 0) / total || 0;

            document.getElementById('totalIssues').textContent = total;
            document.getElementById('avgPriority').textContent = avgPriority.toFixed(1);
            document.getElementById('avgUpvotes').textContent = avgUpvotes.toFixed(1);

            // Update issues list
            const issuesList = document.getElementById('issuesList');
            issuesList.innerHTML = issues.slice(0, 5).map(issue => `
                <div class="issue-card card">
                    <div class="card-body p-2">
                        <div class="issue-type ${issue.type}">${getTypeIcon(issue.type)} ${issue.type.replace('_', ' ')}</div>
                        <div class="severity-${issue.severity}">${issue.severity}</div>
                        <small class="text-muted">${issue.address}</small>
                    </div>
                </div>
            `).join('');
        }

        function getTypeIcon(type) {
            const icons = {
                pothole: '🕳️',
                road_construction: '🚧',
                road_closure: '🚫'
            };
            return icons[type] || '📍';
        }

        // Handle form submission
        document.getElementById('reportForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                type: document.getElementById('issueType').value,
                severity: document.getElementById('severity').value,
                description: document.getElementById('description').value,
                address: document.getElementById('address').value,
                latitude: 12.9716 + (Math.random() - 0.5) * 0.1, // Random location near Bangalore
                longitude: 77.5946 + (Math.random() - 0.5) * 0.1,
                reporterId: 'demo_user'
            };

            fetch('/api/issues/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Issue reported successfully!');
                    document.getElementById('reportForm').reset();
                    loadIssues();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        });

        // Load initial data
        loadIssues();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/issues/report', methods=['POST'])
def report_issue():
    try:
        data = request.get_json()
        
        # Create new issue
        new_issue = {
            "id": str(uuid.uuid4()),
            "type": data.get('type'),
            "location": {
                "type": "Point",
                "coordinates": [data.get('longitude'), data.get('latitude')]
            },
            "address": data.get('address'),
            "severity": data.get('severity'),
            "description": data.get('description'),
            "photos": [],
            "status": "reported",
            "priority": calculate_priority(data.get('severity'), 0, 'other'),
            "upvotes": 0,
            "upvoters": [],
            "reporter": data.get('reporterId'),
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        issues_db.append(new_issue)
        
        return jsonify({
            "success": True,
            "message": "Issue reported successfully",
            "issue": new_issue
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/issues/map', methods=['GET'])
def get_issues_map():
    try:
        min_lat = float(request.args.get('minLat', 12.8))
        max_lat = float(request.args.get('maxLat', 13.2))
        min_lng = float(request.args.get('minLng', 77.4))
        max_lng = float(request.args.get('maxLng', 77.8))
        
        # Filter issues within bounding box
        filtered_issues = []
        for issue in issues_db:
            lng, lat = issue['location']['coordinates']
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                filtered_issues.append(issue)
        
        return jsonify({
            "success": True,
            "issues": filtered_issues,
            "count": len(filtered_issues)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/issues/stats', methods=['GET'])
def get_stats():
    try:
        total_issues = len(issues_db)
        avg_priority = sum(issue['priority'] for issue in issues_db) / total_issues if total_issues > 0 else 0
        avg_upvotes = sum(issue['upvotes'] for issue in issues_db) / total_issues if total_issues > 0 else 0
        
        # Type breakdown
        type_breakdown = {}
        severity_breakdown = {}
        status_breakdown = {}
        
        for issue in issues_db:
            type_breakdown[issue['type']] = type_breakdown.get(issue['type'], 0) + 1
            severity_breakdown[issue['severity']] = severity_breakdown.get(issue['severity'], 0) + 1
            status_breakdown[issue['status']] = status_breakdown.get(issue['status'], 0) + 1
        
        return jsonify({
            "success": True,
            "stats": {
                "totalIssues": total_issues,
                "avgPriority": round(avg_priority, 1),
                "avgUpvotes": round(avg_upvotes, 1),
                "avgRepairTime": 7,  # Demo value
                "typeBreakdown": type_breakdown,
                "severityBreakdown": severity_breakdown,
                "statusBreakdown": status_breakdown
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def calculate_priority(severity, upvotes, road_type):
    """Calculate priority score based on multiple factors"""
    severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 5}
    road_type_scores = {'highway': 3, 'main_road': 2, 'commercial': 2, 'residential': 1, 'other': 1}
    
    score = severity_scores.get(severity, 2)
    score += upvotes * 0.5
    score += road_type_scores.get(road_type, 1)
    
    return round(score, 1)

if __name__ == '__main__':
    print("🚀 Starting Pothole Reporting System Demo Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🗺️  Interactive map with sample data loaded")
    print("📱 Features: Report issues, view map, see statistics")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
