// SharedPreferences key constants for the Profile screen family
// (centralised so reads + writes stay in sync).
//
// `kSafetyPlanFilled` is written by SafetyPlanBuilderStep only on full
// completion (final step). It is NOT sufficient on its own to tell whether
// a plan exists — WO-6.4: per-field content persists on every step
// regardless of completion, so a 3-of-5 plan has real content with this
// flag still false. See `kSafetyPlanFieldKeys` and _loadSafetyPlanState()
// in crisis_resources.dart, which derives state from content first and
// treats this flag only as the empty/partial vs filled distinction.

const String kProfileNickname = 'profile_nickname_v1';
const String kProfilePronoun = 'profile_pronoun_v1';
const String kProfileAvatar = 'profile_avatar_v1';
const String kProfileTone = 'profile_tone_v1';
const String kProfileVoiceNotes = 'profile_voice_notes_v1';
const String kSafetyPlanFilled = 'safety_plan_filled_v1';

/// Every per-field SafetyPlanBuilderStep prefs key, in the same order the
/// builder's 5 steps write them. Mirrors the literal keys already inlined
/// in safety_plan_builder.dart and safety_plan_recall_sheet.dart — kept
/// here too because _loadSafetyPlanState() is the first consumer that
/// needs the full set at once (to answer "is there any content at all"),
/// rather than one field at a time.
const List<String> kSafetyPlanFieldKeys = [
  'safety_plan_step0_warning_0_v1',
  'safety_plan_step0_warning_1_v1',
  'safety_plan_step0_warning_2_v1',
  'safety_plan_step1_coping_0_v1',
  'safety_plan_step1_coping_1_v1',
  'safety_plan_step1_coping_2_v1',
  'safety_plan_step2_contact_1_name_v1',
  'safety_plan_step2_contact_1_rel_v1',
  'safety_plan_step2_contact_1_phone_v1',
  'safety_plan_step2_contact_2_name_v1',
  'safety_plan_step2_contact_2_rel_v1',
  'safety_plan_step2_contact_2_phone_v1',
  'safety_plan_step3_place_0_v1',
  'safety_plan_step3_place_1_v1',
  'safety_plan_step3_place_2_v1',
  'safety_plan_step4_meaning_v1',
];
