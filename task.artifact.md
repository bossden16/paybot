# Task: Resolve Build Errors and Test Failures

- [ ] Fix Android Build Errors
    - [x] Update `mobile/android/package.json` and run `npm install`
    - [x] Update `mobile/android/android/gradle.properties` paths
    - [ ] Update `mobile/android/android/settings.gradle` to remove legacy scripts
    - [ ] Update `mobile/android/android/app/build.gradle` to remove legacy scripts
- [ ] Fix Backend Test Failures
    - [/] Fix `tmp_telegram_test.py` (already done)
    - [ ] Fix `tests/test_bot.py` mocks and assertions
    - [ ] Fix `tests/test_multi_currency.py` logic and syntax
    - [ ] Fix `tests/test_magpie_integration.py` asyncio loop issue
    - [ ] Resolve missing `USDT` currency in service
- [ ] Verify all builds and tests pass
    - [ ] Run `pytest`
    - [ ] Run `gradlew help`
