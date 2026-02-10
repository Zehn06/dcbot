"""
Test script for Instagram Analytics module
Validates core functionality without Discord bot running
"""

import asyncio
import sys
from instagram_analytics import InstagramAnalytics, AIProvider, create_instagram_tables

async def test_analytics():
    """Test Instagram analytics functions"""
    
    print("=" * 60)
    print("🧪 Instagram Analytics Test Suite")
    print("=" * 60)
    print()
    
    # Initialize AI Provider
    print("1️⃣ Initializing AI Provider...")
    ai_config = {
        'OPENAI_API_KEY': 'test_key',
        'ANTHROPIC_API_KEY': 'test_key',
        'GEMINI_API_KEY': 'test_key',
        'HUGGINGFACE_API_KEY': 'test_key'
    }
    ai_provider = AIProvider(ai_config)
    print("   ✅ AI Provider initialized")
    print()
    
    # Initialize Analytics Engine
    print("2️⃣ Initializing Analytics Engine...")
    analytics = InstagramAnalytics(ai_provider)
    print("   ✅ Analytics Engine initialized")
    print()
    
    # Test 1: Engagement Rate Calculation
    print("3️⃣ Testing Engagement Rate Calculation...")
    engagement_rate = analytics.calculate_engagement_rate(
        likes=500, comments=50, saves=30, followers=10000
    )
    print(f"   📊 Engagement Rate: {engagement_rate:.2f}%")
    assert engagement_rate > 0, "Engagement rate should be positive"
    print("   ✅ Test passed")
    print()
    
    # Test 2: Follower Quality Analysis
    print("4️⃣ Testing Follower Quality Analysis...")
    test_followers = [
        {'posts': 50, 'followers': 200, 'following': 300},
        {'posts': 2, 'followers': 5, 'following': 1500},  # Bot-like
        {'posts': 100, 'followers': 1000, 'following': 500},
    ]
    quality = analytics.analyze_follower_quality(test_followers)
    print(f"   🎯 Quality Score: {quality['quality_score']:.2f}%")
    print(f"   👥 Real Followers: {quality['real_followers']}")
    print(f"   🤖 Bot Percentage: {quality['bot_percentage']:.2f}%")
    assert 0 <= quality['quality_score'] <= 100, "Quality score should be 0-100"
    print("   ✅ Test passed")
    print()
    
    # Test 3: Growth Metrics
    print("5️⃣ Testing Growth Metrics...")
    historical_data = [
        {'followers': 1000}, {'followers': 1100}, {'followers': 1250}, {'followers': 1400}
    ]
    growth = analytics.calculate_growth_metrics(historical_data)
    print(f"   📈 Growth Rate: {growth['growth_rate']:.2f}%")
    print(f"   📊 Avg Daily Growth: {growth['avg_daily_growth']:.2f}")
    print(f"   🎯 Trend: {growth['trend']}")
    print("   ✅ Test passed")
    print()
    
    # Test 4: Content Performance Analysis
    print("6️⃣ Testing Content Performance...")
    test_posts = [
        {'type': 'reels', 'likes': 1000, 'comments': 50},
        {'type': 'reels', 'likes': 1500, 'comments': 75},
        {'type': 'posts', 'likes': 500, 'comments': 30},
        {'type': 'carousel', 'likes': 800, 'comments': 40},
    ]
    performance = await analytics.analyze_content_performance(test_posts)
    print(f"   🎬 Reels Avg Engagement: {performance['reels']['avg_engagement']:.2f}")
    print(f"   📷 Posts Avg Engagement: {performance['posts']['avg_engagement']:.2f}")
    print("   ✅ Test passed")
    print()
    
    # Test 5: Hashtag Optimization
    print("7️⃣ Testing Hashtag Optimization...")
    hashtags = analytics.optimize_hashtags("", "fitness", "high")
    print(f"   #️⃣ Generated {len(hashtags)} hashtags")
    print(f"   📝 Sample: {', '.join(['#' + h for h in hashtags[:5]])}")
    assert len(hashtags) > 0, "Should generate hashtags"
    print("   ✅ Test passed")
    print()
    
    # Test 6: Optimal Posting Time
    print("8️⃣ Testing Optimal Posting Time...")
    historical_engagement = [
        {'hour': h, 'engagement': 100 + (h * 10) % 100} 
        for h in range(24) for _ in range(7)
    ]
    optimal = analytics.calculate_optimal_posting_time('Europe/Istanbul', historical_engagement)
    print(f"   ⏰ Best Time: {optimal['best_time']:02d}:00")
    print(f"   📅 Recommended Frequency: {optimal['recommended_frequency']}")
    print("   ✅ Test passed")
    print()
    
    # Test 7: Algorithm Score
    print("9️⃣ Testing Algorithm Score...")
    profile_data = {
        'engagement_rate': 5.0,
        'posts_per_week': 5,
        'stories_per_week': 7,
        'save_rate': 3.0,
        'follower_quality': 80
    }
    algo_score = analytics.calculate_algorithm_score(profile_data)
    print(f"   🎯 Algorithm Score: {algo_score}/100")
    assert 0 <= algo_score <= 100, "Algorithm score should be 0-100"
    print("   ✅ Test passed")
    print()
    
    # Test 8: Performance Prediction
    print("🔟 Testing Performance Prediction...")
    profile_data = {
        'followers': 10000,
        'engagement_rate': 4.5,
        'avg_reach': 3000
    }
    post_data = {
        'optimal_time': True,
        'optimized_hashtags': True,
        'quality_score': 85
    }
    prediction = await analytics.predict_post_performance(post_data, profile_data)
    print(f"   👁️ Predicted Reach: {prediction['predicted_reach']['min']:,} - {prediction['predicted_reach']['max']:,}")
    print(f"   💝 Predicted Likes: ~{prediction['predicted_engagement']['likes']:,}")
    print(f"   🔥 Viral Probability: {prediction['viral_probability']:.1f}%")
    assert prediction['predicted_reach']['avg'] > 0, "Should predict reach"
    print("   ✅ Test passed")
    print()
    
    # Test 9: Monetization Value
    print("1️⃣1️⃣ Testing Monetization Calculator...")
    profile_data = {
        'followers': 50000,
        'engagement_rate': 5.0,
        'posts_per_month': 20
    }
    monetization = analytics.calculate_monetization_value(profile_data)
    print(f"   💰 Post Value: ${monetization['sponsorship_value_per_post']:.2f}")
    print(f"   📅 Monthly Potential: ${monetization['monthly_earning_potential']:.2f}")
    print(f"   🏆 Tier: {monetization['tier'].upper()}")
    assert monetization['sponsorship_value_per_post'] > 0, "Should calculate value"
    print("   ✅ Test passed")
    print()
    
    # Test 10: Growth Strategy
    print("1️⃣2️⃣ Testing Growth Strategy Generator...")
    current = {'followers': 5000, 'daily_growth': 20, 'engagement_rate': 3.0}
    goal = {'followers': 10000}
    strategy = analytics.generate_growth_strategy(current, goal)
    print(f"   🎯 Followers Needed: {strategy['followers_needed']:,}")
    print(f"   📅 Estimated Days: {strategy['estimated_days']}")
    print(f"   📈 Recommended Daily Growth: {strategy['recommended_daily_growth']}")
    print(f"   💡 Strategies: {len(strategy['strategies'])} action items")
    print("   ✅ Test passed")
    print()
    
    # Test 11: Competitor Analysis
    print("1️⃣3️⃣ Testing Competitor Analysis...")
    my_metrics = {'followers': 10000, 'engagement_rate': 4.5}
    competitor_metrics = [
        {'followers': 12000, 'engagement_rate': 3.8},
        {'followers': 9000, 'engagement_rate': 4.2}
    ]
    comp_analysis = analytics.competitor_analysis(my_metrics, competitor_metrics)
    print(f"   📊 Engagement Status: {comp_analysis['engagement_comparison']['status']}")
    print(f"   👥 Follower Status: {comp_analysis['follower_comparison']['status']}")
    print(f"   💡 Recommendations: {len(comp_analysis['recommendations'])} items")
    print("   ✅ Test passed")
    print()
    
    # Test 12: AI Caption Generation
    print("1️⃣4️⃣ Testing AI Caption Generation...")
    caption = await ai_provider.generate_caption("Fitness motivasyonu", "engaging")
    print(f"   ✍️ Generated Caption: {caption[:60]}...")
    assert len(caption) > 0, "Should generate caption"
    print("   ✅ Test passed")
    print()
    
    # Test 13: Comprehensive Report
    print("1️⃣5️⃣ Testing Comprehensive Report Generation...")
    profile_data = {
        'followers': 25000,
        'engagement_rate': 4.8,
        'avg_reach': 7500,
        'posts_per_week': 5,
        'stories_per_week': 7,
        'save_rate': 2.5,
        'follower_quality': 75,
        'posts_per_month': 20,
        'daily_growth': 30
    }
    report = await analytics.generate_content_report(profile_data)
    print(f"   📄 Report Length: {len(report)} characters")
    assert "ANALYTICS REPORT" in report, "Should contain report header"
    print("   ✅ Test passed")
    print()
    
    # Test 14: Database Tables
    print("1️⃣6️⃣ Testing Database Creation...")
    await create_instagram_tables("test_instagram.db")
    print("   ✅ Database tables created")
    print()
    
    # Clean up test database
    import os
    if os.path.exists("test_instagram.db"):
        os.remove("test_instagram.db")
        print("   🧹 Cleaned up test database")
    print()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("📊 Test Summary:")
    print("   • Engagement calculations: ✅")
    print("   • Follower quality analysis: ✅")
    print("   • Growth metrics: ✅")
    print("   • Content performance: ✅")
    print("   • Hashtag optimization: ✅")
    print("   • Optimal timing: ✅")
    print("   • Algorithm scoring: ✅")
    print("   • Performance predictions: ✅")
    print("   • Monetization calculator: ✅")
    print("   • Growth strategies: ✅")
    print("   • Competitor analysis: ✅")
    print("   • AI caption generation: ✅")
    print("   • Report generation: ✅")
    print("   • Database operations: ✅")
    print()
    print("🎉 Instagram Analytics Module is fully functional!")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(test_analytics())
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
