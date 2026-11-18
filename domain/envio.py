"""Capa de DOMINIO: entidad Envio y sus reglas de negocio.

Python puro: NO importa FastAPI, Pydantic ni ninguna librería de infraestructura.
Reglas tomadas de: Gherkin HU1 (AA1.2), máquina de estados (AA2.1) y contrato (AA2.3).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class EstadoOrden(Enum):
    RECIBIDO = "RECIBIDO"
    EN_ALMACEN = "EN_ALMACEN"
    EN_TRANSITO = "EN_TRANSITO"
    ENTREGADO = "ENTREGADO"
    CANCELADA = "CANCELADA"
    ANULADA = "ANULADA"


ESTADOS_CANCELACION = frozenset({EstadoOrden.CANCELADA, EstadoOrden.ANULADA})

# Máquina de estados: estado actual -> estados a los que SÍ puede pasar.
_TRANSICIONES_PERMITIDAS = {
    EstadoOrden.RECIBIDO: {EstadoOrden.EN_ALMACEN, EstadoOrden.CANCELADA, EstadoOrden.ANULADA},
    EstadoOrden.EN_ALMACEN: {EstadoOrden.EN_TRANSITO, EstadoOrden.CANCELADA, EstadoOrden.ANULADA},
    EstadoOrden.EN_TRANSITO: {EstadoOrden.ENTREGADO},
    EstadoOrden.ENTREGADO: set(),   # estado final
    EstadoOrden.CANCELADA: set(),   # estado final
    EstadoOrden.ANULADA: set(),     # estado final
}


class ErrorDeDominio(Exception):
    """Base de los errores de reglas de negocio."""


class DatosInvalidos(ErrorDeDominio):
    """Datos de entrada que violan una regla (equivale a HTTP 400)."""


class TransicionNoPermitida(ErrorDeDominio):
    """La máquina de estados prohíbe el cambio (equivale a HTTP 409)."""


@dataclass(frozen=True)
class Envio:
    id_envio: UUID
    estado_orden: EstadoOrden
    fecha_actualizacion: datetime
    id_operador: str
    motivo_cancelacion: Optional[str] = None

    def cambiar_estado(
        self,
        nuevo_estado: EstadoOrden,
        id_operador: str,
        motivo_cancelacion: Optional[str],
        ahora: datetime,
    ) -> "Envio":
        """Devuelve un Envio nuevo con el estado cambiado, o lanza un error de dominio."""
        id_operador = (id_operador or "").strip()
        if not id_operador:
            raise DatosInvalidos("El campo idOperador es requerido.")

        motivo = (motivo_cancelacion or "").strip()
        es_cancelacion = nuevo_estado in ESTADOS_CANCELACION
        if es_cancelacion and not motivo:
            raise DatosInvalidos(
                "El campo motivoCancelacion es requerido cuando el estado es CANCELADA o ANULADA."
            )

        if nuevo_estado not in _TRANSICIONES_PERMITIDAS[self.estado_orden]:
            raise TransicionNoPermitida(self._mensaje_de_rechazo(nuevo_estado))

        return replace(
            self,
            estado_orden=nuevo_estado,
            fecha_actualizacion=ahora,
            id_operador=id_operador,
            motivo_cancelacion=motivo if es_cancelacion else None,
        )

    def _mensaje_de_rechazo(self, nuevo_estado: EstadoOrden) -> str:
        if self.estado_orden is EstadoOrden.ENTREGADO:
            return "No se puede cancelar o modificar un paquete que ya fue entregado."
        if self.estado_orden in ESTADOS_CANCELACION:
            return f"La orden ya se encuentra en estado {self.estado_orden.value}."
        if self.estado_orden is EstadoOrden.EN_TRANSITO and nuevo_estado in ESTADOS_CANCELACION:
            return "No se puede cancelar, paquete en tránsito."
        return (
            f"Transición no permitida: de {self.estado_orden.value} a {nuevo_estado.value}."
        )
