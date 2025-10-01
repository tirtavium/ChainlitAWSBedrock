import argparse
from langgraph.graph import StateGraph, MessagesState
#from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import MemorySaver
from utils import save_graph_to_file
from langchain_aws.agents import BedrockAgentsRunnable



# Create the memory checkpointer
memory = MemorySaver()

# Create the model
# model = ChatBedrockConverse(
#     model="anthropic.claude-3-5-sonnet-20240620-v1:0",
#     temperature=0,
#     max_tokens=None,
#     region_name="us-east-1",
#     credentials_profile_name="chatbot"
# )

import boto3

#client = boto3.client("bedrock-agent-runtime", region_name="us-east-1", profile_name="chatbot")

# Create a session with your profile
session = boto3.Session(profile_name="chatbot", region_name="us-east-1")

# Use that session to create the client
client = session.client("bedrock-agent-runtime")

model = BedrockAgentsRunnable(
    agent_id="0DVHAFVMSI",
    agent_alias_id="EJ8UDKFOR8",
    client=client
)


# model = BedrockAgentsRunnable(
#     agent_id="0DVHAFVMSI",
#     agent_alias_id="EJ8UDKFOR8",
#     region_name="us-east-1",              # your region
#     credentials_profile_name="chatbot"    # AWS profile with Bedrock permissions
# )


# Define the function that generates the assistant response
# def generate_answer(state: MessagesState):
#     return {"messages": [model.invoke(state["messages"])]}
# --- Node function ---
def generate_answer(state: MessagesState):
    user_messages = state["messages"]
    # invoke agent with conversation history
    print(">> Sending to Bedrock:", repr(user_messages))
    print(">> Sending to Bedrock:", repr(user_messages[-1].content))
    print(">> Sending to Bedrock:", repr(user_messages[-1].id))
    response = model.invoke({"input":user_messages[-1].content})
    #response2 = model.invoke(state["messages"])
    print("<< Received from Bedrock:", repr(response))
    #print("<< Received from Bedrock:", repr(response2))
    if hasattr(response, "return_values") and "output" in response.return_values:
        output_text = response.return_values["output"]
    else:
        output_text = str(response)
    return {"messages": [output_text]}

# Initialize the LangGraph workflow
chatbot_graph = StateGraph(MessagesState)

# Add a node that generates an answer
chatbot_graph.add_node("response", generate_answer)

# Define the flow: Start at "response" and then end
chatbot_graph.set_entry_point("response")
chatbot_graph.set_finish_point("response")

# Compile the graph
flow = chatbot_graph.compile(checkpointer=memory)

# if __name__ == "__main__":
#     # Set up command-line argument parsing
#     parser = argparse.ArgumentParser(description="Save chatbot graph to file")
#     parser.add_argument(
#         "file_path", 
#         type=str, 
#         help="The file path to save the graph image (e.g., 'graph.png')"
#     )
#     parser.add_argument(
#         "--format", 
#         type=str, 
#         default="png", 
#         choices=["png", "svg"], 
#         help="The format of the image file (default is 'png')"
#     )

#     # Parse command-line arguments
#     args = parser.parse_args()

#     # Save the graph to the specified file
#     save_graph_to_file(flow, args.file_path, format=args.format)


# aws bedrock-agent-runtime invoke-agent \
#     --agent-id 0DVHAFVMSI \
#     --agent-alias-id TEJ8UDKFOR8EST \
#     --session-id my-test-session-123 \
#     --input-text "What is the capital of France?"