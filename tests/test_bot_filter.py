"""Tests for the qualified_human bot-filtering rule set (Activation Proof Task 5)."""

import sys
import os

# Make the scripts/ directory importable as a package path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.analytics_dashboard import is_qualified_human, _BOT_UA_SUBSTRINGS


# Representative real-browser UAs (long enough to pass the >20 char rule).
CHROME_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)
FIREFOX_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
    "Gecko/20100101 Firefox/127.0"
)
# Desktop Linux Chrome (real human, long session).
CHROME_LINUX_DESKTOP = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
# Android Chrome (mobile — contains "Linux" but must be exempted).
CHROME_ANDROID = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
)


class TestBotUAFiltering:
    """Every crawler/automation UA in the blocklist must be rejected."""

    def test_each_blocklisted_substring_returns_false(self):
        # Wrap each needle in a realistic-looking UA shell so the >20 char
        # rule doesn't trip before the substring check.
        for needle in _BOT_UA_SUBSTRINGS:
            ua = f"Mozilla/5.0 (compatible; {needle}/1.0; +https://example.com/bot)"
            assert is_qualified_human({}, ua, 30.0, 3) is False, (
                f"UA containing {needle!r} was NOT filtered out"
            )

    def test_googlebot_rejected(self):
        ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        assert is_qualified_human({}, ua, 30.0, 3) is False

    def test_python_requests_rejected(self):
        ua = "python-requests/2.32.3"
        # Short UA — also caught by the <20 char rule, but the substring
        # rule would catch it regardless.
        assert is_qualified_human({}, ua, 1.0, 1) is False

    def test_headless_chrome_rejected(self):
        ua = (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/126.0.0.0 Safari/537.36"
        )
        assert is_qualified_human({}, ua, 1.0, 1) is False


class TestRealHumanSessions:
    """Genuine browser sessions must pass the filter."""

    def test_chrome_mac_long_session(self):
        assert is_qualified_human({}, CHROME_MAC, 30.0, 3) is True

    def test_safari_iphone_short_session(self):
        # Mobile short session is still human.
        assert is_qualified_human({}, SAFARI_IPHONE, 1.0, 1) is True

    def test_firefox_windows(self):
        assert is_qualified_human({}, FIREFOX_WIN, 120.0, 5) is True

    def test_chrome_linux_desktop_long_session(self):
        # Desktop Linux with a real-duration, multi-pageview session is human.
        assert is_qualified_human({}, CHROME_LINUX_DESKTOP, 45.0, 4) is True

    def test_android_short_session_not_penalized(self):
        # Android UA contains "Linux" but must NOT be penalized by the
        # desktop-Linux headless rule.
        assert is_qualified_human({}, CHROME_ANDROID, 1.0, 1) is True


class TestDesktopLinuxHeadlessRule:
    """The desktop-Linux + sub-2s + single-pageview heuristic."""

    def test_desktop_linux_short_single_pageview_rejected(self):
        assert is_qualified_human({}, CHROME_LINUX_DESKTOP, 1.0, 1) is False

    def test_desktop_linux_short_multi_pageview_passes(self):
        # Multi-pageview breaks the single-pageview condition.
        assert is_qualified_human({}, CHROME_LINUX_DESKTOP, 1.0, 2) is True

    def test_desktop_linux_long_single_pageview_passes(self):
        # Long duration breaks the sub-2s condition.
        assert is_qualified_human({}, CHROME_LINUX_DESKTOP, 5.0, 1) is True


class TestEdgeCases:
    def test_empty_ua_rejected(self):
        assert is_qualified_human({}, "", 30.0, 3) is False

    def test_none_ua_rejected(self):
        assert is_qualified_human({}, None, 30.0, 3) is False

    def test_short_ua_rejected(self):
        assert is_qualified_human({}, "bot", 30.0, 3) is False

    def test_non_string_ua_rejected(self):
        assert is_qualified_human({}, 12345, 30.0, 3) is False
