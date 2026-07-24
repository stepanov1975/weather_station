from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests

from weather_display.services.ims_lasthour import IMSLastHourWeather


def test_fetch_data_from_local_xml_extracts_station_measurements(tmp_path: Path) -> None:
    xml_path = tmp_path / "imslasthour.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ims>
  <HebrewVariablesNames>
    <TD>Temperature</TD>
    <RH>Humidity</RH>
  </HebrewVariablesNames>
  <Observation>
    <stn_name>En Hahoresh</stn_name>
    <stn_num>123</stn_num>
    <time_obs>2026-07-03T12:30:00</time_obs>
    <TD>28.4</TD>
    <RH>63</RH>
  </Observation>
</ims>
""",
        encoding="utf-8",
    )

    weather = IMSLastHourWeather("en hahoresh")

    assert weather.fetch_data(use_local_file=True, local_file_path=str(xml_path))
    assert weather.get_metadata() == {"StationName": "En Hahoresh", "StationNumber": "123"}
    assert weather.get_measurement("TD") == {"value": "28.4", "description": "Temperature"}
    assert weather.get_measurement("RH") == {"value": "63", "description": "Humidity"}
    assert weather.get_observation_time(israel_time=False)["raw"] == "2026-07-03T12:30:00"
    assert weather.get_observation_time()["Hour"] == "15"
    assert weather.get_hebrew_variables() == {"TD": "Temperature", "RH": "Humidity"}


def test_list_all_stations_from_local_xml_omits_duplicate_names(tmp_path: Path) -> None:
    xml_path = tmp_path / "imslasthour.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ims>
  <Observation>
    <stn_name>En Hahoresh</stn_name>
    <stn_num>123</stn_num>
  </Observation>
  <Observation>
    <stn_name>En Hahoresh</stn_name>
    <stn_num>999</stn_num>
  </Observation>
  <Observation>
    <stn_name>Tel Aviv Coast</stn_name>
    <stn_num>456</stn_num>
  </Observation>
</ims>
""",
        encoding="utf-8",
    )

    stations = IMSLastHourWeather.list_all_stations(use_local_file=True, local_file_path=str(xml_path))

    assert stations == {
        "En Hahoresh": {"StationNumber": "123"},
        "Tel Aviv Coast": {"StationNumber": "456"},
    }


def test_fetch_data_from_local_xml_returns_false_when_station_missing(tmp_path: Path) -> None:
    xml_path = tmp_path / "imslasthour.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<ims>
  <Observation>
    <stn_name>Tel Aviv Coast</stn_name>
    <stn_num>456</stn_num>
  </Observation>
</ims>
""",
        encoding="utf-8",
    )
    weather = IMSLastHourWeather("En Hahoresh")

    assert not weather.fetch_data(use_local_file=True, local_file_path=str(xml_path))
    assert weather.get_all_data() is None


def test_fetch_data_from_malformed_local_xml_returns_false(tmp_path: Path) -> None:
    xml_path = tmp_path / "imslasthour.xml"
    xml_path.write_text("<ims><Observation>", encoding="utf-8")
    weather = IMSLastHourWeather("En Hahoresh")

    assert not weather.fetch_data(use_local_file=True, local_file_path=str(xml_path))
    assert weather.get_all_data() is None


def test_station_network_error_returns_false_without_data() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    with patch(
        "weather_display.services.ims_lasthour.requests.get",
        side_effect=requests.exceptions.ConnectionError("offline"),
    ):
        assert not weather.fetch_data()

    assert weather.get_all_data() is None


def test_station_request_uses_short_connect_and_read_timeouts() -> None:
    weather = IMSLastHourWeather("En Hahoresh")
    response = SimpleNamespace(
        content=b"<ims></ims>",
        raise_for_status=lambda: None,
        status_code=200,
    )

    with patch("weather_display.services.ims_lasthour.requests.get", return_value=response) as get:
        weather.fetch_data()

    get.assert_called_once_with(weather.IMS_URL, timeout=(3, 10))


def test_observation_time_accepts_offset_and_zulu_timestamps() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    offset_time = weather._convert_to_israel_time({"raw": "2026-07-24T12:00:00+00:00"})
    zulu_time = weather._convert_to_israel_time({"raw": "2026-07-24T12:00:00Z"})

    assert offset_time["Hour"] == "15"
    assert zulu_time["Hour"] == "15"
    assert "Conversion_Error" not in offset_time
    assert "Conversion_Error" not in zulu_time


def test_empty_accessors_return_empty_or_none_before_fetching() -> None:
    weather = IMSLastHourWeather("En Hahoresh")

    assert weather.get_all_data() is None
    assert weather.get_metadata() is None
    assert weather.get_measurement("TD") is None
    assert weather.get_all_measurements() is None
    assert weather.get_observation_time() is None
    assert weather.get_hebrew_variables() == {}


def test_list_all_stations_from_malformed_local_xml_returns_empty(tmp_path: Path) -> None:
    xml_path = tmp_path / "imslasthour.xml"
    xml_path.write_text("<ims><Observation>", encoding="utf-8")

    assert IMSLastHourWeather.list_all_stations(
        use_local_file=True,
        local_file_path=str(xml_path),
    ) == {}
