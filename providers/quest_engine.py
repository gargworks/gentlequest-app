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
        # This will create them if missing, or return existing
        quests_data = QuestGenerator.generate_weekly_quests(week, year)
        
        results = []
        
        # 3. Build status map
        # Convert dicts to objects or iterate dicts
        for q_data in quests_data:
            quest_id = q_data['id']
            progress = QuestProgress.query.filter_by(
                session_id=session_id, quest_id=quest_id
            ).first()
            
            status = progress.status if progress else "available"
            
            # Auto-create availability if missing? 
            # Ideally we lazily create QuestProgress only on start/complete, 
            # but UI needs to know status. "available" is default.
            
            results.append({
                "id": quest_id,
                "title": q_data['title'],
                "description": q_data['description'],
                "xp_reward": q_data['xp_reward'],
                "status": status,
                "type": q_data['type'],
                "difficulty": q_data['difficulty']
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
    def complete_quest(session_id, quest_id):
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
                
            if progress.status == "completed":
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
            progress.status = "completed"
            progress.completed_at = datetime.utcnow()
            
            # Update Profile (already fetched)
            
            profile.xp += quest.xp_reward
            
            # Simple Leveling: Level = 1 + XP // 100
            new_level = 1 + (profile.xp // 100)
            leveled_up = new_level > profile.level
            profile.level = new_level
            
            # Streak logic (Simplified: check last_activity)
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
