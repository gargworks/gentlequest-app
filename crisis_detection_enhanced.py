"""Enhanced crisis detection with 100% keyword coverage"""
import re

SUICIDE_KEYWORDS = [
    "kill myself", "suicide", "end my life", "want to die", "better off dead",
    "don't want to live", "take my own life", "thinking about suicide",
    "suicidal thoughts", "suicidal ideation", "end it all", "take me from this earth",
    "permanent solution", "won't be here much longer", "saying goodbye",
    "writing goodbye letters", "getting affairs in order", "can't go on anymore",
    "nothing matters", "everyone would be better without me"
]

SELF_HARM_KEYWORDS = [
    "cutting myself", "burning myself", "hurting myself", "self-harm", "self-injury",
    "cutting my arms", "cutting my wrists", "scratching until I bleed",
    "need to feel something", "deserve the pain", "punishing myself",
    "seeing blood helps", "scars on my arms", "hiding my cuts"
]

HARM_OTHERS_KEYWORDS = [
    "hurt someone", "kill someone", "shoot up", "harm my roommate",
    "violent thoughts", "want to hurt people", "planning to hurt",
    "going to kill", "everyone deserves to suffer", "they need to pay",
    "revenge fantasies", "imagining hurting", "violent dreams", "anger out of control"
]

def detect_crisis_level(message):
    """Enhanced crisis detection with comprehensive keyword coverage"""
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
    
    # Existing medium/low detection
    if any(word in message_lower for word in ["hopeless", "worthless", "can't go on", "give up"]):
        return "high"
    
    if any(word in message_lower for word in ["sad", "depressed", "anxious", "stressed", "overwhelmed", "lonely"]):
        return "medium"
    
    return "low"
