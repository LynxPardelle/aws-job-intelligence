import assert from 'node:assert/strict';
import { test } from 'node:test';
import { App } from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { CandidateStack } from '../lib/candidate-stack';
import { SharedStack } from '../lib/shared-stack';

const environment = { account: '111111111111', region: 'us-east-1' };

function stacks() {
  const app = new App();
  const shared = new SharedStack(app, 'aji-shared-dev', {
    env: environment,
    budgetEmail: 'alerts@example.invalid',
  });
  const alec = new CandidateStack(app, 'aji-alec-dev', {
    env: environment,
    candidateId: 'alec',
    principalArn: 'arn:aws:iam::111111111111:role/example-alec',
    publicJobsTable: shared.jobsTable,
  });
  const hector = new CandidateStack(app, 'aji-hector-dev', {
    env: environment,
    candidateId: 'hector',
    principalArn: 'arn:aws:iam::111111111111:role/example-hector',
    publicJobsTable: shared.jobsTable,
  });
  return { app, shared, alec, hector };
}

test('shared stack schedules collection at 08:00 Mexico City but leaves it disabled', () => {
  const { shared } = stacks();
  const template = Template.fromStack(shared);
  template.hasResourceProperties('AWS::Scheduler::Schedule', {
    ScheduleExpression: 'cron(0 8 * * ? *)',
    ScheduleExpressionTimezone: 'America/Mexico_City',
    State: 'DISABLED',
    FlexibleTimeWindow: { Mode: 'OFF' },
  });
  template.hasResourceProperties('AWS::Lambda::Function', {
    Runtime: 'python3.13', ReservedConcurrentExecutions: 1, Timeout: 60,
  });
  template.hasResourceProperties('AWS::DynamoDB::Table', { BillingMode: 'PAY_PER_REQUEST' });
  template.hasResourceProperties('AWS::Logs::LogGroup', { RetentionInDays: 7 });
  template.resourceCountIs('AWS::CloudWatch::Alarm', 1);
  template.resourceCountIs('AWS::Budgets::Budget', 1);
  const budgets = Object.values(template.findResources('AWS::Budgets::Budget')) as Array<{
    Properties: { Budget: { CostFilters?: unknown }; NotificationsWithSubscribers: Array<{
      Notification: { Threshold: number; ThresholdType: string }
    }> }
  }>;
  assert.equal(budgets[0].Properties.Budget.CostFilters, undefined);
  assert.deepEqual(budgets[0].Properties.NotificationsWithSubscribers.map(item =>
    [item.Notification.Threshold, item.Notification.ThresholdType]),
  [[3, 'ABSOLUTE_VALUE'], [5, 'ABSOLUTE_VALUE']]);
});

test('candidate resources are private, encrypted and isolated by identity', () => {
  const { alec, hector } = stacks();
  for (const [candidate, stack] of [['alec', alec], ['hector', hector]] as const) {
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true, BlockPublicPolicy: true,
        IgnorePublicAcls: true, RestrictPublicBuckets: true,
      },
      BucketEncryption: { ServerSideEncryptionConfiguration: [{
        ServerSideEncryptionByDefault: { SSEAlgorithm: 'AES256' },
      }] },
    });
    template.hasResourceProperties('AWS::DynamoDB::Table', { BillingMode: 'PAY_PER_REQUEST' });
    template.resourceCountIs('AWS::IAM::Role', 1);
    const rendered = JSON.stringify(template.toJSON());
    assert.ok(rendered.includes(`example-${candidate}`));
    assert.ok(!rendered.includes(`example-${candidate === 'alec' ? 'hector' : 'alec'}`));
  }
});

test('no stack provisions always-on or public gateway resources', () => {
  const { shared, alec, hector } = stacks();
  const forbidden = ['AWS::EC2::', 'AWS::RDS::', 'AWS::ECS::', 'AWS::EKS::',
    'AWS::ApiGateway::', 'AWS::Bedrock::'];
  for (const stack of [shared, alec, hector]) {
    const resources = Object.values(Template.fromStack(stack).toJSON().Resources) as Array<{ Type: string }>;
    for (const resource of resources) {
      assert.ok(!forbidden.some(prefix => resource.Type.startsWith(prefix)), resource.Type);
    }
  }
});

test('collector IAM allows only named log group, table and function resources', () => {
  const { shared } = stacks();
  const template = Template.fromStack(shared);
  const rendered = JSON.stringify(template.toJSON());
  assert.ok(!rendered.includes('AWSLambdaBasicExecutionRole'));
  const policies = Object.values(template.findResources('AWS::IAM::Policy')) as Array<{
    Properties: { PolicyDocument: { Statement: Array<{ Effect: string; Resource: unknown }> } }
  }>;
  for (const policy of policies) {
    for (const statement of policy.Properties.PolicyDocument.Statement) {
      if (statement.Effect === 'Allow') {
        assert.notEqual(statement.Resource, '*');
      }
    }
  }
});

test('candidate access role rejects a principal from another AWS account', () => {
  const app = new App();
  const shared = new SharedStack(app, 'aji-shared-dev', { env: environment });
  assert.throws(() => new CandidateStack(app, 'aji-alec-dev', {
    env: environment, candidateId: 'alec',
    principalArn: 'arn:aws:iam::222222222222:role/example-alec',
    publicJobsTable: shared.jobsTable,
  }), /same account/);
});
