# Resolve Build Errors and Test Failures

This plan outlines the steps to resolve the Android build error and multiple backend test failures.

## User Review Required

> [!IMPORTANT]
> The Android project in `mobile/android/` appears to be using a very new React Native version (0.85.3) but has legacy Gradle configuration files. I will update the configuration to match modern React Native standards to resolve the build error.

## Proposed Changes

### Mobile Component

#### [package.json](file:///C:/Users/DELL/Desktop/paybot/mobile/android/package.json)
- Update `@types/react` to `^19.1.1` to resolve peer dependency conflicts with React Native 0.85.3.

#### [gradle.properties](file:///C:/Users/DELL/Desktop/paybot/mobile/android/android/gradle.properties)
- Update `org.gradle.java.installations.paths` to point to the correct JDK path on this machine.

#### [settings.gradle](file:///C:/Users/DELL/Desktop/paybot/mobile/android/android/settings.gradle)
- Comment out legacy `native_modules.gradle` application which is no longer needed/available in React Native 0.85.3.

#### [build.gradle](file:///C:/Users/DELL/Desktop/paybot/mobile/android/android/app/build.gradle)
- Comment out legacy `native_modules.gradle` application.

---

### Backend Component

#### [magpie_service.py](file:///C:/Users/DELL/Desktop/paybot/backend/services/magpie_service.py)
- Update `create_unified_checkout` to include `"gateway": "magpie"` in the returned success response.

#### [currency_service.py](file:///C:/Users/DELL/Desktop/paybot/backend/services/currency_service.py)
- Add `"USDT"` to `SUPPORTED_CURRENCIES`.

#### [test_bot.py](file:///C:/Users/DELL/Desktop/paybot/backend/tests/test_bot.py)
- Update `fake_create_session` mocks to accept keyword arguments correctly.
- Synchronize error message assertions with the implementation.

#### [test_multi_currency.py](file:///C:/Users/DELL/Desktop/paybot/backend/tests/test_multi_currency.py)
- Fix `set_rate_override` calls to use currency pair strings (e.g., `"USD_PHP"`).
- Fix `monkeypatch` usage by passing the fixture to test functions.
- Update `pytest.raises` regex to match the actual error message.

#### [test_magpie_integration.py](file:///C:/Users/DELL/Desktop/paybot/backend/tests/test_magpie_integration.py)
- Fix the asyncio event loop error by using a more appropriate test pattern.

---

## Verification Plan

### Automated Tests
- Run backend tests: `pytest` in `backend/` directory.
- Verify Android project evaluation: `cmd /c ./gradlew.bat help` in `mobile/android/android/`.

### Manual Verification
- Verify frontend build: `cmd /c npm run build` in `frontend/`.
