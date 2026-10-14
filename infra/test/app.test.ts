import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('first-PC synth omits the project budget until its cost tag is active', () => {
  const infraDir = path.resolve(__dirname, '../..');
  const result = spawnSync(process.execPath, [
    path.join(infraDir, 'node_modules/aws-cdk/bin/cdk'),
    'synth',
    'aji-shared-dev', 'aji-alec-dev',
    '-c', 'account=111111111111',
    '-c', 'region=us-east-1',
    '-c', 'alecPrincipalArn=arn:aws:iam::111111111111:user/example-admin',
    '--quiet',
  ], { cwd: infraDir, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const template = JSON.parse(fs.readFileSync(
    path.join(infraDir, 'cdk.out/aji-shared-dev.template.json'), 'utf8',
  )) as { Resources: Record<string, { Type: string }> };
  assert.ok(Object.values(template.Resources).every(resource =>
    resource.Type !== 'AWS::Budgets::Budget'));
});
