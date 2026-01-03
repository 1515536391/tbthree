<template>
  <div class="audit">
    <div class="top">
      <div class="title"><i class="el-icon-finished"></i> 日志审计 (TB32)</div>
      <div class="controls">
        <el-input v-model="taskId" size="mini" placeholder="输入 taskId，例如 demo-A-0001" style="width: 260px" />
        <el-button size="mini" type="primary" icon="el-icon-search" @click="load">查询</el-button>
        <el-button size="mini" icon="el-icon-refresh" @click="reload">刷新</el-button>
      </div>
    </div>

    <div class="panel">
      <div class="hint">链上只存 hash + 元数据；后端 DB 存明细。此处做 hash 对照校验。</div>
      <el-table :data="rows" size="mini" style="width: 100%" :row-class-name="rowClass">
        <el-table-column prop="stage" label="stage" width="100"></el-table-column>
        <el-table-column prop="ts" label="ts" width="140"></el-table-column>
        <el-table-column prop="logHash" label="chainLogHash" min-width="260">
          <template slot-scope="s"><span class="mono">{{ s.row.logHash }}</span></template>
        </el-table-column>
        <el-table-column prop="dbLogHash" label="dbLogHash" min-width="260">
          <template slot-scope="s"><span class="mono">{{ s.row.dbLogHash || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="match" label="match" width="80">
          <template slot-scope="s">
            <el-tag v-if="s.row.match" type="success" size="mini">MATCH</el-tag>
            <el-tag v-else type="danger" size="mini">MISMATCH</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="txHash" label="txHash" min-width="220">
          <template slot-scope="s"><span class="mono">{{ s.row.txHash || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="height" label="height" width="90"></el-table-column>
      </el-table>
    </div>

    <div class="panel" v-if="rows.length">
      <div class="hint">点击行可展开查看 DB 明细 JSON（脱敏后）。</div>
      <el-collapse>
        <el-collapse-item v-for="r in rows" :key="r.logHash" :title="`${r.stage} · ${r.logHash.slice(0, 10)}…`">
          <pre class="json">{{ pretty(r.detail) }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/tb3';

export default {
  name: 'LogsAudit',
  data() {
    return {
      taskId: 'demo-A-0001',
      rows: [],
    };
  },
  mounted() {
    this.reload();
    this.$root.$on('tb3:refresh', this.reload);
  },
  beforeDestroy() {
    this.$root.$off('tb3:refresh', this.reload);
  },
  methods: {
    rowClass({ row }) {
      return row.match ? '' : 'row--bad';
    },
    pretty(obj) {
      try {
        return JSON.stringify(obj, null, 2);
      } catch (e) {
        return String(obj);
      }
    },
    async load() {
      if (!this.taskId) return;
      try {
        const res = await api.auditLogs(this.taskId);
        this.rows = res.data.items || [];
        this.$message.success(`加载完成：${this.rows.length} 条`);
      } catch (e) {
        const msg = e?.response?.data?.detail || e.message;
        this.$message.error(`查询失败：${msg}`);
      }
    },
    reload() {
      // keep current taskId
      if (this.taskId) this.load();
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/styles/theme.scss';

.audit {
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

.controls {
  display: flex;
  align-items: center;
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

.json {
  margin: 0;
  padding: 12px;
  border-radius: 12px;
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(255,255,255,0.10);
  overflow: auto;
  max-height: 320px;
  color: rgba(255,255,255,0.85);
}

::v-deep .row--bad td {
  background: rgba(255,92,210,0.08) !important;
}
</style>
