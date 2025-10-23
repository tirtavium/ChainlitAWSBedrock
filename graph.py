import argparse
from langgraph.graph import StateGraph, MessagesState
#from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import MemorySaver
from utils import save_graph_to_file, convert_pdf_to_markdown, upload_markdown_and_sync_kb, detect_github_url, convert_github_repo_to_markdown
from langchain_aws.agents import BedrockAgentsRunnable
import chainlit as cl
import asyncio



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


# Helper function to send loading message
async def send_loading_message(message: str):
    """Send a loading message to Chainlit UI"""
    try:
        msg = cl.Message(content=message)
        await msg.send()
    except Exception as e:
        print(f"Could not send loading message: {e}")

# Define the function that generates the assistant response
# def generate_answer(state: MessagesState):
#     return {"messages": [model.invoke(state["messages"])]}
# --- Node function ---
def generate_answer(state: MessagesState):
    user_messages = state["messages"]
    last_message = user_messages[-1]
    
    # Check for PDF files in the message and convert to markdown
    pdf_markdown_content = []
    
    # Check for GitHub URLs in the message and convert to markdown
    github_markdown_content = []
    
   
    if hasattr(last_message, 'additional_kwargs') and 'files' in last_message.additional_kwargs:
        files = last_message.additional_kwargs['files']
        for file_info in files:
            if isinstance(file_info, dict) and 'path' in file_info:
                file_path = file_info['path']
                if file_path.lower().endswith('.pdf'):
                        print(f">> Detected PDF file: {file_path}")
                        markdown_text = convert_pdf_to_markdown(file_path)
                        if markdown_text:
                            file_name = file_info.get('name', 'Unknown PDF')
                            pdf_markdown_content.append({
                                'file_name': file_name,
                                'content': markdown_text
                            })
                            print(f">> PDF converted to markdown: {file_name}")
                            
                            # Upload markdown to S3 and sync knowledge base only if message contains save keywords
                            message_lower = last_message.content.lower() if last_message.content else ""
                            if "save" in message_lower or "save file" in message_lower:
                                knowledge_base_id = 'KALBYLJM4N'
                                data_source_id = 'DFG01BWHSR'
                                print(f">> 'Save file' detected - uploading to S3 and syncing knowledge base")
                                result = upload_markdown_and_sync_kb(
                                    markdown_text, 
                                    file_name, 
                                    knowledge_base_id, 
                                    data_source_id
                                )
                                if result:
                                    print(f">> Successfully uploaded and synced: {result['s3_uri']}")
                                    return {"messages": [ f"Successfully uploaded and synced: {result['s3_uri']}"]}
                                else:
                                    print(f">> Warning: Upload/sync failed for {file_name}")
                                    return {"messages": [ f"Failed to upload and sync: {file_name}"]}
                            else:
                                print(f">> PDF converted but not saved (no 'save file' keyword in message)")
    
    # Check for GitHub URLs in the message content
    message_content_text = last_message.content if last_message.content else ""
    github_urls = detect_github_url(message_content_text)
    
    if github_urls:
        print(f">> Detected {len(github_urls)} GitHub URL(s): {github_urls}")
        for repo_url in github_urls:
            print(f">> Processing GitHub repository: {repo_url}")
            markdown_text = convert_github_repo_to_markdown(repo_url)
            if markdown_text:
                repo_name = repo_url.split('/')[-1]
                github_markdown_content.append({
                    'repo_name': repo_name,
                    'repo_url': repo_url,
                    'content': markdown_text
                })
                print(f">> GitHub repository converted to markdown: {repo_name}")
                
                # Upload markdown to S3 and sync knowledge base if save keywords are present
                message_lower = message_content_text.lower()
                if "save" in message_lower or "save file" in message_lower or "save repo" in message_lower or "save the repo" in message_lower:
                    knowledge_base_id = 'KALBYLJM4N'
                    data_source_id = 'XCXWMKTBNA'
                    # Use different S3 bucket for GitHub repositories
                    github_bucket = 'ai-agent-knowlege-code-repository'
                    print(f">> 'Save' keyword detected - uploading to S3 bucket: {github_bucket}")
                    
    
                    result = upload_markdown_and_sync_kb(
                        markdown_text, 
                        f"{repo_name}.md", 
                        knowledge_base_id, 
                        data_source_id,
                        bucket_name=github_bucket
                    )
                    if result:
                        print(f">> Successfully uploaded and synced: {result['s3_uri']}")
                        return {"messages": [ f"Successfully uploaded and synced: {result['s3_uri']}"]}
                    else:
                        print(f">> Warning: Upload/sync failed for {repo_name}")
                        return {"messages": [ f"Failed to upload and sync: {repo_name}"]}
                else:
                    print(f">> GitHub repo converted but not saved (no 'save' keyword in message)")
            else:
                print(f">> Warning: Failed to convert GitHub repository: {repo_url}")

    # invoke agent with conversation history
    print(">> Sending to Bedrock:", repr(user_messages))
    print(">> Sending to Bedrock:", repr(last_message.content))
    print(">> Sending to Bedrock:", repr(last_message.id))
    
    # Add PDF markdown content to the message if PDFs were converted
    message_content = last_message.content
    if pdf_markdown_content:
        pdf_sections = []
        for pdf_data in pdf_markdown_content:
            pdf_section = f"\n\n--- Content from PDF: {pdf_data['file_name']} ---\n{pdf_data['content']}\n--- End of PDF content ---"
            pdf_sections.append(pdf_section)
        message_content = message_content + "".join(pdf_sections)
        print(f">> Added {len(pdf_markdown_content)} PDF(s) as markdown to the message")
    
    # Add GitHub repository markdown content to the message if repos were converted
    if github_markdown_content:
        github_sections = []
        for repo_data in github_markdown_content:
            github_section = f"\n\n--- Content from GitHub Repository: {repo_data['repo_name']} ({repo_data['repo_url']}) ---\n{repo_data['content']}\n--- End of GitHub repository content ---"
            github_sections.append(github_section)
        message_content = message_content + "".join(github_sections)
        print(f">> Added {len(github_markdown_content)} GitHub repo(s) as markdown to the message")
    
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