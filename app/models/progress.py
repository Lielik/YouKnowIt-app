# Tracks each user's knowledge status per card

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship

from app.database import Base


# The only two valid statuses — nothing else can be stored in the DB
class CardStatus(enum.Enum):
    I_KNOW_THIS = "i_know_this"
    I_WILL_KNOW_THIS = "i_will_know_this"


class CardProgress(Base):
    __tablename__ = "card_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    # Enum enforces only valid values — DB will reject anything else
    status = Column(Enum(CardStatus), nullable=False,
                    default=CardStatus.I_WILL_KNOW_THIS)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Ensures one progress record per card for every user — no duplicates
    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_user_card_progress"),
    )

    user = relationship("User", back_populates="progress")
    card = relationship("Card", back_populates="progress")
