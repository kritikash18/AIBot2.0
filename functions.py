import os
import openai
from IPython.display import display, HTML
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.llms import ChatMessage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

openai.api_key = ''

def moderation_check(user_input):
    # Call the OpenAI API to perform moderation on the user's input.
    response = openai.moderations.create(input=user_input)

    # Extract the moderation result from the API response.
    moderation_output = response.results[0].flagged
    # Check if the input was flagged by the moderation system.
    if response.results[0].flagged == True:
        # If flagged, return "Flagged"
        return "Flagged"
    else:
        # If not flagged, return "Not Flagged"
        return "Not Flagged"

def process_document(pdf_path, custom_engine=False):
    #Create object of SimpleDirectoryReader
    reader = SimpleDirectoryReader(input_dir=pdf_path)
    documents = reader.load_data()
    if custom_engine == True:
        return custom_query_engine(documents)
    return create_query_engine(documents)


def create_query_engine(documents):
    parser = SimpleNodeParser.from_defaults()
    nodes = parser.get_nodes_from_documents(documents)
    index = VectorStoreIndex(nodes)
    query_engine = index.as_query_engine()
    return query_engine

def query_response(user_input, query_engine):
    response = query_engine.query(user_input)
    file_name = response.source_nodes[0].node.metadata['file_name'] + "page: " + response.source_nodes[0].node.metadata['page_label']
    final_response = response.response + '\n <br> For more details, check further at ' + file_name
    return final_response

def query_response_enhanced(user_input, query_engine):
    response = query_engine.query(user_input)
    retrieved = response.source_nodes[0].node.text + response.source_nodes[1].node.text
    messages = [
        {"role":"system", "content":"You are an AI assistant to user."},
        {"role":"user", "content":f"""'{user_input}' Check in '{retrieved}' """},
    ]
    response_new = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages)
    return response_new.choices[0].message.content

def custom_query_engine(documents):
    ##Initialize the OpenAI model
    Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=256)

    ##Initialize the embedding model
    Settings.embed_model = OpenAIEmbedding()

    ## Initialize the node_parser with the custom node settings
    Settings.node_parser = SentenceSplitter(chunk_size=500, chunk_overlap=50)
    ## Initialize the num_output and the context window
    Settings.num_output = 500
    Settings.context_window = 3900

    # Create a VectorStoreIndex from a list of documents using the service context
    index = VectorStoreIndex.from_documents(documents)

    retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=3,
    )

    # configure response synthesizer - refine mode as this is QA system
    response_synthesizer = get_response_synthesizer(
        response_mode="refine",
    )

    # assemble query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    return query_engine
