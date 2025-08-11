import streamlit as st
from tool import get_diet_agent_chain

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Dietitian",
    page_icon="🍎",
    layout="centered"
)

# --- UI Setup ---
st.title("AI Dietitian 🍎")
st.caption("Your personal AI-powered nutrition guide")

# --- Sidebar for API Key Configuration ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Gemini API Key:", type="password", key="api_key_input")
    st.markdown(
        "Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)."
    )
    if api_key:
        st.success("API Key provided! You can now start chatting.")

# --- Session State Initialization ---
if "agent_chain" not in st.session_state:
    st.session_state.agent_chain = None
if "memory" not in st.session_state:
    st.session_state.memory = None
if "messages" not in st.session_state:
    # Start with a welcome message from the assistant
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm your AI Dietitian. To get started, please enter your Gemini API key in the sidebar. Then, tell me about your health goals!"
    }]

# --- Chat Avatars ---
avatars = {"user": "🧑‍💻", "assistant": "🩺"}

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=avatars.get(message["role"])):
        st.markdown(message["content"])

# --- Main Logic ---
# Only proceed if the API key is available
if api_key:
    # Initialize agent and memory if they haven't been already
    if st.session_state.agent_chain is None:
        try:
            st.session_state.agent_chain, st.session_state.memory = get_diet_agent_chain(api_key)
        except Exception as e:
            st.error(f"Failed to initialize the AI agent. Please check your API key and dependencies. Error: {e}")
            st.stop()
            
    # Handle user input
    if user_input := st.chat_input("Ask about your diet, meals, or health goals..."):
        # Add user message to session state and display it
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=avatars["user"]):
            st.markdown(user_input)

        # Get and display AI response
        with st.chat_message("assistant", avatar=avatars["assistant"]):
            with st.spinner("Thinking..."):
                chat_history = st.session_state.memory.load_memory_variables({})["chat_history"]
                
                response = st.session_state.agent_chain.invoke({
                    "chat_history": chat_history,
                    "input": user_input
                })
                
                ai_response = response.content
                
                # Update memory and display response
                st.session_state.memory.save_context({"input": user_input}, {"output": ai_response})
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.markdown(ai_response)
else:
    # Disable chat input if no API key is provided
    st.chat_input("Enter your API key in the sidebar to chat.", disabled=True)