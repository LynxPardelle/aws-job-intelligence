import { App } from 'aws-cdk-lib';
import { CandidateStack } from '../lib/candidate-stack';
import { SharedStack } from '../lib/shared-stack';

const app = new App();
const account = app.node.tryGetContext('account') as string | undefined;
const region = app.node.tryGetContext('region') as string | undefined;
const alecPrincipalArn = app.node.tryGetContext('alecPrincipalArn') as string | undefined;
const hectorPrincipalArn = app.node.tryGetContext('hectorPrincipalArn') as string | undefined;
const budgetEmail = app.node.tryGetContext('budgetEmail') as string | undefined;

if (!account || !/^\d{12}$/.test(account) || !region || !alecPrincipalArn ||
    !hectorPrincipalArn || !budgetEmail) {
  throw new Error('synth requires account, region, alecPrincipalArn, hectorPrincipalArn and budgetEmail context');
}
if (alecPrincipalArn === hectorPrincipalArn) {
  throw new Error('candidate principals must be different');
}

const env = { account, region };
const shared = new SharedStack(app, 'aji-shared-dev', { env, budgetEmail });
new CandidateStack(app, 'aji-alec-dev', {
  env, candidateId: 'alec', principalArn: alecPrincipalArn,
  publicJobsTable: shared.jobsTable,
});
new CandidateStack(app, 'aji-hector-dev', {
  env, candidateId: 'hector', principalArn: hectorPrincipalArn,
  publicJobsTable: shared.jobsTable,
});
