import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import MovieReview

app = FastAPI(title="Personal Movie Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Movie Reviews Backend Running"}

@app.get("/schema")
def get_schema():
    """Expose schemas for tooling"""
    return {"collections": ["moviereview"]}

# DTO for creating a review (leveraging MovieReview)
class MovieReviewCreate(MovieReview):
    pass

# DTO for responses
class MovieReviewResponse(BaseModel):
    id: str
    title: str
    review: str
    rating: int
    watched_on: Optional[str] = None
    poster_url: Optional[str] = None
    tags: Optional[List[str]] = None


def _serialize(doc: dict) -> MovieReviewResponse:
    return MovieReviewResponse(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        review=doc.get("review"),
        rating=doc.get("rating"),
        watched_on=(doc.get("watched_on").isoformat() if doc.get("watched_on") else None),
        poster_url=doc.get("poster_url"),
        tags=doc.get("tags"),
    )


@app.post("/api/reviews", response_model=dict)
def create_review(payload: MovieReviewCreate):
    try:
        inserted_id = create_document("moviereview", payload)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reviews", response_model=List[MovieReviewResponse])
def list_reviews(limit: int = 50):
    try:
        docs = get_documents("moviereview", limit=limit)
        return [_serialize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
