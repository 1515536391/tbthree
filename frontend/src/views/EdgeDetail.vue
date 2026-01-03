<template>
  <div class="edge">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/' }">Dashboard</el-breadcrumb-item>
      <el-breadcrumb-item>Edge Detail</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="hero" v-if="edgeObj">
      <div class="hero__left">
        <div class="addr">{{ edgeObj.edgeAddr }}</div>
        <div class="meta">
          <span class="tag">region: {{ edgeObj.region }}</span>
          <span class="tag">status: {{ edgeObj.status }}</span>
          <span class="tag">penalty: {{ edgeObj.priorityPenalty }}</span>
        </div>
      </div>
      <div class="hero__right">
        <div class="score">
          <div class="score__label">信誉 score</div>
          <div class="score__value">{{ fmt(edgeObj.score) }}</div>
          <div class="score__hint">阈值: 0.300 (TB33)</div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel__title"><i class="el-icon-pie-chart"></i> 主观逻辑 b / d / u</div>
        <div ref="bduChart" class="chart"></div>
        <div class="mini">
          b={{ fmt(edgeObj.b) }} · d={{ fmt(edgeObj.d) }} · u={{ fmt(edgeObj.u) }}
        </div>
      </div>

      <div class="panel">
        <div class="panel__title"><i class="el-icon-data-line"></i> HMM 三态概率</div>
        <div ref="hmmBar" class="chart"></div>
        <div class="mini">
          T={{ fmt(edgeObj.hmmProbT) }} · S={{ fmt(edgeObj.hmmProbS) }} · M={{ fmt(edgeObj.hmmProbM) }}
        </div>
      </div>

      <div class="panel panel--wide">
        <div class="panel__title"><i class="el-icon-time"></i> 最近交互时间线（按日志摘要）</div>
        <el-table :data="recentLogs" size="mini" style="width:100%">
          <el-table-column prop="ts" label="ts" width="140"></el-table-column>
          <el-table-column prop="taskId" label="taskId" min-width="200"></el-table-column>
          <el-table-column prop="stage" label="stage" width="100"></el-table-column>
          <el-table-column label="latency(ms)" width="120"><template slot-scope="s">{{ s.row.latencyMs }}</template></el-table-column>
          <el-table-column label="cpu" width="90"><template slot-scope="s">{{ s.row.cpuMs }}</template></el-table-column>
          <el-table-column label="mem" width="90"><template slot-scope="s">{{ s.row.memMbPeak }}</template></el-table-column>
          <el-table-column label="logHash" min-width="260"><template slot-scope="s"><span class="mono">{{ s.row.logHash }}</span></template></el-table-column>
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
  name: 'EdgeDetail',
  data() {
    return {
      edgeObj: null,
      logs: [],
      c1: null,
      c2: null,
    };
  },
  computed: {
    addr() {
      return this.$route.params.addr;
    },
    recentLogs() {
      // filter by edgeAddr
      const items = this.logs.filter((l) => l.edgeAddr === this.addr);
      items.sort((a, b) => parseInt(b.ts, 10) - parseInt(a.ts, 10));
      return items.slice(0, 20);
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
      const n = parseInt(v || 0, 10);
      return Number.isFinite(n) ? n : 0;
    },
    fmt(v) {
      return (this.toInt(v) / FP).toFixed(3);
    },
    resizeCharts() {
      if (this.c1) this.c1.resize();
      if (this.c2) this.c2.resize();
    },
    async reload() {
      try {
        const [edgeRes, logsRes] = await Promise.all([
          api.edge(this.addr),
          api.logsAll(),
        ]);
        this.edgeObj = edgeRes.data.edge || edgeRes.data;
        const items = logsRes.data.logSummary || logsRes.data.logSummaries || [];
        this.logs = items;
        this.renderCharts();
      } catch (e) {
        const msg = e?.response?.data?.detail || e.message;
        this.$message.error(`加载失败：${msg}`);
      }
    },
    renderCharts() {
      if (!this.edgeObj) return;
      const b = this.toInt(this.edgeObj.b) / FP;
      const d = this.toInt(this.edgeObj.d) / FP;
      const u = this.toInt(this.edgeObj.u) / FP;

      const dom1 = this.$refs.bduChart;
      if (!this.c1) this.c1 = echarts.init(dom1);
      this.c1.setOption({
        tooltip: { trigger: 'item' },
        series: [
          {
            type: 'pie',
            radius: ['45%', '70%'],
            label: { color: 'rgba(255,255,255,0.75)' },
            labelLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } },
            data: [
              { value: b, name: 'b (belief)', itemStyle: { color: 'rgba(92,224,255,0.85)' } },
              { value: d, name: 'd (disbelief)', itemStyle: { color: 'rgba(255,92,210,0.85)' } },
              { value: u, name: 'u (uncertainty)', itemStyle: { color: 'rgba(255,196,0,0.85)' } },
            ],
          },
        ],
      });

      const t = this.toInt(this.edgeObj.hmmProbT) / FP;
      const s = this.toInt(this.edgeObj.hmmProbS) / FP;
      const m = this.toInt(this.edgeObj.hmmProbM) / FP;

      const dom2 = this.$refs.hmmBar;
      if (!this.c2) this.c2 = echarts.init(dom2);
      this.c2.setOption({
        grid: { left: 30, right: 20, top: 20, bottom: 30 },
        xAxis: {
          type: 'category',
          data: ['Trusted', 'Suspicious', 'Malicious'],
          axisLabel: { color: 'rgba(255,255,255,0.6)' },
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
            data: [
              { value: t, itemStyle: { color: 'rgba(92,224,255,0.85)' } },
              { value: s, itemStyle: { color: 'rgba(255,196,0,0.85)' } },
              { value: m, itemStyle: { color: 'rgba(255,92,210,0.85)' } },
            ],
            barWidth: 42,
            itemStyle: { borderRadius: [8, 8, 4, 4] },
          },
        ],
      });
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/styles/theme.scss';

.edge {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero {
  @include glass-card;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.addr {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 13px;
  opacity: 0.95;
}

.meta {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tag {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  font-size: 12px;
  color: rgba(255,255,255,0.75);
}

.score__label {
  font-size: 12px;
  color: rgba(255,255,255,0.6);
}
.score__value {
  font-size: 34px;
  font-weight: 800;
  margin-top: 6px;
}
.score__hint {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255,255,255,0.55);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel {
  @include glass-card;
  padding: 14px;
}

.panel--wide {
  grid-column: 1 / -1;
}

.panel__title {
  font-weight: 800;
  margin-bottom: 10px;
}

.chart {
  width: 100%;
  height: 240px;
}

.mini {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.6);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

@media (max-width: 1200px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
