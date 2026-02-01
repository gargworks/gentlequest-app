# OpenGraph Image Optimization - A/B Testing TODO

**Date Created:** February 2, 2026  
**Status:** ✅ Current version working (nucleus-social-v2.jpg)  
**Priority:** Test these optimizations once we have 1000+ monthly visitors

---

## Current Performance Baseline

### What's Working ✅
- Brain logo displays correctly on all platforms (Facebook, LinkedIn, Twitter/X, WhatsApp, Discord)
- Professional, memorable, on-brand design
- 80KB image size (optimal for fast loading)
- Image aspect ratio: 1200x630 (perfect for OG standards)

### Current Metrics to Track
- **OG Title:** "Nucleus OS - The Sovereign Agent Control Plane" (46 chars)
- **OG Description:** "The Recursive Aggregator that turns MCP servers into a unified, secure operating system for autonomous agents."
- **Image:** `/public/nucleus-social-v2.jpg` (brain logo, black background)

---

## Optimization #1: Title Length (Quick Win)

**Issue:** Title is 46 characters. Optimal: 50-60 characters  
**Impact:** Low effort, 5-10% potential CTR improvement  
**Priority:** ⭐⭐⭐ (Do this first)

### Variants to Test:

```html
<!-- Current (46 chars) -->
<meta property="og:title" content="Nucleus OS - The Sovereign Agent Control Plane">

<!-- Option A (59 chars) - Most descriptive -->
<meta property="og:title" content="Nucleus OS - The Recursive Aggregator for Autonomous Agents">

<!-- Option B (54 chars) - Action-oriented -->
<meta property="og:title" content="Nucleus OS - Turn MCP Servers into an AI Control Plane">

<!-- Option C (48 chars) - User benefit focused -->
<meta property="og:title" content="Nucleus OS - Build & Control Sovereign AI Agents">

<!-- Option D (50 chars) - Product category -->
<meta property="og:title" content="Nucleus OS - The Operating System for AI Agents">
```

### A/B Test Plan:
1. Implement Option A as default
2. Track click-through rates for 2 weeks
3. Test Options B, C, D in rotation
4. Pick winner based on CTR + conversion rate

---

## Optimization #2: Image with Bigger Headline

**Issue:** "Missing a clear headline in your image"  
**Impact:** 15-25% potential CTR improvement  
**Priority:** ⭐⭐ (Test after getting 1000+ monthly visitors)

### Design Variations:

#### Variant A: Headline Above Logo
```
┌─────────────────────────────────────┐
│                                     │
│    "Your AI. Your Rules."          │  ← Big, bold (72px)
│                                     │
│         [Brain Logo]                │  ← Existing logo
│                                     │
│  Nucleus OS - The Sovereign Agent   │  ← Smaller subtitle
│      Control Plane                  │
└─────────────────────────────────────┘
```

#### Variant B: Split Layout (Text + Logo)
```
┌─────────────────────────────────────┐
│  Take Control of                    │
│  Your AI Agents        [Brain Logo] │
│                                     │
│  Open Source • Self-Hosted          │
│  MCP-Native                         │
└─────────────────────────────────────┘
```

#### Variant C: Minimal + Bold Statement
```
┌─────────────────────────────────────┐
│                                     │
│  "The Operating System              │
│   for Autonomous Agents"            │
│                                     │
│         [Brain Logo]                │
│      NUCLEUSOS.DEV                  │
└─────────────────────────────────────┘
```

### Implementation:
- Create `nucleus-social-v3.jpg`, `v4.jpg`, `v5.jpg` for each variant
- Use Figma/Canva or hire designer on Fiverr ($15-30)
- Dimensions: 1200x630px
- File size: Keep under 100KB

---

## Optimization #3: Call-to-Action in Image

**Issue:** "Missing a call-to-action in your image"  
**Impact:** 20-35% potential conversion improvement  
**Priority:** ⭐⭐⭐ (High value, test alongside headline)

### CTA Button Options:

#### Style Guidelines:
- **Size:** 180-220px wide, 50-60px tall
- **Color:** High contrast (orange/green on dark background)
- **Position:** Bottom-right or centered below logo
- **Font:** Bold, 18-22px

#### CTA Text Variants:
1. **"Get Started Free"** ← Best for SaaS
2. **"Try Nucleus Now"**
3. **"Join the Waitlist"** ← If still pre-launch
4. **"Explore Now"**
5. **"Download Free"** ← If open source focused
6. **"See How It Works"**

### Design Example:
```
┌─────────────────────────────────────┐
│         [Brain Logo]                │
│                                     │
│  Nucleus OS - The Sovereign Agent   │
│      Control Plane                  │
│                                     │
│      ┌─────────────────┐           │
│      │ Get Started Free │           │  ← Bright orange/green
│      └─────────────────┘           │
└─────────────────────────────────────┘
```

---

## Optimization #4: Dynamic OG Images (Advanced)

**Tool:** Use a service like [OpenGraph.xyz](https://opengraph.xyz) or [Cloudinary](https://cloudinary.com)  
**Priority:** ⭐ (Nice-to-have, test after validating static variants)

### Benefits:
- Auto-generate images for blog posts with custom titles
- Personalized images for different traffic sources
- Real-time A/B testing with UTM parameters

### Implementation:
```html
<!-- Example with dynamic title -->
<meta property="og:image" content="https://opengraph.xyz/api/generate?
  title=Nucleus%20OS
  &template=brain-logo
  &cta=Get%20Started%20Free">
```

---

## A/B Testing Strategy

### Phase 1: Title Optimization (Month 1)
- Baseline: Current 46-char title
- Test 4 variants (50-60 chars each)
- Track: CTR from social shares, referral traffic
- **Success Metric:** 10%+ CTR improvement

### Phase 2: Image with Headline (Month 2-3)
- Create 3 image variants with different headlines
- Rotate weekly via Cloudflare Workers or CDN
- Track: CTR + time on site
- **Success Metric:** 15%+ CTR improvement

### Phase 3: CTA Buttons (Month 4)
- Test 5 different CTA styles on winning image from Phase 2
- Track: CTR + signup/download conversions
- **Success Metric:** 20%+ conversion improvement

### Phase 4: Combined Winner (Month 5)
- Deploy best-performing title + image + CTA combo
- Monitor for 30 days
- Document final metrics

---

## Measurement & Tools

### Analytics to Set Up:
1. **Google Analytics 4**
   - Track social referral traffic
   - Set up custom events for "og_image_click"

2. **UTM Parameters**
   - Add to shared links: `?utm_source=facebook&utm_medium=social&utm_campaign=og_test_v2`

3. **Social Media Platform Analytics**
   - Facebook Insights
   - Twitter/X Analytics
   - LinkedIn Analytics

4. **A/B Testing Tools:**
   - [Cloudflare Workers](https://workers.cloudflare.com) - Serve different OG images based on user
   - [Google Optimize](https://optimize.google.com) - Free A/B testing
   - [VWO](https://vwo.com) - Advanced visual testing

---

## Quick Reference: File Naming Convention

```
nucleus-social-v2.jpg          ← Current (brain logo only)
nucleus-social-v3-headline.jpg ← Test: Big headline variant
nucleus-social-v4-cta.jpg      ← Test: CTA button variant
nucleus-social-v5-split.jpg    ← Test: Split layout
nucleus-social-v6-minimal.jpg  ← Test: Minimal design
nucleus-social-WINNER.jpg      ← Final production version
```

---

## Cost Estimates

### Design Work:
- **Fiverr Designer:** $15-30 per variant (5 variants = $75-150)
- **Canva Pro:** $12.99/month (DIY option)
- **AI Image Tools:** Free (Midjourney/DALL-E for concepts)

### Testing Tools:
- **Google Analytics 4:** Free
- **Cloudflare Workers:** Free tier (100k requests/day)
- **Domain Analytics:** Included in Cloudflare

**Total Budget:** $100-200 for complete A/B testing campaign

---

## Next Steps (When Ready to Test)

1. ✅ Save this document
2. ⏸️ Wait until 1000+ monthly visitors (need statistically significant data)
3. 📊 Set up analytics tracking
4. 🎨 Design image variants (hire on Fiverr or use Canva)
5. 🧪 Implement Phase 1 (title optimization)
6. 📈 Monitor results weekly
7. 🚀 Deploy winning combination

---

**Note:** Current OG setup is production-ready and working perfectly. These optimizations are for incremental improvements once we have traffic to validate changes.

**Estimated Time to ROI:** 3-4 months after starting A/B tests  
**Expected Overall Improvement:** 30-50% better CTR + conversion rates
