<template>
  <div class="dash">
    <div class="dash__top">
      <div class="dash__left">
        <div class="kpis">
          <div class="kpi" v-for="k in kpiCards" :key="k.title">
            <div class="kpi__title">{{ k.title }}</div>
            <div class="kpi__value">{{ k.value }}</div>
            <div class="kpi__sub">{{ k.sub }}</div>
          </div>
        </div>
      </div>
      <div class="dash__right">
        <div class="filters">
          <el-select v-model="region" size="mini" placeholder="Region" style="width: 120px">
            <el-option label="All" value="ALL"></el-option>
            <el-option label="A" value="A"></el-option>
            <el-option label="B" value="B"></el-option>
          </el-select>
          <el-button size="mini" icon="el-icon-refresh" @click="reload">刷新</el-button>
        </div>
        <div class="alerts">
          <div class="alert" v-for="a in alerts" :key="a.key">
            <i :class="a.icon"></i>
            <div class="alert__text">
              <div class="alert__title">{{ a.title }}</div>
              <div class="alert__sub">{{ a.sub }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel__header">
          <div class="panel__title"><i class="el-icon-data-line"></i> 节点信誉排行 (score)</div>
          <div class="panel__hint">score=b+0.5u (链上定点数，前端换算)</div>
        </div>
        <div ref="scoreChart" class="chart"></div>
      </div>

      <div class="panel">
        <div class="panel__header">
          <div class="panel__title"><i class="el-icon-pie-chart"></i> HMM 状态分布</div>
          <div class="panel__hint">按 max(P(T),P(S),P(M)) 归类</div>
        </div>
        <div ref="hmmChart" class="chart"></div>
      </div>

      <div class="panel panel--wide">
        <div class="panel__header">
          <div class="panel__title"><i class="el-icon-s-grid"></i> Edge 节点列表</div>
          <div class="panel__hint">点击行跳转详情（b/d/u + HMM）</div>
        </div>
        <el-table :data="filteredEdges" size="mini" style="width:100%" @row-click="goEdge" :row-class-name="rowClass">
          <el-table-column prop="edgeAddr" label="edgeAddr" min-width="280"></el-table-column>
          <el-table-column prop="region" label="region" width="80"></el-table-column>
          <el-table-column prop="status" label="status" width="140"></el-table-column>
          <el-table-column label="score" width="90">
            <template slot-scope="scope">
              <span class="mono">{{ fmtScore(scope.row.score) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="HMM" width="140">
            <template slot-scope="scope">
              <span class="mono">T {{ fmtProb(scope.row.hmmProbT) }} / S {{ fmtProb(scope.row.hmmProbS) }} / M {{ fmtProb(scope.row.hmmProbM) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="b/d/u" min-width="180">
            <template slot-scope="scope">
              <span class="mono">b {{ fmtProb(scope.row.b) }} · d {{ fmtProb(scope.row.d) }} · u {{ fmtProb(scope.row.u) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { api } from '@/api/tb3';

const FP = 1000000;

export default {
  name: 'Dashboard',
  data() {
    return {
      region: 'ALL',
      edges: [],
      proposals: [],
      tasks: [],
      loading: false,
      chart1: null,
      chart2: null,
    };
  },
  computed: {
    filteredEdges() {
      if (this.region === 'ALL') return this.edges;
      return this.edges.filter((e) => e.region === this.region);
    },
    kpiCards() {
      const bad = this.edges.filter((e) => (this.toInt(e.score) / FP) < 0.3).length;
      const pending = this.proposals.filter((p) => (p.status || '').toUpperCase() === 'PENDING').length;
      return [
        { title: 'Edges', value: this.edges.length, sub: 'edge1~3' },
        { title: 'Tasks', value: this.tasks.length, sub: '全生命周期 on-chain' },
        { title: 'PENDING 提案', value: pending, sub: 'TB33 半自动治理' },
        { title: '低信誉节点', value: bad, sub: 'score < 0.3' },
      ];
    },
    alerts() {
      const a = [];
      const pending = this.proposals.filter((p) => (p.status || '').toUpperCase() === 'PENDING');
      if (pending.length > 0) {
        a.push({
          key: 'pending',
          icon: 'el-icon-warning',
          title: `发现 ${pending.length} 个待审批治理提案`,
          sub: '进入治理中心一键审批',
        });
      }
      const badEdges = this.edges.filter((e) => (this.toInt(e.score) / FP) < 0.3);
      if (badEdges.length > 0) {
        a.push({
          key: 'bad',
          icon: 'el-icon-bell',
          title: `${badEdges.length} 个节点信誉过低`,
          sub: '可能触发冻结/降权',
        });
      }
      if (a.length === 0) {
        a.push({ key: 'ok', icon: 'el-icon-success', title: '系统状态正常', sub: '暂无告警' });
      }
      return a;
    },
  },
  mounted() {
    this.reload();
    this.$root.$on('tb3:refresh', this.reload);
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeDestroy() {
    this.$root.$off('tb3:refresh', this.reload);
    window.removeEventListener('resize', this.resizeCharts);
  },
  methods: {
    toInt(v) {
      if (v === undefined || v === null) return 0;
      const n = parseInt(v, 10);
      return Number.isFinite(n) ? n : 0;
    },
    fmtScore(v) {
      return (this.toInt(v) / FP).toFixed(3);
    },
    fmtProb(v) {
      return (this.toInt(v) / FP).toFixed(2);
    },
    rowClass({ row }) {
      const score = this.toInt(row.score) / FP;
      if (score < 0.3) return 'row--bad';
      if ((row.status || '').includes('FROZEN')) return 'row--frozen';
      return '';
    },
    goEdge(row) {
      this.$router.push(`/edge/${row.edgeAddr}`);
    },
    resizeCharts() {
      if (this.chart1) this.chart1.resize();
      if (this.chart2) this.chart2.resize();
    },
    async reload() {
      this.loading = true;
      try {
        const [edgesRes, propsRes, tasksRes] = await Promise.all([
          api.edges(),
          api.proposals(),
          api.tasks(),
        ]);
        const edges = edgesRes.data.edge || edgesRes.data.edges || [];
        const props = propsRes.data.governanceProposal || propsRes.data.governanceProposals || [];
        const tasks = tasksRes.data.task || tasksRes.data.tasks || [];
        this.edges = edges;
        this.proposals = props;
        this.tasks = tasks;
        this.renderCharts();
      } catch (e) {
        const msg = e?.response?.data?.detail || e.message;
        this.$message.error(`加载失败：${msg}`);
      } finally {
        this.loading = false;
      }
    },
    renderCharts() {
      // score bar
      const dom1 = this.$refs.scoreChart;
      if (!this.chart1) this.chart1 = echarts.init(dom1);
      const data = this.filteredEdges
        .map((e) => ({ name: e.edgeAddr?.slice(0, 10) + '…', full: e.edgeAddr, score: this.toInt(e.score) / FP }))
        .sort((a, b) => b.score - a.score);

      this.chart1.setOption({
        grid: { left: 30, right: 20, top: 30, bottom: 50 },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const p = params[0];
            return `<div style="min-width:220px">
              <div><b>${p.data.full}</b></div>
              <div>score: <b>${p.data.score.toFixed(3)}</b></div>
            </div>`;
          },
        },
        xAxis: {
          type: 'category',
          data: data.map((d) => d.name),
          axisLabel: { color: 'rgba(255,255,255,0.6)', rotate: 25 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 1,
          axisLabel: { color: 'rgba(255,255,255,0.6)' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
        },
        series: [
          {
            type: 'bar',
            data,
            barWidth: 24,
            itemStyle: {
              color: (p) => {
                const s = p.data.score;
                if (s < 0.3) return 'rgba(255, 92, 210, 0.85)';
                if (s < 0.6) return 'rgba(255, 196, 0, 0.85)';
                return 'rgba(92, 224, 255, 0.85)';
              },
              borderRadius: [8, 8, 4, 4],
            },
          },
        ],
      });

      // hmm distribution pie
      const dom2 = this.$refs.hmmChart;
      if (!this.chart2) this.chart2 = echarts.init(dom2);
      const counts = { Trusted: 0, Suspicious: 0, Malicious: 0 };
      this.filteredEdges.forEach((e) => {
        const t = this.toInt(e.hmmProbT);
        const s = this.toInt(e.hmmProbS);
        const m = this.toInt(e.hmmProbM);
        const max = Math.max(t, s, m);
        if (max === m) counts.Malicious += 1;
        else if (max === s) counts.Suspicious += 1;
        else counts.Trusted += 1;
      });

      this.chart2.setOption({
        tooltip: { trigger: 'item' },
        series: [
          {
            type: 'pie',
            radius: ['42%', '70%'],
            avoidLabelOverlap: false,
            label: { color: 'rgba(255,255,255,0.75)' },
            labelLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } },
            data: [
              { value: counts.Trusted, name: 'Trusted', itemStyle: { color: 'rgba(92,224,255,0.85)' } },
              { value: counts.Suspicious, name: 'Suspicious', itemStyle: { color: 'rgba(255,196,0,0.85)' } },
              { value: counts.Malicious, name: 'Malicious', itemStyle: { color: 'rgba(255,92,210,0.85)' } },
            ],
          },
        ],
      });
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/styles/theme.scss';

.dash {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dash__top {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.kpi {
  @include glass-card;
  padding: 14px;
  position: relative;
  overflow: hidden;
}
.kpi:before {
  content: '';
  position: absolute;
  inset: -40px;
  background: radial-gradient(circle at 20% 10%, rgba(92,224,255,0.18), transparent 45%),
              radial-gradient(circle at 70% 30%, rgba(255,92,210,0.12), transparent 40%);
  transform: rotate(8deg);
}
.kpi__title {
  position: relative;
  font-size: 12px;
  color: rgba(255,255,255,0.65);
}
.kpi__value {
  position: relative;
  margin-top: 6px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.4px;
}
.kpi__sub {
  position: relative;
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255,255,255,0.55);
}

.filters {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 10px;
}

.alerts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert {
  @include glass-card;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.alert i {
  font-size: 20px;
  color: rgba(255,255,255,0.75);
}
.alert__title {
  font-weight: 700;
}
.alert__sub {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(255,255,255,0.6);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-auto-rows: minmax(280px, auto);
  gap: 16px;
}

.panel {
  @include glass-card;
  padding: 14px;
}

.panel--wide {
  grid-column: 1 / -1;
}

.panel__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 10px;
}
.panel__title {
  font-weight: 800;
}
.panel__hint {
  font-size: 12px;
  color: rgba(255,255,255,0.55);
}

.chart {
  width: 100%;
  height: 260px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

::v-deep .row--bad td {
  background: rgba(255,92,210,0.08) !important;
}
::v-deep .row--frozen td {
  background: rgba(255,196,0,0.08) !important;
}

@media (max-width: 1200px) {
  .dash__top {
    grid-template-columns: 1fr;
  }
  .kpis {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
