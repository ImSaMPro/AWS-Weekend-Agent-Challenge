import json
import boto3
import os

def lambda_handler(event, context):
    # Initialize AWS clients
    bedrock = boto3.client('bedrock-runtime')
    sns = boto3.client('sns')
    
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    
    # Define the prompt for the AI agent
    prompt_data = "Write a short, highly motivating morning quote and one quick productivity tip for a software developer. Keep it under 3 sentences."
    
    # Configure the Bedrock Nova model
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt_data
                    }
                ]
            }
        ],
        "inferenceConfig": {
            "maxNewTokens": 100,
            "temperature": 0.7
        }
    })
    
    try:
        # Call the AI model
        response = bedrock.invoke_model(
            body=body,
            modelId='amazon.nova-micro-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        ai_message = response_body.get('output').get('message').get('content')[0].get('text')
        
        # Report back: Send the email via SNS
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject="Your Morning AI Briefing",
            Message=f"Good morning!\n\nHere is your daily brief:\n{ai_message}\n\n- Your AWS Agent"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Briefing sent successfully!')
        }
        
    except Exception as e:
        print(f"Error generating brief: {e}")
        raise e