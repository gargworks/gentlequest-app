import {
  Lock,
  PhoneCall,
  SkipForward,
  Sparkles,
  BookOpen,
  CalendarHeart,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
import { createElement, useState } from 'react';

const IOS_APP_URL = 'https://apps.apple.com/app/gentlequest/id6756537464';
const ANDROID_APP_URL = 'https://play.google.com/store/apps/details?id=app.gentlequest.www';
const WEB_APP_URL = 'https://app.gentlequest.app';
const NEWSLETTER_API = 'https://app.gentlequest.app/api/newsletter/subscribe';

function AppleGlyph() {
  return (
    <svg width="26" height="28" viewBox="0 0 24 28" fill="currentColor" aria-hidden="true">
      <path d="M16.7 14.8c0-2.6 2.1-3.9 2.2-3.9-1.2-1.7-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9-1.7 0-3.3 1-4.2 2.6-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.3 2.6 1.3 0 1.8-.8 3.4-.8s2 .8 3.4.8c1.4 0 2.3-1.2 3.2-2.5 1-1.4 1.4-2.9 1.4-2.9-.1 0-2.7-1-2.7-4.1zM14.3 6.1c.7-.8 1.2-2 1-3.1-1 0-2.2.6-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z" />
    </svg>
  );
}

function PlayGlyph() {
  return (
    <svg width="24" height="26" viewBox="0 0 24 26" aria-hidden="true">
      <path d="M3 2.5v21l16.5-10.5L3 2.5z" fill="var(--gq-primary)" />
    </svg>
  );
}

const FEATURES = [
  {
    Icon: Lock,
    title: 'Private by default',
    body: "Stays on your device. Never synced. Never shared by default. Export when you want. Delete when you're done.",
  },
  {
    Icon: PhoneCall,
    title: 'Crisis paths that never block',
    body: '988 always reachable — even when the app is in a compliance state. Even offline. Even mid-flow.',
  },
  {
    Icon: SkipForward,
    title: 'Skip anything, no shame',
    body: 'Every step has a skip. Every input is optional. Coming back is never penalized.',
  },
  {
    Icon: Sparkles,
    title: 'One-tap mood check-in',
    body: 'Open the app, tap once, done in 5 seconds. Low days gently offer a breathing exercise or someone to talk to. No pressure, no streaks.',
  },
  {
    Icon: BookOpen,
    title: 'Journal on phone',
    body: 'Local-first by default. Three views: today, an entry, the timeline. Yours.',
  },
  {
    Icon: CalendarHeart,
    title: 'Weekly review without scores',
    body: 'Sundays show mood shapes — not a diagnosis. One thing worth remembering.',
  },
];

function App() {
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [newsletterStatus, setNewsletterStatus] = useState(null);

  const handleNewsletterSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(NEWSLETTER_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newsletterEmail, source: 'landing' }),
      });
      if (response.ok) {
        setNewsletterStatus('success');
        setNewsletterEmail('');
        // Track conversion
        if (typeof window.gtag !== 'undefined') {
          window.gtag('event', 'newsletter_signup', {
            event_category: 'engagement',
            event_label: 'landing page newsletter'
          });
        }
      } else {
        setNewsletterStatus('error');
      }
    } catch (err) {
      setNewsletterStatus('error');
    }
  };

  return (
    <div>
      <header className="gq-topbar">
        <div className="gq-container row">
          <a className="gq-brand" href="/">
            <span className="gq-brand-mark" />
            <span>GentleQuest</span>
          </a>
          <nav className="gq-nav-links">
            <a href="#features">Features</a>
            <a href="#crisis">988</a>
            <a href="/blog/">Blog</a>
            <a href="/about">About</a>
            <a href={WEB_APP_URL}>Get the app</a>
            <a href={WEB_APP_URL}>Open app</a>
          </nav>
        </div>
      </header>

      <section className="gq-hero">
        <div className="gq-container inner">
          <h1>
            A quiet place,
            <br />
            <span className="accent">whenever you need it.</span>
          </h1>
          <p className="sub">
            GentleQuest is a wellness companion for heavy moments. Not therapy. Not medical care. A
            space to log how you're feeling and find resources that match where you are.
          </p>
          <div className="gq-hero-cta" id="download">
            <a
              className="gq-appstore-badge"
              href={IOS_APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Download on the App Store"
              onClick={() => { if (typeof window.gtag !== 'undefined') { window.gtag('event', 'ios_download_click', { event_category: 'app_download', event_label: 'hero iOS' }); } }}
            >
              <AppleGlyph />
              <div>
                <div className="gq-store-line1">Download on the</div>
                <div className="gq-store-line2">App&nbsp;Store</div>
              </div>
            </a>
            <a
              className="gq-androidstore-badge"
              href={ANDROID_APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Get it on Google Play"
              onClick={() => { if (typeof window.gtag !== 'undefined') { window.gtag('event', 'android_download_click', { event_category: 'app_download', event_label: 'hero Android' }); } }}
            >
              <PlayGlyph />
              <div>
                <div className="gq-store-line1">Get it on</div>
                <div className="gq-store-line2">Google&nbsp;Play</div>
              </div>
            </a>
            <a className="gq-web-cta" href={WEB_APP_URL}>
              <ExternalLink size={14} />
              <span>Or check in on the web — 5 seconds</span>
            </a>
          </div>
          <div className="gq-hero-meta" style={{ marginTop: 16 }}>
            Free · iOS · Android · v1.4.3
          </div>
        </div>

        <div className="gq-container gq-trust-strip">
          <div className="gq-trust-chips" aria-label="Promises">
            <span className="gq-trust-chip">
              <span className="glyph">🔒</span> Private by default
            </span>
            <span className="gq-trust-chip">
              <span className="glyph">🙅</span> No streaks
            </span>
            <span className="gq-trust-chip">
              <span className="glyph">📞</span> 988 always reachable
            </span>
          </div>
        </div>
      </section>

      <section className="gq-section" id="features">
        <div className="gq-container">
          <div className="gq-section-eyebrow">What it is, what it isn't</div>
          <h2 className="gq-section-title">
            Quiet structure for <em>harder days</em>.
          </h2>
          <p className="gq-section-sub">
            Six pieces. Every one of them has a skip. Every one of them respects where you are.
          </p>

          <div className="gq-features">
            {FEATURES.map(({ Icon: FeatureIcon, title, body }) => (
              <article className="gq-feature" key={title}>
                <span className="ic" aria-hidden="true">
                  {createElement(FeatureIcon, { size: 20 })}
                </span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="gq-crisis-strip" id="crisis">
        <div className="row">
          <span className="pill">
            <span className="dot" /> WORKS OFFLINE
          </span>
          <h2>
            If you're in crisis, call <span className="num">988</span>.
            <br />
            We never block this. Even offline.
          </h2>
          <p className="meta">Suicide &amp; Crisis Lifeline · free · 24 / 7 · multilingual</p>
        </div>
      </section>

      <section className="gq-newsletter-section">
        <div className="gq-container">
          <div className="newsletter-box">
            <h3>Get the occasional letter</h3>
            <p>No spam, no streaks, no pressure. One thoughtful email every few weeks about ADHD, anxiety, and building a gentler relationship with yourself.</p>
            <form id="landing-newsletter-form" onSubmit={handleNewsletterSubmit}>
              <input
                type="email"
                name="email"
                placeholder="your@email.com"
                required
                value={newsletterEmail}
                onChange={(e) => setNewsletterEmail(e.target.value)}
              />
              <button type="submit">Subscribe</button>
            </form>
            {newsletterStatus === 'success' && (
              <p className="newsletter-success">You're in. We'll send you something good soon.</p>
            )}
            {newsletterStatus === 'error' && (
              <p className="newsletter-error">Something went wrong. Try again, or email us at hi@gentlequest.app</p>
            )}
            <p className="privacy-note">We never share your email. Unsubscribe anytime.</p>
          </div>
        </div>
      </section>

      <footer className="gq-footer">
        <div className="gq-container">
          <div className="row">
            <div className="brand-row">
              <a className="gq-brand" href="/">
                <span className="gq-brand-mark" />
                <span>GentleQuest</span>
              </a>
              <span className="tagline">
                A wellness companion for heavy moments. Not therapy. Not medical care.
              </span>
            </div>
            <nav className="links" aria-label="Footer">
              <a href="/blog/">Blog</a>
              <a href="/privacy">Privacy</a>
              <a href="/terms">Terms</a>
              <a href="/about">About</a>
              <a href="/press">Press</a>
            </nav>
          </div>
          <div className="meta-row">
            <span>© 2026 Eidetic Works. All rights reserved.</span>
            <span className="contact">
              Contact · <a href="mailto:hi@gentlequest.app">hi@gentlequest.app</a>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
