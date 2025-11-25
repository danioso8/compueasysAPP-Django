"""
CompuEasys Remote Support - Servidor
Servidor de control remoto para técnicos de soporte
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import io
import json
import secrets
import string

class RemoteSupportServer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CompuEasys Remote Support - Servidor")
        self.window.geometry("1200x800")
        
        self.clients = {}
        self.active_session = None
        self.server_socket = None
        self.running = False
        
        self.setup_ui()
        self.start_server()
        
    def setup_ui(self):
        """Configurar interfaz gráfica"""
        # Frame superior - Información del servidor
        top_frame = ttk.Frame(self.window, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="🖥️ CompuEasys Remote Support", 
                 font=("Arial", 16, "bold")).pack()
        
        self.status_label = ttk.Label(top_frame, text="Estado: Iniciando...", 
                                      font=("Arial", 10))
        self.status_label.pack()
        
        # Frame principal con dos columnas
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Columna izquierda - Lista de clientes
        left_frame = ttk.LabelFrame(main_frame, text="Clientes Conectados", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        self.clients_listbox = tk.Listbox(left_frame, width=30, height=15)
        self.clients_listbox.pack(fill=tk.BOTH, expand=True)
        self.clients_listbox.bind('<<ListboxSelect>>', self.on_client_select)
        
        # Botones de control
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Conectar", 
                  command=self.connect_to_client).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Desconectar", 
                  command=self.disconnect_client).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Actualizar Lista", 
                  command=self.refresh_clients).pack(fill=tk.X, pady=2)
        
        # Columna derecha - Visor de pantalla y controles
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Visor de pantalla remota
        screen_frame = ttk.LabelFrame(right_frame, text="Pantalla Remota", padding="10")
        screen_frame.pack(fill=tk.BOTH, expand=True)
        
        self.screen_label = ttk.Label(screen_frame, text="Selecciona un cliente para ver su pantalla")
        self.screen_label.pack(fill=tk.BOTH, expand=True)
        
        # Panel de chat/comandos
        control_frame = ttk.LabelFrame(right_frame, text="Panel de Control", padding="10")
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(control_frame, height=8, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Entrada de comandos
        cmd_frame = ttk.Frame(control_frame)
        cmd_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(cmd_frame, text="Comando:").pack(side=tk.LEFT)
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(cmd_frame, text="Enviar", 
                  command=self.send_command).pack(side=tk.LEFT)
        
    def start_server(self):
        """Iniciar servidor socket"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', 9999))
            self.server_socket.listen(5)
            self.running = True
            
            # Hilo para aceptar conexiones
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
            self.log("✅ Servidor iniciado en puerto 9999")
            self.status_label.config(text="Estado: ✅ Servidor activo - Esperando clientes...")
            
        except Exception as e:
            self.log(f"❌ Error al iniciar servidor: {e}")
            messagebox.showerror("Error", f"No se pudo iniciar el servidor: {e}")
    
    def accept_connections(self):
        """Aceptar conexiones entrantes"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.log(f"🔌 Nueva conexión desde {address}")
                
                # Recibir información del cliente
                data = client_socket.recv(4096).decode('utf-8')
                client_info = json.loads(data)
                
                # Generar código de acceso único
                access_code = ''.join(secrets.choice(string.digits) for _ in range(6))
                
                client_id = f"{client_info['hostname']} ({address[0]})"
                self.clients[client_id] = {
                    'socket': client_socket,
                    'address': address,
                    'info': client_info,
                    'access_code': access_code
                }
                
                # Enviar código de acceso al cliente
                response = {'access_code': access_code}
                client_socket.send(json.dumps(response).encode('utf-8'))
                
                self.log(f"✅ Cliente registrado: {client_id} - Código: {access_code}")
                self.refresh_clients_list()
                
            except Exception as e:
                if self.running:
                    self.log(f"❌ Error aceptando conexión: {e}")
    
    def refresh_clients_list(self):
        """Actualizar lista de clientes en UI"""
        self.clients_listbox.delete(0, tk.END)
        for client_id in self.clients.keys():
            self.clients_listbox.insert(tk.END, client_id)
    
    def refresh_clients(self):
        """Refrescar lista de clientes"""
        self.refresh_clients_list()
        self.log("🔄 Lista de clientes actualizada")
    
    def on_client_select(self, event):
        """Cuando se selecciona un cliente"""
        selection = self.clients_listbox.curselection()
        if selection:
            client_id = self.clients_listbox.get(selection[0])
            info = self.clients[client_id]['info']
            self.log(f"📋 Cliente seleccionado: {client_id}")
            self.log(f"   Sistema: {info['system']} {info['release']}")
            self.log(f"   Código de acceso: {self.clients[client_id]['access_code']}")
    
    def connect_to_client(self):
        """Conectar a cliente seleccionado"""
        selection = self.clients_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona un cliente primero")
            return
        
        client_id = self.clients_listbox.get(selection[0])
        
        # Solicitar código de acceso
        code = tk.simpledialog.askstring("Código de Acceso", 
                                         f"Ingresa el código de acceso para {client_id}:")
        
        if not code:
            return
        
        if code == self.clients[client_id]['access_code']:
            self.active_session = client_id
            self.log(f"🔓 Conexión autorizada con {client_id}")
            self.send_command_to_client(client_id, {'action': 'start_screen_share'})
            self.start_screen_capture(client_id)
        else:
            messagebox.showerror("Error", "Código de acceso incorrecto")
            self.log(f"❌ Intento de acceso fallido a {client_id}")
    
    def disconnect_client(self):
        """Desconectar cliente activo"""
        if self.active_session:
            self.send_command_to_client(self.active_session, {'action': 'stop_screen_share'})
            self.active_session = None
            self.screen_label.config(text="Sesión desconectada", image='')
            self.log("🔌 Sesión desconectada")
        else:
            messagebox.showinfo("Info", "No hay sesión activa")
    
    def start_screen_capture(self, client_id):
        """Iniciar captura de pantalla del cliente"""
        def capture_loop():
            while self.active_session == client_id:
                try:
                    self.send_command_to_client(client_id, {'action': 'capture_screen'})
                    
                    # Recibir imagen
                    client_socket = self.clients[client_id]['socket']
                    size_data = client_socket.recv(8)
                    if not size_data:
                        break
                    
                    img_size = int.from_bytes(size_data, 'big')
                    img_data = b''
                    
                    while len(img_data) < img_size:
                        chunk = client_socket.recv(min(4096, img_size - len(img_data)))
                        if not chunk:
                            break
                        img_data += chunk
                    
                    # Mostrar imagen
                    if img_data:
                        image = Image.open(io.BytesIO(img_data))
                        # Redimensionar para que quepa en la ventana
                        image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self.screen_label.config(image=photo)
                        self.screen_label.image = photo
                        
                        # Vincular eventos de mouse y teclado
                        self.screen_label.bind('<Button-1>', lambda e: self.send_mouse_click(client_id, e.x, e.y, 'left'))
                        self.screen_label.bind('<Button-3>', lambda e: self.send_mouse_click(client_id, e.x, e.y, 'right'))
                        self.screen_label.bind('<Motion>', lambda e: self.send_mouse_move(client_id, e.x, e.y))
                    
                    self.window.after(500)  # Actualizar cada 500ms
                    
                except Exception as e:
                    self.log(f"❌ Error capturando pantalla: {e}")
                    break
        
        threading.Thread(target=capture_loop, daemon=True).start()
    
    def send_mouse_click(self, client_id, x, y, button):
        """Enviar evento de clic de mouse al cliente"""
        # Ajustar coordenadas a la resolución original del cliente
        self.send_command_to_client(client_id, {
            'action': 'mouse_click',
            'x': x,
            'y': y,
            'button': button
        })
        self.log(f"🖱️ Clic {button} en ({x}, {y})")
    
    def send_mouse_move(self, client_id, x, y):
        """Enviar movimiento de mouse al cliente"""
        self.send_command_to_client(client_id, {
            'action': 'mouse_move',
            'x': x,
            'y': y
        })
    
    def send_command_to_client(self, client_id, command):
        """Enviar comando a cliente específico"""
        try:
            client_socket = self.clients[client_id]['socket']
            client_socket.send(json.dumps(command).encode('utf-8'))
        except Exception as e:
            self.log(f"❌ Error enviando comando: {e}")
    
    def send_command(self):
        """Enviar comando personalizado"""
        if not self.active_session:
            messagebox.showwarning("Aviso", "No hay sesión activa")
            return
        
        cmd = self.cmd_entry.get().strip()
        if cmd:
            self.send_command_to_client(self.active_session, {'action': 'execute', 'command': cmd})
            self.log(f"📤 Comando enviado: {cmd}")
            self.cmd_entry.delete(0, tk.END)
    
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def run(self):
        """Ejecutar aplicación"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        """Cerrar aplicación"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.window.destroy()

if __name__ == "__main__":
    import tkinter.simpledialog
    server = RemoteSupportServer()
    server.run()
