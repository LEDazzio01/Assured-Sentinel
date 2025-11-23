import os
import asyncio
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

async def generate_code(user_request: str):
    # 1. Initialize the Kernel
    kernel = sk.Kernel()

    # 2. Configure Azure OpenAI Service
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not all([deployment, endpoint, api_key]):
        raise ValueError("Missing Azure OpenAI environment variables.")

    service_id = "analyst"
    
    kernel.add_service(
        AzureChatCompletion(
            service_id=service_id,
            deployment_name=deployment,
            endpoint=endpoint,
            api_key=api_key
        )
    )

    # 3. Define the System Persona & Settings
    # High temperature (0.8) to drive stochastic proposal generation [cite: 1164]
    req_settings = AzureChatPromptExecutionSettings(service_id=service_id)
    req_settings.temperature = 0.8 
    req_settings.top_p = 0.95

    prompt_template = """
    SYSTEM ROLE:
    You are a Senior Python Engineer. You act as 'The Analyst'.
    Your goal is to write functional, efficient Python code to solve the user's problem.
    Do not explain the code excessively. Provide the code block clearly.
    
    USER REQUEST:
    {{$input}}
    """

    # 4. Create the Function (Fixed for v1.x)
    # We now use 'add_function' instead of 'create_function_from_prompt'
    analyst_function = kernel.add_function(
        plugin_name="AnalystPlugin",
        function_name="generate_code",
        prompt=prompt_template,
        prompt_execution_settings=req_settings
    )

    # 5. Execute
    print(f"--- Analyst (High Temp) Generating Solution for: '{user_request}' ---")
    
    # Invoke using KernelArguments
    result = await kernel.invoke(
        analyst_function,
        KernelArguments(input=user_request)
    )
    
    print("\n--- RAW OUTPUT ---")
    print(result)
    return str(result)

if __name__ == "__main__":
    test_prompt = "Write a Python function to parse an XML string safely."
    asyncio.run(generate_code(test_prompt)) 