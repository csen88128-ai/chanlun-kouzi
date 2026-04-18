#!/usr/bin/env python3
"""
运行带监督机制的BTC缠论多智能体协作分析
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.workflow_supervised import run_analysis

if __name__ == "__main__":
    run_analysis()
