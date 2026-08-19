"""Creates 3 demo MSME personas so the app isn't empty for a live demo.

Run from the backend/ directory, after load_regulations and
create_demo_users:
    python -m seed.load_regulations
    python -m seed.create_demo_users
    python -m seed.create_demo_personas

Idempotent: upserts by business name. Uses the same real service
functions the API routes use (evaluate_business_compliance,
generate_growth_forecast_alerts, create_filing) -- not hand-crafted
Obligation rows -- so every obligation/alert/filing shown is genuinely
computed by the deterministic Rules Engine, not fabricated demo data.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.enums import (
    BusinessLegalType,
    ObligationApplicability,
    ObligationType,
    RegistrationStatus,
    RegistrationType,
    SectorType,
    TurnoverBand,
    UserRole,
)
from app.models.business import Business
from app.models.registration import Registration
from app.models.user import User
from app.services.alerts import generate_growth_forecast_alerts
from app.services.compliance import evaluate_business_compliance
from app.services.filings import FilingStateError, create_filing

PERSONAS = [
    {
        "name": "Ganga Textiles Private Limited",
        "sector": SectorType.TRADING,
        "state": "Tamil Nadu",
        "registration_type": BusinessLegalType.PRIVATE_LIMITED,
        "turnover_band": TurnoverBand.CR5_50CR,
        "employee_count": 18,  # 2 short of EPF's 20 -> growth-forecast alert
        "registrations": {
            RegistrationType.GST: "27AASCD1234F1Z5",
            RegistrationType.UDYAM: "UDYAM-TN-03-0012345",
        },
        "seed_filing": True,
    },
    {
        "name": "Coimbatore Micro Traders",
        "sector": SectorType.TRADING,
        "state": "Tamil Nadu",
        "registration_type": BusinessLegalType.PROPRIETORSHIP,
        "turnover_band": TurnoverBand.UNDER_10L,
        "employee_count": 2,
        "registrations": {},
        "seed_filing": False,
    },
    {
        "name": "Nilgiri Manufacturing Co.",
        "sector": SectorType.MANUFACTURING,
        "state": "Tamil Nadu",
        "registration_type": BusinessLegalType.PRIVATE_LIMITED,
        "turnover_band": TurnoverBand.CR50_250CR,
        "employee_count": 35,  # past both EPF (20) and ESI (10) thresholds
        "registrations": {
            RegistrationType.GST: "33AABCN5678G1ZQ",
            RegistrationType.UDYAM: "UDYAM-TN-05-0067890",
            RegistrationType.EPF: None,
            RegistrationType.ESI: None,
        },
        "seed_filing": False,
    },
]


def _upsert_business(db: Session, persona: dict) -> Business:
    business = db.query(Business).filter(Business.name == persona["name"]).one_or_none()
    if business is None:
        business = Business(name=persona["name"])
        db.add(business)

    business.sector = persona["sector"]
    business.state = persona["state"]
    business.registration_type = persona["registration_type"]
    business.turnover_band = persona["turnover_band"]
    business.employee_count = persona["employee_count"]
    if persona["registrations"].get(RegistrationType.GST):
        business.gstin = persona["registrations"][RegistrationType.GST]
    if persona["registrations"].get(RegistrationType.UDYAM):
        business.udyam_number = persona["registrations"][RegistrationType.UDYAM]
    db.flush()

    existing_types = {r.type for r in db.query(Registration).filter(Registration.business_id == business.id).all()}
    for reg_type, number in persona["registrations"].items():
        if reg_type in existing_types:
            continue
        db.add(
            Registration(
                business_id=business.id,
                type=reg_type,
                number=number,
                status=RegistrationStatus.ACTIVE,
            )
        )
    db.commit()
    return business


def create_demo_personas() -> None:
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.role == UserRole.OWNER).first()

        for persona in PERSONAS:
            business = _upsert_business(db, persona)
            obligations, _results, regulations_by_code = evaluate_business_compliance(db, business)
            generate_growth_forecast_alerts(db, business, regulations_by_code)

            if persona["seed_filing"] and owner is not None:
                filing_obligation = next(
                    (
                        o
                        for o in obligations
                        if o.obligation_type == ObligationType.FILING
                        and o.applicability == ObligationApplicability.APPLICABLE
                    ),
                    None,
                )
                if filing_obligation is not None:
                    try:
                        create_filing(db, obligation=filing_obligation, actor=owner, period=None)
                    except FilingStateError:
                        pass  # already prepared on a previous run -- fine, idempotent

            print(f"Seeded '{business.name}' ({len(obligations)} obligations evaluated)")
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_personas()
