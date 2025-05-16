import os
import sys
import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from config.paths_config import *
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)

app = FastAPI(
    title="Anime Recommendation API",
    description="API for getting personalized anime recommendations",
    version="1.0.0"
)

# Define data models for requests and responses
class UserRecommendationRequest(BaseModel):
    user_id: int
    num_recommendations: int = 10

class AnimeRecommendationRequest(BaseModel):
    anime_id: int
    num_recommendations: int = 10

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]

# Load all necessary data and models
@app.on_event("startup")
async def load_model_and_data():
    global user2user_encoded, user2user_decoded, anime2anime_encoded, anime2anime_decoded
    global user_weights, anime_weights, anime_df, rating_df
    
    try:
        # Load mappings
        user2user_encoded = joblib.load(os.path.join(PROCESSED_DIR, "user2user_encoded.pkl"))
        user2user_decoded = joblib.load(os.path.join(PROCESSED_DIR, "user2user_decoded.pkl"))
        anime2anime_encoded = joblib.load(os.path.join(PROCESSED_DIR, "anim2anime_encoded.pkl"))
        anime2anime_decoded = joblib.load(os.path.join(PROCESSED_DIR, "anim2anime_decoded.pkl"))
        
        # Load model weights
        user_weights = joblib.load(USER_WEIGHTS_PATH)
        anime_weights = joblib.load(ANIME_WEIGHTS_PATH)
        
        # Load anime metadata
        anime_df = pd.read_csv(DF)
        
        # Load rating data for popularity-based recommendations
        rating_df = pd.read_csv(RATING_DF)
        
        logger.info("Model and data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model and data: {str(e)}")
        raise RuntimeError(f"Failed to load model and data: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to the Anime Recommendation API", 
            "docs_url": "/docs",
            "endpoints": ["/recommend/user", "/recommend/similar", "/recommend/popular", "/valid-users", "/valid-anime", "/health"]}

@app.get("/valid-users")
async def get_valid_users(limit: int = 10):
    """
    Get a list of valid user IDs for testing the recommendation API.
    
    - **limit**: Maximum number of user IDs to return (default: 10)
    """
    try:
        valid_users = list(user2user_encoded.keys())[:limit]
        return {
            "valid_user_ids": valid_users,
            "total_users": len(user2user_encoded),
            "message": "Use these IDs to test the /recommend/user endpoint"
        }
    except Exception as e:
        logger.error(f"Error getting valid users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting valid users: {str(e)}")

@app.get("/valid-anime")
async def get_valid_anime(limit: int = 10):
    """
    Get a list of valid anime IDs for testing the recommendation API.
    
    - **limit**: Maximum number of anime IDs to return (default: 10)
    """
    try:
        valid_anime = list(anime2anime_encoded.keys())[:limit]
        anime_details = []
        
        for anime_id in valid_anime:
            anime_info = anime_df[anime_df['anime_id'] == anime_id]
            if not anime_info.empty:
                anime_row = anime_info.iloc[0]
                anime_details.append({
                    "anime_id": int(anime_id),
                    "name": anime_row.get("eng_version", "Unknown"),
                    "score": float(anime_row.get("Score", 0)) if not pd.isna(anime_row.get("Score", 0)) else 0
                })
            else:
                anime_details.append({
                    "anime_id": int(anime_id),
                    "name": "Unknown",
                    "score": 0
                })
                
        return {
            "valid_anime": anime_details,
            "total_anime": len(anime2anime_encoded),
            "message": "Use these IDs to test the /recommend/similar endpoint"
        }
    except Exception as e:
        logger.error(f"Error getting valid anime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting valid anime: {str(e)}")

@app.post("/recommend/user", response_model=RecommendationResponse)
async def recommend_for_user(request: UserRecommendationRequest):
    """
    Get personalized anime recommendations for a specific user.
    
    - **user_id**: ID of the user to get recommendations for
    - **num_recommendations**: Number of recommendations to return (default: 10)
    """
    try:
        # Check if user exists
        if request.user_id not in user2user_encoded:
            raise HTTPException(status_code=404, detail=f"User ID {request.user_id} not found. Use /valid-users to get valid user IDs.")
        
        # Get user embedding
        user_encoded_id = user2user_encoded[request.user_id]
        user_embedding = user_weights[user_encoded_id]
        
        # Calculate similarity with all anime
        scores = np.dot(anime_weights, user_embedding)
        
        # Get top recommendations
        top_indices = np.argsort(scores)[::-1][:request.num_recommendations]
        
        # Get anime IDs from encoded IDs
        anime_ids = [anime2anime_decoded[idx] for idx in top_indices]
        
        # Get anime details
        recommendations = []
        for anime_id in anime_ids:
            anime_info = anime_df[anime_df['anime_id'] == anime_id]
            if not anime_info.empty:
                anime_row = anime_info.iloc[0]
                recommendations.append({
                    "anime_id": int(anime_id),
                    "name": anime_row.get("eng_version", "Unknown"),
                    "score": float(anime_row.get("Score", 0)) if not pd.isna(anime_row.get("Score", 0)) else 0,
                    "genres": anime_row.get("Genres", "Unknown"),
                    "episodes": int(anime_row.get("Episodes", 0)) if not pd.isna(anime_row.get("Episodes", 0)) else 0,
                    "type": anime_row.get("Type", "Unknown"),
                    "recommendation_score": float(scores[anime2anime_encoded[anime_id]])
                })
            else:
                recommendations.append({
                    "anime_id": int(anime_id),
                    "name": "Unknown",
                    "recommendation_score": float(scores[anime2anime_encoded[anime_id]])
                })
        
        return {"recommendations": recommendations}
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/recommend/similar", response_model=RecommendationResponse)
async def recommend_similar_anime(request: AnimeRecommendationRequest):
    """
    Get anime recommendations similar to a specific anime.
    
    - **anime_id**: ID of the anime to find similar titles for
    - **num_recommendations**: Number of recommendations to return (default: 10)
    """
    try:
        # Check if anime exists
        if request.anime_id not in anime2anime_encoded:
            raise HTTPException(status_code=404, detail=f"Anime ID {request.anime_id} not found. Use /valid-anime to get valid anime IDs.")
        
        # Get anime embedding
        anime_encoded_id = anime2anime_encoded[request.anime_id]
        anime_embedding = anime_weights[anime_encoded_id]
        
        # Calculate similarity with all anime
        scores = np.dot(anime_weights, anime_embedding)
        
        # Get top recommendations (excluding the input anime)
        top_indices = np.argsort(scores)[::-1]
        top_indices = [idx for idx in top_indices if idx != anime_encoded_id][:request.num_recommendations]
        
        # Get anime IDs from encoded IDs
        anime_ids = [anime2anime_decoded[idx] for idx in top_indices]
        
        # Get anime details
        recommendations = []
        for anime_id in anime_ids:
            anime_info = anime_df[anime_df['anime_id'] == anime_id]
            if not anime_info.empty:
                anime_row = anime_info.iloc[0]
                recommendations.append({
                    "anime_id": int(anime_id),
                    "name": anime_row.get("eng_version", "Unknown"),
                    "score": float(anime_row.get("Score", 0)) if not pd.isna(anime_row.get("Score", 0)) else 0,
                    "genres": anime_row.get("Genres", "Unknown"),
                    "episodes": int(anime_row.get("Episodes", 0)) if not pd.isna(anime_row.get("Episodes", 0)) else 0,
                    "type": anime_row.get("Type", "Unknown"),
                    "similarity": float(scores[anime2anime_encoded[anime_id]])
                })
            else:
                recommendations.append({
                    "anime_id": int(anime_id),
                    "name": "Unknown",
                    "similarity": float(scores[anime2anime_encoded[anime_id]])
                })
        
        return {"recommendations": recommendations}
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error finding similar anime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error finding similar anime: {str(e)}")

@app.get("/recommend/popular", response_model=RecommendationResponse)
async def get_popular_anime(num_recommendations: int = Query(10, description="Number of recommendations to return")):
    """
    Get the most popular anime based on ratings.
    
    - **num_recommendations**: Number of recommendations to return (default: 10)
    """
    try:
        # Get popular anime based on average rating and number of ratings
        anime_stats = rating_df.groupby('anime_id').agg(
            avg_rating=('rating', 'mean'),
            num_ratings=('rating', 'count')
        ).reset_index()
        
        # Filter anime with at least 100 ratings
        anime_stats = anime_stats[anime_stats['num_ratings'] >= 100]
        
        # Sort by average rating
        anime_stats = anime_stats.sort_values(by='avg_rating', ascending=False)
        
        # Get top anime
        top_anime_ids = anime_stats.head(num_recommendations)['anime_id'].tolist()
        
        # Get anime details
        recommendations = []
        for anime_id in top_anime_ids:
            anime_info = anime_df[anime_df['anime_id'] == anime_id]
            if not anime_info.empty:
                anime_row = anime_info.iloc[0]
                anime_stat = anime_stats[anime_stats['anime_id'] == anime_id].iloc[0]
                recommendations.append({
                    "anime_id": int(anime_id),
                    "name": anime_row.get("eng_version", "Unknown"),
                    "score": float(anime_row.get("Score", 0)) if not pd.isna(anime_row.get("Score", 0)) else 0,
                    "genres": anime_row.get("Genres", "Unknown"),
                    "episodes": int(anime_row.get("Episodes", 0)) if not pd.isna(anime_row.get("Episodes", 0)) else 0,
                    "type": anime_row.get("Type", "Unknown"),
                    "avg_rating": float(anime_stat['avg_rating']),
                    "num_ratings": int(anime_stat['num_ratings'])
                })
        
        return {"recommendations": recommendations}
    
    except Exception as e:
        logger.error(f"Error getting popular anime: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting popular anime: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "model_loaded": "user_weights" in globals() and "anime_weights" in globals(),
        "data_loaded": "anime_df" in globals() and "rating_df" in globals(),
        "num_users": len(user2user_encoded) if "user2user_encoded" in globals() else 0,
        "num_anime": len(anime2anime_encoded) if "anime2anime_encoded" in globals() else 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
