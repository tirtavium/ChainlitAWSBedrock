import chainlit as cl
from graph import flow  # Import the compiled LangGraph workflow
from chainlit.input_widget import Select, Switch, Slider
from langchain_core.messages import HumanMessage

# Define the starters
@cl.set_starters
def set_starters():
    return [
        cl.Starter(
            label="What I need to do in first 5 days",
            message="Give me the process of on boarding employee in first 5 days.",
            icon="/public/idea.svg"
        ),
        cl.Starter(
            label="How to create new REST API in bank project?",
            message="How to create new REST API in account service bank account provide link.",
            icon="/public/idea.svg"
        ),
        cl.Starter(
            label="How to create new requirement in bank project",
            message="Explain how to create new story in Jira.",
            icon="/public/idea.svg"
        )
    ]

@cl.on_message
async def main(message: cl.Message):

    # Invoke the LangGraph flow to get the assistant's response
    thread_id = cl.user_session.get("id")
    config = {"configurable": {"thread_id": thread_id }}
    
    # Create input message with file attachments if present
    additional_kwargs = {}
    if message.elements:
        files = []
        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                files.append({
                    'path': element.path,
                    'name': element.name if hasattr(element, 'name') else None,
                    'mime': element.mime if hasattr(element, 'mime') else None
                })
        if files:
            additional_kwargs['files'] = files
    
    input_message = HumanMessage(content=message.content, additional_kwargs=additional_kwargs)
    final_state = flow.invoke({"messages" : [input_message]}, config)
    content = final_state["messages"][-1].content

    # Send a response back to the user
    await cl.Message(
        content
    ).send()