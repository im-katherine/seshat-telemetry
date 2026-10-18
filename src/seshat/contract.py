from typing import Literal

from pydantic import BaseModel, Field, ConfigDict 


class DetectorEvent(BaseModel):
    """One counting interval reported by a radiation detector."""
    model_config = ConfigDict(extra="forbid", strict=True) #Se vir com um campo extra, nao aceita; Tipo errado: recusa e nao converte

    type: Literal["detector"]
    device_id: str = Field(min_length=1, max_length=64,  pattern=r"^[A-Za-z0-9_-]+$") ##  1-64 chars: letters, digits, _ and -
    ts: int = Field(gt=0)
    kind: Literal["gamma", "neutron"]
    counts: int = Field(ge=0)
    interval_s: float = Field(gt=0)

    @property
    def rate_cps(self) -> float:
        """Counts per second."""
        return self.counts/self.interval_s 

def parse_event(line: str) -> DetectorEvent:
    """Parse and validate one JSON line. Raise pydantic.ValidationError if invalid"""
    return DetectorEvent.model_validate_json(line)
    