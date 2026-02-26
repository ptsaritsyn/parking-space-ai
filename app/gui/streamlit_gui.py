import streamlit as st
from app.gui import _BaseGUI


class ChatGUI(_BaseGUI):
    def __init__(self, agent):
        self.agent = agent

    def string_to_stream(self, text):
        for char in text:
            yield char

    def _run(self):
        st.title("Parking Chatbot")

        if st.button("🗑️ Remove Chat"):
            st.session_state.chat_history = []
            st.rerun()

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg, is_user in st.session_state.chat_history:
            if is_user:
                with st.chat_message("user"):
                    st.markdown(msg)
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg)

        user_message = st.chat_input("Enter your question...")

        if user_message:
            st.session_state.chat_history.append((user_message, True))
            with st.chat_message("user"):
                st.markdown(user_message)

            response = self.agent.run(user_message)
            st.session_state.chat_history.append((response, False))
            with st.chat_message("assistant"):
                st.markdown(response)
