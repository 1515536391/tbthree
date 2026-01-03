<template>
  <div class="app-shell">
    <el-container class="app-container">
      <el-aside width="250px" class="aside">
        <div class="brand">
          <div class="brand__logo">TB3</div>
          <div class="brand__sub">可信交互引擎链 · MVP</div>
        </div>
        <el-menu :default-active="$route.path" class="menu" background-color="transparent" text-color="#ffffffcc" active-text-color="#5ce0ff" router>
          <el-menu-item index="/">
            <i class="el-icon-data-analysis"></i>
            <span slot="title">Dashboard</span>
          </el-menu-item>
          <el-menu-item index="/audit">
            <i class="el-icon-finished"></i>
            <span slot="title">日志审计</span>
          </el-menu-item>
          <el-menu-item index="/governance">
            <i class="el-icon-s-check"></i>
            <span slot="title">治理中心</span>
          </el-menu-item>
        </el-menu>
        <div class="aside__footer">
          <div class="pill">
            <i class="el-icon-link"></i>
            <span>单链模拟跨域 A/B</span>
          </div>
        </div>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header__left">
            <div class="title">TB3 可审计可信交互</div>
            <div class="subtitle">FastAPI 代签发交易 · Cosmos/ Ignite 单链 · 前端大屏</div>
          </div>
          <div class="header__right">
            <el-button size="mini" type="primary" plain icon="el-icon-refresh" @click="reloadAll">刷新</el-button>
            <el-button size="mini" type="success" icon="el-icon-magic-stick" @click="seedDemo" :loading="seeding">一键填充演示数据</el-button>
          </div>
        </el-header>
        <el-main class="main">
          <router-view :key="$route.fullPath" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { api } from '@/api/tb3';

export default {
  name: 'App',
  data() {
    return {
      seeding: false,
    };
  },
  methods: {
    reloadAll() {
      // emit a global refresh event
      this.$root.$emit('tb3:refresh');
    },
    async seedDemo() {
      this.seeding = true;
      try {
        const res = await api.demoSeed({ seed: 42, tasks_per_region: 15, days_span: 7, bad_edge_mode: true });
        this.$message.success(`Seed 完成：tasks=${res.data.tasks}, logs=${res.data.logs}, proposals=${res.data.proposals_after}`);
        this.reloadAll();
      } catch (e) {
        const msg = e?.response?.data?.detail || e.message;
        this.$message.error(`Seed 失败：${msg}`);
      } finally {
        this.seeding = false;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
@import '@/styles/theme.scss';

.app-shell {
  height: 100%;
}

.app-container {
  height: 100%;
}

.aside {
  background: rgba(0, 0, 0, 0.14);
  border-right: 1px solid rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(12px);
  padding: 14px 10px;
}

.brand {
  padding: 14px 14px 8px 14px;
}
.brand__logo {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 1px;
  color: rgba(255,255,255,0.9);
  background: radial-gradient(circle at 20% 20%, rgba(92,224,255,0.6), rgba(255,92,210,0.35));
  border: 1px solid rgba(255,255,255,0.18);
  box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}
.brand__sub {
  margin-top: 10px;
  color: rgba(255,255,255,0.72);
  font-size: 12px;
}

.menu {
  border-right: none;
}

.aside__footer {
  position: absolute;
  bottom: 14px;
  left: 10px;
  right: 10px;
}

.pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  color: rgba(255,255,255,0.7);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  background: rgba(0, 0, 0, 0.10);
  border-bottom: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(12px);
}

.title {
  font-weight: 700;
  letter-spacing: 0.3px;
}
.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255,255,255,0.55);
}

.main {
  height: calc(100vh - 60px);
  overflow: auto;
  padding: 18px;
}
</style>
