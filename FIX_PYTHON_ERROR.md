# SOLUCIÓN AL ERROR DE PYTHON

## 🔴 Problema Identificado

Tu entorno virtual fue creado con el alias problemático de Windows Store Python, que no funciona correctamente.

## ✅ Solución (3 pasos simples)

### **Paso 1: Eliminar el entorno virtual antiguo**
```cmd
rmdir /s /q venv_new
```

### **Paso 2: Crear nuevo entorno virtual con Python 3.13**
```cmd
C:\Python313\python.exe -m venv venv_new
```

### **Paso 3: Activar e instalar dependencias**
```cmd
venv_new\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Después de recrear el entorno, ejecuta:

```cmd
setup_contable.bat
```

O manualmente:
```cmd
venv_new\Scripts\activate
python manage.py makemigrations contable
python manage.py migrate
python manage.py init_plans
python manage.py runserver
```

---

## 🎯 Alternativa: Deshabilitar App Execution Aliases

1. Presiona `Windows + I` (Configuración)
2. Ve a **Aplicaciones** → **Aplicaciones instaladas** → **Alias de ejecución de aplicaciones**
3. Desactiva los switches de:
   - `python.exe`
   - `python3.exe`
   - `python3.7.exe`

Luego reinicia la terminal y vuelve a intentar.

---

## 📋 Comandos de Verificación

Después de recrear el venv, verifica que todo esté bien:

```cmd
# Activar entorno
venv_new\Scripts\activate

# Verificar versión de Python
python --version
# Debe mostrar: Python 3.13.x

# Verificar que Django esté instalado
python -c "import django; print(django.get_version())"
```

---

## ⚡ Quick Fix (Comando único)

Copia y pega esto en cmd:

```cmd
cd D:\ESCRITORIO\CompueasysApp && rmdir /s /q venv_new && C:\Python313\python.exe -m venv venv_new && venv_new\Scripts\activate && pip install -r requirements.txt && python manage.py makemigrations contable && python manage.py migrate && python manage.py init_plans && python manage.py runserver
```

---

## 🔍 Por qué ocurrió esto

El entorno virtual `venv_new` fue creado apuntando a:
```
C:\Users\Daniel Osorio\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.7_qbz5n2kfra8p0
```

Este es un **alias de Windows Store**, no una instalación real de Python. Estos aliases tienen problemas conocidos con procesos hijos y entornos virtuales.

La solución es usar la instalación real de Python 3.13 en `C:\Python313\`.
