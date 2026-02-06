# Architecture Summary

后端入口为 src/apps/api/main.py，核心链路是 routes -> services -> models -> db。
前端入口为 src/apps/web/src/main.ts，与 API 通过统一封装交互。

详细结构与职责请参考：src/docs/ARCHITECTURE.md
