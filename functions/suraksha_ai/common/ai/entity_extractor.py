import re
from common.models.dto import NormalizedQueryDTO, ExtractedEntityDTO


class EntityExtractor:
    def extract(self, query: NormalizedQueryDTO) -> list[ExtractedEntityDTO]:
        entities = []
        text = query.normalized_text

        name_patterns = re.findall(r"(?:accused|suspect|criminal|person|offender|named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        for name in name_patterns:
            entities.append(ExtractedEntityDTO(
                entity_type="accused_name", entity_value=name.strip(), confidence=0.8
            ))

        location_patterns = re.findall(r"(?:in|at|near|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        known_districts = ["bangalore", "mysuru", "mysore", "hubli", "mangalore", "belgaum",
                          "dharwad", "shivamogga", "tumkur", "gulbarga", "kalaburagi", "udupi"]
        for loc in location_patterns:
            loc_lower = loc.strip().lower()
            if any(d in loc_lower for d in known_districts):
                entities.append(ExtractedEntityDTO(
                    entity_type="location", entity_value=loc.strip(), confidence=0.9
                ))
                break

        year_patterns = re.findall(r"\b(20\d{2})\b", text)
        for y in year_patterns:
            entities.append(ExtractedEntityDTO(
                entity_type="year", entity_value=y, confidence=1.0
            ))

        crime_type_keywords = {
            "theft": "Theft", "murder": "Murder", "robbery": "Robbery",
            "assault": "Assault", "kidnap": "Kidnapping", "rape": "Rape",
            "dacoit": "Dacoity", "burglary": "Burglary", "cheating": "Cheating",
            "homicide": "Murder", "snatch": "Snatching"
        }
        for keyword, crime_type in crime_type_keywords.items():
            if keyword in text:
                entities.append(ExtractedEntityDTO(
                    entity_type="crime_type", entity_value=crime_type, confidence=0.85
                ))
                break

        return entities
