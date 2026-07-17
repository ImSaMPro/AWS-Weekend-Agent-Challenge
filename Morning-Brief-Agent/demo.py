import sys
import argparse
import json
import boto3
import urllib.request
import urllib.error

def invoke_via_url(url):
    print(f"[*] Triggering Lambda via Function URL: {url}")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8')
            print(f"[+] Success! HTTP Status Code: {status}")
            print(f"[+] Response Body: {body}")
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(f"[-] Response: {e.read().decode('utf-8')}", file=sys.stderr)
        except Exception:
            pass
    except urllib.error.URLError as e:
        print(f"[-] Network Connection Error: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"[-] Unexpected Error: {e}", file=sys.stderr)

def invoke_via_sdk(function_name, region):
    print(f"[*] Triggering Lambda via AWS SDK (Lambda.Client.invoke) in region '{region}'...")
    try:
        client = boto3.client('lambda', region_name=region)
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            LogType='Tail'
        )
        status_code = response['StatusCode']
        payload = response['Payload'].read().decode('utf-8')
        print(f"[+] Success! Lambda invocation status: {status_code}")
        print(f"[+] Lambda Response Payload: {payload}")
    except Exception as e:
        print(f"[-] SDK Invocation failed: {e}", file=sys.stderr)

def local_dry_run(region):
    print(f"[*] Performing local dry-run (calling Amazon Bedrock directly) in region '{region}'...")
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        prompt_data = "Write a short, highly motivating morning quote and one quick productivity tip for a software developer. Keep it under 3 sentences."
        
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
        
        print(f"[*] Sending prompt to Bedrock: '{prompt_data}'")
        response = bedrock.invoke_model(
            body=body,
            modelId='amazon.nova-micro-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        ai_message = response_body.get('output').get('message').get('content')[0].get('text')
        
        print("\n=== AI GENERATED BRIEFING (DRY-RUN) ===")
        print(f"Good morning!\n\nHere is your daily brief:\n{ai_message.strip()}\n\n- Your AWS Agent")
        print("=======================================\n")
        print("[+] Dry-run completed successfully!")
    except Exception as e:
        print(f"[-] Bedrock invocation failed: {e}", file=sys.stderr)
        print("[-] Ensure you have requested/enabled model access for 'Amazon Nova Micro' in Bedrock console in this region.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Demo script to test the Morning Briefing Agent.")
    
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Testing mode")
    
    # URL Mode
    parser_url = subparsers.add_parser("url", help="Test via Lambda Function URL (Public HTTP Endpoint)")
    parser_url.add_argument("--url", required=True, help="The Lambda Function URL")
    
    # SDK Mode
    parser_sdk = subparsers.add_parser("sdk", help="Test via AWS SDK (Invoke Lambda directly)")
    parser_sdk.add_argument("--function", default="MorningBriefAgent", help="Lambda Function name/ARN (default: MorningBriefAgent)")
    parser_sdk.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    
    # Local Dry-Run Mode
    parser_local = subparsers.add_parser("local", help="Run model generation locally via Bedrock API (no Lambda needed)")
    parser_local.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    
    args = parser.parse_args()
    
    if args.mode == "url":
        invoke_via_url(args.url)
    elif args.mode == "sdk":
        invoke_via_sdk(args.function, args.region)
    elif args.mode == "local":
        local_dry_run(args.region)

if __name__ == "__main__":
    main()
