import streamlit as st
import os
import time
import json
from datetime import datetime, timedelta
from woocommerce import API
from dotenv import load_dotenv
from database import Database

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
        return {"session_active": False, "session_end_time": 0, "last_run": 0}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
         return {"session_active": False, "session_end_time": 0, "last_run": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Streamlit UI
st.set_page_config(page_title="Inventory Automator", layout="wide")
st.title("Inventory Automation Dashboard")

tab1, tab2, tab3 = st.tabs(["Inventory Manager", "Automation Control", "Price Inventory"])

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
        st.info("The backend script will check for updates every 10 minutes.")
        
        if st.button("Stop Session Early"):
            state["session_active"] = False
            save_state(state)
            st.rerun()
    else:
        st.warning("Automation is IDLE.")
        st.write("Start a 40-minute monitoring session. The script will run checks every 10 minutes.")
        
        if st.button("Start 40min Session"):
            state["session_active"] = True
            state["session_end_time"] = time.time() + (40 * 60) # 40 mins from now
            # Reset last run to forced trigger immediately? Or wait? 
            # Usually users want immediate check then periodic.
            state["last_run"] = 0 
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
