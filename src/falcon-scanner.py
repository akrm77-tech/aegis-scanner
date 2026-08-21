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

warnings.filterwarnings("ignore")

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.colors import HexColor, black, darkred, orange
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ==========================================
# وحدة التشفير
# ==========================================
class CryptoEngine:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.generate_keys()

    def generate_keys(self):
        """توليد مفتاح RSA"""
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as sym_padding
        
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()

    def encrypt_data(self, data_text):
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as sym_padding
        
        aes_key = os.urandom(32)
        iv = os.urandom(16)
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data_text.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted_content = encryptor.update(padded_data) + encryptor.finalize()

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
        """فك تشفير البيانات"""
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as sym_padding
        
        try:
            aes_key = self.private_key.decrypt(
                bytes.fromhex(encrypted_data['enc_key']),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            iv = bytes.fromhex(encrypted_data['iv'])
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(bytes.fromhex(encrypted_data['content'])) + decryptor.finalize()
            
            unpadder = sym_padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            return decrypted.decode('utf-8')
        except Exception as e:
            return f"[خطأ في فك التشفير] {e}"


# ==========================================
# وحدة التعلم الآلي
# ==========================================
class MLEngine:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.model_path = 'falcon_rf_model.pkl'
        self.vec_path = 'falcon_vectorizer.pkl'

    def create_dummy_dataset(self):
        """توليد بيانات تدريب وهمية"""
        data = {
            'request': [
                "SELECT * FROM users", "UNION SELECT 1,2", "<script>alert(1)</script>", 
                "home.php?id=1", "DROP TABLE users", "admin' --", "1' OR '1'='1", 
                "Hello world", "Contact us page", "search=laptop", "order=desc"
            ] * 50,
            'label': [0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0] * 50
        }
        df = pd.DataFrame(data)
        df.to_csv('training_data.csv', index=False)
        return 'training_data.csv'

    def train_model(self, log_callback):
        """تدريب نموذج التعلم الآلي"""
        dataset = 'training_data.csv'
        if not os.path.exists(dataset):
            log_callback("[!] لا يوجد ملف تدريب. جاري توليد بيانات وهمية...")
            self.create_dummy_dataset()

        log_callback(f"[...] جاري تدريب نموذج Random Forest على {dataset}...")
        
        try:
            df = pd.read_csv(dataset)
            self.vectorizer = TfidfVectorizer(max_features=1000)
            X = self.vectorizer.fit_transform(df['request'].astype(str))
            y = df['label']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)

            preds = self.model.predict(X_test)
            report = classification_report(y_test, preds)
            acc = accuracy_score(y_test, preds)

            with open(self.model_path, 'wb') as f: pickle.dump(self.model, f)
            with open(self.vec_path, 'wb') as f: pickle.dump(self.vectorizer, f)

            return f"[+] تم التدريب بنجاح.\nالدقة: {acc:.4f}\n\nالتقرير:\n{report}"

        except Exception as e:
            return f"[-] خطأ في التدريب: {e}"

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f: self.model = pickle.load(f)
            with open(self.vec_path, 'rb') as f: self.vectorizer = pickle.load(f)
            return True
        except:
            return False

    def predict_anomaly(self, response_text):
        """استخدام النموذج لاكتشاف الشذوذ"""
        if not self.model or not self.vectorizer:
            return False, 0.0
        
        try:
            vec = self.vectorizer.transform([response_text[:5000]])
            prob = self.model.predict_proba(vec)[0][1] if hasattr(self.model, 'predict_proba') else 0.0
            is_threat = prob > 0.5 
            return is_threat, prob
        except:
            return False, 0.0


# ==========================================
# وحدة توليد الحمولات
# ==========================================
def generate_payloads(vuln_type):
    """توليد حمولات للثغرات"""
    if vuln_type == "SQLi":
        return [
            "' OR 1=1 --", "admin'--", "1' UNION SELECT NULL, version()--",
            "' OR '1'='1", "1'; DROP TABLE users--", "' UNION SELECT 1,2,3--"
        ]
    elif vuln_type == "XSS":
        return [
            "<script>alert('test')</script>", "<img src=x onerror=alert(1)>",
            "'\"><svg/onload=alert(1)>", "javascript:alert(1)"
        ]
    elif vuln_type == "LFI":
        return [
            "../../../etc/passwd", "../../../../windows/win.ini",
            "/etc/passwd", "C:\\boot.ini"
        ]
    elif vuln_type == "RCE":
        return [
            "; ls", "| dir", "&& whoami"
        ]
    return []


# ==========================================
# التطبيق الرئيسي
# ==========================================
class VulnerabilityScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Falcon Security Scanner v1.0")
        self.geometry("1200x900")
        
        self.crypto = CryptoEngine()
        self.ml_engine = MLEngine()
        
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
        
        self.vulnerabilities = []
        self.network_results = {}
        self.scanned_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Falcon-Scanner/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

        self.create_widgets()
        self.log("[+] تم تشغيل Falcon Security Scanner")
        
    def _configure_styles(self):
        self.style.configure('.', background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 10))
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('Dark.TFrame', background=self.frame_bg)
        self.style.configure('Title.TLabel', background=self.bg_color, font=('Segoe UI', 22, "bold"), foreground=self.accent_color)
        self.style.configure('TButton', background=self.button_bg, foreground="white", font=('Segoe UI', 10, 'bold'), borderwidth=0)
        self.style.map('TButton', background=[('active', self.accent_color)])

    def create_widgets(self):
        header = ttk.Frame(self, padding="15")
        header.pack(fill=tk.X)
        ttk.Label(header, text="Falcon Security Scanner v1.0", style='Title.TLabel').pack()
        ttk.Label(header, text="Vulnerability Detection Tool", 
                  background=self.bg_color, foreground=self.accent_color, font=('Segoe UI', 10)).pack()

        control_frame = ttk.Frame(self, style='Dark.TFrame', padding=15)
        control_frame.pack(fill=tk.X, padx=15, pady=5)
        
        ttk.Label(control_frame, text="Target URL:", background=self.frame_bg, font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, padx=5, sticky='w')
        self.url_entry = ttk.Entry(control_frame, width=60, font=('Segoe UI', 10))
        self.url_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.url_entry.insert(0, "http://testphp.vulnweb.com")

        self.btn_scan = ttk.Button(control_frame, text="Start Scan", command=self.start_scan_thread)
        self.btn_scan.grid(row=0, column=2, padx=5)

        self.btn_train = ttk.Button(control_frame, text="Train AI Model", command=self.start_training_thread)
        self.btn_train.grid(row=0, column=3, padx=5)

        self.btn_decrypt = ttk.Button(control_frame, text="Decrypt Report", command=self.decrypt_report)
        self.btn_decrypt.grid(row=0, column=4, padx=5)

        self.progress = ttk.Progressbar(control_frame, mode='determinate', length=200)
        self.progress.grid(row=0, column=5, padx=10)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        log_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.log_text = scrolledtext.ScrolledText(log_frame, bg=self.widget_bg, fg=self.fg_color, font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        notebook.add(log_frame, text="Live Logs")

        report_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.report_text = scrolledtext.ScrolledText(report_frame, bg=self.widget_bg, fg=self.fg_color, font=('Segoe UI', 11))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        notebook.add(report_frame, text="Scan Report")

        vuln_frame = ttk.Frame(notebook, style='Dark.TFrame')
        self.vuln_tree = ttk.Treeview(vuln_frame, columns=('Type', 'URL', 'Param', 'Confidence'), show='headings')
        self.vuln_tree.heading('Type', text='Type')
        self.vuln_tree.heading('URL', text='URL')
        self.vuln_tree.heading('Param', text='Parameter')
        self.vuln_tree.heading('Confidence', text='AI Confidence')
        self.vuln_tree.pack(fill=tk.BOTH, expand=True)
        notebook.add(vuln_frame, text="Vulnerabilities")

        footer = ttk.Frame(self, padding=10, style='Dark.TFrame')
        footer.pack(fill=tk.X, padx=15, pady=5)
        
        self.status_label = ttk.Label(footer, text="Ready", background=self.frame_bg, foreground=self.accent_color)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.btn_export = ttk.Button(footer, text="Export Encrypted PDF", command=self.export_report, state='disabled')
        self.btn_export.pack(side=tk.RIGHT, padx=5)

    def log(self, msg):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.status_label.config(text=msg[:50])

    def start_training_thread(self):
        t = Thread(target=self.run_training)
        t.daemon = True
        t.start()

    def run_training(self):
        self.btn_train.config(state='disabled')
        self.log("=== بدء تدريب النموذج ===")
        result = self.ml_engine.train_model(self.log)
        self.log(result)
        self.log("=== انتهى التدريب ===")
        self.btn_train.config(state='normal')

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
        self.log(f"=== بدء المسح: {url} ===")
        
        if not self.ml_engine.load_model():
            self.log("[!] لا يوجد نموذج مدرب. استخدم Train AI Model أولاً")
        else:
            self.log("[+] تم تحميل النموذج")

        if NMAP_AVAILABLE:
            try:
                hostname = urlparse(url).hostname
                target_ip = socket.gethostbyname(hostname)
                self.log(f"[*] فحص الشبكة: {target_ip}...")
                nm = nmap.PortScanner()
                nm.scan(target_ip, arguments='-p 1-1000 -T4')
                self.network_results = nm[target_ip]
                open_ports = list(self.network_results.get('tcp', {}).keys())
                self.log(f"[+] المنافذ المفتوحة: {open_ports}")
            except Exception as e:
                self.log(f"[-] فشل فحص الشبكة: {e}")
        else:
            self.log("[!] فحص الشبكة غير متاح")
        self.progress['value'] = 20

        try:
            self.log("[*] جاري الزحف...")
            res = self.session.get(url, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")
            forms = soup.find_all("form")
            links = soup.find_all("a", href=True)
            self.log(f"[+] تم العثور على {len(forms)} نموذج و {len(links)} رابط")
            self.progress['value'] = 40

            for i, form in enumerate(forms):
                action = form.get("action")
                target = urljoin(url, action)
                method = form.get("method", "get").lower()
                inputs = form.find_all("input")

                self.log(f"[*] اختبار: {target}")

                for vuln_type in ["SQLi", "XSS", "LFI", "RCE"]:
                    payloads = generate_payloads(vuln_type)
                    
                    for input_tag in inputs:
                        name = input_tag.get("name")
                        if not name: continue
                        
                        for payload in payloads[:3]:
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
                                
                                is_threat, conf = self.ml_engine.predict_anomaly(r.text[:5000])
                                
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
                                    self.log(f"[!] ثغرة: {vuln_type} (AI: {conf:.2f})")
                            except:
                                pass
                
                self.progress['value'] = 40 + ((i+1)/len(forms) * 50)

        except Exception as e:
            self.log(f"[-] خطأ في المسح: {e}")

        self.progress['value'] = 100
        self.generate_report()
        self.btn_scan.config(state='normal')
        self.btn_export.config(state='normal')
        self.log("=== انتهى المسح ===")

    def generate_report(self):
        self.report_text.delete('1.0', tk.END)
        report = "=== FALCON SECURITY SCAN REPORT ===\n"
        report += f"التاريخ: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if self.network_results:
            report += "--- نتائج الشبكة ---\n"
            open_ports = list(self.network_results.get('tcp', {}).keys())
            report += f"المنافذ المفتوحة: {open_ports}\n\n"
        
        report += "--- نتائج الويب ---\n"
        if not self.vulnerabilities:
            report += "لم يتم العثور على ثغرات.\n"
        else:
            report += f"عدد الثغرات: {len(self.vulnerabilities)}\n\n"
            for v in self.vulnerabilities:
                report += f"[!] {v['type']} في {v['url']}\n"
                report += f"    المعامل: {v['param']} | الثقة: {v['confidence']:.3f}\n"
                report += f"    الحمولة: {v['payload']}\n"
                report += "-"*50 + "\n"
        
        self.report_text.insert(tk.END, report)

    def decrypt_report(self):
        filename = filedialog.askopenfilename(
            title="اختر ملف التقرير المشفر",
            filetypes=[("Encrypted files", "*.aegis"), ("All files", "*.*")]
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                encrypted_data = eval(f.read())
            
            decrypted = self.crypto.decrypt_data(encrypted_data)
            
            decrypt_window = tk.Toplevel(self)
            decrypt_window.title("التقرير المفكوك")
            decrypt_window.geometry("800x600")
            decrypt_window.configure(background=self.bg_color)
            
            text_area = scrolledtext.ScrolledText(decrypt_window, bg=self.widget_bg, fg=self.fg_color, font=('Consolas', 10))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, decrypted)
            
        except Exception as e:
            messagebox.showerror("Error", f"فشل فك التشفير: {e}")

    def export_report(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab غير مثبت.\nالتثبيت: pip install reportlab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".aegis",
            filetypes=[("Encrypted files", "*.aegis"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not filename: 
            return

        raw_text = self.report_text.get("1.0", tk.END)
        encrypted_data = self.crypto.encrypt_data(raw_text)
        self.log(f"[+] تم تشفير التقرير")

        with open(filename, 'w') as f:
            f.write(str(encrypted_data))
        self.log(f"[+] تم حفظ التقرير المشفر: {filename}")

        if filename.endswith('.pdf'):
            try:
                doc = SimpleDocTemplate(filename, pagesize=(8.5*inch, 11*inch))
                styles = getSampleStyleSheet()
                story = []
                
                story.append(Paragraph("Falcon Security - Encrypted Report", styles['Title']))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Total Vulnerabilities: {len(self.vulnerabilities)}", styles['Normal']))
                story.append(Spacer(1, 12))
                
                enc_hex = encrypted_data['content'][:2000]
                story.append(Paragraph(f"<font fontName='Courier' size=8>{enc_hex}...</font>", styles['Normal']))
                
                doc.build(story)
                self.log("[+] تم إنشاء ملف PDF")
            except Exception as e:
                self.log(f"[-] خطأ في PDF: {e}")

        messagebox.showinfo("Success", "تم حفظ التقرير المشفر")


# ==========================================
# التشغيل
# ==========================================
if __name__ == "__main__":
    app = VulnerabilityScannerApp()
    app.mainloop()
