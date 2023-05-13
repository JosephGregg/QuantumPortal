import json
import boto3

def lambda_handler(event, context):
    http_method = event.get('httpMethod')
    path = event.get('path')
    # Initialize the API Gateway client
    api_gateway_client = boto3.client('apigateway')

    if path == "/create":
        if http_method == "GET":
            target_url = event.get('queryStringParameters', {}).get('targetUrl')
            
            if target_url:
                # Generate the API name and title based on targetUrl
                api_name = "QP-" + target_url.replace('.', '-')
                api_title = "QuantumPortal - " + target_url
                
                # Create a new API Gateway with the provided Swagger definition
                api_gateway_client = boto3.client('apigateway')
                swagger_definition = '''
                {
                    "swagger": "2.0",
                    "info": {
                        "version": "{{version_date}}",
                        "title": "{{title}}"
                    },
                    "basePath": "/",
                    "schemes": [
                        "https"
                    ],
                    "paths": {
                        "/": {
                            "get": {
                                "parameters": [
                                    {
                                        "name": "proxy",
                                        "in": "path",
                                        "required": true,
                                        "type": "string"
                                    },
                                    {
                                        "name": "X-My-X-Forwarded-For",
                                        "in": "header",
                                        "required": false,
                                        "type": "string"
                                    }
                                ],
                                "responses": {},
                                "x-amazon-apigateway-integration": {
                                    "uri": "{{url}}/",
                                    "responses": {
                                        "default": {
                                            "statusCode": "200"
                                        }
                                    },
                                    "requestParameters": {
                                        "integration.request.path.proxy": "method.request.path.proxy",
                                        "integration.request.header.X-Forwarded-For": "method.request.header.X-My-X-Forwarded-For"
                                    },
                                    "passthroughBehavior": "when_no_match",
                                    "httpMethod": "ANY",
                                    "cacheNamespace": "irx7tm",
                                    "cacheKeyParameters": [
                                        "method.request.path.proxy"
                                    ],
                                    "type": "http_proxy"
                                }
                            }
                        },
                        "/{proxy+}": {
                            "x-amazon-apigateway-any-method": {
                                "produces": [
                                    "application/json"
                                ],
                                "parameters": [
                                    {
                                        "name": "proxy",
                                        "in": "path",
                                        "required": true,
                                        "type": "string"
                                    },
                                    {
                                        "name": "X-My-X-Forwarded-For",
                                        "in": "header",
                                        "required": false,
                                        "type": "string"
                                    }
                                ],
                                "responses": {},
                                "x-amazon-apigateway-integration": {
                                    "uri": "{{url}}/{proxy}",
                                    "responses": {
                                        "default": {
                                            "statusCode": "200"
                                        }
                                    },
                                    "requestParameters": {
                                        "integration.request.path.proxy": "method.request.path.proxy",
                                        "integration.request.header.X-Forwarded-For": "method.request.header.X-My-X-Forwarded-For"
                                    },
                                    "passthroughBehavior": "when_no_match",
                                    "httpMethod": "ANY",
                                    "cacheNamespace": "irx7tm",
                                    "cacheKeyParameters": [
                                        "method.request.path.proxy"
                                    ],
                                    "type": "http_proxy"
                                }
                            }
                        }
                    }
                }
                '''
               
                swagger_definition = swagger_definition.replace('{{version_date}}', '2023-05-13T13:57:20Z')
                swagger_definition = swagger_definition.replace('{{title}}', api_title)
                swagger_definition = swagger_definition.replace('{{url}}', target_url)

                # Create the API Gateway
                try:
                    api_response = api_gateway_client.import_rest_api(
                        body=swagger_definition
                    )
                except Exception as e:
                    return {
                        'statusCode': 500,
                        'body': json.dumps(str(e))
                    }

                # Get the API ID and construct the full URL
                api_id = api_response['id']
                api_url = f"https://{api_id}.execute-api.{boto3.Session().region_name}.amazonaws.com"
                api_url += '/QuantumPortal'

                # Deploy the API with the desired stage settings
                try:
                    deployment_response = api_gateway_client.create_deployment(
                        restApiId=api_id,
                        stageName='QuantumPortal',
                        stageDescription='QP Proxy for ' + target_url,
                        description='QP Proxy for ' + target_url
                    )
                except Exception as e:
                    return {
                        'statusCode': 500,
                        'body': json.dumps(str(e))
                    }

                return {
                    'statusCode': 200,
                    'body': json.dumps(api_url)
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps('Please provide a valid target URL')
                }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request')
            }

    # Rest of the code for /delete and /list endpoints

    elif path == "/delete":
        if http_method == "DELETE":
            target_url = event.get('queryStringParameters', {}).get('targetUrl', 'Not provided')
            return {
                'statusCode': 200,
                'body': json.dumps('Delete: ' + target_url)
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request')
            }

    elif path == "/list":
        if http_method == "GET":
            try:
                # Retrieve all APIs
                api_response = api_gateway_client.get_rest_apis()
                apis = api_response['items']
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps(str(e))
                }

            # Extract URL and API ID from API Gateway names
            quantum_portals = []
            for api in apis:
                if "QuantumPortal - " in api['name']:
                    url = api['name'].replace("QuantumPortal - ", "")
                    api_id = api['id']
                    quantum_portals.append({'url': url, 'api_id': api_id})

            return {
                'statusCode': 200,
                'body': json.dumps(quantum_portals)
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request')
            }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps('Endpoint not found')
        }
