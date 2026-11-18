"""Adaptador de almacenamiento: guarda los envíos en un diccionario en memoria.

Implementa el puerto EnvioRepository. Se reemplazará por una BD real más adelante
sin tocar Dominio ni Aplicación.
"""
from typing import Dict, Optional
from uuid import UUID

from application.ports import EnvioRepository
from domain.envio import Envio


class InMemoryEnvioRepository(EnvioRepository):
    def __init__(self) -> None:
        self._envios: Dict[UUID, Envio] = {}

    def obtener_por_id(self, id_envio: UUID) -> Optional[Envio]:
        return self._envios.get(id_envio)

    def guardar(self, envio: Envio) -> None:
        self._envios[envio.id_envio] = envio
