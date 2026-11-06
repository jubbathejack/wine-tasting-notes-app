"""
Data models and validation for Wine Tasting Notes.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

COLOR_STYLES = ["Red", "White", "Rosé", "Sparkling", "Dessert", "Fortified"]
CLOSURE_TYPES = ["Cork", "Screwcap", "Glass", "Synthetic"]

@dataclass
class Wine:
    wine_name: str
    winery: str
    country: str
    color_style: str = "Red"
    grape_variety: str = ""
    tasting_notes: Optional[str] = None
    rating: Optional[int] = None
    tasting_date: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    sub_region: Optional[str] = None
    abv: Optional[float] = None
    price: Optional[float] = None
    serving_temperature: Optional[int] = None
    aging_potential: Optional[str] = None
    food_pairing: Optional[str] = None
    purchase_location: Optional[str] = None
    purchase_date: Optional[str] = None
    bottle_size: Optional[float] = 0.75
    closure_type: Optional[str] = "Cork"
    organic: bool = False
    biodynamic: bool = False
    aroma_notes: List[str] = field(default_factory=list)
    in_cellar: bool = False
    bottles: int = 1
    storage_location: Optional[str] = None
    drink_from: Optional[int] = None
    drink_until: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def vintage_display(self) -> str:
        return str(self.vintage) if self.vintage else "NV (Non-Vintage)"

    @property
    def rating_stars(self) -> str:
        """Return a 5-star visual representation for ratings 0-100."""
        if self.rating is None:
            return ""
        if self.rating >= 95:
            return "★★★★★"
        elif self.rating >= 88:
            return "★★★★☆"
        elif self.rating >= 80:
            return "★★★☆☆"
        elif self.rating >= 70:
            return "★★☆☆☆"
        else:
            return "★☆☆☆☆"

    @property
    def rating_level(self) -> str:
        """Human-readable classification."""
        if self.rating is None:
            return ""
        if self.rating >= 95:
            return "Classic / Extraordinary"
        elif self.rating >= 90:
            return "Outstanding"
        elif self.rating >= 85:
            return "Very Good"
        elif self.rating >= 80:
            return "Good"
        else:
            return "Mediocre / Below Average"

    @property
    def style_badge_class(self) -> str:
        mapping = {
            "Red": "style-badge-red",
            "White": "style-badge-white",
            "Rosé": "style-badge-rose",
            "Sparkling": "style-badge-sparkling",
            "Dessert": "style-badge-dessert",
            "Fortified": "style-badge-fortified",
        }
        return mapping.get(self.color_style, "style-badge-default")

    @property
    def location_summary(self) -> str:
        parts = [p for p in [self.sub_region, self.region, self.country] if p]
        return ", ".join(parts) if parts else "Unknown origin"

    @property
    def drink_window_display(self) -> str:
        """e.g. '2027–2035', 'From 2027', 'Until 2035', or ''"""
        if self.drink_from and self.drink_until:
            return f"{self.drink_from}–{self.drink_until}"
        elif self.drink_from:
            return f"From {self.drink_from}"
        elif self.drink_until:
            return f"Until {self.drink_until}"
        return ""

    @property
    def is_in_drink_window(self) -> bool:
        """True if the current year is within the drink window."""
        current_year = datetime.now().year
        after_from = (self.drink_from is None) or (current_year >= self.drink_from)
        before_until = (self.drink_until is None) or (current_year <= self.drink_until)
        return after_from and before_until and (self.drink_from is not None or self.drink_until is not None)

    def validate(self) -> List[str]:
        errors = []
        if not self.wine_name or not self.wine_name.strip():
            errors.append("Wine name is required.")
        if not self.winery or not self.winery.strip():
            errors.append("Winery / Producer is required.")
        if not self.country or not self.country.strip():
            errors.append("Country is required.")
        if self.color_style not in COLOR_STYLES:
            errors.append(f"Color style must be one of {', '.join(COLOR_STYLES)}.")
        if self.vintage is not None:
            current_year = datetime.now().year + 1
            if self.vintage < 1800 or self.vintage > current_year:
                errors.append(f"Vintage must be between 1800 and {current_year}.")
        if self.abv is not None and (self.abv < 0 or self.abv > 100):
            errors.append("ABV must be between 0% and 100%.")

        # Tasting-specific validation only for non-cellar wines
        if not self.in_cellar:
            if self.rating is None or not (0 <= self.rating <= 100):
                errors.append("Rating must be between 0 and 100.")
            if not self.tasting_notes or not self.tasting_notes.strip():
                errors.append("Tasting notes are required.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> Wine:
        return cls(
            id=row.get("id"),
            wine_name=row.get("wine_name", ""),
            winery=row.get("winery", ""),
            country=row.get("country", ""),
            region=row.get("region"),
            sub_region=row.get("sub_region"),
            vintage=row.get("vintage"),
            color_style=row.get("color_style", "Red"),
            grape_variety=row.get("grape_variety", ""),
            abv=float(row["abv"]) if row.get("abv") is not None else None,
            price=float(row["price"]) if row.get("price") is not None else None,
            tasting_date=row.get("tasting_date"),
            rating=int(row["rating"]) if row.get("rating") is not None else None,
            tasting_notes=row.get("tasting_notes"),
            serving_temperature=row.get("serving_temperature"),
            aging_potential=row.get("aging_potential"),
            food_pairing=row.get("food_pairing"),
            purchase_location=row.get("purchase_location"),
            purchase_date=row.get("purchase_date"),
            bottle_size=float(row["bottle_size"]) if row.get("bottle_size") is not None else 0.75,
            closure_type=row.get("closure_type", "Cork"),
            organic=bool(row.get("organic", 0)),
            biodynamic=bool(row.get("biodynamic", 0)),
            aroma_notes=cls._parse_aroma_notes(row.get("aroma_notes")),
            in_cellar=bool(row.get("in_cellar", 0)),
            bottles=int(row.get("bottles", 1)),
            storage_location=row.get("storage_location"),
            drink_from=row.get("drink_from"),
            drink_until=row.get("drink_until"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    @staticmethod
    def _parse_aroma_notes(raw: Any) -> List[str]:
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
            return [item.strip() for item in raw.split(",") if item.strip()]
        return []
