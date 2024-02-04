import streamlit as st
from model import get_df_from_lease_dictionary
from dotenv import load_dotenv
load_dotenv()
def streamlit():
    # Get or create the session state dictionary
    if 'session_state' not in st.session_state:
        st.session_state['session_state'] = {}

    st.title('LLM Legal AI Chatbot')

    if 'chat' not in st.session_state['session_state']:
        st.session_state['session_state']['chat'], st.session_state['session_state']['lease_entries'] = get_df_from_lease_dictionary()

    # Retrieve the ChatAI object from the session state
    chat = st.session_state['session_state']['chat']
    if "lease_entries" in st.session_state['session_state']:
        st.sidebar.subheader("Lease Entries")
        st.sidebar.write("schedule_of_notices_of_lease_examples.json parsed successfully!")
        st.sidebar.write("Length of lease entries: " + str(len(st.session_state['session_state']['lease_entries'])))

        # Print the first 200 entries
        for i, entry in st.session_state['session_state']['lease_entries'].iterrows():
            if i > 200:
                break
            outer_box = st.sidebar.container()
            with outer_box:
                st.title(f"Schedule Lease Object {entry['page_num']} - {entry['entry_id']}")

                # Create an inner box inside the outer box
                inner_box = st.container()
                with inner_box:
                    st.caption("Registration Date and Plan Ref")
                    st.write(entry["registration_date_and_plan_ref"])
                    st.caption("Property Description")
                    st.write(entry["property_description"])
                    st.caption("Date of Lease and Term")
                    st.write(entry["date_of_lease_and_term"])
                    st.caption("Lessee's Title")
                    st.write(entry["lessees_title"])
                    st.caption("Notes")
                    st.write(entry["notes"])


    # Store LLM generated responses
    if "messages" not in st.session_state or st.sidebar.button("Clear conversation history"):
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # User-provided prompt
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat.run({"input": st.session_state.messages[-1]["content"]})
                st.write(response)

        # Add the response to the chat history if its has not been written
        message = {"role": "assistant", "content": response}
        st.session_state.messages.append(message)
streamlit()