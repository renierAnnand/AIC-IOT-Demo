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
    """Generate simulated IoT sensor data for factory machines (last 7 days)"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10T')
    
    data = []
    
    for machine in MACHINES:
        machine_uptime = 0
        daily_uptime_reset = start_time.date()
        
        for timestamp in timestamps:
            if timestamp.date() != daily_uptime_reset:
                machine_uptime = 0
                daily_uptime_reset = timestamp.date()
            
            machine_uptime += 1/6
            
            row = {
                'Timestamp': timestamp,
                'Machine_ID': machine,
                'Machine_Uptime': round(machine_uptime, 2)
            }
            
            for sensor, (min_val, max_val) in SENSOR_RANGES.items():
                hour_factor = np.sin(2 * np.pi * timestamp.hour / 24) * 0.1
                base_value = (min_val + max_val) / 2 + (max_val - min_val) * hour_factor
                noise = np.random.normal(0, (max_val - min_val) * 0.05)
                
                if random.random() < 0.05:
                    anomaly = np.random.normal(0, (max_val - min_val) * 0.2)
                    noise += anomaly
                
                value = base_value + noise
                value = np.clip(value, min_val, max_val)
                row[sensor] = round(value, 2)
            
            data.append(row)
    
    return pd.DataFrame(data)

@st.cache_data
def generate_cold_chain_data():
    """Generate cold chain monitoring data (last 7 days, every 20 minutes)"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='20T')
    
    data = []
    shipment_ids = [f'SHIP_{i:04d}' for i in range(100, 131)]
    
    for shipment_id in shipment_ids:
        truck_id = random.choice(TRUCK_IDS)
        route_coords = list(ROUTE_COORDINATES)
        random.shuffle(route_coords)
        
        for i, timestamp in enumerate(timestamps):
            # Simulate truck moving along route
            coord_index = min(i // 20, len(route_coords) - 1)
            lat, lon = route_coords[coord_index]
            
            # Add small random variations to coordinates
            lat += np.random.normal(0, 0.01)
            lon += np.random.normal(0, 0.01)
            
            # Temperature should be around 2-8°C for cold chain
            base_temp = 4.0
            temp_variation = np.random.normal(0, 1.5)
            
            # Occasionally simulate temperature excursions (5% chance)
            if random.random() < 0.05:
                temp_variation += np.random.uniform(5, 15)
            
            cold_storage_temp = base_temp + temp_variation
            
            # Humidity around 60-75%
            humidity = np.random.uniform(55, 80)
            
            # Door status (mostly closed, occasionally open for 1-2 readings)
            door_status = 'closed'
            if random.random() < 0.02:
                door_status = 'open'
            
            data.append({
                'timestamp': timestamp,
                'shipment_id': shipment_id,
                'truck_id': truck_id,
                'cold_storage_temp': round(cold_storage_temp, 1),
                'humidity': round(humidity, 1),
                'latitude': round(lat, 4),
                'longitude': round(lon, 4),
                'door_status': door_status
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_warehouse_environmental_data():
    """Generate warehouse environmental monitoring data"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='15T')
    
    data = []
    
    for warehouse_id in WAREHOUSES:
        for timestamp in timestamps:
            # CO2 levels (normal: 400-1000 ppm, alerts > 1500)
            base_co2 = 600
            co2_variation = np.random.normal(0, 150)
            
            # Business hours effect (higher CO2 during work hours)
            if 8 <= timestamp.hour <= 18:
                co2_variation += np.random.uniform(100, 400)
            
            # Occasional spikes (3% chance)
            if random.random() < 0.03:
                co2_variation += np.random.uniform(800, 1200)
            
            co2_level = max(400, base_co2 + co2_variation)
            
            # Warehouse temperature (should be controlled)
            temp_warehouse = np.random.normal(22, 2)
            
            # Humidity
            humidity = np.random.normal(45, 8)
            
            # Air Quality Index (0-500 scale, >100 is unhealthy)
            base_aqi = 35
            aqi_variation = np.random.normal(0, 20)
            
            # Correlate with CO2 levels
            if co2_level > 1200:
                aqi_variation += np.random.uniform(30, 80)
            
            air_quality_index = max(0, base_aqi + aqi_variation)
            
            data.append({
                'timestamp': timestamp,
                'warehouse_id': warehouse_id,
                'co2_level_ppm': round(co2_level, 0),
                'temp_warehouse': round(temp_warehouse, 1),
                'humidity': round(humidity, 1),
                'air_quality_index': round(air_quality_index, 0)
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_inventory_data():
    """Generate inventory monitoring data"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7) 
    timestamps = pd.date_range(start=start_time, end=end_time, freq='30T')
    
    data = []
    
    for sku_id in SKU_LIST:
        warehouse_id = random.choice(WAREHOUSES)
        
        # Set initial stock level and reorder threshold
        initial_stock = np.random.randint(50, 500)
        reorder_threshold = np.random.randint(20, 80)
        
        current_stock = initial_stock
        
        for timestamp in timestamps:
            # Simulate stock consumption (random decreases)
            if random.random() < 0.3:  # 30% chance of stock movement
                consumption = np.random.randint(1, 15)
                current_stock = max(0, current_stock - consumption)
            
            # Simulate restocking
            restock_scheduled = False
            if current_stock <= reorder_threshold:
                restock_scheduled = True
                # Sometimes stock gets replenished
                if random.random() < 0.1:  # 10% chance of restocking
                    current_stock += np.random.randint(100, 300)
                    restock_scheduled = False
            
            data.append({
                'timestamp': timestamp,
                'sku_id': sku_id,
                'warehouse_id': warehouse_id,
                'stock_level': current_stock,
                'reorder_threshold': reorder_threshold,
                'restock_scheduled': restock_scheduled
            })
    
    return pd.DataFrame(data)

@st.cache_data
def generate_package_tampering_data():
    """Generate package tampering detection data"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='25T')
    
    data = []
    package_ids = [f'PKG_{i:06d}' for i in range(100000, 100201)]
    
    for package_id in package_ids:
        for timestamp in timestamps:
            # Tilt angle (normal: 0-10°, alert > 45°)
            base_tilt = np.random.uniform(0, 5)
            
            # Occasional high tilt events (2% chance)
            if random.random() < 0.02:
                base_tilt += np.random.uniform(40, 80)
            
            tilt_angle = base_tilt
            
            # Light exposure (normal: 0-100 lux, alert > 1000)
            base_light = np.random.uniform(0, 50)
            
            # Occasional high light exposure (tampering attempts)
            if random.random() < 0.015:
                base_light += np.random.uniform(500, 2000)
            
            light_exposure = base_light
            
            # Seal status (mostly intact, occasionally broken)
            seal_status = 'intact'
            if random.random() < 0.005:  # 0.5% chance of broken seal
                seal_status = 'broken'
            
            data.append({
                'timestamp': timestamp,
                'package_id': package_id,
                'tilt_angle': round(tilt_angle, 1),
                'light_exposure': round(light_exposure, 0),
                'seal_status': seal_status
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