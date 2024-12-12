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

# Load environment variables
load_dotenv(override=True)  # Add override=True to ensure variables are reloaded

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

# Check if API key is in Streamlit secrets
if not api_key and 'OPENAI_API_KEY' in st.secrets:
    api_key = st.secrets['OPENAI_API_KEY']

# Final check and client initialization
if not api_key:
    st.error("OpenAI API key not found. Please check your .env file or Streamlit secrets.")
    st.stop()

# Initialize OpenAI client at the module level
client = OpenAI(api_key=api_key)


def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['post_id', 'user', 'content', 'timestamp'])
    return df


def infer_aspirations_from_bio(username, user_bio): 
    """
    Infer information from bio
    """
    
    system_prompt = """You are an experienced life coach who works with clients to support them in their journeys to manifest their live goals.
    Your task is to identify aspirational goals from the information your clients give you."""

    user_prompt = f"""Based on this user's bio: identify aspirational goals.

User: {username if username else 'No bio provided'}
User Bio: {user_bio if user_bio else 'No bio provided'}"""

    try:
        # Verify API key is set
        if not os.getenv('OPENAI_API_KEY'):
            print("OpenAI API key is not set!")
            return pd.DataFrame()
            
        response = client.chat.completions.create(
            model = "gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt}
                    ]
                }
            ],
            max_tokens=2000
        )      
    
        # Get the reponse content
        user_aspirations = response.choices[0].message.content
        print(f"GPT-4o response: {user_aspirations}")
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

def get_recommended_posts(username, num_recommendations=5):
    """
    Get recommended posts for a user.
    """
    # Load all posts
    posts_df = load_posts_df()
    print(f"Total posts loaded: {len(posts_df)}")
    
    # Get user profile to access bio
    conn = sqlite3.connect('newsfeed.db')
    c = conn.cursor()
    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        print(f"No user profile found for username: {username}")
        return pd.DataFrame()
        
    user_bio = result[0]
    print(f"Retrieved user bio: {user_bio}")
    
    # Define user aspiration

    user_aspirations = infer_aspirations_from_bio(
        username=username,
        user_bio=user_bio
    )

    # Get LLM recommendations
    recommended_posts = get_llm_recommended_posts(
        username=username,
        user_aspirations=user_aspirations,
        user_bio=user_bio,
        posts_df=posts_df,
        num_recommendations=num_recommendations
    )
    
    if recommended_posts.empty:
        print("No recommendations returned from LLM")
        return pd.DataFrame()
    
    # Get like counts for recommended posts
    like_counts = get_likes_count()
    like_counts_df = pd.DataFrame(like_counts, columns=['post_id', 'like_count'])
    
    # Merge recommendations with like counts
    final_recommendations = recommended_posts.merge(
        like_counts_df, 
        on='post_id', 
        how='left'
    )
    
    # Fill NaN like counts with 0
    final_recommendations['like_count'] = final_recommendations['like_count'].fillna(0)
    
    return final_recommendations

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("Please log in to access this page.")
    st.stop()

st.title("Recommendations")

# Display recommended posts
recommended_posts = get_recommended_posts(st.session_state.username)

if not recommended_posts.empty:
    for _, row in recommended_posts.iterrows():
        st.markdown(f"**{row['user']}** at {row['timestamp']}")
        st.write(row['content'])
        st.markdown(f"👍 {row['like_count']} likes")
        
        if st.button(f"Like", key=f"like_{row['post_id']}"):
            add_interaction(st.session_state.username, row['post_id'], 'like')
            st.success("Post liked!")
            st.rerun()
        st.markdown("---")
else:
    st.info("No recommendations available. Try liking some posts!")