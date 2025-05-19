from config.paths_config import *
from utils.helpers import *
import numpy as np

def hybrid_recommendation(user_id, user_weight=0.5, content_weight=0.5):
    """Hybrid recommendation system that combines user-based and content-based filtering"""
    
    try:
        ## User Recommendation
        # Fix for find_similar_users
        user_weights = joblib.load(USER_WEIGHTS_PATH)
        user2user_encoded = joblib.load(USER2USER_ENCODED)
        user2user_decoded = joblib.load(USER2USER_DECODED)
        
        try:
            encoded_index = user2user_encoded.get(user_id)
            if encoded_index is None:
                print(f"User ID {user_id} not found in encoded mapping")
                return []
                
            # FIX: Ensure weights[encoded_index] is 1D for dot product
            user_vector = user_weights[encoded_index]
            if len(user_vector.shape) > 1:  # If it has extra dimensions
                user_vector = user_vector.reshape(-1)  # Flatten to 1D
                
            dists = np.dot(user_weights, user_vector)
            
            # Continue with the rest of the similar users logic
            sorted_dists = np.argsort(dists)
            n = 11  # n+1 as in the original function
            closest = sorted_dists[-n:]
            
            SimilarityArr = []
            for close in closest:
                similarity = dists[close]
                if isinstance(user_id, int):
                    decoded_id = user2user_decoded.get(close)
                    SimilarityArr.append({
                        "similar_users": decoded_id,
                        "similarity": similarity
                    })
            
            similar_users = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)
            similar_users = similar_users[similar_users.similar_users != user_id]
            
        except Exception as e:
            print(f"Error in finding similar users: {str(e)}")
            return []
            
        # Get user preferences and recommendations
        user_pref = get_user_preferences(user_id, RATING_DF, DF)
        user_recommended_animes = get_user_recommendations(similar_users, user_pref, DF, SYNOPSIS_DF, RATING_DF)
        
        user_recommended_anime_list = user_recommended_animes["anime_name"].tolist()
        
        #### Content recommendation
        content_recommended_animes = []
        
        for anime in user_recommended_anime_list:
            try:
                similar_animes = find_similar_animes(anime, ANIME_WEIGHTS_PATH, ANIME2ANIME_ENCODED, ANIME2ANIME_DECODED, DF)
                
                if similar_animes is not None and not similar_animes.empty:
                    content_recommended_animes.extend(similar_animes["name"].tolist())
                else:
                    print(f"No similar anime found {anime}")
            except Exception as e:
                print(f"Error finding similar anime for {anime}: {str(e)}")
                # Continue to the next anime instead of failing
                continue
        
        combined_scores = {}
        
        for anime in user_recommended_anime_list:
            combined_scores[anime] = combined_scores.get(anime, 0) + user_weight
        
        for anime in content_recommended_animes:
            combined_scores[anime] = combined_scores.get(anime, 0) + content_weight
        
        sorted_animes = sorted(combined_scores.items(), key=lambda x:x[1], reverse=True)
        
        return [anime for anime, score in sorted_animes[:10]]
    
    except Exception as e:
        print(f"Error in hybrid_recommendation: {str(e)}")
        # Return a default/fallback recommendation or empty list
        return []
