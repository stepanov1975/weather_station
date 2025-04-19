"""
Israel Meteorological Service (IMS) Last Hour Weather Data Service.

This module provides the `IMSLastHourWeather` class, designed to retrieve and
parse the publicly available XML feed containing the last hour's weather
observations from various stations across Israel.

The class handles:
- Fetching the XML data from the official IMS URL or a local file.
- Parsing the XML structure using `xml.etree.ElementTree`.
- Identifying and extracting data for a specific weather station by name.
- Parsing observation timestamps and converting them to the Israel timezone.
- Extracting measurement values (e.g., temperature, humidity) and associated
  metadata, including Hebrew descriptions if available in the feed.
- Providing methods to access the fetched data (metadata, specific measurements,
  all measurements, observation time).
- Offering a class method to list all stations found in the data feed.

Error handling is included for network issues, XML parsing errors, and cases
where the specified station is not found. Debug logging provides insights into
the fetching and parsing process.
"""

import xml.etree.ElementTree as ET
import requests
import os
import datetime
import pytz # For timezone handling
import logging
from typing import Dict, Any, Optional, List, Set, Tuple

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

class IMSLastHourWeather:
    """
    Fetches and parses the last hour weather observation data from the IMS XML feed.

    Retrieves XML data from the specified IMS URL, identifies the data corresponding
    to the configured station name, and parses various measurements and metadata.
    Handles timezone conversion for observation times.

    Attributes:
        station_name (str): The target weather station name to extract data for.
        data (Optional[Dict[str, Any]]): Stores the parsed data for the target
            station after a successful fetch. Structure includes 'metadata',
            'measurements', 'time', and 'time_israel'. None initially or if
            fetch fails.
        hebrew_variables (Dict[str, str]): A dictionary mapping technical
            measurement tags (e.g., 'TD', 'RH') to their Hebrew descriptions
            as found in the XML feed.
        israel_timezone (pytz.tzinfo.BaseTzInfo): Timezone object for 'Asia/Jerusalem'.
        IMS_URL (str): The constant URL for the IMS last hour XML data feed.
    """

    IMS_URL: str = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
    # DEBUG flag is removed in favor of standard logging levels
    # DEBUG = True

    def __init__(self, station_name: str):
        """
        Initializes the IMSLastHourWeather service for a specific station.

        Args:
            station_name (str): The name of the weather station to retrieve data for
                                (e.g., "En Hahoresh", "Tel Aviv Coast"). Case-insensitive
                                matching is attempted during fetch.
        """
        if not station_name:
            raise ValueError("Station name cannot be empty.")
        self.station_name: str = station_name
        self.data: Optional[Dict[str, Any]] = None # Parsed data stored here
        self.hebrew_variables: Dict[str, str] = {} # Stores Hebrew variable descriptions
        try:
            self.israel_timezone = pytz.timezone('Asia/Jerusalem')
        except pytz.UnknownTimeZoneError:
            logger.error("Failed to initialize timezone 'Asia/Jerusalem'. Time conversions may fail.")
            # Fallback to UTC or handle error as appropriate
            self.israel_timezone = pytz.UTC

        logger.info(f"IMSLastHourWeather initialized for station: '{self.station_name}'")

    def fetch_data(self, use_local_file: bool = False, local_file_path: str = "imslasthour.xml") -> bool:
        """
        Fetches and parses the IMS XML weather data.

        Retrieves the XML data either from the live IMS_URL or a specified local file.
        Parses the XML, extracts Hebrew variable descriptions, finds the data for
        the initialized `station_name`, and stores it in `self.data`.

        Args:
            use_local_file (bool): If True, attempts to read data from `local_file_path`
                                   instead of fetching from `IMS_URL`. Defaults to False.
            local_file_path (str): The path to the local XML file to use if
                                   `use_local_file` is True. Defaults to "imslasthour.xml".

        Returns:
            bool: True if data was successfully fetched, parsed, and the station was
                  found. False indicates an error during fetching, parsing, or if the
                  station was not present in the data. Details are logged.
        """
        root: Optional[ET.Element] = None
        try:
            if use_local_file:
                logger.info(f"Attempting to use local IMS data file: {local_file_path}")
                if not os.path.exists(local_file_path):
                    logger.error(f"Local IMS file not found: {local_file_path}")
                    return False
                # Parse the local XML file
                tree = ET.parse(local_file_path)
                root = tree.getroot()
                logger.info(f"Successfully parsed local file: {local_file_path}")
            else:
                logger.info(f"Fetching IMS data from URL: {self.IMS_URL}")
                # Fetch data from the live URL with a timeout
                response = requests.get(self.IMS_URL, timeout=30) # 30-second timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                logger.debug(f"IMS data fetched successfully (Status: {response.status_code}).")
                # Parse the XML content from the response
                root = ET.fromstring(response.content)
                logger.debug("Successfully parsed XML content from response.")

            if root is None:
                 logger.error("XML root element is None after fetch/parse attempt.")
                 return False

            # Parse Hebrew variable names first, if available
            self._parse_hebrew_variables(root)

            # Find the specific station's data within the parsed XML
            station_data = self._find_station_data(root)

            if station_data:
                self.data = station_data
                logger.info(f"Successfully processed data for station '{self.station_name}'.")
                return True
            else:
                logger.warning(f"Station '{self.station_name}' not found in the IMS data feed.")
                self.data = None # Ensure data is None if station not found
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching IMS data: {e}", exc_info=True)
            self.data = None
            return False
        except ET.ParseError as e:
            logger.error(f"Error parsing IMS XML data: {e}", exc_info=True)
            self.data = None
            return False
        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"Unexpected error during IMS data fetch/parse: {e}", exc_info=True)
            self.data = None
            return False

    def _parse_hebrew_variables(self, root: ET.Element) -> None:
        """
        Parses the Hebrew variable names and descriptions from the XML root element.

        Looks for a specific 'HebrewVariablesNames' tag and extracts the mapping
        between technical variable tags (like 'TD') and their Hebrew text descriptions.
        Stores the results in `self.hebrew_variables`.

        Args:
            root (ET.Element): The root element of the parsed XML document.
        """
        hebrew_section = root.find("HebrewVariablesNames")
        if hebrew_section is not None:
            logger.debug("Parsing Hebrew variable names section...")
            count = 0
            for child in hebrew_section:
                tag = child.tag
                value = child.text.strip() if child.text else ""
                if tag and value:
                    self.hebrew_variables[tag] = value
                    logger.debug(f"  Found Hebrew variable: {tag} = '{value}'")
                    count += 1
            logger.debug(f"Parsed {count} Hebrew variable descriptions.")
        else:
            logger.debug("No 'HebrewVariablesNames' section found in XML.")

    def _find_station_data(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Searches the parsed XML for the observation data matching `self.station_name`.

        Iterates through all 'Observation' elements in the XML root. It first attempts
        an exact, case-insensitive match on the 'stn_name' tag. If no exact match is
        found, it attempts a partial, case-insensitive match (checking if
        `self.station_name` is contained within the 'stn_name' tag text).

        Args:
            root (ET.Element): The root element of the parsed XML document.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the parsed data for the
                                      found station, or None if no matching station
                                      (exact or partial) is found.
        """
        logger.debug(f"Searching for station '{self.station_name}' in observations...")
        station_name_upper = self.station_name.upper()
        target_observation: Optional[ET.Element] = None

        # --- First Pass: Exact Match ---
        for observation in root.findall("Observation"):
            stn_name_elem = observation.find("stn_name")
            if stn_name_elem is not None and stn_name_elem.text:
                current_station_name = stn_name_elem.text.strip().upper()
                if current_station_name == station_name_upper:
                    target_observation = observation
                    logger.debug(f"Found exact match for station: '{stn_name_elem.text}'")
                    break # Stop searching once exact match is found

        # --- Second Pass: Partial Match (if no exact match) ---
        if target_observation is None:
            logger.debug("Exact match not found, trying partial match...")
            for observation in root.findall("Observation"):
                stn_name_elem = observation.find("stn_name")
                if stn_name_elem is not None and stn_name_elem.text:
                    current_station_name = stn_name_elem.text.strip().upper()
                    # Check if the target name is a substring of the current name
                    if station_name_upper in current_station_name:
                        target_observation = observation
                        logger.debug(f"Found partial match for station: '{stn_name_elem.text}' (contains '{self.station_name}')")
                        break # Stop searching once partial match is found

        # --- Process Found Observation or Return None ---
        if target_observation is not None:
            # Extract data from the found observation element
            return self._extract_station_data(target_observation)
        else:
            logger.debug(f"Station '{self.station_name}' not found (neither exact nor partial match).")
            return None # Station not found

    def _extract_station_data(self, observation_elem: ET.Element) -> Dict[str, Any]:
        """
        Extracts all relevant data points from a specific station's 'Observation' XML element.

        Parses metadata (name, number), observation time, and all other child elements
        as measurements. Associates Hebrew descriptions with measurements if available.
        Converts the observation time to Israel timezone.

        Args:
            observation_elem (ET.Element): The 'Observation' XML element corresponding
                                           to the target station.

        Returns:
            Dict[str, Any]: A dictionary structured with 'metadata', 'measurements',
                            'time' (raw/UTC components), and 'time_israel' keys.
        """
        logger.debug("Extracting data from found observation element...")
        metadata: Dict[str, str] = {}
        measurements: Dict[str, Dict[str, Any]] = {}
        time_data: Dict[str, str] = {}

        # Extract metadata fields
        stn_name_elem = observation_elem.find("stn_name")
        stn_num_elem = observation_elem.find("stn_num")
        time_obs_elem = observation_elem.find("time_obs") # Observation time element

        if stn_name_elem is not None and stn_name_elem.text:
            metadata["StationName"] = stn_name_elem.text.strip()
            logger.debug(f"  Extracted StationName: {metadata['StationName']}")
        if stn_num_elem is not None and stn_num_elem.text:
            metadata["StationNumber"] = stn_num_elem.text.strip()
            logger.debug(f"  Extracted StationNumber: {metadata['StationNumber']}")

        # Extract and parse time information (assumed UTC from source)
        if time_obs_elem is not None and time_obs_elem.text:
            time_text = time_obs_elem.text.strip()
            time_data["raw"] = time_text
            logger.debug(f"  Extracted raw time_obs: {time_text}")
            # Attempt to parse the ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
            try:
                # Use datetime.fromisoformat for robust ISO parsing
                dt = datetime.datetime.fromisoformat(time_text)
                # Store components (still UTC at this point)
                time_data["Year"] = str(dt.year)
                time_data["Month"] = str(dt.month).zfill(2) # Pad with zero
                time_data["Day"] = str(dt.day).zfill(2)
                time_data["Hour"] = str(dt.hour).zfill(2)
                time_data["Minute"] = str(dt.minute).zfill(2)
                time_data["Second"] = str(dt.second).zfill(2)
                logger.debug(f"  Parsed time components (UTC): {time_data}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse time_obs '{time_text}' as ISO 8601: {e}")
                # Clear components if parsing failed
                time_data = {"raw": time_text} # Keep only raw value

        # Extract all other child elements as measurements
        measurement_count = 0
        for child in observation_elem:
            tag = child.tag
            # Skip elements already processed or those without text content
            if tag in ["stn_name", "stn_num", "time_obs"] or child.text is None:
                continue

            value = child.text.strip()
            if not value: # Skip empty values
                continue

            # Get Hebrew description from the parsed dictionary
            hebrew_desc = self.hebrew_variables.get(tag, "N/A") # Default to N/A

            measurements[tag] = {
                "value": value,
                "description": hebrew_desc
            }
            logger.debug(f"  Extracted measurement: {tag} = '{value}' (Desc: '{hebrew_desc}')")
            measurement_count += 1
        logger.debug(f"Extracted {measurement_count} measurements.")

        # Assemble the final station data dictionary
        station_data = {
            "metadata": metadata,
            "measurements": measurements,
            "time": time_data # Contains raw and potentially UTC components
        }

        # Convert time to Israel timezone and add it
        station_data["time_israel"] = self._convert_to_israel_time(time_data)
        logger.debug(f"  Converted time to Israel timezone: {station_data['time_israel']}")

        return station_data

    def _convert_to_israel_time(self, time_data: Dict[str, str]) -> Dict[str, str]:
        """
        Converts a dictionary containing UTC time components to Israel time.

        Attempts to parse the 'raw' timestamp if available, otherwise constructs
        a datetime object from individual components ('Year', 'Month', etc.).
        Assumes the input time is UTC. Converts the resulting datetime object
        to the 'Asia/Jerusalem' timezone.

        Args:
            time_data (Dict[str, str]): Dictionary containing UTC time information.
                                        Should ideally have a 'raw' key with an
                                        ISO 8601 timestamp, or individual component
                                        keys ('Year', 'Month', 'Day', etc.).

        Returns:
            Dict[str, str]: A dictionary containing the time components converted
                            to Israel time, including a 'Formatted' key with a
                            standard string representation. Returns the original
                            data with an error key if conversion fails.
        """
        logger.debug(f"Attempting to convert time data to Israel time: {time_data}")
        try:
            utc_dt: Optional[datetime.datetime] = None
            # Prioritize parsing the raw ISO timestamp if available
            if "raw" in time_data:
                try:
                    # Use fromisoformat for robust parsing
                    dt_naive = datetime.datetime.fromisoformat(time_data["raw"])
                    # Assume the naive datetime from IMS is UTC
                    utc_dt = pytz.utc.localize(dt_naive)
                    logger.debug(f"  Parsed raw timestamp '{time_data['raw']}' as UTC: {utc_dt}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"  Could not parse raw timestamp '{time_data['raw']}' as ISO: {e}. Trying components.")
                    # Fallback to constructing from components if raw parsing fails
                    utc_dt = self._construct_datetime_from_components(time_data)
            else:
                # If no raw timestamp, construct directly from components
                logger.debug("  No raw timestamp found, constructing from components.")
                utc_dt = self._construct_datetime_from_components(time_data)

            if utc_dt is None:
                 raise ValueError("Failed to obtain a valid UTC datetime object.")

            # Convert the UTC datetime to the target Israel timezone
            israel_dt = utc_dt.astimezone(self.israel_timezone)
            logger.debug(f"  Converted to Israel time: {israel_dt}")

            # Format the result as a dictionary
            israel_time_dict = {
                "Year": str(israel_dt.year),
                "Month": str(israel_dt.month).zfill(2),
                "Day": str(israel_dt.day).zfill(2),
                "Hour": str(israel_dt.hour).zfill(2),
                "Minute": str(israel_dt.minute).zfill(2),
                "Second": str(israel_dt.second).zfill(2),
                "Formatted": israel_dt.strftime("%Y-%m-%d %H:%M:%S %Z%z") # Include timezone info
            }
            return israel_time_dict

        except Exception as e:
            # Log the error and return original data with an error flag
            logger.error(f"Error converting UTC time to Israel time: {e}", exc_info=True)
            time_data_copy = time_data.copy()
            time_data_copy["Conversion_Error"] = str(e)
            return time_data_copy

    def _construct_datetime_from_components(self, time_data: Dict[str, str]) -> Optional[datetime.datetime]:
        """
        Constructs a timezone-aware datetime object (UTC) from time components.

        Helper method used when a raw timestamp isn't available or parsable.
        Extracts Year, Month, Day, Hour, Minute, Second from the dictionary,
        converts them to integers, and creates a `datetime.datetime` object
        localized to UTC.

        Args:
            time_data (Dict[str, str]): Dictionary potentially containing string
                                        representations of 'Year', 'Month', 'Day',
                                        'Hour', 'Minute', 'Second'.

        Returns:
            Optional[datetime.datetime]: A timezone-aware datetime object set to UTC,
                                         or None if essential components are missing
                                         or invalid.

        Raises:
            ValueError: If required components are missing or cannot be converted
                        to integers.
        """
        logger.debug("Constructing datetime from components...")
        try:
            # Provide defaults in case components are missing, though this might lead to incorrect dates
            year = int(time_data.get("Year", 0))
            month = int(time_data.get("Month", 0))
            day = int(time_data.get("Day", 0))
            # Check if essential components were found
            if year == 0 or month == 0 or day == 0:
                 raise ValueError("Essential date components (Year, Month, Day) missing or invalid.")

            hour = int(time_data.get("Hour", 0))
            minute = int(time_data.get("Minute", 0))
            second = int(time_data.get("Second", 0))

            # Create a naive datetime object first
            dt_naive = datetime.datetime(year, month, day, hour, minute, second)
            # Localize the naive datetime to UTC
            dt_aware_utc = pytz.utc.localize(dt_naive)
            logger.debug(f"  Constructed UTC datetime: {dt_aware_utc}")
            return dt_aware_utc
        except (ValueError, TypeError, KeyError) as e:
            # Log error if components are missing or invalid format
            logger.error(f"Failed to construct datetime from components {time_data}: {e}")
            # Re-raise ValueError to be caught by the calling function (_convert_to_israel_time)
            raise ValueError(f"Invalid or missing time components: {e}") from e
        except Exception as e:
             logger.error(f"Unexpected error constructing datetime: {e}", exc_info=True)
             raise ValueError("Unexpected error during datetime construction") from e


    # --- Public Data Access Methods ---

    def get_all_data(self) -> Optional[Dict[str, Any]]:
        """
        Returns the entire parsed data dictionary for the station.

        This includes metadata, all measurements, and time information (UTC and Israel).
        Returns None if data has not been successfully fetched yet.

        Returns:
            Optional[Dict[str, Any]]: The complete parsed data dictionary, or None.
        """
        if self.data is None:
            logger.warning("Attempted to get_all_data, but data has not been fetched successfully.")
        return self.data

    def get_metadata(self) -> Optional[Dict[str, str]]:
        """
        Returns the station metadata (Name, Number).

        Returns None if data has not been fetched or if metadata is missing.

        Returns:
            Optional[Dict[str, str]]: Dictionary containing 'StationName' and
                                      'StationNumber', or None.
        """
        if not self.data or "metadata" not in self.data:
            logger.warning("Attempted to get_metadata, but data or metadata is missing.")
            return None
        return self.data["metadata"]

    def get_measurement(self, measurement_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns the data for a specific measurement by its tag name.

        Args:
            measurement_name (str): The technical tag name of the measurement
                                    (e.g., 'TD' for temperature, 'RH' for humidity).
                                    Case-sensitive.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the 'value' and
                                      'description' (Hebrew) for the measurement,
                                      or None if the measurement is not found or
                                      data hasn't been fetched.
        """
        if not self.data or "measurements" not in self.data:
            logger.warning(f"Attempted to get_measurement '{measurement_name}', but data or measurements are missing.")
            return None

        measurement_data = self.data["measurements"].get(measurement_name)
        if measurement_data is None:
             logger.debug(f"Measurement '{measurement_name}' not found in fetched data.")
        return measurement_data


    def get_all_measurements(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Returns a dictionary containing all parsed measurements.

        The keys are the measurement tag names (e.g., 'TD', 'RH'), and the values
        are dictionaries containing 'value' and 'description'.

        Returns:
            Optional[Dict[str, Dict[str, Any]]]: Dictionary of all measurements,
                                                 or None if data hasn't been fetched.
        """
        if not self.data or "measurements" not in self.data:
            logger.warning("Attempted to get_all_measurements, but data or measurements are missing.")
            return None
        return self.data["measurements"]

    def get_observation_time(self, israel_time: bool = True) -> Optional[Dict[str, str]]:
        """
        Returns the observation time information.

        Can return either the time converted to Israel timezone or the original
        UTC time components based on the `israel_time` flag.

        Args:
            israel_time (bool): If True (default), returns the time converted to
                                'Asia/Jerusalem'. If False, returns the original
                                UTC time data (components and raw string).

        Returns:
            Optional[Dict[str, str]]: A dictionary containing time information
                                      (components like 'Year', 'Month', etc., and
                                      potentially 'Formatted' or 'raw'), or None if
                                      time data is unavailable. May include a
                                      'Conversion_Error' key if timezone conversion failed.
        """
        if not self.data:
            logger.warning("Attempted to get_observation_time, but data has not been fetched.")
            return None

        if israel_time:
            if "time_israel" in self.data:
                return self.data["time_israel"]
            else:
                 logger.warning("Requested Israel time, but 'time_israel' key is missing in data.")
                 # Fallback to UTC time if Israel time conversion failed or wasn't stored
                 return self.data.get("time")
        else: # Requesting UTC time
            return self.data.get("time")


    def get_hebrew_variables(self) -> Dict[str, str]:
        """
        Returns the dictionary mapping measurement tags to Hebrew descriptions.

        Returns:
            Dict[str, str]: The dictionary of Hebrew variable mappings parsed
                            from the XML feed. May be empty if none were found.
        """
        return self.hebrew_variables

    @classmethod
    def list_all_stations(cls, use_local_file: bool = False, local_file_path: str = "imslasthour.xml") -> Dict[str, Dict[str, str]]:
        """
        Fetches or reads the IMS data feed and lists all unique stations found.

        Provides a way to discover available station names and their associated numbers
        without initializing an instance for a specific station.

        Args:
            use_local_file (bool): If True, reads from `local_file_path`. Defaults to False.
            local_file_path (str): Path to the local XML file if `use_local_file` is True.
                                   Defaults to "imslasthour.xml".

        Returns:
            Dict[str, Dict[str, str]]: A dictionary where keys are unique station names
                                       and values are dictionaries containing station
                                       attributes (currently just 'StationNumber').
                                       Returns an empty dictionary on error.
        """
        logger.info(f"Listing all stations from {'local file' if use_local_file else 'IMS URL'}...")
        root: Optional[ET.Element] = None
        try:
            if use_local_file:
                if not os.path.exists(local_file_path):
                    logger.error(f"Local file not found for listing stations: {local_file_path}")
                    return {}
                tree = ET.parse(local_file_path)
                root = tree.getroot()
            else:
                response = requests.get(cls.IMS_URL, timeout=30)
                response.raise_for_status()
                root = ET.fromstring(response.content)

            if root is None:
                 logger.error("XML root element is None after fetch/parse for listing stations.")
                 return {}

            stations_dict: Dict[str, Dict[str, str]] = {}
            station_count = 0
            unique_station_count = 0

            for observation in root.findall("Observation"):
                station_count += 1
                stn_name_elem = observation.find("stn_name")
                stn_num_elem = observation.find("stn_num")

                if stn_name_elem is not None and stn_name_elem.text:
                    station_name = stn_name_elem.text.strip()
                    if not station_name: continue # Skip if name is empty

                    attributes: Dict[str, str] = {}
                    if stn_num_elem is not None and stn_num_elem.text:
                        attributes["StationNumber"] = stn_num_elem.text.strip()

                    # Add only if station name hasn't been seen before to ensure uniqueness
                    if station_name not in stations_dict:
                        stations_dict[station_name] = attributes
                        unique_station_count += 1

            logger.info(f"Found {unique_station_count} unique stations out of {station_count} observations.")
            return stations_dict

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing stations: {e}", exc_info=True)
            return {}
        except ET.ParseError as e:
            logger.error(f"Error parsing XML for listing stations: {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error listing stations: {e}", exc_info=True)
            return {}


# --- Example Usage (for testing when run directly) ---
if __name__ == "__main__":
    # Configure logging for direct script execution testing
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    import argparse
    import sys

    # --- Command Line Argument Parser ---
    parser = argparse.ArgumentParser(
        description='Fetch and display last hour weather data from Israel Meteorological Service (IMS).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--station',
        type=str,
        default="En Hahoresh", # Default station if none provided
        help='Specific station name to fetch data for (e.g., "Tel Aviv Coast").'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available station names found in the data feed and exit.'
    )
    parser.add_argument(
        '--local',
        action='store_true',
        help='Use a local XML file instead of fetching from the live IMS URL.'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='imslasthour.xml',
        help='Path to the local XML file to use when --local is specified.'
    )

    args = parser.parse_args()

    # --- Execution Logic ---
    use_local = args.local
    local_file = args.file

    # List stations if requested
    if args.list:
        print("Listing all available stations from the IMS feed...")
        stations = IMSLastHourWeather.list_all_stations(use_local_file=use_local, local_file_path=local_file)

        if stations:
            print("\nAvailable stations found:")
            # Sort stations alphabetically by name for readability
            for name, attrs in sorted(stations.items()):
                station_num = attrs.get("StationNumber", "N/A")
                print(f"  - {name} (Number: {station_num})")
        else:
            print("Could not retrieve station list. Check logs for errors.")
            sys.exit(1)
        sys.exit(0) # Exit after listing

    # Fetch data for the specified (or default) station
    station_name = args.station
    print(f"\nFetching weather data for station: '{station_name}'...")
    weather_service = IMSLastHourWeather(station_name)
    success = weather_service.fetch_data(use_local_file=use_local, local_file_path=local_file)

    if success:
        print(f"\n--- Data for Station: {station_name} ---")
        all_data = weather_service.get_all_data()

        # Display Metadata
        metadata = weather_service.get_metadata()
        if metadata:
            print("\n[Station Information]")
            for key, value in metadata.items():
                print(f"  {key}: {value}")

        # Display Observation Time
        time_info_israel = weather_service.get_observation_time(israel_time=True)
        if time_info_israel:
            print("\n[Observation Time (Israel)]")
            if 'Formatted' in time_info_israel:
                print(f"  Formatted: {time_info_israel['Formatted']}")
            else: # Fallback if formatted string isn't available (e.g., conversion error)
                for key, value in time_info_israel.items():
                    print(f"  {key}: {value}")

        # Display Measurements
        measurements = weather_service.get_all_measurements()
        if measurements:
            print("\n[Weather Measurements]")
            # Sort measurements by tag name for consistent output
            for param_name, param_data in sorted(measurements.items()):
                value = param_data.get('value', 'N/A')
                desc = param_data.get('description', 'N/A')
                print(f"  {param_name:<6} ({desc}): {value}") # Pad tag name for alignment

        # Display Hebrew Variable Mappings (Optional)
        # hebrew_vars = weather_service.get_hebrew_variables()
        # if hebrew_vars:
        #     print("\n[Hebrew Variable Descriptions]")
        #     for var_name, var_desc in sorted(hebrew_vars.items()):
        #         print(f"  {var_name}: {var_desc}")

    else:
        print(f"\nFailed to fetch or process data for station '{station_name}'. Check logs for details.")
        sys.exit(1)

    print("\nExecution finished.")
