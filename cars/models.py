from pydantic import BaseModel, Field


class Car(BaseModel):
    id: str = Field(None)
    model: str = Field(...)
    brand: str = Field(...)
    color: str = Field(...)
    c_type: str = Field(...)
    c_license: str = Field(...)
    user_id: str = Field(None)

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "model": "cr7",
                "brand": "toyota",
                "color": "red",
                "c_type": "camry",
                "c_license": "Qhfdjfio9"
            }
        }

