import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import time
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="IIoT & Supply Chain Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

# Machine and facility configurations
MACHINES = [f'Machine_{i:02d}' for i in range(1, 11)]
PRODUCTION_LINES = [f'Line_{chr(65+i)}' for i in range(5)]  # Line_A to Line_E
FACTORY_ZONES = [f'Zone_{i}' for i in range(1, 8)]
WAREHOUSES = [f'WH_{i:03d}' for i in range(1, 6)]
SHIPMENTS = [f'SHIP_{i:04d}' for i in range(1000, 1021)]
TRUCKS = [f'TRUCK_{i:03d}' for i in range(1, 16)]
SKUS = [f'SKU_{i:04d}' for i in range(2000, 2051)]
PACKAGES = [f'PKG_{i:06d}' for i in range(500000, 500101)]

# GPS coordinates for realistic truck routes
GPS_ROUTES = [
    (40.7128, -74.0060),   # New York
    (34.0522, -118.2437),  # Los Angeles
    (41.8781, -87.6298),   # Chicago
    (29.7604, -95.3698),   # Houston
    (33.4484, -112.0740),  # Phoenix
    (39.9526, -75.1652),   # Philadelphia
    (32.7767, -96.7970),   # Dallas
    (37.7749, -122.4194),  # San Francisco
    (47.6062, -122.3321),  # Seattle
    (25.7617, -80.1918),   # Miami
]

# =============================================================================
# DATA GENERATION FUNCTIONS
# =============================================================================

@st.cache_data
def generate_predictive_maintenance_data():
    """Generate predictive maintenance data for machines"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='12T')
    
    data = []
    
    # Machine profiles with different health conditions
    machine_profiles = {
        'Machine_01': {'health': 'excellent', 'age_months': 6},
        'Machine_02': {'health': 'good', 'age_months': 18},
        'Machine_03': {'health': 'warning', 'age_months': 36},
        'Machine_04': {'health': 'critical', 'age_months': 60},
        'Machine_05': {'health': 'good', 'age_months': 12},
        'Machine_06': {'health': 'excellent', 'age_months': 3},
        'Machine_07': {'health': 'warning', 'age_months': 42},
        'Machine_08': {'health': 'good', 'age_months': 24},
        'Machine_09': {'health': 'critical', 'age_months': 72},
        'Machine_10': {'health': 'excellent', 'age_months': 9},
    }
    
    for machine_id in MACHINES:
        profile = machine_profiles[machine_id]
        runtime_hours = profile['age_months'] * 30 * 16  # Assuming 16 hours/day operation
        
        for timestamp in timestamps:
            # Base values depending on machine health
            if profile['health'] == 'excellent':
                base_vibration = np.random.uniform(2, 6)
                base_temp = np.random.uniform(45, 65)
                base_failure_risk = np.random.uniform(5, 15)
            elif profile['health'] == 'good':
                base_vibration = np.random.uniform(4, 8)
                base_temp = np.random.uniform(50, 70)
                base_failure_risk = np.random.uniform(15, 30)
            elif profile['health'] == 'warning':
                base_vibration = np.random.uniform(6, 11)
                base_temp = np.random.uniform(60, 78)
                base_failure_risk = np.random.uniform(30, 55)
            else:  # critical
                base_vibration = np.random.uniform(9, 15)
                base_temp = np.random.uniform(70, 85)
                base_failure_risk = np.random.uniform(55, 85)
            
            # Add operational patterns (higher during work hours)
            hour = timestamp.hour
            if 6 <= hour <= 22:  # Operating hours
                operational_factor = 1.0 + 0.2 * np.sin(np.pi * (hour - 6) / 16)
            else:  # Maintenance/idle time
                operational_factor = 0.3
            
            vibration_rms = base_vibration * operational_factor + np.random.normal(0, 0.5)
            temperature_C = base_temp * operational_factor + np.random.normal(0, 2)
            
            # Failure risk calculation based on thresholds
            failure_risk_score = base_failure_risk
            if vibration_rms > 12:
                failure_risk_score += (vibration_rms - 12) * 5
            if temperature_C > 80:
                failure_risk_score += (temperature_C - 80) * 3
            
            failure_risk_score = min(100, max(0, failure_risk_score))
            runtime_hours += 0.2  # Increment runtime
            
            data.append({
                'timestamp': timestamp,
                'machine_id': machine_id,
                'vibration_rms': round(vibration_rms, 2),
                'temperature_C': round(temperature_C, 1),
                'runtime_hours': round(runtime_hours, 1),
                'failure_risk_score': round(failure_risk_score, 1),
                'health_status': profile['health']
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_machine_status_data():
    """Generate machine status monitoring data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10T')
    
    data = []
    
    for machine_id in MACHINES:
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Determine if machine should be running
            if day_of_week < 5:  # Weekdays
                if 6 <= hour <= 22:  # Work hours
                    # 95% chance of running during work hours
                    is_running = random.random() < 0.95
                else:  # Off hours
                    # 10% chance of running (maintenance, night shift)
                    is_running = random.random() < 0.10
            else:  # Weekends
                # 30% chance of running on weekends
                is_running = random.random() < 0.30
            
            if is_running:
                status = 'Running'
                rpm = np.random.uniform(1200, 1800) + np.sin(timestamp.hour * np.pi / 12) * 100
                energy_kWh = np.random.uniform(15, 25) + np.random.normal(0, 2)
            else:
                status = 'Stopped'
                rpm = 0
                energy_kWh = np.random.uniform(0.5, 2.0)  # Standby power
            
            # Add some variability for running machines
            if status == 'Running':
                # Occasional maintenance stops
                if random.random() < 0.02:  # 2% chance
                    status = 'Maintenance'
                    rpm = 0
                    energy_kWh = np.random.uniform(1, 3)
                
                # Machine faults
                elif random.random() < 0.005:  # 0.5% chance
                    status = 'Fault'
                    rpm = np.random.uniform(0, 500)
                    energy_kWh = np.random.uniform(5, 15)
            
            data.append({
                'timestamp': timestamp,
                'machine_id': machine_id,
                'rpm': round(rpm, 0),
                'energy_kWh': round(energy_kWh, 2),
                'status': status
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_factory_environment_data():
    """Generate factory environment monitoring data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15T')
    
    data = []
    
    # Zone characteristics
    zone_profiles = {
        'Zone_1': {'type': 'Production Floor', 'base_temp': 24, 'base_co2': 800},
        'Zone_2': {'type': 'Assembly Line', 'base_temp': 22, 'base_co2': 900},
        'Zone_3': {'type': 'Quality Control', 'base_temp': 20, 'base_co2': 600},
        'Zone_4': {'type': 'Warehouse', 'base_temp': 18, 'base_co2': 500},
        'Zone_5': {'type': 'Office Area', 'base_temp': 23, 'base_co2': 700},
        'Zone_6': {'type': 'Chemical Storage', 'base_temp': 16, 'base_co2': 450},
        'Zone_7': {'type': 'Loading Dock', 'base_temp': 26, 'base_co2': 1000},
    }
    
    for zone_id in FACTORY_ZONES:
        profile = zone_profiles[zone_id]
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Activity level affects environment
            if day_of_week < 5 and 6 <= hour <= 22:  # Work hours
                activity_factor = 0.7 + 0.3 * np.sin(np.pi * (hour - 6) / 16)
            else:
                activity_factor = 0.2
            
            # Temperature
            external_temp = 15 + 10 * np.sin(2 * np.pi * (hour - 6) / 24)  # Daily cycle
            temperature_C = (profile['base_temp'] + 
                           external_temp * 0.1 + 
                           activity_factor * 5 + 
                           np.random.normal(0, 1.5))
            
            # Humidity (inversely related to temperature)
            humidity_percent = 60 - (temperature_C - 20) * 1.5 + np.random.normal(0, 5)
            humidity_percent = np.clip(humidity_percent, 30, 85)
            
            # CO2 levels
            co2_ppm = (profile['base_co2'] + 
                      activity_factor * 500 + 
                      np.random.normal(0, 100))
            
            # Occasional CO2 spikes
            if random.random() < 0.03:  # 3% chance
                co2_ppm += np.random.uniform(300, 800)
            
            co2_ppm = max(400, co2_ppm)
            
            # Air Quality Index
            base_aqi = 25
            if co2_ppm > 1000:
                aqi_co2_impact = (co2_ppm - 1000) * 0.05
            else:
                aqi_co2_impact = 0
            
            aqi = base_aqi + aqi_co2_impact + activity_factor * 20 + np.random.normal(0, 10)
            aqi = max(0, aqi)
            
            # Noise levels
            if profile['type'] in ['Production Floor', 'Assembly Line', 'Loading Dock']:
                base_noise = 75
            elif profile['type'] in ['Quality Control', 'Office Area']:
                base_noise = 45
            else:
                base_noise = 55
            
            noise_db = base_noise + activity_factor * 15 + np.random.normal(0, 5)
            
            # Occasional noise spikes
            if random.random() < 0.05:  # 5% chance
                noise_db += np.random.uniform(10, 25)
            
            data.append({
                'timestamp': timestamp,
                'zone_id': zone_id,
                'zone_type': profile['type'],
                'temperature_C': round(temperature_C, 1),
                'humidity_percent': round(humidity_percent, 1),
                'co2_ppm': round(co2_ppm, 0),
                'aqi': round(aqi, 0),
                'noise_db': round(noise_db, 1)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_oee_data():
    """Generate Production Line OEE tracking data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30T')  # Every 30 minutes
    
    data = []
    
    # Production line profiles
    line_profiles = {
        'Line_A': {'efficiency': 0.92, 'reliability': 0.95, 'product': 'Electronics'},
        'Line_B': {'efficiency': 0.88, 'reliability': 0.90, 'product': 'Automotive'},
        'Line_C': {'efficiency': 0.94, 'reliability': 0.97, 'product': 'Pharmaceuticals'},
        'Line_D': {'efficiency': 0.85, 'reliability': 0.87, 'product': 'Food Processing'},
        'Line_E': {'efficiency': 0.90, 'reliability': 0.92, 'product': 'Textiles'},
    }
    
    for line_id in PRODUCTION_LINES:
        profile = line_profiles[line_id]
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            if day_of_week < 5 and 6 <= hour <= 22:  # Work hours
                # Base performance during work hours
                base_availability = profile['reliability'] * 100
                base_performance = profile['efficiency'] * 100
                base_quality = np.random.uniform(92, 98)
                
                # Shift patterns
                if 6 <= hour <= 14:  # Morning shift (usually best)
                    shift_factor = 1.0
                elif 14 <= hour <= 22:  # Evening shift
                    shift_factor = 0.95
                else:  # Night shift
                    shift_factor = 0.90
                
            else:  # Off hours/weekends
                base_availability = np.random.uniform(10, 30)  # Minimal operations
                base_performance = np.random.uniform(20, 50)
                base_quality = np.random.uniform(85, 95)
                shift_factor = 0.8
            
            # Add variability
            availability_percent = base_availability * shift_factor + np.random.normal(0, 3)
            performance_percent = base_performance * shift_factor + np.random.normal(0, 4)
            quality_percent = base_quality + np.random.normal(0, 2)
            
            # Ensure realistic bounds
            availability_percent = np.clip(availability_percent, 0, 100)
            performance_percent = np.clip(performance_percent, 0, 100)
            quality_percent = np.clip(quality_percent, 70, 100)
            
            # Occasional issues
            if random.random() < 0.05:  # 5% chance of issues
                availability_percent *= np.random.uniform(0.6, 0.9)
                performance_percent *= np.random.uniform(0.7, 0.9)
            
            if random.random() < 0.02:  # 2% chance of quality issues
                quality_percent *= np.random.uniform(0.8, 0.95)
            
            # Calculate OEE
            oee_percent = (availability_percent * performance_percent * quality_percent) / 10000
            
            data.append({
                'timestamp': timestamp,
                'line_id': line_id,
                'product_type': profile['product'],
                'availability_percent': round(availability_percent, 1),
                'performance_percent': round(performance_percent, 1),
                'quality_percent': round(quality_percent, 1),
                'oee_percent': round(oee_percent, 1)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_cold_chain_data():
    """Generate cold chain monitoring data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='20T')
    
    data = []
    
    # Shipment types
    shipment_configs = {
        'SHIP_1000': {'target_temp': -18, 'tolerance': 2, 'cargo': 'Frozen Foods'},
        'SHIP_1001': {'target_temp': 4, 'tolerance': 2, 'cargo': 'Dairy Products'},
        'SHIP_1002': {'target_temp': 2, 'tolerance': 1, 'cargo': 'Vaccines'},
        'SHIP_1003': {'target_temp': 6, 'tolerance': 3, 'cargo': 'Fresh Produce'},
        'SHIP_1004': {'target_temp': -15, 'tolerance': 3, 'cargo': 'Ice Cream'},
        'SHIP_1005': {'target_temp': 3, 'tolerance': 1, 'cargo': 'Blood Products'},
        'SHIP_1006': {'target_temp': 8, 'tolerance': 2, 'cargo': 'Beverages'},
        'SHIP_1007': {'target_temp': -20, 'tolerance': 2, 'cargo': 'Medical Samples'},
        'SHIP_1008': {'target_temp': 5, 'tolerance': 2, 'cargo': 'Meat Products'},
        'SHIP_1009': {'target_temp': 7, 'tolerance': 3, 'cargo': 'Chemicals'},
    }
    
    for i, (shipment_id, config) in enumerate(list(shipment_configs.items())[:10]):
        truck_id = TRUCKS[i % len(TRUCKS)]
        route_coords = GPS_ROUTES[i % len(GPS_ROUTES)]
        
        for j, timestamp in enumerate(timestamps):
            # Simulate route progress
            progress = min(j / len(timestamps), 1.0)
            
            # GPS coordinates with route simulation
            base_lat, base_lon = route_coords
            gps_lat = base_lat + progress * np.random.uniform(-2, 2) + np.random.normal(0, 0.01)
            gps_lon = base_lon + progress * np.random.uniform(-2, 2) + np.random.normal(0, 0.01)
            
            # Temperature simulation
            target_temp = config['target_temp']
            tolerance = config['tolerance']
            
            temp_variation = np.random.normal(0, tolerance * 0.5)
            
            # External factors
            hour = timestamp.hour
            if 12 <= hour <= 16:  # Hot afternoon
                external_factor = np.random.uniform(0.5, 2.0)
            elif 2 <= hour <= 6:  # Cold night
                external_factor = np.random.uniform(-1.0, -0.3)
            else:
                external_factor = np.random.uniform(-0.5, 0.5)
            
            # Equipment malfunctions
            if truck_id in ['TRUCK_003', 'TRUCK_007', 'TRUCK_012']:  # Problem trucks
                if random.random() < 0.08:  # 8% chance of temperature excursion
                    temp_variation += np.random.uniform(5, 15)
            elif random.random() < 0.02:  # 2% chance for normal trucks
                temp_variation += np.random.uniform(3, 10)
            
            cold_storage_temp = target_temp + temp_variation + external_factor * 0.3
            
            # Humidity
            humidity = np.random.uniform(60, 85) + np.random.normal(0, 5)
            humidity = np.clip(humidity, 40, 95)
            
            # Door status
            door_status = 'closed'
            if progress < 0.05 or progress > 0.95:  # Loading/unloading
                if random.random() < 0.1:  # 10% chance
                    door_status = 'open'
            elif random.random() < 0.01:  # 1% chance during transit
                door_status = 'open'
            
            data.append({
                'timestamp': timestamp,
                'shipment_id': shipment_id,
                'truck_id': truck_id,
                'cargo_type': config['cargo'],
                'cold_storage_temp': round(cold_storage_temp, 1),
                'humidity': round(humidity, 1),
                'gps_lat': round(gps_lat, 4),
                'gps_lon': round(gps_lon, 4),
                'door_status': door_status,
                'target_temp': target_temp
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_warehouse_environment_data():
    """Generate warehouse environment monitoring data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15T')
    
    data = []
    
    for warehouse_id in WAREHOUSES:
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Activity level
            if day_of_week < 5 and 6 <= hour <= 18:  # Work hours
                activity = 0.8
            elif day_of_week < 5 and 18 <= hour <= 22:  # Evening
                activity = 0.4
            else:  # Off hours/weekends
                activity = 0.1
            
            # Temperature
            base_temp = 20
            temp = base_temp + activity * 3 + np.random.normal(0, 2)
            
            # Humidity
            humidity = 50 + activity * 10 + np.random.normal(0, 8)
            humidity = np.clip(humidity, 30, 80)
            
            # CO2
            base_co2 = 450
            co2 = base_co2 + activity * 600 + np.random.normal(0, 100)
            
            # CO2 spikes
            if random.random() < 0.03:
                co2 += np.random.uniform(400, 1000)
            
            # AQI
            aqi = 30 + activity * 40
            if co2 > 1000:
                aqi += (co2 - 1000) * 0.03
            aqi += np.random.normal(0, 15)
            aqi = max(0, aqi)
            
            data.append({
                'timestamp': timestamp,
                'warehouse_id': warehouse_id,
                'temp': round(temp, 1),
                'humidity': round(humidity, 1),
                'co2': round(co2, 0),
                'aqi': round(aqi, 0)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_inventory_data():
    """Generate inventory level tracking data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='60T')  # Hourly
    
    data = []
    
    # SKU configurations
    sku_configs = {}
    for i, sku_id in enumerate(SKUS[:25]):  # Use first 25 SKUs
        sku_configs[sku_id] = {
            'initial_stock': np.random.randint(100, 1000),
            'reorder_point': np.random.randint(50, 200),
            'consumption_rate': np.random.uniform(0.5, 5.0),  # Units per hour
            'warehouse_id': WAREHOUSES[i % len(WAREHOUSES)]
        }
    
    for sku_id, config in sku_configs.items():
        current_stock = config['initial_stock']
        warehouse_id = config['warehouse_id']
        reorder_point = config['reorder_point']
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Consumption patterns
            if day_of_week < 5 and 8 <= hour <= 17:  # Business hours
                consumption_multiplier = 1.0
            elif day_of_week < 5:  # Weekday off-hours
                consumption_multiplier = 0.3
            else:  # Weekends
                consumption_multiplier = 0.5
            
            # Apply consumption
            consumption = config['consumption_rate'] * consumption_multiplier + np.random.normal(0, 0.5)
            consumption = max(0, consumption)
            current_stock = max(0, current_stock - consumption)
            
            # Restocking logic
            if current_stock <= reorder_point:
                # Simulate restocking delay
                if random.random() < 0.1:  # 10% chance per hour of restocking
                    restock_amount = np.random.randint(200, 800)
                    current_stock += restock_amount
                    restock_eta = None
                else:
                    restock_eta = np.random.randint(6, 48)  # Hours until restock
            else:
                restock_eta = None
            
            data.append({
                'timestamp': timestamp,
                'sku_id': sku_id,
                'warehouse_id': warehouse_id,
                'stock_level': round(current_stock, 0),
                'reorder_point': reorder_point,
                'restock_eta': restock_eta
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_package_tamper_data():
    """Generate package tampering detection data"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30T')
    
    data = []
    
    for package_id in PACKAGES[:50]:  # Use first 50 packages
        for timestamp in timestamps:
            # Normal tilt angle (0-15 degrees)
            tilt_angle = np.random.uniform(0, 10) + np.random.normal(0, 2)
            
            # Occasional high tilt events (drops, mishandling)
            if random.random() < 0.02:  # 2% chance
                tilt_angle += np.random.uniform(30, 80)
            
            tilt_angle = max(0, tilt_angle)
            
            # Light exposure (normal: 0-200 lux)
            light_exposure_lux = np.random.uniform(10, 150) + np.random.normal(0, 20)
            
            # Tampering attempts (high light exposure)
            if random.random() < 0.01:  # 1% chance
                light_exposure_lux += np.random.uniform(800, 2000)
            
            light_exposure_lux = max(0, light_exposure_lux)
            
            # Seal status
            seal_status = 'intact'
            
            # Seal failure probability increases with high tilt/light
            failure_prob = 0.001  # Base 0.1%
            if tilt_angle > 45:
                failure_prob += 0.02
            if light_exposure_lux > 1000:
                failure_prob += 0.03
            
            if random.random() < failure_prob:
                seal_status = 'broken'
            
            data.append({
                'timestamp': timestamp,
                'package_id': package_id,
                'tilt_angle': round(tilt_angle, 1),
                'light_exposure_lux': round(light_exposure_lux, 0),
                'seal_status': seal_status
            })
    
    return pd.DataFrame(data)

# =============================================================================
# ALERT CHECKING FUNCTIONS
# =============================================================================

def check_predictive_maintenance_alerts(df):
    """Check for predictive maintenance alerts"""
    alerts = []
    latest_data = df.groupby('machine_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        if row['vibration_rms'] > 12:
            alerts.append({
                'type': 'High Vibration',
                'machine': row['machine_id'],
                'value': row['vibration_rms'],
                'threshold': 12,
                'severity': 'Warning'
            })
        
        if row['temperature_C'] > 80:
            alerts.append({
                'type': 'High Temperature',
                'machine': row['machine_id'],
                'value': row['temperature_C'],
                'threshold': 80,
                'severity': 'Critical'
            })
        
        if row['failure_risk_score'] > 70:
            alerts.append({
                'type': 'High Failure Risk',
                'machine': row['machine_id'],
                'value': row['failure_risk_score'],
                'threshold': 70,
                'severity': 'Critical'
            })
    
    return alerts

def check_environment_alerts(df):
    """Check for factory environment alerts"""
    alerts = []
    latest_data = df.groupby('zone_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        if row['co2_ppm'] > 1500:
            alerts.append({
                'type': 'High CO2',
                'zone': row['zone_id'],
                'value': row['co2_ppm'],
                'threshold': 1500,
                'severity': 'Warning'
            })
        
        if row['aqi'] > 100:
            alerts.append({
                'type': 'Poor Air Quality',
                'zone': row['zone_id'],
                'value': row['aqi'],
                'threshold': 100,
                'severity': 'Warning'
            })
        
        if row['noise_db'] > 90:
            alerts.append({
                'type': 'High Noise',
                'zone': row['zone_id'],
                'value': row['noise_db'],
                'threshold': 90,
                'severity': 'Warning'
            })
    
    return alerts

def check_cold_chain_alerts(df):
    """Check for cold chain alerts"""
    alerts = []
    latest_data = df.groupby('shipment_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        target_temp = row['target_temp']
        current_temp = row['cold_storage_temp']
        
        # Temperature deviation alert
        if abs(current_temp - target_temp) > 5:
            alerts.append({
                'type': 'Temperature Deviation',
                'shipment': row['shipment_id'],
                'current': current_temp,
                'target': target_temp,
                'severity': 'Critical'
            })
    
    return alerts

def check_inventory_alerts(df):
    """Check for inventory alerts"""
    alerts = []
    latest_data = df.groupby('sku_id').last().reset_index()
    
    low_stock = latest_data[latest_data['stock_level'] <= latest_data['reorder_point']]
    
    for _, row in low_stock.iterrows():
        alerts.append({
            'type': 'Low Stock',
            'sku': row['sku_id'],
            'warehouse': row['warehouse_id'],
            'stock_level': row['stock_level'],
            'reorder_point': row['reorder_point'],
            'severity': 'Warning'
        })
    
    return alerts

def check_tampering_alerts(df):
    """Check for package tampering alerts"""
    alerts = []
    latest_data = df.groupby('package_id').last().reset_index()
    
    for _, row in latest_data.iterrows():
        if row['tilt_angle'] > 45:
            alerts.append({
                'type': 'High Tilt',
                'package': row['package_id'],
                'value': row['tilt_angle'],
                'threshold': 45,
                'severity': 'Warning'
            })
        
        if row['light_exposure_lux'] > 1000:
            alerts.append({
                'type': 'High Light Exposure',
                'package': row['package_id'],
                'value': row['light_exposure_lux'],
                'threshold': 1000,
                'severity': 'Warning'
            })
        
        if row['seal_status'] == 'broken':
            alerts.append({
                'type': 'Broken Seal',
                'package': row['package_id'],
                'status': 'broken',
                'severity': 'Critical'
            })
    
    return alerts

# =============================================================================
# MAIN DASHBOARD APPLICATION
# =============================================================================

def main():
    # Page header
    st.title("🏭 Industrial IoT & Supply Chain Monitoring Dashboard")
    st.markdown("Comprehensive monitoring system for factory operations and supply chain logistics")
    
    # Sidebar configuration
    st.sidebar.header("🔧 Dashboard Controls")
    st.sidebar.markdown("---")
    
    # Load all data
    with st.spinner("Loading data..."):
        predictive_data = generate_predictive_maintenance_data()
        machine_status_data = generate_machine_status_data()
        environment_data = generate_factory_environment_data()
        oee_data = generate_oee_data()
        cold_chain_data = generate_cold_chain_data()
        warehouse_env_data = generate_warehouse_environment_data()
        inventory_data = generate_inventory_data()
        tampering_data = generate_package_tamper_data()
    
    # Check all alerts
    pm_alerts = check_predictive_maintenance_alerts(predictive_data)
    env_alerts = check_environment_alerts(environment_data)
    cc_alerts = check_cold_chain_alerts(cold_chain_data)
    inv_alerts = check_inventory_alerts(inventory_data)
    tamper_alerts = check_tampering_alerts(tampering_data)
    
    # Alert summary in sidebar
    st.sidebar.subheader("🚨 Alert Summary")
    total_alerts = len(pm_alerts) + len(env_alerts) + len(cc_alerts) + len(inv_alerts) + len(tamper_alerts)
    
    if total_alerts > 0:
        st.sidebar.error(f"**{total_alerts} Active Alerts**")
        
        alert_types = {
            'Predictive Maintenance': len(pm_alerts),
            'Environment': len(env_alerts),
            'Cold Chain': len(cc_alerts),
            'Inventory': len(inv_alerts),
            'Tampering': len(tamper_alerts)
        }
        
        for alert_type, count in alert_types.items():
            if count > 0:
                st.sidebar.warning(f"{alert_type}: {count}")
    else:
        st.sidebar.success("✅ No Active Alerts")
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🔧 Predictive Maintenance",
        "⚙️ Machine Status",
        "🌡️ Factory Environment",
        "📊 Production OEE",
        "🚛 Cold Chain",
        "🏪 Warehouse Environment",
        "📦 Inventory Tracking",
        "🔒 Package Security"
    ])
    
    # Tab 1: Predictive Maintenance
    with tab1:
        st.header("🔧 Predictive Maintenance Dashboard")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_machine = st.selectbox(
                "Select Machine:",
                ["All Machines"] + MACHINES,
                key="pm_machine"
            )
        with col2:
            time_range = st.selectbox(
                "Time Range:",
                ["Last 24 Hours", "Last 3 Days", "Last 7 Days"],
                index=2,
                key="pm_time"
            )
        
        # Filter data
        if time_range == "Last 24 Hours":
            filtered_data = predictive_data[predictive_data['timestamp'] >= predictive_data['timestamp'].max() - timedelta(days=1)]
        elif time_range == "Last 3 Days":
            filtered_data = predictive_data[predictive_data['timestamp'] >= predictive_data['timestamp'].max() - timedelta(days=3)]
        else:
            filtered_data = predictive_data
        
        if selected_machine != "All Machines":
            filtered_data = filtered_data[filtered_data['machine_id'] == selected_machine]
        
        # Alert banners
        current_pm_alerts = [a for a in pm_alerts if selected_machine == "All Machines" or a['machine'] == selected_machine]
        if current_pm_alerts:
            st.error(f"🚨 {len(current_pm_alerts)} Predictive Maintenance Alerts")
            for alert in current_pm_alerts[:3]:
                if alert['severity'] == 'Critical':
                    st.error(f"**{alert['machine']}**: {alert['type']} = {alert['value']} (threshold: {alert['threshold']})")
                else:
                    st.warning(f"**{alert['machine']}**: {alert['type']} = {alert['value']} (threshold: {alert['threshold']})")
        
        # KPIs
        latest_data = filtered_data.groupby('machine_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_vibration = latest_data['vibration_rms'].mean()
            st.metric("Avg Vibration", f"{avg_vibration:.1f} mm/s", delta=None)
        
        with col2:
            avg_temp = latest_data['temperature_C'].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C", delta=None)
        
        with col3:
            avg_risk = latest_data['failure_risk_score'].mean()
            st.metric("Avg Failure Risk", f"{avg_risk:.1f}%", delta=None)
        
        with col4:
            critical_machines = len(latest_data[latest_data['failure_risk_score'] > 70])
            st.metric("Critical Machines", critical_machines, delta=None)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Vibration trend
            fig_vib = px.line(
                filtered_data,
                x='timestamp',
                y='vibration_rms',
                color='machine_id',
                title='Vibration RMS Trend',
                labels={'vibration_rms': 'Vibration (mm/s)'}
            )
            fig_vib.add_hline(y=12, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
            st.plotly_chart(fig_vib, use_container_width=True)
        
        with col2:
            # Temperature trend
            fig_temp = px.line(
                filtered_data,
                x='timestamp',
                y='temperature_C',
                color='machine_id',
                title='Temperature Trend',
                labels={'temperature_C': 'Temperature (°C)'}
            )
            fig_temp.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
            st.plotly_chart(fig_temp, use_container_width=True)
        
        # Failure risk heatmap
        if selected_machine == "All Machines":
            latest_pivot = latest_data.pivot_table(
                values='failure_risk_score',
                index='machine_id',
                aggfunc='mean'
            ).reset_index()
            
            fig_risk = px.bar(
                latest_pivot,
                x='machine_id',
                y='failure_risk_score',
                title='Current Failure Risk Scores by Machine',
                color='failure_risk_score',
                color_continuous_scale='RdYlGn_r'
            )
            fig_risk.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Machine health status table
        st.subheader("Machine Health Status")
        health_df = latest_data[['machine_id', 'vibration_rms', 'temperature_C', 'failure_risk_score', 'health_status']].copy()
        health_df.columns = ['Machine', 'Vibration (mm/s)', 'Temperature (°C)', 'Failure Risk (%)', 'Status']
        
        # Color coding
        def highlight_status(row):
            colors = []
            for col in row.index:
                if col == 'Failure Risk (%)':
                    if row[col] > 70:
                        colors.append('background-color: #ffcccc')
                    elif row[col] > 50:
                        colors.append('background-color: #fff2cc')
                    else:
                        colors.append('background-color: #ccffcc')
                else:
                    colors.append('')
            return colors
        
        st.dataframe(health_df.style.apply(highlight_status, axis=1), use_container_width=True)
    
    # Tab 2: Machine Status Monitoring
    with tab2:
        st.header("⚙️ Machine Status Monitoring")
        
        # Real-time toggle
        real_time_enabled = st.checkbox("Enable Real-Time Updates", key="realtime")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_machine_status = st.selectbox(
                "Select Machine:",
                ["All Machines"] + MACHINES,
                key="status_machine"
            )
        with col2:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "Running", "Stopped", "Maintenance", "Fault"],
                key="status_filter"
            )
        
        # Filter data
        filtered_status = machine_status_data.copy()
        if selected_machine_status != "All Machines":
            filtered_status = filtered_status[filtered_status['machine_id'] == selected_machine_status]
        if status_filter != "All":
            filtered_status = filtered_status[filtered_status['status'] == status_filter]
        
        # Real-time simulation
        if real_time_enabled:
            placeholder = st.empty()
            
            for _ in range(5):  # 5 updates
                # Generate new data point
                current_time = datetime.now()
                new_data = []
                
                for machine_id in (MACHINES if selected_machine_status == "All Machines" else [selected_machine_status]):
                    # Simple real-time simulation
                    if random.random() < 0.9:  # 90% chance running
                        status = 'Running'
                        rpm = np.random.uniform(1400, 1700)
                        energy = np.random.uniform(18, 23)
                    else:
                        status = 'Stopped'
                        rpm = 0
                        energy = np.random.uniform(0.5, 2.0)
                    
                    new_data.append({
                        'timestamp': current_time,
                        'machine_id': machine_id,
                        'rpm': round(rpm, 0),
                        'energy_kWh': round(energy, 2),
                        'status': status
                    })
                
                new_df = pd.DataFrame(new_data)
                
                with placeholder.container():
                    # Current status metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        running_count = len(new_df[new_df['status'] == 'Running'])
                        st.metric("Running Machines", running_count)
                    
                    with col2:
                        avg_rpm = new_df[new_df['status'] == 'Running']['rpm'].mean()
                        st.metric("Avg RPM", f"{avg_rpm:.0f}" if not np.isnan(avg_rpm) else "0")
                    
                    with col3:
                        total_energy = new_df['energy_kWh'].sum()
                        st.metric("Total Energy", f"{total_energy:.1f} kWh")
                    
                    with col4:
                        fault_count = len(new_df[new_df['status'] == 'Fault'])
                        st.metric("Faults", fault_count)
                    
                    # Real-time chart
                    fig_realtime = px.bar(
                        new_df,
                        x='machine_id',
                        y='rpm',
                        color='status',
                        title=f'Real-Time Machine Status - {current_time.strftime("%H:%M:%S")}',
                        color_discrete_map={
                            'Running': 'green',
                            'Stopped': 'red',
                            'Maintenance': 'orange',
                            'Fault': 'darkred'
                        }
                    )
                    st.plotly_chart(fig_realtime, use_container_width=True)
                
                time.sleep(2)  # 2-second updates
        
        else:
            # Static analysis
            latest_status = filtered_status.groupby('machine_id').last().reset_index()
            
            # Status overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                running_count = len(latest_status[latest_status['status'] == 'Running'])
                st.metric("Running Machines", running_count)
            
            with col2:
                avg_rpm = latest_status[latest_status['status'] == 'Running']['rpm'].mean()
                st.metric("Avg RPM", f"{avg_rpm:.0f}" if not np.isnan(avg_rpm) else "0")
            
            with col3:
                total_energy = latest_status['energy_kWh'].sum()
                st.metric("Total Energy", f"{total_energy:.1f} kWh")
            
            with col4:
                fault_count = len(latest_status[latest_status['status'] == 'Fault'])
                st.metric("Faults", fault_count)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution
                status_counts = latest_status['status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='Machine Status Distribution'
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Energy consumption
                fig_energy = px.bar(
                    latest_status,
                    x='machine_id',
                    y='energy_kWh',
                    color='status',
                    title='Energy Consumption by Machine'
                )
                st.plotly_chart(fig_energy, use_container_width=True)
            
            # RPM trend over time
            recent_data = filtered_status[filtered_status['timestamp'] >= filtered_status['timestamp'].max() - timedelta(hours=6)]
            fig_rpm = px.line(
                recent_data,
                x='timestamp',
                y='rpm',
                color='machine_id',
                title='RPM Trend (Last 6 Hours)'
            )
            st.plotly_chart(fig_rpm, use_container_width=True)
    
    # Tab 3: Factory Environment
    with tab3:
        st.header("🌡️ Factory Environment Monitoring")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_zone = st.selectbox(
                "Select Zone:",
                ["All Zones"] + FACTORY_ZONES,
                key="env_zone"
            )
        with col2:
            env_metric = st.selectbox(
                "Primary Metric:",
                ["Temperature", "CO2", "Air Quality", "Noise"],
                key="env_metric"
            )
        
        # Filter data
        filtered_env = environment_data.copy()
        if selected_zone != "All Zones":
            filtered_env = filtered_env[filtered_env['zone_id'] == selected_zone]
        
        # Alert banners
        current_env_alerts = [a for a in env_alerts if selected_zone == "All Zones" or a['zone'] == selected_zone]
        if current_env_alerts:
            st.warning(f"⚠️ {len(current_env_alerts)} Environment Alerts")
            for alert in current_env_alerts[:3]:
                st.warning(f"**{alert['zone']}**: {alert['type']} = {alert['value']} (threshold: {alert['threshold']})")
        
        # Environmental KPIs
        latest_env = filtered_env.groupby('zone_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_temp = latest_env['temperature_C'].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        with col2:
            avg_co2 = latest_env['co2_ppm'].mean()
            co2_status = "🔴" if avg_co2 > 1500 else "🟡" if avg_co2 > 1000 else "🟢"
            st.metric("Avg CO2", f"{avg_co2:.0f} ppm {co2_status}")
        
        with col3:
            avg_aqi = latest_env['aqi'].mean()
            aqi_status = "🔴" if avg_aqi > 100 else "🟡" if avg_aqi > 50 else "🟢"
            st.metric("Avg AQI", f"{avg_aqi:.0f} {aqi_status}")
        
        with col4:
            avg_noise = latest_env['noise_db'].mean()
            noise_status = "🔴" if avg_noise > 90 else "🟡" if avg_noise > 75 else "🟢"
            st.metric("Avg Noise", f"{avg_noise:.1f} dB {noise_status}")
        
        # Main environmental chart
        metric_mapping = {
            "Temperature": "temperature_C",
            "CO2": "co2_ppm",
            "Air Quality": "aqi",
            "Noise": "noise_db"
        }
        
        fig_env = px.line(
            filtered_env,
            x='timestamp',
            y=metric_mapping[env_metric],
            color='zone_id',
            title=f'{env_metric} Levels Over Time'
        )
        
        # Add threshold lines
        if env_metric == "CO2":
            fig_env.add_hline(y=1500, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
        elif env_metric == "Air Quality":
            fig_env.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Unhealthy Threshold")
        elif env_metric == "Noise":
            fig_env.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
        
        st.plotly_chart(fig_env, use_container_width=True)
        
        # Environmental heatmap
        col1, col2 = st.columns(2)
        
        with col1:
            # CO2 vs AQI scatter
            fig_scatter = px.scatter(
                latest_env,
                x='co2_ppm',
                y='aqi',
                color='zone_type',
                size='temperature_C',
                hover_data=['zone_id'],
                title='CO2 vs Air Quality by Zone'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Zone comparison
            fig_compare = px.bar(
                latest_env,
                x='zone_id',
                y=metric_mapping[env_metric],
                color='zone_type',
                title=f'{env_metric} by Zone'
            )
            st.plotly_chart(fig_compare, use_container_width=True)
        
        # Environment status table
        st.subheader("Zone Environmental Status")
        env_table = latest_env[['zone_id', 'zone_type', 'temperature_C', 'co2_ppm', 'aqi', 'noise_db']].copy()
        env_table.columns = ['Zone', 'Type', 'Temp (°C)', 'CO2 (ppm)', 'AQI', 'Noise (dB)']
        
        def highlight_env(row):
            colors = []
            for col in row.index:
                if col == 'CO2 (ppm)' and row[col] > 1500:
                    colors.append('background-color: #ffcccc')
                elif col == 'AQI' and row[col] > 100:
                    colors.append('background-color: #ffcccc')
                elif col == 'Noise (dB)' and row[col] > 90:
                    colors.append('background-color: #ffcccc')
                else:
                    colors.append('')
            return colors
        
        st.dataframe(env_table.style.apply(highlight_env, axis=1), use_container_width=True)
    
    # Tab 4: Production OEE
    with tab4:
        st.header("📊 Production Line OEE Tracking")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_line = st.selectbox(
                "Select Production Line:",
                ["All Lines"] + PRODUCTION_LINES,
                key="oee_line"
            )
        with col2:
            oee_period = st.selectbox(
                "Time Period:",
                ["Last 24 Hours", "Last 3 Days", "Last 7 Days"],
                index=1,
                key="oee_period"
            )
        
        # Filter data
        if oee_period == "Last 24 Hours":
            filtered_oee = oee_data[oee_data['timestamp'] >= oee_data['timestamp'].max() - timedelta(days=1)]
        elif oee_period == "Last 3 Days":
            filtered_oee = oee_data[oee_data['timestamp'] >= oee_data['timestamp'].max() - timedelta(days=3)]
        else:
            filtered_oee = oee_data
        
        if selected_line != "All Lines":
            filtered_oee = filtered_oee[filtered_oee['line_id'] == selected_line]
        
        # OEE KPIs
        latest_oee = filtered_oee.groupby('line_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_oee = latest_oee['oee_percent'].mean()
            oee_color = "🟢" if avg_oee > 80 else "🟡" if avg_oee > 60 else "🔴"
            st.metric("Overall OEE", f"{avg_oee:.1f}% {oee_color}")
        
        with col2:
            avg_availability = latest_oee['availability_percent'].mean()
            st.metric("Avg Availability", f"{avg_availability:.1f}%")
        
        with col3:
            avg_performance = latest_oee['performance_percent'].mean()
            st.metric("Avg Performance", f"{avg_performance:.1f}%")
        
        with col4:
            avg_quality = latest_oee['quality_percent'].mean()
            st.metric("Avg Quality", f"{avg_quality:.1f}%")
        
        # OEE trend chart
        fig_oee_trend = px.line(
            filtered_oee,
            x='timestamp',
            y='oee_percent',
            color='line_id',
            title='OEE Trend Over Time',
            labels={'oee_percent': 'OEE (%)'}
        )
        fig_oee_trend.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="World Class (80%)")
        fig_oee_trend.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Acceptable (60%)")
        st.plotly_chart(fig_oee_trend, use_container_width=True)
        
        # OEE components breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            # OEE components by line
            oee_components = latest_oee.melt(
                id_vars=['line_id', 'product_type'],
                value_vars=['availability_percent', 'performance_percent', 'quality_percent'],
                var_name='component',
                value_name='percentage'
            )
            
            fig_components = px.bar(
                oee_components,
                x='line_id',
                y='percentage',
                color='component',
                title='OEE Components by Production Line',
                barmode='group'
            )
            st.plotly_chart(fig_components, use_container_width=True)
        
        with col2:
            # Current OEE status
            fig_current_oee = px.bar(
                latest_oee,
                x='line_id',
                y='oee_percent',
                color='product_type',
                title='Current OEE by Production Line'
            )
            fig_current_oee.add_hline(y=80, line_dash="dash", line_color="green")
            st.plotly_chart(fig_current_oee, use_container_width=True)
        
        # Production efficiency table
        st.subheader("Production Line Performance Summary")
        performance_table = latest_oee[['line_id', 'product_type', 'availability_percent', 'performance_percent', 'quality_percent', 'oee_percent']].copy()
        performance_table.columns = ['Line', 'Product', 'Availability (%)', 'Performance (%)', 'Quality (%)', 'OEE (%)']
        
        def highlight_oee(row):
            colors = []
            for col in row.index:
                if col == 'OEE (%)':
                    if row[col] >= 80:
                        colors.append('background-color: #ccffcc')
                    elif row[col] >= 60:
                        colors.append('background-color: #fff2cc')
                    else:
                        colors.append('background-color: #ffcccc')
                else:
                    colors.append('')
            return colors
        
        st.dataframe(performance_table.style.apply(highlight_oee, axis=1), use_container_width=True)
    
    # Tab 5: Cold Chain Monitoring
    with tab5:
        st.header("🚛 Cold Chain Monitoring")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_shipment = st.selectbox(
                "Select Shipment:",
                ["All Shipments"] + [s for s in cold_chain_data['shipment_id'].unique()],
                key="cc_shipment"
            )
        with col2:
            selected_truck = st.selectbox(
                "Select Truck:",
                ["All Trucks"] + [t for t in cold_chain_data['truck_id'].unique()],
                key="cc_truck"
            )
        
        # Filter data
        filtered_cc = cold_chain_data.copy()
        if selected_shipment != "All Shipments":
            filtered_cc = filtered_cc[filtered_cc['shipment_id'] == selected_shipment]
        if selected_truck != "All Trucks":
            filtered_cc = filtered_cc[filtered_cc['truck_id'] == selected_truck]
        
        # Cold chain alerts
        current_cc_alerts = [a for a in cc_alerts 
                           if (selected_shipment == "All Shipments" or a['shipment'] == selected_shipment)]
        if current_cc_alerts:
            st.error(f"🚨 {len(current_cc_alerts)} Cold Chain Temperature Alerts")
            for alert in current_cc_alerts[:3]:
                st.error(f"**{alert['shipment']}**: Current temp {alert['current']}°C (Target: {alert['target']}°C)")
        
        # Cold chain KPIs
        latest_cc = filtered_cc.groupby('shipment_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_shipments = len(latest_cc)
            st.metric("Active Shipments", total_shipments)
        
        with col2:
            avg_temp = latest_cc['cold_storage_temp'].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        with col3:
            temp_violations = len([a for a in cc_alerts])
            st.metric("Temp Violations", temp_violations)
        
        with col4:
            door_open_count = len(latest_cc[latest_cc['door_status'] == 'open'])
            st.metric("Doors Open", door_open_count)
        
        # Temperature monitoring
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp_cc = px.line(
                filtered_cc,
                x='timestamp',
                y='cold_storage_temp',
                color='shipment_id',
                title='Cold Storage Temperature Monitoring',
                labels={'cold_storage_temp': 'Temperature (°C)'}
            )
            # Add target temperature lines for each shipment
            for shipment in filtered_cc['shipment_id'].unique():
                target_temp = filtered_cc[filtered_cc['shipment_id'] == shipment]['target_temp'].iloc[0]
                fig_temp_cc.add_hline(
                    y=target_temp,
                    line_dash="dot",
                    line_color="blue",
                    opacity=0.7,
                    annotation_text=f"Target: {target_temp}°C"
                )
            st.plotly_chart(fig_temp_cc, use_container_width=True)
        
        with col2:
            fig_humidity_cc = px.line(
                filtered_cc,
                x='timestamp',
                y='humidity',
                color='shipment_id',
                title='Humidity Monitoring',
                labels={'humidity': 'Humidity (%)'}
            )
            st.plotly_chart(fig_humidity_cc, use_container_width=True)
        
        # GPS tracking map
        st.subheader("🗺️ Real-Time GPS Tracking")
        latest_positions = filtered_cc.groupby('shipment_id').last().reset_index()
        
        if not latest_positions.empty:
            fig_map = px.scatter_mapbox(
                latest_positions,
                lat='gps_lat',
                lon='gps_lon',
                color='cold_storage_temp',
                size='humidity',
                hover_data=['shipment_id', 'truck_id', 'cargo_type', 'door_status'],
                title='Current Shipment Locations',
                mapbox_style='open-street-map',
                height=500,
                color_continuous_scale='RdYlBu_r'
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        
        # Shipment status table
        st.subheader("Shipment Status Overview")
        shipment_table = latest_positions[['shipment_id', 'truck_id', 'cargo_type', 'cold_storage_temp', 'target_temp', 'humidity', 'door_status']].copy()
        shipment_table.columns = ['Shipment', 'Truck', 'Cargo', 'Current Temp (°C)', 'Target Temp (°C)', 'Humidity (%)', 'Door Status']
        
        def highlight_temp(row):
            colors = []
            for col in row.index:
                if col == 'Current Temp (°C)':
                    current = row[col]
                    target = row['Target Temp (°C)']
                    if abs(current - target) > 5:
                        colors.append('background-color: #ffcccc')
                    elif abs(current - target) > 3:
                        colors.append('background-color: #fff2cc')
                    else:
                        colors.append('background-color: #ccffcc')
                elif col == 'Door Status' and row[col] == 'open':
                    colors.append('background-color: #fff2cc')
                else:
                    colors.append('')
            return colors
        
        st.dataframe(shipment_table.style.apply(highlight_temp, axis=1), use_container_width=True)
    
    # Tab 6: Warehouse Environment
    with tab6:
        st.header("🏪 Warehouse Environment Monitoring")
        
        # Filters
        selected_warehouse = st.selectbox(
            "Select Warehouse:",
            ["All Warehouses"] + WAREHOUSES,
            key="wh_env"
        )
        
        # Filter data
        filtered_wh = warehouse_env_data.copy()
        if selected_warehouse != "All Warehouses":
            filtered_wh = filtered_wh[filtered_wh['warehouse_id'] == selected_warehouse]
        
        # Warehouse KPIs
        latest_wh = filtered_wh.groupby('warehouse_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_temp_wh = latest_wh['temp'].mean()
            st.metric("Avg Temperature", f"{avg_temp_wh:.1f}°C")
        
        with col2:
            avg_humidity_wh = latest_wh['humidity'].mean()
            st.metric("Avg Humidity", f"{avg_humidity_wh:.1f}%")
        
        with col3:
            avg_co2_wh = latest_wh['co2'].mean()
            co2_status_wh = "🔴" if avg_co2_wh > 1500 else "🟡" if avg_co2_wh > 1000 else "🟢"
            st.metric("Avg CO2", f"{avg_co2_wh:.0f} ppm {co2_status_wh}")
        
        with col4:
            avg_aqi_wh = latest_wh['aqi'].mean()
            aqi_status_wh = "🔴" if avg_aqi_wh > 100 else "🟡" if avg_aqi_wh > 50 else "🟢"
            st.metric("Avg AQI", f"{avg_aqi_wh:.0f} {aqi_status_wh}")
        
        # Warehouse environment charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp_wh = px.line(
                filtered_wh,
                x='timestamp',
                y='temp',
                color='warehouse_id',
                title='Warehouse Temperature',
                labels={'temp': 'Temperature (°C)'}
            )
            st.plotly_chart(fig_temp_wh, use_container_width=True)
        
        with col2:
            fig_co2_wh = px.line(
                filtered_wh,
                x='timestamp',
                y='co2',
                color='warehouse_id',
                title='Warehouse CO2 Levels',
                labels={'co2': 'CO2 (ppm)'}
            )
            fig_co2_wh.add_hline(y=1500, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
            st.plotly_chart(fig_co2_wh, use_container_width=True)
        
        # Combined environmental metrics
        fig_combined = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Temperature', 'Humidity', 'CO2', 'AQI'],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        for warehouse in latest_wh['warehouse_id'].unique():
            wh_data = filtered_wh[filtered_wh['warehouse_id'] == warehouse]
            
            fig_combined.add_trace(
                go.Scatter(x=wh_data['timestamp'], y=wh_data['temp'], name=f'{warehouse} - Temp', showlegend=False),
                row=1, col=1
            )
            fig_combined.add_trace(
                go.Scatter(x=wh_data['timestamp'], y=wh_data['humidity'], name=f'{warehouse} - Humidity', showlegend=False),
                row=1, col=2
            )
            fig_combined.add_trace(
                go.Scatter(x=wh_data['timestamp'], y=wh_data['co2'], name=f'{warehouse} - CO2', showlegend=False),
                row=2, col=1
            )
            fig_combined.add_trace(
                go.Scatter(x=wh_data['timestamp'], y=wh_data['aqi'], name=f'{warehouse} - AQI', showlegend=False),
                row=2, col=2
            )
        
        fig_combined.update_layout(height=600, title_text="Warehouse Environmental Monitoring")
        st.plotly_chart(fig_combined, use_container_width=True)
    
    # Tab 7: Inventory Tracking
    with tab7:
        st.header("📦 Inventory Level Tracking")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_sku = st.selectbox(
                "Select SKU:",
                ["All SKUs"] + [s for s in inventory_data['sku_id'].unique()],
                key="inv_sku"
            )
        with col2:
            selected_warehouse_inv = st.selectbox(
                "Select Warehouse:",
                ["All Warehouses"] + WAREHOUSES,
                key="inv_warehouse"
            )
        
        # Filter data
        filtered_inv = inventory_data.copy()
        if selected_sku != "All SKUs":
            filtered_inv = filtered_inv[filtered_inv['sku_id'] == selected_sku]
        if selected_warehouse_inv != "All Warehouses":
            filtered_inv = filtered_inv[filtered_inv['warehouse_id'] == selected_warehouse_inv]
        
        # Inventory alerts
        current_inv_alerts = [a for a in inv_alerts 
                            if (selected_sku == "All SKUs" or a['sku'] == selected_sku) and
                               (selected_warehouse_inv == "All Warehouses" or a['warehouse'] == selected_warehouse_inv)]
        if current_inv_alerts:
            st.warning(f"⚠️ {len(current_inv_alerts)} Low Stock Alerts")
            for alert in current_inv_alerts[:5]:
                st.warning(f"**{alert['sku']}** at {alert['warehouse']}: {alert['stock_level']} units (reorder at {alert['reorder_point']})")
        
        # Inventory KPIs
        latest_inv = filtered_inv.groupby('sku_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_skus = len(latest_inv)
            st.metric("Total SKUs", total_skus)
        
        with col2:
            total_stock = latest_inv['stock_level'].sum()
            st.metric("Total Stock", f"{total_stock:.0f} units")
        
        with col3:
            low_stock_count = len(latest_inv[latest_inv['stock_level'] <= latest_inv['reorder_point']])
            st.metric("Low Stock Items", low_stock_count)
        
        with col4:
            restock_needed = len(latest_inv[latest_inv['restock_eta'].notna()])
            st.metric("Restock Scheduled", restock_needed)
        
        # Inventory charts
        if selected_sku != "All SKUs":
            # Individual SKU tracking
            sku_data = filtered_inv[filtered_inv['sku_id'] == selected_sku]
            
            fig_stock_trend = px.line(
                sku_data,
                x='timestamp',
                y='stock_level',
                title=f'Stock Level Trend - {selected_sku}',
                labels={'stock_level': 'Stock Level (units)'}
            )
            
            # Add reorder point line
            reorder_point = sku_data['reorder_point'].iloc[0]
            fig_stock_trend.add_hline(
                y=reorder_point,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Reorder Point ({reorder_point})"
            )
            st.plotly_chart(fig_stock_trend, use_container_width=True)
        
        else:
            # Multi-SKU comparison
            col1, col2 = st.columns(2)
            
            with col1:
                # Current stock levels
                fig_current_stock = px.bar(
                    latest_inv.head(15),  # Show top 15
                    x='sku_id',
                    y='stock_level',
                    title='Current Stock Levels (Top 15 SKUs)',
                    labels={'stock_level': 'Stock Level (units)'}
                )
                fig_current_stock.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_current_stock, use_container_width=True)
            
            with col2:
                # Stock vs reorder point
                comparison_data = latest_inv.head(15).copy()
                comparison_data['reorder_gap'] = comparison_data['stock_level'] - comparison_data['reorder_point']
                
                fig_reorder_gap = px.bar(
                    comparison_data,
                    x='sku_id',
                    y='reorder_gap',
                    color='reorder_gap',
                    title='Stock vs Reorder Point Gap',
                    labels={'reorder_gap': 'Units Above/Below Reorder Point'},
                    color_continuous_scale='RdYlGn'
                )
                fig_reorder_gap.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_reorder_gap, use_container_width=True)
        
        # Low stock items
        st.subheader("Low Stock Items Requiring Attention")
        low_stock_items = latest_inv[latest_inv['stock_level'] <= latest_inv['reorder_point']]
        
        if not low_stock_items.empty:
            low_stock_display = low_stock_items[['sku_id', 'warehouse_id', 'stock_level', 'reorder_point', 'restock_eta']].copy()
            low_stock_display.columns = ['SKU', 'Warehouse', 'Current Stock', 'Reorder Point', 'Restock ETA (hrs)']
            st.dataframe(low_stock_display, use_container_width=True)
        else:
            st.success("✅ All items are above reorder points")
    
    # Tab 8: Package Security
    with tab8:
        st.header("🔒 Package Tampering Detection")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_package = st.selectbox(
                "Select Package:",
                ["All Packages"] + PACKAGES[:20],  # Show first 20 for performance
                key="tamper_package"
            )
        with col2:
            tamper_period = st.selectbox(
                "Time Period:",
                ["Last 24 Hours", "Last 3 Days", "Last 7 Days"],
                index=1,
                key="tamper_period"
            )
        
        # Filter data
        if tamper_period == "Last 24 Hours":
            filtered_tamper = tampering_data[tampering_data['timestamp'] >= tampering_data['timestamp'].max() - timedelta(days=1)]
        elif tamper_period == "Last 3 Days":
            filtered_tamper = tampering_data[tampering_data['timestamp'] >= tampering_data['timestamp'].max() - timedelta(days=3)]
        else:
            filtered_tamper = tampering_data
        
        if selected_package != "All Packages":
            filtered_tamper = filtered_tamper[filtered_tamper['package_id'] == selected_package]
        
        # Tampering alerts
        current_tamper_alerts = [a for a in tamper_alerts 
                               if selected_package == "All Packages" or a['package'] == selected_package]
        if current_tamper_alerts:
            st.error(f"🚨 {len(current_tamper_alerts)} Package Security Alerts")
            for alert in current_tamper_alerts[:5]:
                if alert['type'] == 'Broken Seal':
                    st.error(f"**{alert['package']}**: {alert['type']} - Status: {alert['status']}")
                else:
                    st.warning(f"**{alert['package']}**: {alert['type']} = {alert['value']} (threshold: {alert['threshold']})")
        
        # Security KPIs
        latest_tamper = filtered_tamper.groupby('package_id').last().reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_packages = len(latest_tamper)
            st.metric("Monitored Packages", total_packages)
        
        with col2:
            high_tilt_count = len(latest_tamper[latest_tamper['tilt_angle'] > 45])
            st.metric("High Tilt Alerts", high_tilt_count)
        
        with col3:
            high_light_count = len(latest_tamper[latest_tamper['light_exposure_lux'] > 1000])
            st.metric("Light Exposure Alerts", high_light_count)
        
        with col4:
            broken_seal_count = len(latest_tamper[latest_tamper['seal_status'] == 'broken'])
            st.metric("Broken Seals", broken_seal_count)
        
        # Tampering detection charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_tilt = px.scatter(
                filtered_tamper,
                x='timestamp',
                y='tilt_angle',
                color='package_id',
                title='Package Tilt Angle Detection',
                labels={'tilt_angle': 'Tilt Angle (degrees)'}
            )
            fig_tilt.add_hline(y=45, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
            st.plotly_chart(fig_tilt, use_container_width=True)
        
        with col2:
            fig_light = px.scatter(
                filtered_tamper,
                x='timestamp',
                y='light_exposure_lux',
                color='package_id',
                title='Light Exposure Detection',
                labels={'light_exposure_lux': 'Light Exposure (lux)'}
            )
            fig_light.add_hline(y=1000, line_dash="dash", line_color="red", annotation_text="Alert Threshold")
            st.plotly_chart(fig_light, use_container_width=True)
        
        # Seal status analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Seal status distribution
            seal_counts = latest_tamper['seal_status'].value_counts()
            fig_seal = px.pie(
                values=seal_counts.values,
                names=seal_counts.index,
                title='Package Seal Status Distribution',
                color_discrete_map={'intact': 'green', 'broken': 'red'}
            )
            st.plotly_chart(fig_seal, use_container_width=True)
        
        with col2:
            # Security risk assessment
            latest_tamper['risk_score'] = (
                (latest_tamper['tilt_angle'] > 45).astype(int) * 30 +
                (latest_tamper['light_exposure_lux'] > 1000).astype(int) * 40 +
                (latest_tamper['seal_status'] == 'broken').astype(int) * 50
            )
            
            risk_distribution = pd.cut(latest_tamper['risk_score'], 
                                     bins=[0, 20, 50, 100], 
                                     labels=['Low', 'Medium', 'High']).value_counts()
            
            fig_risk = px.bar(
                x=risk_distribution.index,
                y=risk_distribution.values,
                title='Package Security Risk Distribution',
                labels={'x': 'Risk Level', 'y': 'Number of Packages'},
                color=risk_distribution.index,
                color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'}
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Suspected tampering events
        st.subheader("Suspected Tampering Events")
        suspected_packages = latest_tamper[
            (latest_tamper['tilt_angle'] > 45) |
            (latest_tamper['light_exposure_lux'] > 1000) |
            (latest_tamper['seal_status'] == 'broken')
        ]
        
        if not suspected_packages.empty:
            tamper_table = suspected_packages[['package_id', 'tilt_angle', 'light_exposure_lux', 'seal_status']].copy()
            tamper_table.columns = ['Package ID', 'Tilt Angle (°)', 'Light Exposure (lux)', 'Seal Status']
            
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
            
            st.dataframe(tamper_table.style.apply(highlight_tampering, axis=1), use_container_width=True)
        else:
            st.success("✅ No suspicious tampering activity detected")

if __name__ == "__main__":
    main()
