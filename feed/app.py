import streamlit as st
import pandas as pd
from database import (
    init_db, add_post, get_posts, add_interaction, get_user_interactions, 
    get_likes_count, create_user, verify_user, get_user_profile, update_user_profile
)

# Initialize the database
init_db()

def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['post_id', 'user', 'content', 'timestamp'])  # Include post_id from database
    return df


def get_recommended_posts(user, num_recommendations=5):
    posts_df = load_posts_df()

    # Get the posts that the user has liked
    user_interactions = get_user_interactions(user)
    if not user_interactions:
        return pd.DataFrame()  # Return an empty DataFrame if no interactions
    
    # Get like counts for all posts
    like_counts = get_likes_count()
    like_counts_df = pd.DataFrame(like_counts, columns=['post_id', 'like_count'])

    # Filter out:
    # 1. Posts the user has already interacted with
    # 2. Posts created by the user themselves
    filtered_posts_df = posts_df[
        (~posts_df['post_id'].isin(user_interactions)) & 
        (posts_df['user'] != user)
    ]

    # Merge the like counts with the liked posts
    liked_posts_with_counts = filtered_posts_df.merge(like_counts_df, on='post_id', how='left')
    
    # Sort by the like count in descending order
    liked_posts_with_counts = liked_posts_with_counts.sort_values(by='like_count', ascending=False)
    
    # Return the top N recommended posts
    return liked_posts_with_counts.head(num_recommendations)

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

def login_user(username, password):
    if verify_user(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = None

# Authentication UI
if not st.session_state.logged_in:
    st.title("Welcome to the Recommender Testing Platform")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login_user(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            display_name = st.text_input("Display Name (optional)")
            bio = st.text_area("Bio (optional)")
            signup = st.form_submit_button("Sign Up")
            
            if signup:
                if create_user(new_username, new_password, display_name, bio):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already exists")

else:
    # Show logout button in sidebar
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state.username}")
        if st.button("Logout"):
            logout_user()
            st.rerun()
        
        # Profile section in sidebar
        st.subheader("Your Profile")
        profile = get_user_profile(st.session_state.username)
        if profile:
            with st.expander("Edit Profile"):
                with st.form("profile_form"):
                    new_display_name = st.text_input("Display Name", value=profile[1])
                    new_bio = st.text_area("Bio", value=profile[2])
                    if st.form_submit_button("Update Profile"):
                        update_user_profile(st.session_state.username, new_display_name, new_bio)
                        st.success("Profile updated!")
                        st.rerun()

    # Main app content
    st.title("Recommender Testing Platform")

    # Post creation
    with st.form("post_form"):
        content = st.text_area("What's on your mind?", max_chars=280)
        submit = st.form_submit_button("Post")

        if submit and content:
            add_post(st.session_state.username, content)
            st.success("Post added successfully!")

    # Display recommended posts
    st.subheader("Recommended Posts")
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

    # Show all posts
    st.subheader("All Posts")
    posts_df = load_posts_df()
    for _, row in posts_df.iterrows():
        st.markdown(f"**{row['user']}** at {row['timestamp']}")
        st.write(row['content'])
        
        if st.button(f"Like", key=f"like_all_{row['post_id']}"):
            add_interaction(st.session_state.username, row['post_id'], 'like')
            st.success("Post liked!")
            st.rerun()
        st.markdown("---")