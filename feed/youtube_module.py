import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from typing import List, Dict, Optional

class YouTubeIntegration:
    def __init__(self, api_key: str):
        """Initialize YouTube API client"""
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_relevant_content(
        self, 
        user_aspirations: str, 
        max_results: int = 5
    ) -> pd.DataFrame:
        """
        Search YouTube for content relevant to user aspirations
        Returns DataFrame with standardized columns matching your existing schema
        """
        try:
            # Convert aspirations to search queries
            search_query = self._generate_search_query(user_aspirations)
            
            # Call YouTube API
            request = self.youtube.search().list(
                part="snippet",
                q=search_query,
                type="video",
                maxResults=max_results,
                relevanceLanguage="en",
                safeSearch="moderate"
            )
            response = request.execute()
            
            # Transform to DataFrame matching your schema
            videos = []
            for item in response['items']:
                video = {
                    'post_id': f"yt_{item['id']['videoId']}",  # Prefix to distinguish source
                    'user': item['snippet']['channelTitle'],
                    'content': f"{item['snippet']['title']}\n{item['snippet']['description']}\nWatch: https://youtube.com/watch?v={item['id']['videoId']}",
                    'timestamp': item['snippet']['publishedAt'],
                    'platform': 'youtube'  # Add platform identifier
                }
                videos.append(video)
            
            return pd.DataFrame(videos)
            
        except HttpError as e:
            print(f"YouTube API error: {str(e)}")
            return pd.DataFrame()
    
    def _generate_search_query(self, user_aspirations: str) -> str:
        """
        Convert user aspirations to relevant YouTube search queries
        You can enhance this with your existing GPT-4 logic
        """
        # Basic implementation - you can enhance with GPT-4
        return user_aspirations.replace('\n', ' OR ')

def get_mixed_recommendations(
    username: str,
    user_aspirations: str,
    platform_posts_df: pd.DataFrame,
    youtube_api_key: str,
    num_recommendations: int = 5
) -> pd.DataFrame:
    """
    Get mixed recommendations from both platform and YouTube
    """
    try:
        # Initialize YouTube integration
        yt = YouTubeIntegration(youtube_api_key)
        
        # Get YouTube recommendations
        youtube_recommendations = yt.search_relevant_content(
            user_aspirations=user_aspirations,
            max_results=num_recommendations
        )
        
        # Add platform column to original posts
        platform_posts_df['platform'] = 'platform'
        
        # Combine recommendations
        all_recommendations = pd.concat(
            [platform_posts_df, youtube_recommendations],
            ignore_index=True
        )
        
        # Sort by relevance/timestamp (you can enhance this)
        all_recommendations = all_recommendations.sort_values('timestamp', ascending=False)
        
        return all_recommendations.head(num_recommendations)
        
    except Exception as e:
        print(f"Error getting mixed recommendations: {str(e)}")
        return platform_posts_df  # Fallback to platform-only recommendations