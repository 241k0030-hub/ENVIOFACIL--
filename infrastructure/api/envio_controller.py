"""Adaptador HTTP (FastAPI): implementa la ruta del contrato OpenAPI (AA2.3).

PATCH /api/v1/envios/{id}/estado  ->  200 / 400 / 404 / 409
Aquí SÍ se permite FastAPI y Pydantic (es la capa de Infraestructura).
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from application.actualizar_estado_envio import ActualizarEstadoComando, ActualizarEstadoEnvio
from application.errors import EnvioNoEncontrado
from domain.envio import DatosInvalidos, EstadoOrden, TransicionNoPermitida


# ---- Esquemas del contrato (components/schemas) ----
class ActualizarEstadoEnvioRequest(BaseModel):
    estadoOrden: EstadoOrden
    idOperador: str
    motivoCancelacion: Optional[str] = None


class EnvioResponse(BaseModel):
    idEnvio: UUID
    estadoOrden: EstadoOrden
    fechaActualizacion: datetime
    idOperador: str
    motivoCancelacion: Optional[str] = None


class ErrorResponse(BaseModel):
    codigo: int
    mensaje: str
    fecha: str


def _error(codigo: int, mensaje: str) -> JSONResponse:
    cuerpo = ErrorResponse(
        codigo=codigo,
        mensaje=mensaje,
        fecha=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return JSONResponse(status_code=codigo, content=cuerpo.model_dump())


def crear_app(actualizar_estado: ActualizarEstadoEnvio) -> FastAPI:
    """El caso de uso llega por parámetro (inyección manual por constructor/función)."""
    app = FastAPI(title="API EnvioFacil - Módulo de Almacén", version="1.0.0")

    # FastAPI responde 422 por defecto; el contrato exige 400 con ErrorResponse.
    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        campos = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
        return _error(
            400,
            "El payload carece de campos obligatorios o contiene valores inválidos"
            + (f" ({', '.join(campos)})." if campos else "."),
        )

    @app.patch(
        "/api/v1/envios/{id}/estado",
        response_model=EnvioResponse,
        tags=["Envíos"],
        summary="Modificar o cancelar el estado de un envío en almacén",
        operation_id="actualizarEstadoEnvio",
        responses={
            400: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
        },
    )
    def actualizar_estado_envio(id: str, cuerpo: ActualizarEstadoEnvioRequest):
        try:
            id_envio = UUID(id)
        except ValueError:
            return _error(400, "El parámetro id debe ser un UUID válido.")

        comando = ActualizarEstadoComando(
            id_envio=id_envio,
            nuevo_estado=cuerpo.estadoOrden,
            id_operador=cuerpo.idOperador,
            motivo_cancelacion=cuerpo.motivoCancelacion,
        )
        try:
            envio = actualizar_estado.ejecutar(comando)
        except DatosInvalidos as e:
            return _error(400, str(e))
        except EnvioNoEncontrado as e:
            return _error(404, str(e))
        except TransicionNoPermitida as e:
            return _error(409, str(e))

        return EnvioResponse(
            idEnvio=envio.id_envio,
            estadoOrden=envio.estado_orden,
            fechaActualizacion=envio.fecha_actualizacion,
            idOperador=envio.id_operador,
            motivoCancelacion=envio.motivo_cancelacion,
        )

    return app
