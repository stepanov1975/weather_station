# Muggy Weather Condition Localization Design

## Goal

Translate the IMS forecast condition `Muggy` through the existing weather-condition localization path so Russian displays show `Душно` instead of the untranslated English value and no missing-mapping warning is emitted.

## Design

- Add the `muggy` translation key to the English and Russian translation dictionaries with values `Muggy` and `Душно`.
- Add `muggy` to `WEATHER_CONDITION_MAP`, pointing to the new translation key.
- Keep the existing case-insensitive, longest-match translation behavior unchanged.
- Do not suppress warnings or add a condition-specific branch; unknown conditions must continue to use the existing warning and fallback behavior.

## Testing

- Add a focused regression test using the real `translate_weather_condition` function.
- Verify `Muggy` translates to `Muggy` in English and `Душно` in Russian.
- Verify the successful translations do not emit the missing-mapping warning.
- Run the focused test first, followed by the repository's complete pytest, Ruff, and mypy checks.

## Scope

Only the `Muggy` condition and its regression coverage are included. No other weather conditions, localization behavior, logging, or runtime code will change.
