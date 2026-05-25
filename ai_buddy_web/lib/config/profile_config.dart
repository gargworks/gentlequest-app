import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Centralized config for participant profiles and avatar assets.
/// Update names/images here to change across the app.
///
/// Hydration: [hydrateFromPrefs] reads the profile_*_v1 keys persisted by
/// `profile_screen.dart` and assigns them to the static fields so chat /
/// avatar / message-bubble surfaces pick up the user's choice without
/// every reader doing its own SharedPreferences read. Call once at app
/// start (see main.dart) and from profile_screen on every save.
class ProfileConfig {
  ProfileConfig._();

  // ── SharedPreferences keys (mirror profile_screen.dart) ─────────────────
  static const String _kProfileNickname = 'profile_nickname_v1';
  static const String _kProfilePronoun = 'profile_pronoun_v1';
  static const String _kProfileAvatar = 'profile_avatar_v1';
  static const String _kProfileTone = 'profile_tone_v1';
  static const String _kProfileGreetingStyle = 'profile_greeting_style_v1';

  // ── AI assistant ────────────────────────────────────────────────────────
  static String aiName = 'Alex';
  static String? aiAvatarAsset = 'assets/images/avatar_alex.png';

  // ── Current user ────────────────────────────────────────────────────────
  /// Display name. Defaults to 'You' (sentinel) when no nickname is set.
  /// Chat greeting paths skip personalisation when the value equals 'You'.
  static String userName = 'You';
  static String? userAvatarAsset;

  /// Pronoun text for prompt injection (e.g. "she/her", "they/them").
  /// Empty string = no preference set — prompt path omits the directive.
  static String userPronoun = '';

  /// Tone preference — one of {'warm', 'direct', 'quiet'}. Default 'warm'.
  /// Consumed by the chat system-prompt builder to shape AI response style.
  static String userTone = 'warm';

  /// Greeting style — one of {'casual','formal','minimal'}. Default 'casual'.
  /// Shapes the first-message opener delivered by the chat surface.
  static String userGreetingStyle = 'casual';

  // ── Mappings — keep in sync with profile_screen.dart UI lists ───────────
  /// Pronoun choices rendered in AboutYouCard. Index -1 = unselected.
  static const List<String> pronouns = ['she/her', 'he/him', 'they/them'];

  /// Tone choices in VoiceCard. Lowercased for prompt injection.
  static const List<String> tones = ['warm', 'direct', 'quiet'];

  /// Greeting-style choices. (display label, example) pairs are rendered
  /// in profile_screen.dart; this is the canonical lowercased enum.
  static const List<String> greetingStyles = ['casual', 'formal', 'minimal'];

  /// Avatar choices in AboutYouCard — gradient color pairs (no PNG assets
  /// exist for user avatars; the picker is gradient-based). The selected
  /// pair is rendered by StatusAvatar's gradient fallback. Default index
  /// 2 matches profile_screen.dart's `_avatarIndex = 2` fallback.
  /// Keep length + colors in sync with profile_screen.dart `_avatarGradients`.
  static const List<List<Color>> avatarGradients = [
    [Color(0xFFFFC4A3), Color(0xFFFF8E8E)],
    [Color(0xFFA8D8B9), Color(0xFF5FBA7D)],
    [Color(0xFF9DB4FF), Color(0xFF6F62D6)],
    [Color(0xFFF8C8DC), Color(0xFFD87FB0)],
    [Color(0xFFFFE3A3), Color(0xFFE5A85B)],
    [Color(0xFFC8E1E8), Color(0xFF7FB3C2)],
  ];

  /// Active gradient — assigned by [setAvatarIndex] from [avatarGradients].
  /// Consumed by StatusAvatar via the userAvatarGradient param so chat
  /// message bubbles + chat header reflect the user's choice.
  static List<Color>? userAvatarGradient;

  // ── Hydration + setters ─────────────────────────────────────────────────

  /// Load all persisted profile prefs into the static fields. Safe to call
  /// repeatedly — overwrites with whatever's on disk.
  static Future<void> hydrateFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final n = prefs.getString(_kProfileNickname);
    if (n != null && n.trim().isNotEmpty) {
      userName = n.trim();
    }
    final pIdx = prefs.getInt(_kProfilePronoun) ?? -1;
    userPronoun = (pIdx >= 0 && pIdx < pronouns.length) ? pronouns[pIdx] : '';
    final aIdx = prefs.getInt(_kProfileAvatar) ?? 2;
    if (aIdx >= 0 && aIdx < avatarGradients.length) {
      userAvatarGradient = avatarGradients[aIdx];
    }
    final tIdx = prefs.getInt(_kProfileTone) ?? 0;
    userTone = (tIdx >= 0 && tIdx < tones.length) ? tones[tIdx] : 'warm';
    final gIdx = prefs.getInt(_kProfileGreetingStyle) ?? 0;
    userGreetingStyle = (gIdx >= 0 && gIdx < greetingStyles.length)
        ? greetingStyles[gIdx]
        : 'casual';
  }

  /// Live-update the static when profile_screen persists a new nickname.
  /// Empty/whitespace input resets to the 'You' sentinel.
  static void setNickname(String value) {
    final trimmed = value.trim();
    userName = trimmed.isEmpty ? 'You' : trimmed;
  }

  /// Live-update pronoun by UI index. Out-of-range clears the value.
  static void setPronounIndex(int index) {
    userPronoun = (index >= 0 && index < pronouns.length) ? pronouns[index] : '';
  }

  /// Live-update avatar gradient by UI index. Out-of-range no-ops.
  static void setAvatarIndex(int index) {
    if (index >= 0 && index < avatarGradients.length) {
      userAvatarGradient = avatarGradients[index];
    }
  }

  /// Live-update tone by UI index. Out-of-range falls back to 'warm'.
  static void setToneIndex(int index) {
    userTone = (index >= 0 && index < tones.length) ? tones[index] : 'warm';
  }

  /// Live-update greeting style by UI index. Out-of-range → 'casual'.
  static void setGreetingStyleIndex(int index) {
    userGreetingStyle =
        (index >= 0 && index < greetingStyles.length) ? greetingStyles[index] : 'casual';
  }

  // ── Colors for status ───────────────────────────────────────────────────
  static const Color online = Color(0xFF22C55E);
  static const Color idle = Color(0xFFF59E0B);
  static const Color offline = Color(0xFF9CA3AF);
}

/// High-level presence for status badge.
enum PresenceStatus { online, idle, offline, none }

extension PresenceColor on PresenceStatus {
  Color color() {
    switch (this) {
      case PresenceStatus.online:
        return ProfileConfig.online;
      case PresenceStatus.idle:
        return ProfileConfig.idle;
      case PresenceStatus.offline:
        return ProfileConfig.offline;
      case PresenceStatus.none:
        return Colors.transparent;
    }
  }
}
