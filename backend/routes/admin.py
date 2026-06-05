from fastapi import APIRouter, Depends, HTTPException, Query
from models.schemas import AdminLoginRequest, AdminLoginResponse, AppointmentUpdateRequest
from services.auth import create_token, get_current_admin
from services.database import (
    verify_admin, get_dashboard_stats, get_all_customers,
    get_all_appointments, get_appointment_detail, update_appointment_status,
    get_all_escalations, get_db_tables, get_table_data
)
from routes.chat import agent

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@router.post("/login", response_model=AdminLoginResponse)
def admin_login(req: AdminLoginRequest):
    user = verify_admin(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["username"])
    return AdminLoginResponse(token=token, username=user["username"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard")
def dashboard(admin=Depends(get_current_admin)):
    return get_dashboard_stats()


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
@router.get("/customers")
def list_customers(admin=Depends(get_current_admin)):
    return get_all_customers()


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------
@router.get("/appointments")
def list_appointments(status: str = Query(None), admin=Depends(get_current_admin)):
    return get_all_appointments(status_filter=status)


@router.get("/appointments/{ticket_id}")
def appointment_detail(ticket_id: str, admin=Depends(get_current_admin)):
    detail = get_appointment_detail(ticket_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return detail


@router.put("/appointments/{ticket_id}/status")
def update_status(ticket_id: str, req: AppointmentUpdateRequest, admin=Depends(get_current_admin)):
    result = update_appointment_status(
        ticket_id=ticket_id,
        new_status=req.status,
        technician=req.technician,
        arrival_date=req.arrival_date,
        notes=req.notes,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Escalations
# ---------------------------------------------------------------------------
@router.get("/escalations")
def list_escalations(admin=Depends(get_current_admin)):
    return get_all_escalations()


# ---------------------------------------------------------------------------
# RAG Ingest (existing)
# ---------------------------------------------------------------------------
@router.post("/ingest")
def ingest(admin=Depends(get_current_admin)):
    agent.rag.ingest()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# DB Viewer
# ---------------------------------------------------------------------------
@router.get("/db/tables")
def db_tables(admin=Depends(get_current_admin)):
    return get_db_tables()


@router.get("/db/{table_name}")
def db_table_data(table_name: str, limit: int = Query(100, le=500), admin=Depends(get_current_admin)):
    result = get_table_data(table_name, limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
