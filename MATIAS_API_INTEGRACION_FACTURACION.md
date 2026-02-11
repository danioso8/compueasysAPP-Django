# Documentación Integración Matias API - Facturación Electrónica DIAN

**Fecha:** 11 de Febrero 2026  
**Versión API:** Matias API v3.0.0 UBL 2.1  
**Endpoint Base:** https://api-v2.matias-api.com/api/ubl2.1

---

## 📋 TABLA DE CONTENIDO

1. [Configuración Inicial](#configuración-inicial)
2. [Modelos de Base de Datos](#modelos-de-base-de-datos)
3. [Autenticación OAuth2](#autenticación-oauth2)
4. [Estructura Payload Factura Electrónica](#estructura-payload-factura-electrónica)
5. [Estructura Payload Documento Soporte](#estructura-payload-documento-soporte)
6. [Campos Requeridos por Sección](#campos-requeridos-por-sección)
7. [Respuesta de Matias API](#respuesta-de-matias-api)
8. [Manejo de Estados DIAN](#manejo-de-estados-dian)

---

## 🔧 CONFIGURACIÓN INICIAL

### Variables de Entorno (.env)

```env
# Credenciales OAuth2 (GLOBALES - una cuenta emite facturas para todos los NITs)
MATIAS_EMAIL=demo@lopezsoft.net.co
MATIAS_PASSWORD=DEMO123456

# URL de API (NO CAMBIAR)
MATIAS_API_BASE_URL=https://api-v2.matias-api.com/api/ubl2.1
```

### Tabla: `billing_matias_configuration`

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | INT | Primary Key | 1 |
| `organization_id` | INT | FK a Organization | 2 |
| `test_mode` | BOOLEAN | True=Habilitación, False=Producción | True |
| `resolution_number` | VARCHAR(50) | Número de resolución DIAN | "18760000001" |
| `prefix` | VARCHAR(10) | Prefijo de facturación | "SETP" |
| `type_document_id` | INT | 1=Factura, 7=Doc.Soporte | 1 |
| `default_payment_method_id` | INT | Forma de pago (1=Contado) | 1 |
| `default_means_payment_id` | INT | Medio de pago (10=Efectivo) | 10 |

---

## 💾 MODELOS DE BASE DE DATOS

### Tabla: `billing_invoice` (Factura Electrónica)

```python
# Campos principales
id                      # INT - Primary Key
organization_id         # INT - FK Organization
customer_id            # INT - FK Customer/Patient
consecutive            # INT - Número consecutivo
invoice_number         # VARCHAR - Prefijo + Consecutivo
issue_date             # DATE
issue_time             # TIME
payment_form           # INT - 1=Contado, 2=Crédito
payment_method         # INT - 10=Efectivo, etc.

# Totales
subtotal               # DECIMAL(10,2)
total_discount         # DECIMAL(10,2)
total_tax              # DECIMAL(10,2)
total_other_taxes      # DECIMAL(10,2)
total                  # DECIMAL(10,2)

# DIAN
dian_status           # VARCHAR - pending/processing/approved/rejected/error
cufe                  # VARCHAR - Código Único Factura Electrónica
cude                  # VARCHAR - (alternativo)
qr_code               # TEXT - Data URL de QR
pdf_url               # VARCHAR - URL del PDF
xml_url               # VARCHAR - URL del XML
matias_track_id       # VARCHAR - ID de seguimiento Matias
dian_response         # JSON - Respuesta completa de Matias API

# Metadata
items                 # JSON - Array de productos/servicios
created_at            # TIMESTAMP
updated_at            # TIMESTAMP
```

### Tabla: `billing_support_document` (Documento Soporte)

```python
# Igual estructura que billing_invoice PERO:
- Usa CUDS en lugar de CUFE
- Campo adicional: tipo_operacion (22 = Documento soporte)
- Campos de vendedor (persona natural):
  vendedor_tipo_documento
  vendedor_numero_documento
  vendedor_primer_nombre
  vendedor_segundo_nombre
  vendedor_primer_apellido
  vendedor_segundo_apellido
  vendedor_razon_social
  vendedor_direccion
  vendedor_municipio_codigo
  vendedor_municipio_nombre
  vendedor_departamento
  vendedor_telefono
  vendedor_email
```

### Campo JSON: `items` (Productos/Servicios)

```json
[
  {
    "codigo": "001",
    "descripcion": "Producto ejemplo",
    "cantidad": 2.0,
    "precio_unitario": 50000.0,
    "subtotal": 100000.0,
    "descuento": 0.0,
    "iva_porcentaje": 19.0,
    "iva_valor": 19000.0,
    "otros_impuestos": 0.0,
    "total": 119000.0
  }
]
```

---

## 🔐 AUTENTICACIÓN OAUTH2

### Endpoint de Autenticación

```
POST https://api-v2.matias-api.com/oauth/token
Content-Type: application/json

{
  "grant_type": "password",
  "client_id": 2,
  "client_secret": "lYflu65FMrsZG3p4tLtSIZKTLrDt66KKZ1LilNdK",
  "username": "demo@lopezsoft.net.co",
  "password": "DEMO123456",
  "scope": "*"
}
```

### Respuesta de Token

```json
{
  "token_type": "Bearer",
  "expires_in": 31536000,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "def5020..."
}
```

### Usar Token en Requests

```
Authorization: Bearer {access_token}
Accept: application/json
Content-Type: application/json
```

---

## 📤 ESTRUCTURA PAYLOAD FACTURA ELECTRÓNICA

### Endpoint

```
POST /ubl2.1/invoice
```

### Payload Completo

```json
{
  "type_document_id": 1,
  "number": 100023,
  "sync": true,
  "date": "2026-02-11",
  "time": "14:30:00",
  
  "resolution_number": "9234567890",
  "prefix": "SETP",
  "resolution_date": "2019-01-19",
  "technical_key": "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c",
  "from_number": 1,
  "to_number": 5000000,
  
  "payment_method_id": 1,
  "means_payment_id": 10,
  
  "customer": {
    "identification_number": "900123456",
    "type_document_identification_id": 6,
    "type_organization_id": 2,
    "name": "CLIENTE EJEMPLO S.A.S.",
    "phone": "3001234567",
    "address": "Calle 123 #45-67",
    "email": "cliente@ejemplo.com",
    "merchant_registration": "900123456-1",
    "municipality_id": 149,
    "type_regime_id": 49,
    "type_liability_id": 117,
    "organization_id": 1
  },
  
  "lines": [
    {
      "invoiced_quantity": 2.0,
      "line_extension_amount": 100000.0,
      "free_of_charge_indicator": false,
      "description": "Producto ejemplo",
      "code": "001",
      "type_item_identifications_id": 4,
      "price_amount": 50000.0,
      "base_quantity": 2.0,
      "quantity_units_id": 642,
      "tax_totals": [
        {
          "tax_id": 1,
          "tax_amount": 19000.0,
          "taxable_amount": 100000.0,
          "percent": 19.0
        }
      ]
    }
  ],
  
  "legal_monetary_totals": {
    "line_extension_amount": 100000.0,
    "tax_exclusive_amount": 100000.0,
    "tax_inclusive_amount": 119000.0,
    "allowance_total_amount": 0.0,
    "payable_amount": 119000.0
  },
  
  "payments": [
    {
      "payment_form_id": 1,
      "payment_method_id": 1,
      "means_payment_id": 10,
      "value_paid": 119000.0
    }
  ],
  
  "Ambiente": "2"
}
```

---

## 📋 CAMPOS REQUERIDOS POR SECCIÓN

### ✅ Documento Principal

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `type_document_id` | INT | ✅ Sí | 1=Factura, 7=Doc.Soporte |
| `number` | INT | ✅ Sí | Consecutivo del documento |
| `sync` | BOOLEAN | ✅ Sí | true (envío sincrónico) |
| `date` | STRING | ✅ Sí | Formato: YYYY-MM-DD |
| `time` | STRING | ✅ Sí | Formato: HH:MM:SS |
| `resolution_number` | STRING | ✅ Sí | Número resolución DIAN |
| `prefix` | STRING | ✅ Sí | Prefijo de facturación |
| `resolution_date` | STRING | ✅ Sí | Fecha resolución YYYY-MM-DD |
| `technical_key` | STRING | ✅ Sí | Clave técnica DIAN |
| `from_number` | INT | ✅ Sí | Rango inicial resolución |
| `to_number` | INT | ✅ Sí | Rango final resolución |
| `payment_method_id` | INT | ✅ Sí | ID forma de pago |
| `means_payment_id` | INT | ✅ Sí | ID medio de pago |
| `Ambiente` | STRING | ✅ Sí | "1"=Producción, "2"=Habilitación |

### ✅ Customer (Cliente)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `identification_number` | STRING | ✅ Sí | NIT o CC del cliente |
| `type_document_identification_id` | INT | ✅ Sí | 6=NIT, 13=CC |
| `type_organization_id` | INT | ✅ Sí | 1=Persona Jurídica, 2=Persona Natural |
| `name` | STRING | ✅ Sí | Razón social o nombre completo |
| `phone` | STRING | ✅ Sí | Teléfono de contacto |
| `address` | STRING | ✅ Sí | Dirección completa |
| `email` | STRING | ✅ Sí | Email para envío de documentos |
| `merchant_registration` | STRING | ✅ Sí | Matrícula mercantil (NIT-DV) |
| `municipality_id` | INT | ✅ Sí | Código DANE del municipio |
| `type_regime_id` | INT | ✅ Sí | 49=Simplificado, 48=Común |
| `type_liability_id` | INT | ✅ Sí | 117=No responsable IVA, etc. |
| `organization_id` | INT | ✅ Sí | ID organización emisora |

### ✅ Lines (Productos/Servicios)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `invoiced_quantity` | FLOAT | ✅ Sí | Cantidad facturada |
| `line_extension_amount` | FLOAT | ✅ Sí | Subtotal línea (precio * cantidad) |
| `free_of_charge_indicator` | BOOLEAN | ✅ Sí | false=se cobra, true=gratis |
| `description` | STRING | ✅ Sí | Descripción del producto/servicio |
| `code` | STRING | ✅ Sí | Código del producto |
| `type_item_identifications_id` | INT | ✅ Sí | 4=Estándar (nota: plural) |
| `price_amount` | FLOAT | ✅ Sí | Precio unitario |
| `base_quantity` | FLOAT | ✅ Sí | Cantidad base (igual a invoiced) |
| `quantity_units_id` | INT | ✅ Sí | 642=Unidad (código UBL) |
| `tax_totals` | ARRAY | ⚠️ Condicional | Solo si aplican impuestos |

### ✅ Tax Totals (Impuestos por Línea)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `tax_id` | INT | ✅ Sí | 1=IVA, 4=INC, 5=ICA |
| `tax_amount` | FLOAT | ✅ Sí | Valor del impuesto |
| `taxable_amount` | FLOAT | ✅ Sí | Base gravable |
| `percent` | FLOAT | ✅ Sí | Porcentaje del impuesto |

### ✅ Legal Monetary Totals (Totales DIAN)

| Campo | Tipo | Obligatorio | Descripción | Cálculo |
|-------|------|-------------|-------------|---------|
| `line_extension_amount` | FLOAT | ✅ Sí | Subtotal sin impuestos | Suma de todos los subtotales |
| `tax_exclusive_amount` | FLOAT | ✅ Sí | Subtotal - descuentos | subtotal - descuentos |
| `tax_inclusive_amount` | FLOAT | ✅ Sí | Total con impuestos | Total final |
| `allowance_total_amount` | FLOAT | ✅ Sí | Total descuentos | Suma de descuentos |
| `payable_amount` | FLOAT | ✅ Sí | Total a pagar | Total final |

**IMPORTANTE:** Estos campos deben ser valores numéricos directos (FLOAT), NO objetos con `{amount, currency_id}`.

### ✅ Payments (Formas de Pago)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `payment_form_id` | INT | ✅ Sí | 1=Contado, 2=Crédito |
| `payment_method_id` | INT | ✅ Sí | 1=Efectivo (ID válido en tabla) |
| `means_payment_id` | INT | ✅ Sí | 10=Efectivo (código DIAN) |
| `value_paid` | FLOAT | ✅ Sí | Monto pagado |

---

## 📥 RESPUESTA DE MATIAS API

### Respuesta Exitosa (200 OK)

```json
{
  "IsValid": true,
  "StatusCode": "00",
  "StatusDescription": "Procesado Correctamente",
  "StatusMessage": "Documento procesado correctamente.",
  "cufe": "abc123def456...",
  "trackId": "xyz789...",
  "processedTime": "2026-02-11T14:30:00Z",
  "qrCode": "data:image/png;base64,iVBORw0KGgoAAAANSU...",
  "pdfUrl": "https://api-v2.matias-api.com/documents/12345.pdf",
  "xmlUrl": "https://api-v2.matias-api.com/documents/12345.xml"
}
```

### Respuesta con Errores (422 Unprocessable Entity)

```json
{
  "IsValid": false,
  "StatusCode": "422",
  "StatusMessage": "El campo lines.*.quantity_units_id es requerido (and 2 more errors)",
  "Errors": [
    {
      "Field": "lines.0.quantity_units_id",
      "Message": "El campo lines.*.quantity_units_id es requerido"
    },
    {
      "Field": "payments.0.value_paid",
      "Message": "El campo payments.*.value_paid es requerido"
    }
  ]
}
```

### Códigos de Estado DIAN

| StatusCode | Significado | Estado BD |
|------------|-------------|-----------|
| `00` | Aprobado | `approved` |
| `98` | En procesamiento | `processing` |
| `99` | Rechazado | `rejected` |
| Otros | Error | `error` |

---

## 🔄 MANEJO DE ESTADOS DIAN

### Estados Posibles en BD

```python
DIAN_STATUS_CHOICES = [
    ('pending', 'Pendiente de envío'),
    ('processing', 'En procesamiento DIAN'),
    ('approved', 'Aprobado por DIAN'),
    ('rejected', 'Rechazado por DIAN'),
    ('error', 'Error en envío'),
]
```

### Flujo de Estados

```
pending → processing → approved ✅
pending → processing → rejected ❌
pending → error ❌
```

### Reenvío de Documentos

**Permitir reenviar cuando:**
- `dian_status` = `'pending'`
- `dian_status` = `'rejected'`
- `dian_status` = `'error'`

**NO permitir reenviar cuando:**
- `dian_status` = `'approved'`
- `dian_status` = `'processing'`

---

## 🗂️ ESTRUCTURA DE ARCHIVOS CLAVE

```
apps/billing/
├── models_matias.py              # Modelos Invoice, SupportDocument, MatiasConfiguration
├── services/
│   └── matias_client.py          # Cliente API Matias (autenticación + envío)
├── views_invoice.py              # CRUD facturas electrónicas
├── views_support_document.py     # CRUD documentos soporte
└── templates/billing/
    ├── invoice_list.html
    ├── invoice_detail.html
    ├── support_document_list.html
    └── support_document_detail.html
```

---

## 📌 NOTAS IMPORTANTES

### 1. Multi-Empresa
- **Una sola cuenta Matias** puede emitir facturas para **múltiples NITs**
- La configuración de resolución es **por organización** (tabla `billing_matias_configuration`)
- El campo `customer.organization_id` identifica quién emite el documento

### 2. Inventario
- **OpticaApp NO maneja inventario automáticamente**
- Los productos se envían como JSON en el campo `items`
- Para CompueasysApp: deberás agregar lógica de descuento de stock después de envío exitoso a DIAN

### 3. Ambiente de Pruebas vs Producción
- **Modo prueba:** `Ambiente = "2"` + `test_mode = True` en configuración
- **Modo producción:** `Ambiente = "1"` + `test_mode = False`
- La cuenta demo (`demo@lopezsoft.net.co`) solo funciona en modo prueba

### 4. Diferencias Factura vs Documento Soporte

| Característica | Factura | Documento Soporte |
|---------------|---------|-------------------|
| Endpoint | `/invoice` | `/ds/document` |
| type_document_id | 1 | 7 |
| Código único | CUFE | CUDS |
| Cliente | Persona jurídica/natural | Persona natural NO obligada |
| Campos adicionales | - | Datos completos del vendedor |
| Uso | Venta normal facturada | Compra a persona natural |

### 5. Códigos Útiles

**Unidades de Medida:**
- `642`: Unidad
- `94`: Unidad (alternativo)

**Tipos de Documento Identificación:**
- `6`: NIT
- `13`: Cédula de Ciudadanía
- `22`: Cédula de Extranjería
- `31`: Pasaporte

**Tipos de Organización:**
- `1`: Persona Jurídica
- `2`: Persona Natural

**Regímenes Tributarios:**
- `48`: Responsable IVA - Régimen Común
- `49`: No Responsable IVA - Régimen Simplificado

---

## 🚀 CHECKLIST PARA IMPLEMENTAR EN NUEVA APP

- [ ] Crear modelos: Invoice, MatiasConfiguration
- [ ] Copiar `matias_client.py` (cliente API)
- [ ] Configurar variables de entorno (.env)
- [ ] Crear tabla de configuración en BD
- [ ] Implementar vistas CRUD de facturas
- [ ] Agregar lógica de selección de productos desde tienda
- [ ] Implementar descuento automático de stock
- [ ] Agregar opción "Factura Normal" vs "Factura Electrónica"
- [ ] Crear templates de visualización
- [ ] Probar en modo habilitación (test_mode=True)
- [ ] Configurar resolución real y pasar a producción

---

**Última actualización:** 2026-02-11  
**Autor:** Sistema OpticaApp  
**Contacto Soporte Matias:** https://matias-api.com
