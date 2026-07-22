#!/usr/bin/env bash
# AI HOT 简报 → GitHub Pages 自动推送脚本
# 前置：本地已 git init，且 remote origin 已配置为带 PAT 的 HTTPS 地址
#       （形如 https://USER:TOKEN@github.com/USER/REPO.git）
set -e
cd "$(dirname "$0")"

git add -A
if git diff --cached --quiet; then
  echo "没有改动，跳过提交"
else
  git commit -m "AI HOT 简报更新 $(date +%Y-%m-%d_%H:%M)"
fi

git push
echo "已推送到 GitHub，GitHub Pages 通常在 1 分钟内完成构建并更新。"
