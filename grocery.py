import customtkinter as ctk  # type: ignore[import-not-found]
from tkinter import messagebox, ttk
import datetime
import os
import csv
from collections import Counter

# --- App Configuration ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ProInventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Naija Pro POS & Inventory")
        self.geometry("1100x750")

        # Data Storage
        self.inventory = {} 
        self.cart = {}      
        self.current_bill_total = 0.0
        self.editing_item = None # Keeps track of the item currently being edited

        self.load_data()

        # --- Main Window Grid Configuration ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Header ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1A237E")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🇳🇬 NAIJA PRO POS & INVENTORY", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), 
            text_color="white"
        )
        self.title_label.pack(pady=15)

        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_inv = self.tabview.add("📦 Inventory Manager")
        self.tab_sales = self.tabview.add("🛒 Sales Terminal")
        self.tab_record = self.tabview.add("📊 Sales Record")
        self.tab_reports = self.tabview.add("📈 Reports & Analytics")

        self.setup_inventory_tab()
        self.setup_sales_tab()
        self.setup_record_tab()
        self.setup_reports_tab()
        
        self.refresh_inventory_display()
        self.refresh_sales_dropdown()
        self.refresh_sales_record()
        self.refresh_reports()

    # ==========================================
    # 1. INVENTORY MANAGER TAB
    # ==========================================
    def setup_inventory_tab(self):
        self.tab_inv.grid_rowconfigure(1, weight=1)
        self.tab_inv.grid_columnconfigure(0, weight=1)

        # Input Section
        input_frame = ctk.CTkFrame(self.tab_inv, corner_radius=10)
        input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.lbl_form_title = ctk.CTkLabel(input_frame, text="Add New Stock", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_form_title.grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky="w")

        ctk.CTkLabel(input_frame, text="Item Name:").grid(row=1, column=0, padx=10, pady=10)
        self.inv_name = ctk.CTkEntry(input_frame, width=200)
        self.inv_name.grid(row=1, column=1, padx=10)

        ctk.CTkLabel(input_frame, text="Price (₦):").grid(row=1, column=2, padx=10)
        self.inv_price = ctk.CTkEntry(input_frame, width=120)
        self.inv_price.grid(row=1, column=3, padx=10)

        ctk.CTkLabel(input_frame, text="Quantity:").grid(row=2, column=0, padx=10, pady=10)
        self.inv_qty = ctk.CTkEntry(input_frame, width=200)
        self.inv_qty.grid(row=2, column=1, padx=10)

        # Action Buttons Frame
        btn_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="ew")

        self.btn_save = ctk.CTkButton(btn_frame, text="➕ Add / Update Stock", fg_color="#2E7D32", hover_color="#1B5E20", command=self.add_stock)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Cancel Button (Hidden by default, only shows when editing)
        self.btn_cancel = ctk.CTkButton(btn_frame, text="Cancel Edit", fg_color="#D32F2F", hover_color="#B71C1C", command=self.cancel_edit)

        # Display Section
        self.inv_display = ctk.CTkScrollableFrame(self.tab_inv, label_text="Current Inventory", corner_radius=10)
        self.inv_display.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def add_stock(self):
        name = self.inv_name.get().strip().title() 
        try:
            price = float(self.inv_price.get().replace(',', ''))
            qty = int(self.inv_qty.get())
            if price < 0 or qty < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for Price and Quantity.")
            return

        if not name:
            messagebox.showerror("Error", "Item name cannot be empty.")
            return

        # If we are currently editing an item
        if self.editing_item:
            # If the user changed the name, make sure the new name doesn't already exist
            if name != self.editing_item and name in self.inventory:
                messagebox.showerror("Error", f"An item named '{name}' already exists.")
                return
            
            # Delete the old entry and create the new one with updated data
            del self.inventory[self.editing_item]
            self.inventory[name] = {'price': price, 'stock': qty}
            self.editing_item = None
            self.lbl_form_title.configure(text="Add New Stock")
            self.btn_save.configure(text="➕ Add / Update Stock")
            self.btn_cancel.pack_forget() # Hide cancel button
        else:
            # Normal adding logic
            if name in self.inventory:
                self.inventory[name]['price'] = price
                self.inventory[name]['stock'] += qty
            else:
                self.inventory[name] = {'price': price, 'stock': qty}

        self.save_inventory()
        self.clear_inv_inputs()
        self.refresh_inventory_display()
        self.refresh_sales_dropdown()
        self.refresh_reports()

    def start_edit(self, item_name):
        self.editing_item = item_name
        data = self.inventory[item_name]
        
        # Fill the input boxes with the item's current data
        self.inv_name.delete(0, 'end')
        self.inv_name.insert(0, item_name)
        
        self.inv_price.delete(0, 'end')
        self.inv_price.insert(0, str(data['price']))
        
        self.inv_qty.delete(0, 'end')
        self.inv_qty.insert(0, str(data['stock']))

        # Change UI to "Edit Mode"
        self.lbl_form_title.configure(text=f"Editing: {item_name}")
        self.btn_save.configure(text="💾 Save Changes")
        self.btn_cancel.pack(side="left", fill="x", expand=True, padx=(5, 0))

    def cancel_edit(self):
        self.editing_item = None
        self.clear_inv_inputs()
        self.lbl_form_title.configure(text="Add New Stock")
        self.btn_save.configure(text="➕ Add / Update Stock")
        self.btn_cancel.pack_forget()

    def clear_inv_inputs(self):
        self.inv_name.delete(0, 'end')
        self.inv_price.delete(0, 'end')
        self.inv_qty.delete(0, 'end')

    def delete_item(self, item_name):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to completely remove '{item_name}'?"):
            del self.inventory[item_name]
            self.save_inventory()
            
            # If we were editing this item, cancel the edit
            if self.editing_item == item_name:
                self.cancel_edit()
                
            self.refresh_inventory_display()
            self.refresh_sales_dropdown()
            self.refresh_reports()

    def refresh_inventory_display(self):
        for widget in self.inv_display.winfo_children():
            widget.destroy()

        if not self.inventory:
            ctk.CTkLabel(self.inv_display, text="Inventory is empty.").pack(pady=20)
            return

        for name, data in self.inventory.items():
            row = ctk.CTkFrame(self.inv_display)
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=name, width=200, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"₦{data['price']:,.2f}", width=120, anchor="w").pack(side="left", padx=10)
            
            stock_color = "#D32F2F" if data['stock'] < 10 else "#1A237E"
            ctk.CTkLabel(row, text=f"Stock: {data['stock']}", width=100, anchor="w", text_color=stock_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

            # EDIT BUTTON
            ctk.CTkButton(row, text="✏️ Edit", width=70, fg_color="#F57C00", hover_color="#E65100", 
                          command=lambda n=name: self.start_edit(n)).pack(side="right", padx=5)

            # DELETE BUTTON
            ctk.CTkButton(row, text="🗑️ Delete", width=70, fg_color="#D32F2F", hover_color="#B71C1C", 
                          command=lambda n=name: self.delete_item(n)).pack(side="right", padx=5)

    # (The rest of the code for Sales, Records, and Reports remains exactly the same)
    # ==========================================
    # 2. SALES TERMINAL TAB
    # ==========================================
    def setup_sales_tab(self):
        self.tab_sales.grid_columnconfigure(0, weight=1)
        self.tab_sales.grid_columnconfigure(1, weight=1)
        self.tab_sales.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self.tab_sales)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_frame, text="Select Item to Sell", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)
        
        self.sales_dropdown = ctk.CTkOptionMenu(left_frame, values=["No stock available"], width=300, command=self.update_selected_item_info)
        self.sales_dropdown.grid(row=1, column=0, pady=5)

        self.lbl_item_info = ctk.CTkLabel(left_frame, text="Price: ₦0.00 | Available: 0", text_color="#555555")
        self.lbl_item_info.grid(row=2, column=0, pady=5)

        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.grid(row=3, column=0, pady=10)
        
        ctk.CTkLabel(control_frame, text="Qty:").pack(side="left", padx=5)
        self.sales_qty = ctk.CTkEntry(control_frame, width=60)
        self.sales_qty.insert(0, "1")
        self.sales_qty.pack(side="left", padx=5)

        btn_add = ctk.CTkButton(control_frame, text="🛒 Add to Cart", fg_color="#2E7D32", hover_color="#1B5E20", command=self.add_to_cart)
        btn_add.pack(side="left", padx=20)

        self.cart_display = ctk.CTkScrollableFrame(left_frame, label_text="Current Cart")
        self.cart_display.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_rowconfigure(4, weight=1)

        right_frame = ctk.CTkFrame(self.tab_sales)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)

        ctk.CTkLabel(right_frame, text="Customer Details", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        self.cust_name = ctk.CTkEntry(right_frame, placeholder_text="Customer Name (Optional)", width=250)
        self.cust_name.pack(pady=5)
        self.cust_phone = ctk.CTkEntry(right_frame, placeholder_text="Phone Number", width=250)
        self.cust_phone.pack(pady=5)

        self.lbl_total = ctk.CTkLabel(right_frame, text="Total: ₦0.00", font=ctk.CTkFont(size=28, weight="bold"), text_color="#D32F2F")
        self.lbl_total.pack(pady=30)

        pay_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        pay_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(pay_frame, text="Cash Received (₦):", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.cash_received = ctk.CTkEntry(pay_frame, width=120)
        self.cash_received.pack(side="right")
        self.cash_received.bind("<KeyRelease>", self.calculate_change)

        self.lbl_change = ctk.CTkLabel(right_frame, text="Change: ₦0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2E7D32")
        self.lbl_change.pack(pady=(0, 20))

        btn_checkout = ctk.CTkButton(right_frame, text="🖨️ Complete Sale & Print", height=50, fg_color="#F57C00", hover_color="#E65100", font=ctk.CTkFont(size=16, weight="bold"), command=self.checkout)
        btn_checkout.pack(side="bottom", fill="x", padx=20, pady=20)

    def update_selected_item_info(self, selected_item):
        if selected_item in self.inventory:
            price = self.inventory[selected_item]['price']
            stock = self.inventory[selected_item]['stock']
            self.lbl_item_info.configure(text=f"Price: ₦{price:,.2f} | Available: {stock}")

    def add_to_cart(self):
        item = self.sales_dropdown.get()
        if item == "No stock available" or item not in self.inventory:
            return

        try:
            qty = int(self.sales_qty.get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive whole number.")
            return

        available_stock = self.inventory[item]['stock']
        if qty > available_stock:
            messagebox.showerror("Out of Stock", f"Only {available_stock} left in stock!")
            return

        price = self.inventory[item]['price']

        if item in self.cart:
            if self.cart[item]['qty'] + qty > available_stock:
                messagebox.showerror("Out of Stock", f"Only {available_stock} left. You already have {self.cart[item]['qty']} in cart.")
                return
            self.cart[item]['qty'] += qty
        else:
            self.cart[item] = {'price': price, 'qty': qty}

        self.sales_qty.delete(0, 'end')
        self.sales_qty.insert(0, "1")
        self.refresh_cart_display()

    def refresh_cart_display(self):
        for widget in self.cart_display.winfo_children():
            widget.destroy()

        self.current_bill_total = 0.0
        for name, data in self.cart.items():
            row = ctk.CTkFrame(self.cart_display, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            subtotal = data['price'] * data['qty']
            self.current_bill_total += subtotal
            
            ctk.CTkLabel(row, text=f"{name} (x{data['qty']})", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=f"₦{subtotal:,.2f}", width=100, anchor="e").pack(side="left", padx=20)
            
            ctk.CTkButton(row, text="✕", width=30, fg_color="transparent", text_color="#D32F2F", hover_color="#FFCDD2", 
                          command=lambda n=name: self.remove_from_cart(n)).pack(side="right")

        self.lbl_total.configure(text=f"Total: ₦{self.current_bill_total:,.2f}")
        self.calculate_change()

    def remove_from_cart(self, item):
        del self.cart[item]
        self.refresh_cart_display()

    def calculate_change(self, event=None):
        try:
            cash = float(self.cash_received.get().replace(',', ''))
            change = cash - self.current_bill_total
            if change < 0:
                self.lbl_change.configure(text=f"Balance Due: ₦{abs(change):,.2f}", text_color="#D32F2F")
            else:
                self.lbl_change.configure(text=f"Change: ₦{change:,.2f}", text_color="#2E7D32")
        except ValueError:
            self.lbl_change.configure(text="Change: ₦0.00", text_color="#2E7D32")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty", "Cart is empty.")
            return

        cust = self.cust_name.get() or "Walk-in Customer"
        phone = self.cust_phone.get() or "N/A"
        receipt_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        receipt_text = "========================================\n"
        receipt_text += "           NAIJA PRO STORE              \n"
        receipt_text += "========================================\n"
        receipt_text += f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        receipt_text += f"Customer: {cust} | Phone: {phone}\n"
        receipt_text += "----------------------------------------\n"
        receipt_text += f"{'Item':<15} {'Qty':<5} {'Total':<10}\n"
        receipt_text += "----------------------------------------\n"

        items_str = ""
        for name, data in self.cart.items():
            self.inventory[name]['stock'] -= data['qty']
            subtotal = data['price'] * data['qty']
            items_str += f"{name} (x{data['qty']}), "
            receipt_text += f"{name[:15]:<15} {data['qty']:<5} ₦{subtotal:<9,.2f}\n"

        receipt_text += "----------------------------------------\n"
        receipt_text += f"TOTAL TO PAY:               ₦{self.current_bill_total:,.2f}\n"
        receipt_text += "========================================\n"
        receipt_text += "         Thank you for your patronage!  \n"

        self.save_inventory()
        
        with open("sales.csv", mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.datetime.now().strftime('%Y-%m-%d'), receipt_id, cust, f"{self.current_bill_total:.2f}", items_str.rstrip(", ")])

        filename = f"Receipt_{receipt_id}.txt"
        with open(filename, "w") as f:
            f.write(receipt_text)
        os.startfile(filename)

        messagebox.showinfo("Success", f"Sale Complete!\nStock has been updated.\nTotal: ₦{self.current_bill_total:,.2f}")
        
        self.cart = {}
        self.refresh_cart_display()
        self.cust_name.delete(0, 'end')
        self.cust_phone.delete(0, 'end')
        self.cash_received.delete(0, 'end')
        
        self.load_data()
        self.refresh_inventory_display()
        self.refresh_sales_dropdown()
        self.refresh_sales_record()
        self.refresh_reports()

    def refresh_sales_dropdown(self):
        available_items = [item for item, data in self.inventory.items() if data['stock'] > 0]
        
        if available_items:
            self.sales_dropdown.configure(values=available_items)
            if self.sales_dropdown.get() not in available_items:
                self.sales_dropdown.set(available_items[0])
            self.update_selected_item_info(self.sales_dropdown.get())
        else:
            self.sales_dropdown.configure(values=["No stock available"])
            self.sales_dropdown.set("No stock available")
            self.lbl_item_info.configure(text="Price: ₦0.00 | Available: 0")

    # ==========================================
    # 3. SALES RECORD TAB
    # ==========================================
    def setup_record_tab(self):
        self.tab_record.grid_rowconfigure(1, weight=1)
        self.tab_record.grid_columnconfigure(0, weight=1)

        filter_frame = ctk.CTkFrame(self.tab_record, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        ctk.CTkLabel(filter_frame, text="Filter by Date:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        self.date_filter_combo = ctk.CTkComboBox(filter_frame, values=["All Dates"], width=200, command=self.filter_sales_record)
        self.date_filter_combo.pack(side="left")
        self.date_filter_combo.set("All Dates")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=30, font=('Helvetica', 11))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))

        self.record_frame = ctk.CTkFrame(self.tab_record)
        self.record_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.record_frame.grid_rowconfigure(0, weight=1)
        self.record_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.record_frame, columns=("Date", "ID", "Customer", "Total", "Items"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("ID", text="Receipt ID")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Total", text="Total (₦)")
        self.tree.heading("Items", text="Items Bought")
        
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("ID", width=150, anchor="center")
        self.tree.column("Customer", width=150, anchor="w")
        self.tree.column("Total", width=100, anchor="e")
        self.tree.column("Items", width=400, anchor="w")
        
        self.tree.grid(row=0, column=0, sticky="nsew")

    def refresh_sales_record(self):
        if os.path.exists("sales.csv"):
            with open("sales.csv", mode='r') as f:
                reader = csv.reader(f)
                next(reader)
                dates = list(set(row[0] for row in reader if len(row) > 0))
                dates.sort(reverse=True)
                self.date_filter_combo.configure(values=["All Dates"] + dates)

        self.filter_sales_record()

    def filter_sales_record(self, selected_date=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists("sales.csv"):
            return

        filter_val = self.date_filter_combo.get()

        with open("sales.csv", mode='r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) == 5:
                    if filter_val == "All Dates" or row[0] == filter_val:
                        self.tree.insert("", "end", values=row)

    # ==========================================
    # 4. REPORTS & ANALYTICS TAB
    # ==========================================
    def setup_reports_tab(self):
        self.tab_reports.grid_rowconfigure(1, weight=1)
        self.tab_reports.grid_columnconfigure(0, weight=1)
        self.tab_reports.grid_columnconfigure(1, weight=1)
        self.tab_reports.grid_columnconfigure(2, weight=1)

        card_frame = ctk.CTkFrame(self.tab_reports, fg_color="transparent")
        card_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        card_frame.grid_columnconfigure((0,1,2), weight=1)

        self.card_revenue = ctk.CTkFrame(card_frame, corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.card_revenue.grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(self.card_revenue, text="Total Revenue", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0))
        self.lbl_rep_revenue = ctk.CTkLabel(self.card_revenue, text="₦0.00", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2E7D32")
        self.lbl_rep_revenue.pack(pady=10)

        self.card_txns = ctk.CTkFrame(card_frame, corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.card_txns.grid(row=0, column=1, padx=10, sticky="ew")
        ctk.CTkLabel(self.card_txns, text="Total Sales", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0))
        self.lbl_rep_txns = ctk.CTkLabel(self.card_txns, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#1A237E")
        self.lbl_rep_txns.pack(pady=10)

        self.card_top_item = ctk.CTkFrame(card_frame, corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.card_top_item.grid(row=0, column=2, padx=10, sticky="ew")
        ctk.CTkLabel(self.card_top_item, text="Top Selling Item", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0))
        self.lbl_rep_top = ctk.CTkLabel(self.card_top_item, text="N/A", font=ctk.CTkFont(size=20, weight="bold"), text_color="#F57C00")
        self.lbl_rep_top.pack(pady=10)

        self.alert_frame = ctk.CTkScrollableFrame(self.tab_reports, label_text="⚠️ Low Stock Alert (Below 10 items)")
        self.alert_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=20, pady=(0, 20))

    def refresh_reports(self):
        for widget in self.alert_frame.winfo_children():
            widget.destroy()
            
        low_stock = {k: v for k, v in self.inventory.items() if v['stock'] < 10}
        if not low_stock:
            ctk.CTkLabel(self.alert_frame, text="All items are well stocked!", text_color="#2E7D32").pack(pady=10)
        else:
            for item, data in low_stock.items():
                row = ctk.CTkFrame(self.alert_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=item, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
                ctk.CTkLabel(row, text=f"Stock: {data['stock']}", text_color="#D32F2F").pack(side="right", padx=10)

        if not os.path.exists("sales.csv"):
            return

        total_revenue = 0.0
        total_txns = 0
        items_sold = Counter()

        with open("sales.csv", mode='r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) == 5:
                    total_txns += 1
                    total_revenue += float(row[3])
                    
                    items_part = row[4]
                    if items_part:
                        for item_str in items_part.split(", "):
                            try:
                                name = item_str.split(" (x")[0]
                                qty = int(item_str.split(" (x")[1].replace(")", ""))
                                items_sold[name] += qty
                            except:
                                pass

        self.lbl_rep_revenue.configure(text=f"₦{total_revenue:,.2f}")
        self.lbl_rep_txns.configure(text=str(total_txns))

        if items_sold:
            top_item = items_sold.most_common(1)[0]
            self.lbl_rep_top.configure(text=f"{top_item[0]} ({top_item[1]})")
        else:
            self.lbl_rep_top.configure(text="N/A")

    # ==========================================
    # 5. FILE SAVING / LOADING
    # ==========================================
    def save_inventory(self):
        with open("inventory.csv", mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Item", "Price", "Stock"])
            for name, data in self.inventory.items():
                writer.writerow([name, data['price'], data['stock']])

    def load_data(self):
        if not os.path.exists("inventory.csv"):
            with open("inventory.csv", mode='w', newline='') as f:
                csv.writer(f).writerow(["Item", "Price", "Stock"])
                
        if not os.path.exists("sales.csv"):
            with open("sales.csv", mode='w', newline='') as f:
                csv.writer(f).writerow(["Date", "Receipt ID", "Customer", "Total", "Items"])

        self.inventory = {}
        with open("inventory.csv", mode='r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) == 3:
                    self.inventory[row[0]] = {'price': float(row[1]), 'stock': int(row[2])}

if __name__ == "__main__":
    app = ProInventoryApp()
    app.mainloop()