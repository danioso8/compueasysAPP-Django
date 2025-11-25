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
        self.window.geometry("500x400")
        
        self.connected = False
        self.access_code = None
        self.session_id = None
        self.sharing_screen = False
        
        # URL del servidor relay en Render
        self.relay_url = "https://compueasys.onrender.com/api/relay"
        
        self.setup_ui()
        
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
        
        # Conexión
        connect_frame = ttk.LabelFrame(main_frame, text="Conectar con Soporte", padding="10")
        connect_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(connect_frame, text="Conexión a través de CompuEasys Cloud", 
                 font=("Arial", 9, "italic")).pack(anchor=tk.W, pady=(0, 10))
        
        self.connect_btn = ttk.Button(connect_frame, text="🔗 Conectar con Soporte", 
                                     command=self.connect_to_relay, style='Accent.TButton')
        self.connect_btn.pack(fill=tk.X)
        
        # Código de acceso
        code_frame = ttk.LabelFrame(main_frame, text="Código de Acceso", padding="10")
        code_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.code_label = ttk.Label(code_frame, text="", 
                                    font=("Courier New", 24, "bold"), 
                                    foreground="green")
        self.code_label.pack()
        
        ttk.Label(code_frame, text="Comparte este código con el técnico", 
                 font=("Arial", 9, "italic")).pack()
        
        # Status
        self.status_frame = ttk.LabelFrame(main_frame, text="Estado", padding="10")
        self.status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(self.status_frame, text="⚪ Desconectado", 
                                     font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        self.log_text = tk.Text(self.status_frame, height=5, state=tk.DISABLED)
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
        
    def generate_access_code(self):
        """Generar código de acceso de 6 dígitos"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
    def connect_to_relay(self):
        """Conectar al servidor relay en Render"""
        try:
            self.log("Conectando al servidor CompuEasys...")
            self.connect_btn.config(state=tk.DISABLED)
            
            # Generar código de acceso
            self.access_code = self.generate_access_code()
            client_id = f"{platform.node()}_{int(time.time())}"
            
            # Registrar cliente en el relay
            response = requests.post(
                f"{self.relay_url}/register_client/",
                json={
                    'client_id': client_id,
                    'access_code': self.access_code
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.session_id = data['session_id']
                    self.connected = True
                    
                    # Actualizar UI
                    self.code_label.config(text=self.access_code)
                    self.status_label.config(text="🟢 Conectado - Esperando técnico", 
                                           foreground="green")
                    self.disconnect_btn.config(state=tk.NORMAL)
                    
                    self.log(f"✅ Conectado exitosamente")
                    self.log(f"📋 Código de acceso: {self.access_code}")
                    self.log("⏳ Esperando que el técnico se conecte...")
                    
                    # Iniciar threads
                    threading.Thread(target=self.receive_commands_loop, daemon=True).start()
                    threading.Thread(target=self.send_screen_loop, daemon=True).start()
                else:
                    raise Exception(data.get('error', 'Error desconocido'))
            else:
                raise Exception(f"Error HTTP {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Error al conectar: {str(e)}")
            self.connect_btn.config(state=tk.NORMAL)
            messagebox.showerror("Error de Conexión", 
                               f"No se pudo conectar al servidor:\n{str(e)}")
            
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
