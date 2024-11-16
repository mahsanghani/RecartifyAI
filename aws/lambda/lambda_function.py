import json
import boto3
import requests

# Initialize the Secrets Manager client
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

def get_secret(secret_arn):
    """Retrieve the secret from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = response['SecretString']
        return json.loads(secret)
    except Exception as e:
        print(f"Error retrieving secret: {str(e)}")
        raise

def lambda_handler(event, context):
    # ARN of the secret in Secrets Manager
    secret_arn = "arn:aws:secretsmanager:us-east-1:126500756700:secret:Shopify-irH5Hr"

    try:
        # Get the Shopify secret
        secret = get_secret(secret_arn)
        shopify_access_token = secret['shopify_access_token']

        # Shopify API details
        shopify_url = "https://naturosupps.myshopify.com/admin/api/2024-10/graphql.json"
        graphql_query = {
            "query": """
            query AbandonedCheckouts {
                abandonedCheckouts(first: 1) {
                    nodes {
                        abandonedCheckoutUrl
                        billingAddress { country }
                        completedAt
                        createdAt
                        customer { firstName lastName email }
                        id
                        shippingAddress { country }
                        updatedAt
                    }
                }
            }
            """
        }

        # Make the API call to Shopify
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": shopify_access_token
        }
        response = requests.post(shopify_url, headers=headers, data=json.dumps(graphql_query))

        # Check the response
        if response.status_code == 200:
            data = response.json()
            print("Abandoned carts retrieved successfully:", data)
            return {
                "statusCode": 200,
                "body": json.dumps(data)
            }
        else:
            print("Error:", response.status_code, response.text)
            return {
                "statusCode": response.status_code,
                "body": response.text
            }

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return {
            "statusCode": 500,
            "body": str(e)
        }
