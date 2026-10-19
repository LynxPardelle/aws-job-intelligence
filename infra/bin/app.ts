import fs from 'node:fs';
import path from 'node:path';
import { App } from 'aws-cdk-lib';
import { CandidateStack } from '../lib/candidate-stack';
import { SharedStack } from '../lib/shared-stack';

const app = new App();
const account = app.node.tryGetContext('account') as string | undefined;
const region = app.node.tryGetContext('region') as string | undefined;
const alecPrincipalArn = app.node.tryGetContext('alecPrincipalArn') as string | undefined;
const hectorPrincipalArn = app.node.tryGetContext('hectorPrincipalArn') as string | undefined;
const budgetEmail = app.node.tryGetContext('budgetEmail') as string | undefined;
const activationConfigPath = app.node.tryGetContext('activationConfigPath') as string | undefined;

if (!account || !/^\d{12}$/.test(account) || !region || !alecPrincipalArn) {
  throw new Error('synth requires account, region and alecPrincipalArn context');
}
if (hectorPrincipalArn && alecPrincipalArn === hectorPrincipalArn) {
  throw new Error('candidate principals must be different');
}

type ActivationConfig = {
  sources: Array<{ source: 'greenhouse' | 'lever' | 'ashby'; board: string; company: string; enabled: true }>;
  maxSources: number;
  collectionEnabled: boolean;
  collectionScheduleEnabled: boolean;
  publicationEnabled: boolean;
  publicationScheduleEnabled: boolean;
};
let activation: ActivationConfig | undefined;
if (activationConfigPath !== undefined) {
  if (typeof activationConfigPath !== 'string' || !activationConfigPath.trim()) {
    throw new Error('activation config path required');
  }
  const raw: unknown = JSON.parse(fs.readFileSync(path.resolve(activationConfigPath), 'utf8'));
  const allowed = ['sources', 'maxSources', 'collectionEnabled', 'collectionScheduleEnabled',
    'publicationEnabled', 'publicationScheduleEnabled'];
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) ||
      Object.keys(raw).some(key => !allowed.includes(key)) ||
      !Array.isArray((raw as ActivationConfig).sources) ||
      !Number.isInteger((raw as ActivationConfig).maxSources) ||
      allowed.slice(2).some(key => typeof (raw as unknown as Record<string, unknown>)[key] !== 'boolean')) {
    throw new Error('invalid activation config');
  }
  activation = raw as ActivationConfig;
}

const env = { account, region };
const shared = new SharedStack(app, 'aji-shared-dev', {
  env, budgetEmail,
  sources: activation?.sources,
  maxSources: activation?.maxSources,
  collectionEnabled: activation?.collectionEnabled,
  collectionScheduleEnabled: activation?.collectionScheduleEnabled,
});
new CandidateStack(app, 'aji-alec-dev', {
  env, candidateId: 'alec', principalArn: alecPrincipalArn,
  publicJobsTable: shared.jobsTable,
  publicationEnabled: activation?.publicationEnabled,
  publicationScheduleEnabled: activation?.publicationScheduleEnabled,
});
if (hectorPrincipalArn) {
  new CandidateStack(app, 'aji-hector-dev', {
    env, candidateId: 'hector', principalArn: hectorPrincipalArn,
    publicJobsTable: shared.jobsTable,
  });
}
