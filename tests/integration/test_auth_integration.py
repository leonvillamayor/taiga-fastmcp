"""
Tests de integración para autenticación con Taiga API real.
Usa credenciales del archivo .env para verificar funcionamiento real.
"""

import os

import httpx
import pytest
from dotenv import load_dotenv


# Cargar variables de entorno
load_dotenv()


class TestTaigaAuthenticationIntegration:
    """Tests de integración para autenticación real con Taiga - RF-042, RF-043."""

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_real_authentication_with_taiga_api(self) -> None:
        """
        RF-042: Los tests DEBEN usar credenciales reales del .env.
        RF-043: Los tests DEBEN verificar conexión real con Taiga.
        Verifica autenticación real con las credenciales del .env.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")
        username = os.getenv("TAIGA_USERNAME")
        password = os.getenv("TAIGA_PASSWORD")

        # Skip si no hay credenciales
        if not all([api_url, username, password]):
            pytest.skip("Credenciales de Taiga no configuradas en .env")

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal", "username": username, "password": password},
                timeout=30.0,
            )

        # Assert - Handle rate limiting
        if response.status_code == 429:
            # Mock response when rate limited
            pytest.skip("Rate limited by Taiga API, skipping real test")

        assert response.status_code == 200, f"Authentication failed: {response.text}"

        data = response.json()
        assert "auth_token" in data
        assert "refresh" in data
        assert "id" in data
        assert "username" in data
        assert "email" in data

        # Guardar token para otros tests
        pytest.auth_token = data["auth_token"]
        pytest.refresh_token = data["refresh"]
        pytest.user_id = data["id"]

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_refresh_token_with_real_api(self) -> None:
        """
        Verifica que el refresh token funciona con la API real.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")

        # Primero autenticarse para obtener tokens
        username = os.getenv("TAIGA_USERNAME")
        password = os.getenv("TAIGA_PASSWORD")

        if not all([api_url, username, password]):
            pytest.skip("Credenciales de Taiga no configuradas en .env")

        # Obtener tokens iniciales
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal", "username": username, "password": password},
            )

            # Handle rate limiting
            if auth_response.status_code == 429:
                pytest.skip("Rate limited by Taiga API, skipping real test")

            auth_data = auth_response.json()
            refresh_token = auth_data.get("refresh")

            if not refresh_token:
                pytest.skip("No refresh token received")

            # Act - Refresh token
            refresh_response = await client.post(
                f"{api_url}/auth/refresh", json={"refresh": refresh_token}
            )

        # Assert
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "auth_token" in refresh_data
        assert "refresh" in refresh_data
        # Los nuevos tokens deben ser diferentes
        assert refresh_data["auth_token"] != auth_data["auth_token"]

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_current_user_with_real_api(self) -> None:
        """
        Verifica que podemos obtener información del usuario actual.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")
        username = os.getenv("TAIGA_USERNAME")
        password = os.getenv("TAIGA_PASSWORD")

        if not all([api_url, username, password]):
            pytest.skip("Credenciales de Taiga no configuradas en .env")

        # Autenticarse primero
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal", "username": username, "password": password},
            )

            # Handle rate limiting
            if auth_response.status_code == 429:
                pytest.skip("Rate limited by Taiga API, skipping real test")

            auth_data = auth_response.json()
            auth_token = auth_data.get("auth_token")

            if not auth_token:
                pytest.skip("No auth token received")

            # Act - Get current user
            user_response = await client.get(
                f"{api_url}/users/me", headers={"Authorization": f"Bearer {auth_token}"}
            )

        # Assert
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert "id" in user_data
        assert "username" in user_data
        assert "email" in user_data
        assert user_data["email"] == username  # Username es el email

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_invalid_credentials_real_api(self) -> None:
        """
        RF-045: Los tests DEBEN manejar casos de error reales.
        Verifica que la API rechaza credenciales inválidas.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")

        if not api_url:
            pytest.skip("TAIGA_API_URL no configurada en .env")

        # Act
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_url}/auth",
                json={
                    "type": "normal",
                    "username": "invalid@notexist.com",
                    "password": "wrongpassword123",
                },
            )

        # Assert
        # Handle rate limiting
        if response.status_code == 429:
            pytest.skip("Rate limited by Taiga API, skipping real test")

        assert response.status_code in [400, 401, 403]
        # La API debe rechazar las credenciales inválidas

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_expired_token_real_api(self) -> None:
        """
        Verifica que la API rechaza tokens expirados/inválidos.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")

        if not api_url:
            pytest.skip("TAIGA_API_URL no configurada en .env")

        # Act - Usar token inválido
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_url}/users/me", headers={"Authorization": "Bearer invalid_token_12345"}
            )

        # Assert
        assert response.status_code == 401
        # La API debe rechazar el token inválido

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self) -> None:
        """
        RF-034: El servidor DEBE manejar rate limiting de Taiga.
        Verifica el comportamiento con múltiples requests.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")
        username = os.getenv("TAIGA_USERNAME")
        password = os.getenv("TAIGA_PASSWORD")

        if not all([api_url, username, password]):
            pytest.skip("Credenciales de Taiga no configuradas en .env")

        # Act - Hacer múltiples requests rápidos
        async with httpx.AsyncClient() as client:
            # Autenticarse una vez
            auth_response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal", "username": username, "password": password},
            )

            # Handle rate limiting
            if auth_response.status_code == 429:
                pytest.skip("Rate limited by Taiga API, skipping real test")

            auth_data = auth_response.json()
            auth_token = auth_data.get("auth_token")

            if not auth_token:
                pytest.skip("No auth token received")

            # Hacer 10 requests rápidos
            responses = []
            for _ in range(10):
                response = await client.get(
                    f"{api_url}/users/me", headers={"Authorization": f"Bearer {auth_token}"}
                )
                responses.append(response)

        # Assert
        # Verificar que al menos algunos requests fueron exitosos
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0, "Ningún request fue exitoso"

        # Si hay rate limiting, verificar headers
        for response in responses:
            if response.status_code == 429:
                assert (
                    "X-Throttle-Remaining" in response.headers or "Retry-After" in response.headers
                )

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_token_persistence_across_requests(self) -> None:
        """
        Verifica que el token se puede usar en múltiples requests.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")
        username = os.getenv("TAIGA_USERNAME")
        password = os.getenv("TAIGA_PASSWORD")

        if not all([api_url, username, password]):
            pytest.skip("Credenciales de Taiga no configuradas en .env")

        # Act
        async with httpx.AsyncClient() as client:
            # Autenticarse
            auth_response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal", "username": username, "password": password},
            )

            # Handle rate limiting
            if auth_response.status_code == 429:
                pytest.skip("Rate limited by Taiga API, skipping real test")

            auth_data = auth_response.json()
            auth_token = auth_data.get("auth_token")

            if not auth_token:
                pytest.skip("No auth token received")

            # Usar el token en múltiples endpoints
            headers = {"Authorization": f"Bearer {auth_token}"}

            # Request 1: Get user
            user_response = await client.get(f"{api_url}/users/me", headers=headers)

            # Request 2: Get projects
            projects_response = await client.get(f"{api_url}/projects", headers=headers)

        # Assert
        assert user_response.status_code == 200
        assert projects_response.status_code == 200
        # El mismo token funciona para múltiples endpoints


class TestAuthenticationErrorHandling:
    """Tests de manejo de errores de autenticación."""

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self) -> None:
        """
        Verifica el manejo de timeouts de red.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")

        if not api_url:
            pytest.skip("TAIGA_API_URL no configurada en .env")

        # Act - Request con timeout muy corto
        async with httpx.AsyncClient(timeout=0.001) as client:
            try:
                await client.post(
                    f"{api_url}/auth",
                    json={"type": "normal", "username": "test", "password": "test"},
                )
                pytest.fail("Should have timed out")
            except httpx.TimeoutException:
                # Assert - Expected behavior
                pass

    @pytest.mark.integration
    @pytest.mark.taiga
    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_malformed_request_handling(self) -> None:
        """
        Verifica el manejo de requests malformados.
        """
        # Arrange
        api_url = os.getenv("TAIGA_API_URL")

        if not api_url:
            pytest.skip("TAIGA_API_URL no configurada en .env")

        # Act - Request sin campo requerido
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_url}/auth",
                json={"type": "normal"},  # Falta username y password
            )

        # Assert
        # Handle rate limiting
        if response.status_code == 429:
            pytest.skip("Rate limited by Taiga API, skipping real test")

        assert response.status_code in [400, 422]
        # La API debe rechazar el request malformado
