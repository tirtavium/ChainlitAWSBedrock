import argparse
from langgraph.graph import StateGraph, MessagesState
#from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import MemorySaver
from utils import save_graph_to_file, upload_pdf_to_s3
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
    agent_id="XZUYJQWY92",
    agent_alias_id="EZMNLUBFHR",
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
    last_message = user_messages[-1]
    
    # Check for PDF files in the message
    pdf_s3_uris = []
    if hasattr(last_message, 'additional_kwargs') and 'files' in last_message.additional_kwargs:
        files = last_message.additional_kwargs['files']
        for file_info in files:
            if isinstance(file_info, dict) and 'path' in file_info:
                file_path = file_info['path']
                if file_path.lower().endswith('.pdf'):
                    print(f">> Detected PDF file: {file_path}")
                    s3_uri = upload_pdf_to_s3(file_path)
                    if s3_uri:
                        pdf_s3_uris.append(s3_uri)
    
    # invoke agent with conversation history
    print(">> Sending to Bedrock:", repr(user_messages))
    print(">> Sending to Bedrock:", repr(last_message.content))
    print(">> Sending to Bedrock:", repr(last_message.id))
    
    # Add PDF upload info to the message content if PDFs were uploaded
    message_content = last_message.content
    if pdf_s3_uris:
        pdf_info = "\n\n[PDFs uploaded to S3: " + ", ".join(pdf_s3_uris) + "]"
        message_content = message_content + pdf_info
        print(f">> PDFs uploaded: {pdf_s3_uris}")
    
    response = model.invoke({"input": message_content})
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