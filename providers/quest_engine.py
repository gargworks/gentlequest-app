from datetime import datetime
from sqlalchemy import extract
from models import db, Quest, QuestProgress, UserProfile

class QuestEngine:
    @staticmethod
    def get_weekly_quests(session_id):
        """Get quests for the current week/context."""
        from providers.quest_generator import QuestGenerator
        
        # 1. Ensure UserProfile exists
        profile = UserProfile.query.filter_by(session_id=session_id).first()
        if not profile:
            profile = UserProfile(session_id=session_id)
            db.session.add(profile)
            db.session.commit()

        # 2. Ensure Quests exist for this week
        week, year = QuestGenerator.get_week_number()
        try:
            # This will create them if missing, or return existing
            quests_data = QuestGenerator.generate_weekly_quests(week, year)
        except Exception as e:
            # FALLBACK logic for production resilience
            print(f"Quest Generation Failed: {e}. Using hardcoded resilience set.")
            quests_data = [
                {
                    'id': 999, 
                    'title': 'One Tiny Step', 
                    'description': 'Log your energy level for today. Just one click.', 
                    'xp_reward': 15, 
                    'type': 'check_in', 
                    'difficulty': 'easy',
                    'target': 1,
                    'status': 'available'
                },
                {
                    'id': 998, 
                    'title': 'Box Breathing', 
                    'description': '4 seconds in, 4 hold, 4 out, 4 hold. Repeat twice.', 
                    'xp_reward': 25, 
                    'type': 'mindfulness', 
                    'difficulty': 'medium',
                    'target': 1,
                    'status': 'available'
                },
                {
                    'id': 997, 
                    'title': 'CBT Basics', 
                    'description': 'Learn about thoughts, feelings, and behaviors.', 
                    'xp_reward': 10, 
                    'type': 'tip', 
                    'difficulty': 'easy',
                    'target': 1,
                    'status': 'available'
                },
                {
                    'id': 996, 
                    'title': 'Nature Walk', 
                    'description': 'Take a 10-minute walk outside.', 
                    'xp_reward': 25, 
                    'type': 'activity', 
                    'difficulty': 'medium',
                    'target': 1,
                    'status': 'available'
                }
            ]
        
        # 2.5 Ensure Quests exist in DB (Sync)
        # This is critical for the 'complete_quest' endpoint to work, as it relies on DB existence.
        try:
            for q_data in quests_data:
                q = Quest.query.get(q_data['id'])
                if not q:
                    # Map string difficulty to likely int logic or default
                    diff_val = 1
                    diff_str = str(q_data.get('difficulty', 'easy')).lower()
                    if diff_str == 'medium': diff_val = 2
                    if diff_str == 'hard': diff_val = 3
                    
                    new_quest = Quest(
                        id=q_data['id'],
                        title=q_data['title'],
                        description=q_data['description'],
                        quest_type=q_data.get('type', 'task'),
                        xp_reward=q_data.get('xp_reward', 10),
                        difficulty=diff_val,
                        target=q_data.get('target', 1),
                        week_number=week,
                        year=year,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_quest)
            db.session.commit()
        except Exception as e:
            print(f"Quest Sync Failed: {e}")
        
        # 3. Build status map and batch-query progress
        quest_ids = [q['id'] for q in quests_data]
        all_progress = QuestProgress.query.filter(
            QuestProgress.session_id == session_id,
            QuestProgress.quest_id.in_(quest_ids)
        ).all()
        
        progress_map = {p.quest_id: p for p in all_progress}
        
        results = []
        for q_data in quests_data:
            quest_id = q_data['id']
            progress = progress_map.get(quest_id)
            
            status = progress.status if progress else "available"
            
            results.append({
                "id": quest_id,
                "title": q_data['title'],
                "description": q_data['description'],
                "xp_reward": q_data['xp_reward'],
                "status": status,
                "type": q_data['type'],
                "difficulty": q_data['difficulty'],
                "target": q_data.get('target', 1),
                "progress": progress.progress if progress and hasattr(progress, 'progress') else 0
            })
            
        return {
            "quests": results, 
            "week": week,
            "year": year,
            "profile": {
                "level": profile.level,
                "xp": profile.xp,
                "streak_days": profile.streak_days
            }
        }

    @staticmethod
    def complete_quest(session_id, quest_id, data=None):
        if data is None:
            data = {}
        try:
            # Verify Quest Exists
            quest = Quest.query.get(quest_id)
            if not quest:
                return {"success": False, "message": "Quest not found"}, 404

            # Ensure Profile Exists
            profile = UserProfile.query.filter_by(session_id=session_id).first()
            if not profile:
                 profile = UserProfile(session_id=session_id, xp=0, level=1, streak_days=0)
                 db.session.add(profile)

            progress = QuestProgress.query.filter_by(
                session_id=session_id, quest_id=quest_id
            ).first()
            
            if not progress:
                progress = QuestProgress(
                    session_id=session_id, quest_id=quest_id, status="available"
                )
                db.session.add(progress)
                
            # Determine requested state
            target_progress = data.get('progress', 100)
            is_undo = target_progress == 0
            
            if progress.status == "completed" and not is_undo:
                return {
                    "success": True, 
                    "message": "Already completed",
                    "xp_earned": 0,
                    "new_total_xp": profile.xp,
                    "leveled_up": False,
                    "new_level": profile.level,
                    "new_badges": []
                }
                
            # Update Progress
            if is_undo:
                if progress.status == "completed":
                    profile.xp = max(0, profile.xp - quest.xp_reward)
                progress.status = "available"
                progress.progress = 0
            else:
                progress.status = "completed"
                progress.progress = target_progress
                progress.completed_at = datetime.utcnow()
                profile.xp += quest.xp_reward
            
            # Simple Leveling: Level = 1 + XP // 100
            new_level = 1 + (profile.xp // 100)
            leveled_up = new_level > profile.level
            profile.level = new_level
            
            # Streak logic (Simplified: check last_activity)
            if not is_undo:
                if profile.last_activity_date:
                    delta = datetime.utcnow().date() - profile.last_activity_date.date()
                    if delta.days == 1:
                        profile.streak_days += 1
                    elif delta.days > 1:
                        profile.streak_days = 1
                else:
                    profile.streak_days = 1
                profile.last_activity_date = datetime.utcnow()
            
            db.session.commit()
            
            # Badges
            new_badges = []
            if profile.streak_days == 7 and "streak_7" not in (profile.badges or ""):
                if profile.badges:
                    profile.badges += ",streak_7"
                else:
                    profile.badges = "streak_7"
                new_badges.append({"id": "streak_7"})
                db.session.commit()
            
            return {
                "success": True, 
                "xp_earned": quest.xp_reward, 
                "new_total_xp": profile.xp,
                "leveled_up": leveled_up,
                "new_level": profile.level,
                "new_badges": new_badges
            }
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    @staticmethod
    def complete_quest_for_assessment(session_id, assessment_type):
        """
        Auto-complete a quest related to a specific assessment type (e.g. PHQ-9).
        Finds active 'progress' quest with matching title keywords.
        """
        from models import Quest, QuestProgress
        
        # 1. Map assessment type to keywords
        keywords = []
        if assessment_type == 'phq9':
            keywords = ['PHQ-9', 'Depression']
        elif assessment_type == 'gad7':
            keywords = ['GAD-7', 'Anxiety']
        
        if not keywords:
            print(f"No keywords mapped for assessment: {assessment_type}")
            return
            
        try:
            # 2. Find active quests for this session
            # We look for quests of type 'progress' that match keywords
            # We join with QuestProgress to prioritize 'in_progress' or 'available'
            
            # Simplified approach: Get all weekly quests, filter in python for safety/speed
            weekly_data = QuestEngine.get_weekly_quests(session_id)
            quests_list = weekly_data.get('quests', [])
            
            target_quest_id = None
            
            for q in quests_list:
                if q['type'] == 'progress' and q['status'] != 'completed':
                    # Check title match
                    title = q['title'].lower()
                    if any(k.lower() in title for k in keywords):
                        target_quest_id = q['id']
                        break
            
            if target_quest_id:
                print(f"Auto-completing Quest {target_quest_id} for assessment {assessment_type}")
                QuestEngine.complete_quest(session_id, target_quest_id, data={'progress': 1})
            else:
                print(f"No matching active quest found for assessment {assessment_type}")
                
        except Exception as e:
            print(f"Error in auto-complete quest: {e}")
