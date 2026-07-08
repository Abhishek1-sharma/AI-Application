from sqlalchemy.orm import Session

from app.models import HCP


def seed_demo_data(db: Session) -> None:
    if db.query(HCP).count():
        return

    hcps = [
        HCP(
            name="Dr. Aditi Mehra",
            specialty="Cardiology",
            territory="Mumbai Central",
            segment="A",
            preferred_channel="In-person",
        ),
        HCP(
            name="Dr. Rohan Iyer",
            specialty="Endocrinology",
            territory="Bengaluru North",
            segment="A",
            preferred_channel="WhatsApp",
        ),
        HCP(
            name="Dr. Sana Kapoor",
            specialty="Internal Medicine",
            territory="Delhi South",
            segment="B",
            preferred_channel="Email",
        ),
    ]
    db.add_all(hcps)
    db.commit()
