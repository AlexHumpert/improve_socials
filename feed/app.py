import streamlit as st
import pandas as pd
from database import init_db, add_post, get_posts, add_interaction, get_user_interactions 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the database
init_db()

st.title("Simple Newsfeed")

# Form to add a new post
with st.form("post_form"):
    user = st.text_input("Name", max_chars=20)
    content = st.text_area("What's on your mind?", max_chars=280)
    submit = st.form_submit_button("Post")

    if submit and user and content:
        add_post(user, content)
        st.success("Post added successfully!")

st.subheader("Newsfeed")
posts = get_posts()

# Display posts
if posts:
    for user, content, timestamp in posts:
        st.markdown(f"**{user}** at {timestamp}")
        st.write(content)
        st.markdown("---")
else:
    st.info("No posts yet. Be the first to share!")


# Personalized Newsfeed Section
st.title("Personalized Newsfeed")

user = st.text_input("Enter your username", max_chars=20)

# Load all posts
def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['user', 'content', 'timestamp'])
    return df

# Calculate similarity using TF-IDF
def get_recommended_posts(user, num_recommendations=5):
    posts_df = load_posts_df()
    
    # Fetch posts that the user has interacted with
    user_interactions = get_user_interactions(user)
    if not user_interactions:
        return posts_df  # Return all posts if no interactions

    # Use TF-IDF to vectorize post content
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(posts_df['content'])
    
    # Calculate cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Get indices of posts the user interacted with
    interacted_indices = [posts_df.index[posts_df['content'].eq(content)].tolist()[0]
                          for content in posts_df.loc[user_interactions, 'content']]
    
    # Calculate average similarity scores for posts
    scores = similarity_matrix[interacted_indices].mean(axis=0)
    posts_df['similarity_score'] = scores

    # Sort by similarity score and return top recommendations
    recommended_posts = posts_df.sort_values(by='similarity_score', ascending=False)
    return recommended_posts.head(num_recommendations)

# Display recommended posts
if user:
    st.subheader("Recommended for you")
    recommended_posts = get_recommended_posts(user)
    for _, row in recommended_posts.iterrows():
        st.markdown(f"**{row['user']}** at {row['timestamp']}")
        st.write(row['content'])
        st.markdown("---")