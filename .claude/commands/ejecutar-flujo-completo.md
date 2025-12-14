---
description: "Ejecuta el flujo completo TDD/DDD desde caso de negocio hasta aplicación lista"
---

# Flujo Completo TDD/DDD - Ejecución Secuencial

## Objetivo

Ejecutar el flujo completo de desarrollo TDD/DDD invocando secuencialmente a los tres expertos:
1. **Experto TDD**: Analiza caso de negocio y genera tests en rojo
2. **Experto DDD**: Implementa código DDD para poner tests en verde
3. **Experto Documentación**: Genera documentación completa

## Prerequisito CRÍTICO

ANTES de comenzar, verifica que existe el archivo [Documentacion/caso_negocio.txt](Documentacion/caso_negocio.txt).

Si NO existe, DETENTE e informa al usuario:
```
❌ ERROR: No se encontró Documentacion/caso_negocio.txt

Para ejecutar el flujo completo, primero debes crear este archivo con:
- Descripción del proyecto
- Requerimientos funcionales
- Requerimientos no funcionales
- Reglas de negocio
- Casos de uso esperados

Ejemplo de ubicación: Documentacion/caso_negocio.txt
```

Si SÍ existe, continúa con la ejecución.

## Ejecución del Flujo

### FASE 1: Experto TDD

**IMPORTANTE**: Invoca al Experto TDD. Claude delegará automáticamente usando el Task tool.

**Invocación**:
Solicita al usuario o invoca directamente al agente `experto-tdd` con el siguiente prompt:

"Lee el archivo Documentacion/caso_negocio.txt de forma exhaustiva y minuciosa. Realiza TODOS los pasos de tu flujo de trabajo:
1) Análisis punto por punto con convergencias,
2) Investigación REAL con context7, sobre las bibliotecas a utilizar (NO simules),
3) Creación REAL de archivos de tests usando Write tool,
4) Verificacion REAL de que los archivos de tests cubren el 100% de lo especificado en Documentacion/caso_negocio.txt.
5) Verificación de cobertura. Los tests deben estar en ROJO."

El Experto TDD DEBE ejecutar REALMENTE:
- Lectura exhaustiva del caso de negocio con Read tool
- Invocación REAL de context7 (mcp__context7__resolve-library-id y get-library-docs)
- Creación REAL de archivos de tests con Write tool
- Verificacion REAL de que los archivos de test cubren el 100% de lo especificado en Documentacion/caso_negocio.txt
- Ejecución de tests con Bash tool
- Verificacion que los test cubren el 100% del caso de negocio.
- Los test unitarios pueden utilizar mocks pero los de integracion usaran credenciales reales
- Documentación del análisis con Write tool

**VERIFICACIÓN**: Si el agente solo muestra código sin crear archivos, DETENTE y reporta el problema.

Espera a que el Experto TDD complete su trabajo antes de continuar.

---

### FASE 2: Experto DDD

Una vez que el Experto TDD haya terminado, invoca al **Experto DDD**.

**Invocación**:
Invoca al agente `experto-ddd` con el siguiente prompt:

"Los tests ya están creados en rojo. Realiza TODOS los pasos de tu flujo de trabajo:
1) Lee los tests existentes con Read, uno a uno,
2) Investigación REAL con context7 (NO simules), sobre las bibliotecas que piensas utilizar
3) Implementación REAL de código usando Write tool para crear archivos en src/, garantizando que el codigo realiza lo necesario para poner cada test en rojo, asegurandote de ello antes de comenzar con el siguiente test
4) Ejecución de tests con Bash hasta que TODOS estén en verde,
5) Verificación de cobertura 100%. NO modifiques los tests bajo ninguna circunstancia."

El Experto DDD DEBE ejecutar REALMENTE:
- Lectura de tests con Read tool, uno a uno
- Invocación REAL de context7 para librerías de implementación
- Creación REAL de archivos de código con Write tool, cubriendo uno a uno lo necesario para que los test pasen a verde
- No se usaran mocks en los ficheros de codigo
- Ejecución test por test con Bash tool
- Verificación de cobertura con Bash tool
- Si algun test continua en rojo, continuar hasta que este en verde.

**IMPORTANTE**: El Experto DDD **NUNCA modificará los tests**.

**VERIFICACIÓN**: Si el agente solo muestra código sin crear archivos, DETENTE y reporta el problema.

Espera a que el Experto DDD complete su trabajo antes de continuar.

---

### FASE 3: Experto Documentación

Una vez que TODOS los tests estén en VERDE, invoca al **Experto Documentación**.

**Invocación**:
Invoca al agente `experto-documentacion` con el siguiente prompt:

"Todos los tests están en verde. Realiza TODOS los pasos de tu flujo de trabajo: 1) Verificación previa con Bash (pytest), 2) Análisis del proyecto con Read, 3) Creación REAL de README.md con Write tool incluyendo sección de toma de decisiones y por qué, 4) Creación REAL de guia_uso.md exhaustiva con Write tool. USA Write tool para crear los archivos, NO solo muestres el contenido."

El Experto Documentación DEBE ejecutar REALMENTE:
- Verificación de tests en verde con Bash tool
- Lectura de archivos del proyecto con Read tool
- Creación REAL de README.md con Write tool
- Creación REAL de guia_uso.md con Write tool

**VERIFICACIÓN**: Si el agente solo muestra documentación sin crear archivos, DETENTE y reporta el problema.

---

## Resumen Final

Después de que los 3 expertos hayan terminado, presenta un resumen:

```
🎉 FLUJO COMPLETO TDD/DDD COMPLETADO

✅ FASE 1 - Análisis y Tests (Experto TDD)
   - Requerimientos identificados: [número]
   - Tests creados: [número]
   - Tests en ROJO: ✓

✅ FASE 2 - Implementación DDD (Experto DDD)
   - Tests en VERDE: [número/número]
   - Cobertura: [XX%]
   - Capas implementadas: Domain, Application, Infrastructure

✅ FASE 3 - Documentación (Experto Documentación)
   - README.md: ✓
   - guia_uso.md: ✓
   - Diagramas de arquitectura: ✓

🚀 LA APLICACIÓN ESTÁ LISTA PARA USAR
```

---

## Notas Importantes

**Ejecución Secuencial**: Los agentes se ejecutan UNO DESPUÉS DEL OTRO, NO en paralelo.

**Comunicación entre Agentes**: Los agentes NO se comunican directamente. La información se pasa mediante archivos:
- Experto TDD → escribe en `Documentacion/` y `tests/`
- Experto DDD → lee de `Documentacion/` y `tests/`, escribe en `src/`
- Experto Documentación → lee todo, escribe en raíz y `Documentacion/`

**Gestión con uv**: Todos los agentes usan `uv` para gestión de proyecto y dependencias.

**Investigación con context7**: Los agentes usan el MCP server context7 para obtener documentación actualizada de librerías Python.
