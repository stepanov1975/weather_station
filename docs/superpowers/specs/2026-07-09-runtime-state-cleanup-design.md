# Runtime State and Refactor Cleanup Design

## Goal

Fix the five verified runtime defects from the IMS-only refactor and remove the
confirmed optional leftovers without redesigning the application UI or broadly
rewriting the large controller, GUI, or IMS parser modules.

## State Ownership

Internet connectivity has one owner: the connection-monitoring loop. Current
observation and forecast requests must not overwrite the monitor's
`last_connection_status` value. A transition from disconnected to connected
continues to trigger one immediate refresh of both IMS sources.

Current observations and forecasts retain independent API status values in the
controller. A small controller helper combines them for the existing single API
label with this priority:

1. `error`
2. `offline`
3. `mock`
4. `ok`
5. pending (`None`)

This prevents a successful current-observation refresh from hiding a failed
forecast refresh. The GUI layout remains unchanged.

## Cache Behavior

The forecast cache moves from the project/package directory to
`$XDG_STATE_HOME/weather_display/forecast_cache.json`, falling back to
`~/.local/state/weather_display/forecast_cache.json`. This makes the cache
writable for installed packages and keeps generated data out of the repository.

A valid cache hit continues to return usable forecast data with `api_status`
`ok` and `cache_hit` true, but its `connection_status` is `None` because no
network request occurred. The controller does not derive global connectivity
from this service field.

## Side-Effect Isolation

Importing `weather_display.main` must not clear root logging handlers, create log
files, or configure logging. A `configure_logging()` function performs the
existing console and rotating-file setup when `main()` starts.

Connectivity checks apply their timeout only to the socket created for that
check. They must leave `socket.getdefaulttimeout()` unchanged.

## Cleanup Scope

Remove only confirmed leftovers identified in the review:

- unused `format_temperature`;
- unused `ctk_theme_name` and status-background colors;
- unreachable `limit_reached` GUI status handling and obsolete footer comments;
- unused production path for IMS city current analysis: `get_current_weather`,
  `parse_current_weather`, `CurrentWeather`, and `forecast_time` mock data;
- unused eager `WeatherIconHandler` re-export from `utils.__init__`;
- runtime creation of the bundled, read-only weather icon directory;
- stale or redundant comments directly adjacent to changed code.

The standalone IMS station-listing command, public forecast behavior, GUI
layout, unrelated localization data, and broad module organization remain
unchanged. Translations used only by functionality removed in this cleanup may
be removed with that functionality.

## Error Handling

Forecast request failures continue to use the last cached payload when one
exists. Cache write failures remain non-fatal. Logging configuration failures
continue to fall back to console-only logging. The status aggregator must not
raise when one or both service statuses are still pending.

## Testing

Regression tests are written before production edits and must demonstrate:

- forecast cache path respects `XDG_STATE_HOME` and is outside the project;
- cache hits do not assert connectivity;
- observation success cannot mask forecast failure;
- service updates do not mutate monitor-owned connectivity;
- importing `weather_display.main` preserves existing root handlers;
- connectivity checks preserve the process-wide socket timeout;
- removed APIs and configuration names have no production call sites.

Focused tests run after each change. Final verification uses the repository's
full `pytest`, Ruff, and mypy commands.
