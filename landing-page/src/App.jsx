import { Heart, MessageCircle, Brain, Download, Smartphone, ExternalLink } from 'lucide-react';

function App() {
  const IOS_APP_URL = 'https://apps.apple.com/us/app/gentlequest/id6737521877';
  const ANDROID_APP_URL = 'https://play.google.com/store/apps/details?id=com.gentlequest.app';
  const WEB_APP_URL = 'https://app.gentlequest.app';

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <img src="/favicon.png" alt="GentleQuest" className="w-10 h-10 rounded-xl" />
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
              Progress{' '}
              <span className="gradient-text">Without Pressure</span>
            </h1>
            <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-lg">
              The AI companion that helps you build mental resilience through gentle,
              gamified daily quests. Tiny wins when you're overwhelmed.
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

          {/* Hero Image Placeholder */}
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

      {/* Features Section */}
      <section className="px-6 py-16 bg-white/5">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            Why GentleQuest?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-pink-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-pink-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">No Guilt Streaks</h3>
              <p className="text-gray-300">
                We never shame you for missed days. Life happens.
                We&apos;re here when you're ready.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Buddy Alex</h3>
              <p className="text-gray-300">
                A compassionate AI that remembers your context
                and adapts to your unique journey.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Science-Backed</h3>
              <p className="text-gray-300">
                Built on CBT & DBT principles. Real techniques,
                delivered gently.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Start Your Gentle Journey Today
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Free to download. No credit card required.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href={IOS_APP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold hover:opacity-90 transition-opacity"
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
            <img src="/icon-512.png" alt="GentleQuest" className="w-8 h-8 rounded-lg" />
            <span className="text-sm text-gray-400">© 2026 GentleQuest</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-400">
            <a href="/privacy" className="hover:text-white transition-colors">Privacy</a>
            <a href="/terms" className="hover:text-white transition-colors">Terms</a>
            <a href="/support" className="hover:text-white transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
