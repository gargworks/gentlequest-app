# EXTENSION GUIDE - GentleQuest 2026
## How to Add Features Without Re-Exploration

**Purpose:** Step-by-step patterns for extending the codebase  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. ADD A NEW API ENDPOINT

### Step 1: Define the route in app.py
```python
# app.py - Add near similar routes

@app.route('/api/newfeature', methods=['POST'])
@limiter.limit("60 per minute")
def new_feature():
    data = request.get_json()
    session_id = data.get('session_id')
    
    # Validate
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    
    # Business logic
    result = process_new_feature(data)
    
    return jsonify(result), 200
```

### Step 2: Add Flutter service method
```dart
// ai_buddy_web/lib/services/api_service.dart

Future<Map<String, dynamic>> newFeature(Map<String, dynamic> data) async {
  final response = await _dio.post('/api/newfeature', data: {
    ...data,
    'session_id': SessionManager.sessionId,
  });
  return response.data;
}
```

### Step 3: Add provider method (if stateful)
```dart
// ai_buddy_web/lib/providers/new_feature_provider.dart

class NewFeatureProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  Future<void> doNewFeature() async {
    final result = await _api.newFeature({});
    // Update state
    notifyListeners();
  }
}
```

### Step 4: Register provider in main.dart
```dart
// ai_buddy_web/lib/main.dart

MultiProvider(
  providers: [
    // ... existing providers
    ChangeNotifierProvider(create: (_) => NewFeatureProvider()),
  ],
)
```

---

## 2. ADD A NEW SCREEN/PAGE

### Step 1: Create screen file
```dart
// ai_buddy_web/lib/screens/new_screen/new_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class NewScreen extends StatefulWidget {
  const NewScreen({super.key});

  @override
  State<NewScreen> createState() => _NewScreenState();
}

class _NewScreenState extends State<NewScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New Feature')),
      body: // Your UI here
    );
  }
}
```

### Step 2: Add route (if using named routes)
```dart
// In your router configuration or home_shell.dart

// Option A: Add as new tab in HomeShell
// Modify home_shell.dart _tabs list

// Option B: Add as pushable route
Navigator.push(
  context,
  MaterialPageRoute(builder: (_) => const NewScreen()),
);
```

### Step 3: Add navigation from existing UI
```dart
// In relevant screen, add button/link
ElevatedButton(
  onPressed: () => Navigator.push(
    context,
    MaterialPageRoute(builder: (_) => const NewScreen()),
  ),
  child: const Text('Go to New Feature'),
)
```

---

## 3. ADD A NEW QUEST TYPE

### Step 1: Define quest in backend catalog
```python
# app.py or dedicated quests.py

QUEST_CATALOG = {
    # ... existing quests
    "new-quest-type": {
        "id": "new-quest-type",
        "title": "New Quest Title",
        "description": "What this quest does",
        "category": "mindfulness",  # or activity, social, learning, challenge
        "xp_reward": 50,
        "steps": [
            {"title": "Step 1", "description": "Do this first"},
            {"title": "Step 2", "description": "Then this"},
        ],
        "duration_minutes": 10,
    }
}
```

### Step 2: Quest appears automatically
- GET /api/quest/catalog returns it
- Flutter QuestProvider fetches and displays
- No Flutter code changes needed if using existing quest UI

### Step 3: Add custom step handler (if needed)
```python
# If quest step has special logic

def handle_quest_step_completion(quest_id, step_index, data):
    if quest_id == "new-quest-type" and step_index == 1:
        # Custom validation or side effects
        pass
    return standard_step_completion(quest_id, step_index, data)
```

---

## 4. ADD A NEW AI PROVIDER (Fallback)

### Step 1: Create provider file
```python
# providers/new_provider.py

import os

class NewProvider:
    def __init__(self):
        self.api_key = os.getenv('NEW_PROVIDER_API_KEY')
    
    def generate_response(self, message: str, context: list = None) -> str:
        # Implement API call
        # Return response text
        pass
    
    def stream_response(self, message: str, context: list = None):
        # Implement streaming if supported
        # Yield tokens
        pass
```

### Step 2: Add to fallback chain in app.py
```python
# app.py

from providers.new_provider import NewProvider

AI_PROVIDERS = [
    ('gemini', GeminiProvider),
    ('openai', OpenAIProvider),
    ('new_provider', NewProvider),  # Add here
    ('perplexity', PerplexityProvider),
]

def get_ai_response(message, context):
    for name, ProviderClass in AI_PROVIDERS:
        try:
            provider = ProviderClass()
            return provider.generate_response(message, context)
        except Exception as e:
            log_warning(f"[AI_FALLBACK] {name} failed: {e}")
            continue
    raise Exception("All AI providers failed")
```

### Step 3: Add environment variable
```yaml
# render.yaml
- key: NEW_PROVIDER_API_KEY
  sync: false
```

---

## 5. ADD A NEW WIDGET

### Step 1: Create widget file
```dart
// ai_buddy_web/lib/widgets/new_widget.dart

import 'package:flutter/material.dart';

class NewWidget extends StatelessWidget {
  final String title;
  final VoidCallback? onTap;
  
  const NewWidget({
    super.key,
    required this.title,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.all(16.h),  // Using size_utils
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
            ),
          ],
        ),
        child: Text(title),
      ),
    );
  }
}
```

### Step 2: Use in screens
```dart
// In any screen
import 'package:ai_buddy_web/widgets/new_widget.dart';

NewWidget(
  title: 'My Widget',
  onTap: () => print('Tapped'),
)
```

---

## 6. ADD DATABASE TABLE/COLUMN

### Step 1: Define model (if using SQLAlchemy)
```python
# In models.py or app.py

class NewModel(db.Model):
    __tablename__ = 'new_table'
    
    id = db.Column(db.String(36), primary_key=True)
    session_id = db.Column(db.String(36), index=True)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Step 2: Create migration (or auto-create)
```python
# If using Flask-Migrate
flask db migrate -m "Add new_table"
flask db upgrade

# Or simple approach in app.py
with app.app_context():
    db.create_all()
```

### Step 3: Add CRUD operations
```python
# In app.py

@app.route('/api/newtable', methods=['POST'])
def create_new_record():
    data = request.get_json()
    record = NewModel(
        id=str(uuid.uuid4()),
        session_id=data['session_id'],
        data=data.get('data', {})
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"id": record.id}), 201
```

---

## 7. ADD ANALYTICS EVENT

### Step 1: Define event in Flutter
```dart
// ai_buddy_web/lib/services/analytics_service.dart

static Future<void> logNewFeatureEvent(Map<String, dynamic> params) async {
  await FirebaseAnalytics.instance.logEvent(
    name: 'new_feature_used',
    parameters: params,
  );
}
```

### Step 2: Call from relevant code
```dart
// When feature is used
AnalyticsService.logNewFeatureEvent({
  'feature_name': 'xyz',
  'user_action': 'completed',
});
```

---

## 8. ADD ENVIRONMENT VARIABLE

### Step 1: Add to render.yaml
```yaml
# render.yaml
envVars:
  - key: NEW_VAR_NAME
    sync: false  # If secret, set in dashboard
    # value: "default"  # If not secret
```

### Step 2: Use in Python
```python
import os
new_var = os.getenv('NEW_VAR_NAME', 'default_value')
```

### Step 3: Use in Flutter (if needed)
```dart
// Define in build: --dart-define=NEW_VAR=value
const newVar = String.fromEnvironment('NEW_VAR', defaultValue: 'default');
```

---

## EXTENSION CHECKLIST

When adding any feature, verify:

- [ ] Backend endpoint added (if needed)
- [ ] Rate limiting configured
- [ ] Error handling in place
- [ ] Flutter service method added
- [ ] Provider updated (if stateful)
- [ ] UI component created
- [ ] Navigation/routing configured
- [ ] Analytics event added
- [ ] Tests updated
- [ ] Documentation updated
- [ ] Environment variables documented

---

## FILE LOCATION QUICK REFERENCE

| What | Where |
|------|-------|
| Backend routes | `app.py` |
| AI providers | `providers/` |
| Flutter services | `ai_buddy_web/lib/services/` |
| Flutter providers | `ai_buddy_web/lib/providers/` |
| Flutter screens | `ai_buddy_web/lib/screens/` |
| Flutter widgets | `ai_buddy_web/lib/widgets/` |
| Flutter models | `ai_buddy_web/lib/models/` |
| Environment config | `render.yaml`, `.env` |
| Database models | `app.py` or `models.py` |
