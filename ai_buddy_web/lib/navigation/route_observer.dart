import 'package:flutter/widgets.dart';
import '../services/firebase_service.dart';

/// Global route observer for screens that need route visibility callbacks.
final RouteObserver<ModalRoute<void>> routeObserver =
    RouteObserver<ModalRoute<void>>();

/// Logs screen views to Firebase Analytics on every navigation event.
class AnalyticsRouteObserver extends NavigatorObserver {
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _logScreen(route);
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    if (newRoute != null) _logScreen(newRoute);
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (previousRoute != null) _logScreen(previousRoute);
  }

  void _logScreen(Route<dynamic> route) {
    final name = route.settings.name;
    if (name != null && name.isNotEmpty) {
      FirebaseService().logScreenView(name);
    }
  }
}
