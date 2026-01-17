# University Customization Templates
## White-Label Branding & University-Specific Configuration

## Customization Levels

### Level 1: Basic (All Universities, Free)
- University name in emails/reports
- CAPS contact info (crisis alerts)
- University-specific crisis resources (campus hotline, CAPS hours)

### Level 2: Standard (Paid Contracts, Included)
- Custom welcome message (CAPS director message to students)
- University logo in app (header, splash screen)
- Custom crisis resources (campus-specific hotlines, support groups)

### Level 3: Premium (Large Universities, +$5K/year)
- Full white-label branding (colors, logo, name)
- Custom domain (gentlequest.university.edu)
- SSO integration (university login system)
- LMS integration (Canvas, Blackboard)

## Configuration Templates

### University Profile (Database)

```sql
CREATE TABLE universities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    domain VARCHAR(100),  -- university.edu
    caps_email VARCHAR(255),
    caps_phone VARCHAR(50),
    caps_hours VARCHAR(200),  -- "Mon-Fri 9am-5pm"
    waitlist_weeks INTEGER,
    enrollment INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Branding (Level 2+)
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),  -- #667EEA
    secondary_color VARCHAR(7),
    welcome_message TEXT,
    
    -- Integration (Level 3)
    sso_enabled BOOLEAN DEFAULT FALSE,
    sso_provider VARCHAR(50),  -- 'saml', 'oauth', 'cas'
    sso_config JSONB,
    lms_integration VARCHAR(50),  -- 'canvas', 'blackboard', 'moodle'
    custom_domain VARCHAR(100)
);
```

### Crisis Resources (University-Specific)

```sql
-- Add university-specific crisis resources
INSERT INTO resources (title, description, url, category, university_id)
VALUES 
    ('UMich CAPS Crisis Line', '24/7 crisis support', 'tel:+1734555000', 'crisis', 2),
    ('UMich Counseling Center', 'Schedule appointment', 'https://caps.umich.edu', 'university', 2),
    ('UMich Wellness Resources', 'Campus wellness programs', 'https://wellness.umich.edu', 'university', 2);
```

### Welcome Message (CAPS Director to Students)

```
Hi! I'm Dr. [DIRECTOR NAME], Director of Counseling Services at [UNIVERSITY].

You're on our CAPS waitlist (currently [X] weeks), and I want you to know we 
haven't forgotten about you. While you wait for your appointment, we're offering 
GentleQuest - a 24/7 AI support tool designed specifically for students like you.

Think of Luna (the AI) as a supportive friend who's always available. She uses 
evidence-based techniques to help you manage stress, anxiety, and difficult emotions.

A few things to know:
• Your conversations are private (I don't see what you say to Luna)
• If Luna detects a crisis, she'll notify me so I can follow up
• This is support WHILE you wait, not instead of your CAPS appointment
• It's completely free and anonymous

I hope Luna helps. Your appointment is still scheduled for [DATE]. See you then.

- Dr. [DIRECTOR NAME]
```

### Branding Configuration (Level 2)

```json
{
  "university_id": 2,
  "name": "University of Michigan",
  "branding": {
    "logo_url": "https://brand.umich.edu/logo.png",
    "primary_color": "#00274C",  // Michigan Blue
    "secondary_color": "#FFCB05",  // Maize
    "welcome_message": "[CUSTOM MESSAGE FROM DIRECTOR]",
    "app_name": "UMich Mental Health Support"  // Optional white-label
  },
  "crisis_resources": [
    {
      "name": "UMich CAPS Crisis Line",
      "phone": "+1734555000",
      "available": "24/7"
    },
    {
      "name": "UMich Counseling Center",
      "url": "https://caps.umich.edu",
      "hours": "Mon-Fri 9am-5pm"
    }
  ]
}
```

### SSO Integration (Level 3)

```python
# SAML SSO configuration
SSO_CONFIG = {
    "provider": "saml",
    "entity_id": "https://gentlequest.com/saml/umich",
    "sso_url": "https://shibboleth.umich.edu/idp/profile/SAML2/Redirect/SSO",
    "x509_cert": "[UNIVERSITY CERTIFICATE]",
    "attribute_mapping": {
        "email": "urn:oid:0.9.2342.19200300.100.1.3",
        "first_name": "urn:oid:2.5.4.42",
        "last_name": "urn:oid:2.5.4.4"
    }
}

# OAuth 2.0 configuration
OAUTH_CONFIG = {
    "provider": "oauth",
    "client_id": "[UNIVERSITY CLIENT ID]",
    "client_secret": "[UNIVERSITY SECRET]",
    "authorization_url": "https://oauth.university.edu/authorize",
    "token_url": "https://oauth.university.edu/token",
    "userinfo_url": "https://oauth.university.edu/userinfo"
}
```

### LMS Integration (Level 3)

```python
# Canvas LTI 1.3 integration
CANVAS_CONFIG = {
    "client_id": "[CANVAS CLIENT ID]",
    "deployment_id": "[DEPLOYMENT ID]",
    "public_jwk_url": "https://canvas.university.edu/api/lti/security/jwks",
    "auth_login_url": "https://canvas.university.edu/api/lti/authorize_redirect",
    "auth_token_url": "https://canvas.university.edu/login/oauth2/token",
    "launch_url": "https://gentlequest.com/lti/launch"
}

# Deep linking (add GentleQuest to Canvas course)
DEEP_LINK_CONFIG = {
    "title": "GentleQuest Mental Health Support",
    "description": "24/7 AI support for mental health and wellness",
    "icon_url": "https://gentlequest.com/icon.png",
    "launch_url": "https://gentlequest.com/lti/launch"
}
```

## Customization Workflow

### For Each New University

**Step 1: Create University Record (5 min)**
```sql
INSERT INTO universities (name, domain, caps_email, caps_phone, waitlist_weeks, enrollment)
VALUES ('University of Michigan', 'umich.edu', 'caps@umich.edu', '+1734555000', 8, 45000);
```

**Step 2: Add Counselor Contacts (5 min)**
```sql
INSERT INTO university_counselors (university_id, name, email, phone, role, alert_methods)
VALUES 
    (2, 'Dr. Jane Smith', 'jsmith@umich.edu', '+1734555001', 'Director', 'email,sms'),
    (2, 'Dr. John Doe', 'jdoe@umich.edu', NULL, 'Crisis Counselor', 'email');
```

**Step 3: Add University Resources (10 min)**
```sql
INSERT INTO resources (title, description, url, category, university_id)
VALUES 
    ('UMich CAPS', 'Schedule appointment', 'https://caps.umich.edu', 'university', 2),
    ('UMich Crisis Line', '24/7 support', 'tel:+1734555000', 'crisis', 2),
    ('UMich Wellness', 'Campus wellness programs', 'https://wellness.umich.edu', 'university', 2);
```

**Step 4: Configure Branding (Level 2, 15 min)**
```sql
UPDATE universities 
SET logo_url = 'https://brand.umich.edu/logo.png',
    primary_color = '#00274C',
    secondary_color = '#FFCB05',
    welcome_message = '[CUSTOM MESSAGE FROM DIRECTOR]'
WHERE id = 2;
```

**Step 5: Test Configuration (10 min)**
- Sign up as student (verify university resources shown)
- Trigger crisis keyword (verify alert sent to correct counselor)
- Check branding (logo, colors displayed correctly)

**Total Customization Time: 45 minutes per university**

## Customization Pricing

**Level 1 (Basic):** Included free
**Level 2 (Standard):** Included in paid contract
**Level 3 (Premium):** +$5K/year (SSO, LMS, custom domain)

**Setup Fees:**
- Level 1: $0
- Level 2: $0 (included)
- Level 3: $2K one-time (SSO/LMS integration development)

## White-Label Options

### Option A: Co-Branded (Standard)
- "Powered by GentleQuest" footer
- GentleQuest logo + University logo
- gentlequest.com/[university] URL

### Option B: White-Label (Premium, +$10K/year)
- No GentleQuest branding
- University logo only
- Custom domain (support.university.edu)
- Custom app name ("UMich Mental Health Support")

**When to Offer White-Label:**
- Large universities (>30K students, $50K+ contracts)
- Universities with strong brand identity
- Strategic partnerships (research collaboration, advisory board)

---

## Customization Examples

### Small Liberal Arts College
- **Level:** 1 (Basic)
- **Customization:** University name, CAPS contact, campus hotline
- **Branding:** Standard GentleQuest
- **Reason:** Budget-conscious, standard offering sufficient

### Medium State University
- **Level:** 2 (Standard)
- **Customization:** Logo, colors, welcome message, campus resources
- **Branding:** Co-branded (GentleQuest + University)
- **Reason:** Wants some customization, not full white-label

### Large R1 Research University
- **Level:** 3 (Premium)
- **Customization:** Full white-label, SSO, LMS integration, custom domain
- **Branding:** University-only (no GentleQuest branding)
- **Reason:** Large budget, strong brand, wants full control

**Customization templates complete. 3 levels: Basic (free, university name/contact), Standard (included, logo/colors/welcome), Premium (+$5K/year, SSO/LMS/custom domain). White-label: Co-branded (standard) vs. full white-label (+$10K/year, no GentleQuest branding). Configuration: University profile (database), crisis resources (university-specific), welcome message (CAPS director), branding (logo/colors), SSO (SAML/OAuth), LMS (Canvas/Blackboard). Workflow: 45 min per university (create record, add counselors, add resources, configure branding, test). Pricing: Level 1 $0, Level 2 $0 (included), Level 3 +$5K/year + $2K setup. Examples: Small (Level 1), medium (Level 2), large R1 (Level 3 white-label).**
