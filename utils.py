from IPython.display import Image, display
import warnings

# save a graph to a file
def save_graph_to_file(graph, file_path, format='png'):
    try:
        # Normalize to lowercase for both file extension and format
        format = format.lower()
        file_extension = file_path.split('.')[-1].lower()

        # Only raise a warning if the normalized file extension doesn't match the format
        if file_extension != format:
            warnings.warn(f"File extension '{file_extension}' does not match the specified format '{format}'. Saving as {format} anyway.")
        
        with open(file_path, 'wb') as file:
            if format == 'png':
                file.write(graph.get_graph().draw_mermaid_png())
            elif format == 'svg':
                file.write(graph.get_graph().draw_mermaid_svg())
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        print(f"Graph saved successfully at {file_path}")
    except Exception as e:
        print(f"Error saving graph: {e}")

# display the image in a Jupyter Notebook
def show_graph(graph):
    try:
        display(Image(graph.get_graph().draw_mermaid_png()))
    except Exception as e:
        print(f"Error displaying graph: {e}")

# Upload PDF file to S3
def upload_pdf_to_s3(file_path, bucket_name='ai-agent-knowledge-documents', profile_name='chatbot', region_name='us-east-1'):
    """
    Upload a PDF file to S3 bucket
    
    Args:
        file_path: Path to the PDF file
        bucket_name: S3 bucket name (default: 'ai-agent-knowledge-documents')
        profile_name: AWS profile name (default: 'chatbot')
        region_name: AWS region (default: 'us-east-1')
    
    Returns:
        str: S3 URI of the uploaded file or None if upload failed
    """
    import boto3
    import os
    from botocore.exceptions import ClientError
    
    try:
        # Create S3 client with profile
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        s3_client = session.client('s3')
        
        # Get the file name from the path
        file_name = os.path.basename(file_path)
        
        # Upload the file
        s3_client.upload_file(file_path, bucket_name, file_name)
        
        s3_uri = f"s3://{bucket_name}/{file_name}"
        print(f"PDF uploaded successfully to {s3_uri}")
        return s3_uri
        
    except ClientError as e:
        print(f"Error uploading PDF to S3: {e}")
        return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Unexpected error uploading PDF: {e}")
        return None