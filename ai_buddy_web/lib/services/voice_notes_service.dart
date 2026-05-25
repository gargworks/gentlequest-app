// voice_notes_service.dart — TTS playback for AI replies.
//
// Wired to the Profile "Voice notes" toggle (profile_voice_notes_v1). When
// the toggle is ON, [maybeSpeak] is invoked on every AI reply rendered by
// the chat surface — it strips markdown, caps the length, and asks the
// platform TTS engine (AVSpeechSynthesizer on iOS, TextToSpeech on
// Android) to read it aloud. No network, no recording — fully on-device.
//
// Audit reference: .brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md §7.

import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:shared_preferences/shared_preferences.dart';

class VoiceNotesService {
  VoiceNotesService._();
  static final VoiceNotesService _instance = VoiceNotesService._();
  static VoiceNotesService get instance => _instance;

  static const String _kPrefVoiceNotes = 'profile_voice_notes_v1';

  /// Hard cap so we never lock up the engine on a runaway reply. Most AI
  /// replies in this app target 2–4 sentences, well under this limit.
  static const int _maxChars = 600;

  FlutterTts? _tts;
  bool _initialized = false;
  Future<void>? _initFuture;

  /// Idempotent lazy init. Safe to call from any number of callers.
  Future<void> _ensureInit() {
    return _initFuture ??= _init();
  }

  Future<void> _init() async {
    try {
      final tts = FlutterTts();
      await tts.setLanguage('en-US');
      await tts.setSpeechRate(0.48); // slower than default for warmth
      await tts.setVolume(1.0);
      await tts.setPitch(1.0);
      _tts = tts;
      _initialized = true;
    } catch (e) {
      debugPrint('VoiceNotesService: init failed — $e');
      _initialized = false;
    }
  }

  /// Read [text] aloud only if the user has the Profile voice-notes
  /// toggle ON. Caller doesn't need to gate; this method short-circuits
  /// when the pref is false / missing.
  Future<void> maybeSpeak(String text) async {
    final cleaned = _clean(text);
    if (cleaned.isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    if (!(prefs.getBool(_kPrefVoiceNotes) ?? false)) return;
    await _ensureInit();
    if (!_initialized || _tts == null) return;
    try {
      // Stop any in-flight utterance so a fast back-and-forth doesn't
      // pile up overlapping replies.
      await _tts!.stop();
      await _tts!.speak(cleaned);
    } catch (e) {
      debugPrint('VoiceNotesService: speak failed — $e');
    }
  }

  /// Stop any pending utterance. Called when the chat is dismissed or
  /// the user navigates away mid-reply.
  Future<void> stop() async {
    if (_tts == null) return;
    try {
      await _tts!.stop();
    } catch (_) {}
  }

  String _clean(String input) {
    // Strip basic markdown so the engine doesn't say "asterisk-asterisk".
    var s = input.trim();
    if (s.isEmpty) return s;
    s = s.replaceAll(RegExp(r'```[\s\S]*?```'), ''); // fenced code
    s = s.replaceAll(RegExp(r'`([^`]*)`'), r'$1'); // inline code
    s = s.replaceAll(RegExp(r'\*\*([^*]+)\*\*'), r'$1');
    s = s.replaceAll(RegExp(r'__([^_]+)__'), r'$1');
    s = s.replaceAll(RegExp(r'\*([^*]+)\*'), r'$1');
    s = s.replaceAll(RegExp(r'_([^_]+)_'), r'$1');
    s = s.replaceAll(RegExp(r'\[([^\]]+)\]\([^)]+\)'), r'$1'); // [text](url)
    s = s.replaceAll(RegExp(r'\s{2,}'), ' ');
    if (s.length > _maxChars) {
      s = '${s.substring(0, _maxChars)}…';
    }
    return s.trim();
  }
}
