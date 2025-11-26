"""
CompuEasys Remote Support - Cliente (con Relay Server)
Cliente de soporte remoto que se conecta a través de servidor relay en Render
"""

import json
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab
import io
import threading
import time
import requests
from io import BytesIO
import base64

class RemoteSupportClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CompuEasys Remote Support - Cliente")
        self.window.geometry("600x500")  # Más grande para ver mejor el código
        
        self.connected = False
        self.client_id = f"{platform.node()}_{int(time.time())}"
        self.session_id = None
        self.sharing_screen = False
        self.technician_connected = False
        
        # URL del servidor relay en Render
        self.relay_url = "https://compueasys.onrender.com/api/relay"
        
        self.setup_ui()
        
        # Conectar automáticamente al iniciar
        self.window.after(1000, self.auto_connect)
        
    def setup_ui(self):
        """Configurar interfaz gráfica"""
        # Header
        header = ttk.Frame(self.window, padding="20")
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="🛠️ CompuEasys Remote Support", 
                 font=("Arial", 18, "bold")).pack()
        ttk.Label(header, text="Soporte Técnico Remoto", 
                 font=("Arial", 10)).pack()
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Información del sistema
        info_frame = ttk.LabelFrame(main_frame, text="Información del Sistema", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        system_info = f"Sistema: {platform.system()} {platform.release()}\n"
        system_info += f"Máquina: {platform.machine()}\n"
        system_info += f"Nombre: {platform.node()}"
        
        ttk.Label(info_frame, text=system_info, justify=tk.LEFT).pack()
        
        # Estado de conexión
        status_frame = ttk.LabelFrame(main_frame, text="Estado de Conexión", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connection_status = ttk.Label(status_frame, 
                                          text="🔄 Conectando automáticamente...", 
                                          font=("Arial", 10, "bold"))
        self.connection_status.pack(pady=5)
        
        ttk.Label(status_frame, text="Esperando solicitud de conexión del técnico", 
                 font=("Arial", 9, "italic"), foreground="gray").pack()
        
        # ID de sesión - VISIBLE Y SIMPLE
        id_frame = ttk.LabelFrame(main_frame, text="🆔 Identificación del Cliente", padding="20")
        id_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Frame para ID
        id_container = tk.Frame(id_frame, bg="#f0f0f0", bd=2, relief=tk.SOLID)
        id_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(id_container, text="Tu ID de Cliente:", 
                 font=("Arial", 11, "bold")).pack(pady=(10, 5))
        
        self.client_id_label = tk.Label(id_container, text="Conectando...", 
                                        font=("Courier New", 16, "bold"),
                                        foreground="#0066cc",
                                        background="#f0f0f0")
        self.client_id_label.pack(pady=(0, 10))
        
        ttk.Label(id_frame, text="El técnico verá este ID en su lista y podrá conectarse", 
                 font=("Arial", 9, "italic"), foreground="gray").pack(pady=5)
        
        # Log de actividad
        log_frame = ttk.LabelFrame(main_frame, text="📋 Actividad", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, 
                               font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.disconnect_btn = ttk.Button(button_frame, text="❌ Desconectar", 
                                        command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.RIGHT)
        
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def auto_connect(self):
        """Conectar automáticamente al relay al iniciar"""
        threading.Thread(target=self.connect_to_relay_auto, daemon=True).start()
    
    def connect_to_relay_auto(self):
        """Conectar automáticamente al relay"""
        try:
            self.log("🔄 Conectando a CompuEasys Cloud...")
            self.log(f"🆔 Tu ID: {self.client_id}")
            self.log(f"🌐 URL: {self.relay_url}/register_client/")
            
            # Registrar cliente en el relay
            self.log("📡 Enviando petición de registro...")
            response = requests.post(
                f"{self.relay_url}/register_client/",
                json={
                    'client_id': self.client_id,
                    'access_code': '',  # No necesitamos código
                    'client_name': platform.node(),
                    'os': f"{platform.system()} {platform.release()}"
                },
                timeout=15
            )
            
            self.log(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.session_id = data['session_id']
                    self.connected = True
                    
                    # Actualizar UI
                    self.connection_status.config(text="✅ Conectado - Esperando técnico")
                    self.client_id_label.config(text=platform.node())
                    
                    self.log(f"✅ Conectado exitosamente")
                    self.log(f"⏳ Esperando solicitud de conexión...")
                    
                    # Iniciar thread para escuchar solicitudes
                    threading.Thread(target=self.listen_for_connection_requests, daemon=True).start()
                else:
                    self.log(f"❌ Error: {data}")
                    self.connection_status.config(text="❌ Error de conexión")
            else:
                self.log(f"❌ Error HTTP {response.status_code}")
                self.connection_status.config(text="❌ Error de conexión")
                
        except requests.exceptions.Timeout:
            self.log(f"⏱️ Timeout - El servidor no respondió")
            self.log("🔄 Reintentando en 10 segundos...")
            self.connection_status.config(text="🔄 Reintentando...")
            self.window.after(10000, self.auto_connect)
        except requests.exceptions.ConnectionError as e:
            self.log(f"🔌 Error de conexión a internet")
            self.log(f"📝 {str(e)[:80]}")
            self.log("🔄 Reintentando en 10 segundos...")
            self.connection_status.config(text="🔄 Reintentando...")
            self.window.after(10000, self.auto_connect)
        except Exception as e:
            self.log(f"⚠️ Error: {type(e).__name__}")
            self.log(f"📝 {str(e)[:100]}")
            self.log("🔄 Reintentando en 10 segundos...")
            self.connection_status.config(text="🔄 Reintentando...")
            self.window.after(10000, self.auto_connect)
    
    def listen_for_connection_requests(self):
        """Escuchar solicitudes de conexión de técnicos"""
        while self.connected:
            try:
                response = requests.get(
                    f"{self.relay_url}/check_connection_request/",
                    params={'session_id': self.session_id},
                    timeout=30  # Long polling
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('connection_request'):
                        # Hay una solicitud de conexión
                        tech_name = data.get('technician_name', 'Técnico')
                        self.ask_authorization(tech_name)
                        
            except Exception as e:
                if self.connected:
                    time.sleep(5)  # Esperar antes de reintentar
                    
    def ask_authorization(self, tech_name):
        """Pedir autorización al usuario para permitir conexión"""
        result = messagebox.askyesno(
            "Solicitud de Conexión",
            f"🔔 El técnico '{tech_name}' quiere conectarse a tu PC.\n\n"
            f"¿Permitir el acceso remoto?",
            icon='question'
        )
        
        if result:
            self.authorize_connection()
        else:
            self.deny_connection()
    
    def authorize_connection(self):
        """Autorizar la conexión del técnico"""
        try:
            response = requests.post(
                f"{self.relay_url}/authorize_connection/",
                json={'session_id': self.session_id, 'authorized': True},
                timeout=10
            )
            
            if response.status_code == 200:
                self.technician_connected = True
                self.connection_status.config(text="✅ Técnico conectado")
                self.log("✅ Conexión autorizada")
                self.log("👁️ El técnico puede ver tu pantalla")
                
                # Iniciar compartir pantalla
                threading.Thread(target=self.send_screen_loop, daemon=True).start()
                threading.Thread(target=self.receive_commands_loop, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Error al autorizar: {str(e)[:100]}")
    
    def deny_connection(self):
        """Denegar la conexión del técnico"""
        try:
            requests.post(
                f"{self.relay_url}/authorize_connection/",
                json={'session_id': self.session_id, 'authorized': False},
                timeout=10
            )
            self.log("❌ Conexión denegada")
        except:
            pass
        

            
    def send_screen_loop(self):
        """Enviar capturas de pantalla continuamente"""
        while self.connected:
            try:
                # Capturar pantalla
                screenshot = ImageGrab.grab()
                screenshot.thumbnail((1280, 720), Image.LANCZOS)
                
                # Convertir a JPEG base64
                buffer = BytesIO()
                screenshot.save(buffer, format='JPEG', quality=60)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Enviar al relay
                requests.post(
                    f"{self.relay_url}/send_message/",
                    json={
                        'session_id': self.session_id,
                        'sender': 'client',
                        'message': {
                            'type': 'screen',
                            'data': img_base64
                        }
                    },
                    timeout=5
                )
                
                time.sleep(0.5)  # Actualizar cada 500ms
                
            except Exception as e:
                if self.connected:
                    self.log(f"⚠️ Error al enviar pantalla: {str(e)}")
                time.sleep(1)
                
    def receive_commands_loop(self):
        """Recibir comandos del técnico"""
        while self.connected:
            try:
                response = requests.post(
                    f"{self.relay_url}/receive_messages/",
                    json={
                        'session_id': self.session_id,
                        'receiver': 'client'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        for msg in data['messages']:
                            self.process_command(msg['message'])
                        
                        # Verificar si la sesión sigue activa
                        if not data['session_active']:
                            self.log("🔴 El técnico se desconectó")
                            self.disconnect()
                            break
                            
                time.sleep(1)  # Polling cada segundo
                
            except Exception as e:
                if self.connected:
                    self.log(f"⚠️ Error al recibir comandos: {str(e)}")
                time.sleep(2)
                
    def process_command(self, command):
        """Procesar comando recibido del técnico"""
        try:
            cmd_type = command.get('action')
            
            if cmd_type == 'mouse_click':
                self.handle_mouse_click(command['x'], command['y'], command['button'])
            elif cmd_type == 'mouse_move':
                self.handle_mouse_move(command['x'], command['y'])
            elif cmd_type == 'keyboard_input':
                self.handle_keyboard_input(command['keys'])
            elif cmd_type == 'execute_command':
                self.execute_remote_command(command['command'])
                
        except Exception as e:
            self.log(f"❌ Error al procesar comando: {str(e)}")
            
    def handle_mouse_click(self, x, y, button):
        """Manejar clic de mouse remoto"""
        try:
            import pyautogui
            # Ajustar coordenadas (800x600 en remoto → resolución real)
            screen_width, screen_height = pyautogui.size()
            adjusted_x = int(x * screen_width / 800)
            adjusted_y = int(y * screen_height / 600)
            
            if button == 'left':
                pyautogui.click(adjusted_x, adjusted_y)
            elif button == 'right':
                pyautogui.rightClick(adjusted_x, adjusted_y)
                
            self.log(f"🖱️ Clic {button} en ({adjusted_x}, {adjusted_y})")
        except Exception as e:
            self.log(f"❌ Error en clic: {str(e)}")
            
    def handle_mouse_move(self, x, y):
        """Manejar movimiento de mouse"""
        try:
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            adjusted_x = int(x * screen_width / 800)
            adjusted_y = int(y * screen_height / 600)
            pyautogui.moveTo(adjusted_x, adjusted_y)
        except:
            pass
            
    def handle_keyboard_input(self, keys):
        """Manejar entrada de teclado"""
        try:
            import pyautogui
            pyautogui.write(keys)
            self.log(f"⌨️ Texto escrito: {keys}")
        except Exception as e:
            self.log(f"❌ Error en teclado: {str(e)}")
            
    def execute_remote_command(self, command):
        """Ejecutar comando del sistema"""
        try:
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.log(f"💻 Comando ejecutado: {command}")
        except Exception as e:
            self.log(f"❌ Error al ejecutar: {str(e)}")
            
    def disconnect(self):
        """Desconectar del soporte"""
        try:
            if self.session_id:
                requests.post(
                    f"{self.relay_url}/disconnect/",
                    json={
                        'session_id': self.session_id,
                        'who': 'client'
                    },
                    timeout=5
                )
        except:
            pass
            
        self.connected = False
        self.session_id = None
        self.access_code = None
        
        self.status_label.config(text="⚪ Desconectado", foreground="black")
        self.code_label.config(text="")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.log("🔴 Desconectado del soporte")
        
    def run(self):
        """Iniciar aplicación"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
        
    def on_closing(self):
        """Manejar cierre de ventana"""
        if self.connected:
            self.disconnect()
        self.window.destroy()

if __name__ == "__main__":
    try:
        # Importar PIL.Image si es necesario
        from PIL import Image
    except ImportError:
        print("Error: Necesitas instalar Pillow: pip install pillow")
        exit(1)
        
    client = RemoteSupportClient()
    client.run()
