import os
import json
import boto3
from dotenv import load_dotenv
import strands
from src.rag.visual_grounding_helper import (
    extract_chunk_id_from_markdown,
    extract_chunk_image 
)
_ = load_dotenv()

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
s3_client = session.client("s3")


@strands.tool
def search_knowledge_base(query: str) -> str:
    """Search the Bedrock knowledge base for relevant budget documents with visual grounding."""
    try:
        kb_id = os.getenv("BEDROCK_KB_ID")  
        bucket = os.getenv("S3_BUCKET")
        if not kb_id:
            return "Error: Knowledge base ID not configured. Please set BEDROCK_KB_ID environment variable."

        bedrock_agent_runtime = session.client("bedrock-agent-runtime")
        
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                    "overrideSearchType": "HYBRID"  
                }
            }
        )
        
        raw_results = response.get("retrievalResults", [])
        sorted_results = sorted(raw_results, key=lambda x: x.get("score", 0), reverse=True)
        
        results = []
        seen_chunk_ids = set()  

        # 2. For each result, get the location and check if this is a chunk JSON file from budget_chunks folder
        for result in sorted_results:
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            location = result.get("location", {})
            
            s3_location = location.get("s3Location", {})
            source_uri = s3_location.get("uri", "")
            source_file = source_uri.split("/")[-1] if source_uri else "Unknown source"
            
            chunk_id = None
            visual_info = None
            cropped_image_url = None
            chunk_type = "text"
            page = None
            bbox = None
            source_document = None
            
            if source_file.endswith('.json') and 'chunks' in source_uri:
                try:
                    chunk_key = source_uri.replace(f"s3://{bucket}/", "")
                    chunk_response = s3_client.get_object(Bucket=bucket, Key=chunk_key)
                    chunk_data = json.loads(chunk_response['Body'].read().decode('utf-8'))
                    
                    chunk_id = chunk_data.get('chunk_id', '')
                    chunk_type = chunk_data.get('chunk_type', 'text')
                    page = chunk_data.get('page', 0)
                    bbox = chunk_data.get('bbox', [0, 0, 1, 1])
                    source_document = chunk_data.get('source_document', '')
                    
                    text = chunk_data.get('text', content)
                    
                    if chunk_id and chunk_id in seen_chunk_ids:
                        continue
                    seen_chunk_ids.add(chunk_id)
                    
                    # Generate cropped chunk image
                    if chunk_id and source_document:
                        source_pdf_key = f"input/gov_data/{source_document}.pdf"
                        try:
                            s3_client.head_object(Bucket=bucket, Key=source_pdf_key)
                            cropped_image_url = extract_chunk_image(
                                s3_client=s3_client,
                                bucket=bucket,
                                source_pdf_key=source_pdf_key,
                                bbox=bbox,
                                page_num=page,
                                chunk_id=chunk_id,
                                source_document=source_document,
                                highlight=True,
                                padding=10
                            )
                        except:
                            pass  
                            
                except Exception as e:
                    pass
            else:
                # Not a chunk file, try to extract chunk ID from markdown
                chunk_id = extract_chunk_id_from_markdown(content)
                if chunk_id and chunk_id in seen_chunk_ids:
                    continue
                if chunk_id:
                    seen_chunk_ids.add(chunk_id)
            
            if cropped_image_url and chunk_id and page is not None:
                result_text = f"""
                **Source:** {source_document or source_file} (Relevance: {score:.2f})
                **Chunk ID:** {chunk_id}
                **Page:** {page}
                **Chunk Type:** {chunk_type}
                **Cropped Chunk Image:** {cropped_image_url}
                
                **Content:**
                {content}"""
                results.append(result_text)
            elif chunk_id and page is not None:
                # Partial visual info (no image but has metadata)
                result_text = f"""
                **Source:** {source_document or source_file} (Relevance: {score:.2f})
                **Chunk ID:** {chunk_id}
                **Page:** {page}
                **Chunk Type:** {chunk_type}
                **Bbox:** {bbox if bbox else 'Not available'}
                
                **Content:**
                {content}"""
                results.append(result_text)
            else:
                # No visual grounding available - use content hash as unique ID
                content_hash = hash(content[:200])  # Hash first 200 chars for uniqueness
                if content_hash in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(content_hash)
                
                clean_source = source_file.replace('_grounding.json', '').replace('.json', '').replace('.md', '')
                result_text = f"""**Source:** {clean_source} (Relevance: {score:.2f})
                                **Content:**{content}"""
                results.append(result_text)
        
        if results:
            # Return only top 2 most relevant results with visual references
            return "\n\n---\n\n".join(results[:2])
        else:
            return f"No documents found for query: '{query}'. The knowledge base may be empty or still processing."
            
    except Exception as e:
        error_msg = str(e)
        if "ResourceNotFoundException" in error_msg:
            return f"Error: Knowledge base {kb_id} not found. Please verify the BEDROCK_KB_ID is correct."
        elif "ValidationException" in error_msg:
            return f"Error: Invalid query or configuration. Details: {error_msg}"
        else:
            return f"Error searching knowledge base: {error_msg}"