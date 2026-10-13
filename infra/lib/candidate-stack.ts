import { Duration, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export interface CandidateStackProps extends StackProps {
  candidateId: 'alec' | 'hector';
  principalArn: string;
  publicJobsTable: dynamodb.ITable;
}

export class CandidateStack extends Stack {
  constructor(scope: Construct, id: string, props: CandidateStackProps) {
    super(scope, id, props);
    if (!/^arn:aws:iam::\d{12}:role\/[A-Za-z0-9+=,.@_/-]+$/.test(props.principalArn)) {
      throw new Error('candidate principal must be an IAM role ARN');
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
    props.publicJobsTable.grantReadData(role);
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:UpdateItem', 'dynamodb:Query'],
      resources: [stateTable.tableArn],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:ListBucket'], resources: [bucket.bucketArn],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject', 's3:PutObject'], resources: [bucket.arnForObjects('*')],
    }));
  }
}
