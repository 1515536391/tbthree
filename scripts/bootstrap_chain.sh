#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CHAIN_NAME="${CHAIN_NAME:-tbthree}"
MODULE_NAME="${MODULE_NAME:-tbthree}"

CHAIN_DIR="${ROOT_DIR}/chain/${CHAIN_NAME}"
OVERRIDES_DIR="${ROOT_DIR}/chain/overrides"

mkdir -p "${ROOT_DIR}/chain"
rm -rf "${CHAIN_DIR}"

echo "==> scaffold chain: ${CHAIN_NAME}"
( cd "${ROOT_DIR}/chain" && ignite scaffold chain "${CHAIN_NAME}" --no-module )

echo "==> scaffold module: ${MODULE_NAME}"
( cd "${CHAIN_DIR}" && ignite scaffold module "${MODULE_NAME}" -y )

echo "==> scaffold maps"
( cd "${CHAIN_DIR}" && ignite scaffold map edge \
  creatorAddr:string region:string status:string priorityPenalty:uint64 \
  bdScore:uint64 buScore:uint64 duScore:uint64 dudScore:uint64 \
  hmmProbT:uint64 hmmProbS:uint64 hmmProbM:uint64 \
  evidencePos:uint64 evidenceNeg:uint64 pendingProposalId:string \
  missedVotes:uint64 doubleSigns:uint64 blockParticipationPermil:uint64 \
  onTime:uint64 correct:uint64 resourceAnomaly:uint64 timeout:uint64 \
  complaints:uint64 anomalies:uint64 updatedAt:int64 \
  --module "${MODULE_NAME}" --index edgeAddr:string )

( cd "${CHAIN_DIR}" && ignite scaffold map task \
  vehicleAddr:string chosenEdgeAddr:string region:string status:string \
  taskType:string payloadHash:string logHashes:string \
  resultHash:string resultSig:string verified:bool \
  createdAt:int64 updatedAt:int64 \
  --module "${MODULE_NAME}" --index taskId:string )

( cd "${CHAIN_DIR}" && ignite scaffold map logSummary \
  taskId:string edgeAddr:string stage:string ts:int64 \
  cpuMs:uint64 memMbPeak:uint64 netKb:uint64 latencyMs:uint64 \
  resultHash:string \
  --module "${MODULE_NAME}" --index logHash:string )

( cd "${CHAIN_DIR}" && ignite scaffold map reputationPropagation \
  edgeAddr:string fromRegion:string toRegion:string repSnapshotHash:string \
  reason:string height:uint64 createdAt:int64 \
  --module "${MODULE_NAME}" --index propagationId:string )

( cd "${CHAIN_DIR}" && ignite scaffold map governanceProposal \
  edgeAddr:string status:string reason:string approvedBy:string decidedAt:int64 \
  --module "${MODULE_NAME}" --index proposalId:string )

echo "==> scaffold messages"
( cd "${CHAIN_DIR}" && ignite scaffold message register-edge edgeAddr:string region:string --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message submit-log-summary stage:string taskId:string logHash:string resultHash:string cpuMs:uint64 memMbPeak:uint64 latencyMs:uint64 netKb:uint64 ts:int64 --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message submit-task-feedback taskId:string accepted:bool --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message propagate-reputation edgeAddr:string fromRegion:string toRegion:string reason:string --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message report-task-event edgeAddr:string correct:bool onTime:bool resourceAnomaly:bool timeout:bool --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message report-consensus-event edgeAddr:string missedVotes:uint64 doubleSigns:uint64 blockParticipationPermil:uint64 --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message approve-proposal proposalId:string reason:string --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message reject-proposal proposalId:string reason:string --module "${MODULE_NAME}" )
( cd "${CHAIN_DIR}" && ignite scaffold message record-result taskId:string resultHash:string resultSig:string verified:bool --module "${MODULE_NAME}" )

echo "==> apply overrides"
if [ -d "${OVERRIDES_DIR}/x/${MODULE_NAME}" ]; then
  rsync -a "${OVERRIDES_DIR}/x/${MODULE_NAME}/" "${CHAIN_DIR}/x/${MODULE_NAME}/"
fi

echo "✅ bootstrap done: chain=${CHAIN_NAME}, module=${MODULE_NAME}"
