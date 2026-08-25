from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    total_cases: int
    total_recovered: int
