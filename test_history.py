#!/usr/bin/env python3
"""
Test script to create sample history entries
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from runtime.history_db import HistoryDB

def create_test_sessions():
    """Create some test sessions for UI testing"""
    db = HistoryDB()
    
    # Create test session 1
    session_id1 = db.start_session('./tests/sample.csv', 'General EDA Analysis', 5)
    print(f'Created test session 1: {session_id1}')
    
    # Add a plan version
    plan_items1 = [
        {'id': 'item_1', 'goal': 'Explore data distribution', 'plots': ['histogram'], 'columns': ['age', 'income']},
        {'id': 'item_2', 'goal': 'Check correlations', 'plots': ['correlation_matrix'], 'columns': ['all']}
    ]
    db.save_plan_version(session_id1, 1, plan_items1, approved=True)
    
    # Complete the session
    db.complete_session(session_id1, True, {'rows': 100, 'cols': 5}, './report/test1.md', './artifacts')
    
    # Create test session 2
    session_id2 = db.start_session('./tests/HousingData.csv', 'Housing Price Analysis', 8) 
    print(f'Created test session 2: {session_id2}')
    
    # Add a plan version
    plan_items2 = [
        {'id': 'item_1', 'goal': 'Price distribution analysis', 'plots': ['boxplot', 'histogram'], 'columns': ['price']},
        {'id': 'item_2', 'goal': 'Location insights', 'plots': ['scatter'], 'columns': ['lat', 'lng', 'price']}
    ]
    db.save_plan_version(session_id2, 1, plan_items2, approved=True)
    
    # Complete the session
    db.complete_session(session_id2, True, {'rows': 500, 'cols': 8}, './report/test2.md', './artifacts')
    
    # Create test session 3 (failed)
    session_id3 = db.start_session('./tests/Titanic-Dataset.csv', 'Survival Analysis', 6)
    print(f'Created test session 3: {session_id3}')
    
    # Complete the session as failed
    db.complete_session(session_id3, False, {'rows': 891, 'cols': 12}, error="API key error")
    
    # Check sessions
    sessions = db.get_session_history(10)
    print(f'\nTotal sessions in database: {len(sessions)}')
    for session in sessions:
        print(f"  Session {session['session_id']}: {session['user_goal']} - {'✅' if session['success'] else '❌'}")
    
    db.close()

if __name__ == "__main__":
    create_test_sessions()
