"""
Crisis detection, response, logging, and geography-specific resources.
Extracted from app.py monolith.
"""

import functools
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests
from flask import current_app

from models import db, CrisisEvent
from providers.alert_manager import AlertManager


# ── Geography-specific crisis resources ─────────────────────────────

CRISIS_RESOURCES_BY_COUNTRY = {
    "in": {  # India
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call iCall Helpline at 022-25521111 or AASRA at 91-22-27546669. You can also text HOME to 741741 to reach Crisis Text Line. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "iCall Helpline", "number": "022-25521111", "available": "24/7"},
            {"name": "AASRA", "number": "91-22-27546669", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
        ],
    },
    "us": {  # United States
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call the National Suicide Prevention Lifeline at 988 or text HOME to 741741 to reach the Crisis Text Line. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "National Suicide Prevention Lifeline",
                "number": "988",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "uk": {  # United Kingdom
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call Samaritans at 116 123 or text SHOUT to 85258. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "Samaritans", "number": "116 123", "available": "24/7"},
            {"name": "SHOUT Text Line", "text": "SHOUT to 85258", "available": "24/7"},
            {"name": "Emergency Services", "number": "999", "available": "24/7"},
        ],
    },
    "ca": {  # Canada
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call the National Suicide Prevention Service at 1-833-456-4566 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "National Suicide Prevention Service",
                "number": "1-833-456-4566",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "au": {  # Australia
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call Lifeline at 13 11 14 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "Lifeline", "number": "13 11 14", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "000", "available": "24/7"},
        ],
    },
    "de": {  # Germany
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call TelefonSeelsorge at 0800 111 0 111 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {
                "name": "TelefonSeelsorge",
                "number": "0800 111 0 111",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "112", "available": "24/7"},
        ],
    },
    "fr": {  # France
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call SOS Amitié at 09 72 39 40 50 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "SOS Amitié", "number": "09 72 39 40 50", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "112", "available": "24/7"},
        ],
    },
    "jp": {  # Japan
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call TELL Lifeline at 03-5774-0992 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "TELL Lifeline", "number": "03-5774-0992", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "119", "available": "24/7"},
        ],
    },
    "br": {  # Brazil
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call CVV at 188 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "CVV", "number": "188", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "192", "available": "24/7"},
        ],
    },
    "mx": {  # Mexico
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please call SAPTEL at 55-5259-8121 or text HOME to 741741. You're not alone, and help is available 24/7.",
        "crisis_numbers": [
            {"name": "SAPTEL", "number": "55-5259-8121", "available": "24/7"},
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {"name": "Emergency Services", "number": "911", "available": "24/7"},
        ],
    },
    "generic": {  # Fallback for unsupported countries
        "crisis_msg": "I'm very concerned about what you're sharing. This is a crisis situation and you need immediate help. Please reach out to Befrienders Worldwide or call your local emergency services. You can also text HOME to 741741 for international crisis support. You're not alone, and help is available.",
        "crisis_numbers": [
            {
                "name": "Befrienders Worldwide",
                "url": "https://www.befrienders.org/",
                "available": "24/7",
            },
            {"name": "Crisis Text Line", "text": "HOME to 741741", "available": "24/7"},
            {
                "name": "Emergency Services",
                "note": "Call your local emergency number",
                "available": "24/7",
            },
        ],
    },
}


# ── IP → Country helpers ────────────────────────────────────────────

@functools.lru_cache(maxsize=1024)
def get_country_code_from_ip(ip: str) -> str:
    """Get country code from IP address using ipinfo.io (cached per IP)."""
    try:
        # Skip local/private IPs
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith(
            ("10.", "172.", "192.168.")
        ):
            return "generic"

        # Validate IP format before external call (SSRF prevention)
        import ipaddress as _ipaddress
        try:
            _ipaddress.ip_address(ip)
        except ValueError:
            return "generic"

        # Use ipinfo.io for geolocation
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get("country", "").lower()
            return (
                country_code
                if country_code in CRISIS_RESOURCES_BY_COUNTRY
                else "generic"
            )
        else:
            return "generic"
    except Exception as e:
        print(f"IP geolocation error: {e}")
        return "generic"


def get_country_from_request(req) -> str:
    """Get country from request - either from country parameter or IP"""
    # Check for explicit country override
    data = req.get_json() if req.is_json else {}
    country = data.get("country", "").lower()

    if country and country in CRISIS_RESOURCES_BY_COUNTRY:
        return country

    # Get IP from various headers
    ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not ip:
        ip = req.headers.get("X-Real-IP", "")
    if not ip:
        ip = req.remote_addr

    return get_country_code_from_ip(ip)


# ── Crisis detection ────────────────────────────────────────────────

def _enhanced_crisis_detection(message: str) -> Tuple[str, float, List[str]]:
    """Enhanced crisis detection with keyword analysis"""
    message_lower = message.lower()

    # Crisis keywords with weights
    crisis_keywords = {
        "suicide": 1.0,
        "kill myself": 1.0,
        "want to die": 1.0,
        "end it all": 1.0,
        "take me from this earth": 1.0,
        "take me from earth": 1.0,
        "remove me from earth": 1.0,
        "self harm": 0.9,
        "cut myself": 0.9,
        "hurt myself": 0.9,
        "hopeless": 0.8,
        "no hope": 0.8,
        "worthless": 0.8,
        "useless": 0.8,
        "depressed": 0.7,
        "depression": 0.7,
        "anxiety": 0.6,
        "panic": 0.6,
        "lonely": 0.5,
        "alone": 0.5,
        "isolated": 0.5,
        "stress": 0.4,
        "overwhelmed": 0.4,
        "can't cope": 0.4,
    }

    found_keywords = []
    total_score = 0.0

    for keyword, weight in crisis_keywords.items():
        if keyword in message_lower:
            found_keywords.append(keyword)
            total_score += weight

    # Normalize score
    max_possible_score = sum(crisis_keywords.values())
    normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0

    # Determine risk level
    if normalized_score >= 0.8:
        risk_level = "crisis"
    elif normalized_score >= 0.6:
        risk_level = "high"
    elif normalized_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return risk_level, normalized_score, found_keywords


# ── Crisis response & resources ─────────────────────────────────────

def get_crisis_response_and_resources(
    risk_level: str, country: str = "generic"
) -> Dict[str, Any]:
    """Get geography-specific crisis response and resources"""
    if risk_level == "crisis":
        # Get country-specific crisis resources
        country_resources = CRISIS_RESOURCES_BY_COUNTRY.get(
            country, CRISIS_RESOURCES_BY_COUNTRY["generic"]
        )
        return {
            "crisis_msg": country_resources["crisis_msg"],
            "crisis_numbers": country_resources["crisis_numbers"],
            "risk_level": risk_level,
        }
    else:
        # For non-crisis levels, return standard responses
        responses = {
            "high": "I'm worried about what you're experiencing. These feelings are serious and you deserve support. Please consider reaching out to a mental health professional or calling your local crisis helpline. You don't have to face this alone.",
            "medium": "I can see you're going through a difficult time. It's important to take these feelings seriously. Consider talking to someone you trust or reaching out to a mental health professional. You're showing strength by sharing this.",
            "low": "Thank you for sharing how you're feeling. It's normal to have difficult moments, and it's okay to not be okay. Consider reaching out to friends, family, or a mental health professional for support.",
        }
        return {
            "crisis_msg": responses.get(risk_level, responses["low"]),
            "crisis_numbers": [],
            "risk_level": risk_level,
        }


def _get_crisis_response(risk_level: str, risk_score: float) -> str:
    """Get appropriate crisis response based on risk level (legacy function)"""
    if risk_level == "crisis":
        return CRISIS_RESOURCES_BY_COUNTRY["generic"]["crisis_msg"]
    else:
        responses = {
            "high": "I'm worried about what you're experiencing. These feelings are serious and you deserve support. Please consider reaching out to a mental health professional or calling your local crisis helpline. You don't have to face this alone.",
            "medium": "I can see you're going through a difficult time. It's important to take these feelings seriously. Consider talking to someone you trust or reaching out to a mental health professional. You're showing strength by sharing this.",
            "low": "Thank you for sharing how you're feeling. It's normal to have difficult moments, and it's okay to not be okay. Consider reaching out to friends, family, or a mental health professional for support.",
        }
        return responses.get(risk_level, responses["low"])


def _get_crisis_resources(risk_level: str) -> Dict[str, Any]:
    """Get crisis resources based on risk level"""
    resources = {
        "crisis": {
            "immediate": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "number": "988",
                    "available": "24/7",
                },
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                },
                {"name": "Emergency Services", "number": "911", "available": "24/7"},
            ],
            "online": [
                {"name": "Crisis Chat", "url": "https://www.crisischat.org/"},
                {"name": "IMAlive", "url": "https://www.imalive.org/"},
            ],
        },
        "high": {
            "immediate": [
                {
                    "name": "National Suicide Prevention Lifeline",
                    "number": "988",
                    "available": "24/7",
                },
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                },
            ],
            "online": [
                {
                    "name": "Find a Therapist",
                    "url": "https://www.psychologytoday.com/us/therapists",
                },
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
            ],
        },
        "medium": {
            "immediate": [
                {
                    "name": "Crisis Text Line",
                    "text": "HOME to 741741",
                    "available": "24/7",
                }
            ],
            "online": [
                {
                    "name": "Find a Therapist",
                    "url": "https://www.psychologytoday.com/us/therapists",
                },
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
            ],
        },
        "low": {
            "immediate": [],
            "online": [
                {"name": "Mental Health Resources", "url": "https://www.nami.org/help"},
                {
                    "name": "Self-Care Tips",
                    "url": "https://www.mind.org.uk/information-support/tips-for-everyday-living/",
                },
            ],
        },
    }
    return resources.get(risk_level, resources["low"])


# ── Crisis watchdog (background LLM analysis) ──────────────────────

def _run_crisis_watchdog(flask_app, message: str, session_id: str, sync_risk: str):
    """
    Background worker: Uses an LLM to analyze the message for subtle crisis signs.
    If the LLM detects a higher risk than the synchronous keyword check, updates the record.
    """
    with flask_app.app_context():
        try:
            # 1. Skip if message is too short or already handled at 'crisis' level
            if len(message) < 5 or sync_risk == "crisis":
                return
            
            # 2. Call LLM for clinical analysis
            system_prompt = (
                "You are a clinical crisis detection specialist. Analyze student messages for subtle signs of crisis "
                "(hopelessness, finality, self-harm intention) that keyword matching might miss."
            )
            
            prompt = (
                f"Analyze this message: \"{message}\".\n"
                f"Respond ONLY with a valid JSON object: {{\"risk_level\": \"low\"|\"medium\"|\"high\"|\"crisis\", \"reason\": \"string\"}}"
            )
            
            from app import _call_llm_json
            response_text = _call_llm_json(prompt, system_prompt)
            
            # Clean up response (LLMs sometimes wrap JSON in code blocks)
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(cleaned_json)
                llm_risk = result.get("risk_level", "low").lower()
            except (json.JSONDecodeError, AttributeError):
                flask_app.logger.warning(f"⚠️ Crisis Watchdog failed to parse JSON from provider: {response_text[:100]}")
                return
                
            # 3. Only escalate if the LLM thinks it's high/crisis and sync check missed it
            risk_hierarchy = {"low": 0, "medium": 1, "high": 2, "crisis": 3}
            if risk_hierarchy.get(llm_risk, 0) > risk_hierarchy.get(sync_risk, 0):
                new_event = CrisisEvent(
                    session_id=session_id,
                    message=message,
                    risk_level=llm_risk,
                    risk_score=1.0 if llm_risk == "crisis" else 0.5,
                    keywords="LLM_WATCHDOG_DETECTION",
                    intervention_taken="Escalated to CAPS Dashboard",
                    escalated=True
                )
                db.session.add(new_event)
                db.session.commit()
                flask_app.logger.info(f"🛡️ Crisis Watchdog escalated risk: {sync_risk} -> {llm_risk} for session {session_id}")
        except Exception as e:
            flask_app.logger.error(f"❌ Crisis Watchdog error: {e}")


# ── Crisis logging ──────────────────────────────────────────────────

def _log_crisis_detection(
    session_id: str,
    message: str,
    risk_level: str,
    risk_score: float,
    keywords: List[str],
) -> None:
    """Log crisis detection for monitoring"""
    try:
        event = CrisisEvent(
            session_id=session_id,
            message=message,
            risk_level=risk_level,
            risk_score=risk_score,
            keywords=",".join(keywords),
            timestamp=datetime.utcnow()
        )
        db.session.add(event)
        db.session.commit()
        
        # Trigger Counselor Alert
        # AlertManager handles severity determination and rate limiting
        alert_id = AlertManager.create_alert(
            session_id=session_id,
            trigger_message=message,
            risk_level=risk_level,
            risk_score=risk_score,
            keywords=keywords
        )
        if alert_id:
            from flask import current_app as _app
            _app.logger.info(f"Counselor Alert created: ID {alert_id}")
    except Exception as e:
        try:
            from flask import current_app as _app
            _app.logger.error(f"Failed to log crisis detection: {e}")
        except RuntimeError:
            pass  # Outside request context — safe to skip logging
        db.session.rollback()
