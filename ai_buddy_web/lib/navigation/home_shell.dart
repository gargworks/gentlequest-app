import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kDebugMode, debugPrint;
import '../widgets/app_bottom_nav.dart';
import 'home_tab_deeplink.dart';
import '../screens/interactive_chat_screen.dart';
import '../screens/journal_screen.dart';
import '../screens/home/wellness_home_screen.dart';
import '../services/compliance_service.dart';
import '../screens/compliance_guard_screen.dart';
import '../screens/yours_screen.dart';

import '../widgets/crisis_resources.dart';
import '../models/message.dart';
import '../widgets/safety_legal_sheet.dart';
import '../widgets/help_entrypoint.dart';

// Global deep-link controller for switching HomeShell tabs from anywhere
// e.g., when handling a notification tap.

/// Design Authority D5 — 4-tab IA: Home / Chat / Journal / You.
///
/// [AppTab] still carries `mood`, `quest`, and `community` cases so the
/// not-yet-swept dhiwise/leopard code keeps compiling, but this shell only
/// has 4 real tabs. Any of those 3 retired values reaching here (an old
/// deep link, a stray notification payload, the legacy `/home/quest` route)
/// is treated as an alias for [AppTab.home] rather than crashing.
class HomeShell extends StatefulWidget {
  final AppTab initialTab;
  const HomeShell({super.key, this.initialTab = AppTab.home});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> with WidgetsBindingObserver {
  late AppTab _current;
  // Per-tab navigator keys
  final _homeNavKey = GlobalKey<NavigatorState>();
  final _talkNavKey = GlobalKey<NavigatorState>();
  final _journalNavKey = GlobalKey<NavigatorState>();
  final _yoursNavKey = GlobalKey<NavigatorState>();

  // Reselect notifiers to trigger screen-specific actions
  final ValueNotifier<int> _homeReselect = ValueNotifier<int>(0);
  final ValueNotifier<int> _talkReselect = ValueNotifier<int>(0);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this); // Compliance Watcher
    _current = _normalize(widget.initialTab);
    // Only let a deep link override the route-supplied initialTab if one was
    // ACTUALLY requested. Until 2026-09-02 this called _onDeepLinkTab()
    // unconditionally, and the bus's default value made "nothing requested"
    // look like a real request — so initialTab was silently discarded on
    // every mount, in both directions. See home_tab_deeplink.dart.
    if (homeTabDeepLink.hasRequest) {
      _onDeepLinkTab(); // Process a genuinely pre-set deep-link tab on startup
      // Consume it. A request is an event, not standing state: leaving it set
      // meant the last tab ever requested kept overriding initialTab on every
      // LATER mount of this shell. See home_tab_deeplink.consume().
      homeTabDeepLink.consume();
    }
    // Listen for deep-link tab change requests
    homeTabDeepLink.addListener(_onDeepLinkTab);
  }

  /// Maps the 3 retired tab values (mood/quest/community — no longer
  /// visible in [AppBottomNav]) onto [AppTab.home]. Every switch in this
  /// class routes through here first so a stray old-shaped deep link or
  /// route argument degrades to Home instead of hitting a missing case.
  AppTab _normalize(AppTab tab) {
    switch (tab) {
      case AppTab.home:
      case AppTab.mood:
      case AppTab.quest:
      case AppTab.community:
        return AppTab.home;
      case AppTab.talk:
        return AppTab.talk;
      case AppTab.journal:
        return AppTab.journal;
      case AppTab.yours:
        return AppTab.yours;
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _checkComplianceOnResume();
    }
  }

  Future<void> _checkComplianceOnResume() async {
    // Sixth-Order Hardening: Re-verify compliance on app resume.
    // If cache is >24h, this triggers GPS check.
    // If user moved to restricted zone, this catches them.
    try {
      final status = await ComplianceService().checkCompliance();
      if (status != ComplianceStatus.allowed) {
        if (mounted) {
           // Force back to Guard Screen if no longer compliant
           Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
             MaterialPageRoute(builder: (_) => const ComplianceGuardScreen()),
             (route) => false,
           );
        }
      }
    } catch (e) {
      debugPrint("Compliance resume check failed: $e");
    }
  }

  void _onDeepLinkTab() {
    final target = _normalize(homeTabDeepLink.value);
    if (kDebugMode) {
      try {
        debugPrint(
            '[HomeShell] deepLink request -> $target (current=$_current)');
      } catch (_) {}
    }
    if (_current != target) {
      setState(() => _current = target);
      if (kDebugMode) {
        try {
          debugPrint('[HomeShell] switched to $target');
        } catch (_) {}
      }
    } else {
      // If already on the tab, pop to its root and trigger reselect behavior
      final nav = _navFor(target);
      nav?.popUntil((route) => route.isFirst);
      switch (target) {
        case AppTab.home:
          _homeReselect.value++;
          break;
        case AppTab.talk:
          _talkReselect.value++;
          break;
        case AppTab.journal:
        case AppTab.yours:
          break;
        case AppTab.mood:
        case AppTab.quest:
        case AppTab.community:
          break; // unreachable — _normalize already folded these into home
      }
    }
  }

  int get _index {
    switch (_current) {
      case AppTab.home:
        return 0;
      case AppTab.talk:
        return 1;
      case AppTab.journal:
        return 2;
      case AppTab.yours:
        return 3;
      case AppTab.mood:
      case AppTab.quest:
      case AppTab.community:
        return 0; // unreachable — _normalize already folded these into home
    }
  }

  NavigatorState? _navFor(AppTab tab) {
    switch (tab) {
      case AppTab.home:
        return _homeNavKey.currentState;
      case AppTab.talk:
        return _talkNavKey.currentState;
      case AppTab.journal:
        return _journalNavKey.currentState;
      case AppTab.yours:
        return _yoursNavKey.currentState;
      case AppTab.mood:
      case AppTab.quest:
      case AppTab.community:
        return _homeNavKey.currentState; // unreachable — see _normalize
    }
  }

  Future<void> _showHelpSheet() async {
    await showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return SafeArea(
          top: false,
          child: Padding(
            padding: EdgeInsets.only(
              left: 16.0,
              right: 16.0,
              bottom: MediaQuery.of(ctx).viewInsets.bottom + 16.0,
              top: 12.0,
            ),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Need help now?',
                          style: theme.textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Close',
                        onPressed: () => Navigator.of(ctx).maybePop(),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'If you are in immediate danger, call your local emergency number.',
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: Colors.black54),
                  ),
                  const SizedBox(height: 12),
                  const CrisisResourcesWidget(riskLevel: RiskLevel.high),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: () async {
                        Navigator.of(ctx).maybePop();
                        await Future.delayed(Duration.zero);
                        if (!mounted) return;
                        await showSafetyLegalSheet(context);
                      },
                      icon: const Icon(Icons.gavel_outlined),
                      label: const Text('Safety & Legal'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // Help overlay shown only on the Home tab (was: Community tab, retired).
    Widget buildTabNavigator({
      required GlobalKey<NavigatorState> key,
      required WidgetBuilder builder,
      required bool active,
    }) {
      return HeroMode(
        enabled: active,
        child: Navigator(
          key: key,
          onGenerateRoute: (settings) => MaterialPageRoute(builder: builder),
        ),
      );
    }

    final pages = <Widget>[
      buildTabNavigator(
        key: _homeNavKey,
        active: _index == 0,
        builder: (_) => WellnessHomeScreen(
          showBottomNav: false,
          reselect: _homeReselect,
        ),
      ),
      buildTabNavigator(
        key: _talkNavKey,
        active: _index == 1,
        builder: (_) => InteractiveChatScreen(
          showBottomNav: false,
          reselect: _talkReselect,
        ),
      ),
      buildTabNavigator(
        key: _journalNavKey,
        active: _index == 2,
        builder: (_) => const JournalScreen(),
      ),
      buildTabNavigator(
        key: _yoursNavKey,
        active: _index == 3,
        builder: (_) => const YoursScreen(),
      ),
    ];

    final nav = _navFor(_current);
    final isKeyboardOpen = MediaQuery.viewInsetsOf(context).bottom > 0;

    return PopScope(
      // Allow system back only when keyboard is closed and current tab stack cannot pop
      canPop: !(isKeyboardOpen || (nav?.canPop() ?? false)),
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          if (isKeyboardOpen) {
            FocusScope.of(context).unfocus();
            return;
          }
          if (nav?.canPop() ?? false) {
            nav!.pop();
            return;
          }
        }
      },
      child: Scaffold(
        body: Stack(
          children: [
            IndexedStack(index: _index, children: pages),
            if (_current == AppTab.home)
              HelpEntrypointOverlay(onPressed: _showHelpSheet),
          ],
        ),
        bottomNavigationBar: AppBottomNav(
          current: _current,
          onTap: (tab) {
            setState(() => _current = _normalize(tab));
            if (tab == AppTab.talk) {
              _talkReselect.value++;
            }
          },
          onReselect: (tab) {
            // Pop to root of the tab, then trigger reselect action
            final target = _normalize(tab);
            final nav = _navFor(target);
            nav?.popUntil((route) => route.isFirst);
            switch (target) {
              case AppTab.home:
                _homeReselect.value++;
                break;
              case AppTab.talk:
                _talkReselect.value++;
                break;
              case AppTab.journal:
              case AppTab.yours:
                break;
              case AppTab.mood:
              case AppTab.quest:
              case AppTab.community:
                break; // unreachable — _normalize already folded these into home
            }
          },
        ),
      ),
    );
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    homeTabDeepLink.removeListener(_onDeepLinkTab);
    super.dispose();
  }
}
