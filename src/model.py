import os
import pandas as pd
from itertools import chain
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory, ConversationKGMemory, \
    CombinedMemory
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from parse_data import paginate_json_file, PAGE_SIZE
from dotenv import load_dotenv

load_dotenv()

OPEN_API_KEY = os.getenv("OPEN_API_KEY")

def get_df_from_lease_dictionary() -> (AgentExecutor, pd.DataFrame):
    """
    Get a Pandas DataFrame from the lease dictionary
    :return:
    """
    full_lease_dictionary = paginate_json_file('src/schedule_of_notices_of_lease_examples.json', PAGE_SIZE)
    leases_flattened = list(chain(*[lease for lease_schedule in full_lease_dictionary.values() for lease in lease_schedule.values()]))
    lease_entries_dict_list = [entry.__dict__ for entry in leases_flattened]

    # Convert the list of dictionaries to a Pandas DataFrame
    df = pd.DataFrame(lease_entries_dict_list)
    return get_ai_model(df), df


def get_ai_model(df: pd.DataFrame) -> AgentExecutor:
    """
    Initialize the AI model with the Pandas DataFrame, the prompt and the chat history
    :param df:
    :return:
    """
    llm = ChatOpenAI(
        temperature=0, model="gpt-4", openai_api_key=OPEN_API_KEY
    )

    prefix = """
    You are working with a pandas dataframe in Python. The name of the dataframe is `df`, use this if needed.
    You have a dataset containing information on real estate sub leases with the following columns:
    [registration_date_and_plan_ref, property_description, date_of_lease_and_term, lessees_title, notes]
    
    Summary of the whole conversation:
    {chat_history_summary}

    Last few messages between you and user:
    {chat_history_buffer}

    Entities that the conversation is about:
    {chat_history_kg}
    """

    chat_history_buffer = ConversationBufferWindowMemory(
        k=5,
        memory_key="chat_history_buffer",
        input_key="input"
    )

    chat_history_summary = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history_summary",
        input_key="input"
    )

    chat_history_kg = ConversationKGMemory(
        llm=llm,
        memory_key="chat_history_kg",
        input_key="input",
    )

    memory = CombinedMemory(memories=[chat_history_buffer, chat_history_summary, chat_history_kg])

    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        prefix=prefix,
        agent_executor_kwargs={"memory": memory, "handle_parsing_errors":_handle_error},
        input_variables=['df_head', 'agent_scratchpad', 'chat_history_buffer', 'chat_history_summary',
                         'chat_history_kg'],
    )


def _handle_error(error) -> str:
    return str(error)