# RDS / DynamoDB datasources in single GraphQL model with AWS AppSync

WORK IN PROGRESS - 

# Architecture


# Main elements


# How to deploy

Have your RDS database ready -> not included in CDK Stack
=> update cdk.json to match your environments, don't forget your secret for RDS

create table product
(
    id       INTEGER primary key auto_increment not null,
    name     TEXT,
    price    DECIMAL
);

INSERT INTO product (id, name, price) VALUES (2, 'Book', 9.99);


Dynamodb table created in CDK stack -> schema for sorted key UP#<timestamp> or DOWN#<timestamp>

AppSync CDK stack

cdk init / bootstrap and deploy

Add LambdaSG security group to your Database inbound ! 

AWS Secrets Manager called in the lambda needs NAT Gateway / internet access from the lambda OR use PrivateLink.

VTL code from lambda RDS return is matching the return type of MYSQL query. 
If you use PostgreSQL, you may need to use $context.result.rows[0] instead of $context.result[0]

# Disclaimer

This code is provided as-is with no guarantee whatsoever. Use it at your own risk. 


