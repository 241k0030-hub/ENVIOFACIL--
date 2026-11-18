"""Caso de uso: actualizar (o cancelar) el estado de un envío.

Orquesta el flujo: buscar -> aplicar regla de dominio -> guardar.
No conoce HTTP ni cómo se almacenan los datos.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID

from application.errors import EnvioNoEncontrado
from application.ports import EnvioRepository
from domain.envio import Envio, EstadoOrden


@dataclass(frozen=True)
class ActualizarEstadoComando:
    id_envio: UUID
    nuevo_estado: EstadoOrden
    id_operador: str
    motivo_cancelacion: Optional[str] = None


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class ActualizarEstadoEnvio:
    def __init__(self, repositorio: EnvioRepository, reloj: Callable[[], datetime] = _ahora_utc):
        self._repositorio = repositorio
        self._reloj = reloj

    def ejecutar(self, comando: ActualizarEstadoComando) -> Envio:
        envio = self._repositorio.obtener_por_id(comando.id_envio)
        if envio is None:
            raise EnvioNoEncontrado(f"No existe un envío con id {comando.id_envio}.")

        actualizado = envio.cambiar_estado(
            nuevo_estado=comando.nuevo_estado,
            id_operador=comando.id_operador,
            motivo_cancelacion=comando.motivo_cancelacion,
            ahora=self._reloj(),
        )
        self._repositorio.guardar(actualizado)
        return actualizado
