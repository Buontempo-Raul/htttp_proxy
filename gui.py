import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import datetime
import queue
import os
import json
from tkinter import simpledialog, messagebox


class ProxyServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HTTP Proxy Server")
        self.root.geometry("1800x900")  # Increased size to accommodate new feature

        # Blocked domains management
        self.blocked_domains_file = "blocked_domains.json"
        self.blocked_domains = self.load_blocked_domains()

        # Queue to manage waiting requests
        self.waiting_requests_queue = queue.Queue()
        self.waiting_requests = []
        self.current_request_id = 0

        self.server_socket = None
        self.client_socket = None
        self.intercept_enabled = True
        self.current_message_type = None
        self.history = []

        self.create_main_layout()
        self.create_control_panel()
        self.create_request_panel()
        self.create_response_panel()
        self.create_waiting_requests_panel()
        self.create_blocked_domains_panel()  # New panel for blocked domains
        self.create_history_tab()

        self.start_gui_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def save_and_forward_request(self):
        if self.current_selected_request:
            try:
                # Collect modified headers and body
                headers = self.request_headers.get("1.0", tk.END).strip()
                body = self.request_body.get("1.0", tk.END).strip()
                
                # Reconstruct the HTTP request
                modified_request = f"{headers}\r\n\r\n{body}"
                
                try:
                    # Get the client socket
                    client_socket = self.current_selected_request['client_socket']
                    request_id = self.current_selected_request['id']
                    
                    # Send edit signal
                    client_socket.sendall("EDIT\n\n".encode())
                    
                    # Send message length as a fixed-length string (padded with spaces)
                    message_length = str(len(modified_request)).ljust(10)
                    print(message_length)
                    client_socket.sendall(message_length.encode())

                    # Wait for acknowledgment with timeout
                    client_socket.settimeout(5.0)  # 5 second timeout
                    response = client_socket.recv(1024).decode().strip()
                    if response != "READY":
                        self.remove_request_from_waiting_list(request_id)
                        messagebox.showerror("Error", "Server did not acknowledge message length")
                        client_socket.close()
                        return

                    print(modified_request)
                    # Send modified request
                    client_socket.sendall(modified_request.encode())
                    
                    # Wait for confirmation
                    response = client_socket.recv(1024).decode().strip()
                    if response != "OK":
                        self.remove_request_from_waiting_list(request_id)
                        messagebox.showerror("Error", "Failed to send modified request")
                        client_socket.close()
                        return
                    
                    # Remove from waiting requests
                    self.remove_request_from_waiting_list(request_id)
                    
                    messagebox.showinfo("Success", "Request modified and forwarded successfully")
                    
                except socket.timeout:
                    self.remove_request_from_waiting_list(request_id)
                    messagebox.showerror("Error", "Connection timed out")
                except ConnectionResetError:
                    self.remove_request_from_waiting_list(request_id)
                    messagebox.showerror("Error", "Connection was reset by the server")
                except Exception as e:
                    self.remove_request_from_waiting_list(request_id)
                    messagebox.showerror("Error", f"Failed to forward modified request: {str(e)}")
                finally:
                    try:
                        client_socket.close()
                    except:
                        pass
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to prepare modified request: {str(e)}")

    def remove_request_from_waiting_list(self, request_id):
        """Remove a request from the waiting list and update the GUI"""
        # Remove from waiting requests list
        self.waiting_requests = [
            req for req in self.waiting_requests 
            if req['id'] != request_id
        ]
        
        # Update GUI
        self.root.after(0, self.update_waiting_requests_list)
        self.root.after(0, self.clear_request_display)

    def load_blocked_domains(self):
        """Load blocked domains from a JSON file"""
        try:
            if os.path.exists(self.blocked_domains_file):
                with open(self.blocked_domains_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading blocked domains: {e}")
            return []

    def save_blocked_domains(self):
        """Save blocked domains to a JSON file"""
        try:
            with open(self.blocked_domains_file, 'w') as f:
                json.dump(self.blocked_domains, f, indent=2)
            
            # Send updated blocked domains to the proxy server
            self.send_blocked_domains_to_proxy()
        except Exception as e:
            print(f"Error saving blocked domains: {e}")

    def send_blocked_domains_to_proxy(self):
        """Send updated blocked domains list to the proxy server"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 9092))  # New port for blocked domains update
                domains_json = json.dumps(self.blocked_domains)
                s.sendall(domains_json.encode())
        except Exception as e:
            print(f"Failed to send blocked domains: {e}")

    def create_blocked_domains_panel(self):
        """Create panel for managing blocked domains"""
        blocked_domains_tab = ttk.Frame(self.notebook)
        self.notebook.add(blocked_domains_tab, text='Blocked Domains')

        # Treeview to display blocked domains
        self.blocked_domains_list = ttk.Treeview(blocked_domains_tab, columns=("Domain",), show="headings")
        self.blocked_domains_list.heading("Domain", text="Blocked Domains")
        self.blocked_domains_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Update the list with current blocked domains
        self.update_blocked_domains_list()

        # Frame for buttons
        button_frame = ttk.Frame(blocked_domains_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add Domain button
        add_button = ttk.Button(button_frame, text="Add Domain", command=self.add_blocked_domain)
        add_button.pack(side=tk.LEFT, padx=5)

        # Remove Domain button
        remove_button = ttk.Button(button_frame, text="Remove Domain", command=self.remove_blocked_domain)
        remove_button.pack(side=tk.LEFT, padx=5)

    def update_blocked_domains_list(self):
        """Update the treeview with current blocked domains"""
        # Clear existing items
        for i in self.blocked_domains_list.get_children():
            self.blocked_domains_list.delete(i)
        
        # Add current blocked domains
        for domain in self.blocked_domains:
            self.blocked_domains_list.insert("", "end", values=(domain,))

    def add_blocked_domain(self):
        """Prompt user to add a new blocked domain"""
        domain = simpledialog.askstring("Add Blocked Domain", "Enter domain to block:")
        if domain:
            # Validate domain (basic check)
            domain = domain.strip().lower()
            if domain and domain not in self.blocked_domains:
                self.blocked_domains.append(domain)
                self.update_blocked_domains_list()
                self.save_blocked_domains()
                messagebox.showinfo("Success", f"Domain {domain} added to blocked list")
            elif domain in self.blocked_domains:
                messagebox.showwarning("Warning", f"Domain {domain} is already blocked")

    def remove_blocked_domain(self):
        """Remove selected blocked domain"""
        selected_item = self.blocked_domains_list.selection()
        if selected_item:
            domain = self.blocked_domains_list.item(selected_item, "values")[0]
            self.blocked_domains.remove(domain)
            self.update_blocked_domains_list()
            self.save_blocked_domains()
            messagebox.showinfo("Success", f"Domain {domain} removed from blocked list")
        else:
            messagebox.showwarning("Warning", "Please select a domain to remove")

    def start_gui_listener(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', 9090))
        self.server_socket.listen(5)  # Increased to allow multiple connections
        threading.Thread(target=self.listen_for_requests, daemon=True).start()

    def listen_for_requests(self):
        while True:
            self.client_socket, _ = self.server_socket.accept()
            data = self.client_socket.recv(20000).decode(errors="replace")

            # Increment request ID
            self.current_request_id += 1
            
            # Split message
            parts = data.split("\n\n", 1)
            self.current_message_type = parts[0] if len(parts) > 0 else ""
            content = parts[1] if len(parts) > 1 else ""

            if self.current_message_type == "REQUEST":
                # Add to waiting requests
                waiting_request = {
                    "id": self.current_request_id,
                    "content": content,
                    "client_socket": self.client_socket
                }
                self.waiting_requests.append(waiting_request)
                self.waiting_requests_queue.put(waiting_request)
                
                # Update waiting requests list in main thread
                self.root.after(0, self.update_waiting_requests_list)
            
            elif self.current_message_type == "RESPONSE":
                self.root.after(0, self.display_response, content)
                self.add_to_history("RESPONSE", content)

    def update_waiting_requests_list(self):
        # Clear existing items
        for i in self.waiting_requests_list.get_children():
            self.waiting_requests_list.delete(i)
        
        # Populate with waiting requests
        for req in self.waiting_requests:
            self.waiting_requests_list.insert("", "end", 
                                              iid=str(req['id']), 
                                              values=(req['id'], 
                                                      self.extract_method_and_url(req['content'])))

    def extract_method_and_url(self, request_data):
        # Extract method and URL from request
        lines = request_data.split('\n')
        if lines:
            first_line = lines[0].strip()
            parts = first_line.split(' ')
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}"
        return "Unknown Request"

    def handle_waiting_request_selection(self, event):
        # Get selected request
        selected_item = self.waiting_requests_list.selection()
        if not selected_item:
            return
        
        request_id = int(selected_item[0])
        
        # Find the corresponding request
        selected_request = next((req for req in self.waiting_requests if req['id'] == request_id), None)
        
        if selected_request:
            # Display request in request panels
            request_data = selected_request['content']
            self.display_request(request_data, selected_request)

    @staticmethod
    def sanitize_text(text):
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        return text

    def split_headers_body(self, data):
        if "\r\n\r\n" in data:
            headers, body = data.split("\r\n\r\n", 1)
        elif "\n\n" in data:
            headers, body = data.split("\n\n", 1)
        else:
            headers, body = data, ""
        return self.sanitize_text(headers), self.sanitize_text(body)

    def display_request(self, request_data, selected_request=None):
        request_data = self.sanitize_text(request_data)
        if not request_data.strip():
            return  

        headers, body = self.split_headers_body(request_data)
        self.request_headers.delete("1.0", tk.END)
        self.request_headers.insert("1.0", headers)
        self.request_body.delete("1.0", tk.END)
        self.request_body.insert("1.0", body)

        # Store the current selected request for forwarding/dropping
        self.current_selected_request = selected_request

        self.request_buttons_frame.pack(fill=tk.X, pady=5)
        self.response_buttons_frame.pack_forget()

    def display_response(self, response_data):
        response_data = self.sanitize_text(response_data)
        if not response_data.strip():
            return 

        headers, body = self.split_headers_body(response_data)
        self.response_headers.delete("1.0", tk.END)
        self.response_headers.insert("1.0", headers)
        self.response_body.delete("1.0", tk.END)
        self.response_body.insert("1.0", body)

        self.response_buttons_frame.pack(fill=tk.X, pady=5)
        self.request_buttons_frame.pack_forget()

    def forward_request(self):
        if self.current_selected_request:
            client_socket = self.current_selected_request['client_socket']
            client_socket.sendall("FORWARD".encode())
            client_socket.close()
            
            # Remove from waiting requests
            self.waiting_requests = [req for req in self.waiting_requests 
                                     if req['id'] != self.current_selected_request['id']]
            
            # Update waiting requests list
            self.update_waiting_requests_list()
            
            # Clear request display
            self.clear_request_display()

    def drop_request(self):
        if self.current_selected_request:
            client_socket = self.current_selected_request['client_socket']
            client_socket.sendall("DROP".encode())
            client_socket.close()
            
            # Remove from waiting requests
            self.waiting_requests = [req for req in self.waiting_requests 
                                     if req['id'] != self.current_selected_request['id']]
            
            # Update waiting requests list
            self.update_waiting_requests_list()
            
            # Clear request display
            self.clear_request_display()

    def forward_response(self):
        if self.client_socket and self.current_message_type == "RESPONSE":
            self.client_socket.sendall("FORWARD_RESPONSE".encode())
            self.client_socket.close()
        self.clear_response_display()

    def drop_response(self):
        if self.client_socket and self.current_message_type == "RESPONSE":
            self.client_socket.sendall("DROP_RESPONSE".encode())
            self.client_socket.close()
        self.clear_response_display()

    def clear_request_display(self):
        self.request_headers.delete("1.0", tk.END)
        self.request_body.delete("1.0", tk.END)

    def clear_response_display(self):
        self.response_headers.delete("1.0", tk.END)
        self.response_body.delete("1.0", tk.END)

    def add_to_history(self, message_type, data):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        headers, body = self.split_headers_body(data)
        
        # Parse the first line to get method and URL
        lines = headers.splitlines()
        if not lines:
            return  # No headers to process
        
        first_line = lines[0].strip()
        parts = first_line.split(' ')
        
        # More flexible parsing of method, URL, and protocol
        method = parts[0] if parts and len(parts) > 0 else "UNKNOWN"
        url = parts[1] if parts and len(parts) > 1 else "UNKNOWN"
        protocol = parts[2] if parts and len(parts) > 2 else "HTTP"

        # Find host from headers if possible
        host = "UNKNOWN"
        for line in lines:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break

        # Check for duplicate response entries
        if message_type == "RESPONSE":
            for entry in self.history:
                if entry["url"] == url and "response_body" not in entry:
                    entry["response_body"] = body
                    entry["response_headers"] = headers
                    return

        # Create new history entry
        entry = {
            "timestamp": timestamp,
            "type": message_type,
            "method": method,
            "url": url,
            "protocol": protocol,
            "headers": headers,
            "body": body,
        }
        self.history.append(entry)
        
        # Update the treeview in the history list
        self.history_list.insert("", "end", values=(method, url, timestamp, protocol))


    def show_history_details(self, event):
        selected_item = self.history_list.selection()
        if selected_item:
            item = selected_item[0]
            values = self.history_list.item(item, "values") 
            method, url, timestamp, protocol = values

          
            for entry in self.history:
                if entry["timestamp"] == timestamp and entry["url"] == url:
                    self.open_details_window(entry)
                    break

    def open_details_window(self, entry):
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Details - {entry['method']} {entry['url']}")
        details_window.geometry("800x600")

        content_frame = ttk.Frame(details_window)
        content_frame.pack(fill=tk.BOTH, expand=True)

        request_text = scrolledtext.ScrolledText(content_frame, height=10, wrap=tk.WORD)
        request_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        request_text.insert("1.0", f"Request:\n{entry['headers']}\n\n{entry['body']}")

        if "response_headers" in entry:
            response_text = scrolledtext.ScrolledText(content_frame, height=10, wrap=tk.WORD)
            response_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            response_text.insert("1.0", f"Response:\n{entry['response_headers']}\n\n{entry['response_body']}")


       
        def show_request():
            content_text.delete("1.0", tk.END)
            content_text.insert("1.0", f"{entry['headers']}\n\n{entry['body']}")

        def show_response():
          
            response_data = entry.get("response_body", "")
            response_headers = entry.get("response_headers", "")
            content_text.delete("1.0", tk.END)
            content_text.insert("1.0", f"{response_headers}\n\n{response_data}")

       
        request_btn = ttk.Button(button_frame, text="Show Request", command=show_request)
        request_btn.pack(side=tk.LEFT, padx=5)

        response_btn = ttk.Button(button_frame, text="Show Response", command=show_response)
        response_btn.pack(side=tk.LEFT, padx=5)

      
        show_request()


    def send_intercept_command(self, command):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 9091))
                s.sendall(command.encode())
        except Exception as e:
            print(f"Failed to send intercept command: {e}")

    def toggle_intercept(self):
        self.intercept_enabled = not self.intercept_enabled
        if self.intercept_enabled:
            self.send_intercept_command("INTERCEPT_ON")
            self.intercept_btn.config(text="Intercept: ON")
        else:
            self.send_intercept_command("INTERCEPT_OFF")
            self.intercept_btn.config(text="Intercept: OFF")

    def create_main_layout(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.h_paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.h_paned.pack(fill=tk.BOTH, expand=True)

    def create_waiting_requests_panel(self):
        waiting_requests_frame = ttk.Frame(self.h_paned)
        self.h_paned.add(waiting_requests_frame, weight=1)
        
        waiting_requests_label = ttk.Label(waiting_requests_frame, text="Waiting Requests")
        waiting_requests_label.pack(fill=tk.X, pady=(5,0))
        
        self.waiting_requests_list = ttk.Treeview(waiting_requests_frame, 
                                                  columns=("ID", "Request"), 
                                                  show="headings")
        self.waiting_requests_list.heading("ID", text="Request ID")
        self.waiting_requests_list.heading("Request", text="Request Details")
        self.waiting_requests_list.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.waiting_requests_list.bind("<<TreeviewSelect>>", self.handle_waiting_request_selection)

    def create_control_panel(self):
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        self.intercept_btn = ttk.Button(control_frame, text="Intercept: ON", command=self.toggle_intercept)
        self.intercept_btn.pack(side=tk.LEFT, padx=5)

    def create_request_panel(self):
        request_frame = ttk.Frame(self.h_paned)
        self.h_paned.add(request_frame, weight=2)
        self.notebook = ttk.Notebook(request_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        request_tab = ttk.Frame(self.notebook)
        self.notebook.add(request_tab, text='Request')
        headers_frame = ttk.LabelFrame(request_tab, text="Headers", padding="5")
        headers_frame.pack(fill=tk.BOTH, expand=True)
        self.request_headers = scrolledtext.ScrolledText(headers_frame, height=10)
        self.request_headers.pack(fill=tk.BOTH, expand=True)
        body_frame = ttk.LabelFrame(request_tab, text="Body", padding="5")
        body_frame.pack(fill=tk.BOTH, expand=True)
        self.request_body = scrolledtext.ScrolledText(body_frame, height=10)
        self.request_body.pack(fill=tk.BOTH, expand=True)

        self.request_buttons_frame = ttk.Frame(request_tab)
        self.forward_request_btn = ttk.Button(self.request_buttons_frame, text="Forward Request", command=self.forward_request)
        self.forward_request_btn.pack(side=tk.LEFT, padx=5)
        self.drop_request_btn = ttk.Button(self.request_buttons_frame, text="Drop Request", command=self.drop_request)
        self.drop_request_btn.pack(side=tk.LEFT, padx=5)

        self.save_and_forward_btn = ttk.Button(self.request_buttons_frame, text="Save & Forward Request", command=self.save_and_forward_request)
        self.save_and_forward_btn.pack(side=tk.LEFT, padx=5)


    def create_response_panel(self):
        response_frame = ttk.Frame(self.h_paned)
        self.h_paned.add(response_frame, weight=1)
        response_tab = ttk.Frame(self.notebook)
        self.notebook.add(response_tab, text='Response')

        headers_frame = ttk.LabelFrame(response_tab, text="Headers", padding="5")
        headers_frame.pack(fill=tk.BOTH, expand=True)
        self.response_headers = scrolledtext.ScrolledText(headers_frame, height=10)
        self.response_headers.pack(fill=tk.BOTH, expand=True)

        body_frame = ttk.LabelFrame(response_tab, text="Body", padding="5")
        body_frame.pack(fill=tk.BOTH, expand=True)
        self.response_body = scrolledtext.ScrolledText(body_frame, height=10)
        self.response_body.pack(fill=tk.BOTH, expand=True)

        self.response_buttons_frame = ttk.Frame(response_tab)
        self.forward_response_btn = ttk.Button(self.response_buttons_frame, text="Forward Response", command=self.forward_response)
        self.forward_response_btn.pack(side=tk.LEFT, padx=5)
        self.drop_response_btn = ttk.Button(self.response_buttons_frame, text="Drop Response", command=self.drop_response)
        self.drop_response_btn.pack(side=tk.LEFT, padx=5)

    def create_history_tab(self):
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text='History')

        self.history_list = ttk.Treeview(history_tab, columns=("Method", "URL", "Time", "Protocol"), show="headings")
        self.history_list.heading("Method", text="Method")
        self.history_list.heading("URL", text="URL")
        self.history_list.heading("Time", text="Time")
        self.history_list.heading("Protocol", text="Protocol")
        self.history_list.pack(fill=tk.BOTH, expand=True)
        self.history_list.bind("<<TreeviewSelect>>", self.show_history_details)

    def on_closing(self):
        if self.server_socket:
            self.server_socket.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyServerGUI(root)
    root.mainloop()