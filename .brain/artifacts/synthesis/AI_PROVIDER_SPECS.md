# AI PROVIDER SPECS - GentleQuest 2026
## Provider-Specific Details, Limits, and Configuration

**Purpose:** Complete reference for AI provider integration  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. PROVIDER HIERARCHY

```
Request Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GEMINI    │ ──▶ │   OPENAI    │ ──▶ │  PERPLEXITY │
│  (Primary)  │     │ (Fallback 1)│     │ (Fallback 2)│
└─────────────┘     └─────────────┘     └─────────────┘
     ↓ fail              ↓ fail              ↓ fail
                                        Return Error
```

**Selection Logic:**
```python
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')

for provider in [gemini, openai, perplexity]:
    try:
        return provider.generate(message)
    except Exception as e:
        log_warning(f"[AI_FALLBACK] {provider} failed: {e}")
        continue
raise Exception("All AI providers failed")
```

---

## 2. GOOGLE GEMINI (Primary)

### Configuration
| Setting | Value |
|---------|-------|
| Model | `gemini-1.5-flash` (or `gemini-pro`) |
| Env Var | `GEMINI_API_KEY` |
| Multiple Keys | `GEMINI_API_KEYS` (comma-separated) |
| File | `providers/gemini_provider.py` |

### Rate Limits (Free Tier)
| Metric | Limit |
|--------|-------|
| RPM | 60 requests/minute |
| TPM | 1,000,000 tokens/minute |
| RPD | 1,500 requests/day |

### Token Limits
| Model | Input | Output |
|-------|-------|--------|
| gemini-1.5-flash | 1M tokens | 8K tokens |
| gemini-pro | 30K tokens | 2K tokens |

### Implementation
```python
# providers/gemini_provider.py
import google.generativeai as genai

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_response(self, message, context=None):
        chat = self.model.start_chat(history=context or [])
        response = chat.send_message(message)
        return response.text
    
    def stream_response(self, message, context=None):
        chat = self.model.start_chat(history=context or [])
        response = chat.send_message(message, stream=True)
        for chunk in response:
            yield chunk.text
```

### System Prompt
```python
SYSTEM_PROMPT = """You are a compassionate mental health companion...
[Full prompt in providers/gemini_provider.py]
"""
```

### Key Rotation
```python
# If using multiple keys
keys = os.getenv('GEMINI_API_KEYS', '').split(',')
current_key_index = 0

def get_next_key():
    global current_key_index
    key = keys[current_key_index]
    current_key_index = (current_key_index + 1) % len(keys)
    return key
```

### Error Codes
| Error | Meaning | Action |
|-------|---------|--------|
| 429 | Rate limit | Switch key or wait |
| 400 | Bad request | Check prompt format |
| 500 | Server error | Retry or fallback |

---

## 3. OPENAI (Fallback 1)

### Configuration
| Setting | Value |
|---------|-------|
| Model | `gpt-4o-mini` or `gpt-3.5-turbo` |
| Env Var | `OPENAI_API_KEY` |
| File | `providers/openai_provider.py` |

### Rate Limits (Pay-as-you-go)
| Tier | RPM | TPM |
|------|-----|-----|
| Free | 3 | 40,000 |
| Tier 1 | 500 | 200,000 |
| Tier 2+ | Higher | Higher |

### Token Limits
| Model | Context | Output |
|-------|---------|--------|
| gpt-4o-mini | 128K | 16K |
| gpt-3.5-turbo | 16K | 4K |

### Implementation
```python
# providers/openai_provider.py
from openai import OpenAI

class OpenAIProvider:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def generate_response(self, message, context=None):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    
    def stream_response(self, message, context=None):
        # Similar with stream=True
        pass
```

### Pricing (as of 2026)
| Model | Input | Output |
|-------|-------|--------|
| gpt-4o-mini | $0.15/1M | $0.60/1M |
| gpt-3.5-turbo | $0.50/1M | $1.50/1M |

---

## 4. PERPLEXITY (Fallback 2)

### Configuration
| Setting | Value |
|---------|-------|
| Model | `llama-3.1-sonar-small-128k-online` |
| Env Var | `PPLX_API_KEY` |
| File | `providers/perplexity_provider.py` |

### Rate Limits
| Metric | Limit |
|--------|-------|
| RPM | Varies by plan |

### Implementation
```python
# providers/perplexity_provider.py
import requests

class PerplexityProvider:
    def __init__(self):
        self.api_key = os.getenv('PPLX_API_KEY')
        self.base_url = "https://api.perplexity.ai"
    
    def generate_response(self, message, context=None):
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]
            }
        )
        return response.json()['choices'][0]['message']['content']
```

### Notes
- Has internet access (can cite sources)
- Good for factual queries
- Slower than Gemini/OpenAI

---

## 5. STREAMING CONFIGURATION

### Backend (Flask)
```python
def stream_chat_response(message, session_id):
    def generate():
        provider = get_active_provider()
        for token in provider.stream_response(message):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
```

### Frontend (Flutter Web)
```dart
// streaming_sse_web.dart
final eventSource = html.EventSource(url);
eventSource.onMessage.listen((event) {
    final data = jsonDecode(event.data);
    if (data['type'] == 'token') {
        onToken(data['content']);
    } else if (data['type'] == 'done') {
        onComplete();
    }
});
```

### Feature Flag
```dart
// config/feature_flags.dart
class FeatureFlags {
    static const bool enableStreaming = true;
    static const String streamingTransport = 'sse';
}
```

---

## 6. PROMPT ENGINEERING

### System Prompt Structure
```
1. Role definition (compassionate companion)
2. Behavioral guidelines (non-judgmental, supportive)
3. Safety rules (crisis detection, boundaries)
4. Response format (conversational, not clinical)
5. Limitations (not a replacement for professional help)
```

### Context Window Management
```python
MAX_CONTEXT_MESSAGES = 20

def prepare_context(history):
    # Keep system prompt + last N messages
    if len(history) > MAX_CONTEXT_MESSAGES:
        return history[-MAX_CONTEXT_MESSAGES:]
    return history
```

### Token Estimation
```python
def estimate_tokens(text):
    # Rough estimate: 4 chars per token
    return len(text) // 4

def check_context_fit(context, max_tokens=30000):
    total = sum(estimate_tokens(m['content']) for m in context)
    return total < max_tokens
```

---

## 7. COST OPTIMIZATION

### Strategies
1. **Gemini first** - Free tier is generous
2. **Key rotation** - Distribute load across keys
3. **Response caching** - Cache common responses (careful with context)
4. **Shorter prompts** - Minimize system prompt tokens
5. **Model selection** - Use smaller models for simple queries

### Cost Tracking
```python
# Log provider usage for cost analysis
def log_ai_usage(provider, tokens_in, tokens_out):
    # Store in database or monitoring system
    pass
```

### Estimated Monthly Costs
| Usage Level | Gemini | OpenAI Fallback | Total |
|-------------|--------|-----------------|-------|
| 1K users | $0 | ~$5 | ~$5 |
| 10K users | $0 | ~$50 | ~$50 |
| 100K users | $0-50 | ~$500 | ~$500 |

---

## 8. MONITORING

### Metrics to Track
- Provider selection distribution
- Fallback trigger rate
- Response latency by provider
- Error rate by provider
- Token usage

### Alerting
```python
# Alert if fallback rate exceeds threshold
if fallback_rate > 0.20:  # 20%
    alert("High AI fallback rate")
```

---

## 9. TROUBLESHOOTING

### "AI not responding"
1. Check provider status pages
2. Verify API key validity
3. Check rate limit status
4. Review error logs
5. Test fallback chain

### "Responses are slow"
1. Check if using fallback (slower)
2. Verify streaming is enabled
3. Check network latency
4. Consider response caching

### "Responses are poor quality"
1. Review system prompt
2. Check context window (too short/long?)
3. Verify model selection
4. Test with different providers

---

## 10. PROVIDER STATUS PAGES

| Provider | Status URL |
|----------|------------|
| Gemini | https://status.cloud.google.com/ |
| OpenAI | https://status.openai.com/ |
| Perplexity | https://status.perplexity.ai/ |

---

## QUICK REFERENCE

| Need | Solution |
|------|----------|
| Change primary provider | Set `AI_PROVIDER` env var |
| Add new API key | Update `GEMINI_API_KEY` in dashboard |
| Rotate keys | Update key, deploy, verify, revoke old |
| Check usage | Provider dashboards |
| Debug response | Check logs for `[AI_FALLBACK]` |
