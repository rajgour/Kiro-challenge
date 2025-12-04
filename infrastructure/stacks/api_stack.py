from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    CfnOutput
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # DynamoDB Tables
        events_table = dynamodb.Table(
            self, "EventsTable",
            partition_key=dynamodb.Attribute(
                name="eventId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        users_table = dynamodb.Table(
            self, "UsersTable",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        registrations_table = dynamodb.Table(
            self, "RegistrationsTable",
            partition_key=dynamodb.Attribute(
                name="eventId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Add GSI for querying registrations by userId
        registrations_table.add_global_secondary_index(
            index_name="userId-index",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Lambda Function with all dependencies packaged
        api_lambda = lambda_.Function(
            self, "EventsApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="main.handler",
            code=lambda_.Code.from_asset("../backend/lambda_package"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DYNAMODB_TABLE": events_table.table_name,
                "USERS_TABLE": users_table.table_name,
                "REGISTRATIONS_TABLE": registrations_table.table_name,
                "ALLOWED_ORIGINS": "*"
            }
        )
        
        # Grant Lambda permissions to access DynamoDB
        events_table.grant_read_write_data(api_lambda)
        users_table.grant_read_write_data(api_lambda)
        registrations_table.grant_read_write_data(api_lambda)
        
        # API Gateway
        api = apigateway.RestApi(
            self, "EventsApi",
            rest_api_name="Events Management API",
            description="Serverless API for managing events",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization", "Accept"]
            )
        )
        
        # Lambda Integration
        lambda_integration = apigateway.LambdaIntegration(api_lambda)
        
        # API Gateway Routes
        api.root.add_method("GET", lambda_integration)
        api.root.add_resource("health").add_method("GET", lambda_integration)
        
        # Users routes
        users_resource = api.root.add_resource("users")
        users_resource.add_method("POST", lambda_integration)
        
        user_resource = users_resource.add_resource("{user_id}")
        user_resource.add_method("GET", lambda_integration)
        
        user_registrations = user_resource.add_resource("registrations")
        user_registrations.add_method("GET", lambda_integration)
        
        # Events routes
        events_resource = api.root.add_resource("events")
        events_resource.add_method("GET", lambda_integration)
        events_resource.add_method("POST", lambda_integration)
        
        event_resource = events_resource.add_resource("{event_id}")
        event_resource.add_method("GET", lambda_integration)
        event_resource.add_method("PUT", lambda_integration)
        event_resource.add_method("DELETE", lambda_integration)
        
        # Event registration routes
        event_registrations = event_resource.add_resource("registrations")
        event_registrations.add_method("GET", lambda_integration)
        event_registrations.add_method("POST", lambda_integration)
        
        event_registration_user = event_registrations.add_resource("{user_id}")
        event_registration_user.add_method("DELETE", lambda_integration)
        
        event_waitlist = event_resource.add_resource("waitlist")
        event_waitlist.add_method("PUT", lambda_integration)
        
        # Outputs
        CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway URL")
        CfnOutput(self, "TableName", value=events_table.table_name, description="DynamoDB Table Name")
