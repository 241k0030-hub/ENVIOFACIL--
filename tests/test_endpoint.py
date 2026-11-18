import pytest
from fastapi.testclient import TestClient

from main import construir_app

EN_ALMACEN = "11111111-1111-4111-8111-111111111111"
RECIBIDO = "22222222-2222-4222-8222-222222222222"
EN_TRANSITO = "33333333-3333-4333-8333-333333333333"
ENTREGADO = "44444444-4444-4444-8444-444444444444"
CANCELADA = "55555555-5555-4555-8555-555555555555"
NO_EXISTE = "99999999-9999-4999-8999-999999999999"


@pytest.fixture()
def cliente():
    return TestClient(construir_app())  # app nueva (datos frescos) en cada prueba


def patch(cliente, id_envio, cuerpo):
    return cliente.patch(f"/api/v1/envios/{id_envio}/estado", json=cuerpo)


def cancelar(motivo="Cliente solicitó la cancelación."):
    return {"estadoOrden": "CANCELADA", "idOperador": "OP-9876", "motivoCancelacion": motivo}


def test_200_cancelacion_exitosa_en_almacen(cliente):
    r = patch(cliente, EN_ALMACEN, cancelar())
    assert r.status_code == 200
    assert r.json()["estadoOrden"] == "CANCELADA"
    assert r.json()["motivoCancelacion"] == "Cliente solicitó la cancelación."


def test_200_avanzar_estado(cliente):
    r = patch(cliente, RECIBIDO, {"estadoOrden": "EN_ALMACEN", "idOperador": "OP-9876"})
    assert r.status_code == 200
    assert r.json()["estadoOrden"] == "EN_ALMACEN"


def test_400_id_no_es_uuid(cliente):
    r = patch(cliente, "abc", cancelar())
    assert r.status_code == 400
    assert r.json()["codigo"] == 400


def test_400_cancelar_sin_motivo(cliente):
    r = patch(cliente, EN_ALMACEN, {"estadoOrden": "CANCELADA", "idOperador": "OP-9876"})
    assert r.status_code == 400
    assert "motivoCancelacion" in r.json()["mensaje"]


def test_400_motivo_en_blanco(cliente):
    assert patch(cliente, EN_ALMACEN, cancelar("   ")).status_code == 400


def test_400_estado_invalido_o_faltan_campos(cliente):
    assert patch(cliente, EN_ALMACEN, {"estadoOrden": "VOLANDO", "idOperador": "OP-1"}).status_code == 400
    assert patch(cliente, EN_ALMACEN, {}).status_code == 400


def test_404_envio_inexistente(cliente):
    assert patch(cliente, NO_EXISTE, cancelar()).status_code == 404


def test_409_cancelar_en_transito(cliente):
    r = patch(cliente, EN_TRANSITO, cancelar())
    assert r.status_code == 409
    assert r.json()["mensaje"] == "No se puede cancelar, paquete en tránsito."


def test_409_modificar_entregado(cliente):
    assert patch(cliente, ENTREGADO, cancelar()).status_code == 409


def test_409_cancelar_dos_veces(cliente):
    assert patch(cliente, CANCELADA, cancelar()).status_code == 409
    assert patch(cliente, EN_ALMACEN, cancelar()).status_code == 200
    assert patch(cliente, EN_ALMACEN, cancelar()).status_code == 409
