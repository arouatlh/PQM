import streamlit as st
import pandas as pd
import sqlite3
from pymodbus.client import ModbusTcpClient
import time
import random

# --- Settings ---
METER_IP = "192.168.1.100"  # replace with your PQM meter IP later
METER_PORT = 502
DB_FILE = "pqm_data.db"

# --- Connect to Modbus device ---
client = ModbusTcpClient(METER_IP, port=METER_PORT)

# --- Create database if not exists ---
conn = sqlite3.connect(DB_FILE)
conn.execute("""
CREATE TABLE IF NOT EXISTS readings(
  timestamp TEXT,
  voltage REAL,
  current REAL,
  power REAL
)
""")
conn.commit()

# --- Streamlit UI ---
st.title("🔋 PQM 1000s Local Dashboard")
st.write("Monitoring Voltage, Current, and Power in Real-Time")

if client.connect():
    try:
        rr = client.read_holding_registers(0, 6)  # adjust register addresses later
        voltage = rr.registers[0] / 10.0
        current = rr.registers[1] / 100.0
        power = rr.registers[2]
    except Exception as e:
        st.error(f"Error reading data: {e}")
        voltage, current, power = (0, 0, 0)
else:
    st.warning("Unable to connect to PQM 1000s meter — running in simulation mode.")
    voltage = random.uniform(210, 240)   # simulate voltage
    current = random.uniform(0, 20)      # simulate current
    power = voltage * current * random.uniform(0.8, 1.0)  # simulate power

# --- Save data locally ---
conn.execute("INSERT INTO readings VALUES (?,?,?,?)",
             (time.strftime("%Y-%m-%d %H:%M:%S"), voltage, current, power))
conn.commit()

# --- Display ---
st.metric("Voltage (V)", f"{voltage:.1f}")
st.metric("Current (A)", f"{current:.2f}")
st.metric("Power (W)", f"{power:.0f}")

# --- Show chart ---
df = pd.read_sql("SELECT * FROM readings ORDER BY timestamp DESC LIMIT 20", conn)
st.line_chart(df.set_index("timestamp")[["voltage", "current", "power"]])

client.close()
conn.close()
