import customtkinter as ctk
from tkinter import messagebox
import json
import os

# --- App Configuration ---
ctk.set_appearance_mode("System")  # Follows Windows Light/Dark mode
ctk.set_default_color_theme("blue") # Modern blue theme

class GroceryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pro Grocery Manager")
        self.geometry("500x600")
        self.minsize(400, 500)

        # Data Storage file
        self.data_file = "grocery_data.json"
        self.groceries = self.load_data()

        # --- UI Layout ---
        
        # 1. Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10), fill="x", padx=20)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🛒 Grocery List", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(side="left")

        # 2. Input Area
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        self.entry_item = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Enter grocery item...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.entry_item.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.entry_item.bind("<Return>", lambda event: self.add_item()) # Press Enter to add

        self.btn_add = ctk.CTkButton(
            self.input_frame, 
            text="Add Item", 
            width=100, 
            height=40,
            command=self.add_item
        )
        self.btn_add.pack(side="right", padx=(0, 10), pady=10)

        # 3. The List Area (Scrollable Frame)
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Items to Buy")
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # 4. Footer Action Buttons
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(pady=(0, 20), padx=20, fill="x")

        self.btn_clear = ctk.CTkButton(
            self.footer_frame, 
            text="Clear All", 
            fg_color="#D32F2F", # Red for danger
            hover_color="#B71C1C",
            width=120,
            height=35,
            command=self.clear_all
        )
        self.btn_clear.pack(side="left")

        # Load existing items into the UI
        self.refresh_list_ui()

    # --- Logic Functions ---

    def add_item(self):
        item_text = self.entry_item.get().strip()
        
        if not item_text:
            messagebox.showwarning("Empty", "Please enter an item.")
            return

        self.groceries.append({"name": item_text, "bought": False})
        self.entry_item.delete(0, "end")
        self.save_data()
        self.refresh_list_ui()

    def toggle_item(self, index, is_checked):
        self.groceries[index]["bought"] = is_checked
        self.save_data()

    def delete_item(self, index):
        del self.groceries[index]
        self.save_data()
        self.refresh_list_ui()

    def clear_all(self):
        if not self.groceries:
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the entire list?"):
            self.groceries = []
            self.save_data()
            self.refresh_list_ui()

    # --- UI Refresh ---

    def refresh_list_ui(self):
        # Clear current UI elements
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not self.groceries:
            empty_label = ctk.CTkLabel(self.list_frame, text="Your list is empty.", text_color="gray")
            empty_label.pack(pady=20)
            return

        # Rebuild the list
        for i, item in enumerate(self.groceries):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)

            # Checkbox (to mark as bought)
            # We use 'strikethrough' font if bought
            font_style = ctk.CTkFont(size=14, overstrike=item["bought"])
            text_color = "gray" if item["bought"] else ("black", "white")

            chk = ctk.CTkCheckBox(
                row, 
                text=item["name"], 
                font=font_style,
                text_color=text_color,
                command=lambda idx=i, c=item["bought"]: self.toggle_item(idx, not c)
            )
            
            # Set checkbox state without triggering command initially
            if item["bought"]:
                chk.select()
            chk.pack(side="left", padx=10)

            # Delete Button
            btn_del = ctk.CTkButton(
                row, 
                text="✕", 
                width=30, 
                height=30, 
                fg_color="transparent", 
                text_color="#D32F2F",
                hover_color=("#FFCDD2", "#4A0000"), # Light red / Dark red
                command=lambda idx=i: self.delete_item(idx)
            )
            btn_del.pack(side="right", padx=10)

    # --- Data Saving ---

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.groceries, f)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

if __name__ == "__main__":
    app = GroceryApp()
    app.mainloop()