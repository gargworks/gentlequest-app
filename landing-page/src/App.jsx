import { Heart, MessageCircle, Shield, Download, Smartphone, ExternalLink, Lock, PhoneCall } from 'lucide-react';

function App() {
  const IOS_APP_URL = 'https://apps.apple.com/app/gentlequest/id6756537464';
  const ANDROID_APP_URL = 'https://play.google.com/store/apps/details?id=app.gentlequest.www';
  const WEB_APP_URL = 'https://nucleus.gentlequest.app';

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <img src="/logo-192.png" alt="GentleQuest" className="w-10 h-10 rounded-xl" />
          <span className="text-xl font-semibold">GentleQuest</span>
        </div>
        <a
          href={WEB_APP_URL}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-full text-sm font-medium transition-colors"
        >
          Open App →
        </a>
      </nav>

      {/* Hero Section */}
      <section className="px-6 py-16 md:py-24 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
              A quiet place,{' '}
              <span className="gradient-text">whenever you need it.</span>
            </h1>
            <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-lg">
              Private. Judgment-free. Here when you need it — and not when you don&apos;t.
              GentleQuest is a wellness companion for the heavy moments, not a habit tracker.
              No streaks. No scores. No shame.
            </p>

            {/* App Store Badges */}
            <div className="flex flex-wrap gap-4 mb-6">
              <a
                href={IOS_APP_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 bg-white text-black rounded-xl hover:bg-gray-100 transition-colors"
              >
                <Download className="w-5 h-5" />
                <span className="font-medium">Download on iOS</span>
              </a>
              <a
                href={ANDROID_APP_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors"
              >
                <Smartphone className="w-5 h-5" />
                <span className="font-medium">Get on Android</span>
              </a>
            </div>

            <a
              href={WEB_APP_URL}
              className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Or try the Web App</span>
            </a>
          </div>

          {/* Hero Image */}
          <div className="flex justify-center relative">
            <div className="absolute -inset-1 rounded-full bg-purple-500/20 blur-xl"></div>
            <img
              src="/app-screenshot.png"
              alt="GentleQuest App Interface showing Luna AI"
              className="relative w-72 rounded-[2.5rem] shadow-2xl border-4 border-white/10 rotate-[-2deg] hover:rotate-0 transition-transform duration-500"
            />
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="px-6 py-6 border-t border-b border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-center items-center gap-4 md:gap-10 text-center">
          <p className="text-sm text-gray-400">
            Not medical care. Not therapy. Not a substitute.
          </p>
          <span className="hidden md:block text-white/20">·</span>
          <p className="text-sm" style={{ color: '#FF6B6B' }}>
            If you&apos;re in crisis, call{' '}
            <a href="tel:988" className="font-semibold underline underline-offset-2">
              988
            </a>{' '}
            (US) or your local emergency line.
          </p>
        </div>
      </section>

      {/* Features Section — R1 aligned */}
      <section className="px-6 py-16 bg-white/5">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">
            Built for the heavy moments
          </h2>
          <p className="text-center text-gray-400 mb-12 max-w-2xl mx-auto">
            Every part of GentleQuest is designed to be there when you need it — and to get out of your way when you don&apos;t.
          </p>

          {/* Row 1 */}
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            {/* Feature 1 — Private by default */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-pink-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 text-pink-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Private by default</h3>
              <p className="text-gray-300">
                Anonymity mode, data export, your phone stays your phone.
                We don&apos;t sell, train, or share what you say.
              </p>
            </div>

            {/* Feature 2 — Crisis paths that never block */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <PhoneCall className="w-8 h-8" style={{ color: '#FF6B6B' }} />
              </div>
              <h3 className="text-xl font-semibold mb-3">Crisis paths that never block</h3>
              <p className="text-gray-300">
                988 is always one tap away, even offline. A user in crisis is never
                locked out — not by compliance screens, not by anything.
              </p>
            </div>

            {/* Feature 3 — Skip anything, no shame */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Skip anything, no shame</h3>
              <p className="text-gray-300">
                Every step has a graceful exit. We don&apos;t gate you. &ldquo;Skip&rdquo; and
                &ldquo;Not now&rdquo; are always visible, never buried.
              </p>
            </div>
          </div>

          {/* Row 2 */}
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 4 — Warmer onboarding */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Warmer onboarding</h3>
              <p className="text-gray-300">
                Three trust rows up front: Private. No judgment. No pressure.
                You know what you&apos;re walking into before you share a thing.
              </p>
            </div>

            {/* Feature 5 — Journal that stays on your phone */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Journal that stays on your phone</h3>
              <p className="text-gray-300">
                Local-first. Today, an entry, the timeline. Never synced, never shared —
                just yours, encrypted on your device.
              </p>
            </div>

            {/* Feature 6 — Weekly review without scores */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-yellow-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-yellow-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Weekly review without scores</h3>
              <p className="text-gray-300">
                Mood shapes, not diagnoses. One thing worth remembering from the week.
                We surface patterns — we never label you.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Here when you need it.
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Free to download. No credit card. No commitments.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href={IOS_APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 rounded-xl font-semibold hover:opacity-90 transition-opacity"
              style={{ background: 'linear-gradient(to right, #667EEA, #FF6B6B)' }}
            >
              Download for iOS
            </a>
            <a
              href={ANDROID_APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white/10 rounded-xl font-semibold hover:bg-white/20 transition-colors"
            >
              Download for Android
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo-192.png" alt="GentleQuest" className="w-8 h-8 rounded-lg" />
            <span className="text-sm text-gray-400">© 2026 GentleQuest</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-400">
            <a href="https://nucleus.gentlequest.app/privacy" className="hover:text-white transition-colors">Privacy</a>
            <a href="https://nucleus.gentlequest.app/terms" className="hover:text-white transition-colors">Terms</a>
            <a href="mailto:support@gentlequest.app" className="hover:text-white transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
