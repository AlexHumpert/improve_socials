# pages/2_recommendations.py
import streamlit as st
import pandas as pd
from database import (
    get_posts, add_interaction, get_user_interactions, 
    get_likes_count
)

def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['post_id', 'user', 'content', 'timestamp'])
    return df

def get_recommended_posts(user, num_recommendations=5):
    posts_df = load_posts_df()

    # Get the posts that the user has liked
    user_interactions = get_user_interactions(user)
    if not user_interactions:
        return pd.DataFrame()
    
    # Get like counts for all posts
    like_counts = get_likes_count()
    like_counts_df = pd.DataFrame(like_counts, columns=['post_id', 'like_count'])

    # Filter out posts the user has interacted with and their own posts
    filtered_posts_df = posts_df[
        (~posts_df['post_id'].isin(user_interactions)) & 
        (posts_df['user'] != user)
    ]

    # Merge the like counts with the filtered posts
    liked_posts_with_counts = filtered_posts_df.merge(like_counts_df, on='post_id', how='left')
    
    # Sort by the like count in descending order
    liked_posts_with_counts = liked_posts_with_counts.sort_values(by='like_count', ascending=False)
    
    return liked_posts_with_counts.head(num_recommendations)

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