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

# Convert PDF to LLM-friendly markdown
def convert_pdf_to_markdown(file_path):
    """
    Convert a PDF file to LLM-friendly markdown using PyMuPDF4LLM
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        str: Markdown content of the PDF or None if conversion failed
    """
    try:
        import pymupdf4llm
        
        # Convert PDF to markdown
        md_text = pymupdf4llm.to_markdown(file_path)
        
        print(f"PDF converted to markdown successfully: {file_path}")
        print(f"Markdown length: {len(md_text)} characters")
        return md_text
        
    except ImportError:
        print("Error: pymupdf4llm is not installed. Install it with: pip install pymupdf4llm")
        return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error converting PDF to markdown: {e}")
        return None

# Upload markdown content to S3
def upload_markdown_to_s3(markdown_content, original_filename, bucket_name='ai-agent-knowledge-documents', profile_name='chatbot', region_name='us-east-1'):
    """
    Save markdown content to a file and upload to S3 bucket
    
    Args:
        markdown_content: The markdown text content
        original_filename: Original PDF filename (will be converted to .md)
        bucket_name: S3 bucket name (default: 'ai-agent-knowledge-documents')
        profile_name: AWS profile name (default: 'chatbot')
        region_name: AWS region (default: 'us-east-1')
    
    Returns:
        str: S3 URI of the uploaded file or None if upload failed
    """
    import boto3
    import os
    import tempfile
    from botocore.exceptions import ClientError
    
    try:
        # Create markdown filename from original PDF name
        base_name = os.path.splitext(original_filename)[0]
        md_filename = f"{base_name}.md"
        
        # Create temporary file to save markdown
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_file_path = temp_file.name
        
        # Create S3 client with profile
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        s3_client = session.client('s3')
        
        # Upload the markdown file
        s3_client.upload_file(temp_file_path, bucket_name, md_filename)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        s3_uri = f"s3://{bucket_name}/{md_filename}"
        print(f"Markdown uploaded successfully to {s3_uri}")
        return s3_uri
        
    except ClientError as e:
        print(f"Error uploading markdown to S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error uploading markdown: {e}")
        return None

# Upload markdown to S3 and sync Bedrock Knowledge Base (combined function)
def upload_markdown_and_sync_kb(markdown_content, original_filename, knowledge_base_id, data_source_id, 
                                  bucket_name='ai-agent-knowledge-documents', profile_name='chatbot', region_name='us-east-1'):
    """
    Upload markdown content to S3 and sync Bedrock Knowledge Base in one operation
    
    Args:
        markdown_content: The markdown text content
        original_filename: Original PDF filename (will be converted to .md)
        knowledge_base_id: The ID of the knowledge base
        data_source_id: The ID of the data source
        bucket_name: S3 bucket name (default: 'ai-agent-knowledge-documents')
        profile_name: AWS profile name (default: 'chatbot')
        region_name: AWS region (default: 'us-east-1')
    
    Returns:
        dict: {'s3_uri': str, 'sync_job': dict} or None if failed
    """
    import boto3
    import os
    import tempfile
    from botocore.exceptions import ClientError
    
    try:
        # Create markdown filename from original PDF name
        base_name = os.path.splitext(original_filename)[0]
        md_filename = f"{base_name}.md"
        
        # Create temporary file to save markdown
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_file_path = temp_file.name
        
        # Create session and clients
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        s3_client = session.client('s3')
        bedrock_agent_client = session.client('bedrock-agent')
        
        # Upload the markdown file to S3
        s3_client.upload_file(temp_file_path, bucket_name, md_filename)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        s3_uri = f"s3://{bucket_name}/{md_filename}"
        print(f"✓ Markdown uploaded to {s3_uri}")
        
        # Start ingestion job to sync knowledge base
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        ingestion_job = response.get('ingestionJob', {})
        job_id = ingestion_job.get('ingestionJobId', 'unknown')
        status = ingestion_job.get('status', 'unknown')
        
        print(f"✓ Knowledge base sync started - Job ID: {job_id}, Status: {status}")
        
        return {
            's3_uri': s3_uri,
            'sync_job': ingestion_job
        }
        
    except ClientError as e:
        print(f"Error uploading/syncing: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Sync Bedrock Knowledge Base
def sync_bedrock_knowledge_base(knowledge_base_id, data_source_id, profile_name='chatbot', region_name='us-east-1'):
    """
    Start an ingestion job to sync Bedrock Knowledge Base with S3 data source
    
    Args:
        knowledge_base_id: The ID of the knowledge base
        data_source_id: The ID of the data source (default: 'DFG01BWHSR')
        profile_name: AWS profile name (default: 'chatbot')
        region_name: AWS region (default: 'us-east-1')
    
    Returns:
        dict: Ingestion job details or None if sync failed
    """
    import boto3
    from botocore.exceptions import ClientError
    
    try:
        # Create Bedrock Agent client with profile
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        bedrock_agent_client = session.client('bedrock-agent')
        
        # Start ingestion job
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        ingestion_job = response.get('ingestionJob', {})
        job_id = ingestion_job.get('ingestionJobId', 'unknown')
        status = ingestion_job.get('status', 'unknown')
        
        print(f"Knowledge base sync started - Job ID: {job_id}, Status: {status}")
        return ingestion_job
        
    except ClientError as e:
        print(f"Error syncing Bedrock knowledge base: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error syncing knowledge base: {e}")
        return None