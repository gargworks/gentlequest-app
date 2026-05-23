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
  AppTab _value = AppTab.talk;

  /// Latest requested tab. Use for read-only inspection of the most recent
  /// request — NOT a reliable proxy for the currently visible tab (that
  /// lives in `HomeShell._current` and tracks bottom-nav taps that bypass
  /// this bus).
  AppTab get value => _value;

  /// Request a tab switch. Always fires `notifyListeners()`, even when
  /// [tab] equals the previous value. That same-value fire is what makes
  /// "go to Talk from a sheet" work when the user is already on Talk (the
  /// listener still runs, sees the visible tab matches, and pops to root
  /// + reselects — the right behavior for a deep-link request).
  void request(AppTab tab) {
    _value = tab;
    notifyListeners();
  }
}

/// Process-wide deep-link bus. Listened to by `HomeShell._onDeepLinkTab`.
final HomeTabDeepLink homeTabDeepLink = HomeTabDeepLink();
