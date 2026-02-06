// ignore_for_file: avoid_print
import 'dart:io';
import 'package:integration_test/integration_test_driver_extended.dart';

Future<void> main() async {
  await integrationDriver(
    onScreenshot: (String name, List<int> bytes, [Map<String, dynamic>? args]) async {
      final File image = File('build/integration_test_screenshots/$name.png');
      image.parent.createSync(recursive: true);
      await image.writeAsBytes(bytes);
      print('Screenshot saved: ${image.path}');
      return true;
    },
  );
}
