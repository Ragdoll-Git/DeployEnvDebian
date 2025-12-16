# AI Journal & Context

## 1. Necesidades del Usuario y Prioridades (ALTA PRIORIDAD)

*Esta sección es la fuente de verdad sobre lo que el usuario quiere y necesita.*

- **Propósito del Proyecto:** El nombre del proyectro se llama BrainBash. Es un entorno personalizado de desarrollo en la terminal de Linux, con integracion en la terminal de IA local y un respaldo en la nube (Gemini).
- **Necesidades Explícitas/Deducidas:**
  - [x] Contexto Compartido (`context.md`) para IAs (Gemini, Ollama).
  - [x] Modelos Específicos: Qwen 3 (qwen3:0.6b), Gemma 3 (gemma3:1b), Phi 4 Mini (phi4-mini:latest).
  - [x] Robustez en entornos sin SUDO (Docker) y sin TUI gráfica (whiptail).
  - [x] Instalación resiliente (retry/catch en descargas).
  - [x] Configuración interactiva de API Keys.
- **Limitaciones del Agente:**
  - [x] Los modelos de IA local no deben modificarse -> Respetado.
  - [x] Acceso restringido a `.ai/` -> Respetado.
  - [NEW] El archivo `config/zshrc` es sagrado y no debe contener secretos. Usar `~/.brainbash_secrets`.

- **Objetivos Secundarios:**
  - [x] Mantener limpieza.

## 2. Documentacion general

Link a repositorio de github del proyecto:
<https://github.com/Ragdoll-Git/BrainBash>

## 3. Estado del Proyecto

- **Fecha: 2025-12-16 (Sesión Actual - Fin)**
  - **Estado**: Funcional y Robusto.
  - **Cambios Principales**:
    - **Persistencia Docker**: Volumen `ollama_data` agregado.
    - **Estabilidad Ollama**: Script de instalación local (`src/scripts/install_ollama.sh`) descargando de GitHub Releases.
    - **Aislamiento de Secretos**: API Keys movidas a `~/.brainbash_secrets`.
    - **UX**: Fix warnings de Pip y Starship timeout.
    - **Fixes**: Corrección de sintaxis en Modelfile y main.py.

## 4. Decisiones Técnicas

- **[Decisión]:** Empaquetar `install_ollama.sh` localmente para evitar errores 404/timeout de `ollama.com`.
- **[Decisión]:** Usar `GitHub Releases` como fuente de binarios de Ollama por mayor estabilidad.
- **[Decisión]:** Separar secretos en `.brainbash_secrets` (sourced por zshrc) para evitar contaminar el historial de git con API Keys personales.
- **[Decisión]:** Actualizar `pip` dentro del venv de Gemini para silenciar warnings molestos.

## 5. Próximos Pasos

- [ ] Refinar detección de SO (DNF, Pacman/Alpine) - Quedó pendiente de validación profunda.
- [ ] Probar instalación en un entorno "limpio" real (no Docker) para validar paths absolutos si los hubiera.

## 6. FAQ / Preguntas para el Usuario

(Sin preguntas pendientes)
