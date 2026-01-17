"""
Seed initial quests for current week
Run with: python scripts/seed_quests.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from providers.quest_generator import QuestGenerator

def main():
    app = create_app()
    
    with app.app_context():
        # Generate quests for current week
        week, year = QuestGenerator.get_week_number()
        quests = QuestGenerator.generate_weekly_quests(week, year)
        
        print(f"✅ Generated {len(quests)} quests for Week {week}, {year}")
        print()
        
        for quest in quests:
            print(f"  • {quest['title']}")
            print(f"    Type: {quest['type']}, XP: {quest['xp_reward']}, Difficulty: {quest['difficulty']}")
            print()

if __name__ == '__main__':
    main()
