from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
from typing import List, Dict, Any

# Initialize the FastAPI app
app = FastAPI()

# Connect to Redis
redis_client = redis.StrictRedis(host='redis-service', port=6379, db=0, decode_responses=True)

# Models for API requests and responses
class RecommendationRequest(BaseModel):
    user_id: str
    category: str

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[str]

# Endpoint 1: Add recommendation for a user
@app.post("/add_recommendation/")
async def add_recommendation(request: RecommendationRequest):
    try:
        # Fetch the existing recommendations from Redis
        recommendations = redis_client.get(f"user:{request.user_id}:recommendations")
        
        if recommendations:
            recommendations = json.loads(recommendations)
        else:
            recommendations = []
        
        # Add new recommendation
        recommendations.append(request.category)
        
        # Save back the updated list in Redis
        redis_client.set(f"user:{request.user_id}:recommendations", json.dumps(recommendations))
        
        return {
            "status": "success",
            "message": "Recommendation added successfully",
            "data": {
                "user_id": request.user_id,
                "category": request.category,
                "recommendations": recommendations
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Endpoint 2: Get recommendations for a user
@app.get("/get_recommendations/{user_id}")
async def get_recommendations(user_id: str):
    try:
        recommendations = redis_client.get(f"user:{user_id}:recommendations")
        
        if not recommendations:
            return {
                "status": "success",
                "message": "No recommendations found for this user",
                "data": {
                    "user_id": user_id,
                    "recommendations": []
                }
            }
        
        return {
            "status": "success",
            "message": "Recommendations retrieved successfully",
            "data": {
                "user_id": user_id,
                "recommendations": json.loads(recommendations)
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Endpoint 3: Get all recommendations for all users
@app.get("/get_all_recommendations/")
async def get_all_recommendations():
    try:
        keys = redis_client.keys("user:*:recommendations")
        all_recommendations = []
        
        for key in keys:
            user_id = key.split(":")[1]  # Fixed issue: Removed .decode()
            recommendations = redis_client.get(key)
            all_recommendations.append({
                "user_id": user_id,
                "recommendations": json.loads(recommendations)
            })
        
        if not all_recommendations:
            return {
                "status": "success",
                "message": "No recommendations found for any user",
                "data": []
            }
        
        return {
            "status": "success",
            "message": "All recommendations retrieved successfully",
            "data": all_recommendations
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Endpoint 4: Remove recommendation for a user
@app.delete("/remove_recommendation/{user_id}/{category}")
async def remove_recommendation(user_id: str, category: str):
    try:
        recommendations = redis_client.get(f"user:{user_id}:recommendations")
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found for this user")
        
        recommendations = json.loads(recommendations)
        
        if category in recommendations:
            recommendations.remove(category)
            redis_client.set(f"user:{user_id}:recommendations", json.dumps(recommendations))
            return {
                "status": "success",
                "message": "Recommendation removed successfully",
                "data": {
                    "user_id": user_id,
                    "removed_category": category,
                    "recommendations": recommendations
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Recommendation not found")
    except Exception as e:
        return {"status": "error", "message": str(e)}
