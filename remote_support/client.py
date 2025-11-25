"""
CompuEasys Remote Support - Cliente
Cliente de soporte remoto para usuarios finales
"""

import socket
import json
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab
import io
import threading
import subprocess
import os

class RemoteSupportClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CompuEasys Remote Support - Cliente")
        self.window.geometry("500x400")
        
        self.connected = False
        self.access_code = None
        self.client_socket = None
        self.sharing_screen = False
        
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
        
        ttk.Label(connect_frame, text="IP del Servidor:").pack(anchor=tk.W)
        self.server_ip_entry = ttk.Entry(connect_frame)
        self.server_ip_entry.insert(0, "127.0.0.1")  # Localhost por defecto
        self.server_ip_entry.pack(fill=tk.X, pady=(0, 10))
        
        self.connect_btn = ttk.Button(connect_frame, text="🔌 Conectar", 
                                      command=self.connect_to_server)
        self.connect_btn.pack(fill=tk.X)
        
        # Código de acceso
        code_frame = ttk.LabelFrame(main_frame, text="Código de Acceso", padding="10")
        code_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.code_label = ttk.Label(code_frame, text="No conectado", 
                                    font=("Arial", 24, "bold"),
                                    foreground="gray")
        self.code_label.pack()
        
        ttk.Label(code_frame, text="Comparte este código con el técnico", 
                 font=("Arial", 9), foreground="gray").pack()
        
        # Estado
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(status_frame, 
                                     text="⚪ Desconectado", 
                                     font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # Botón de desconexión
        self.disconnect_btn = ttk.Button(status_frame, text="❌ Desconectar", 
                                        command=self.disconnect,
                                        state='disabled')
        self.disconnect_btn.pack()
        
    def connect_to_server(self):
        """Conectar al servidor de soporte"""
        server_ip = self.server_ip_entry.get().strip()
        
        if not server_ip:
            messagebox.showwarning("Aviso", "Ingresa la IP del servidor")
            return
        
        try:
            self.status_label.config(text="🔄 Conectando...", foreground="orange")
            self.window.update()
            
            # Crear socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, 9999))
            
            # Enviar información del sistema
            system_info = {
                'hostname': platform.node(),
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
            
            self.client_socket.send(json.dumps(system_info).encode('utf-8'))
            
            # Recibir código de acceso
            response = self.client_socket.recv(4096).decode('utf-8')
            data = json.loads(response)
            self.access_code = data['access_code']
            
            self.connected = True
            self.code_label.config(text=self.access_code, foreground="green")
            self.status_label.config(text="✅ Conectado - En espera", foreground="green")
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            self.server_ip_entry.config(state='disabled')
            
            # Iniciar hilo para recibir comandos
            threading.Thread(target=self.receive_commands, daemon=True).start()
            
            messagebox.showinfo("Éxito", 
                              f"Conectado al soporte técnico\n\n"
                              f"Tu código de acceso es:\n{self.access_code}\n\n"
                              f"Comparte este código con el técnico")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")
            self.status_label.config(text="❌ Error de conexión", foreground="red")
            self.code_label.config(text="No conectado", foreground="gray")
    
    def receive_commands(self):
        """Recibir y ejecutar comandos del servidor"""
        while self.connected:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                command = json.loads(data)
                action = command.get('action')
                
                if action == 'start_screen_share':
                    self.sharing_screen = True
                    self.status_label.config(text="🎥 Compartiendo pantalla", 
                                           foreground="blue")
                
                elif action == 'stop_screen_share':
                    self.sharing_screen = False
                    self.status_label.config(text="✅ Conectado - En espera", 
                                           foreground="green")
                
                elif action == 'capture_screen':
                    self.capture_and_send_screen()
                
                elif action == 'execute':
                    cmd = command.get('command')
                    self.execute_command(cmd)
                
                elif action == 'mouse_click':
                    self.handle_mouse_click(command.get('x'), command.get('y'), command.get('button'))
                
                elif action == 'mouse_move':
                    self.handle_mouse_move(command.get('x'), command.get('y'))
                
                elif action == 'keyboard_input':
                    self.handle_keyboard_input(command.get('keys'))
                
            except Exception as e:
                print(f"Error recibiendo comandos: {e}")
                break
        
        self.disconnect()
    
    def handle_mouse_click(self, x, y, button):
        """Ejecutar clic de mouse en las coordenadas especificadas"""
        try:
            import pyautogui
            # Ajustar coordenadas proporcionalmente
            screen_width, screen_height = pyautogui.size()
            adjusted_x = int(x * screen_width / 800)  # 800 es el ancho de la vista remota
            adjusted_y = int(y * screen_height / 600)  # 600 es el alto de la vista remota
            
            if button == 'left':
                pyautogui.click(adjusted_x, adjusted_y)
            elif button == 'right':
                pyautogui.rightClick(adjusted_x, adjusted_y)
        except Exception as e:
            print(f"Error ejecutando clic: {e}")
    
    def handle_mouse_move(self, x, y):
        """Mover el mouse a las coordenadas especificadas"""
        try:
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            adjusted_x = int(x * screen_width / 800)
            adjusted_y = int(y * screen_height / 600)
            pyautogui.moveTo(adjusted_x, adjusted_y, duration=0.1)
        except Exception as e:
            print(f"Error moviendo mouse: {e}")
    
    def handle_keyboard_input(self, keys):
        """Simular entrada de teclado"""
        try:
            import pyautogui
            pyautogui.write(keys)
        except Exception as e:
            print(f"Error con teclado: {e}")
    
    def capture_and_send_screen(self):
        """Capturar y enviar pantalla al servidor"""
        try:
            # Capturar pantalla
            screenshot = ImageGrab.grab()
            
            # Redimensionar para optimizar transferencia
            screenshot.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            
            # Convertir a bytes
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='JPEG', quality=60)
            img_data = img_byte_arr.getvalue()
            
            # Enviar tamaño y luego imagen
            size = len(img_data)
            self.client_socket.send(size.to_bytes(8, 'big'))
            self.client_socket.sendall(img_data)
            
        except Exception as e:
            print(f"Error capturando pantalla: {e}")
    
    def execute_command(self, command):
        """Ejecutar comando del sistema"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            response = {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            self.client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            error_response = {'error': str(e)}
            self.client_socket.send(json.dumps(error_response).encode('utf-8'))
    
    def disconnect(self):
        """Desconectar del servidor"""
        self.connected = False
        self.sharing_screen = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        self.code_label.config(text="No conectado", foreground="gray")
        self.status_label.config(text="⚪ Desconectado", foreground="gray")
        self.connect_btn.config(state='normal')
        self.disconnect_btn.config(state='disabled')
        self.server_ip_entry.config(state='normal')
        self.access_code = None
    
    def run(self):
        """Ejecutar aplicación"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        """Cerrar aplicación"""
        self.disconnect()
        self.window.destroy()

if __name__ == "__main__":
    client = RemoteSupportClient()
    client.run()
