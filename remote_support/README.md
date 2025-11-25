# CompuEasys Remote Support

Sistema de soporte técnico remoto personalizado para CompuEasys.

## 🚀 Características

- ✅ **Conexión segura** con código de acceso único
- 🖥️ **Captura de pantalla en tiempo real**
- 🎮 **Control remoto** (con consentimiento del cliente)
- 💬 **Panel de comandos** para ejecutar tareas
- 🔒 **Privacidad garantizada** - El cliente autoriza cada conexión
- 📊 **Múltiples clientes** simultáneos

## 📦 Instalación

### Requisitos
- Python 3.8 o superior
- Windows/Linux/Mac

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🎯 Uso

### Para el Técnico (Servidor)

1. Ejecutar el servidor:
```bash
python server.py
```

2. El servidor estará escuchando en el puerto 9999
3. Cuando un cliente se conecte, aparecerá en la lista
4. Solicita el código de acceso al cliente
5. Ingresa el código para iniciar la sesión de soporte

### Para el Cliente

1. Ejecutar el cliente:
```bash
python client.py
```

2. Ingresar la IP del servidor (proporcionada por el técnico)
3. Hacer clic en "Conectar"
4. Compartir el código de 6 dígitos con el técnico
5. El técnico podrá ver tu pantalla y ayudarte

## 🔐 Seguridad

- Cada conexión genera un código único de 6 dígitos
- El cliente debe autorizar explícitamente cada sesión
- El cliente puede desconectarse en cualquier momento
- No se almacenan datos sensibles

## 📝 Compilar para distribución

### Windows (EXE)

```bash
pip install pyinstaller

# Compilar cliente
pyinstaller --onefile --windowed --icon=icon.ico --name="CompuEasys-Cliente" client.py

# Compilar servidor
pyinstaller --onefile --windowed --icon=icon.ico --name="CompuEasys-Servidor" server.py
```

Los ejecutables estarán en la carpeta `dist/`

### Configurar en Django

1. Copiar `CompuEasys-Cliente.exe` a `media_files/upload/`
2. Actualizar el enlace en `home.html`:

```html
<a href="/media_files/upload/CompuEasys-Cliente.exe" download="CompuEasys-SoporteRemoto.exe" class="btn btn-success">
    <i class="bi bi-hdd"></i> Descargar Cliente Remoto CompuEasys
</a>
```

## 🛠️ Funcionalidades Futuras

- [ ] Control de mouse y teclado en tiempo real
- [ ] Chat integrado técnico-cliente
- [ ] Transferencia de archivos
- [ ] Grabación de sesiones
- [ ] Múltiples monitores
- [ ] Encriptación de datos

## 📞 Soporte

Para más información: soporte@compueasys.com

---

**CompuEasys** - Soluciones Tecnológicas Integrales
