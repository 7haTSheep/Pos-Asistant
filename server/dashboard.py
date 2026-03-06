import streamlit as st
import os
import time
import json
from datetime import datetime, timedelta
from woocommerce import API
from dotenv import load_dotenv
from database import Database
from expiry_logic import determine_expiry_severity

# Load environment variables
load_dotenv()

# Setup WooCommerce API
def get_wc_api():
    wc_url = os.getenv("WC_URL") or "http://localhost"
    # Sanitization (copying logic from main.py)
    if "/wp-includes" in wc_url:
        wc_url = wc_url.split("/wp-includes")[0]
    if "/wp-admin" in wc_url:
        wc_url = wc_url.split("/wp-admin")[0]

    return API(
        url=wc_url,
        consumer_key=os.getenv("WC_CONSUMER_KEY"),
        consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
        version="wc/v3",
        timeout=10
    )

wcapi = get_wc_api()

# State Management
STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"session_active": False, "session_end_time": 0, "last_run": 0, "last_expiry_run": 0, "alerts": []}
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            if not isinstance(state, dict):
                return {"session_active": False, "session_end_time": 0, "last_run": 0, "last_expiry_run": 0, "alerts": []}
            state.setdefault("alerts", [])
            state.setdefault("last_expiry_run", 0)
            return state
    except:
         return {"session_active": False, "session_end_time": 0, "last_run": 0, "last_expiry_run": 0, "alerts": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Streamlit UI
st.set_page_config(page_title="Inventory Automator", layout="wide")
st.title("Inventory Automation Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["Inventory Manager", "Automation Control", "Price Inventory", "Expiry Alerts"])

with tab1:
    st.header("Inventory Management")
    
    # Fetch Products
    try:
        response = wcapi.get("products", params={"per_page": 20})
        if response.status_code == 200:
            products = response.json()
        else:
            st.error(f"Failed to fetch products. API Code: {response.status_code}")
            st.text(response.text)
            products = []
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        products = []

    # Display Products
    if products:
        for p in products:
            with st.expander(f"{p['name']} (ID: {p['id']})"):
                col1, col2 = st.columns(2)
                
                # Update Form
                with col1:
                    new_name = st.text_input("Name", p['name'], key=f"name_{p['id']}")
                    if st.button("Update Name", key=f"upd_{p['id']}"):
                        try:
                            r = wcapi.put(f"products/{p['id']}", {"name": new_name})
                            if r.status_code == 200:
                                st.success("Updated!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update.")
                        except Exception as e:
                             st.error(f"Error: {e}")

                # Delete Button
                with col2:
                    st.write("Actions")
                    if st.button("Delete Product", key=f"del_{p['id']}", type="primary"):
                        try:
                            r = wcapi.delete(f"products/{p['id']}", params={"force": True})
                            if r.status_code == 200:
                                st.success("Deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete.")
                        except Exception as e:
                             st.error(f"Error: {e}")
    else:
        st.info("No products found or connection failed.")

    st.divider()
    st.subheader("Add New Product")
    with st.form("new_product"):
        name = st.text_input("Product Name")
        sku = st.text_input("SKU")
        price = st.text_input("Regular Price")
        submitted = st.form_submit_button("Create Product")
        
        if submitted and name:
            data = {"name": name, "type": "simple", "regular_price": price or "0"}
            if sku: data["sku"] = sku
            
            try:
                r = wcapi.post("products", data)
                if r.status_code == 201:
                     st.success("Product Created!")
                     time.sleep(1)
                     st.rerun()
                else:
                    st.error(f"Failed: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header("Automation Scheduler")
    
    state = load_state()
    
    now_ts = time.time()
    is_active = state.get("session_active", False)
    end_time = state.get("session_end_time", 0)
    
    # Check if time expired
    if is_active and now_ts > end_time:
        is_active = False
        state["session_active"] = False
        save_state(state)
        st.rerun()

    if is_active:
        remaining = int((end_time - now_ts) / 60)
        st.success(f"Session Active! Monitoring for another {remaining} minutes.")
        st.info("The backend script will check for updates every 10 minutes and expiry alerts every hour.")

        if st.button("Stop Session Early"):
            state["session_active"] = False
            save_state(state)
            st.rerun()
    else:
        st.warning("Automation is IDLE.")
        st.write("Start a 40-minute monitoring session. The script will run checks every 10 minutes (products) and every hour (expiry alerts).")

        if st.button("Start 40min Session"):
            state["session_active"] = True
            state["session_end_time"] = time.time() + (40 * 60) # 40 mins from now
            state["last_run"] = 0  # Trigger immediate product check
            state["last_expiry_run"] = 0  # Trigger immediate expiry check
            save_state(state)
            st.rerun()
    
    st.write("---")
    st.caption("Ensure main.py is running in the background to perform the actual checks.")

with tab3:
    st.header("Price Inventory (Local DB)")
    db = Database()
    
    if st.button("Refresh Inventory"):
        st.rerun()
        
    df = db.get_price_inventory()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.caption(f"Total Products: {len(df)}")
    else:
        st.warning("No inventory data found or database connection failed.")
        st.info("Ensure the 'dummydatabase3' is accessible on localhost (root/no-password).")

with tab4:
    st.header("Expiry Alerts")
    db = Database()
    today = datetime.utcnow().date()
    entries = db.get_pending_expiries()

    # Categorize alerts by severity
    meat_urgent = []
    standard_week = []
    standard_month = []
    meat_stale = []

    for entry in entries:
        severity = determine_expiry_severity(entry, today)
        if not severity:
            continue
        if severity == "meat-urgent":
            meat_urgent.append(entry)
        elif severity == "meat-stale":
            meat_stale.append(entry)
        elif severity == "standard-week":
            standard_week.append(entry)
        elif severity == "standard-month":
            standard_month.append(entry)

    # Display alerts by category
    if not any([meat_urgent, meat_stale, standard_week, standard_month]):
        st.success("No expiry alerts in the system.")
    else:
        # Meat Urgent (48h before expiry)
        if meat_urgent:
            st.subheader("🚨 Meat - Urgent (48h before expiry)")
            for entry in meat_urgent:
                expiry_date = entry.get("expiry_date")
                due_days = (expiry_date - today).days if expiry_date else None
                st.markdown(
                    f"<div style='padding:12px; border-radius:12px; background:#fee2e2; border:2px solid #ef4444; margin-bottom:8px;'>"
                    f"<strong>{entry.get('name')} ({entry.get('sku')})</strong><br/>"
                    f"Expiry: {expiry_date} {'(' + str(due_days) + ' days)' if due_days is not None else ''}<br/>"
                    f"<span style='font-size:12px; color:#dc2626;'>⚠️ High priority - process immediately!</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Meat Stale (3+ days after intake)
        if meat_stale:
            st.subheader("⚠️ Meat - Stale (3+ days in storage)")
            for entry in meat_stale:
                expiry_date = entry.get("expiry_date")
                due_days = (expiry_date - today).days if expiry_date else None
                created_at = entry.get("created_at")
                st.markdown(
                    f"<div style='padding:12px; border-radius:12px; background:#fef3c7; border:2px solid #f59e0b; margin-bottom:8px;'>"
                    f"<strong>{entry.get('name')} ({entry.get('sku')})</strong><br/>"
                    f"Expiry: {expiry_date} {'(' + str(due_days) + ' days)' if due_days is not None else ''}<br/>"
                    f"Intake: {created_at}<br/>"
                    f"<span style='font-size:12px; color:#d97706;'>⚠️ Been in storage too long</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Standard Week (7 days before expiry)
        if standard_week:
            st.subheader("📅 Standard - Expiring within a week")
            for entry in standard_week:
                expiry_date = entry.get("expiry_date")
                due_days = (expiry_date - today).days if expiry_date else None
                st.markdown(
                    f"<div style='padding:12px; border-radius:12px; background:#fef3c7; border:1px solid #f59e0b; margin-bottom:8px;'>"
                    f"<strong>{entry.get('name')} ({entry.get('sku')})</strong><br/>"
                    f"Expiry: {expiry_date} {'(' + str(due_days) + ' days)' if due_days is not None else ''}<br/>"
                    f"<span style='font-size:12px; color:#92400e;'>Action needed within the week</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Standard Month (30 days before expiry)
        if standard_month:
            st.subheader("📋 Standard - Expiring within a month")
            for entry in standard_month:
                expiry_date = entry.get("expiry_date")
                due_days = (expiry_date - today).days if expiry_date else None
                st.markdown(
                    f"<div style='padding:12px; border-radius:12px; background:#ecfdf5; border:1px solid #10b981; margin-bottom:8px;'>"
                    f"<strong>{entry.get('name')} ({entry.get('sku')})</strong><br/>"
                    f"Expiry: {expiry_date} {'(' + str(due_days) + ' days)' if due_days is not None else ''}<br/>"
                    f"<span style='font-size:12px; color:#047857;'>Plan to use soon</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Recent Alert Log from state.json
    state = load_state()
    recent_alerts = state.get("alerts", [])
    if recent_alerts:
        st.divider()
        st.subheader("📜 Recent Alert Log (from Automation Service)")
        st.caption("Alerts registered by the hourly expiry scheduler")
        for alert in recent_alerts[:10]:
            severity = alert.get('severity', 'unknown')
            bg_color = "#fee2e2" if severity in ["meat-urgent", "meat-stale", "standard-week"] else "#ecfdf5"
            st.markdown(
                f"<div style='padding:10px; border-radius:10px; background:{bg_color}; border:1px solid #cbd5e1; margin-bottom:6px;'>"
                f"<strong>{alert.get('name')} ({alert.get('sku')})</strong><br/>"
                f"Triggered at {alert.get('timestamp')} - Severity: {alert.get('severity').replace('-', ' ').title()}<br/>"
                f"Due in {alert.get('due_in_days')} days"
                f"</div>",
                unsafe_allow_html=True,
            )
