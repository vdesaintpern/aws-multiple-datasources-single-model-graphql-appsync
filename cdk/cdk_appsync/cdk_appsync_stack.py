from aws_cdk import (
    aws_ec2 as ec2,
    aws_secretsmanager as sc,
    aws_logs as logs,
    aws_lambda as aws_lambda,
    aws_iam as iam,
    aws_appsync as appsync,
    aws_iam as iam,
    aws_logs as logs,
    aws_dynamodb as ddb,
    core
)
import json


class CdkAppsyncStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, vpc_id: str, subnet_ids, rds_secret_arn: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc.from_vpc_attributes(self, vpc_id, vpc_id=vpc_id, 
        availability_zones= [ 'eu-west-1c'],
        public_subnet_ids= subnet_ids)

        # creating vote table for dynamodb resolver
        vote_table = ddb.Table(self, 'votes', 
            table_name='votes', 
            partition_key={
                "name": "productid",
                "type": ddb.AttributeType.STRING
            }, 
            # Sortkey structure is like : UP#20200902T12:34:00 - DOWN#20201030T10:45:12
            sort_key={
                "name": "votesortkey",
                "type": ddb.AttributeType.STRING
            },
            read_capacity=5, 
            write_capacity=5
        )

        # creating API with GraphQL schema
        api = appsync.GraphqlApi(self, 'example_appsync_api',
                                name="example_appsync_api",
                                log_config=appsync.LogConfig(field_log_level=appsync.FieldLogLevel.ALL),
                                schema=appsync.Schema.from_asset(file_path="../appsync-conf/schema.graphql")
                                )

        # Authentication done with API key - for development purposes only
        appsync.CfnApiKey(self, 'examplegraphqlapi',
                                    api_id=api.api_id
                                    )

        # create security group for lambda
        # this will need to be added to your RDS inbound
        lambda_security_group = ec2.SecurityGroup(self, "Example-AppSyncResolverLambdaSG", 
            security_group_name="Example-AppSyncResolverLambdaSG",
            vpc=vpc,
            allow_all_outbound=True
        )

        # getting the code from local directory
        lambda_rds_code = aws_lambda.Code.asset("../lambda-rds")

        lambda_rds_resolver = aws_lambda.Function(self,
            "LambdaAppSyncSQLResolver",
            function_name=f"LambdaAppSyncSQLResolver",
            code=lambda_rds_code,
            handler="index.handler",
            runtime=aws_lambda.Runtime.NODEJS_12_X,
            memory_size=512,
            timeout=core.Duration.seconds(60),
            log_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets={
                "subnet_type": ec2.SubnetType.PUBLIC
            },
            allow_public_subnet=True,
            security_group=lambda_security_group,
        )

        # env parameters for rds lambda to perform SQL calls
        lambda_rds_resolver.add_environment("SECRET_ARN", rds_secret_arn)

        # allow lambda to read secret
        lambda_rds_resolver.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[ 'secretsmanager:GetSecretValue' ],
            resources=[ rds_secret_arn ]
        ))

        # adding the product datasource as lamda resolver
        products_ds = api.add_lambda_data_source('Products', lambda_rds_resolver)

        # creates resolver for query getProduct
        products_ds.create_resolver(
            type_name='Query',
            field_name='getProduct',
            request_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/getProduct.vtl"),
            response_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/getProduct_output_template.vtl"),
        )

        # adding lamda resolver for vote fields in product model
        lambda_dynamodb_code = aws_lambda.Code.asset("../lambda-dynamodb")

        lambda_dynamodb_votes_resolver = aws_lambda.Function(self,
            "LambdaAppSyncVotesResolver",
            function_name=f"LambdaAppSyncVotesResolver",
            code=lambda_dynamodb_code,
            handler="index.handler",
            runtime=aws_lambda.Runtime.NODEJS_12_X,
            memory_size=512,
            timeout=core.Duration.seconds(60),
        )

        # allow lambda to query dynamodb
        lambda_dynamodb_votes_resolver.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[ 
                "dynamodb:GetItem",
                "dynamodb:Query", 
            ],
            resources=[ 
                vote_table.table_arn,
                vote_table.table_arn + "/*"
            ]
        ));           

        # create lambda datasource for dynamodb queries
        votes_ds = api.add_lambda_data_source('Votes', lambda_dynamodb_votes_resolver)

        votes_ds.create_resolver(
            type_name='Product',
            field_name='ups',
            request_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/fields/votes_up.vtl"),
            response_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/fields/votes_up_output_template.vtl"),
        )

        votes_ds.create_resolver(
            type_name='Product',
            field_name='downs',
            request_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/fields/votes_down.vtl"),
            response_mapping_template=appsync.MappingTemplate.from_file("../appsync-conf/vtl/fields/votes_down_output_template.vtl"),
        )

    
