"""Crisis detection with comprehensive keyword coverage"""
import re

# Keywords must be lowercase for matching against message.lower()
SUICIDE_KEYWORDS = [
    "kill myself", "suicide", "end my life", "want to die", "better off dead",
    "don't want to live", "take my own life", "thinking about suicide",
    "suicidal thoughts", "suicidal ideation", "end it all", "take me from this earth",
    "permanent solution", "won't be here much longer", "saying goodbye",
    "writing goodbye letters", "getting affairs in order", "getting my affairs in order",
    "can't go on anymore", "nothing matters", "everyone would be better without me",
    # 2026-05-21 audit additions — soft + inflected forms the original list
    # missed. Test 7 ("want it all to stop") + Test 8 ("thinking about
    # ending my life") both bypassed crisis routing in prod prior to this.
    "ending my life", "ending it", "want it all to stop", "want everything to stop",
    "make it stop", "don't want to be here", "tired of living", "can't do this anymore",
    "no point anymore", "no point in living", "no reason to live", "ready to be done",
    "wish i wasn't here", "want to disappear", "want to vanish",
    "thinking of ending", "thinking of dying", "thoughts of dying",
]

SELF_HARM_KEYWORDS = [
    "cutting myself", "burning myself", "hurting myself", "hurt myself", "self-harm", "self-injury",
    "cutting my arms", "cutting my wrists", "scratching until i bleed",
    "need to feel something", "deserve the pain", "punishing myself",
    "seeing blood helps", "scars on my arms", "hiding my cuts",
    # Past-tense + inflection coverage — original list required gerund
    # ("cutting"); a user saying "I cut myself last night" slipped through.
    "cut myself", "cut my arm", "cut my wrist", "burned myself",
    "hurting me", "hurt me on purpose", "self harm", "selfharm",
]

# Acute somatic panic — frequently signals an in-progress panic attack
# that needs grounding, not a generic breathing offer. Routed to "high"
# (not "crisis") since the user isn't necessarily in danger but does
# need an empathetic, present-tense response.
SOMATIC_PANIC_KEYWORDS = [
    "can't breathe", "cant breathe", "heart palpitations", "heart racing",
    "chest tight", "chest is tight", "hyperventilating", "hyperventilate",
    "feel like i'm dying", "feel like im dying", "panic attack",
    "having a panic attack",
]

HARM_OTHERS_KEYWORDS = [
    "hurt someone", "kill someone", "shoot up", "planning to shoot", "going to shoot", 
    "harm my roommate", "hurt my roommate",
    "violent thoughts", "want to hurt people", "planning to hurt",
    "going to kill", "everyone deserves to suffer", "they need to pay",
    "revenge fantasies", "imagining hurting", "violent dreams", "anger out of control"
]

def detect_crisis_level(message):
    """
    Analyze message for crisis indicators and return risk level.
    Returns risk level string: 'low', 'medium', 'high', 'crisis'
    """
    message_lower = message.lower()
    
    # Check suicide keywords
    if any(keyword in message_lower for keyword in SUICIDE_KEYWORDS):
        return "crisis"
    
    # Check harm to others (also crisis level)
    if any(keyword in message_lower for keyword in HARM_OTHERS_KEYWORDS):
        return "crisis"
    
    # Check self-harm keywords
    if any(keyword in message_lower for keyword in SELF_HARM_KEYWORDS):
        return "high"

    # Acute somatic-panic signals — route to "high" so the chat layer
    # surfaces grounding resources + an empathetic acknowledgment of
    # the body symptom rather than a canned breathing one-liner.
    if any(keyword in message_lower for keyword in SOMATIC_PANIC_KEYWORDS):
        return "high"

    # Existing medium/high detection patterns
    if any(word in message_lower for word in ["hopeless", "worthless", "can't go on", "give up"]):
        return "high"
    
    if any(word in message_lower for word in ["sad", "depressed", "anxious", "stressed", "overwhelmed", "lonely"]):
        return "medium"
    
    return "low"
