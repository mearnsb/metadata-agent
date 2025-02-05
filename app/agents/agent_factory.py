import autogen
from typing import Dict, Any, List
from .agent_config import ModelConfig
from .base_agent import BaseAgent, SQLAgent, JobAgent, ReviewerAgent
from ..tools.dq_tools import run_dq_job, get_job_status, run_sql_statement
import logging

logger = logging.getLogger(__name__)

def create_executor(llm_config: Dict[str, Any]) -> autogen.UserProxyAgent:
    """Create the executor agent"""
    return autogen.UserProxyAgent(
        name="Executor_User",
        system_message="Executor. Execute the instructions and tools suggested by sql_assistant or job_assistant and report the results.",
        description="A computer terminal that performs no other action than running tool calls from sql_assistant or job_assistant.",
        human_input_mode="NEVER",
        llm_config=llm_config,
        code_execution_config=False,
    )

def create_job_assistant(llm_config: Dict[str, Any]) -> autogen.AssistantAgent:
    """Create the job assistant agent"""
    return autogen.AssistantAgent(
        name="Job_Assistant",
        llm_config=llm_config,
        system_message="""Job Assistant. You are able to run dq jobs and check dq job results/status. 
        You use the run_dq_job function to run dq jobs. You use the get_job_status function to check the results, one time each time you're asked.
        Because these dq job functions trigger an API call, the user will want current (up to date) results, you should execute the functions rather than rely on the historical context. 
        Even if job was recently run, you can run it one more time if the user requests this. 
        Example: run a dq job for tables w/ 'xyz' in the name (run dq jobs, you need a connection_name, dataset, query, schema)
        Example: whats the status of the dq jobs (check dq job results/status, no arguments needed)
        Include the word 'TERMINATE' and summarize the answer, if you can answer the question from the context, rather than asking for more tasks."""
    )

def create_sql_assistant(llm_config: Dict[str, Any]) -> autogen.AssistantAgent:
    """Create the SQL assistant agent"""
    return autogen.AssistantAgent(
        name="SQL_Assistant",
        llm_config=llm_config,
        system_message="""SQL Assistant. You provide instructions to the executor to run a query on the 'metadata' table, in order to answer the most user questions.
        REMEMBER: 
        - Only query the 'metadata' table.
        - Only use the columns 'connection_name', 'schema_name', 'table_name'
            - 'connections' typically refers to the 'connection_name' column
            - 'schema' typically refers to the 'schema_name' column
            - 'table' typically refers to the 'table_name' column
        - single quote for escape characters
        - use lower() in the predicate portion of the query, for case insensitive where clauses.
        - use wild cards to match substrings.
        - focus on the immediate task, don't deviate from the task
        - Try a distinct or a limit 10 query to narrow down the results. 
        - If you're unsure, you can try 1 attempt to interpret the question (best guess). 
        - If you're still not sure, or there are no results after trying a query, ask for clarificaiton.
        EXAMPLE_PROMPT: use sql, count total number of tables in this schema
        EXAMPLE QUERY: select * from metadata where lower(connection_name) = lower('<CONNECTION_NAME>') and lower(schema_name) = lower('<SCHEMA>') and lower(table_name) like lower('%<SEARCH_STRING>%') limit 30
        EXAMPLE QUERY: select * from metadata where lower(connection_name) like lower('%<CONNECTION_NAME>%') and lower(schema_name) like lower('%<SCHEMA>%') and lower(table_name) like lower('%<SEARCH_STRING>%') limit 30
        IMPORTANT: If you can clearly answer the question, include the word 'TERMINATE' and summarize the answer, don't respond with the same query and don't ask to help with more tasks.""",
        max_consecutive_auto_reply=4,
    )

def create_user_proxy(llm_config: Dict[str, Any]) -> autogen.UserProxyAgent:
    """Create the user proxy agent"""
    return autogen.UserProxyAgent(
        name="Admin_User",
        system_message="A human admin. Interact with the assistants to complete the tasks. A common workflow is identifying a connection name, then identifying a schema, then identifying a table, then running a dq job, then checking the results.",
        description="A team member that wants to efficiently complete tasks.",
        code_execution_config=False,
        human_input_mode="NEVER",
    )

def create_reviewer_assistant(llm_config: Dict[str, Any]) -> autogen.AssistantAgent:
    """Create the reviewer assistant agent"""
    return autogen.AssistantAgent(
        name="Reviewer_Assistant",
        system_message="""Review the prompt and results to concisely answer the question. Summarize the initial question and answer so it's easy to understand. 
        Use bullet points or lists if the sql or job assistant returns multiple results.
        As the reviewer assisant, you do not include actions, arguments, or tool calls. Only the planner_assistant includes that information.
        Include the word 'TERMINATE' with the summarized response, rather than asking for more tasks.""",
        llm_config=llm_config,
    )

def create_agents(llm_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create and return all agent instances needed for the application.
    """
    # Get config if not provided
    if llm_config is None:
        logger.info("No config provided to create_agents, getting default config")
        llm_config = ModelConfig.get_default_config()
    
    logger.info(f"Creating agents with api_type: {llm_config.get('config_list', [{}])[0].get('api_type')}")
    
    # Create agents first
    executor = create_executor(llm_config)
    job_assistant = create_job_assistant(llm_config)
    sql_assistant = create_sql_assistant(llm_config)
    
    # Register tools
    register_agent_tools(executor, sql_assistant, job_assistant)
    
    # Create remaining agents
    user_proxy = create_user_proxy(llm_config)
    reviewer_assistant = create_reviewer_assistant(llm_config)
    
    return {
        "user_proxy": user_proxy,
        "executor": executor,
        "job_assistant": job_assistant,
        "sql_assistant": sql_assistant,
        "reviewer_assistant": reviewer_assistant
    }

def create_group_chat_agents() -> List[BaseAgent]:
    """Create and return the list of agents for the group chat"""
    logger.info("Creating group chat agents")
    llm_config = ModelConfig.get_default_config()
    logger.info(f"Got LLM config with api_type: {llm_config.get('config_list', [{}])[0].get('api_type')}")
    
    # Get the first config from the list and remove safety settings
    base_config = {
        key: value for key, value in llm_config.get("config_list")[0].items() 
        if key != "safety_settings"
    }
    
    # Wrap in config_list structure expected by autogen
    base_config = {"config_list": [base_config]}
    logger.info(f"Created base config with api_type: {base_config.get('config_list', [{}])[0].get('api_type')}")
    
    agents = [
        autogen.AssistantAgent(
            name="SQL_Expert",
            llm_config=base_config,
            system_message="""You are a SQL expert. You help users understand database structure 
            and write SQL queries. You provide clear explanations about tables and their relationships."""
        ),
        autogen.AssistantAgent(
            name="Data_Analyst",
            llm_config=base_config,
            system_message="""You are a data analyst who helps users understand the data in the database.
            You explain data patterns, suggest useful queries, and help interpret results."""
        ),
        autogen.AssistantAgent(
            name="Documentation_Expert",
            llm_config=base_config,
            system_message="""You help users understand the database documentation and metadata.
            You explain table purposes, column meanings, and data relationships."""
        )
    ]
    
    return agents 

def register_agent_tools(executor: Any, sql_assistant: Any, job_assistant: Any):
    """Register tools with appropriate agents"""
    
    # Register DQ job tools
    executor.register_for_execution()(run_dq_job)
    executor.register_for_llm(description="Execute a DQ job with given parameters")(run_dq_job)
    job_assistant.register_for_llm(
        description="""Submits a DQ Job to run a DQ check.
        IMPORTANT: This requires a connection_name, dataset, query.
        DATASET: Use the table name as the dataset name (e.g. not schema.table, just table.)
        QUERY: The query should use schema.table format and have a limit 10000 to always limit results.
        SCHEMA: Use the schema name as the schema name (e.g. not schema.table, just schema.)"""
    )(run_dq_job)
    
    # Register job status tool
    executor.register_for_execution()(get_job_status)
    executor.register_for_llm(description="Check the status of DQ jobs")(get_job_status)
    job_assistant.register_for_llm(
        description="Check the status of DQ jobs"
    )(get_job_status)
    
    # Register SQL tool
    executor.register_for_execution()(run_sql_statement)
    executor.register_for_llm(
        description="Execute a SQL query on the metadata table"
    )(run_sql_statement)
    sql_assistant.register_for_llm(
        description="""Runs A SELECT statement on 'metadata' table. 
        Available columns: connection_name, schema_name, table_name"""
    )(run_sql_statement) 