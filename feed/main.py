# main.py
import streamlit as st
from database import (
    init_db, create_user, verify_user, get_user_profile, update_user_profile
)

# Initialize the database
init_db()

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
    
    st.title("Recommender Testing Platform")
    st.write("Welcome! Please select a page from the sidebar to continue.")