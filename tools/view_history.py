#!/usr/bin/env python3
"""
CLI tool for viewing EDA history
"""
import os
import sys
import json
import argparse
from tabulate import tabulate
from runtime.history_db import HistoryDB

def format_timestamp(ts):
    """Format timestamp for display"""
    return ts.split("T")[0] + " " + ts.split("T")[1][:8]

def show_sessions(db: HistoryDB, limit: int = 10):
    """Show recent sessions"""
    sessions = db.get_session_history(limit)
    
    # Format for display
    rows = []
    for s in sessions:
        rows.append([
            s["session_id"],
            format_timestamp(s["timestamp"]),
            os.path.basename(s["csv_path"]),
            s["user_goal"][:30] + "..." if s["user_goal"] and len(s["user_goal"]) > 30 else s["user_goal"],
            "✅" if s["success"] else "❌",
            s["plan_versions"],
            f"{s['successful_executions']}/{s['executions']}"
        ])
    
    headers = ["ID", "Date", "Dataset", "Goal", "Status", "Plans", "Success/Total"]
    print("\n🗂️  Recent EDA Sessions:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def show_session_details(db: HistoryDB, session_id: int):
    """Show detailed information about a specific session"""
    details = db.get_session_details(session_id)
    
    # Basic info
    print(f"\n📊 Session {session_id} Details")
    print("=" * 50)
    print(f"Date: {format_timestamp(details['timestamp'])}")
    print(f"Dataset: {details['csv_path']}")
    print(f"Goal: {details['user_goal']}")
    print(f"Status: {'✅ Success' if details['success'] else '❌ Failed'}")
    if details['error']:
        print(f"Error: {details['error']}")
    
    # Plan versions
    print("\n📋 Plan Versions:")
    for plan in details['plan_versions']:
        print(f"\nVersion {plan['version_number']}" + 
              (" (Approved)" if plan['approved'] else ""))
        if plan['user_feedback']:
            print(f"Feedback: {plan['user_feedback']}")
        items = json.loads(plan['plan_items'])
        for item in items:
            print(f"- {item.get('id')}: {item.get('goal')} " +
                  f"({', '.join(item.get('plots', []))})")
    
    # Execution results
    print("\n🔧 Executions:")
    for exec_result in details['execution_results']:
        status = "✅ Success" if exec_result['success'] else "❌ Failed"
        print(f"\nItem {exec_result['item_id']} - {status}")
        if exec_result['retry_count'] > 0:
            print(f"Retries: {exec_result['retry_count']}")
        if exec_result['error']:
            print(f"Error: {exec_result['error']}")

def main():
    parser = argparse.ArgumentParser(description="View EDA History")
    parser.add_argument("--list", "-l", action="store_true", 
                       help="List recent sessions")
    parser.add_argument("--session", "-s", type=int,
                       help="Show details for specific session ID")
    parser.add_argument("--limit", type=int, default=10,
                       help="Number of sessions to show (default: 10)")
    
    args = parser.parse_args()
    
    # Initialize DB
    db = HistoryDB()
    
    if args.session:
        show_session_details(db, args.session)
    else:
        show_sessions(db, args.limit)
    
    db.close()

if __name__ == "__main__":
    main()
