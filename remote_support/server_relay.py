"""
CompuEasys Remote Support - Servidor Técnico (con Relay Server)
Servidor para técnicos que se conecta a través de servidor relay en Render
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import time
import requests
from io import BytesIO
import base64

class RemoteSupportServer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CompuEasys Remote Support - Servidor Técnico")
        self.window.geometry("1000x700")
        
        self.connected = False
        self.session_id = None
        self.current_screen = None
        self.session_map = {}  # Mapeo de índice a session_id
        
        # URL del servidor relay en Render
        self.relay_url = "https://compueasys.onrender.com/api/relay"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz gráfica"""
        # Header
        header = ttk.Frame(self.window, padding="10")
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="🛠️ CompuEasys Remote Support - Panel Técnico", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header, text="⚪ Sin conectar", 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT)
        
        # Contenedor principal
        main_container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel izquierdo - Sesiones disponibles
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        ttk.Label(left_panel, text="Sesiones Disponibles", 
                 font=("Arial", 12, "bold")).pack(pady=5)
        
        # Título de la lista
        ttk.Label(left_panel, text="CLIENTES CONECTADOS", 
                 font=("Arial", 12, "bold")).pack(pady=(5,0))
        
        # Lista de sesiones - Configuración mejorada
        listbox_frame = ttk.Frame(left_panel)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sessions_listbox = tk.Listbox(listbox_frame, height=10, 
                                           font=("Arial", 11, "bold"),
                                           bg="#f0f0f0", fg="#000000",
                                           selectbackground="#0078d7",
                                           selectforeground="white",
                                           yscrollcommand=scrollbar.set)
        self.sessions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sessions_listbox.yview)
        
        # Botones de control
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="🔄 Actualizar Lista", 
                  command=self.refresh_sessions).pack(fill=tk.X, pady=2)
        self.connect_btn = ttk.Button(control_frame, text="🔗 Solicitar Conexión", 
                  command=self.request_connection_to_client, 
                  style='Accent.TButton')
        self.connect_btn.pack(fill=tk.X, pady=2)
        self.disconnect_btn = ttk.Button(control_frame, text="❌ Desconectar", 
                                        command=self.disconnect, 
                                        state=tk.DISABLED)
        self.disconnect_btn.pack(fill=tk.X, pady=2)
        
        # Doble click en lista para conectar
        self.sessions_listbox.bind('<Double-Button-1>', lambda e: self.request_connection_to_client())
        
        # Panel derecho - Vista remota
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=3)
        
        # Frame de pantalla
        screen_frame = ttk.LabelFrame(right_panel, text="Pantalla del Cliente", padding="5")
        screen_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para mostrar pantalla
        self.screen_canvas = tk.Canvas(screen_frame, bg="black", width=800, height=600)
        self.screen_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind eventos de mouse
        self.screen_canvas.bind("<Button-1>", self.on_screen_left_click)
        self.screen_canvas.bind("<Button-3>", self.on_screen_right_click)
        self.screen_canvas.bind("<Motion>", self.on_screen_mouse_move)
        
        # Panel de control
        control_panel = ttk.Frame(right_panel)
        control_panel.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_panel, text="Controles:", 
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_panel, text="⌨️ Enviar Texto", 
                  command=self.send_keyboard_input).pack(side=tk.LEFT, padx=2)
        
        # Log
        log_frame = ttk.LabelFrame(right_panel, text="Registro de Actividad", padding="5")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=5, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Iniciar actualización de sesiones
        self.log("🚀 Iniciando CompuEasys Servidor Cloud...")
        self.log(f"🌐 Conectando a: {self.relay_url}")
        self.refresh_sessions()
        
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        # También imprimir en consola para debugging
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def refresh_sessions(self):
        """Actualizar lista de sesiones disponibles"""
        try:
            self.log(f"🔄 Actualizando lista de sesiones...")
            response = requests.get(f"{self.relay_url}/list_sessions/", timeout=5)
            self.log(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.sessions_listbox.delete(0, tk.END)
                    self.session_map.clear()  # Limpiar mapeo anterior
                    sessions = data['sessions']
                    
                    if not sessions:
                        self.sessions_listbox.insert(tk.END, "--- No hay clientes ---")
                        self.log("📋 0 clientes disponibles")
                    else:
                        for idx, session in enumerate(sessions):
                            client_name = session.get('client_name', session.get('client_id', 'Cliente'))
                            os_info = session.get('os', 'Unknown OS')
                            session_id = session.get('session_id', '')
                            
                            # Guardar mapeo de índice a session_id
                            self.session_map[idx] = session_id
                            
                            # Formato: numero - nombre - OS
                            display_text = f"{idx+1}. {client_name} - {os_info}"
                            self.sessions_listbox.insert(tk.END, display_text)
                            self.log(f"➕ Agregado #{idx+1}: {client_name}")
                        
                        self.log(f"✅ {len(sessions)} cliente(s) disponible(s)")
                        self.log(f"📋 Items en listbox: {self.sessions_listbox.size()}")
                        
                        # Triple actualización forzada
                        self.sessions_listbox.update_idletasks()
                        self.sessions_listbox.update()
                        self.window.update()
            else:
                self.log(f"❌ Error HTTP {response.status_code}")
                self.sessions_listbox.delete(0, tk.END)
                self.sessions_listbox.insert(tk.END, f"❌ Error: {response.status_code}")
                        
            # Auto-refresh cada 5 segundos si no está conectado
            if not self.connected:
                self.window.after(5000, self.refresh_sessions)
        except Exception as e:
            self.log(f"⚠️ Error: {str(e)[:80]}")
            self.sessions_listbox.delete(0, tk.END)
            self.sessions_listbox.insert(tk.END, f"⚠️ Error de conexión")
            
    def request_connection_to_client(self):
        """Solicitar conexión a un cliente seleccionado"""
        selection = self.sessions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un cliente de la lista")
            return
        
        # Obtener el session_id del mapeo
        index = selection[0]
        session_id = self.session_map.get(index)
        
        if not session_id:
            messagebox.showerror("Error", "No se encontró el session_id del cliente")
            self.log(f"❌ Error: No hay session_id para índice {index}")
            self.log(f"📋 Session map: {self.session_map}")
            return
        
        try:
            self.log(f"📞 Solicitando conexión al cliente...")
            self.connect_btn.config(state=tk.DISABLED)
            
            # Solicitar conexión
            response = requests.post(
                f"{self.relay_url}/request_connection/",
                json={
                    'session_id': session_id,
                    'technician_name': platform.node()  # Nombre del técnico
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.session_id = session_id
                    self.log("⏳ Esperando autorización del cliente...")
                    
                    # Esperar autorización en otro thread
                    threading.Thread(target=self.wait_for_authorization, daemon=True).start()
                else:
                    raise Exception(data.get('error', 'Error en solicitud'))
            else:
                raise Exception(f"Error HTTP {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Error: {str(e)[:100]}")
            self.connect_btn.config(state=tk.NORMAL)
            messagebox.showerror("Error", f"No se pudo solicitar conexión:\n{str(e)[:80]}")
    
    def wait_for_authorization(self):
        """Esperar a que el cliente autorice la conexión"""
        try:
            response = requests.get(
                f"{self.relay_url}/check_authorization/",
                params={'session_id': self.session_id},
                timeout=35  # Esperar hasta 35s
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authorized'):
                    self.connected = True
                    self.log("✅ ¡Conexión autorizada!")
                    self.log("👁️ Ahora puedes ver la pantalla del cliente")
                    
                    # Actualizar UI
                    self.status_label.config(text="🟢 Conectado y Autorizado", foreground="green")
                    self.disconnect_btn.config(state=tk.NORMAL)
                    self.connect_btn.config(state=tk.DISABLED)
                    
                    # Iniciar recepción de pantalla
                    threading.Thread(target=self.receive_screen_loop, daemon=True).start()
                elif data.get('timeout'):
                    self.log("⏱️ Timeout - El cliente no respondió")
                    self.connect_btn.config(state=tk.NORMAL)
                    messagebox.showwarning("Timeout", "El cliente no respondió a tiempo")
                else:
                    self.log("❌ Conexión denegada por el cliente")
                    self.connect_btn.config(state=tk.NORMAL)
                    messagebox.showinfo("Denegado", "El cliente rechazó la conexión")
            else:
                raise Exception(f"Error HTTP {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Error esperando autorización: {str(e)[:100]}")
            self.connect_btn.config(state=tk.NORMAL)
            
    def receive_screen_loop(self):
        """Recibir pantallas del cliente continuamente"""
        while self.connected:
            try:
                response = requests.post(
                    f"{self.relay_url}/receive_messages/",
                    json={
                        'session_id': self.session_id,
                        'receiver': 'technician'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        for msg in data['messages']:
                            message = msg['message']
                            if message.get('type') == 'screen':
                                self.display_screen(message['data'])
                        
                        # Verificar si la sesión sigue activa
                        if not data['session_active']:
                            self.log("🔴 El cliente se desconectó")
                            self.disconnect()
                            break
                            
                time.sleep(0.5)  # Polling cada 500ms
                
            except Exception as e:
                if self.connected:
                    self.log(f"⚠️ Error al recibir pantalla: {str(e)}")
                time.sleep(1)
                
    def display_screen(self, img_base64):
        """Mostrar pantalla del cliente"""
        try:
            # Decodificar imagen base64
            img_data = base64.b64decode(img_base64)
            image = Image.open(BytesIO(img_data))
            
            # Redimensionar a 800x600
            image.thumbnail((800, 600), Image.LANCZOS)
            
            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Actualizar canvas
            self.screen_canvas.delete("all")
            self.screen_canvas.create_image(400, 300, image=photo)
            self.screen_canvas.image = photo  # Mantener referencia
            
            self.current_screen = photo
            
        except Exception as e:
            self.log(f"❌ Error al mostrar pantalla: {str(e)}")
            
    def on_screen_left_click(self, event):
        """Manejar clic izquierdo en pantalla"""
        if self.connected:
            self.send_mouse_command(event.x, event.y, 'left')
            
    def on_screen_right_click(self, event):
        """Manejar clic derecho en pantalla"""
        if self.connected:
            self.send_mouse_command(event.x, event.y, 'right')
            
    def on_screen_mouse_move(self, event):
        """Manejar movimiento de mouse (opcional)"""
        # Descomentar si quieres movimiento de mouse en tiempo real
        # if self.connected:
        #     self.send_mouse_move(event.x, event.y)
        pass
        
    def send_mouse_command(self, x, y, button):
        """Enviar comando de mouse al cliente"""
        try:
            requests.post(
                f"{self.relay_url}/send_message/",
                json={
                    'session_id': self.session_id,
                    'sender': 'technician',
                    'message': {
                        'action': 'mouse_click',
                        'x': x,
                        'y': y,
                        'button': button
                    }
                },
                timeout=2
            )
            self.log(f"🖱️ Clic {button} enviado en ({x}, {y})")
        except Exception as e:
            self.log(f"❌ Error al enviar clic: {str(e)}")
            
    def send_mouse_move(self, x, y):
        """Enviar movimiento de mouse"""
        try:
            requests.post(
                f"{self.relay_url}/send_message/",
                json={
                    'session_id': self.session_id,
                    'sender': 'technician',
                    'message': {
                        'action': 'mouse_move',
                        'x': x,
                        'y': y
                    }
                },
                timeout=1
            )
        except:
            pass
            
    def send_keyboard_input(self):
        """Enviar entrada de teclado"""
        if not self.connected:
            messagebox.showwarning("No Conectado", "Debes estar conectado a un cliente")
            return
            
        text = simpledialog.askstring("Enviar Texto", 
                                     "Escribe el texto a enviar:",
                                     parent=self.window)
        
        if text:
            try:
                requests.post(
                    f"{self.relay_url}/send_message/",
                    json={
                        'session_id': self.session_id,
                        'sender': 'technician',
                        'message': {
                            'action': 'keyboard_input',
                            'keys': text
                        }
                    },
                    timeout=5
                )
                self.log(f"⌨️ Texto enviado: {text}")
            except Exception as e:
                self.log(f"❌ Error al enviar texto: {str(e)}")
                
    def disconnect(self):
        """Desconectar de la sesión"""
        try:
            if self.session_id:
                requests.post(
                    f"{self.relay_url}/disconnect/",
                    json={
                        'session_id': self.session_id,
                        'who': 'technician'
                    },
                    timeout=5
                )
        except:
            pass
            
        self.connected = False
        self.session_id = None
        
        self.status_label.config(text="⚪ Sin conectar", foreground="black")
        self.disconnect_btn.config(state=tk.DISABLED)
        self.screen_canvas.delete("all")
        self.log("🔴 Desconectado")
        
        # Reanudar actualización de sesiones
        self.refresh_sessions()
        
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
    server = RemoteSupportServer()
    server.run()
