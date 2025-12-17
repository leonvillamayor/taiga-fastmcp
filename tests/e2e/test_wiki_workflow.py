"""
Test E2E 4.8.4: Flujo de wiki y documentación.

Valida el ciclo completo de gestión de documentación wiki en Taiga:
crear páginas → enlazar → organizar

Criterios de aceptación:
- Datos de prueba aislados
- Limpieza automática
- Ejecución < 60 segundos
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from .conftest import E2ECleanupManager, E2ETestConfig, StatefulTaigaMock


@pytest.mark.e2e
@pytest.mark.asyncio
class TestWikiWorkflowE2E:
    """Tests E2E para el flujo completo de gestión de wiki."""

    async def test_complete_wiki_lifecycle(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test del ciclo de vida completo de wiki.

        Flujo:
        1. Crear proyecto con wiki habilitada
        2. Crear página principal (Home)
        3. Crear páginas secundarias
        4. Actualizar contenido
        5. Verificar estructura
        6. Eliminar páginas
        """
        # === FASE 1: Crear proyecto con wiki ===
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}Wiki_Lifecycle",
            description="Proyecto para test de ciclo de wiki",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register(
            "projects",
            project_id,
            lambda: e2e_taiga_client.delete_project(project_id),
        )

        # === FASE 2: Crear página principal (Home) ===
        home_page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="home",
            content="""# Bienvenido al Proyecto

Este es el proyecto de prueba E2E.

## Contenido

- [Guía de Instalación](/wiki/instalacion)
- [Configuración](/wiki/configuracion)
- [API Reference](/wiki/api)
""",
        )

        assert home_page["id"] is not None
        assert home_page["slug"] == "home"
        assert "Bienvenido" in home_page["content"]
        assert home_page["project"] == project_id

        # === FASE 3: Crear páginas secundarias ===
        # Página de instalación
        install_page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="instalacion",
            content="""# Guía de Instalación

## Requisitos

- Python 3.11+
- uv

## Pasos

1. Clonar repositorio
2. Instalar dependencias
3. Configurar variables de entorno
""",
        )
        assert install_page["slug"] == "instalacion"

        # Página de configuración
        config_page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="configuracion",
            content="""# Configuración

## Variables de Entorno

- `TAIGA_URL`: URL del servidor
- `TAIGA_USERNAME`: Usuario
- `TAIGA_PASSWORD`: Contraseña
""",
        )
        assert config_page["slug"] == "configuracion"

        # Página de API
        api_page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="api",
            content="""# API Reference

## Endpoints

### Proyectos
- `GET /projects` - Listar proyectos
- `POST /projects` - Crear proyecto

### Issues
- `GET /issues` - Listar issues
- `POST /issues` - Crear issue
""",
        )
        assert api_page["slug"] == "api"

        # === FASE 4: Actualizar contenido ===
        updated_home = await e2e_taiga_client.update_wiki_page(
            home_page["id"],
            content="""# Bienvenido al Proyecto (Actualizado)

Este es el proyecto de prueba E2E con documentación actualizada.

## Contenido

- [Guía de Instalación](/wiki/instalacion)
- [Configuración](/wiki/configuracion)
- [API Reference](/wiki/api)
- [FAQ](/wiki/faq) (Nueva sección)
""",
        )
        assert "Actualizado" in updated_home["content"]
        assert updated_home["version"] > home_page["version"]

        # === FASE 5: Verificar estructura ===
        all_pages = await e2e_taiga_client.list_wiki_pages(project_id=project_id)
        slugs = [p["slug"] for p in all_pages]

        assert "home" in slugs
        assert "instalacion" in slugs
        assert "configuracion" in slugs
        assert "api" in slugs

        # Verificar obtención por slug
        retrieved_home = await e2e_taiga_client.get_wiki_page_by_slug(project_id, "home")
        assert retrieved_home["id"] == home_page["id"]

        # === FASE 6: Eliminar página ===
        await e2e_taiga_client.delete_wiki_page(api_page["id"])

        remaining_pages = await e2e_taiga_client.list_wiki_pages(project_id=project_id)
        remaining_slugs = [p["slug"] for p in remaining_pages]
        assert "api" not in remaining_slugs

    async def test_wiki_content_versioning(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de versionado de contenido wiki.

        Valida que las actualizaciones incrementan la versión.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiVersions",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear página
        page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="versioned-page",
            content="Versión 1 del contenido",
        )

        initial_version = page["version"]

        # Actualización 1
        updated1 = await e2e_taiga_client.update_wiki_page(
            page["id"],
            content="Versión 2 del contenido",
        )
        assert updated1["version"] > initial_version

        # Actualización 2
        updated2 = await e2e_taiga_client.update_wiki_page(
            page["id"],
            content="Versión 3 del contenido",
        )
        assert updated2["version"] > updated1["version"]

        # Actualización 3
        updated3 = await e2e_taiga_client.update_wiki_page(
            page["id"],
            content="Versión 4 del contenido con más detalles",
        )
        assert updated3["version"] > updated2["version"]

    async def test_wiki_multiple_pages_structure(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de estructura de múltiples páginas wiki.

        Crea una estructura jerárquica de documentación.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiStructure",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Estructura jerárquica de documentación
        wiki_structure = [
            ("home", "# Inicio\n\nBienvenido"),
            ("getting-started", "# Empezando\n\nGuía rápida"),
            ("getting-started-install", "# Instalación\n\nPasos de instalación"),
            ("getting-started-config", "# Configuración\n\nOpciones de config"),
            ("api", "# API\n\nReferencia de API"),
            ("api-auth", "# Autenticación\n\nCómo autenticar"),
            ("api-projects", "# Proyectos\n\nEndpoints de proyectos"),
            ("contributing", "# Contribuir\n\nCómo contribuir"),
        ]

        created_pages: list[dict[str, Any]] = []
        for slug, content in wiki_structure:
            page = await e2e_taiga_client.create_wiki_page(
                project_id=project_id,
                slug=slug,
                content=content,
            )
            created_pages.append(page)

        assert len(created_pages) == 8

        # Verificar listado completo
        all_pages = await e2e_taiga_client.list_wiki_pages(project_id=project_id)
        assert len(all_pages) >= 8

        # Verificar que todos los slugs están presentes
        slugs = {p["slug"] for p in all_pages}
        for expected_slug, _ in wiki_structure:
            assert expected_slug in slugs


@pytest.mark.e2e
@pytest.mark.asyncio
class TestWikiAdvancedFeaturesE2E:
    """Tests E2E de características avanzadas de wiki."""

    async def test_wiki_search_by_slug(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de búsqueda de páginas por slug.

        Valida la obtención de páginas específicas.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiSearch",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear varias páginas
        await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="page-alpha",
            content="Contenido Alpha",
        )

        page_beta = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="page-beta",
            content="Contenido Beta",
        )

        await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="page-gamma",
            content="Contenido Gamma",
        )

        # Buscar página específica por slug
        found_page = await e2e_taiga_client.get_wiki_page_by_slug(project_id, "page-beta")

        assert found_page["id"] == page_beta["id"]
        assert found_page["slug"] == "page-beta"
        assert found_page["content"] == "Contenido Beta"

    async def test_wiki_page_updates_preserve_metadata(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test que las actualizaciones preservan metadatos.

        Verifica que owner y created_date no cambian.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiMetadata",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear página
        original_page = await e2e_taiga_client.create_wiki_page(
            project_id=project_id,
            slug="metadata-test",
            content="Contenido original",
        )

        original_created = original_page["created_date"]
        original_owner = original_page["owner"]

        # Actualizar varias veces
        for i in range(3):
            await e2e_taiga_client.update_wiki_page(
                original_page["id"],
                content=f"Contenido actualizado #{i + 1}",
            )

        # Obtener página actualizada
        updated_page = await e2e_taiga_client.get_wiki_page(original_page["id"])

        # Verificar que metadatos originales se preservan
        assert updated_page["created_date"] == original_created
        assert updated_page["owner"] == original_owner

        # Pero modified_date debería cambiar
        assert updated_page["modified_date"] is not None

    async def test_wiki_cascade_delete_with_project(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de eliminación en cascada al eliminar proyecto.

        Verifica que las páginas wiki se eliminan con el proyecto.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiCascade",
            is_wiki_activated=True,
        )
        project_id = project["id"]

        # Crear varias páginas
        page_ids: list[int] = []
        for i in range(5):
            page = await e2e_taiga_client.create_wiki_page(
                project_id=project_id,
                slug=f"cascade-page-{i}",
                content=f"Contenido de página {i}",
            )
            page_ids.append(page["id"])

        # Verificar que las páginas existen
        pages_before = await e2e_taiga_client.list_wiki_pages(project_id=project_id)
        assert len(pages_before) >= 5

        # Eliminar proyecto
        await e2e_taiga_client.delete_project(project_id)

        # Verificar que las páginas fueron eliminadas
        pages_after = await e2e_taiga_client.list_wiki_pages(project_id=project_id)
        assert len(pages_after) == 0

    async def test_wiki_slug_uniqueness(
        self,
        e2e_taiga_client: MagicMock,
        stateful_mock: StatefulTaigaMock,
        e2e_cleanup: E2ECleanupManager,
        e2e_config: E2ETestConfig,
    ) -> None:
        """
        Test de unicidad de slugs dentro del proyecto.

        Crea páginas con slugs únicos y verifica identificación.
        """
        # Setup
        project = await e2e_taiga_client.create_project(
            name=f"{e2e_config.project_prefix}WikiSlugs",
            is_wiki_activated=True,
        )
        project_id = project["id"]
        e2e_cleanup.register("projects", project_id)

        # Crear páginas con slugs diferentes
        slugs_to_create = [
            "page-one",
            "page-two",
            "special-chars-test",
            "numbers-123",
            "readme",
        ]

        for slug in slugs_to_create:
            await e2e_taiga_client.create_wiki_page(
                project_id=project_id,
                slug=slug,
                content=f"Contenido para {slug}",
            )

        # Verificar que cada slug es único y accesible
        for slug in slugs_to_create:
            page = await e2e_taiga_client.get_wiki_page_by_slug(project_id, slug)
            assert page["slug"] == slug
