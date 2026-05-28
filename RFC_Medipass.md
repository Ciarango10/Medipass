# RFC: Medipass — Sistema de Agendamiento Especializado

**Autores:** [Nombres de los integrantes]
**Versión:** 1.0 | **Estado:** Propuesta técnica

---

## 1. Resumen Ejecutivo

### Problema

Una red de salud de alta complejidad gestiona citas para especialistas críticos (Oncólogos, Cardiólogos). El proceso de agendamiento manual introduce tres errores sistémicos con consecuencias graves:

1. **Double-Booking**: Dos recepcionistas confirman al mismo médico en el mismo horario → tiempo clínico desperdiciado y riesgo para el paciente.
2. **Confirmación sin cobertura**: Se agenda un procedimiento que la aseguradora no cubre → deuda hospitalaria incobreable y conflictos con el paciente.
3. **Historial desactualizado**: El médico atiende al paciente sin ver el resumen de la cita → riesgo clínico por falta de contexto.

### Solución propuesta

**Medipass**: tres microservicios con responsabilidades claramente delimitadas, comunicación síncrona y asíncrona según el tipo de operación, y persistencia políglota acorde a cada modelo de datos.

| Microservicio | Responsabilidad | Patrón |
|---|---|---|
| **MS-AgendaHub** | Orquestar validación, bloquear agenda, confirmar cita | Hexagonal / SOLID / ACID |
| **MS-Insurance** | Proxy hacia API de aseguradora externa | REST / Circuit Breaker |
| **MS-EHRLogger** | Registrar resumen en Historial Clínico Digital | Consumer / Event-driven |

**Flujo principal:**
```
Recepcionista → [Nginx] → MS-AgendaHub
                               ├── [REST síncrono] → MS-Insurance → API Aseguradora
                               │       ↓ (si cobertura OK)
                               ├── [SELECT FOR UPDATE] PostgreSQL (bloquea slot)
                               ├── [Confirma cita] → responde al recepcionista
                               └── [Publica evento] → RabbitMQ → MS-EHRLogger → MongoDB
```

---

## 2. Atributos de Calidad

### Atributo 1: Integridad Transaccional (Correctness / Safety)

**Escenario crítico**: Dos recepcionistas intentan agendar al Dr. García en el mismo slot de 10:00 a.m. simultáneamente desde terminales diferentes.

**Decisión arquitectónica**: MS-AgendaHub ejecuta la reserva del slot bajo una transacción SERIALIZABLE en PostgreSQL con `SELECT FOR UPDATE` sobre la tabla `doctor_slots`. Solo una transacción puede adquirir el lock; la segunda recibe un error de conflicto y se rechaza con mensaje controlado.

**Por qué no consistencia eventual**: En oncología, un doble agendamiento puede implicar preparar dos pacientes para quimioterapia en el mismo box de tratamiento. El costo de inconsistencia supera incomparablemente el costo de mayor latencia. La consistencia aquí debe ser **fuerte**, no eventual.

**Métrica de éxito**: Cero instancias de doble reserva bajo carga concurrente. Verificable con prueba de carga (k6/JMeter) con 50 threads intentando el mismo slot simultáneamente.

---

### Atributo 2: Disponibilidad Degradada (Resilience)

**Escenario crítico**: La API de la aseguradora (sistema externo, SLA desconocido) tarda 30 segundos en responder o está caída.

**Decisión arquitectónica**: MS-Insurance implementa tres mecanismos de resiliencia en cascada:

1. **Timeout fijo**: WebClient con timeout de 5 segundos sobre la llamada HTTP externa.
2. **Circuit Breaker** (Resilience4j): Si ≥50% de las llamadas fallan en ventana de 10 requests, el circuito abre y retorna `INSURANCE_UNAVAILABLE` inmediatamente.
3. **Cache de validaciones** (Redis, TTL 15 min): Si el mismo paciente + procedimiento ya fue validado recientemente, se sirve desde cache sin llamar al externo.

**Por qué no async para la validación**: No podemos confirmar una cita de oncología de forma optimista y rechazarla después; el paciente ya está en el teléfono o en recepción esperando confirmación. La validación debe ser bloqueante.

**Métrica de éxito**: Latencia P99 del agendamiento < 6 segundos incluso con aseguradora degradada. El sistema devuelve `PROCEDURE_NOT_COVERED` o `INSURANCE_UNAVAILABLE` en < 5.5s.

---

### Atributo 3: Desacoplamiento Temporal del HCD (Decoupling)

**Escenario crítico**: El sistema de Historial Clínico Digital está en ventana de mantenimiento o sufre latencia elevada por ingesta masiva de datos.

**Decisión arquitectónica**: Tras confirmar la cita en PostgreSQL, MS-AgendaHub publica un `AppointmentConfirmedEvent` a RabbitMQ y **retorna inmediatamente** la confirmación al recepcionista. MS-EHRLogger consume el evento de forma independiente y escribe el resumen en MongoDB.

**Garantías del broker**: RabbitMQ con `publisher confirms` y `durable queues` garantiza entrega at-least-once. Si MongoDB está caído, el mensaje permanece en la cola hasta recuperación. Dead Letter Queue (DLQ) captura mensajes que fallen > 3 reintentos para análisis posterior.

**Por qué no síncrono para HCD**: El proceso de agendamiento no debe esperar una escritura en un sistema de historial que puede tomar segundos. El médico consultará el historial horas o días después de la cita, no durante el agendamiento.

**Métrica de éxito**: El tiempo de respuesta del agendamiento es independiente de la latencia de MongoDB. Consistencia eventual garantizada: el resumen aparece en HCD dentro de los SLA del broker (< 30 segundos en condiciones normales).

---

## 3. Decisiones Arquitectónicas

### 3.1 Lenguaje y Framework: Java 17 + Spring Boot 3.x

**Justificación**: Spring Boot 3 sobre Java 17 Virtual Threads (Project Loom) permite thread-per-request con el rendimiento de reactivo, sin la complejidad cognitiva de WebFlux para el equipo. El ecosistema Spring provee todo lo necesario:

| Necesidad | Solución Spring |
|---|---|
| Cliente HTTP externo | `WebClient` (non-blocking) |
| Circuit Breaker | `Resilience4j` (starter nativo) |
| Mensajería | `spring-amqp` (RabbitMQ) |
| Observabilidad | `Micrometer` + `spring-actuator` |
| Persistencia políglota | `spring-data-jpa` + `spring-data-mongodb` |

**Alternativa descartada: Node.js/TypeScript**. El ecosistema de interoperabilidad con sistemas médicos (HL7 FHIR, IHE) es más maduro en Java. El equipo cliente ya opera con Java.

---

### 3.2 Base de Datos Principal: PostgreSQL 15

**Justificación técnica**:

- **ACID completo**: Transacciones con aislamiento `SERIALIZABLE` para detectar conflictos de escritura concurrente en la agenda.
- **`SELECT FOR UPDATE SKIP LOCKED`**: Permite múltiples workers procesar slots disponibles sin deadlocks.
- **Esquema relacional estricto**: La agenda médica tiene reglas de integridad complejas (FK doctor↔slot, FK paciente↔seguro) que un modelo relacional maneja mejor que documental.
- **Open Source**: Sin costo de licencia Oracle para el servicio principal.

**Modelo de datos clave (simplificado)**:
```sql
CREATE TABLE doctor_slots (
  id            UUID PRIMARY KEY,
  doctor_id     UUID NOT NULL REFERENCES doctors(id),
  slot_datetime TIMESTAMPTZ NOT NULL,
  status        VARCHAR(20) CHECK (status IN ('AVAILABLE','BLOCKED','CONFIRMED')),
  UNIQUE (doctor_id, slot_datetime)
);
```

---

### 3.3 Oracle 19c para MS-Insurance

**Justificación**: Oracle es un **constraint externo**, no una elección libre. La aseguradora provee acceso a su catálogo de pólizas y procedimientos cubiertos únicamente a través de procedimientos almacenados en Oracle 19c. MS-Insurance actúa como Anti-Corruption Layer (ACL): traduce el contrato Oracle a una API REST consumible por MS-AgendaHub, aislando al dominio de la tecnología del proveedor.

---

### 3.4 Broker de Mensajes: RabbitMQ (vs. Kafka)

**Análisis comparativo**:

| Criterio | RabbitMQ (elegido) | Apache Kafka |
|---|---|---|
| Modelo | Push (mensaje discreto) | Pull (log distribuido) |
| Caso de uso | Task queues, eventos de negocio | Event sourcing, replay, alto volumen |
| Latencia | < 1ms | ~5ms (overhead de log) |
| Operacional | Docker Compose simple | Requiere KRaft/Zookeeper |
| Replay de eventos | No (mensajes consumidos) | Sí (log compacto) |
| Volumen objetivo | Miles de citas/día | Millones de eventos/día |

**Decisión**: Para el volumen de una red hospitalaria (estimado: 500-5,000 citas/día), RabbitMQ es suficiente y operacionalmente más simple. No necesitamos replay de eventos históricos (responsabilidad de MongoDB). Kafka introduciría complejidad de infraestructura sin beneficio proporcional.

**Configuración clave**:
```yaml
# Publisher Confirms para garantía at-least-once desde MS-AgendaHub
spring.rabbitmq.publisher-confirm-type: correlated
spring.rabbitmq.publisher-returns: true
```

---

### 3.5 MongoDB para el Historial Clínico Digital

**Justificación**: Los registros clínicos son documentos semi-estructurados con esquema variable por especialidad:

```json
{
  "appointmentId": "uuid",
  "patient": { "id": "...", "name": "..." },
  "doctor": { "id": "...", "specialty": "ONCOLOGY" },
  "insuranceCoverage": { "procedureCode": "CHT-001", "status": "COVERED" },
  "specialtyNotes": {
    "oncology": { "protocol": "FOLFOX", "cycle": 3 }
  }
}
```

Un cardiólogo documenta `ecgFindings` donde un oncólogo documenta `chemotherapyProtocol`. MongoDB permite esta variación sin ALTER TABLE y escala horizontalmente para volúmenes de datos históricos que crecen indefinidamente.

---

### 3.6 Arquitectura Hexagonal en MS-AgendaHub

MS-AgendaHub concentra la lógica de negocio más crítica y compleja. La arquitectura hexagonal (Ports & Adapters) garantiza que las reglas de negocio sean independientes de frameworks e infraestructura.

**Estructura de paquetes**:
```
ms-agenda-hub/
├── domain/
│   ├── model/          # Appointment, DoctorSlot, Patient, InsuranceCoverage
│   ├── service/        # AppointmentSchedulingService (lógica pura)
│   └── port/
│       ├── in/         # ScheduleAppointmentUseCase (Puerto de entrada)
│       └── out/        # InsuranceValidationPort, SlotRepositoryPort,
│                       # AppointmentEventPublisherPort
├── application/
│   └── usecase/        # Implementación de casos de uso
└── infrastructure/
    ├── rest/           # Adaptador HTTP entrada (Controllers)
    ├── insurance/      # Adaptador REST salida → MS-Insurance
    ├── persistence/    # Adaptador JPA → PostgreSQL
    └── messaging/      # Adaptador RabbitMQ salida
```

**Beneficio clave**: Las reglas de negocio (ej. `if (coverage.status == NOT_COVERED) throw AppointmentDeniedException()`) se testean con mocks de los puertos, sin levantar bases de datos ni brokers.

---

### 3.7 Aplicación de Principios SOLID

| Principio | Aplicación concreta en Medipass |
|---|---|
| **S** — Single Responsibility | Cada microservicio tiene exactamente una razón para cambiar. MS-Insurance solo cambia si cambia el proveedor de seguros. MS-EHRLogger solo si cambia el HCD. |
| **O** — Open/Closed | `InsuranceValidationPort` tiene múltiples implementaciones por aseguradora (EPS-Sanitas, SisaludEPS…) sin modificar el dominio. |
| **L** — Liskov Substitution | Cualquier implementación de `SlotRepositoryPort` (JPA, JDBC, en memoria para tests) es intercambiable sin romper el servicio. |
| **I** — Interface Segregation | Puertos granulares: `ScheduleAppointmentUseCase` ≠ `CancelAppointmentUseCase` ≠ `RescheduleAppointmentUseCase`. |
| **D** — Dependency Inversion | `AppointmentSchedulingService` depende de `InsuranceValidationPort` (interfaz), no de `MSInsuranceAdapter` (implementación). |

---

### 3.8 Patrones GoF Aplicados

| Patrón | Contexto |
|---|---|
| **Strategy** | `InsuranceValidationStrategy`: comportamiento diferente según tipo de aseguradora (REST, SOAP, Oracle directo). |
| **Factory Method** | `AppointmentFactory.create(type, dto)`: instancia `OncologyAppointment` o `CardiologyAppointment` según la especialidad. |
| **Observer** | `AppointmentConfirmedEvent` se emite desde el dominio; el adaptador de mensajería lo suscribe y publica en RabbitMQ. Desacopla dominio de infraestructura. |
| **Repository** | `SlotRepositoryPort` implementado por `JpaSlotRepository`. El dominio nunca toca JPA directamente. |
| **Circuit Breaker** | Resilience4j en MS-Insurance protege el circuito hacia la API externa (variante del patrón Proxy). |

---

## 4. Trade-offs

### Trade-off 1: Consistencia Fuerte vs. Disponibilidad (teorema CAP)

| Dimensión | Decisión | Costo |
|---|---|---|
| **Qué se eligió** | Consistencia fuerte (PostgreSQL ACID) para reserva de slots | Mayor latencia de escritura |
| **Qué se sacrificó** | Disponibilidad: si el primary de PostgreSQL falla, el agendamiento no está disponible | Downtime temporal posible |
| **Justificación** | Un double-booking en oncología tiene consecuencias irreversibles para el paciente | — |
| **Mitigación** | Replicación síncrona PostgreSQL (Patroni + streaming replication) para minimizar downtime | RTO < 30s con failover automático |

> **Regla**: en salud de alta complejidad, **precisión > disponibilidad** para operaciones de escritura crítica.

---

### Trade-off 2: Latencia Adicional por Validación Síncrona

| Dimensión | Decisión | Costo |
|---|---|---|
| **Qué se eligió** | Validación de seguro síncrona (bloqueante) en el flujo principal | P99 latencia: ~6s vs ~200ms sin validación |
| **Qué se sacrificó** | Velocidad de confirmación al recepcionista | Mayor tiempo en llamada |
| **Justificación** | Confirmar una cita sin cobertura y revertirla después genera confusión en pacientes críticos | — |
| **Mitigación** | Cache Redis (TTL 15 min) reduce el ~70% de llamadas redundantes. Circuit Breaker limita la espera máxima a 5s | — |

---

### Trade-off 3: Consistencia Eventual del Historial Clínico

| Dimensión | Decisión | Costo |
|---|---|---|
| **Qué se eligió** | Escritura asíncrona en HCD (consistencia eventual) | Ventana de inconsistencia de segundos a minutos |
| **Qué se sacrificó** | El historial no es atómico con la confirmación de la cita | Si el broker falla antes del ACK, puede haber mensaje perdido (mitigado con publisher confirms) |
| **Justificación** | El médico consultará el historial horas/días después, no durante el agendamiento | — |
| **Mitigación** | `publisher confirms` + `durable queues` + DLQ garantizan entrega eventual incluso con MongoDB temporalmente caído | — |

---

### Trade-off 4: RabbitMQ vs. Kafka

| Dimensión | RabbitMQ (elegido) | Kafka (descartado) |
|---|---|---|
| **Ventaja** | Operacional simple, baja latencia, suficiente para el volumen | Replay de eventos, escalabilidad masiva |
| **Costo** | Sin replay de eventos históricos; mensajes consumidos son eliminados | Complejidad operacional (KRaft/Zookeeper) en Docker Compose |
| **Conclusión** | Correcto para task queues de citas médicas (< 5,000/día) | Sobreingeniería para este caso |

---

## 5. Diagrama C4 Nivel 2

*Ver diagrama de contenedores adjunto (renderizado por separado).*

**Leyenda del diagrama**:
- **Línea sólida** → Llamada síncrona (REST/JDBC)
- **Línea punteada** → Comunicación asíncrona (AMQP) o externa
- **Caja punteada** → Sistema externo fuera del límite de Medipass
- **Borde grueso** → Componente principal (MS-AgendaHub)

---

## 6. Infraestructura Docker Compose

```yaml
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    depends_on: [ms-agenda-hub]

  ms-agenda-hub:
    build: ./ms-agenda-hub
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/agenda
      SPRING_RABBITMQ_HOST: rabbitmq
      INSURANCE_SERVICE_URL: http://ms-insurance:8081

  ms-insurance:
    build: ./ms-insurance
    environment:
      ORACLE_URL: jdbc:oracle:thin:@oracle:1521/POLIZAS

  ms-ehr-logger:
    build: ./ms-ehr-logger
    environment:
      SPRING_RABBITMQ_HOST: rabbitmq
      SPRING_DATA_MONGODB_URI: mongodb://mongodb:27017/hcd

  postgres:
    image: postgres:15-alpine
    volumes: [pgdata:/var/lib/postgresql/data]

  oracle:
    image: gvenzl/oracle-xe:21-slim
    volumes: [oradata:/opt/oracle/oradata]

  rabbitmq:
    image: rabbitmq:3.12-management
    ports: ["15672:15672"]

  mongodb:
    image: mongo:7
    volumes: [mongodata:/data/db]

  prometheus:
    image: prom/prometheus:latest

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports: ["16686:16686"]

volumes:
  pgdata:
  oradata:
  mongodata:
```

---

## 7. Observabilidad

| Herramienta | Propósito | Configuración |
|---|---|---|
| **Micrometer** | Métricas de negocio y técnicas | `@Timed`, `@Counted` en use cases |
| **Prometheus** | Scraping de métricas | `actuator/prometheus` endpoint |
| **Grafana** | Dashboard: latencia P50/P95/P99, tasa de error, cobertura rechazada | Dashboard preconstruido via JSON |
| **OpenTelemetry** | Instrumentación de trazas distribuidas | Auto-instrumentation agent |
| **Jaeger** | Visualización de trazas end-to-end | Exportador OTLP → Jaeger |

**Métrica de negocio clave**:
```
# Tasa de citas rechazadas por cobertura
medipass_appointments_denied_total{reason="NOT_COVERED"} / medipass_appointments_attempted_total
```

---

## 8. Reglas de Negocio — Implementación

### RN-01: No confirmar si aseguradora devuelve "Procedimiento No Cubierto"
```java
// En AppointmentSchedulingService (dominio puro, sin Spring)
public Appointment schedule(ScheduleAppointmentCommand cmd) {
    InsuranceCoverage coverage = insurancePort.validate(cmd.patientId(), cmd.procedureCode());
    if (coverage.status() == NOT_COVERED) {
        throw new ProcedureNotCoveredException(coverage.rejectionCode());
    }
    // continúa con bloqueo de slot...
}
```

### RN-02: Bloqueo síncrono anti Double-Booking
```sql
-- En SlotRepositoryAdapter
SELECT * FROM doctor_slots
WHERE doctor_id = ? AND slot_datetime = ? AND status = 'AVAILABLE'
FOR UPDATE NOWAIT;
-- NOWAIT: falla inmediatamente si otro proceso tiene el lock
-- La excepción se captura y retorna HTTP 409 CONFLICT
```

### RN-03: Historial asíncrono sin esperar respuesta
```java
// Tras confirmar la cita, publica evento y retorna
eventPublisher.publish(new AppointmentConfirmedEvent(appointment));
return AppointmentConfirmation.from(appointment); // Retorna SIN esperar MongoDB
```
