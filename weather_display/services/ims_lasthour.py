"""
IMS Weather Last Hour Data Parser

This module provides a class to retrieve and parse the last hour weather data
from the Israel Meteorological Service (IMS).
"""
import xml.etree.ElementTree as ET
import requests
import os
import datetime
import pytz
from typing import Dict, Any, Optional, List, Set, Tuple


class IMSLastHourWeather:
    """
    Class to fetch and parse last hour weather data from the Israel Meteorological Service.
    
    This class retrieves XML data from the IMS website's last hour data feed, 
    parses it, and extracts data for a specific station.
    """
    
    IMS_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/imslasthour.xml"
    DEBUG = True  # Enable debug mode
    
    def __init__(self, station_name: str):
        """
        Initialize the IMSLastHourWeather class with a station name.
        
        Args:
            station_name: The weather station name to retrieve data for
        """
        self.station_name = station_name
        self.data = None
        self.hebrew_variables = {}  # Will store Hebrew variable names and meanings
        self.israel_timezone = pytz.timezone('Asia/Jerusalem')
        
    def fetch_data(self, use_local_file: bool = False, local_file_path: str = "imslasthour.xml") -> bool:
        """
        Fetch the XML last hour weather data from IMS website or local file.
        
        Args:
            use_local_file: Whether to use a local XML file instead of fetching from the URL
            local_file_path: Path to the local XML file
        
        Returns:
            bool: True if data was successfully fetched, False otherwise
        """
        try:
            if use_local_file:
                if self.DEBUG:
                    print(f"Using local file: {local_file_path}")
                
                if not os.path.exists(local_file_path):
                    print(f"Local file not found: {local_file_path}")
                    return False
                
                # Parse the local XML file
                tree = ET.parse(local_file_path)
                root = tree.getroot()
            else:
                if self.DEBUG:
                    print(f"Fetching data from URL: {self.IMS_URL}")
                
                response = requests.get(self.IMS_URL, timeout=30)
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Parse the XML content
                root = ET.fromstring(response.content)
            
            # Parse Hebrew variable names if available
            self._parse_hebrew_variables(root)
            
            # Find the station and extract data
            station_data = self._find_station_data(root)
            
            if station_data:
                self.data = station_data
                return True
            else:
                print(f"Station '{self.station_name}' not found in the data")
                return False
            
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return False
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def _parse_hebrew_variables(self, root: ET.Element) -> None:
        """
        Parse Hebrew variable names and their meanings from the XML.
        
        Args:
            root: The root XML element
        """
        hebrew_section = root.find("HebrewVariablesNames")
        if hebrew_section is not None:
            for child in hebrew_section:
                tag = child.tag
                value = child.text
                if tag and value:
                    self.hebrew_variables[tag] = value
                    if self.DEBUG:
                        print(f"Hebrew variable: {tag} = {value}")
    
    def _find_station_data(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Find and extract data for the specified station.
        
        Args:
            root: The root XML element
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing station data or None if not found
        """
        # Case-insensitive station name comparison
        station_name_upper = self.station_name.upper()
        target_observation = None
        
        for observation in root.findall("Observation"):
            stn_name_elem = observation.find("stn_name")
            if stn_name_elem is not None and stn_name_elem.text and stn_name_elem.text.upper() == station_name_upper:
                target_observation = observation
                break
        
        if target_observation is None:
            # Try partial match if exact match not found
            for observation in root.findall("Observation"):
                stn_name_elem = observation.find("stn_name")
                if (stn_name_elem is not None and stn_name_elem.text and 
                    station_name_upper in stn_name_elem.text.upper()):
                    target_observation = observation
                    if self.DEBUG:
                        print(f"Found partial match: {stn_name_elem.text}")
                    break
        
        if target_observation is None:
            return None
        
        # Extract all station data
        return self._extract_station_data(target_observation)
    
    def _extract_station_data(self, observation_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract all data from an observation element.
        
        Args:
            observation_elem: The observation XML element
            
        Returns:
            Dict[str, Any]: Dictionary containing all station data
        """
        metadata = {}
        measurements = {}
        time_data = {}
        
        # Extract metadata (station name and number)
        stn_name_elem = observation_elem.find("stn_name")
        stn_num_elem = observation_elem.find("stn_num")
        time_obs_elem = observation_elem.find("time_obs")
        
        if stn_name_elem is not None and stn_name_elem.text:
            metadata["StationName"] = stn_name_elem.text
        
        if stn_num_elem is not None and stn_num_elem.text:
            metadata["StationNumber"] = stn_num_elem.text
        
        # Extract time information
        if time_obs_elem is not None and time_obs_elem.text:
            time_text = time_obs_elem.text
            time_data["raw"] = time_text
            
            # Try to parse ISO format (2025-04-13T14:00:00)
            try:
                dt = datetime.datetime.strptime(time_text, "%Y-%m-%dT%H:%M:%S")
                time_data["Year"] = str(dt.year)
                time_data["Month"] = str(dt.month)
                time_data["Day"] = str(dt.day)
                time_data["Hour"] = str(dt.hour)
                time_data["Minute"] = str(dt.minute)
                time_data["Second"] = str(dt.second)
            except (ValueError, TypeError):
                pass
        
        # Extract all other elements as measurements
        for child in observation_elem:
            tag = child.tag
            # Skip elements already processed or empty values
            if tag in ["stn_name", "stn_num", "time_obs"] or not child.text:
                continue
            
            value = child.text
            
            # Get Hebrew description if available
            hebrew_desc = self.hebrew_variables.get(tag, "")
            
            measurements[tag] = {
                "value": value,
                "description": hebrew_desc
            }
        
        station_data = {
            "metadata": metadata,
            "measurements": measurements,
            "time": time_data
        }
        
        # Add Israeli time
        station_data["time_israel"] = self._convert_to_israel_time(time_data)
        
        return station_data
    
    def _convert_to_israel_time(self, time_data: Dict[str, str]) -> Dict[str, str]:
        """
        Convert UTC time data to Israel time.
        
        Args:
            time_data: Dictionary containing time components in UTC
            
        Returns:
            Dict[str, str]: Dictionary with Israel time components
        """
        try:
            # Check if we have a raw timestamp
            if "raw" in time_data:
                try:
                    # Try to parse ISO format
                    if "T" in time_data["raw"]:
                        dt = datetime.datetime.strptime(time_data["raw"], "%Y-%m-%dT%H:%M:%S")
                    else:
                        # Try standard format
                        dt = datetime.datetime.strptime(time_data["raw"], "%Y-%m-%d %H:%M:%S")
                    
                    # Assume UTC if timezone not specified
                    utc_dt = dt.replace(tzinfo=pytz.UTC)
                except (ValueError, TypeError):
                    # If parsing fails, try to construct from components
                    utc_dt = self._construct_datetime_from_components(time_data)
            else:
                # Construct from components
                utc_dt = self._construct_datetime_from_components(time_data)
            
            # Convert to Israel time
            israel_dt = utc_dt.astimezone(self.israel_timezone)
            
            # Format result as dictionary
            israel_time = {
                "Year": str(israel_dt.year),
                "Month": str(israel_dt.month),
                "Day": str(israel_dt.day),
                "Hour": str(israel_dt.hour),
                "Minute": str(israel_dt.minute),
                "Second": str(israel_dt.second),
                "Formatted": israel_dt.strftime("%Y-%m-%d %H:%M:%S %Z%z")
            }
            return israel_time
        except Exception as e:
            if self.DEBUG:
                print(f"Error converting to Israel time: {e}")
            # Return original data with error flag
            time_data_copy = time_data.copy()
            time_data_copy["Conversion_Error"] = str(e)
            return time_data_copy
    
    def _construct_datetime_from_components(self, time_data: Dict[str, str]) -> datetime.datetime:
        """
        Construct a datetime object from time components.
        
        Args:
            time_data: Dictionary containing time components
            
        Returns:
            datetime.datetime: A datetime object with timezone (UTC)
            
        Raises:
            ValueError: If required components are missing or invalid
        """
        try:
            year = int(time_data.get("Year", 2000))
            month = int(time_data.get("Month", 1))
            day = int(time_data.get("Day", 1))
            hour = int(time_data.get("Hour", 0))
            minute = int(time_data.get("Minute", 0))
            second = int(time_data.get("Second", 0))
            
            # Create UTC datetime object
            return datetime.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to construct datetime: {e}")
    
    def get_all_data(self) -> Optional[Dict[str, Any]]:
        """
        Get all available data for the station.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing all station data or None if not available
        """
        return self.data
    
    def get_metadata(self) -> Optional[Dict[str, str]]:
        """
        Get station metadata.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing station metadata or None if not available
        """
        if not self.data or "metadata" not in self.data:
            return None
            
        return self.data["metadata"]
    
    def get_measurement(self, measurement_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific measurement's data.
        
        Args:
            measurement_name: The name of the measurement
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing measurement data or None if not found
        """
        if not self.data or "measurements" not in self.data:
            return None
            
        return self.data["measurements"].get(measurement_name)
    
    def get_all_measurements(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get all measurements.
        
        Returns:
            Optional[Dict[str, Dict[str, Any]]]: Dictionary containing all measurements or None if not available
        """
        if not self.data or "measurements" not in self.data:
            return None
            
        return self.data["measurements"]
    
    def get_observation_time(self, israel_time: bool = True) -> Optional[Dict[str, str]]:
        """
        Get observation time information.
        
        Args:
            israel_time: Whether to return time in Israel timezone (True) or UTC (False)
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing time information or None if not available
        """
        if not self.data:
            return None
            
        if israel_time and "time_israel" in self.data:
            return self.data["time_israel"]
        elif "time" in self.data:
            return self.data["time"]
        
        return None
    
    def get_hebrew_variables(self) -> Dict[str, str]:
        """
        Get the dictionary of Hebrew variable names and their meanings.
        
        Returns:
            Dict[str, str]: Dictionary mapping variable names to their Hebrew descriptions
        """
        return self.hebrew_variables
    
    @classmethod
    def list_all_stations(cls, use_local_file: bool = False, local_file_path: str = "imslasthour.xml") -> Dict[str, Dict[str, str]]:
        """
        List all available stations with their attributes.
        
        Args:
            use_local_file: Whether to use a local XML file instead of fetching from the URL
            local_file_path: Path to the local XML file
            
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping station names to their attribute dictionaries
        """
        try:
            if use_local_file:
                if not os.path.exists(local_file_path):
                    print(f"Local file not found: {local_file_path}")
                    return {}
                
                # Parse the local XML file
                tree = ET.parse(local_file_path)
                root = tree.getroot()
            else:
                response = requests.get(cls.IMS_URL, timeout=30)
                response.raise_for_status()
                root = ET.fromstring(response.content)
            
            stations_dict = {}
            
            for observation in root.findall("Observation"):
                stn_name_elem = observation.find("stn_name")
                stn_num_elem = observation.find("stn_num")
                
                if stn_name_elem is not None and stn_name_elem.text:
                    station_name = stn_name_elem.text
                    attributes = {}
                    
                    if stn_num_elem is not None and stn_num_elem.text:
                        attributes["StationNumber"] = stn_num_elem.text
                    
                    # Add only if not already in the dictionary (to avoid duplicates)
                    if station_name not in stations_dict:
                        stations_dict[station_name] = attributes
            
            return stations_dict
            
        except Exception as e:
            print(f"Error listing stations: {e}")
            return {}


# Example usage for testing
if __name__ == "__main__":
    import argparse
    import sys
    
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='Fetch last hour weather data from Israel Meteorological Service')
    parser.add_argument('--station', type=str, help='Station name to fetch data for')
    parser.add_argument('--list', action='store_true', help='List all available stations')
    parser.add_argument('--local', action='store_true', help='Use local XML file instead of fetching from URL')
    parser.add_argument('--file', type=str, default='imslasthour.xml', help='Path to local XML file (default: imslasthour.xml)')
    
    args = parser.parse_args()
    
    # Check if we need to use local file
    use_local = args.local
    local_file = args.file
    
    # List all stations if requested
    if args.list or args.station is None:
        print("Listing all available stations...")
        stations = IMSLastHourWeather.list_all_stations(use_local_file=use_local, local_file_path=local_file)
        
        if stations:
            print("\nAvailable stations:")
            for name, attrs in sorted(stations.items()):
                print(f"  Station: {name}")
                for key, value in attrs.items():
                    print(f"    {key}: {value}")
        else:
            print("No stations found or error occurred")
            sys.exit(1)
    
    # If no station specified and not just listing, use default "En Hahoresh"
    if args.station is None and not args.list:
        station_name = "En Hahoresh"  # Default to "En Hahoresh" station
        print(f"\nUsing default station: {station_name}")
    else:
        station_name = args.station
    
    # If we're not just listing stations, fetch data for the specified station
    if not args.list and station_name is not None:
        print(f"\nFetching data for station '{station_name}'...")
        weather = IMSLastHourWeather(station_name)
        success = weather.fetch_data(use_local_file=use_local, local_file_path=local_file)
        
        if success:
            station_data = weather.get_all_data()
            metadata = weather.get_metadata()
            time_info = weather.get_observation_time(israel_time=True)
            
            if metadata:
                print("\nStation Information:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
            
            if time_info:
                print("\nObservation Time (Israel Time):")
                if 'Formatted' in time_info:
                    print(f"  {time_info['Formatted']}")
                else:
                    for key, value in time_info.items():
                        if key != 'Conversion_Error':
                            print(f"  {key}: {value}")
                    if 'Conversion_Error' in time_info:
                        print(f"  Warning: {time_info['Conversion_Error']}")
            
            if 'measurements' in station_data:
                print("\nWeather Measurements:")
                for param_name, param_data in station_data['measurements'].items():
                    value = param_data['value']
                    desc = param_data['description']
                    
                    print(f"  {param_name} ({desc}): {value}")
            
            # Show Hebrew variable mappings
            hebrew_vars = weather.get_hebrew_variables()
            if hebrew_vars:
                print("\nHebrew Variable Descriptions:")
                for var_name, var_desc in hebrew_vars.items():
                    print(f"  {var_name}: {var_desc}")
        else:
            print(f"Failed to fetch data for station '{station_name}'")
            sys.exit(1)
