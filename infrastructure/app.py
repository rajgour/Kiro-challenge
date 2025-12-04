#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.api_stack import ApiStack

app = cdk.App()
ApiStack(
    app, 
    "EventsApiStack",
    env=cdk.Environment(
        account="692859950494",
        region="us-west-2"
    )
)

app.synth()
