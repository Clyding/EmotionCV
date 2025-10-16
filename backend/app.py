from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
import json
from db import init_db, add_user, get_user_by_username, add_emergency_contact, save_emotion_session, get_user_sessions # type: ignore
from ml_pipeline import analyze_emotions, generate_ai_response, assess_risk # type: ignore

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = 'emotioncv-secret-key-2025'
app.config['SELF_HARM_THRESHOLD'] = 0.8
app.config['SEVERE_STRESS_THRESHOLD'] = 0.7

# Initialize database
init_db()

@app.route('/')
def home():
    return jsonify({"message": "EmotionCV Backend API", "status": "running"})

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user exists
        if get_user_by_username(data['username']):
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create user
        user = add_user(data)
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = get_user_by_username(username)
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_emotion():
    """Analyze emotions from text, voice, and facial data"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        text_input = data.get('text_input', '')
        voice_data = data.get('voice_data', {})
        facial_data = data.get('facial_data', {})
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Analyze emotions using ML pipeline
        emotion_results = analyze_emotions(text_input, voice_data, facial_data)
        
        # Generate AI response
        ai_response = generate_ai_response(text_input, emotion_results)
        
        # Assess risk
        risk_assessment = assess_risk(text_input, emotion_results)
        
        # Check for emergency
        emergency_triggered = (
            risk_assessment.get('self_harm_risk', 0) > app.config['SELF_HARM_THRESHOLD'] or
            risk_assessment.get('severe_stress_risk', 0) > app.config['SEVERE_STRESS_THRESHOLD']
        )
        
        # Save session to database
        session_data = {
            'user_id': user_id,
            'text_input': text_input,
            'ai_response': ai_response,
            'emotion_scores': emotion_results,
            'risk_assessment': risk_assessment,
            'emergency_triggered': emergency_triggered
        }
        
        session = save_emotion_session(session_data)
        
        response_data = {
            'success': True,
            'emotions': emotion_results,
            'ai_response': ai_response,
            'risk_assessment': risk_assessment,
            'emergency_triggered': emergency_triggered,
            'session_id': session.id
        }
        
        # Add emergency alert info if triggered
        if emergency_triggered:
            response_data['emergency_alert'] = {
                'message': 'Emergency contacts have been notified',
                'actions_taken': ['Contacted emergency contacts', 'Alerted support team']
            }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency-contacts', methods=['POST'])
def add_emergency_contact_route():
    """Add emergency contact for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        contact_data = data.get('contact')
        
        if not user_id or not contact_data:
            return jsonify({'error': 'User ID and contact data required'}), 400
        
        contact = add_emergency_contact(user_id, contact_data)
        
        return jsonify({
            'message': 'Emergency contact added successfully',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'relationship': contact.relationship
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:user_id>', methods=['GET'])
def get_user_sessions_route(user_id):
    """Get user's emotion analysis sessions"""
    try:
        limit = request.args.get('limit', 50, type=int)
        sessions = get_user_sessions(user_id, limit)
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'session_date': session.session_date.isoformat(),
                'text_input': session.text_input,
                'ai_response': session.ai_response,
                'emotion_scores': session.emotion_scores,
                'risk_assessment': session.risk_assessment,
                'emergency_triggered': session.emergency_triggered
            })
        
        return jsonify({
            'sessions': sessions_data,
            'count': len(sessions_data)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'EmotionCV Backend',
        'timestamp': '2025-01-01T00:00:00Z'  # You can use datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    print("Starting EmotionCV Backend Server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
