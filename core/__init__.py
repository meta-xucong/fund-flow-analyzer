# -*- coding: utf-8 -*-
"""
核心模块
"""
from core.fetcher import DataFetcher
from core.storage import DataStorage
from core.analyzer import SectorStrengthCalculator, MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy, FundFlowStrategy
from core.report_generator import ReportGenerator
from core.explanation import AnalysisExplainer, PrincipleLibrary, explain_analysis

__all__ = [
    'DataFetcher',
    'DataStorage', 
    'SectorStrengthCalculator',
    'MarketAnalyzer',
    'MomentumStrategy',
    'ReversalStrategy',
    'FundFlowStrategy',
    'ReportGenerator',
    'AnalysisExplainer',
    'PrincipleLibrary',
    'explain_analysis'
]
