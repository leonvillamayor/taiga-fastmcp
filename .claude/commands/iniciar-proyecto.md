---
description: "Inicializa un nuevo proyecto Python con uv siguiendo estructura DDD"
allowed-tools:
  - Bash
  - Write
  - Read
---

# Iniciar Proyecto Python con DDD

Crea la estructura inicial del proyecto:

## Paso 1: Crear proyecto con uv

!uv init $1
!cd $1

## Paso 2: Crear estructura de directorios DDD

!mkdir -p src/domain/{entities,value_objects,aggregates,domain_services,repositories,events,exceptions}
!mkdir -p src/application/{use_cases,commands,queries,dtos}
!mkdir -p src/infrastructure/{persistence/{orm,repositories},adapters/{api,cli},config}
!mkdir -p src/shared/{exceptions,utils}
!mkdir -p tests/{unit/{domain,application,infrastructure},integration,functional,fixtures}
!mkdir -p Documentacion
!mkdir -p scripts
!mkdir -p docs

## Paso 3: Crear archivos __init__.py

!find src tests -type d -exec touch {}/__init__.py \;

## Paso 4: Agregar dependencias de testing

!uv add --dev pytest pytest-cov pytest-mock pytest-asyncio

El proyecto $1 está listo. Estructura DDD creada ✅
