import assert from 'node:assert/strict';
import { test } from 'node:test';
import { App } from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
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
  template.hasResourceProperties('AWS::DynamoDB::Table', {
    BillingMode: 'PAY_PER_REQUEST',
    GlobalSecondaryIndexes: [{
      IndexName: 'collection-run-index',
      KeySchema: [
        { AttributeName: 'collection_run_id', KeyType: 'HASH' },
        { AttributeName: 'job_id', KeyType: 'RANGE' },
      ],
      Projection: { ProjectionType: 'ALL' },
    }],
  });
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
    template.resourceCountIs('AWS::IAM::Role', 3);
    template.hasResourceProperties('AWS::Scheduler::Schedule', {
      ScheduleExpression: 'cron(30 8 * * ? *)',
      ScheduleExpressionTimezone: 'America/Mexico_City',
      State: 'DISABLED',
    });
    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'python3.13', ReservedConcurrentExecutions: 1, Timeout: 60,
      Environment: { Variables: {
        AJI_CANDIDATE_ID: candidate,
        AJI_PUBLISH_ENABLED: 'false',
        AJI_POLICY_KEY: 'config/search-policy.json',
        AJI_PRIVATE_BUCKET: { Ref: Object.keys(template.findResources('AWS::S3::Bucket'))[0] },
        AJI_PUBLIC_TABLE: Match.anyValue(),
      } },
    });
    template.hasResourceProperties('AWS::Logs::LogGroup', { RetentionInDays: 7 });
    template.resourceCountIs('AWS::CloudWatch::Alarm', 1);
    template.hasOutput('CandidateRoleArn', {});
    template.hasOutput('ArtifactsBucketName', {});
    const rendered = JSON.stringify(template.toJSON());
    assert.ok(rendered.includes(`example-${candidate}`));
    assert.ok(!rendered.includes(`example-${candidate === 'alec' ? 'hector' : 'alec'}`));
  }
});

test('publisher can read public collection and write only its own candidate batch', () => {
  const { alec } = stacks();
  const template = Template.fromStack(alec);
  const policies = Object.values(template.findResources('AWS::IAM::Policy')) as Array<{
    Properties: { PolicyDocument: { Statement: Array<{
      Action: string | string[]; Resource: unknown; Effect: string
    }> } }
  }>;
  const rendered = JSON.stringify(policies);
  assert.ok(rendered.includes('dynamodb:GetItem'));
  assert.ok(rendered.includes('dynamodb:Query'));
  assert.ok(rendered.includes('collection-run-index'));
  assert.ok(rendered.includes('config/search-policy.json'));
  assert.ok(rendered.includes('batches/*'));
  for (const policy of policies) {
    for (const statement of policy.Properties.PolicyDocument.Statement) {
      if (statement.Effect === 'Allow') assert.notEqual(statement.Resource, '*');
    }
  }
});

test('daily candidate role can read its batch but cannot overwrite publisher manifests', () => {
  const { alec } = stacks();
  const policies = Template.fromStack(alec).findResources('AWS::IAM::Policy');
  const accessPolicy = Object.entries(policies).find(([id]) => id.startsWith('CandidateAccessRoleDefaultPolicy'));
  assert.ok(accessPolicy);
  const rendered = JSON.stringify(accessPolicy[1]);
  assert.ok(rendered.includes('s3:GetObject'));
  assert.ok(rendered.includes('batches/*'));
  assert.ok(!rendered.includes('s3:PutObject'));
  assert.ok(!rendered.includes('dynamodb:Scan'));
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

test('Alec access role can trust the existing same-account IAM user', () => {
  const app = new App();
  const shared = new SharedStack(app, 'aji-shared-dev', { env: environment });
  const alec = new CandidateStack(app, 'aji-alec-dev', {
    env: environment, candidateId: 'alec',
    principalArn: 'arn:aws:iam::111111111111:user/example-admin',
    publicJobsTable: shared.jobsTable,
  });
  const rendered = JSON.stringify(Template.fromStack(alec).toJSON());
  assert.ok(rendered.includes('arn:aws:iam::111111111111:user/example-admin'));
});
