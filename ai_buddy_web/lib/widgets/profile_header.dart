import 'package:flutter/material.dart';

class ProfileHeader extends StatelessWidget {
  // level, xp, nextLevelXp, streakDays kept in constructor for backwards compat
  // with call-sites that pass them; none are rendered (principle #14).
  final int level;
  final int xp;
  final int nextLevelXp;
  final int streakDays;

  const ProfileHeader({
    super.key,
    required this.level,
    required this.xp,
    required this.streakDays,
    this.nextLevelXp = 100,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.purple.shade700, Colors.deepPurple.shade900],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: const Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: Colors.white24,
            child: Icon(Icons.person, color: Colors.white, size: 28),
          ),
          SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Your Journey",
                style: TextStyle(color: Colors.white70, fontSize: 14),
              ),
              Text(
                "Today's Quests",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
