import aws_cdk as core
import aws_cdk.assertions as assertions

from salesforce_prototype_cdk.salesforce_prototype_cdk_stack import SalesforcePrototypeCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in salesforce_prototype_cdk/salesforce_prototype_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SalesforcePrototypeCdkStack(app, "salesforce-prototype-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
