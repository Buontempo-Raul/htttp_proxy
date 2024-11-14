import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading

class ProxyServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HTTP Proxy Server")
        self.root.geometry("1400x800")

        self.server_socket = None
        self.client_socket = None
        self.intercept_enabled = True
        self.current_message_type = None

        self.create_main_layout()
        self.create_control_panel()
        self.create_request_panel()
        self.create_response_panel()

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
            data = self.client_socket.recv(8192).decode()

            # Split into type and actual content
            parts = data.split("\n\n", 1)
            self.current_message_type = parts[0] if len(parts) > 0 else ""
            content = parts[1] if len(parts) > 1 else ""

            # Display based on type
            if self.current_message_type == "REQUEST":
                self.root.after(0, self.display_request, content)
            elif self.current_message_type == "RESPONSE":
                self.root.after(0, self.display_response, content)

    def display_request(self, request_data):
        headers, body = request_data.split("\n\n", 1) if "\n\n" in request_data else (request_data, "")
        self.request_headers.delete("1.0", tk.END)
        self.request_headers.insert("1.0", headers)
        self.request_body.delete("1.0", tk.END)
        self.request_body.insert("1.0", body)
        self.forward_request_btn.config(state=tk.NORMAL)
        self.drop_request_btn.config(state=tk.NORMAL)

    def display_response(self, response_data):
        headers, body = response_data.split("\n\n", 1) if "\n\n" in response_data else (response_data, "")
        self.response_headers.delete("1.0", tk.END)
        self.response_headers.insert("1.0", headers)
        self.response_body.delete("1.0", tk.END)
        self.response_body.insert("1.0", body)
        self.forward_response_btn.config(state=tk.NORMAL)
        self.drop_response_btn.config(state=tk.NORMAL)

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
        self.forward_request_btn.config(state=tk.DISABLED)
        self.drop_request_btn.config(state=tk.DISABLED)
        self.request_headers.delete("1.0", tk.END)
        self.request_body.delete("1.0", tk.END)

    def clear_response_display(self):
        self.forward_response_btn.config(state=tk.DISABLED)
        self.drop_response_btn.config(state=tk.DISABLED)
        self.response_headers.delete("1.0", tk.END)
        self.response_body.delete("1.0", tk.END)

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

        button_frame = ttk.Frame(request_frame)
        button_frame.pack(fill=tk.X, pady=5)
        self.forward_request_btn = ttk.Button(button_frame, text="Forward Request", command=self.forward_request, state=tk.DISABLED)
        self.forward_request_btn.pack(side=tk.RIGHT, padx=5)
        self.drop_request_btn = ttk.Button(button_frame, text="Drop Request", command=self.drop_request, state=tk.DISABLED)
        self.drop_request_btn.pack(side=tk.RIGHT, padx=5)

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

        button_frame = ttk.Frame(response_frame)
        button_frame.pack(fill=tk.X, pady=5)
        self.forward_response_btn = ttk.Button(button_frame, text="Forward Response", command=self.forward_response, state=tk.DISABLED)
        self.forward_response_btn.pack(side=tk.RIGHT, padx=5)
        self.drop_response_btn = ttk.Button(button_frame, text="Drop Response", command=self.drop_response, state=tk.DISABLED)
        self.drop_response_btn.pack(side=tk.RIGHT, padx=5)

    def on_closing(self):
        if self.server_socket:
            self.server_socket.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyServerGUI(root)
    root.mainloop()
