#!/usr/bin/env python3
"""
Demo script for Automated EDA & Visualization system
"""
import os
import sys
sys.path.append('.')

from main import EDAOrchestrator


def demo_without_llm():
    """Demo the system using fallback modes (no LLM required)"""
    print("🎯 Automated EDA Demo (Fallback Mode)")
    print("=" * 50)
    print("This demo runs without requiring a DeepSeek API key")
    print("It uses deterministic fallback modes for all agents")
    print()
    
    # Create orchestrator with mock API key
    orchestrator = EDAOrchestrator(api_key="demo_key")
    
    # Replace LLM client with None to force fallback modes
    orchestrator.llm_client = None
    orchestrator.planner.llm_client = None
    orchestrator.coder.llm_client = None
    orchestrator.critic.llm_client = None
    orchestrator.reporter.llm_client = None
    
    # Run EDA analysis
    result = orchestrator.run_eda(
        csv_path="tests/sample.csv",
        user_goal="Demo EDA analysis",
        max_items=6
    )
    
    if result["success"]:
        print("\n🎉 Demo completed successfully!")
        print(f"📊 Generated {len(result['highlights'])} analyses")
        print(f"🖼️  Plots saved to: {result['artifacts_dir']}")
        print(f"📝 Report: {result['report_path']}")
        print(f"📋 Log: {result['log_path']}")
        
        # Show some highlights
        print("\n📈 Analysis Highlights:")
        for i, highlight in enumerate(result['highlights'][:3], 1):
            print(f"  {i}. {highlight['title']}")
            for artifact in highlight['artifacts']:
                filename = artifact.split('/')[-1]
                print(f"     📊 {filename}")
        
        print(f"\n🎯 Next Questions:")
        for question in result['report']['next_questions'][:3]:
            print(f"  • {question}")
        
        return True
    else:
        print(f"\n❌ Demo failed: {result['error']}")
        return False


def demo_with_llm():
    """Demo the system with real LLM (requires API key)"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not api_key:
        print("⚠️  No DEEPSEEK_API_KEY found in environment")
        print("   Set it with: export DEEPSEEK_API_KEY='your_key_here'")
        print("   Or run the fallback demo instead")
        return False
    
    print("🤖 Automated EDA Demo (LLM Mode)")
    print("=" * 50)
    print("This demo uses real DeepSeek LLM for intelligent analysis")
    print()
    
    # Create orchestrator with real LLM
    orchestrator = EDAOrchestrator(api_key=api_key)
    
    # Run EDA analysis
    result = orchestrator.run_eda(
        csv_path="tests/sample.csv",
        user_goal="Focus on transaction patterns and seasonality",
        max_items=8
    )
    
    if result["success"]:
        print("\n🎉 LLM Demo completed successfully!")
        print(f"📊 Generated {len(result['highlights'])} analyses")
        print(f"🖼️  Plots saved to: {result['artifacts_dir']}")
        print(f"📝 Report: {result['report_path']}")
        print(f"📋 Log: {result['log_path']}")
        return True
    else:
        print(f"\n❌ LLM Demo failed: {result['error']}")
        return False


def main():
    """Main demo function"""
    print("🚀 Automated EDA & Visualization Demo")
    print("=" * 60)
    print()
    
    # Check if sample data exists
    if not os.path.exists("tests/sample.csv"):
        print("❌ Sample data not found: tests/sample.csv")
        print("   Please run this from the automated_eda directory")
        return False
    
    # Try LLM demo first, fallback to no-LLM demo
    if not demo_with_llm():
        print("\n" + "="*60)
        demo_without_llm()
    
    print("\n" + "="*60)
    print("🎯 Demo completed! Check the generated files:")
    print("   📁 artifacts/ - Generated plots")
    print("   📁 report/ - Markdown report")
    print("   📁 logs/ - Execution logs")
    print()
    print("💡 To use with your own data:")
    print("   python main.py your_data.csv --goal 'Your analysis goal'")


if __name__ == "__main__":
    main()
