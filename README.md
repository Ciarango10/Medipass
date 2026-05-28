# Medipass — Sistema de Agendamiento Especializado

Arquitectura de microservicios basada en los patrones de **ClubFit**
(mismo stack Python/Flask, misma estructura hexagonal, mismos ABCs).

## Estructura

```
medipass/
├── ms-agenda-hub/        # Servicio principal (Puerto 8080)
│   └── app/
│       ├── domain/       # Modelos puros: Appointment, DoctorSlot
│       ├── application/
│       │   ├── ports/input/   # AppointmentUseCase (ABC)
│       │   ├── ports/out/     # AppointmentRepositoryPort, InsuranceValidationPort...
│       │   └── use_cases/     # AppointmentService (orquestador)
│       └── infrastructure/
│           └── adapters/
│               ├── input/     # Flask controller
│               ├── mappers/   # Domain <-> SQLAlchemy entity
│               └── output/
│                   ├── persistence/  # SQLAlchemy + SELECT FOR UPDATE
│                   ├── messaging/    # RabbitMQPublisher
│                   └── external/     # InsuranceClient (HTTP)
├── ms-insurance/         # Proxy aseguradora (Puerto 8081)
└── ms-ehr-logger/        # Worker asíncrono (RabbitMQ → MongoDB)
```

## Levantar el sistema

```bash
docker compose up --build
```

## Flujo de agendamiento

```
POST /appointments
  └─ 1. InsuranceClient → GET /insurance/validate (sync, 5s timeout)
  └─ 2. SELECT FOR UPDATE NOWAIT en doctor_slots (anti double-booking)
  └─ 3. INSERT appointments
  └─ 4. PUBLISH agenda.confirmed → RabbitMQ (async, fire-and-forget)
         └─ ms-ehr-logger consume → INSERT en MongoDB (HCD)
```

## Seed de pólizas

```bash
curl -X POST http://localhost:8081/insurance/seed
```

## Crear slot y agendar cita

```bash
# 1. Crear slot
curl -X POST http://localhost/slots -H "Content-Type: application/json" \
  -d '{"doctor_id":1,"doctor_name":"Dr. García","specialty":"ONCOLOGY","slot_datetime":"2026-06-15T09:00:00"}'

# 2. Agendar cita
curl -X POST http://localhost/appointments -H "Content-Type: application/json" \
  -d '{"patient_id":"P001","patient_name":"Ana Torres","doctor_id":1,"slot_id":1,"procedure_code":"CHT-001"}'
```

## Reglas de negocio implementadas

| RN | Regla | Implementación |
|----|-------|----------------|
| RN-01 | No confirmar si aseguradora devuelve NOT_COVERED | `InsuranceService.validate_coverage()` → `ProcedureNotCoveredException` |
| RN-02 | Bloquear agenda síncronamente (anti double-booking) | `SELECT FOR UPDATE NOWAIT` en `find_available_slot_for_update()` |
| RN-03 | Enviar al HCD asíncrono sin bloquear | `RabbitMQPublisher.publish()` + worker EHRLogger |
