import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import random
import uuid

# Set page config
st.set_page_config(
    page_title="IoT Factory & Supply Chain Monitoring",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# FACTORY IOT SENSOR PARAMETERS (Original System)
# =============================================================================
SENSOR_RANGES = {
    'Temperature': (20, 80),
    'Vibration': (0, 15),
    'Humidity': (30, 90),
    'Power_Consumption': (100, 300),
    'Pressure': (1, 10),
    'CO2_Levels': (400, 3000),
    'Noise_Levels': (40, 100)
}

SENSOR_UNITS = {
    'Temperature': '°C',
    'Vibration': 'mm/s',
    'Humidity': '%',
    'Power_Consumption': 'kWh',
    'Pressure': 'bar',
    'CO2_Levels': 'ppm',
    'Noise_Levels': 'dB'
}

THRESHOLD_LIMITS = {
    'Temperature': 70,
    'Vibration': 12,
    'Humidity': 85,
    'Power_Consumption': 280,
    'Pressure': 9,
    'CO2_Levels': 2500,
    'Noise_Levels': 90
}

MACHINES = [f'Machine_{i}' for i in range(1, 6)]

# =============================================================================
# SUPPLY CHAIN PARAMETERS
# =============================================================================
WAREHOUSES = ['WH_North', 'WH_South', 'WH_East', 'WH_West', 'WH_Central']
TRUCK_IDS = [f'TRUCK_{i:03d}' for i in range(1, 21)]
SKU_LIST = [f'SKU_{i:04d}' for i in range(1000, 1051)]

# GPS coordinates for realistic trucking routes (US cities)
ROUTE_COORDINATES = [
    (40.7128, -74.0060),   # New York
    (34.0522, -118.2437),  # Los Angeles  
    (41.8781, -87.6298),   # Chicago
    (29.7604, -95.3698),   # Houston
    (33.4484, -112.0740),  # Phoenix
    (39.9526, -75.1652),   # Philadelphia
    (29.4241, -98.4936),   # San Antonio
    (32.7767, -96.7970),   # Dallas
    (37.7749, -122.4194),  # San Francisco
    (47.6062, -122.3321),  # Seattle
]

# =============================================================================
# DATA GENERATION FUNCTIONS
# =============================================================================

@st.cache_data
def generate_factory_sensor_data():
    """Generate simulated IoT sensor data for factory machines (last 7 days) with realistic patterns"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10T')
    
    data = []
    
    # Define machine-specific characteristics for more realistic demo data
    machine_profiles = {
        'Machine_1': {'efficiency': 0.95, 'age': 2, 'maintenance_due': False},  # New, efficient
        'Machine_2': {'efficiency': 0.85, 'age': 5, 'maintenance_due': True},   # Older, needs maintenance
        'Machine_3': {'efficiency': 0.90, 'age': 3, 'maintenance_due': False}, # Average
        'Machine_4': {'efficiency': 0.75, 'age': 8, 'maintenance_due': True},  # Old, problematic
        'Machine_5': {'efficiency': 0.92, 'age': 1, 'maintenance_due': False}  # Almost new
    }
    
    for machine in MACHINES:
        machine_uptime = 0
        daily_uptime_reset = start_time.date()
        profile = machine_profiles[machine]
        
        for i, timestamp in enumerate(timestamps):
            if timestamp.date() != daily_uptime_reset:
                machine_uptime = 0
                daily_uptime_reset = timestamp.date()
            
            # Simulate downtime for maintenance or issues
            is_running = True
            if profile['maintenance_due'] and random.random() < 0.02:  # 2% chance of downtime
                is_running = False
            
            if is_running:
                machine_uptime += 1/6
            
            row = {
                'Timestamp': timestamp,
                'Machine_ID': machine,
                'Machine_Uptime': round(machine_uptime, 2)
            }
            
            for sensor, (min_val, max_val) in SENSOR_RANGES.items():
                if not is_running:
                    # Machine is down - minimal readings
                    if sensor == 'Temperature':
                        value = np.random.uniform(20, 25)  # Ambient temperature
                    elif sensor == 'Power_Consumption':
                        value = np.random.uniform(10, 30)  # Standby power
                    elif sensor == 'Vibration':
                        value = np.random.uniform(0, 1)    # No vibration
                    else:
                        value = min_val + (max_val - min_val) * 0.1
                else:
                    # Normal operation with realistic patterns
                    
                    # Daily cycle (higher activity during work hours)
                    hour_factor = np.sin(2 * np.pi * timestamp.hour / 24) * 0.15
                    if 6 <= timestamp.hour <= 22:  # Work hours
                        hour_factor += 0.2
                    
                    # Weekly cycle (lower on weekends)
                    if timestamp.weekday() >= 5:  # Weekend
                        hour_factor -= 0.1
                    
                    # Machine efficiency impact
                    efficiency_factor = (1 - profile['efficiency']) * 0.3
                    
                    # Age-related degradation
                    age_factor = profile['age'] * 0.02
                    
                    base_value = (min_val + max_val) / 2 + (max_val - min_val) * hour_factor
                    base_value += (max_val - min_val) * (efficiency_factor + age_factor)
                    
                    # Sensor-specific realistic patterns
                    if sensor == 'Temperature':
                        # Temperature correlates with power and activity
                        base_value += np.random.normal(0, 3)
                        if profile['maintenance_due']:
                            base_value += np.random.uniform(2, 8)  # Overheating
                    
                    elif sensor == 'Vibration':
                        # Old machines vibrate more
                        base_value += profile['age'] * 0.5
                        if profile['maintenance_due']:
                            base_value += np.random.uniform(1, 4)  # High vibration
                    
                    elif sensor == 'Power_Consumption':
                        # Inefficient machines consume more power
                        base_value *= (2 - profile['efficiency'])
                    
                    elif sensor == 'Pressure':
                        # Pressure variations for hydraulic systems
                        base_value += np.sin(i * 0.1) * 0.5  # Cyclic pressure
                    
                    elif sensor == 'CO2_Levels':
                        # Higher during work hours, ventilation effects
                        if 8 <= timestamp.hour <= 17:
                            base_value += np.random.uniform(200, 800)
                    
                    elif sensor == 'Noise_Levels':
                        # Correlates with vibration and activity
                        base_value += profile['age'] * 2
                        if profile['maintenance_due']:
                            base_value += np.random.uniform(5, 15)
                    
                    # Add realistic noise
                    noise = np.random.normal(0, (max_val - min_val) * 0.04)
                    
                    # Critical anomalies (equipment failures)
                    if random.random() < 0.01:  # 1% chance of critical anomaly
                        if sensor in ['Temperature', 'Vibration', 'Noise_Levels']:
                            anomaly = np.random.uniform(0.3, 0.7) * (max_val - min_val)
                            noise += anomaly
                    
                    # Minor anomalies
                    elif random.random() < 0.05:  # 5% chance of minor anomaly
                        anomaly = np.random.normal(0, (max_val - min_val) * 0.15)
                        noise += anomaly
                    
                    value = base_value + noise
                    value = np.clip(value, min_val, max_val)
                
                row[sensor] = round(value, 2)
            
            data.append(row)
    
    return pd.DataFrame(data)

@st.cache_data
def generate_cold_chain_data():
    """Generate cold chain monitoring data with realistic shipping scenarios (last 7 days, every 20 minutes)"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='20T')
    
    data = []
    
    # Define shipment types with different temperature requirements
    shipment_types = {
        'SHIP_0100': {'type': 'Frozen', 'target_temp': -18, 'tolerance': 3, 'cargo': 'Ice Cream'},
        'SHIP_0101': {'type': 'Chilled', 'target_temp': 4, 'tolerance': 2, 'cargo': 'Dairy Products'},
        'SHIP_0102': {'type': 'Pharmaceuticals', 'target_temp': 3, 'tolerance': 1, 'cargo': 'Vaccines'},
        'SHIP_0103': {'type': 'Fresh Produce', 'target_temp': 7, 'tolerance': 3, 'cargo': 'Vegetables'},
        'SHIP_0104': {'type': 'Frozen', 'target_temp': -15, 'tolerance': 4, 'cargo': 'Seafood'},
        'SHIP_0105': {'type': 'Chilled', 'target_temp': 2, 'tolerance': 2, 'cargo': 'Fresh Meat'},
        'SHIP_0106': {'type': 'Blood Products', 'target_temp': 5, 'tolerance': 1, 'cargo': 'Blood Bank'},
        'SHIP_0107': {'type': 'Fresh Produce', 'target_temp': 8, 'tolerance': 2, 'cargo': 'Fruits'},
        'SHIP_0108': {'type': 'Frozen', 'target_temp': -20, 'tolerance': 2, 'cargo': 'Medical Samples'},
        'SHIP_0109': {'type': 'Chilled', 'target_temp': 6, 'tolerance': 3, 'cargo': 'Beverages'},
    }
    
    # Route profiles with different challenges
    route_profiles = {
        'Route_A': {'distance': 500, 'duration_hours': 8, 'difficulty': 'Easy'},      # Short local route
        'Route_B': {'distance': 1200, 'duration_hours': 18, 'difficulty': 'Medium'},  # Medium route
        'Route_C': {'distance': 2500, 'duration_hours': 36, 'difficulty': 'Hard'},    # Long cross-country
        'Route_D': {'distance': 800, 'duration_hours': 12, 'difficulty': 'Medium'},   # Mountain route
        'Route_E': {'distance': 300, 'duration_hours': 5, 'difficulty': 'Easy'},      # City delivery
    }
    
    routes = list(route_profiles.keys())
    
    for shipment_id, ship_config in shipment_types.items():
        truck_id = f"TRUCK_{random.randint(1, 20):03d}"
        route = random.choice(routes)
        route_config = route_profiles[route]
        
        # Select random coordinates for this route
        route_coords = list(ROUTE_COORDINATES)
        random.shuffle(route_coords)
        route_coords = route_coords[:4]  # Use 4 waypoints
        
        # Calculate route progress
        total_duration = len(timestamps)
        
        for i, timestamp in enumerate(timestamps):
            # Calculate route progress (0 to 1)
            progress = min(i / (total_duration * 0.8), 1.0)  # 80% of time for delivery
            
            # Interpolate GPS coordinates along route
            if progress < 1.0:
                coord_progress = progress * (len(route_coords) - 1)
                coord_index = int(coord_progress)
                coord_fraction = coord_progress - coord_index
                
                if coord_index < len(route_coords) - 1:
                    lat1, lon1 = route_coords[coord_index]
                    lat2, lon2 = route_coords[coord_index + 1]
                    lat = lat1 + (lat2 - lat1) * coord_fraction
                    lon = lon1 + (lon2 - lon1) * coord_fraction
                else:
                    lat, lon = route_coords[-1]
            else:
                # Delivered - at final destination
                lat, lon = route_coords[-1]
            
            # Add GPS noise
            lat += np.random.normal(0, 0.005)
            lon += np.random.normal(0, 0.005)
            
            # Temperature simulation based on shipment type
            target_temp = ship_config['target_temp']
            tolerance = ship_config['tolerance']
            
            # Base temperature with small variations
            temp_variation = np.random.normal(0, tolerance * 0.3)
            
            # Environmental factors
            hour = timestamp.hour
            
            # Day/night temperature variations (external influence)
            if 12 <= hour <= 16:  # Hot afternoon
                external_influence = np.random.uniform(0.5, 2.0)
            elif 2 <= hour <= 6:   # Cold night
                external_influence = np.random.uniform(-1.0, -0.3)
            else:
                external_influence = np.random.uniform(-0.5, 0.5)
            
            # Route difficulty impact
            if route_config['difficulty'] == 'Hard':
                temp_variation += np.random.uniform(-1, 1.5)  # More temperature fluctuation
            elif route_config['difficulty'] == 'Medium':
                temp_variation += np.random.uniform(-0.5, 1.0)
            
            # Equipment issues (some trucks have problems)
            if truck_id in ['TRUCK_007', 'TRUCK_015', 'TRUCK_018']:  # Problem trucks
                if random.random() < 0.08:  # 8% chance of temperature excursion
                    temp_variation += np.random.uniform(3, 12)
            elif random.random() < 0.02:  # 2% chance for normal trucks
                temp_variation += np.random.uniform(2, 8)
            
            cold_storage_temp = target_temp + temp_variation + external_influence * 0.3
            
            # Humidity simulation (inversely related to temperature for cold storage)
            base_humidity = 65
            humidity_variation = np.random.normal(0, 5)
            
            # Colder temperatures generally have lower humidity in the data
            if cold_storage_temp < 0:
                humidity = base_humidity - 10 + humidity_variation
            else:
                humidity = base_humidity + humidity_variation
            
            humidity = np.clip(humidity, 30, 95)
            
            # Door status simulation (realistic opening patterns)
            door_status = 'closed'
            
            # More likely to open during loading/unloading times
            if progress < 0.05 or progress > 0.95:  # Start or end of journey
                if random.random() < 0.05:  # 5% chance during loading/unloading
                    door_status = 'open'
            elif random.random() < 0.008:  # 0.8% chance during transit
                door_status = 'open'
            
            # Temperature spikes when door opens
            if door_status == 'open':
                if target_temp < 0:  # Frozen goods
                    cold_storage_temp += np.random.uniform(5, 15)
                else:  # Chilled goods
                    cold_storage_temp += np.random.uniform(2, 8)
            
            data.append({
                'timestamp': timestamp,
                'shipment_id': shipment_id,
                'truck_id': truck_id,
                'cargo_type': ship_config['cargo'],
                'route': route,
                'cold_storage_temp': round(cold_storage_temp, 1),
                'humidity': round(humidity, 1),
                'latitude': round(lat, 4),
                'longitude': round(lon, 4),
                'door_status': door_status,
                'route_progress': round(progress * 100, 1)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_warehouse_environmental_data():
    """Generate warehouse environmental monitoring data with realistic operational patterns"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15T')
    
    data = []
    
    # Define warehouse characteristics for realistic demo data
    warehouse_profiles = {
        'WH_North': {
            'type': 'Pharmaceutical Storage',
            'size': 'Large',
            'ventilation': 'Advanced',
            'occupancy_peak': 150,
            'hvac_efficiency': 0.95,
            'issues': []
        },
        'WH_South': {
            'type': 'Food Distribution',
            'size': 'Medium', 
            'ventilation': 'Standard',
            'occupancy_peak': 80,
            'hvac_efficiency': 0.85,
            'issues': ['Old HVAC System']
        },
        'WH_East': {
            'type': 'Electronics Storage',
            'size': 'Small',
            'ventilation': 'Advanced',
            'occupancy_peak': 40,
            'hvac_efficiency': 0.90,
            'issues': []
        },
        'WH_West': {
            'type': 'Chemical Storage',
            'size': 'Large',
            'ventilation': 'Industrial',
            'occupancy_peak': 100,
            'hvac_efficiency': 0.88,
            'issues': ['Ventilation Maintenance Due']
        },
        'WH_Central': {
            'type': 'General Storage',
            'size': 'Medium',
            'ventilation': 'Standard',
            'occupancy_peak': 120,
            'hvac_efficiency': 0.75,
            'issues': ['CO2 Sensor Calibration', 'HVAC Filter Replacement']
        }
    }
    
    for warehouse_id in WAREHOUSES:
        profile = warehouse_profiles[warehouse_id]
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Simulate occupancy patterns (affects CO2 and temperature)
            if day_of_week < 5:  # Weekday
                if 7 <= hour <= 18:  # Work hours
                    occupancy_factor = 0.6 + 0.4 * np.sin(np.pi * (hour - 7) / 11)
                elif 19 <= hour <= 22:  # Evening shift
                    occupancy_factor = 0.3
                else:  # Night
                    occupancy_factor = 0.05
            else:  # Weekend
                occupancy_factor = 0.1 if 9 <= hour <= 15 else 0.02
            
            current_occupancy = int(profile['occupancy_peak'] * occupancy_factor)
            
            # CO2 Level Simulation
            base_co2 = 420  # Outdoor baseline
            
            # Occupancy impact (people generate CO2)
            occupancy_co2 = current_occupancy * np.random.uniform(8, 15)
            
            # Ventilation efficiency impact
            ventilation_efficiency = {
                'Advanced': 0.9, 'Industrial': 0.85, 'Standard': 0.7
            }[profile['ventilation']]
            
            co2_buildup = occupancy_co2 * (1 - ventilation_efficiency)
            
            # HVAC efficiency impact
            hvac_factor = 1 - profile['hvac_efficiency']
            co2_buildup *= (1 + hvac_factor)
            
            # Warehouse-specific issues
            if 'CO2 Sensor Calibration' in profile['issues']:
                co2_buildup *= np.random.uniform(1.2, 1.5)  # Higher readings due to calibration
            
            if 'Ventilation Maintenance Due' in profile['issues']:
                co2_buildup *= np.random.uniform(1.3, 1.8)  # Poor ventilation performance
            
            # Environmental variations
            co2_variation = np.random.normal(0, 50)
            
            # Special events (deliveries, equipment operation)
            if random.random() < 0.15:  # 15% chance of special activity
                co2_variation += np.random.uniform(100, 300)
            
            # Critical CO2 events (ventilation failure)
            if random.random() < 0.008:  # 0.8% chance of critical event
                co2_variation += np.random.uniform(800, 1500)
            
            co2_level = base_co2 + co2_buildup + co2_variation
            co2_level = max(400, co2_level)  # Minimum outdoor level
            
            # Temperature Simulation
            base_temp_target = {
                'Pharmaceutical Storage': 20, 'Food Distribution': 18,
                'Electronics Storage': 22, 'Chemical Storage': 19,
                'General Storage': 21
            }[profile['type']]
            
            # External temperature influence (day/night cycle)
            external_temp_factor = 2 * np.sin(2 * np.pi * (hour - 6) / 24)
            
            # Occupancy heat generation
            occupancy_heat = current_occupancy * 0.1
            
            # HVAC effectiveness
            hvac_control = profile['hvac_efficiency']
            temp_variation = np.random.normal(0, 2 * (1 - hvac_control))
            
            # System issues
            if 'Old HVAC System' in profile['issues']:
                temp_variation += np.random.uniform(-1, 3)  # Less stable temperature
            
            temp_warehouse = (base_temp_target + 
                            external_temp_factor * (1 - hvac_control) + 
                            occupancy_heat * (1 - hvac_control) + 
                            temp_variation)
            
            # Humidity Simulation
            base_humidity = 45
            
            # Seasonal variations
            if timestamp.month in [6, 7, 8]:  # Summer
                humidity_base_adj = 5
            elif timestamp.month in [12, 1, 2]:  # Winter
                humidity_base_adj = -5
            else:
                humidity_base_adj = 0
            
            # Occupancy impact on humidity
            humidity_occupancy = current_occupancy * 0.15
            
            # Ventilation impact
            humidity_control = ventilation_efficiency * 0.8
            humidity_variation = np.random.normal(0, 8 * (1 - humidity_control))
            
            humidity = (base_humidity + humidity_base_adj + 
                       humidity_occupancy * (1 - humidity_control) + 
                       humidity_variation)
            humidity = np.clip(humidity, 20, 90)
            
            # Air Quality Index Simulation
            base_aqi = 25  # Good air quality baseline
            
            # CO2 correlation
            if co2_level > 1000:
                aqi_co2_impact = (co2_level - 1000) * 0.05
            else:
                aqi_co2_impact = 0
            
            # Occupancy and activity impact
            aqi_activity = current_occupancy * 0.3
            
            # Warehouse type impact
            type_aqi_impact = {
                'Chemical Storage': 15, 'Food Distribution': 5,
                'Pharmaceutical Storage': 2, 'Electronics Storage': 3,
                'General Storage': 8
            }[profile['type']]
            
            # Equipment and ventilation impact
            aqi_equipment = np.random.uniform(0, 20) * (1 - ventilation_efficiency)
            
            # Special events (chemical spills, dust, etc.)
            if random.random() < 0.02:  # 2% chance of air quality event
                aqi_equipment += np.random.uniform(30, 80)
            
            aqi_variation = np.random.normal(0, 15)
            
            air_quality_index = (base_aqi + aqi_co2_impact + aqi_activity + 
                               type_aqi_impact + aqi_equipment + aqi_variation)
            air_quality_index = max(0, air_quality_index)
            
            data.append({
                'timestamp': timestamp,
                'warehouse_id': warehouse_id,
                'warehouse_type': profile['type'],
                'current_occupancy': current_occupancy,
                'co2_level_ppm': round(co2_level, 0),
                'temp_warehouse': round(temp_warehouse, 1),
                'humidity': round(humidity, 1),
                'air_quality_index': round(air_quality_index, 0)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_inventory_data():
    """Generate inventory monitoring data with realistic product categories and stock patterns"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7) 
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30T')
    
    data = []
    
    # Define product categories with realistic inventory patterns
    product_categories = {
        'SKU_1001': {'category': 'Electronics', 'product': 'Smartphones', 'velocity': 'High', 'seasonality': 'Low'},
        'SKU_1002': {'category': 'Electronics', 'product': 'Laptops', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1003': {'category': 'Clothing', 'product': 'Winter Jackets', 'velocity': 'Medium', 'seasonality': 'High'},
        'SKU_1004': {'category': 'Food', 'product': 'Canned Goods', 'velocity': 'High', 'seasonality': 'Low'},
        'SKU_1005': {'category': 'Automotive', 'product': 'Brake Pads', 'velocity': 'Low', 'seasonality': 'Low'},
        'SKU_1006': {'category': 'Healthcare', 'product': 'Surgical Masks', 'velocity': 'High', 'seasonality': 'Medium'},
        'SKU_1007': {'category': 'Home & Garden', 'product': 'Garden Tools', 'velocity': 'Medium', 'seasonality': 'High'},
        'SKU_1008': {'category': 'Books', 'product': 'Technical Manuals', 'velocity': 'Low', 'seasonality': 'Low'},
        'SKU_1009': {'category': 'Sports', 'product': 'Fitness Equipment', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1010': {'category': 'Toys', 'product': 'Educational Toys', 'velocity': 'High', 'seasonality': 'High'},
        
        'SKU_1011': {'category': 'Electronics', 'product': 'Tablets', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1012': {'category': 'Clothing', 'product': 'Summer Apparel', 'velocity': 'High', 'seasonality': 'High'},
        'SKU_1013': {'category': 'Food', 'product': 'Frozen Foods', 'velocity': 'High', 'seasonality': 'Low'},
        'SKU_1014': {'category': 'Automotive', 'product': 'Oil Filters', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1015': {'category': 'Healthcare', 'product': 'First Aid Kits', 'velocity': 'Low', 'seasonality': 'Low'},
        'SKU_1016': {'category': 'Home & Garden', 'product': 'Power Tools', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1017': {'category': 'Books', 'product': 'Novels', 'velocity': 'Low', 'seasonality': 'Low'},
        'SKU_1018': {'category': 'Sports', 'product': 'Running Shoes', 'velocity': 'High', 'seasonality': 'Medium'},
        'SKU_1019': {'category': 'Beauty', 'product': 'Skincare Products', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1020': {'category': 'Office', 'product': 'Printer Paper', 'velocity': 'High', 'seasonality': 'Low'},
        
        'SKU_1021': {'category': 'Electronics', 'product': 'Headphones', 'velocity': 'High', 'seasonality': 'Medium'},
        'SKU_1022': {'category': 'Clothing', 'product': 'Work Uniforms', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1023': {'category': 'Food', 'product': 'Snack Foods', 'velocity': 'High', 'seasonality': 'Low'},
        'SKU_1024': {'category': 'Automotive', 'product': 'Tire Gauges', 'velocity': 'Low', 'seasonality': 'Low'},
        'SKU_1025': {'category': 'Healthcare', 'product': 'Thermometers', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1026': {'category': 'Home & Garden', 'product': 'Light Bulbs', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1027': {'category': 'Books', 'product': 'Children Books', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1028': {'category': 'Sports', 'product': 'Yoga Mats', 'velocity': 'Medium', 'seasonality': 'Medium'},
        'SKU_1029': {'category': 'Beauty', 'product': 'Hair Products', 'velocity': 'Medium', 'seasonality': 'Low'},
        'SKU_1030': {'category': 'Office', 'product': 'Staplers', 'velocity': 'Low', 'seasonality': 'Low'},
    }
    
    for sku_id, product_info in product_categories.items():
        warehouse_id = random.choice(WAREHOUSES)
        
        # Set inventory parameters based on product characteristics
        velocity_multipliers = {'High': 3.0, 'Medium': 1.5, 'Low': 0.5}
        velocity = velocity_multipliers[product_info['velocity']]
        
        # Initial stock levels based on velocity
        if product_info['velocity'] == 'High':
            initial_stock = np.random.randint(200, 800)
            reorder_threshold = np.random.randint(50, 150)
        elif product_info['velocity'] == 'Medium':
            initial_stock = np.random.randint(100, 400)
            reorder_threshold = np.random.randint(25, 80)
        else:  # Low velocity
            initial_stock = np.random.randint(50, 200)
            reorder_threshold = np.random.randint(10, 40)
        
        current_stock = initial_stock
        days_since_restock = 0
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Consumption patterns based on time and product type
            consumption_probability = 0.2  # Base 20% chance
            
            # Business hours increase consumption
            if 8 <= hour <= 18 and day_of_week < 5:  # Business hours, weekdays
                consumption_probability *= 1.5
            elif day_of_week >= 5:  # Weekends
                if product_info['category'] in ['Food', 'Electronics', 'Clothing']:
                    consumption_probability *= 1.2  # Consumer goods move more on weekends
                else:
                    consumption_probability *= 0.6  # B2B products move less
            
            # Seasonal effects
            month = timestamp.month
            if product_info['seasonality'] == 'High':
                if product_info['product'] in ['Winter Jackets'] and month in [10, 11, 12, 1, 2]:
                    consumption_probability *= 2.0
                elif product_info['product'] in ['Summer Apparel', 'Garden Tools'] and month in [4, 5, 6, 7, 8]:
                    consumption_probability *= 2.0
                elif product_info['product'] in ['Educational Toys'] and month in [11, 12]:  # Holiday season
                    consumption_probability *= 1.8
            
            # Apply velocity factor
            consumption_probability *= velocity
            
            # Simulate stock consumption
            if random.random() < consumption_probability:
                if product_info['velocity'] == 'High':
                    consumption = np.random.randint(5, 25)
                elif product_info['velocity'] == 'Medium':
                    consumption = np.random.randint(2, 12)
                else:  # Low velocity
                    consumption = np.random.randint(1, 5)
                
                current_stock = max(0, current_stock - consumption)
            
            # Restocking logic
            restock_scheduled = False
            if current_stock <= reorder_threshold:
                restock_scheduled = True
                days_since_restock += 0.5/24  # 30 minutes
                
                # Restocking happens after some delay (1-3 days typically)
                restock_delay_threshold = np.random.uniform(1, 4)  # days
                
                if days_since_restock >= restock_delay_threshold:
                    # Calculate restock quantity
                    if product_info['velocity'] == 'High':
                        restock_quantity = np.random.randint(300, 1000)
                    elif product_info['velocity'] == 'Medium':
                        restock_quantity = np.random.randint(150, 500)
                    else:  # Low velocity
                        restock_quantity = np.random.randint(75, 250)
                    
                    current_stock += restock_quantity
                    restock_scheduled = False
                    days_since_restock = 0
            else:
                days_since_restock = 0
            
            # Emergency stock situations (supplier delays, quality issues)
            if random.random() < 0.001:  # 0.1% chance of supply chain disruption
                current_stock = max(0, int(current_stock * np.random.uniform(0.1, 0.5)))
            
            # Stock adjustments (inventory corrections, damaged goods)
            if random.random() < 0.005:  # 0.5% chance of stock adjustment
                adjustment = np.random.randint(-10, 5)  # Usually losses
                current_stock = max(0, current_stock + adjustment)
            
            data.append({
                'timestamp': timestamp,
                'sku_id': sku_id,
                'product_name': product_info['product'],
                'category': product_info['category'],
                'warehouse_id': warehouse_id,
                'stock_level': current_stock,
                'reorder_threshold': reorder_threshold,
                'restock_scheduled': restock_scheduled,
                'velocity': product_info['velocity'],
                'days_since_restock': round(days_since_restock, 2)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_package_tampering_data():
    """Generate package tampering detection data with realistic shipping scenarios and security events"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='25T')
    
    data = []
    
    # Define package types with different security requirements
    package_types = {
        'PKG_100001': {'type': 'Electronics', 'value': 'High', 'fragile': True, 'security': 'Standard'},
        'PKG_100002': {'type': 'Pharmaceuticals', 'value': 'High', 'fragile': False, 'security': 'High'},
        'PKG_100003': {'type': 'Jewelry', 'value': 'Very High', 'fragile': True, 'security': 'Maximum'},
        'PKG_100004': {'type': 'Documents', 'value': 'Medium', 'fragile': False, 'security': 'High'},
        'PKG_100005': {'type': 'Artwork', 'value': 'Very High', 'fragile': True, 'security': 'Maximum'},
        'PKG_100006': {'type': 'Books', 'value': 'Low', 'fragile': False, 'security': 'Standard'},
        'PKG_100007': {'type': 'Medical Devices', 'value': 'High', 'fragile': True, 'security': 'High'},
        'PKG_100008': {'type': 'Clothing', 'value': 'Medium', 'fragile': False, 'security': 'Standard'},
        'PKG_100009': {'type': 'Chemicals', 'value': 'Medium', 'fragile': False, 'security': 'High'},
        'PKG_100010': {'type': 'Computer Parts', 'value': 'High', 'fragile': True, 'security': 'High'},
        
        'PKG_100011': {'type': 'Watches', 'value': 'Very High', 'fragile': True, 'security': 'Maximum'},
        'PKG_100012': {'type': 'Cosmetics', 'value': 'Medium', 'fragile': False, 'security': 'Standard'},
        'PKG_100013': {'type': 'Rare Coins', 'value': 'Very High', 'fragile': False, 'security': 'Maximum'},
        'PKG_100014': {'type': 'Legal Documents', 'value': 'High', 'fragile': False, 'security': 'High'},
        'PKG_100015': {'type': 'Prototypes', 'value': 'Very High', 'fragile': True, 'security': 'Maximum'},
        'PKG_100016': {'type': 'Textbooks', 'value': 'Low', 'fragile': False, 'security': 'Standard'},
        'PKG_100017': {'type': 'Laboratory Equipment', 'value': 'High', 'fragile': True, 'security': 'High'},
        'PKG_100018': {'type': 'Samples', 'value': 'Medium', 'fragile': True, 'security': 'High'},
        'PKG_100019': {'type': 'Optical Equipment', 'value': 'High', 'fragile': True, 'security': 'High'},
        'PKG_100020': {'type': 'Data Storage', 'value': 'High', 'fragile': False, 'security': 'Maximum'},
    }
    
    # Shipping phase tracking
    shipping_phases = ['Pickup', 'Transit', 'Hub_Processing', 'Last_Mile', 'Delivered']
    
    for package_id, package_info in package_types.items():
        # Determine shipping duration and phases
        total_shipping_time = len(timestamps)
        phase_durations = {
            'Pickup': int(total_shipping_time * 0.05),      # 5% - pickup phase
            'Transit': int(total_shipping_time * 0.60),     # 60% - main transit
            'Hub_Processing': int(total_shipping_time * 0.15), # 15% - hub processing
            'Last_Mile': int(total_shipping_time * 0.15),   # 15% - last mile delivery
            'Delivered': int(total_shipping_time * 0.05)    # 5% - delivered
        }
        
        current_phase = 'Pickup'
        phase_progress = 0
        
        for i, timestamp in enumerate(timestamps):
            # Determine current shipping phase
            total_progress = 0
            for phase, duration in phase_durations.items():
                if i < total_progress + duration:
                    current_phase = phase
                    phase_progress = i - total_progress
                    break
                total_progress += duration
            
            # Base tilt angle (normal handling)
            base_tilt = np.random.uniform(0, 8)
            
            # Phase-specific tilt patterns
            if current_phase == 'Pickup':
                # More movement during pickup
                base_tilt += np.random.uniform(0, 5)
            elif current_phase == 'Transit':
                # Generally stable during transit
                base_tilt += np.random.uniform(0, 3)
                # Occasional road bumps
                if random.random() < 0.05:
                    base_tilt += np.random.uniform(5, 15)
            elif current_phase == 'Hub_Processing':
                # More handling at hubs
                base_tilt += np.random.uniform(0, 8)
                # Sorting equipment can cause tilting
                if random.random() < 0.08:
                    base_tilt += np.random.uniform(10, 25)
            elif current_phase == 'Last_Mile':
                # Local delivery variations
                base_tilt += np.random.uniform(0, 6)
            
            # Package-specific tilt sensitivity
            if package_info['fragile']:
                # Fragile packages are handled more carefully usually
                base_tilt *= 0.8
                # But occasionally get mishandled
                if random.random() < 0.02:
                    base_tilt += np.random.uniform(20, 50)
            
            # Security level impact (higher security = more careful handling)
            security_multipliers = {'Standard': 1.0, 'High': 0.8, 'Maximum': 0.6}
            base_tilt *= security_multipliers[package_info['security']]
            
            # Critical tilt events (drops, mishandling)
            if random.random() < 0.008:  # 0.8% chance of critical tilt event
                base_tilt += np.random.uniform(45, 90)
            
            tilt_angle = base_tilt
            
            # Light exposure simulation
            base_light = np.random.uniform(0, 80)  # Normal warehouse/truck lighting
            
            # Phase-specific light exposure
            if current_phase == 'Pickup':
                base_light += np.random.uniform(50, 200)  # Loading dock lighting
            elif current_phase == 'Hub_Processing':
                base_light += np.random.uniform(100, 300)  # Bright sorting facilities
            elif current_phase == 'Last_Mile':
                # Outdoor delivery lighting
                hour = timestamp.hour
                if 6 <= hour <= 18:  # Daylight
                    base_light += np.random.uniform(200, 800)
                else:  # Night delivery
                    base_light += np.random.uniform(50, 150)
            
            # Unauthorized access attempts (tampering)
            tampering_risk = {'Standard': 0.01, 'High': 0.005, 'Maximum': 0.002}[package_info['security']]
            
            if random.random() < tampering_risk:
                # Tampering attempt detected
                base_light += np.random.uniform(800, 2500)  # Flashlights, bright lights
                base_tilt += np.random.uniform(20, 60)      # Forceful handling
            
            # High-value packages attract more attention
            if package_info['value'] == 'Very High' and random.random() < 0.003:
                base_light += np.random.uniform(500, 1500)
                base_tilt += np.random.uniform(15, 45)
            
            light_exposure = base_light
            
            # Seal status simulation
            seal_status = 'intact'
            
            # Seal failure rate based on package handling and security
            base_seal_failure_rate = 0.001  # 0.1% base rate
            
            # Higher tilt increases seal failure risk
            if tilt_angle > 30:
                base_seal_failure_rate *= 2
            if tilt_angle > 45:
                base_seal_failure_rate *= 3
            
            # High light exposure suggests tampering attempts
            if light_exposure > 1000:
                base_seal_failure_rate *= 5
            
            # Security level affects seal quality
            security_seal_quality = {'Standard': 1.0, 'High': 0.5, 'Maximum': 0.2}
            base_seal_failure_rate *= security_seal_quality[package_info['security']]
            
            # Transportation phase affects seal integrity
            if current_phase == 'Hub_Processing':
                base_seal_failure_rate *= 1.5  # More handling
            
            if random.random() < base_seal_failure_rate:
                seal_status = 'broken'
            
            # Once broken, seal stays broken
            if i > 0:
                prev_data = [d for d in data if d['package_id'] == package_id]
                if prev_data and prev_data[-1]['seal_status'] == 'broken':
                    seal_status = 'broken'
            
            # Environmental factors
            temperature_effect = np.random.uniform(-5, 5)  # Temperature affects sensors
            humidity_effect = np.random.uniform(-2, 2)     # Humidity affects sensors
            
            tilt_angle += temperature_effect * 0.1
            light_exposure += humidity_effect * 2
            
            # Ensure realistic bounds
            tilt_angle = max(0, tilt_angle)
            light_exposure = max(0, light_exposure)
            
            data.append({
                'timestamp': timestamp,
                'package_id': package_id,
                'package_type': package_info['type'],
                'package_value': package_info['value'],
                'security_level': package_info['security'],
                'shipping_phase': current_phase,
                'tilt_angle': round(tilt_angle, 1),
                'light_exposure': round(light_exposure, 0),
                'seal_status': seal_status,
                'is_fragile': package_info['fragile']
            })
    
    return pd.DataFrame(data)

# =============================================================================
# ALERT CHECKING FUNCTIONS
# =============================================================================

def check_factory_alerts(df):
    """Check factory sensor alerts"""
    alerts = []
    latest_data = df.groupby('Machine_ID').last().reset_index()
    
    for _, row in latest_data.iterrows():
        machine = row['Machine_ID']
        for sensor, threshold in THRESHOLD_LIMITS.items():
            if row[sensor] > threshold:
                alerts.append({
                    'type': 'Factory',
                    'machine': machine,
                    'sensor': sensor,
                    'value': row[sensor],
                    'threshold': threshold,
                    'unit': SENSOR_UNITS[sensor]
                })
    
    return alerts

def check_cold_chain_alerts(df):
    """Check cold chain alerts"""
    alerts = []
    latest_data = df.groupby('shipment_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        shipment = row['shipment_id']
        
        # Temperature alert
        if row['cold_storage_temp'] > 8:
            alerts.append({
                'type': 'Cold Chain',
                'shipment': shipment,
                'issue': f"Temperature: {row['cold_storage_temp']}°C (>8°C)",
                'severity': 'High'
            })
        
        # Humidity alert  
        if row['humidity'] > 75:
            alerts.append({
                'type': 'Cold Chain', 
                'shipment': shipment,
                'issue': f"Humidity: {row['humidity']}% (>75%)",
                'severity': 'Medium'
            })
    
    return alerts

def check_warehouse_alerts(df):
    """Check warehouse environmental alerts"""
    alerts = []
    latest_data = df.groupby('warehouse_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        warehouse = row['warehouse_id']
        
        # CO2 alert
        if row['co2_level_ppm'] > 1500:
            alerts.append({
                'type': 'Warehouse',
                'warehouse': warehouse,
                'issue': f"CO2: {row['co2_level_ppm']} ppm (>1500)",
                'severity': 'High'
            })
        
        # Air quality alert
        if row['air_quality_index'] > 100:
            alerts.append({
                'type': 'Warehouse',
                'warehouse': warehouse, 
                'issue': f"AQI: {row['air_quality_index']} (>100)",
                'severity': 'Medium'
            })
    
    return alerts

def check_inventory_alerts(df):
    """Check inventory alerts"""
    alerts = []
    latest_data = df.groupby('sku_id').last().reset_index()
    
    low_stock_items = latest_data[latest_data['stock_level'] <= latest_data['reorder_threshold']]
    
    for _, row in low_stock_items.iterrows():
        alerts.append({
            'type': 'Inventory',
            'sku': row['sku_id'],
            'warehouse': row['warehouse_id'],
            'issue': f"Low Stock: {row['stock_level']} units (threshold: {row['reorder_threshold']})",
            'severity': 'Medium'
        })
    
    return alerts

def check_tampering_alerts(df):
    """Check package tampering alerts"""
    alerts = []
    latest_data = df.groupby('package_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        package = row['package_id']
        
        # Tilt alert
        if row['tilt_angle'] > 45:
            alerts.append({
                'type': 'Tampering',
                'package': package,
                'issue': f"High Tilt: {row['tilt_angle']}° (>45°)",
                'severity': 'High'
            })
        
        # Light exposure alert
        if row['light_exposure'] > 1000:
            alerts.append({
                'type': 'Tampering',
                'package': package,
                'issue': f"Light Exposure: {row['light_exposure']} lux (>1000)",
                'severity': 'High'
            })
        
        # Seal broken alert
        if row['seal_status'] == 'broken':
            alerts.append({
                'type': 'Tampering',
                'package': package,
                'issue': "Seal Status: Broken",
                'severity': 'Critical'
            })
    
    return alerts

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    # Title and header
    st.title("🏭 Comprehensive IoT & Supply Chain Monitoring System")
    st.markdown("Real-time monitoring dashboard for factory operations and supply chain logistics")
    
    # Demo data notice
    with st.expander("📊 About Demo Data", expanded=False):
        st.markdown("""
        **Enhanced Realistic Demo Data Features:**
        
        🏭 **Factory IoT System:**
        - 5 machines with unique profiles (age, efficiency, maintenance status)
        - Realistic sensor patterns with daily/weekly cycles
        - Equipment failures and maintenance downtime simulation
        - Temperature correlations with power consumption and age
        
        🚛 **Cold Chain Monitoring:**
        - 10 different shipment types (frozen, chilled, pharmaceuticals)
        - Realistic temperature requirements (-20°C to +8°C)
        - Route-based GPS tracking with waypoints
        - Temperature excursions during door openings
        - Equipment failure simulation for specific trucks
        
        🧯 **Warehouse Environmental:**
        - 5 warehouses with different characteristics and HVAC systems
        - Occupancy-based CO2 and temperature patterns
        - Ventilation efficiency and maintenance issues
        - Business hours and seasonal variations
        
        📦 **Inventory Management:**
        - 30 products across 10 categories with realistic stock velocities
        - Seasonal demand patterns (winter jackets, garden tools)
        - Supply chain disruptions and stock adjustments
        - Velocity-based consumption patterns (high/medium/low)
        
        📦 **Package Tampering:**
        - 20 packages with different security levels and values
        - Shipping phase tracking (pickup → transit → hub → delivery)
        - Fragile item handling with lower tilt tolerance
        - Security-based seal failure rates and tampering attempts
        """)
    
    # Load all data
    factory_data = generate_factory_sensor_data()
    cold_chain_data = generate_cold_chain_data()
    warehouse_data = generate_warehouse_environmental_data()
    inventory_data = generate_inventory_data()
    tampering_data = generate_package_tampering_data()
    
    # Check all alerts
    factory_alerts = check_factory_alerts(factory_data)
    cold_chain_alerts = check_cold_chain_alerts(cold_chain_data)
    warehouse_alerts = check_warehouse_alerts(warehouse_data)
    inventory_alerts = check_inventory_alerts(inventory_data)
    tampering_alerts = check_tampering_alerts(tampering_data)
    
    all_alerts = factory_alerts + cold_chain_alerts + warehouse_alerts + inventory_alerts + tampering_alerts
    
    # Sidebar
    st.sidebar.header("🔧 System Controls")
    
    # Alert summary in sidebar
    st.sidebar.subheader("🚨 Alert Summary")
    
    alert_counts = {
        'Factory': len(factory_alerts),
        'Cold Chain': len(cold_chain_alerts),
        'Warehouse': len(warehouse_alerts),
        'Inventory': len(inventory_alerts),
        'Tampering': len(tampering_alerts)
    }
    
    for system, count in alert_counts.items():
        if count > 0:
            st.sidebar.error(f"**{system}**: {count} alerts")
        else:
            st.sidebar.success(f"**{system}**: No alerts")
    
    # Show recent critical alerts
    critical_alerts = [a for a in all_alerts if a.get('severity') == 'Critical']
    if critical_alerts:
        st.sidebar.subheader("🔴 Critical Alerts")
        for alert in critical_alerts[:3]:
            st.sidebar.error(f"**{alert['type']}**: {alert['issue']}")
    
    # System selector
    selected_system = st.sidebar.selectbox(
        "Select Monitoring System:",
        ["Factory IoT", "Cold Chain", "Warehouse Environment", "Inventory", "Package Tampering"]
    )
    
    # Create main tabs
    if selected_system == "Factory IoT":
        # Factory IoT tabs (original system)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview", 
            "🧭 Real-Time Monitoring", 
            "📊 Sensor Analytics", 
            "🗺️ Factory Map", 
            "📋 Data Table"
        ])
        
        # Add machine selector for factory system
        selected_machine = st.sidebar.selectbox(
            "Select Machine:",
            ["All Machines"] + MACHINES
        )
        
        # Sensor visibility checkboxes
        st.sidebar.subheader("📊 Sensor Visibility")
        sensor_visibility = {}
        for sensor in SENSOR_RANGES.keys():
            sensor_visibility[sensor] = st.sidebar.checkbox(
                f"{sensor} ({SENSOR_UNITS[sensor]})",
                value=True
            )
        
        # Factory Overview Tab
        with tab1:
            st.markdown("### 📊 Factory System Overview - Key Performance Indicators")
            st.markdown("Average sensor readings across all machines for the past 7 days")
            
            # Calculate averages
            avg_metrics = {}
            for sensor in SENSOR_RANGES.keys():
                avg_metrics[sensor] = factory_data[sensor].mean()
            
            avg_metrics['Machine_Uptime'] = factory_data.groupby(['Machine_ID', factory_data['Timestamp'].dt.date])['Machine_Uptime'].max().mean()
            
            # Display KPIs in columns
            cols = st.columns(4)
            
            sensors_list = list(SENSOR_RANGES.keys()) + ['Machine_Uptime']
            for i, sensor in enumerate(sensors_list):
                col_idx = i % 4
                with cols[col_idx]:
                    unit = SENSOR_UNITS.get(sensor, 'hrs' if sensor == 'Machine_Uptime' else '')
                    value = avg_metrics[sensor]
                    
                    # Color based on thresholds
                    if sensor in THRESHOLD_LIMITS and value > THRESHOLD_LIMITS[sensor]:
                        st.error(f"**{sensor}**\n\n{value:.1f} {unit}")
                    elif sensor in THRESHOLD_LIMITS and value > THRESHOLD_LIMITS[sensor] * 0.8:
                        st.warning(f"**{sensor}**\n\n{value:.1f} {unit}")
                    else:
                        st.success(f"**{sensor}**\n\n{value:.1f} {unit}")
            
            # Overall system health
            st.markdown("### 🎯 Factory System Health")
            factory_critical = len(factory_alerts)
            if factory_critical == 0:
                st.success("✅ All factory systems operating within normal parameters")
            elif factory_critical <= 2:
                st.warning(f"⚠️ {factory_critical} factory sensor(s) require attention")
            else:
                st.error(f"🚨 {factory_critical} critical factory alerts - immediate action required")
        
        # Add other factory tabs here (similar to original implementation)
        with tab2:
            st.markdown("### 🧭 Factory Real-Time Monitoring")
            st.info("Factory real-time monitoring functionality would go here")
        
        with tab3:
            st.markdown("### 📊 Factory Sensor Analytics")
            st.info("Factory sensor analytics would go here")
        
        with tab4:
            st.markdown("### 🗺️ Factory Floor Map")  
            st.info("Factory floor map would go here")
        
        with tab5:
            st.markdown("### 📋 Factory Data Table")
            st.dataframe(factory_data.head(100), use_container_width=True)
    
    elif selected_system == "Cold Chain":
        # Cold Chain Monitoring
        st.header("🚛 Cold Chain Monitoring System")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_shipment = st.selectbox(
                "Filter by Shipment:",
                ["All Shipments"] + sorted(cold_chain_data['shipment_id'].unique().tolist())
            )
        with col2:
            selected_truck = st.selectbox(
                "Filter by Truck:",
                ["All Trucks"] + sorted(cold_chain_data['truck_id'].unique().tolist())
            )
        
        # Filter data
        filtered_cold_chain = cold_chain_data.copy()
        if selected_shipment != "All Shipments":
            filtered_cold_chain = filtered_cold_chain[filtered_cold_chain['shipment_id'] == selected_shipment]
        if selected_truck != "All Trucks":
            filtered_cold_chain = filtered_cold_chain[filtered_cold_chain['truck_id'] == selected_truck]
        
        # Alert banners
        cold_alerts_current = check_cold_chain_alerts(filtered_cold_chain)
        if cold_alerts_current:
            st.warning(f"🚨 {len(cold_alerts_current)} Cold Chain Alerts Active")
            for alert in cold_alerts_current[:3]:
                st.error(f"**{alert['shipment']}**: {alert['issue']}")
        
        # Temperature and Humidity Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp = px.line(
                filtered_cold_chain,
                x='timestamp',
                y='cold_storage_temp',
                color='shipment_id',
                title='Cold Storage Temperature Over Time',
                labels={'cold_storage_temp': 'Temperature (°C)'}
            )
            fig_temp.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Max Temp Threshold (8°C)")
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            fig_humidity = px.line(
                filtered_cold_chain,
                x='timestamp', 
                y='humidity',
                color='shipment_id',
                title='Humidity Levels Over Time',
                labels={'humidity': 'Humidity (%)'}
            )
            fig_humidity.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="Max Humidity Threshold (75%)")
            st.plotly_chart(fig_humidity, use_container_width=True)
        
        # GPS Tracking Map
        st.markdown("### 🗺️ Real-Time GPS Tracking")
        
        # Get latest positions for each shipment
        latest_positions = filtered_cold_chain.groupby('shipment_id').last().reset_index()
        
        if not latest_positions.empty:
            fig_map = px.scatter_mapbox(
                latest_positions,
                lat='latitude',
                lon='longitude',
                color='cold_storage_temp',
                size='humidity',
                hover_data=['shipment_id', 'truck_id', 'door_status'],
                title='Current Shipment Locations',
                mapbox_style='open-street-map',
                height=500,
                color_continuous_scale='RdYlBu_r'
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        
        # Door Opening Events Table
        st.markdown("### 🚪 Recent Door Opening Events")
        door_events = filtered_cold_chain[filtered_cold_chain['door_status'] == 'open'].sort_values('timestamp', ascending=False)
        
        if not door_events.empty:
            st.dataframe(
                door_events[['timestamp', 'shipment_id', 'truck_id', 'cold_storage_temp', 'door_status']].head(20),
                use_container_width=True
            )
        else:
            st.info("No recent door opening events recorded")
    
    elif selected_system == "Warehouse Environment":
        # Warehouse Environmental Monitoring
        st.header("🧯 Warehouse Environmental Monitoring")
        
        # Filters
        selected_warehouse = st.sidebar.selectbox(
            "Filter by Warehouse:",
            ["All Warehouses"] + WAREHOUSES
        )
        
        # Filter data
        filtered_warehouse = warehouse_data.copy()
        if selected_warehouse != "All Warehouses":
            filtered_warehouse = filtered_warehouse[filtered_warehouse['warehouse_id'] == selected_warehouse]
        
        # Alert banners
        warehouse_alerts_current = check_warehouse_alerts(filtered_warehouse)
        if warehouse_alerts_current:
            st.warning(f"🚨 {len(warehouse_alerts_current)} Warehouse Environmental Alerts")
            for alert in warehouse_alerts_current:
                if alert['severity'] == 'High':
                    st.error(f"**{alert['warehouse']}**: {alert['issue']}")
                else:
                    st.warning(f"**{alert['warehouse']}**: {alert['issue']}")
        
        # Environmental metrics
        col1, col2, col3, col4 = st.columns(4)
        
        latest_warehouse_data = filtered_warehouse.groupby('warehouse_id').last().reset_index()
        
        with col1:
            avg_co2 = latest_warehouse_data['co2_level_ppm'].mean()
            if avg_co2 > 1500:
                st.error(f"**CO2 Level**\n\n{avg_co2:.0f} ppm")
            else:
                st.success(f"**CO2 Level**\n\n{avg_co2:.0f} ppm")
        
        with col2:
            avg_temp = latest_warehouse_data['temp_warehouse'].mean()
            st.info(f"**Temperature**\n\n{avg_temp:.1f} °C")
        
        with col3:
            avg_humidity = latest_warehouse_data['humidity'].mean()
            st.info(f"**Humidity**\n\n{avg_humidity:.1f} %")
        
        with col4:
            avg_aqi = latest_warehouse_data['air_quality_index'].mean()
            if avg_aqi > 100:
                st.error(f"**Air Quality**\n\n{avg_aqi:.0f} AQI")
            else:
                st.success(f"**Air Quality**\n\n{avg_aqi:.0f} AQI")
        
        # Environmental Charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_co2 = px.line(
                filtered_warehouse,
                x='timestamp',
                y='co2_level_ppm', 
                color='warehouse_id',
                title='CO2 Levels Over Time',
                labels={'co2_level_ppm': 'CO2 (ppm)'}
            )
            fig_co2.add_hline(y=1500, line_dash="dash", line_color="red", annotation_text="CO2 Alert Threshold")
            st.plotly_chart(fig_co2, use_container_width=True)
        
        with col2:
            fig_aqi = px.area(
                filtered_warehouse,
                x='timestamp',
                y='air_quality_index',
                color='warehouse_id',
                title='Air Quality Index Over Time',
                labels={'air_quality_index': 'AQI'}
            )
            fig_aqi.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Unhealthy AQI Threshold")
            st.plotly_chart(fig_aqi, use_container_width=True)
        
        # Temperature and Humidity Chart
        fig_temp_hum = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Warehouse Temperature', 'Warehouse Humidity'],
            vertical_spacing=0.1
        )
        
        for warehouse in filtered_warehouse['warehouse_id'].unique():
            wh_data = filtered_warehouse[filtered_warehouse['warehouse_id'] == warehouse]
            
            fig_temp_hum.add_trace(
                go.Scatter(
                    x=wh_data['timestamp'],
                    y=wh_data['temp_warehouse'],
                    mode='lines',
                    name=f'{warehouse} - Temp',
                    showlegend=True
                ),
                row=1, col=1
            )
            
            fig_temp_hum.add_trace(
                go.Scatter(
                    x=wh_data['timestamp'],
                    y=wh_data['humidity'],
                    mode='lines',
                    name=f'{warehouse} - Humidity',
                    showlegend=True
                ),
                row=2, col=1
            )
        
        fig_temp_hum.update_layout(height=500, title_text="Temperature and Humidity Monitoring")
        fig_temp_hum.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
        fig_temp_hum.update_yaxes(title_text="Humidity (%)", row=2, col=1)
        
        st.plotly_chart(fig_temp_hum, use_container_width=True)
    
    elif selected_system == "Inventory":
        # Inventory Monitoring
        st.header("📦 Inventory Monitoring System")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_sku = st.selectbox(
                "Filter by SKU:",
                ["All SKUs"] + sorted(inventory_data['sku_id'].unique().tolist())
            )
        with col2:
            selected_inv_warehouse = st.selectbox(
                "Filter by Warehouse:",
                ["All Warehouses"] + WAREHOUSES,
                key="inv_warehouse"
            )
        
        show_restock_schedule = st.checkbox("Show Restocking Schedule", value=True)
        
        # Filter data
        filtered_inventory = inventory_data.copy()
        if selected_sku != "All SKUs":
            filtered_inventory = filtered_inventory[filtered_inventory['sku_id'] == selected_sku]
        if selected_inv_warehouse != "All Warehouses":
            filtered_inventory = filtered_inventory[filtered_inventory['warehouse_id'] == selected_inv_warehouse]
        
        # Get latest inventory levels
        latest_inventory = filtered_inventory.groupby('sku_id').last().reset_index()
        
        # Alert banners
        inventory_alerts_current = [a for a in inventory_alerts if a['sku'] in latest_inventory['sku_id'].values]
        if inventory_alerts_current:
            st.warning(f"🚨 {len(inventory_alerts_current)} Low Stock Alerts")
            
            low_stock_df = pd.DataFrame([
                {
                    'SKU': alert['sku'],
                    'Warehouse': alert['warehouse'],
                    'Current Stock': alert['issue'].split(':')[1].split('units')[0].strip(),
                    'Status': 'LOW STOCK'
                }
                for alert in inventory_alerts_current[:10]
            ])
            st.dataframe(low_stock_df, use_container_width=True)
        
        # Inventory Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_skus = len(latest_inventory)
            st.metric("Total SKUs", total_skus)
        
        with col2:
            low_stock_count = len([a for a in inventory_alerts_current])
            st.metric("Low Stock Items", low_stock_count)
        
        with col3:
            avg_stock = latest_inventory['stock_level'].mean()
            st.metric("Avg Stock Level", f"{avg_stock:.0f}")
        
        with col4:
            restock_needed = latest_inventory['restock_scheduled'].sum()
            st.metric("Restock Scheduled", restock_needed)
        
        # Stock Level vs Reorder Threshold Chart
        if not latest_inventory.empty:
            fig_stock = px.bar(
                latest_inventory.head(20),
                x='sku_id',
                y=['stock_level', 'reorder_threshold'],
                title='Stock Levels vs Reorder Thresholds (Top 20 SKUs)',
                labels={'value': 'Units', 'variable': 'Metric'}
            )
            fig_stock.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_stock, use_container_width=True)
        
        # Stock Movement Over Time
        if selected_sku != "All SKUs":
            sku_data = filtered_inventory[filtered_inventory['sku_id'] == selected_sku]
            
            fig_movement = px.line(
                sku_data,
                x='timestamp',
                y='stock_level',
                title=f'Stock Movement Over Time - {selected_sku}',
                labels={'stock_level': 'Stock Level (Units)'}
            )
            
            # Add reorder threshold line
            threshold = sku_data['reorder_threshold'].iloc[0]
            fig_movement.add_hline(
                y=threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Reorder Threshold ({threshold})"
            )
            
            st.plotly_chart(fig_movement, use_container_width=True)
        
        # Restocking Schedule
        if show_restock_schedule:
            st.markdown("### 📅 Restocking Schedule")
            restock_items = latest_inventory[latest_inventory['restock_scheduled'] == True]
            
            if not restock_items.empty:
                restock_display = restock_items[['sku_id', 'warehouse_id', 'stock_level', 'reorder_threshold']].copy()
                restock_display.columns = ['SKU', 'Warehouse', 'Current Stock', 'Reorder Threshold']
                st.dataframe(restock_display, use_container_width=True)
            else:
                st.info("No items currently scheduled for restocking")
    
    elif selected_system == "Package Tampering":
        # Package Tampering Detection
        st.header("📦 Package Tampering Detection System")
        
        # Filters
        selected_package = st.sidebar.selectbox(
            "Filter by Package:",
            ["All Packages"] + sorted(tampering_data['package_id'].unique().tolist()[:20])  # Show first 20 for performance
        )
        
        # Filter data
        filtered_tampering = tampering_data.copy()
        if selected_package != "All Packages":
            filtered_tampering = filtered_tampering[filtered_tampering['package_id'] == selected_package]
        
        # Get latest tampering data
        latest_tampering = filtered_tampering.groupby('package_id').last().reset_index()
        
        # Alert banners
        tampering_alerts_current = check_tampering_alerts(filtered_tampering)
        if tampering_alerts_current:
            st.error(f"🚨 {len(tampering_alerts_current)} Package Tampering Alerts!")
            
            for alert in tampering_alerts_current[:5]:
                severity_color = "error" if alert['severity'] == 'Critical' else "warning"
                getattr(st, severity_color)(f"**{alert['package']}**: {alert['issue']}")
        
        # Tampering Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_packages = len(latest_tampering)
            st.metric("Total Packages", total_packages)
        
        with col2:
            high_tilt = len(latest_tampering[latest_tampering['tilt_angle'] > 45])
            st.metric("High Tilt Alerts", high_tilt)
        
        with col3:
            high_light = len(latest_tampering[latest_tampering['light_exposure'] > 1000])
            st.metric("Light Exposure Alerts", high_light)
        
        with col4:
            broken_seals = len(latest_tampering[latest_tampering['seal_status'] == 'broken'])
            st.metric("Broken Seals", broken_seals)
        
        # Tampering Detection Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Tilt Angle Scatter Plot
            fig_tilt = px.scatter(
                filtered_tampering,
                x='timestamp',
                y='tilt_angle',
                color='package_id',
                title='Package Tilt Angles Over Time',
                labels={'tilt_angle': 'Tilt Angle (degrees)'}
            )
            fig_tilt.add_hline(y=45, line_dash="dash", line_color="red", annotation_text="Tilt Alert Threshold (45°)")
            st.plotly_chart(fig_tilt, use_container_width=True)
        
        with col2:
            # Light Exposure Chart
            fig_light = px.scatter(
                filtered_tampering,
                x='timestamp',
                y='light_exposure', 
                color='package_id',
                title='Light Exposure Monitoring',
                labels={'light_exposure': 'Light Exposure (lux)'}
            )
            fig_light.add_hline(y=1000, line_dash="dash", line_color="red", annotation_text="Light Alert Threshold (1000 lux)")
            st.plotly_chart(fig_light, use_container_width=True)
        
        # Seal Status Summary
        st.markdown("### 🔒 Seal Status Summary")
        seal_summary = latest_tampering['seal_status'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_seal = px.pie(
                values=seal_summary.values,
                names=seal_summary.index,
                title='Current Seal Status Distribution'
            )
            st.plotly_chart(fig_seal, use_container_width=True)
        
        with col2:
            # Recent seal breaks
            recent_breaks = filtered_tampering[
                (filtered_tampering['seal_status'] == 'broken') & 
                (filtered_tampering['timestamp'] >= filtered_tampering['timestamp'].max() - timedelta(days=1))
            ].sort_values('timestamp', ascending=False)
            
            st.markdown("**Recent Seal Breaks (Last 24h):**")
            if not recent_breaks.empty:
                st.dataframe(
                    recent_breaks[['timestamp', 'package_id', 'tilt_angle', 'light_exposure']].head(10),
                    use_container_width=True
                )
            else:
                st.success("No seal breaks in the last 24 hours")
        
        # Suspected Tampering Events Table
        st.markdown("### 🕵️ Suspected Tampering Events")
        
        suspected_tampering = latest_tampering[
            (latest_tampering['tilt_angle'] > 45) |
            (latest_tampering['light_exposure'] > 1000) |
            (latest_tampering['seal_status'] == 'broken')
        ].sort_values('tilt_angle', ascending=False)
        
        if not suspected_tampering.empty:
            tampering_display = suspected_tampering[['package_id', 'tilt_angle', 'light_exposure', 'seal_status']].copy()
            tampering_display.columns = ['Package ID', 'Tilt Angle (°)', 'Light Exposure (lux)', 'Seal Status']
            
            # Color code the dataframe
            def highlight_tampering(row):
                colors = []
                for col in row.index:
                    if col == 'Tilt Angle (°)' and row[col] > 45:
                        colors.append('background-color: #ffcccc')
                    elif col == 'Light Exposure (lux)' and row[col] > 1000:
                        colors.append('background-color: #ffcccc')
                    elif col == 'Seal Status' and row[col] == 'broken':
                        colors.append('background-color: #ff9999')
                    else:
                        colors.append('')
                return colors
            
            st.dataframe(
                tampering_display.style.apply(highlight_tampering, axis=1),
                use_container_width=True
            )
        else:
            st.success("✅ No suspected tampering events detected")

if __name__ == "__main__":
    main()
