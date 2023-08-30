from pydantic import BaseModel, Field, AnyUrl
from typing import List


class RatingModel(BaseModel):
    rating: float = Field(...)
    rater: str = Field(...) # user who provided the rating, this is an objectId field
    driver_id: str = Field(...)


class ReviewModel(BaseModel):
    review: str = Field(...)
    reviewer: str = Field(...) # user who provided the review, this is an objectId field
    driver_id: str = Field(...)


class ReportModel(BaseModel):
    report: str = Field(...)
    reporter: str = Field(...) # user who provided the report, this is an objectId field
    driver_id: str = Field(...)


class DriverModel(BaseModel):
    id: str= Field(None)
    nin: AnyUrl = Field(...)
    driver_license: AnyUrl = Field(...)
    is_verified: bool = False
    user_id: str = Field(None)

    ratings: List[RatingModel] = Field(default=[])
    reviews: List[ReviewModel] = Field(default=[])
    reports: List[ReportModel] = Field(default=[])

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "nin": "https://s3.store/12jrjjjrj950/",
                "driver_license": "https://s3.store/12jrjjjrj950/",
            }
        }

    def encode(self):
        return {
                "id": self.id, 
                "nin": self.nin.unicode_string(), 
                "driver_licence": self.driver_license.unicode_string(),
                "user_id": self.user_id,
                "is_verified": self.is_verified,
                "ratings": self.ratings,
                "reviews": self.reviews,
                "reports": self.reports
                }

