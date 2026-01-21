"""
Timing configuration and transit time calculations for realistic supply chain simulation.

Provides distance-based transit times, processing hold times, and business hour
scheduling to create realistic product flow through the supply chain.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from math import radians, sin, cos, sqrt, atan2
from typing import Optional
import random


@dataclass
class TimingConfig:
    """
    Configuration for realistic timing in supply chain simulation.

    All time values are in hours unless otherwise specified.
    """
    # Transit base times (hours) - minimum time regardless of distance
    farm_to_packer_base_hours: float = 4.0
    packer_to_dc_base_hours: float = 8.0
    dc_to_retail_base_hours: float = 4.0
    processor_to_dc_base_hours: float = 6.0

    # Distance factors (additional hours per 100 miles)
    hours_per_100_miles: float = 2.5

    # Processing/hold times
    cooling_hold_hours: float = 12.0  # Post-harvest cooling before shipping
    packer_processing_hours: float = 4.0  # Packing line processing time
    dc_receiving_inspection_hours: float = 6.0  # QA inspection at DC
    retail_stocking_delay_hours: float = 4.0  # Time to reach shelf after receiving

    # Business hours (24h format)
    business_hours_start: int = 6  # 6 AM
    business_hours_end: int = 18  # 6 PM
    ship_on_weekends: bool = True  # Food supply chain often operates weekends

    # Randomness factor (0 = no randomness, 0.2 = +/- 20%)
    transit_time_variance: float = 0.2

    # Speed factor (multiplier for all transit times, useful for UI control)
    speed_factor: float = 1.0


# City coordinates for realistic distance calculations
# Format: "City, State": (latitude, longitude)
CITY_COORDINATES: dict[str, tuple[float, float]] = {
    # Farm locations (California, Arizona, Florida, Georgia growing regions)
    "Salinas, CA": (36.6777, -121.6555),
    "Yuma, AZ": (32.6927, -114.6277),
    "Fresno, CA": (36.7378, -119.7871),
    "Imperial Valley, CA": (32.8480, -115.5692),
    "Oxnard, CA": (34.1975, -119.1771),
    "Watsonville, CA": (36.9103, -121.7569),
    "Coachella, CA": (33.6803, -116.1739),
    "Gilroy, CA": (37.0058, -121.5683),
    "Santa Maria, CA": (34.9530, -120.4357),
    "Hollister, CA": (36.8525, -121.4016),
    # Arizona farms
    "Nogales, AZ": (31.3404, -110.9343),
    "Willcox, AZ": (32.2528, -109.8320),
    "Buckeye, AZ": (33.3703, -112.5838),
    # Florida farms
    "Immokalee, FL": (26.4187, -81.4173),
    "Homestead, FL": (25.4687, -80.4776),
    # Georgia farms
    "Tifton, GA": (31.4505, -83.5085),
    "Moultrie, GA": (31.1799, -83.7890),

    # Packer locations (Central California)
    "Bakersfield, CA": (35.3733, -119.0187),
    "Stockton, CA": (37.9577, -121.2908),
    "Modesto, CA": (37.6391, -120.9969),
    "Visalia, CA": (36.3302, -119.2921),

    # Distribution Center locations (regional hubs)
    "Phoenix, AZ": (33.4484, -112.0740),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Dallas, TX": (32.7767, -96.7970),
    "Denver, CO": (39.7392, -104.9903),
    "Chicago, IL": (41.8781, -87.6298),
    "Atlanta, GA": (33.7490, -84.3880),
    "Seattle, WA": (47.6062, -122.3321),
    "Portland, OR": (45.5152, -122.6784),
    "Salt Lake City, UT": (40.7608, -111.8910),
    "Albuquerque, NM": (35.0844, -106.6504),

    # Retailer/metropolitan areas
    "San Francisco, CA": (37.7749, -122.4194),
    "San Diego, CA": (32.7157, -117.1611),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Houston, TX": (29.7604, -95.3698),
    "San Antonio, TX": (29.4241, -98.4936),
    "Austin, TX": (30.2672, -97.7431),
    "Minneapolis, MN": (44.9778, -93.2650),
    "Kansas City, MO": (39.0997, -94.5786),
    "St. Louis, MO": (38.6270, -90.1994),
    "Indianapolis, IN": (39.7684, -86.1581),
    "Columbus, OH": (39.9612, -82.9988),
    "Detroit, MI": (42.3314, -83.0458),
    "Milwaukee, WI": (43.0389, -87.9065),
    "Nashville, TN": (36.1627, -86.7816),
    "Memphis, TN": (35.1495, -90.0490),
    "New Orleans, LA": (29.9511, -90.0715),
    "Oklahoma City, OK": (35.4676, -97.5164),
    "Tucson, AZ": (32.2226, -110.9747),
    "Sacramento, CA": (38.5816, -121.4944),
    "Reno, NV": (39.5296, -119.8138),
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Uses the Haversine formula to compute distance in miles.

    Args:
        lat1, lon1: Coordinates of first point in decimal degrees
        lat2, lon2: Coordinates of second point in decimal degrees

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    # Convert to radians
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    # Haversine formula
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def get_city_coordinates(city_state: str) -> Optional[tuple[float, float]]:
    """
    Get coordinates for a city.

    Args:
        city_state: City name in "City, State" format

    Returns:
        (latitude, longitude) tuple or None if not found
    """
    return CITY_COORDINATES.get(city_state)


def calculate_distance_between_cities(city1: str, city2: str) -> float:
    """
    Calculate distance in miles between two cities.

    Args:
        city1, city2: City names in "City, State" format

    Returns:
        Distance in miles, or 100.0 as default if cities not found
    """
    coords1 = get_city_coordinates(city1)
    coords2 = get_city_coordinates(city2)

    if coords1 is None or coords2 is None:
        # Default distance if coordinates not available
        return 100.0

    return haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])


def calculate_transit_time(
    config: TimingConfig,
    distance_miles: float,
    base_hours: float,
    random_seed: Optional[int] = None
) -> timedelta:
    """
    Calculate transit time based on distance and configuration.

    Args:
        config: Timing configuration
        distance_miles: Distance in miles
        base_hours: Base transit time in hours (minimum)
        random_seed: Optional seed for reproducibility

    Returns:
        Transit time as timedelta
    """
    if random_seed is not None:
        random.seed(random_seed)

    # Calculate base time plus distance factor
    hours = base_hours + (distance_miles / 100) * config.hours_per_100_miles

    # Apply speed factor
    hours *= config.speed_factor

    # Add randomness
    if config.transit_time_variance > 0:
        variance = config.transit_time_variance
        hours *= random.uniform(1 - variance, 1 + variance)

    return timedelta(hours=hours)


def get_random_business_hour(
    base_date: datetime,
    config: TimingConfig,
    random_seed: Optional[int] = None
) -> datetime:
    """
    Get a random datetime within business hours on the given date.

    Args:
        base_date: Date to use (time component ignored)
        config: Timing configuration
        random_seed: Optional seed for reproducibility

    Returns:
        Datetime with random business hour on the given date
    """
    if random_seed is not None:
        random.seed(random_seed)

    # Random hour within business hours
    hour = random.randint(config.business_hours_start, config.business_hours_end - 1)
    minute = random.randint(0, 59)

    return datetime.combine(base_date.date(), time(hour=hour, minute=minute))


def advance_to_next_business_hour(
    dt: datetime,
    config: TimingConfig
) -> datetime:
    """
    Advance a datetime to the next valid business hour.

    If the datetime is within business hours, return it unchanged.
    Otherwise, advance to the start of the next business day.

    Args:
        dt: Input datetime
        config: Timing configuration

    Returns:
        Datetime at or after input, within business hours
    """
    current_hour = dt.hour
    current_weekday = dt.weekday()  # 0 = Monday, 6 = Sunday

    # Check if weekend and weekends not allowed
    is_weekend = current_weekday >= 5
    if is_weekend and not config.ship_on_weekends:
        # Advance to Monday
        days_until_monday = 7 - current_weekday
        dt = dt + timedelta(days=days_until_monday)
        return datetime.combine(dt.date(), time(hour=config.business_hours_start))

    # Check if before business hours
    if current_hour < config.business_hours_start:
        return datetime.combine(dt.date(), time(hour=config.business_hours_start))

    # Check if after business hours
    if current_hour >= config.business_hours_end:
        # Advance to next day
        next_day = dt + timedelta(days=1)

        # Check if next day is weekend
        if next_day.weekday() >= 5 and not config.ship_on_weekends:
            days_until_monday = 7 - next_day.weekday()
            next_day = next_day + timedelta(days=days_until_monday)

        return datetime.combine(next_day.date(), time(hour=config.business_hours_start))

    # Already within business hours
    return dt


def calculate_farm_to_packer_transit(
    config: TimingConfig,
    distance_miles: float
) -> timedelta:
    """Calculate transit time from farm to packer."""
    return calculate_transit_time(
        config,
        distance_miles,
        config.farm_to_packer_base_hours
    )


def calculate_packer_to_dc_transit(
    config: TimingConfig,
    distance_miles: float
) -> timedelta:
    """Calculate transit time from packer to distribution center."""
    return calculate_transit_time(
        config,
        distance_miles,
        config.packer_to_dc_base_hours
    )


def calculate_dc_to_retail_transit(
    config: TimingConfig,
    distance_miles: float
) -> timedelta:
    """Calculate transit time from DC to retailer."""
    return calculate_transit_time(
        config,
        distance_miles,
        config.dc_to_retail_base_hours
    )


def calculate_processor_to_dc_transit(
    config: TimingConfig,
    distance_miles: float
) -> timedelta:
    """Calculate transit time from processor to DC."""
    return calculate_transit_time(
        config,
        distance_miles,
        config.processor_to_dc_base_hours
    )


def calculate_total_supply_chain_time(
    config: TimingConfig,
    farm_to_packer_miles: float,
    packer_to_dc_miles: float,
    dc_to_retail_miles: float
) -> timedelta:
    """
    Calculate total time for product to flow from farm to retail.

    Includes all transit times and hold times.

    Args:
        config: Timing configuration
        farm_to_packer_miles: Distance from farm to packer
        packer_to_dc_miles: Distance from packer to DC
        dc_to_retail_miles: Distance from DC to retailer

    Returns:
        Total supply chain transit time
    """
    total = timedelta()

    # Farm operations
    total += timedelta(hours=config.cooling_hold_hours)

    # Farm to packer transit
    total += calculate_farm_to_packer_transit(config, farm_to_packer_miles)

    # Packer processing
    total += timedelta(hours=config.packer_processing_hours)

    # Packer to DC transit
    total += calculate_packer_to_dc_transit(config, packer_to_dc_miles)

    # DC receiving inspection
    total += timedelta(hours=config.dc_receiving_inspection_hours)

    # DC to retail transit
    total += calculate_dc_to_retail_transit(config, dc_to_retail_miles)

    # Retail stocking
    total += timedelta(hours=config.retail_stocking_delay_hours)

    return total
