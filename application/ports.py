"""Puertos (interfaces) que la capa de Aplicación necesita del exterior.

La Infraestructura IMPLEMENTA estas interfaces (Inversión de Dependencias).
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.envio import Envio


class EnvioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id_envio: UUID) -> Optional[Envio]:
        """Devuelve el envío o None si no existe."""

    @abstractmethod
    def guardar(self, envio: Envio) -> None:
        """Inserta o actualiza el envío. (No existe borrado físico.)"""
