import path from 'node:path';
import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';
import { Construct } from 'constructs';

export interface CandidateStackProps extends StackProps {
  candidateId: 'alec' | 'hector';
  principalArn: string;
  publicJobsTable: dynamodb.ITable;
  publicationEnabled?: boolean;
  publicationScheduleEnabled?: boolean;
}

export class CandidateStack extends Stack {
  constructor(scope: Construct, id: string, props: CandidateStackProps) {
    super(scope, id, props);
    if (props.publicationScheduleEnabled && !props.publicationEnabled) {
      throw new Error('publication schedule requires enabled function');
    }
    if (!/^arn:aws:iam::\d{12}:(?:role|user)\/[A-Za-z0-9+=,.@_/-]+$/.test(props.principalArn)) {
      throw new Error('candidate principal must be an IAM role or user ARN');
    }
    if (props.principalArn.split(':')[4] !== this.account) {
      throw new Error('candidate principal must be in the same account');
    }
    Tags.of(this).add('Project', 'AWSJobIntelligence');
    Tags.of(this).add('Candidate', props.candidateId);
    Tags.of(this).add('Environment', 'dev');
    Tags.of(this).add('CostCenter', 'aji');

    const stateTable = new dynamodb.Table(this, 'PrivateState', {
      tableName: `aji-${props.candidateId}-state-dev`,
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: 'expires_at',
      removalPolicy: RemovalPolicy.RETAIN,
    });
    const bucket = new s3.Bucket(this, 'PrivateArtifacts', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      removalPolicy: RemovalPolicy.RETAIN,
      lifecycleRules: [{ id: 'expire-batches', prefix: 'batches/', expiration: Duration.days(30) }],
    });

    const role = new iam.Role(this, 'CandidateAccessRole', {
      roleName: `aji-${props.candidateId}-access-dev`,
      assumedBy: new iam.ArnPrincipal(props.principalArn),
      maxSessionDuration: Duration.hours(1),
    });
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:GetItem'], resources: [props.publicJobsTable.tableArn],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:Query'],
      resources: [`${props.publicJobsTable.tableArn}/index/collection-run-index`],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:UpdateItem', 'dynamodb:Query'],
      resources: [stateTable.tableArn],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject'], resources: [bucket.arnForObjects('batches/*')],
    }));

    const publisherLogs = new logs.LogGroup(this, 'PublisherLogs', {
      logGroupName: `/aws/lambda/aji-${props.candidateId}-publisher-dev`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const publisherRole = new iam.Role(this, 'PublisherRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    publisherRole.addToPolicy(new iam.PolicyStatement({
      actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
      resources: [publisherLogs.logGroupArn],
    }));
    publisherRole.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:GetItem'], resources: [props.publicJobsTable.tableArn],
    }));
    publisherRole.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:Query'],
      resources: [`${props.publicJobsTable.tableArn}/index/collection-run-index`],
    }));
    publisherRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject'], resources: [bucket.arnForObjects('config/search-policy.json')],
    }));
    publisherRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:PutObject'], resources: [bucket.arnForObjects('batches/*')],
    }));
    const publisher = new lambda.Function(this, 'Publisher', {
      functionName: `aji-${props.candidateId}-publisher-dev`,
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'aji.publisher_handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../src'), {
        exclude: ['**/__pycache__/**', '**/*.pyc'],
      }),
      timeout: Duration.seconds(60),
      memorySize: 256,
      reservedConcurrentExecutions: 1,
      logGroup: publisherLogs,
      role: publisherRole,
      environment: {
        AJI_CANDIDATE_ID: props.candidateId,
        AJI_PUBLISH_ENABLED: String(props.publicationEnabled === true),
        AJI_POLICY_KEY: 'config/search-policy.json',
        AJI_PRIVATE_BUCKET: bucket.bucketName,
        AJI_PUBLIC_TABLE: props.publicJobsTable.tableName,
      },
    });
    const invokeRole = new iam.Role(this, 'PublisherScheduleRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });
    invokeRole.addToPolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'], resources: [publisher.functionArn],
    }));
    new scheduler.CfnSchedule(this, 'DailyPublisher', {
      name: `aji-${props.candidateId}-publish-dev`,
      scheduleExpression: 'cron(30 8 * * ? *)',
      scheduleExpressionTimezone: 'America/Mexico_City',
      flexibleTimeWindow: { mode: 'OFF' },
      state: props.publicationScheduleEnabled ? 'ENABLED' : 'DISABLED',
      target: {
        arn: publisher.functionArn,
        roleArn: invokeRole.roleArn,
        retryPolicy: { maximumRetryAttempts: 2, maximumEventAgeInSeconds: 1800 },
      },
    });
    new cloudwatch.Alarm(this, 'PublisherErrors', {
      alarmName: `aji-${props.candidateId}-publisher-errors-dev`,
      metric: publisher.metricErrors({ period: Duration.minutes(5) }),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    new CfnOutput(this, 'CandidateRoleArn', { value: role.roleArn });
    new CfnOutput(this, 'ArtifactsBucketName', { value: bucket.bucketName });
  }
}
