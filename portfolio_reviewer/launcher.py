"""
GUI Launcher for Portfolio Reviewer
Cross-platform launcher for Mac and Windows
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import signal


class PortfolioReviewerLauncher:
    """GUI launcher for Portfolio Reviewer background service and teacher UI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Portfolio Reviewer Launcher")
        self.root.geometry("700x600")
        
        # Track running processes
        self.background_process = None
        self.ui_process = None
        
        self.setup_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup the GUI"""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="📝 Portfolio Reviewer Control Panel",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.bg_status_label = ttk.Label(
            status_frame,
            text="Background Service: ⚫ Stopped",
            font=("Arial", 10)
        )
        self.bg_status_label.pack(anchor=tk.W, pady=2)
        
        self.ui_status_label = ttk.Label(
            status_frame,
            text="Teacher UI: ⚫ Stopped",
            font=("Arial", 10)
        )
        self.ui_status_label.pack(anchor=tk.W, pady=2)
        
        # Control buttons frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Background service controls
        bg_frame = ttk.LabelFrame(control_frame, text="Background Service", padding="10")
        bg_frame.pack(fill=tk.X, pady=5)
        
        self.start_bg_button = ttk.Button(
            bg_frame,
            text="▶ Start Background Service",
            command=self.start_background_service,
            width=25
        )
        self.start_bg_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_bg_button = ttk.Button(
            bg_frame,
            text="⏹ Stop Background Service",
            command=self.stop_background_service,
            state=tk.DISABLED,
            width=25
        )
        self.stop_bg_button.pack(side=tk.LEFT, padx=5)
        
        # Teacher UI controls
        ui_frame = ttk.LabelFrame(control_frame, text="Teacher Dashboard", padding="10")
        ui_frame.pack(fill=tk.X, pady=5)
        
        self.start_ui_button = ttk.Button(
            ui_frame,
            text="▶ Open Teacher Dashboard",
            command=self.start_teacher_ui,
            width=25
        )
        self.start_ui_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_ui_button = ttk.Button(
            ui_frame,
            text="⏹ Close Teacher Dashboard",
            command=self.stop_teacher_ui,
            state=tk.DISABLED,
            width=25
        )
        self.stop_ui_button.pack(side=tk.LEFT, padx=5)
        
        # Log output
        log_frame = ttk.LabelFrame(self.root, text="Service Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        info_label = ttk.Label(
            self.root,
            text="The background service runs every 60 seconds to process new submissions.\nKeep this window open while the service is running.",
            font=("Arial", 9),
            foreground="gray"
        )
        info_label.pack(pady=5)
        
        # Initial log message
        self.log("Portfolio Reviewer Launcher started")
        self.log("Click 'Start Background Service' to begin processing submissions")
    
    def log(self, message):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def start_background_service(self):
        """Start the background processing service"""
        try:
            self.log("Starting background service...")
            
            # Get Python executable
            python_exe = sys.executable
            
            # Start background service
            self.background_process = subprocess.Popen(
                [python_exe, "background_service.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Update UI
            self.bg_status_label.config(text="Background Service: 🟢 Running")
            self.start_bg_button.config(state=tk.DISABLED)
            self.stop_bg_button.config(state=tk.NORMAL)
            
            self.log("✅ Background service started successfully")
            
            # Start thread to capture output
            threading.Thread(
                target=self.read_process_output,
                args=(self.background_process,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log(f"❌ Error starting background service: {e}")
            messagebox.showerror("Error", f"Failed to start background service:\n{e}")
    
    def stop_background_service(self):
        """Stop the background service"""
        if self.background_process:
            self.log("Stopping background service...")
            
            try:
                # Send SIGTERM on Unix, close on Windows
                if sys.platform == 'win32':
                    self.background_process.terminate()
                else:
                    self.background_process.send_signal(signal.SIGINT)
                
                self.background_process.wait(timeout=5)
            except:
                self.background_process.kill()
            
            self.background_process = None
            
            # Update UI
            self.bg_status_label.config(text="Background Service: ⚫ Stopped")
            self.start_bg_button.config(state=tk.NORMAL)
            self.stop_bg_button.config(state=tk.DISABLED)
            
            self.log("✅ Background service stopped")
    
    def start_teacher_ui(self):
        """Start the Streamlit teacher UI"""
        try:
            self.log("Opening teacher dashboard...")
            
            # Start Streamlit
            self.ui_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "teacher_ui.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Update UI
            self.ui_status_label.config(text="Teacher UI: 🟢 Running")
            self.start_ui_button.config(state=tk.DISABLED)
            self.stop_ui_button.config(state=tk.NORMAL)
            
            self.log("✅ Teacher dashboard opened in browser")
            self.log("   (If browser doesn't open, go to http://localhost:8501)")
            
            # Start thread to capture output
            threading.Thread(
                target=self.read_process_output,
                args=(self.ui_process,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log(f"❌ Error starting teacher UI: {e}")
            messagebox.showerror("Error", f"Failed to start teacher UI:\n{e}")
    
    def stop_teacher_ui(self):
        """Stop the teacher UI"""
        if self.ui_process:
            self.log("Closing teacher dashboard...")
            
            try:
                if sys.platform == 'win32':
                    self.ui_process.terminate()
                else:
                    self.ui_process.send_signal(signal.SIGINT)
                
                self.ui_process.wait(timeout=5)
            except:
                self.ui_process.kill()
            
            self.ui_process = None
            
            # Update UI
            self.ui_status_label.config(text="Teacher UI: ⚫ Stopped")
            self.start_ui_button.config(state=tk.NORMAL)
            self.stop_ui_button.config(state=tk.DISABLED)
            
            self.log("✅ Teacher dashboard closed")
    
    def read_process_output(self, process):
        """Read and log process output"""
        try:
            for line in process.stdout:
                if line.strip():
                    self.log(line.strip())
        except:
            pass
    
    def on_closing(self):
        """Handle window close event"""
        if self.background_process or self.ui_process:
            if messagebox.askokcancel(
                "Quit",
                "Services are still running. Stop them and quit?"
            ):
                self.stop_background_service()
                self.stop_teacher_ui()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Create and run launcher
    launcher = PortfolioReviewerLauncher()
    launcher.run()


if __name__ == '__main__':
    main()
