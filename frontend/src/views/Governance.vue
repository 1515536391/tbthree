<template>
  <div class="gov">
    <div class="top">
      <div class="title"><i class="el-icon-s-check"></i> 治理中心 (TB33)</div>
      <div class="actions">
        <el-select v-model="filter" size="mini" style="width: 160px">
          <el-option label="All" value="ALL" />
          <el-option label="PENDING" value="PENDING" />
          <el-option label="APPROVED" value="APPROVED" />
          <el-option label="REJECTED" value="REJECTED" />
        </el-select>
        <el-button size="mini" icon="el-icon-refresh" @click="reload">刷新</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="hint">score < 0.3 自动生成治理提案；管理员审批后生效（降权 / 冻结任务资格 / 冻结共识资格）。</div>
      <el-table :data="filtered" size="mini" style="width:100%" :row-class-name="rowClass">
        <el-table-column prop="proposalId" label="proposalId" width="140"></el-table-column>
        <el-table-column prop="edgeAddr" label="edgeAddr" min-width="260"></el-table-column>
        <el-table-column prop="action" label="action" width="160"></el-table-column>
        <el-table-column prop="status" label="status" width="120">
          <template slot-scope="s">
            <el-tag v-if="(s.row.status||'').toUpperCase()==='PENDING'" type="warning" size="mini">PENDING</el-tag>
            <el-tag v-else-if="(s.row.status||'').toUpperCase()==='APPROVED'" type="success" size="mini">APPROVED</el-tag>
            <el-tag v-else type="info" size="mini">REJECTED</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="reason" min-width="240"></el-table-column>
        <el-table-column label="edgeStatus" width="150">
          <template slot-scope="s">
            <span class="mono">{{ edgeStatus(s.row.edgeAddr) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="s">
            <el-button size="mini" type="success" icon="el-icon-check" @click="approve(s.row)" :disabled="!isPending(s.row)">审批</el-button>
            <el-button size="mini" type="danger" plain icon="el-icon-close" @click="openReject(s.row)" :disabled="!isPending(s.row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog title="驳回提案" :visible.sync="rejectDialog" width="420px">
      <el-input v-model="rejectReason" placeholder="请输入驳回原因" />
      <span slot="footer" class="dialog-footer">
        <el-button @click="rejectDialog=false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确认驳回</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { api } from '@/api/tb3';

export default {
  name: 'Governance',
  data() {
    return {
      filter: 'ALL',
      proposals: [],
      edges: [],
      rejectDialog: false,
      rejectReason: '',
      target: null,
    };
  },
  computed: {
    filtered() {
      if (this.filter === 'ALL') return this.proposals;
      return this.proposals.filter((p) => (p.status || '').toUpperCase() === this.filter);
    },
  },
  mounted() {
    this.reload();
    this.$root.$on('tb3:refresh', this.reload);
  },
  beforeDestroy() {
    this.$root.$off('tb3:refresh', this.reload);
  },
  methods: {
    isPending(p) {
      return (p.status || '').toUpperCase() === 'PENDING';
    },
    rowClass({ row }) {
      if (this.isPending(row)) return 'row--pending';
      if ((row.status || '').toUpperCase() === 'APPROVED') return 'row--approved';
      return '';
    },
    edgeStatus(addr) {
      const e = this.edges.find((x) => x.edgeAddr === addr);
      return e ? e.status : '-';
    },
    async reload() {
      try {
        const [p, e] = await Promise.all([api.proposals(), api.edges()]);
        this.proposals = p.data.governanceProposal || p.data.governanceProposals || [];
        this.edges = e.data.edge || e.data.edges || [];
      } catch (err) {
        const msg = err?.response?.data?.detail || err.message;
        this.$message.error(`加载失败：${msg}`);
      }
    },
    async approve(row) {
      try {
        await api.approveProposal(row.proposalId);
        this.$message.success('已审批');
        this.reload();
      } catch (err) {
        const msg = err?.response?.data?.detail || err.message;
        this.$message.error(`审批失败：${msg}`);
      }
    },
    openReject(row) {
      this.target = row;
      this.rejectReason = '';
      this.rejectDialog = true;
    },
    async confirmReject() {
      if (!this.target) return;
      try {
        await api.rejectProposal(this.target.proposalId, this.rejectReason || 'no reason');
        this.$message.success('已驳回');
        this.rejectDialog = false;
        this.reload();
      } catch (err) {
        const msg = err?.response?.data?.detail || err.message;
        this.$message.error(`驳回失败：${msg}`);
      }
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/styles/theme.scss';

.gov {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-weight: 900;
  font-size: 18px;
}

.actions {
  display: flex;
  gap: 10px;
}

.panel {
  @include glass-card;
  padding: 14px;
}

.hint {
  color: rgba(255,255,255,0.6);
  font-size: 12px;
  margin-bottom: 10px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

::v-deep .row--pending td {
  background: rgba(255,196,0,0.08) !important;
}
::v-deep .row--approved td {
  background: rgba(92,224,255,0.06) !important;
}
</style>
