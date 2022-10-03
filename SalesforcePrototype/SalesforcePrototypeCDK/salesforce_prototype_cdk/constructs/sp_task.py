from aws_cdk import (
    aws_applicationautoscaling,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_ecs_patterns,
    aws_iam,
    aws_logs,
    aws_s3,
    aws_ssm,
    aws_sns,
    aws_secretsmanager,
    RemovalPolicy,
    Stack
)
from constructs import Construct


class SalesforcePrototypeTaskProperties:
    """
    Configuration values for creating an instance of the SalesforcePrototypeTaskConstruct class.
    """

    def __init__(self, base_name: str, vpc_id: str, subnet_ids: list[str], bucket: aws_s3.Bucket,
                 ecr_repo: aws_ecr.Repository, image_tag: str, task_definition_env_vars: dict[str, str],
                 parameters: dict[str, aws_ssm.StringParameter], notification_topic: aws_sns.Topic):
        """
        Create configuration values for creating an instance of the SalesforcePrototypeTaskConstruct class.

        Parameters
        ----------
        base_name : str
            The base name of the resources to create.
        vpc_id : str
            The AWS account ID where the resources will be deployed.
        subnet_ids : list[str]
            A list of the AWS subnet IDs where the task could run.
        bucket : aws_s3.Bucket
            The storage bucket that the task will access (i.e. where ELT data will be stored/processed).
        ecr_repo : aws_ecr.Repository
            The ECR repo where the docker image to be executed can be found.
        image_tag : str
            The tag used to select the docker image to run from the images in the ECR repo, e.g. dev-current
        task_definition_env_vars : dict[str, str]
            A dictionary containing parameter names and parameter values to be set as environment variables in the
            docker container.
        parameters : dict[str, aws_ssm.StringParameter]
            A dictionary containing parameter names and Systems Manager Parameter Store parameters to be linked to
            environment variables in the docker container.
        notification_topic : aws_sns.Topic
            The SNS notification topic for the ELT code in the docker container to use to send email alerts.
        """
        self.base_name = base_name
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.bucket = bucket
        self.ecr_repo = ecr_repo
        self.image_tag = image_tag
        self.task_definition_env_vars = task_definition_env_vars
        self.parameters = parameters
        self.notification_topic = notification_topic


class SalesforcePrototypeTaskConstruct(Construct):
    """
    A construct that creates a new ECS task definition, Event Bridge schedule and various related resources.

    The resources created by the construct include:

    - ECS Task Definition
    - IAM "execution" role - used by ECS to start the container running
    - IAM "task" role - used by Python code running within the container to access other AWS resources
    - IAM policies - e.g. to enable access to the S3 bucket
    - CloudWatch Log Group - to capture the run-time logs generated by Python code running inside the container
    """

    def __init__(self, scope: Construct, construct_id: str, *, properties: SalesforcePrototypeTaskProperties) -> None:
        """
        Create a construct that creates a new ECS task definition, Event Bridge schedule and various related resources.

        Parameters
        ----------
        scope : str
            The scope where the construct should be created.
        construct_id : str
            The logical name of the construct to identify it within the scope.
        properties : SalesforcePrototypeTaskProperties
            Configuration values for creating the construct.
        """
        super().__init__(scope, construct_id)

        # create IAM roles
        exec_role = self.create_exec_role()
        task_role = self.create_task_role(properties.bucket, properties.notification_topic)

        # additional permissions
        self.grant_role_parameter_access(properties.base_name, exec_role)
        self.grant_role_secrets_access(properties.base_name, exec_role)

        # networking
        vpc = aws_ec2.Vpc.from_lookup(self, 'vpc', vpc_id=properties.vpc_id)
        subnets = []
        for subnet_id in properties.subnet_ids:
            subnets.append(aws_ec2.Subnet.from_subnet_id(self, subnet_id, subnet_id))

        # security group
        security_group = self.create_security_group(vpc)

        # ecs cluster
        cluster = aws_ecs.Cluster(self, 'task-cluster', vpc=vpc, cluster_name=properties.base_name)

        # add the bucket name and SNS topic name to the task definition environment variables
        properties.task_definition_env_vars['CRUK_AWS_S3_BUCKET_NAME'] = properties.bucket.bucket_name
        if properties.notification_topic is not None and \
                properties.notification_topic.topic_name is not None \
                and len(properties.notification_topic.topic_name) > 0 \
                and not properties.notification_topic.topic_name.isspace():
            properties.task_definition_env_vars['CRUK_AWS_SNS_TOPIC_ARN'] = properties.notification_topic.topic_arn

        # task definition
        fargate_task_definition = self.create_task_definition(
            base_name=properties.base_name, exec_role=exec_role, task_role=task_role,
            ecr_repo=properties.ecr_repo, image_tag=properties.image_tag,
            task_definition_env_vars=properties.task_definition_env_vars,
            parameters=properties.parameters)

        # scheduled task
        self.create_scheduled_task(
            base_name=properties.base_name, fargate_task_definition=fargate_task_definition,
            cluster=cluster, security_group=security_group, subnets=subnets)

    # -------------------- CREATE IAM ROLES --------------------

    def create_exec_role(self):
        """
        Create the IAM role used by ECS to execute the docker container and write container logs.

        Returns
        -------
        aws_iam.Role
            The IAM "execution" role.
        """
        # exec role - used by the AWS plumbing to run the container, read parameters/secrets and write container logs
        ecs_policy_name = 'service-role/AmazonECSTaskExecutionRolePolicy'  # the AWS built-in policy name
        exec_role = aws_iam.Role(self, 'exec-role',
                                 assumed_by=aws_iam.ServicePrincipal('ecs.amazonaws.com'),
                                 managed_policies=[aws_iam.ManagedPolicy.from_aws_managed_policy_name(ecs_policy_name)])
        exec_role_assume_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            principals=[aws_iam.ServicePrincipal('ecs.amazonaws.com'),
                        aws_iam.ServicePrincipal('ecs-tasks.amazonaws.com')],
            actions=['sts:AssumeRole']
        )
        exec_role.assume_role_policy.add_statements(exec_role_assume_policy)
        return exec_role

    def create_task_role(self, bucket: aws_s3.Bucket, notification_topic: aws_sns.Topic):
        """
        Create the IAM role used by Python code running inside the container to access other AWS resources.

        Parameters
        ----------
        bucket : aws_s3.Bucket
            The S3 bucket that the task code will access.
        notification_topic : aws_sns.Topic
            The SNS notification topic that the task code will access.

        Returns
        -------
        aws_iam.Role
            The IAM "task" role.
        """
        # task role - used by any actions carried out by our Python code running inside the container
        # the task role usually needs to be created explicitly since typically additional permissions need to be granted
        task_role = aws_iam.Role(self, 'task-role',
                                 assumed_by=aws_iam.ServicePrincipal('ecs.amazonaws.com'))
        task_role_assume_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            principals=[aws_iam.ServicePrincipal('ecs.amazonaws.com'),
                        aws_iam.ServicePrincipal('ecs-tasks.amazonaws.com')],
            actions=['sts:AssumeRole']
        )
        task_role.assume_role_policy.add_statements(task_role_assume_policy)
        bucket.grant_read_write(task_role)
        task_ecs_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['ecs:ListTasks'],
            resources=['*']
        )
        task_role.add_to_policy(task_ecs_policy)
        if notification_topic is not None:
            notification_topic.grant_publish(task_role)
        return task_role

    # -------------------- ALLOW EXEC ROLE TO READ PARAMETER / SECRET --------------------

    def grant_role_parameter_access(self, base_name: str, exec_role: aws_iam.Role):
        """
        Grant the specified IAM role access to read the Systems Manager Parameter Store parameters for this solution.

        Parameters
        ----------
        base_name : str
            The base name (i.e. prefix) for the Systems Manager Parameter Store parameters.
        exec_role : aws_iam.Role
            The IAM role to be granted access to the parameters

        Returns
        -------
        None
            No return value.
        """
        current_account_id = Stack.of(self).account
        current_region = Stack.of(self).region
        ssm_parameter_arn_match = f'arn:aws:ssm:{current_region}:{current_account_id}:parameter/{base_name}/*'
        exec_ssm_parameter_store_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['ssm:GetParameters'],
            resources=[ssm_parameter_arn_match]
        )
        exec_role.add_to_policy(exec_ssm_parameter_store_policy)

    def grant_role_secrets_access(self, base_name: str, exec_role: aws_iam.Role):
        """
        Grant the specified IAM role access to read the Secrets Manager secrets for this solution.

        Parameters
        ----------
        base_name : str
            The base name for the Systems Manager secrets.
        exec_role : aws_iam.Role
            The IAM role to be granted access to the parameters

        Returns
        -------
        None
            No return value.
        """
        current_account_id = Stack.of(self).account
        current_region = Stack.of(self).region
        secrets_arn_match = f'arn:aws:secretsmanager:{current_region}:{current_account_id}:secret/{base_name}'
        exec_secrets_manager_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['secretsmanager:GetSecretValue'],
            resources=[secrets_arn_match]
        )
        exec_role.add_to_policy(exec_secrets_manager_policy)

    # -------------------- CREATE NETWORK SECURITY GROUP --------------------

    def create_security_group(self, vpc: aws_ec2.Vpc):
        """
        Create a VPC security group to restrict network traffic.

        The security group that is created blocks all inbound network connections and allows outbound
        IP4 and IP6 connections on ports 80 and 443 only.

        Parameters
        ----------
        vpc : aws_ec2.Vpc
            The VPC the security group will be attached to.

        Returns
        -------
        aws_ec2.SecurityGroup
            The security group.
        """
        security_group = aws_ec2.SecurityGroup(self, 'task-security-group', vpc=vpc,
                                               allow_all_outbound=False)
        security_group.add_egress_rule(aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(80), 'IP4 Port 80')
        security_group.add_egress_rule(aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(443), 'IP4 Port 443')
        security_group.add_egress_rule(aws_ec2.Peer.any_ipv6(), aws_ec2.Port.tcp(80), 'IP6 Port 80')
        security_group.add_egress_rule(aws_ec2.Peer.any_ipv6(), aws_ec2.Port.tcp(443), 'IP6 Port 443')
        return security_group

    # -------------------- CREATE ECS TASK DEFINITION --------------------

    def create_task_definition(self, base_name: str, exec_role: aws_iam.Role, task_role: aws_iam.Role,
                               ecr_repo: aws_ecr.Repository, image_tag: str,
                               task_definition_env_vars: dict[str, str],
                               parameters: dict[str, aws_ssm.StringParameter]):
        """
        Create an ECS task definition and CloudWatch log group.

        This method also configures the runtime resources allocated to the docker image - 0.5 vCPU and 1GB RAM.

        Parameters
        ----------
        base_name : str
            The base-name of the ECS task definition to create.
        exec_role : aws_iam.Role
            The IAM "execution" role that will be used by AWS to execute the container and write execution logs.
        task_role : aws_iam.Role
            The IAM "task" role that will be used by Python code running inside the container to access AWS resources.
        ecr_repo : aws_ecr.Repository
            The ECR repo where the docker image to be executed can be found.
        image_tag : str
            The tag used to select the docker image to run from the images in the ECR repo, e.g. dev-current
        task_definition_env_vars : dict[str, str]
            A dictionary containing parameter names and parameter values to be set as environment variables in the
            docker container.
        parameters : dict[str, aws_ssm.StringParameter]
            A dictionary containing parameter names and Systems Manager Parameter Store parameters to be linked to
            environment variables in the docker container.

        Returns
        -------
        aws_ecs.FargateTaskDefinition
            The ECS task definition.
        """
        fargate_task_definition = aws_ecs.FargateTaskDefinition(
            self, 'fargate-task',
            family=base_name,
            cpu=512,
            memory_limit_mib=1024,
            execution_role=exec_role,
            task_role=task_role)

        container_image = aws_ecs.ContainerImage.from_ecr_repository(ecr_repo, image_tag)

        log_group = aws_logs.LogGroup(self, 'log-group',
                                      log_group_name=f'/elt/{base_name}',
                                      removal_policy=RemovalPolicy.DESTROY,
                                      retention=aws_logs.RetentionDays.SIX_MONTHS)
        log_driver = aws_ecs.LogDrivers.aws_logs(log_group=log_group, stream_prefix='elt')

        container_secrets = {}
        for parameter_name, parameter in parameters.items():
            secret = aws_ecs.Secret.from_ssm_parameter(parameter)
            container_secrets['CRUK_' + parameter_name.upper().replace('-', '_')] = secret

        secrets = aws_secretsmanager.Secret.from_secret_name_v2(self, 'secrets', base_name)
        snowflake_rsa_passphrase_secret = aws_ecs.Secret.from_secrets_manager(secrets, 'snowflake-rsa-key-passphrase')
        container_secrets['CRUK_SECRET_SNOWFLAKE_RSA_KEY_PASSPHRASE'] = snowflake_rsa_passphrase_secret

        fargate_task_definition.add_container(
            id='container',
            cpu=512,
            environment=task_definition_env_vars,
            secrets=container_secrets,
            essential=True,
            image=container_image,
            logging=log_driver,
            memory_limit_mib=1024,
            container_name=base_name
        )
        return fargate_task_definition

    # -------------------- CREATE SCHEDULED TASK --------------------

    def create_scheduled_task(self, base_name: str, fargate_task_definition: aws_ecs.FargateTaskDefinition,
                              cluster: aws_ecs.Cluster, security_group: aws_ec2.SecurityGroup,
                              subnets: list[aws_ec2.Subnet]):
        """
        Create an Event Bridge rule to execute an ECS task on a schedule.

        Parameters
        ----------
        base_name : str
            The base name of the Event Bridge rule to create.
        fargate_task_definition : aws_ecs.FargateTaskDefinition
            The ECS task to be executed.
        cluster : aws_ecs.Cluster
            The ECS cluster where the task is to be executed.
        security_group : aws_ec2.SecurityGroup
            The security group that will control network traffic into/out of the running container.
        subnets : list[aws_ec2.Subnet]
            A list of subnets where the docker container can run.

        Returns
        -------
        aws_ecs_patterns.ScheduledFargateTask
            The scheduled task.
        """
        scheduled_task_definition_options = aws_ecs_patterns.ScheduledFargateTaskDefinitionOptions(
            task_definition=fargate_task_definition
        )
        schedule = aws_applicationautoscaling.Schedule.cron(minute='45')
        scheduled_task = aws_ecs_patterns.ScheduledFargateTask(
            self, id='scheduled-task',
            scheduled_fargate_task_definition_options=scheduled_task_definition_options,
            schedule=schedule,
            cluster=cluster,
            desired_task_count=1,
            rule_name=base_name,
            security_groups=[security_group],
            subnet_selection=aws_ec2.SubnetSelection(subnets=subnets)
        )
        return scheduled_task
