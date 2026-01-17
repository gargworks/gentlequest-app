"""
Quest Generator for GentleQuest
Generates weekly quests with progressive difficulty and variety
"""

from datetime import datetime, date
from typing import List, Tuple
import random
from models import db
from sqlalchemy import text


class QuestType:
    TASK = "task"
    TIP = "tip"
    CHECK_IN = "check_in"
    PROGRESS = "progress"


class QuestGenerator:
    """Generate weekly quests with progressive difficulty"""
    
    QUEST_TEMPLATES = {
        QuestType.TASK: [
            {'title': '3-Minute Breathing Exercise', 'description': 'Practice box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s. Repeat 5 times.', 'xp': 15, 'difficulty': 1},
            {'title': '5-4-3-2-1 Grounding', 'description': 'Name 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste.', 'xp': 20, 'difficulty': 2},
            {'title': 'Gratitude Journaling', 'description': 'Write down 3 things you\'re grateful for today.', 'xp': 25, 'difficulty': 2},
            {'title': 'Progressive Muscle Relaxation', 'description': 'Tense and release each muscle group for 10 seconds, head to toe.', 'xp': 30, 'difficulty': 3},
            {'title': '10-Minute Walk', 'description': 'Take a 10-minute walk outside. Notice your surroundings.', 'xp': 20, 'difficulty': 1},
            {'title': 'Mindful Eating', 'description': 'Eat one meal slowly, noticing taste, texture, and smell.', 'xp': 25, 'difficulty': 2},
            {'title': 'Loving-Kindness Meditation', 'description': 'Spend 5 minutes sending kind thoughts to yourself and others.', 'xp': 30, 'difficulty': 3},
        ],
        QuestType.TIP: [
            {'title': 'Learn About Sleep Hygiene', 'description': 'Read about creating a bedtime routine for better sleep.', 'xp': 10, 'difficulty': 1},
            {'title': 'Understand Cognitive Distortions', 'description': 'Learn to identify common thinking traps like catastrophizing.', 'xp': 15, 'difficulty': 2},
            {'title': 'Explore CBT Basics', 'description': 'Learn how thoughts, feelings, and behaviors are connected.', 'xp': 15, 'difficulty': 2},
            {'title': 'Stress Management Techniques', 'description': 'Discover evidence-based strategies for managing stress.', 'xp': 15, 'difficulty': 2},
        ],
        QuestType.CHECK_IN: [
            {'title': 'Daily Mood Check', 'description': 'Log your mood and add a brief note about your day.', 'xp': 10, 'difficulty': 1},
            {'title': 'Weekly Reflection', 'description': 'Reflect on your week: What went well? What was challenging?', 'xp': 20, 'difficulty': 2},
            {'title': 'Energy Level Check', 'description': 'Rate your energy level and note what affected it today.', 'xp': 10, 'difficulty': 1},
        ],
        QuestType.PROGRESS: [
            {'title': 'Complete PHQ-9 Assessment', 'description': 'Track your mental health progress with a quick 9-question assessment.', 'xp': 30, 'difficulty': 2},
            {'title': 'Complete GAD-7 Assessment', 'description': 'Measure your anxiety levels with a 7-question screening.', 'xp': 30, 'difficulty': 2},
        ]
    }
    
    @staticmethod
    def get_week_number() -> Tuple[int, int]:
        """Get current ISO week number and year"""
        today = date.today()
        iso_calendar = today.isocalendar()
        return iso_calendar[1], iso_calendar[0]  # week, year
    
    @staticmethod
    def generate_weekly_quests(week: int = None, year: int = None) -> List[dict]:
        """
        Generate 5 quests for the week with progressive difficulty
        
        Returns list of quest dicts (not ORM objects to avoid session issues)
        """
        if week is None or year is None:
            week, year = QuestGenerator.get_week_number()
        
        # Check if quests already exist for this week
        existing = db.session.execute(
            text("SELECT COUNT(*) FROM quests WHERE week_number = :week AND year = :year"),
            {"week": week, "year": year}
        ).scalar()
        
        if existing and existing > 0:
            # Return existing quests
            result = db.session.execute(
                text("""
                    SELECT id, title, description, quest_type, xp_reward, difficulty, week_number, year
                    FROM quests 
                    WHERE week_number = :week AND year = :year
                    ORDER BY id
                """),
                {"week": week, "year": year}
            ).fetchall()
            
            return [{
                'id': r[0],
                'title': r[1],
                'description': r[2],
                'type': r[3],
                'xp_reward': r[4],
                'difficulty': r[5],
                'week': r[6],
                'year': r[7]
            } for r in result]
        
        # Generate new quests
        quests_to_create = []
        
        # Progressive difficulty (increases every 4 weeks, max 3)
        base_difficulty = min((week % 52) // 4 + 1, 3)
        
        # 2 TASK quests
        task_templates = [t for t in QuestGenerator.QUEST_TEMPLATES[QuestType.TASK] 
                         if t['difficulty'] <= base_difficulty + 1]
        if len(task_templates) >= 2:
            selected_tasks = random.sample(task_templates, 2)
        else:
            selected_tasks = task_templates
        
        for template in selected_tasks:
            quests_to_create.append({
                'title': template['title'],
                'description': template['description'],
                'quest_type': QuestType.TASK,
                'xp_reward': template['xp'],
                'difficulty': template['difficulty'],
                'week_number': week,
                'year': year
            })
        
        # 1 TIP quest
        tip_template = random.choice(QuestGenerator.QUEST_TEMPLATES[QuestType.TIP])
        quests_to_create.append({
            'title': tip_template['title'],
            'description': tip_template['description'],
            'quest_type': QuestType.TIP,
            'xp_reward': tip_template['xp'],
            'difficulty': tip_template['difficulty'],
            'week_number': week,
            'year': year
        })
        
        # 1 CHECK_IN quest
        checkin_template = random.choice(QuestGenerator.QUEST_TEMPLATES[QuestType.CHECK_IN])
        quests_to_create.append({
            'title': checkin_template['title'],
            'description': checkin_template['description'],
            'quest_type': QuestType.CHECK_IN,
            'xp_reward': checkin_template['xp'],
            'difficulty': checkin_template['difficulty'],
            'week_number': week,
            'year': year
        })
        
        # 1 PROGRESS quest (alternating PHQ-9/GAD-7)
        progress_idx = week % 2
        progress_template = QuestGenerator.QUEST_TEMPLATES[QuestType.PROGRESS][progress_idx]
        quests_to_create.append({
            'title': progress_template['title'],
            'description': progress_template['description'],
            'quest_type': QuestType.PROGRESS,
            'xp_reward': progress_template['xp'],
            'difficulty': progress_template['difficulty'],
            'week_number': week,
            'year': year
        })
        
        # Insert all quests
        created_quests = []
        for quest_data in quests_to_create:
            result = db.session.execute(
                text("""
                    INSERT INTO quests (title, description, quest_type, xp_reward, difficulty, week_number, year)
                    VALUES (:title, :description, :quest_type, :xp_reward, :difficulty, :week_number, :year)
                    RETURNING id, title, description, quest_type, xp_reward, difficulty, week_number, year
                """),
                quest_data
            ).fetchone()
            
            created_quests.append({
                'id': result[0],
                'title': result[1],
                'description': result[2],
                'type': result[3],
                'xp_reward': result[4],
                'difficulty': result[5],
                'week': result[6],
                'year': result[7]
            })
        
        db.session.commit()
        return created_quests
