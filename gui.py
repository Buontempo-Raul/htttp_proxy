import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import datetime


class ProxyServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HTTP Proxy Server")
        self.root.geometry("1400x800")

        self.server_socket = None
        self.client_socket = None
        self.intercept_enabled = True
        self.current_message_type = None
        self.history = []

        self.create_main_layout()
        self.create_control_panel()
        self.create_request_panel()
        self.create_response_panel()
        self.create_history_tab()

        self.start_gui_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_gui_listener(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', 9090))
        self.server_socket.listen(1)
        threading.Thread(target=self.listen_for_requests, daemon=True).start()

    def listen_for_requests(self):
        while True:
            self.client_socket, _ = self.server_socket.accept()
            data = self.client_socket.recv(8192).decode(errors="replace")

           
            parts = data.split("\n\n", 1)
            self.current_message_type = parts[0] if len(parts) > 0 else ""
            content = parts[1] if len(parts) > 1 else ""

          
            if self.current_message_type == "REQUEST":
                self.root.after(0, self.display_request, content)
                self.add_to_history("REQUEST", content)
            elif self.current_message_type == "RESPONSE":
                self.root.after(0, self.display_response, content)
                self.add_to_history("RESPONSE", content)

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

    def display_request(self, request_data):
        request_data = self.sanitize_text(request_data)
        if not request_data.strip():
            return  

        headers, body = self.split_headers_body(request_data)
        self.request_headers.delete("1.0", tk.END)
        self.request_headers.insert("1.0", headers)
        self.request_body.delete("1.0", tk.END)
        self.request_body.insert("1.0", body)

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
        if self.client_socket and self.current_message_type == "REQUEST":
            self.client_socket.sendall("FORWARD".encode())
            self.client_socket.close()
        self.clear_request_display()

    def drop_request(self):
        if self.client_socket and self.current_message_type == "REQUEST":
            self.client_socket.sendall("DROP".encode())
            self.client_socket.close()
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
        url = None
        method = None
        protocol = "HTTP"

       
        for line in headers.splitlines():
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
            if line.upper().startswith(("GET", "POST", "PUT", "DELETE", "OPTIONS")):
                parts = line.split(" ")
                if len(parts) == 3:
                    method, url, protocol = parts

        if not method or not url:
            return  

       
        if message_type == "RESPONSE":
            for entry in self.history:
                if entry["url"] == url and "response_body" not in entry:
                    entry["response_body"] = body
                    entry["response_headers"] = headers
                    return

       
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
