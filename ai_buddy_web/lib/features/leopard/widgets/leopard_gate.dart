import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../config/feature_flags.dart';
import '../leopard_shell.dart';
import 'leopard_access_gate.dart';
import '../../../dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart';
import '../../../dhiwise/core/utils/size_utils.dart' as dhiwise_sizer;

class LeopardGate extends StatefulWidget {
  final bool showBottomNav;
  final ValueNotifier<int>? reselect;

  const LeopardGate({
    super.key,
    this.showBottomNav = true,
    this.reselect,
  });

  @override
  State<LeopardGate> createState() => _LeopardGateState();
}

class _LeopardGateState extends State<LeopardGate> {
  Future<bool>? _accessFuture;

  @override
  void initState() {
    super.initState();
    _accessFuture = _checkAccess();
  }

  Future<bool> _checkAccess() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('leopard_access_granted') ?? false;
  }

  void _onAccessGranted() {
    setState(() {
      _accessFuture = Future.value(true);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!FeatureFlags.enableLeopardMode) {
      // LEGACY MODE: The Old World
      return dhiwise_sizer.Sizer(
        builder: (context, orientation, deviceType) => WellnessDashboardScreen(
          showBottomNav: widget.showBottomNav,
          reselect: widget.reselect,
        ),
      );
    }

    // LEOPARD MODE: Check for Invite Code access
    return FutureBuilder<bool>(
      future: _accessFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: Color(0xFF121212),
            body: Center(
                child: CircularProgressIndicator(color: Color(0xFF667EEA))),
          );
        }

        final hasAccess = snapshot.data ?? false;

        if (hasAccess) {
          return const LeopardShell();
        } else {
          return LeopardAccessGate(onGranted: _onAccessGranted);
        }
      },
    );
  }
}
