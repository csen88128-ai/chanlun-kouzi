#!/usr/bin/env python3
"""
运行BTC多智能体协作分析
"""
import sys
import os

# 添加路径
sys.path.insert(0, '/workspace/projects')

from multi_agents.workflow import run_analysis

if __name__ == '__main__':
    result = run_analysis()
