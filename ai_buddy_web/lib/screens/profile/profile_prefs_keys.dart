// SharedPreferences key constants for the Profile screen family
// (centralised so reads + writes stay in sync).
//
// `kSafetyPlanFilled` is written by SafetyPlanBuilderStep (final step) and
// read by the profile home view to flip the safety-plan card state.

const String kProfileNickname = 'profile_nickname_v1';
const String kProfilePronoun = 'profile_pronoun_v1';
const String kProfileAvatar = 'profile_avatar_v1';
const String kProfileTone = 'profile_tone_v1';
const String kProfileVoiceNotes = 'profile_voice_notes_v1';
const String kSafetyPlanFilled = 'safety_plan_filled_v1';
