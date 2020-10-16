#!/usr/bin/env python3
import os
from aws_cdk import core
from cdk_appsync.cdk_appsync_stack import CdkAppsyncStack


app = core.App()

rds_secret_arn = app.node.try_get_context("rds_secret_arn")
vpc_id = app.node.try_get_context("vpc_id")
subnet_ids = app.node.try_get_context("subnet_ids")

CdkAppsyncStack(app, "cdk-appsync", rds_secret_arn=rds_secret_arn, vpc_id=vpc_id, subnet_ids=subnet_ids,
    env={
        'account': os.environ['CDK_DEFAULT_ACCOUNT'], 
        'region': os.environ['CDK_DEFAULT_REGION']
    }
)

app.synth()
