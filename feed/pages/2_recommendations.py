# pages/2_recommendations.py

import streamlit as st
import pandas as pd
from database import (
    get_posts, add_interaction, get_user_interactions, 
    get_likes_count
)
import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import sqlite3
import tempfile
from st_audiorec import st_audiorec
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from functools import lru_cache



# Load environment variables
load_dotenv(override=True)

# Get API keys
openai_api_key = os.getenv('OPENAI_API_KEY')
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

# Check if API keys are in Streamlit secrets
if not openai_api_key and 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets['OPENAI_API_KEY']
if not youtube_api_key and 'YOUTUBE_API_KEY' in st.secrets:
    youtube_api_key = st.secrets['YOUTUBE_API_KEY']

# Final check and client initialization
if not openai_api_key:
    st.error("OpenAI API key not found. Please check your .env file or Streamlit secrets.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Initialize YouTube client if API key is available
youtube_client = None
if youtube_api_key:
    try:
        youtube_client = build('youtube', 'v3', developerKey=youtube_api_key)
    except Exception as e:
        print(f"Error initializing YouTube client: {str(e)}")

@lru_cache()
def get_youtube_client():
    """Initialize and return YouTube client with caching"""
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if not youtube_api_key and 'YOUTUBE_API_KEY' in st.secrets:
        youtube_api_key = st.secrets['YOUTUBE_API_KEY']
        
    if youtube_api_key:
        try:
            return build('youtube', 'v3', developerKey=youtube_api_key)
        except Exception as e:
            print(f"Error initializing YouTube client: {str(e)}")
            return None
    return None

def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['post_id', 'user', 'content', 'timestamp'])
    return df

def transcribe_audio(audio_data):
    """Transcribe audio using OpenAI Whisper API."""
    if audio_data is None:
        return None
        
    try:
        # Save audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name
            
        # Transcribe using OpenAI's Whisper
        with open(tmp_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
        # Clean up temporary file
        os.unlink(tmp_file_path)
        return transcript.text
        
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None

def infer_aspirations_from_bio(username, user_bio, audio_transcript=None):
    """Infer information from bio and audio transcript"""
    
    system_prompt = """You are an experienced life coach who works with clients to support them in their journeys to manifest their life goals.
    Your task is to identify aspirational goals from the information your clients give you, including both their written bio and their spoken feelings."""

    user_prompt = f"""Based on this client's biography and their recorded feelings, identify aspirational goals.

User: {username if username else 'No username provided'}
User Bio: {user_bio if user_bio else 'No bio provided'}
Today's Feelings: {audio_transcript if audio_transcript else 'No audio recording provided'}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000
        )
        
        user_aspirations = response.choices[0].message.content
        st.write(user_aspirations)
        print(f"")
        return user_aspirations
    
    except Exception as e:
        print(f"Error in LLM recommendation: {str(e)}")
        return None

def get_llm_recommended_posts(username, user_aspirations, user_bio, posts_df, num_recommendations=5):
    """
    Get post recommendations for a user based on their bio using GPT-4.
    """
    print(f"Starting LLM recommendations for user: {username}")
    print(f"User bio: {user_bio}")
    print(f"Total posts available before filtering: {len(posts_df)}")

    # Filter out user's own posts but keep original post numbers for reference
    posts_df['original_index'] = range(1, len(posts_df) + 1)  # 1-based index for GPT
    other_posts = posts_df[posts_df['user'] != username].copy()
    print(f"Posts after filtering out user's own posts: {len(other_posts)}")
    
    if other_posts.empty:
        print("No posts from other users found")
        return pd.DataFrame()
    
    # Prepare the prompt using original post numbers
    posts_context = "\n".join([
        f"Post {row['original_index']}: {row['content']}" 
        for _, row in other_posts.iterrows()
    ])
    
    system_prompt = """You are a recommendation system that analyzes user interests and content relevance. 
    Your task is to identify posts that would be most interesting to a user based on their bio and aspirations.
    You must return only the post numbers, separated by commas."""

    user_prompt = f"""Based on this user's bio and aspirations, select the {num_recommendations} most relevant posts that would interest them.
    
User Bio: {user_bio if user_bio else 'No bio provided'}
User Aspirations: {user_aspirations if user_aspirations else "No user aspirations inferred"}

Available Posts:
{posts_context}

Return only the post numbers of the {num_recommendations} most relevant posts, separated by commas.
For example: "1, 4, 7"
If there are fewer posts available than requested, return all available relevant posts."""

    try:
        # Verify API key is set
        if not os.getenv('OPENAI_API_KEY'):
            print("OpenAI API key is not set!")
            return pd.DataFrame()
            
        print("Calling GPT-4o API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000
        )
        
        # Get the response content
        response_content = response.choices[0].message.content
        print(f"GPT-4o response: {response_content}")
        
        # Parse the response to get recommended post numbers
        recommended_post_numbers = [
            int(idx.strip())
            for idx in response_content.replace(" ", "").split(",")
            if idx.strip().isdigit()
        ]
        
        print(f"Recommended post numbers: {recommended_post_numbers}")
        
        # Filter posts based on original_index
        recommended_posts = other_posts[other_posts['original_index'].isin(recommended_post_numbers)]
        print(f"Number of recommended posts: {len(recommended_posts)}")
        
        # Drop the temporary original_index column
        recommended_posts = recommended_posts.drop('original_index', axis=1)
        
        return recommended_posts
        
    except Exception as e:
        print(f"Error in LLM recommendation: {str(e)}")
        return pd.DataFrame()

def get_youtube_recommendations(user_aspirations, max_results=3):
    """Get relevant YouTube content based on user aspirations"""
    youtube_client = get_youtube_client()
    
    print(f"Debug - YouTube received aspirations: {user_aspirations}")  # Debug print
    
    if not youtube_client:
        print("YouTube client not initialized")
        return pd.DataFrame()
        
    try:
        # Extract key terms from aspirations for better search
        search_terms = [
            line.strip().split('.')[1].strip() 
            for line in user_aspirations.split('\n') 
            if line.strip() and '.' in line
        ]
        
        
        # Call YouTube API
        search_query = ' OR '.join(search_terms[:1])
        request = youtube_client.search().list(
            part="snippet",
            q=search_query,
            type="video",
            maxResults=max_results,
            relevanceLanguage="en",
            safeSearch="moderate"
        )
        response = request.execute()
        
        # Transform to DataFrame
        videos = []
        for item in response['items']:
            video = {
                'post_id': f"yt_{item['id']['videoId']}",
                'user': item['snippet']['channelTitle'],
                'content': (f"🎥 **{item['snippet']['title']}**\n\n"
                          f"{item['snippet']['description'][:200]}...\n\n"
                          f"📺 [Watch on YouTube](https://youtube.com/watch?v={item['id']['videoId']})"),
                'timestamp': item['snippet']['publishedAt'],
                'platform': 'youtube'
            }
            videos.append(video)
            
        return pd.DataFrame(videos)
        
    except Exception as e:
        print(f"Error in YouTube recommendations: {str(e)}")
        return pd.DataFrame()

def get_recommended_posts(username, num_recommendations=5, audio_transcript=None):
    """
    Get recommended posts for a user, including YouTube content and audio context
    """
    # Load all posts
    posts_df = load_posts_df()
    
    # Get user profile
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return pd.DataFrame()
        
    user_bio = result[0]
    
    # Get user aspirations with audio context and store it
    user_aspirations = infer_aspirations_from_bio(
        username=username,
        user_bio=user_bio,
        audio_transcript=audio_transcript
    )
    
    print(f"Debug - Initial user_aspirations: {user_aspirations}")  # Debug print
    
    # Get platform recommendations
    platform_recommendations = get_llm_recommended_posts(
        username=username,
        user_aspirations=user_aspirations,  # Pass the actual aspirations
        user_bio=user_bio,
        posts_df=posts_df,
        num_recommendations=max(2, num_recommendations - 3)
    )
    
    # Add platform identifier
    if not platform_recommendations.empty:
        platform_recommendations['platform'] = 'platform'
    
    print(f"Debug - Before YouTube recommendations - user_aspirations: {user_aspirations}")  # Debug print
    
    # Get YouTube recommendations with the same aspirations
    youtube_recommendations = get_youtube_recommendations(
        user_aspirations=user_aspirations,  # Pass the same aspirations
        max_results=min(3, num_recommendations - len(platform_recommendations))
    )
    
    # Combine recommendations
    all_recommendations = pd.concat(
        [platform_recommendations, youtube_recommendations],
        ignore_index=True
    )
    
    if all_recommendations.empty:
        return pd.DataFrame()
    
    # Add like counts for platform posts only
    like_counts = get_likes_count()
    like_counts_df = pd.DataFrame(like_counts, columns=['post_id', 'like_count'])
    
    final_recommendations = all_recommendations.merge(
        like_counts_df, 
        on='post_id', 
        how='left'
    )
    final_recommendations['like_count'] = final_recommendations['like_count'].fillna(0)
    
    return final_recommendations


# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("Please log in to access this page.")
    st.stop()

st.title("Recommendations")

# Initialize session state for audio
if 'audio_processed' not in st.session_state:
    st.session_state.audio_processed = False
if 'current_transcript' not in st.session_state:
    st.session_state.current_transcript = None

# Audio recording section
with st.expander("Share How You're Feeling (Optional)"):
    st.write("Recording your feelings can help us provide better recommendations!")
    wav_audio_data = st_audiorec()
    
    if wav_audio_data is not None:
        st.success("Audio recorded successfully!")
        st.audio(wav_audio_data, format='audio/wav')
        
        st.write("Transcribing audio...")
        transcript = transcribe_audio(wav_audio_data)
        if transcript:
            st.session_state.current_transcript = transcript
            st.success(f"Transcription: {transcript}")
        else:
            st.error("Transcription failed")
    else:
        st.session_state.current_transcript = None

# Get Recommendations button
if st.button("Get Recommendations"):
    recommended_posts = get_recommended_posts(
        st.session_state.username,
        audio_transcript=st.session_state.get('current_transcript')
    )

    if not recommended_posts.empty:
        for _, row in recommended_posts.iterrows():
            # Display platform-specific header
            if row['platform'] == 'youtube':
                st.markdown(f"🎥 **{row['user']}** on YouTube at {row['timestamp']}")
            else:
                st.markdown(f"**{row['user']}** at {row['timestamp']}")
            
            st.write(row['content'])
            
            # Only show like button for platform posts
            if row['platform'] == 'platform':
                st.markdown(f"👍 {row['like_count']} likes")
                if st.button(f"Like", key=f"like_{row['post_id']}"):
                    add_interaction(st.session_state.username, row['post_id'], 'like')
                    st.success("Post liked!")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No recommendations available at the moment. Try updating your profile or interacting with more posts!")