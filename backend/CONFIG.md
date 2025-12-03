# CATIE PARES - Configuración Backend

## 🔐 Configuración de API Key (OpenAI)

### ✅ RECOMENDADO: Usar archivo .env

Esta es la forma **más segura y profesional** para desarrollo y deployment:

#### Paso 1: Crear archivo .env

```bash
cd backend
cp .env.example .env
```

#### Paso 2: Editar .env con tu clave

Abrir `backend/.env` y reemplazar con tu clave real:

```env
OPENAI_API_KEY=sk-tu-clave-real-aqui
```

#### Paso 3: Iniciar el servidor

```bash
python run.py
```

### ✅ Ventajas del archivo .env

1. ✅ **Persistente** - No se pierde al cerrar la terminal
2. ✅ **Seguro** - Está en `.gitignore` (no se sube a GitHub)
3. ✅ **Fácil** - No hay que escribir la clave cada vez
4. ✅ **Estándar** - Es la práctica recomendada en la industria
5. ✅ **Multi-entorno** - Puedes tener `.env.local`, `.env.production`, etc.

---

### 🚀 Para Deployment en Producción

**NO uses archivo .env en producción**. En su lugar, configura las variables de entorno en tu plataforma:

#### Heroku
```bash
heroku config:set OPENAI_API_KEY=sk-...
```

#### Vercel
```bash
vercel env add OPENAI_API_KEY
```

#### Railway
```bash
# En el dashboard: Settings → Variables → Add Variable
OPENAI_API_KEY=sk-...
```

#### Render
```bash
# En el dashboard: Environment → Add Environment Variable
OPENAI_API_KEY=sk-...
```

#### Docker
```bash
docker run -e OPENAI_API_KEY=sk-... your-image
```

#### AWS/Azure/GCP
Usar sus respectivos servicios de secrets management:
- AWS: Secrets Manager
- Azure: Key Vault
- GCP: Secret Manager

---

### ⚡ Opción Rápida (Solo para testing local)

**NO recomendado para deployment**. Solo para pruebas rápidas:

```powershell
# PowerShell
$env:OPENAI_API_KEY="sk-..."
python run.py

# CMD
set OPENAI_API_KEY=sk-...
python run.py

# Linux/Mac
export OPENAI_API_KEY="sk-..."
python run.py
```

**Desventajas:**
- ❌ Temporal (se pierde al cerrar terminal)
- ❌ Puede quedar en historial de comandos
- ❌ Tienes que repetirlo cada vez
- ❌ No funciona en servicios de deployment

---

## 🔑 Obtener tu OpenAI API Key

1. **Ir a** [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Iniciar sesión** con tu cuenta
3. **Click en** "Create new secret key"
4. **Darle un nombre** (ej: "CATIE-PARES-Backend")
5. **Copiar la clave** (empieza con `sk-proj-...`)
6. **Pegarla en** tu archivo `.env`

---

## 📊 Modelo y Costos

- **Modelo**: `gpt-4o-mini`
- **Input**: ~$0.15 por millón de tokens
- **Output**: ~$0.60 por millón de tokens
- **Costo por consulta**: ~$0.001 - $0.002 USD
- **Temperatura**: 0.3 (consistente pero natural)

---

## 🔒 Seguridad - IMPORTANTE

### ✅ Hacer Siempre:
- ✅ Usar archivo `.env` para desarrollo
- ✅ Agregar `.env` al `.gitignore`
- ✅ Usar variables de entorno del servidor en producción
- ✅ Rotar claves periódicamente
- ✅ Monitorear uso en [OpenAI Dashboard](https://platform.openai.com/usage)

### ❌ NUNCA Hacer:
- ❌ Subir `.env` a GitHub
- ❌ Hardcodear la clave en el código
- ❌ Compartir la clave por email/chat
- ❌ Dejar la clave en el historial de comandos
- ❌ Usar la misma clave en múltiples proyectos públicos

---

## 🧪 Verificar Configuración

Después de configurar:

```bash
# 1. Verificar que .env existe
ls .env

# 2. Verificar que está en .gitignore
cat .gitignore | grep .env

# 3. Iniciar servidor y ver logs
python run.py
```

Si hay error:
- Revisar logs del servidor
- Verificar que la clave sea correcta (`sk-proj-...`)
- Confirmar créditos en OpenAI
- Probar la clave en [OpenAI Playground](https://platform.openai.com/playground)

---

## 📦 Instalación

```bash
cd backend

# Instalar dependencias (incluye python-dotenv)
pip install -r requirements.txt

# Crear .env desde el template
cp .env.example .env

# Editar .env con tu clave real
notepad .env  # o vim/nano/code

# Iniciar servidor
python run.py
```

---

## 🔄 Modo Fallback (Sin API Key)

Si **NO** configuras `OPENAI_API_KEY`:
- ✅ El sistema funciona normalmente
- ✅ Muestra 3 extractos únicos de documentos
- ✅ Elimina duplicados automáticamente
- ⚠️ Sin síntesis por IA (solo extractos crudos)
- ⚠️ La respuesta incluye una nota para configurar la clave

---

## 📁 Estructura de Archivos

```
backend/
├── .env                 # ← Tu clave aquí (NO subir a git)
├── .env.example         # Template (sí subir a git)
├── .gitignore          # Incluye .env
├── main.py             # Lee .env automáticamente
├── requirements.txt    # Incluye python-dotenv
└── CONFIG.md          # Este archivo
```
