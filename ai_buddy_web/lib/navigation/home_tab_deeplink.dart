import 'package:flutter/material.dart';
import '../widgets/app_bottom_nav.dart';

/// Tab deep-link request bus.
///
/// `ValueNotifier` suppresses same-value writes (sets that don't actually
/// change `_value` silently no-op), and `AppBottomNav.onTap` updates
/// `HomeShell._current` directly via `setState` without keeping this bus in
/// sync. The combination caused live ship-blocker bugs (mood-low sheet "Chat
/// with Alex" + Quest "Quick Lanes" → silent failure when the user was
/// already at, or had previously visited, the target tab).
///
/// Fix: a plain [ChangeNotifier] subclass that ALWAYS fires
/// `notifyListeners()` on every `request(tab)`, even when [_value] is
/// already equal to the requested tab. The listener in `HomeShell` then
/// branches on whether the visible tab matches the request (switch tabs
/// vs pop-to-root-and-reselect on the current tab).
///
/// Migration: call sites previously did `homeTabDeepLink.value = AppTab.X`.
/// They now call `homeTabDeepLink.request(AppTab.X)`. The `value` getter
/// stays for read access.
class HomeTabDeepLink extends ChangeNotifier {
  /// Defaults to [AppTab.home] so that "nothing has been requested" is
  /// distinguishable from "Talk was requested".
  ///
  /// This was `AppTab.talk` until 2026-09-02, which made the default
  /// indistinguishable from an explicit request and silently defeated
  /// `HomeShell.initialTab`: `HomeShell.initState` sets `_current` from
  /// `initialTab` and then immediately calls `_onDeepLinkTab()`, which
  /// overwrote it with this value. Every mount therefore landed on Talk no
  /// matter what the route passed — including the returning-user path that
  /// welcome_screen.dart:191 deliberately routes to Home.
  ///
  /// Safe to change: all ten call sites set the tab through `request()`
  /// (main.dart deep links at :87/:102/:115, resource_library_screen.dart:299,
  /// wellness_home_screen.dart:173/:438, assessment_flow_screen.dart:240,
  /// mood_reflection_sheet.dart:273, mood_low_reflection_sheet.dart:150).
  /// None depended on the default.
  /// Null until something actually calls [request]. `HomeShell` must not
  /// override its route-supplied `initialTab` while this is null.
  AppTab? _requested;

  /// Whether any tab has actually been requested on this bus. `HomeShell`
  /// checks this at mount so that "no request" leaves `initialTab` alone.
  bool get hasRequest => _requested != null;

  /// Latest requested tab, or [AppTab.home] if nothing has been requested.
  /// Use for read-only inspection of the most recent request — NOT a
  /// reliable proxy for the currently visible tab (that lives in
  /// `HomeShell._current` and tracks bottom-nav taps that bypass this bus).
  ///
  /// Prefer [hasRequest] before acting on this at mount time; a bare read
  /// cannot distinguish "nothing requested" from "Home requested", which is
  /// exactly the confusion that caused the 2026-09-02 bug.
  AppTab get value => _requested ?? AppTab.home;

  /// Request a tab switch. Always fires `notifyListeners()`, even when
  /// [tab] equals the previous value. That same-value fire is what makes
  /// "go to Talk from a sheet" work when the user is already on Talk (the
  /// listener still runs, sees the visible tab matches, and pops to root
  /// + reselects — the right behavior for a deep-link request).
  void request(AppTab tab) {
    _requested = tab;
    notifyListeners();
  }

  /// Marks the current request as handled, returning the bus to "nothing
  /// requested".
  ///
  /// Added 2026-09-03. Without this, `_requested` was write-once-and-STICKY:
  /// nothing cleared it in production, so the LAST request ever made kept
  /// overriding `HomeShell.initialTab` on every subsequent mount. Concretely:
  /// tap a quest notification (main.dart:87 requests Home), then later clear
  /// the compliance gate, which routes `/main` with `AppTab.talk` — the stale
  /// Home request wins and the user lands on Home.
  ///
  /// That is the SAME failure as the 2026-09-02 bug this class was rewritten
  /// to fix — a deep-link value outliving its request and silently defeating
  /// initialTab. The rewrite fixed the "never requested" case and left the
  /// "already consumed" case, because I only tested a first mount. A request
  /// is an EVENT; the old code and my fix both stored it as STATE.
  ///
  /// Only the mount-time consumer calls this. The live listener must NOT:
  /// while a shell is mounted, `value` is read synchronously inside the
  /// notification and consuming there would race nothing but buys nothing.
  void consume() {
    _requested = null;
  }

  /// Test-only: return the bus to its pristine "nothing requested" state.
  /// The bus is a process-wide singleton, so a request made by one test
  /// otherwise leaks into every test that mounts `HomeShell` afterwards.
  @visibleForTesting
  void resetForTest() {
    _requested = null;
  }
}

/// Process-wide deep-link bus. Listened to by `HomeShell._onDeepLinkTab`.
final HomeTabDeepLink homeTabDeepLink = HomeTabDeepLink();
