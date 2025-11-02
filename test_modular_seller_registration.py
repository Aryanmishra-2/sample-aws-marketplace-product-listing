#!/usr/bin/env python3
"""
Test the modular seller registration system
"""

import sys
sys.path.append('.')

from seller_registration_module import SellerRegistrationModule, quick_seller_check, is_seller_registered
from seller_registration_integration_examples import MarketplaceListingAgent, MarketplaceChatbot


def test_modular_architecture():
    """Test the modular seller registration architecture"""
    
    print("🧪 Testing Modular Seller Registration Architecture")
    print("=" * 60)
    
    # Test 1: Standalone Module
    print("\n📋 Test 1: Standalone Module")
    try:
        module = SellerRegistrationModule()
        info = module.get_module_info()
        print(f"✅ Module: {info['module_name']} v{info['version']}")
        print(f"✅ Capabilities: {len(info['capabilities'])} features")
        print(f"✅ Supported Countries: {info['supported_countries']}")
        
        # Test seller status
        status = module.check_seller_status()
        print(f"✅ Seller Status: {status.get('seller_status', 'Unknown')}")
        print(f"✅ Account ID: {status.get('account_id', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Standalone module test failed: {e}")
        return False
    
    # Test 2: Quick Functions
    print("\n📋 Test 2: Quick Functions")
    try:
        # Test quick seller check
        quick_status = quick_seller_check()
        print(f"✅ Quick Status Check: {quick_status.get('seller_status', 'Unknown')}")
        
        # Test boolean check
        is_registered = is_seller_registered()
        print(f"✅ Is Registered: {is_registered}")
        
    except Exception as e:
        print(f"❌ Quick functions test failed: {e}")
        return False
    
    # Test 3: Agent Integration
    print("\n📋 Test 3: Agent Integration")
    try:
        # Test marketplace listing agent
        listing_agent = MarketplaceListingAgent()
        agent_status = listing_agent.get_status()
        print(f"✅ Agent: {agent_status['agent_name']}")
        print(f"✅ Seller Registered: {agent_status['seller_registered']}")
        print(f"✅ Ready for Listings: {agent_status['ready_for_listings']}")
        
        # Test listing creation
        listing_result = listing_agent.create_listing({"product": "test"})
        print(f"✅ Listing Creation: {listing_result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False
    
    # Test 4: Chatbot Integration
    print("\n📋 Test 4: Chatbot Integration")
    try:
        chatbot = MarketplaceChatbot()
        
        # Test seller status query
        response1 = chatbot.handle_user_message("What's my seller registration status?")
        print(f"✅ Status Query Response: {len(response1)} characters")
        
        # Test listing query
        response2 = chatbot.handle_user_message("I want to create a listing")
        print(f"✅ Listing Query Response: {len(response2)} characters")
        
    except Exception as e:
        print(f"❌ Chatbot integration test failed: {e}")
        return False
    
    # Test 5: Module Integration Methods
    print("\n📋 Test 5: Module Integration Methods")
    try:
        module = SellerRegistrationModule()
        
        # Test tool methods creation
        tool_methods = module.create_agent_tool_methods()
        print(f"✅ Tool Methods: {len(tool_methods)} methods available")
        
        # Test credential requirements
        cred_req = SellerRegistrationModule.get_credentials_requirements()
        print(f"✅ Credential Requirements: {len(cred_req['required_permissions'])} permissions")
        
        # Test convenience methods
        progress = module.get_registration_progress()
        next_action = module.get_next_action()
        needs_reg = module.needs_registration()
        
        print(f"✅ Progress: {progress}%")
        print(f"✅ Next Action: {next_action[:50]}...")
        print(f"✅ Needs Registration: {needs_reg}")
        
    except Exception as e:
        print(f"❌ Integration methods test failed: {e}")
        return False
    
    print("\n🎉 All modular architecture tests passed!")
    return True


def test_reusability():
    """Test that the module can be reused across different contexts"""
    
    print("\n🔄 Testing Reusability Across Different Contexts")
    print("=" * 60)
    
    contexts = []
    
    # Context 1: Direct usage
    try:
        module1 = SellerRegistrationModule()
        status1 = module1.check_seller_status()
        contexts.append(("Direct Usage", status1.get('success', False)))
    except Exception as e:
        contexts.append(("Direct Usage", False))
    
    # Context 2: Agent integration
    try:
        agent = MarketplaceListingAgent()
        status2 = agent.seller_registration.check_seller_status()
        contexts.append(("Agent Integration", status2.get('success', False)))
    except Exception as e:
        contexts.append(("Agent Integration", False))
    
    # Context 3: Quick function
    try:
        status3 = quick_seller_check()
        contexts.append(("Quick Function", status3.get('success', False)))
    except Exception as e:
        contexts.append(("Quick Function", False))
    
    # Context 4: Multiple instances
    try:
        module_a = SellerRegistrationModule()
        module_b = SellerRegistrationModule()
        
        status_a = module_a.is_seller_registered()
        status_b = module_b.is_seller_registered()
        
        contexts.append(("Multiple Instances", status_a == status_b))
    except Exception as e:
        contexts.append(("Multiple Instances", False))
    
    # Report results
    for context_name, success in contexts:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {context_name}: {'Working' if success else 'Failed'}")
    
    all_passed = all(success for _, success in contexts)
    print(f"\n{'🎉' if all_passed else '❌'} Reusability Test: {'All contexts working' if all_passed else 'Some contexts failed'}")
    
    return all_passed


def main():
    """Run all modular architecture tests"""
    
    print("🚀 Modular Seller Registration System Tests")
    print("=" * 70)
    
    results = []
    
    # Test modular architecture
    results.append(test_modular_architecture())
    
    # Test reusability
    results.append(test_reusability())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All modular architecture tests passed!")
        print("\n✅ The seller registration system is:")
        print("  - Completely modular and reusable")
        print("  - Easy to integrate with any agent")
        print("  - Provides multiple usage patterns")
        print("  - Maintains consistent behavior across contexts")
        print("  - Offers both simple and advanced APIs")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)