"""
Warehouse Local Agent - Windows Desktop Application

A desktop application for warehouse inventory management.
Connects to the FastAPI backend for all inventory operations.

Features:
- Intake: Add stock to storage
- Dispatch: Remove stock (FIFO)
- Transfer: Move stock to front shelves
- Sales: Sell units from front
- Adjustments: Manual corrections
- Live Updates: WebSocket real-time stock updates
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
import asyncio
import websockets
import requests
from datetime import datetime, date
from typing import Optional, List, Dict
import os

# Configuration
API_BASE_URL = os.environ.get("WAREHOUSE_API_URL", "http://localhost:8000")
WS_URL = API_BASE_URL.replace("http", "ws").replace("https", "wss") + "/ws"


class WarehouseAgent:
    """Main Warehouse Agent Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏷 Warehouse Local Agent")
        self.root.geometry("1200x800")
        
        # State
        self.current_user_id = None
        self.device_id = f"warehouse-pc-{os.getpid()}"
        self.ws_connected = False
        self.current_sku = None
        
        # Setup UI
        self.setup_styles()
        self.create_menu()
        self.create_main_layout()
        self.connect_websocket()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_current_view)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_main_layout(self):
        """Create main application layout"""
        # Top bar with status
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(top_frame, text="🏷 Warehouse Local Agent", style='Title.TLabel').pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(top_frame, text="🔴 Disconnected", style='Error.TLabel')
        self.status_label.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_intake_tab()
        self.create_dispatch_tab()
        self.create_transfer_tab()
        self.create_sales_tab()
        self.create_adjustment_tab()
        self.create_inventory_tab()
        
    def create_intake_tab(self):
        """Create Intake tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="📥 Intake")
        
        # SKU
        ttk.Label(frame, text="SKU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.intake_sku = ttk.Entry(frame, width=40)
        self.intake_sku.grid(row=0, column=1, pady=5, padx=5)
        
        # Product Name
        ttk.Label(frame, text="Product Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.intake_name = ttk.Entry(frame, width=40)
        self.intake_name.grid(row=1, column=1, pady=5, padx=5)
        
        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.intake_quantity = ttk.Spinbox(frame, from_=1, to=10000, width=20)
        self.intake_quantity.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Storage Slot
        ttk.Label(frame, text="Storage Slot:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.intake_slot = ttk.Entry(frame, width=20)
        self.intake_slot.insert(0, "STORAGE-A1")
        self.intake_slot.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Supplier
        ttk.Label(frame, text="Supplier:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.intake_supplier = ttk.Entry(frame, width=40)
        self.intake_supplier.grid(row=4, column=1, pady=5, padx=5)
        
        # Expiry Date
        ttk.Label(frame, text="Expiry Date (YYYY-MM-DD):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.intake_expiry = ttk.Entry(frame, width=20)
        self.intake_expiry.grid(row=5, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Submit button
        ttk.Button(frame, text="✅ Submit Intake", command=self.submit_intake).grid(row=6, column=1, pady=20, sticky=tk.W)
        
        # Result display
        self.intake_result = scrolledtext.ScrolledText(frame, width=60, height=10)
        self.intake_result.grid(row=7, column=0, columnspan=2, pady=10)
        
    def create_dispatch_tab(self):
        """Create Dispatch tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="📤 Dispatch")
        
        # SKU
        ttk.Label(frame, text="SKU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dispatch_sku = ttk.Entry(frame, width=40)
        self.dispatch_sku.grid(row=0, column=1, pady=5, padx=5)
        
        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dispatch_quantity = ttk.Spinbox(frame, from_=1, to=10000, width=20)
        self.dispatch_quantity.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Source Slot
        ttk.Label(frame, text="Source Slot:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dispatch_slot = ttk.Entry(frame, width=20)
        self.dispatch_slot.insert(0, "STORAGE-A1")
        self.dispatch_slot.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Reason
        ttk.Label(frame, text="Reason:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.dispatch_reason = ttk.Combobox(frame, values=["order-fulfillment", "damaged", "return", "other"])
        self.dispatch_reason.current(0)
        self.dispatch_reason.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Order ID
        ttk.Label(frame, text="Order ID:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.dispatch_order_id = ttk.Entry(frame, width=20)
        self.dispatch_order_id.grid(row=4, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Submit button
        ttk.Button(frame, text="✅ Submit Dispatch", command=self.submit_dispatch).grid(row=5, column=1, pady=20, sticky=tk.W)
        
        # Result display
        self.dispatch_result = scrolledtext.ScrolledText(frame, width=60, height=10)
        self.dispatch_result.grid(row=6, column=0, columnspan=2, pady=10)
        
    def create_transfer_tab(self):
        """Create Transfer tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="🔄 Transfer")
        
        # SKU
        ttk.Label(frame, text="SKU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.transfer_sku = ttk.Entry(frame, width=40)
        self.transfer_sku.grid(row=0, column=1, pady=5, padx=5)
        
        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.transfer_quantity = ttk.Spinbox(frame, from_=1, to=10000, width=20)
        self.transfer_quantity.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Source Slot
        ttk.Label(frame, text="Source Slot (Storage):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.transfer_source = ttk.Entry(frame, width=20)
        self.transfer_source.insert(0, "STORAGE-A1")
        self.transfer_source.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Destination Slot
        ttk.Label(frame, text="Destination Slot (Front):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.transfer_dest = ttk.Entry(frame, width=20)
        self.transfer_dest.insert(0, "FRONT-B2")
        self.transfer_dest.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Preview button
        ttk.Button(frame, text="👁 Preview Transfer", command=self.preview_transfer).grid(row=4, column=0, pady=10)
        ttk.Button(frame, text="✅ Confirm Transfer", command=self.submit_transfer).grid(row=4, column=1, pady=10, sticky=tk.W)
        
        # Result display
        self.transfer_result = scrolledtext.ScrolledText(frame, width=60, height=10)
        self.transfer_result.grid(row=5, column=0, columnspan=2, pady=10)
        
    def create_sales_tab(self):
        """Create Sales tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="💰 Sales")
        
        # SKU
        ttk.Label(frame, text="SKU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sales_sku = ttk.Entry(frame, width=40)
        self.sales_sku.grid(row=0, column=1, pady=5, padx=5)
        
        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sales_quantity = ttk.Spinbox(frame, from_=1, to=1000, width=20)
        self.sales_quantity.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Front Slot
        ttk.Label(frame, text="Front Slot:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.sales_slot = ttk.Entry(frame, width=20)
        self.sales_slot.insert(0, "FRONT-B2")
        self.sales_slot.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Sale Type
        ttk.Label(frame, text="Sale Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.sales_type = ttk.Combobox(frame, values=["loose_units", "full_box"])
        self.sales_type.current(0)
        self.sales_type.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Submit button
        ttk.Button(frame, text="✅ Record Sale", command=self.submit_sale).grid(row=4, column=1, pady=20, sticky=tk.W)
        
        # Result display
        self.sales_result = scrolledtext.ScrolledText(frame, width=60, height=10)
        self.sales_result.grid(row=5, column=0, columnspan=2, pady=10)
        
    def create_adjustment_tab(self):
        """Create Adjustment tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="🔧 Adjustment")
        
        # SKU
        ttk.Label(frame, text="SKU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.adjust_sku = ttk.Entry(frame, width=40)
        self.adjust_sku.grid(row=0, column=1, pady=5, padx=5)
        
        # Quantity Delta (can be negative)
        ttk.Label(frame, text="Quantity Delta (+/-):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.adjust_quantity = ttk.Entry(frame, width=20)
        self.adjust_quantity.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Slot
        ttk.Label(frame, text="Slot:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.adjust_slot = ttk.Entry(frame, width=20)
        self.adjust_slot.insert(0, "STORAGE-A1")
        self.adjust_slot.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Reason
        ttk.Label(frame, text="Reason:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.adjust_reason = ttk.Combobox(frame, values=["damaged-goods", "stocktake-correction", "found-items", "theft-loss"])
        self.adjust_reason.current(0)
        self.adjust_reason.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Notes
        ttk.Label(frame, text="Notes:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.adjust_notes = ttk.Entry(frame, width=40)
        self.adjust_notes.grid(row=4, column=1, pady=5, padx=5)
        
        # Submit button
        ttk.Button(frame, text="✅ Submit Adjustment", command=self.submit_adjustment).grid(row=5, column=1, pady=20, sticky=tk.W)
        
        # Result display
        self.adjust_result = scrolledtext.ScrolledText(frame, width=60, height=10)
        self.adjust_result.grid(row=6, column=0, columnspan=2, pady=10)
        
    def create_inventory_tab(self):
        """Create Inventory Overview tab"""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text="📊 Inventory")
        
        # Search
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(search_frame, text="Search SKU:").pack(side=tk.LEFT)
        self.inventory_search = ttk.Entry(search_frame, width=30)
        self.inventory_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍 Search", command=self.search_inventory).pack(side=tk.LEFT)
        ttk.Button(search_frame, text="🔄 Refresh", command=self.refresh_inventory).pack(side=tk.LEFT, padx=5)
        
        # Inventory display
        self.inventory_display = scrolledtext.ScrolledText(frame, width=80, height=30)
        self.inventory_display.pack(fill=tk.BOTH, expand=True, pady=10)
        
    def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        def ws_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.ws_connect())
            except Exception as e:
                self.root.after(0, lambda: self.log_status(f"WS Error: {e}"))
        
        thread = threading.Thread(target=ws_thread, daemon=True)
        thread.start()
        
    async def ws_connect(self):
        """WebSocket connection handler"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.ws_connected = True
                self.root.after(0, lambda: self.status_label.config(text="🟢 Connected", style='Success.TLabel'))
                
                async for message in websocket:
                    data = json.loads(message)
                    self.root.after(0, lambda d=data: self.handle_ws_message(d))
        except Exception as e:
            self.ws_connected = False
            self.root.after(0, lambda: self.status_label.config(text="🔴 Disconnected", style='Error.TLabel'))
            # Retry after 5 seconds
            self.root.after(5000, self.connect_websocket)
            
    def handle_ws_message(self, data: dict):
        """Handle incoming WebSocket message"""
        event = data.get('event')
        event_data = data.get('data', {})
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if event == 'stock_update':
            msg = f"[{timestamp}] 📦 Stock Update: {event_data.get('sku')} = {event_data.get('total_quantity')} units"
            self.log_to_all_tabs(msg)
        elif event == 'low_stock_alert':
            msg = f"[{timestamp}] ⚠️ LOW STOCK: {event_data.get('sku')} in {event_data.get('slot_name')} ({event_data.get('current_quantity')} remaining)"
            self.log_to_all_tabs(msg, 'warning')
        elif event == 'test':
            msg = f"[{timestamp}] 📡 {event_data.get('message')}"
            self.log_to_all_tabs(msg)
            
    def log_to_all_tabs(self, message: str, level: str = 'info'):
        """Log message to all result tabs"""
        for tab in [self.intake_result, self.dispatch_result, self.transfer_result, 
                    self.sales_result, self.adjust_result, self.inventory_display]:
            tab.insert(tk.END, message + "\n")
            if level == 'warning':
                tab.tag_config('warning', foreground='orange')
                tab.tag_add('warning', 'end-2c', 'end')
            tab.see(tk.END)
            
    def log_status(self, message: str):
        """Log to status area"""
        print(f"[STATUS] {message}")
        
    # ========== API Call Methods ==========
    
    def submit_intake(self):
        """Submit intake request"""
        try:
            payload = {
                "sku": self.intake_sku.get().strip(),
                "name": self.intake_name.get().strip(),
                "quantity": int(self.intake_quantity.get()),
                "slot_id": self.intake_slot.get().strip(),
                "batch_info": {
                    "supplier": self.intake_supplier.get().strip(),
                    "expiry_date": self.intake_expiry.get().strip() or None,
                    "is_meat": False
                }
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/intake", json=payload, timeout=10)
            result = response.json()
            
            self.intake_result.delete(1.0, tk.END)
            self.intake_result.insert(tk.END, json.dumps(result, indent=2))
            
            if response.status_code == 200:
                messagebox.showinfo("Success", result.get('message', 'Intake successful'))
            else:
                messagebox.showerror("Error", result.get('detail', 'Intake failed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def submit_dispatch(self):
        """Submit dispatch request"""
        try:
            payload = {
                "sku": self.dispatch_sku.get().strip(),
                "quantity": int(self.dispatch_quantity.get()),
                "source_slot_id": self.dispatch_slot.get().strip(),
                "reason": self.dispatch_reason.get(),
                "order_id": self.dispatch_order_id.get().strip() or None
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/dispatch", json=payload, timeout=10)
            result = response.json()
            
            self.dispatch_result.delete(1.0, tk.END)
            self.dispatch_result.insert(tk.END, json.dumps(result, indent=2))
            
            if response.status_code == 200:
                messagebox.showinfo("Success", result.get('message', 'Dispatch successful'))
            else:
                messagebox.showerror("Error", result.get('detail', 'Dispatch failed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def preview_transfer(self):
        """Preview transfer before committing"""
        try:
            payload = {
                "sku": self.transfer_sku.get().strip(),
                "quantity": int(self.transfer_quantity.get()),
                "source_slot_id": self.transfer_source.get().strip(),
                "dest_slot_id": self.transfer_dest.get().strip(),
                "confirmed": False
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/transfer-to-front/preview", json=payload, timeout=10)
            result = response.json()
            
            self.transfer_result.delete(1.0, tk.END)
            self.transfer_result.insert(tk.END, json.dumps(result, indent=2))
            
            if result.get('can_proceed'):
                messagebox.showinfo("Preview", f"✅ {result.get('message')}\n\nBatch split required: {result.get('requires_batch_split')}")
            else:
                messagebox.showwarning("Cannot Proceed", result.get('message', 'Transfer cannot proceed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def submit_transfer(self):
        """Submit transfer request"""
        try:
            payload = {
                "sku": self.transfer_sku.get().strip(),
                "quantity": int(self.transfer_quantity.get()),
                "source_slot_id": self.transfer_source.get().strip(),
                "dest_slot_id": self.transfer_dest.get().strip(),
                "confirmed": True
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/transfer-to-front", json=payload, timeout=10)
            result = response.json()
            
            self.transfer_result.delete(1.0, tk.END)
            self.transfer_result.insert(tk.END, json.dumps(result, indent=2))
            
            if response.status_code == 200:
                messagebox.showinfo("Success", result.get('message', 'Transfer successful'))
            else:
                messagebox.showerror("Error", result.get('detail', 'Transfer failed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def submit_sale(self):
        """Submit sale request"""
        try:
            payload = {
                "sku": self.sales_sku.get().strip(),
                "quantity": int(self.sales_quantity.get()),
                "front_slot_id": self.sales_slot.get().strip(),
                "sale_type": self.sales_type.get()
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/sell-single", json=payload, timeout=10)
            result = response.json()
            
            self.sales_result.delete(1.0, tk.END)
            self.sales_result.insert(tk.END, json.dumps(result, indent=2))
            
            if response.status_code == 200:
                messagebox.showinfo("Success", result.get('message', 'Sale recorded'))
            else:
                messagebox.showerror("Error", result.get('detail', 'Sale failed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def submit_adjustment(self):
        """Submit adjustment request"""
        try:
            payload = {
                "sku": self.adjust_sku.get().strip(),
                "quantity_delta": int(self.adjust_quantity.get()),
                "slot_id": self.adjust_slot.get().strip(),
                "reason": self.adjust_reason.get(),
                "notes": self.adjust_notes.get().strip()
            }
            
            response = requests.post(f"{API_BASE_URL}/inventory/adjustment", json=payload, timeout=10)
            result = response.json()
            
            self.adjust_result.delete(1.0, tk.END)
            self.adjust_result.insert(tk.END, json.dumps(result, indent=2))
            
            if response.status_code == 200:
                messagebox.showinfo("Success", result.get('message', 'Adjustment successful'))
            else:
                messagebox.showerror("Error", result.get('detail', 'Adjustment failed'))
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def search_inventory(self):
        """Search inventory by SKU"""
        sku = self.inventory_search.get().strip()
        if not sku:
            messagebox.showwarning("Warning", "Please enter a SKU to search")
            return
            
        try:
            response = requests.get(f"{API_BASE_URL}/inventory/sku/{sku}", timeout=10)
            result = response.json()
            
            self.inventory_display.delete(1.0, tk.END)
            
            if response.status_code == 200:
                output = f"=== Inventory for {sku} ===\n\n"
                output += f"Product: {result.get('name')}\n"
                output += f"Units per Box: {result.get('units_per_box')}\n"
                output += f"Total Quantity: {result.get('total_quantity')}\n"
                output += f"Batch Count: {result.get('batch_count')}\n"
                output += f"Earliest Expiry: {result.get('earliest_expiry')}\n\n"
                output += "=== Slot Breakdown ===\n"
                
                for slot in result.get('slots', []):
                    output += f"  • {slot.get('slot_name')}: {slot.get('quantity')} units\n"
                    
                self.inventory_display.insert(tk.END, output)
            else:
                self.inventory_display.insert(tk.END, f"Error: {result.get('detail', 'Search failed')}")
                
        except Exception as e:
            self.inventory_display.insert(tk.END, f"Error: {str(e)}")
            
    def refresh_inventory(self):
        """Refresh inventory display"""
        self.inventory_search.delete(0, tk.END)
        self.inventory_display.delete(1.0, tk.END)
        self.inventory_display.insert(tk.END, "Enter a SKU and click Search to view inventory.\n\n")
        self.inventory_display.insert(tk.END, "Real-time updates will appear below as they happen:\n")
        
    def refresh_current_view(self):
        """Refresh current tab"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 5:  # Inventory tab
            self.refresh_inventory()
            
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
            "🏷 Warehouse Local Agent\n\n"
            "Version: 1.0.0\n"
            "A desktop application for warehouse inventory management.\n\n"
            "Features:\n"
            "• Intake stock into storage\n"
            "• Dispatch stock (FIFO)\n"
            "• Transfer storage → front\n"
            "• Record sales\n"
            "• Manual adjustments\n"
            "• Real-time WebSocket updates")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = WarehouseAgent(root)
    root.mainloop()


if __name__ == "__main__":
    main()
