import path from 'node:path';
import { Duration, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';
import { Construct } from 'constructs';

export interface SharedStackProps extends StackProps {
  budgetEmail?: string;
}

export class SharedStack extends Stack {
  public readonly jobsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: SharedStackProps) {
    super(scope, id, props);
    Tags.of(this).add('Project', 'AWSJobIntelligence');
    Tags.of(this).add('Candidate', 'shared');
    Tags.of(this).add('Environment', 'dev');
    Tags.of(this).add('CostCenter', 'aji');

    this.jobsTable = new dynamodb.Table(this, 'PublicJobs', {
      tableName: 'aji-public-jobs-dev',
      partitionKey: { name: 'job_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: 'expires_at',
      removalPolicy: RemovalPolicy.RETAIN,
    });

    const logGroup = new logs.LogGroup(this, 'CollectorLogs', {
      logGroupName: '/aws/lambda/aji-collector-dev',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const collectorRole = new iam.Role(this, 'CollectorRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    collectorRole.addToPolicy(new iam.PolicyStatement({
      actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
      resources: [logGroup.logGroupArn],
    }));
    collectorRole.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:PutItem'], resources: [this.jobsTable.tableArn],
    }));
    const collector = new lambda.Function(this, 'Collector', {
      functionName: 'aji-collector-dev',
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: 'aji.lambda_handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../src'), {
        exclude: ['**/__pycache__/**', '**/*.pyc'],
      }),
      timeout: Duration.seconds(60),
      memorySize: 256,
      reservedConcurrentExecutions: 1,
      logGroup,
      role: collectorRole,
      environment: {
        AJI_JOBS_TABLE: this.jobsTable.tableName,
        AJI_ENABLED: 'false',
        AJI_MAX_SOURCES: '10',
        AJI_SOURCES_JSON: '[]',
      },
    });

    const invokeRole = new iam.Role(this, 'SchedulerInvokeRole', {
      assumedBy: new iam.ServicePrincipal('scheduler.amazonaws.com'),
    });
    invokeRole.addToPolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'], resources: [collector.functionArn],
    }));
    new scheduler.CfnSchedule(this, 'DailyCollector', {
      name: 'aji-collect-dev',
      scheduleExpression: 'cron(0 8 * * ? *)',
      scheduleExpressionTimezone: 'America/Mexico_City',
      flexibleTimeWindow: { mode: 'OFF' },
      state: 'DISABLED',
      target: {
        arn: collector.functionArn,
        roleArn: invokeRole.roleArn,
        retryPolicy: { maximumRetryAttempts: 2, maximumEventAgeInSeconds: 3600 },
      },
    });

    new cloudwatch.Alarm(this, 'CollectorErrors', {
      alarmName: 'aji-collector-errors-dev',
      metric: collector.metricErrors({ period: Duration.minutes(5) }),
      threshold: 1,
      evaluationPeriods: 1,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    if (props.budgetEmail) {
      new budgets.CfnBudget(this, 'MonthlyCostBudget', {
        budget: {
          budgetName: 'aji-account-guard-dev', budgetType: 'COST', timeUnit: 'MONTHLY',
          budgetLimit: { amount: 5, unit: 'USD' },
        },
        notificationsWithSubscribers: [3, 5].map(amount => ({
          notification: {
            comparisonOperator: 'GREATER_THAN', notificationType: 'ACTUAL',
            threshold: amount, thresholdType: 'ABSOLUTE_VALUE',
          },
          subscribers: [{ address: props.budgetEmail!, subscriptionType: 'EMAIL' }],
        })),
      });
    }
  }
}
