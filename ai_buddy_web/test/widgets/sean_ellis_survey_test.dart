import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ai_buddy_web/providers/survey_provider.dart';
import 'package:ai_buddy_web/widgets/sean_ellis_survey_sheet.dart';

/// Sean-Ellis PMF survey instrument tests.
///
/// Coverage:
///   1. Sheet opens and shows the canonical question.
///   2. All 4 answer options are present.
///   3. Submit button records the answer (provider state + SharedPreferences).
///   4. Survey only shows once (SharedPreferences `sean_ellis_survey_shown_v1`).
///   5. shouldShowSurvey() returns false before 3 sessions.
///   6. shouldShowSurvey() returns true after 3 sessions.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  /// Helper: pump the survey sheet inside a Provider wrapper so
  /// `context.read<SurveyProvider>()` resolves on submit. The provider is
  /// placed ABOVE MaterialApp because the sheet uses `useRootNavigator: true`,
  /// which renders the modal route in the root navigator — above the
  /// MaterialApp's home where a provider placed inside `home` would be
  /// invisible to the sheet's context.
  Future<void> pumpSheet(WidgetTester tester, SurveyProvider provider) async {
    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: provider,
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () => showSeanEllisSurveySheet(context),
                  child: const Text('open'),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
  }

  group('SurveyProvider.shouldShowSurvey', () {
    test('returns false before 3 sessions', () async {
      final p = SurveyProvider();
      await p.load();
      expect(p.sessionCount, 0);
      expect(p.shouldShowSurvey(), isFalse);

      await p.incrementSessionCount();
      await p.incrementSessionCount();
      expect(p.sessionCount, 2);
      expect(p.shouldShowSurvey(), isFalse,
          reason: '2 sessions is below the 3-session threshold');
    });

    test('returns true after 3 sessions and not yet shown', () async {
      final p = SurveyProvider();
      await p.load();
      await p.incrementSessionCount();
      await p.incrementSessionCount();
      await p.incrementSessionCount();
      expect(p.sessionCount, 3);
      expect(p.shouldShowSurvey(), isTrue,
          reason: '3 sessions meets the threshold and survey not yet shown');
    });
  });

  group('SeanEllis survey sheet', () {
    testWidgets('opens and shows the Sean-Ellis question', (tester) async {
      final p = SurveyProvider();
      await p.load();
      await pumpSheet(tester, p);

      expect(
        find.text('How would you feel if you could no longer use GentleQuest?'),
        findsOneWidget,
        reason: 'the canonical Sean-Ellis question must be visible',
      );
    });

    testWidgets('all 4 answer options are present', (tester) async {
      final p = SurveyProvider();
      await p.load();
      await pumpSheet(tester, p);

      expect(find.text('Very disappointed'), findsOneWidget);
      expect(find.text('Somewhat disappointed'), findsOneWidget);
      expect(find.text('Not disappointed'), findsOneWidget);
      expect(find.text('N/A - I no longer use it'), findsOneWidget);
    });

    testWidgets('submit button records the answer', (tester) async {
      final p = SurveyProvider();
      await p.load();
      await pumpSheet(tester, p);

      // Select the first option ("Very disappointed").
      await tester.tap(find.text('Very disappointed'));
      await tester.pump();

      // Submit button is now enabled — tap it.
      final submitFinder = find.widgetWithText(ElevatedButton, 'Submit');
      expect(tester.widget<ElevatedButton>(submitFinder).enabled, isTrue);
      await tester.tap(submitFinder);
      await tester.pumpAndSettle();

      // Provider state reflects the recorded answer + shown flag.
      expect(p.answer, 'Very disappointed');
      expect(p.shown, isTrue);

      // SharedPreferences persisted the answer + shown flag.
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('sean_ellis_survey_answer_v1'),
          'Very disappointed');
      expect(prefs.getBool('sean_ellis_survey_shown_v1'), isTrue);
    });

    testWidgets('survey only shows once (SharedPreferences gate)',
        (tester) async {
      // Simulate a user who has already seen the survey.
      SharedPreferences.setMockInitialValues({
        'sean_ellis_survey_shown_v1': true,
        'gq_chat_session_count_v1': 5,
      });
      final p = SurveyProvider();
      await p.load();

      // Already shown + above threshold → shouldShowSurvey is false.
      expect(p.shown, isTrue);
      expect(p.sessionCount, 5);
      expect(p.shouldShowSurvey(), isFalse,
          reason: 'once shown, the survey must never reappear');
    });
  });
}
