from flask import Blueprint, jsonify, request
from providers.quest_engine import QuestEngine
from models import db

quest_bp = Blueprint('quest_bp', __name__)

@quest_bp.route('/api/quests', methods=['GET'])
def get_quests():
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
        
    try:
        data = QuestEngine.get_weekly_quests(session_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@quest_bp.route('/api/quests/<int:quest_id>/complete', methods=['POST'])
def complete_quest(quest_id):
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id:
        print(f"DEBUG: quest_complete failed - session_id missing (quest_id: {quest_id})")
        return jsonify({"error": "session_id required"}), 400
        
    try:
        result = QuestEngine.complete_quest(session_id, quest_id, data=data)
        
        if isinstance(result, tuple):
            print(f"DEBUG: QuestEngine returned error tuple: {result}")
            return jsonify(result[0]), result[1]
            
        if not result.get('success'):
            print(f"DEBUG: quest_complete success=False: {result}")
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: quest_complete exception: {e}")
        return jsonify({"error": str(e)}), 500

@quest_bp.route('/api/user/profile', methods=['GET'])
def get_profile():
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
        
    try:
        # Re-use logic or fetch direct
        data = QuestEngine.get_weekly_quests(session_id)
        return jsonify(data['profile'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
