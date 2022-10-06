from aws_cdk import (
    aws_ec2
)


def create_security_group(construct, logical_name: str, vpc: aws_ec2.Vpc):
    """
    Create a VPC security group to restrict network traffic.

    The security group that is created blocks all inbound network connections and allows outbound
    IP4 and IP6 connections on ports 80 and 443 only.

    Parameters
    ----------
    construct
        The parent construct in the CDK project.
    logical_name: str
        The logical name of the security group in the CDK project.
    vpc : aws_ec2.Vpc
        The VPC where the security group will be attached.

    Returns
    -------
    aws_ec2.SecurityGroup
        The security group.
    """
    security_group = aws_ec2.SecurityGroup(construct, logical_name, vpc=vpc, allow_all_outbound=False)
    security_group.add_egress_rule(aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(80), 'IP4 Port 80')
    security_group.add_egress_rule(aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(443), 'IP4 Port 443')
    security_group.add_egress_rule(aws_ec2.Peer.any_ipv6(), aws_ec2.Port.tcp(80), 'IP6 Port 80')
    security_group.add_egress_rule(aws_ec2.Peer.any_ipv6(), aws_ec2.Port.tcp(443), 'IP6 Port 443')
    return security_group