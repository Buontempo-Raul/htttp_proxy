import tkinter as tk
from tkinter import scrolledtext, messagebox
import time
import threading
import os
import subprocess

class InterceptedDataMonitor:
    def __init__(self, master):
        self.master = master
        self.master.title("Intercepted Data Monitor")
        
        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.clear_button = tk.Button(master, text="Clear", command=self.clear_text_area)
        self.clear_button.pack(pady=5)

        self.file_path = "intercepted_data.txt"
        self.running = True
        
        self.monitor_thread = threading.Thread(target=self.monitor_file)
        self.monitor_thread.start()

        self.start_http_proxy()

    def start_http_proxy(self):
        """Start the HTTP proxy in a separate process."""
        try:
            self.proxy_process = subprocess.Popen(["./http_proxy"]) 
            self.text_area.insert(tk.END, "HTTP Proxy started successfully.\n")
        except Exception as e:
            self.text_area.insert(tk.END, f"Failed to start HTTP Proxy: {str(e)}\n")

    def monitor_file(self):
        """Monitor the file for new data."""
        if not os.path.exists(self.file_path):
            self.text_area.insert(tk.END, f"Error: The file '{self.file_path}' does not exist.\n")
            return

        try:
            with open(self.file_path, "r") as file:
                file.seek(0, 2)  
                while self.running:
                    line = file.readline()
                    if line:

                        self.text_area.insert(tk.END, line)
                        self.text_area.yview(tk.END)  
                    else:
                        time.sleep(0.1)  
        except Exception as e:
            self.text_area.insert(tk.END, f"Error: {str(e)}\n")

    def clear_text_area(self):
        """Clear the text area."""
        self.text_area.delete(1.0, tk.END)

    def on_closing(self):
        """Stop the thread and close the application."""
        self.running = False
        self.proxy_process.terminate()  
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterceptedDataMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
