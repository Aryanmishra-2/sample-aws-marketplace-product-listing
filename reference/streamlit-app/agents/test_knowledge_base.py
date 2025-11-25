import boto3
import json

class LocalKnowledgeBaseTester:
    def __init__(self, knowledge_base_id=None):
        self.bedrock = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        self.knowledge_base_id = knowledge_base_id or "TEST_KB_ID"
    
    def test_query(self, query):
        """Test Knowledge Base query locally"""
        try:
            response = self.bedrock.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.knowledge_base_id,
                        'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0'
                    }
                }
            )
            return {
                'answer': response['output']['text'],
                'sources': response.get('citations', [])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def test_validation_scenarios(self):
        """Test common validation scenarios"""
        test_cases = [
            "What are valid product ID formats for AWS Marketplace?",
            "How to fix pricing dimension validation errors?",
            "What causes metering_failed to be true?",
            "Steps to troubleshoot CloudFormation deployment failures",
            "Valid email format requirements for marketplace"
        ]
        
        results = {}
        for query in test_cases:
            print(f"Testing: {query}")
            result = self.test_query(query)
            results[query] = result
            print(f"Answer: {result.get('answer', result.get('error'))[:100]}...")
            print("-" * 50)
        
        return results

if __name__ == "__main__":
    # Replace with your actual Knowledge Base ID
    kb_id = input("Enter Knowledge Base ID (or press Enter for mock): ").strip()
    
    tester = LocalKnowledgeBaseTester(kb_id if kb_id else None)
    
    # Interactive testing
    while True:
        query = input("\nEnter test query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        result = tester.test_query(query)
        print(f"\nAnswer: {result.get('answer', result.get('error'))}")
        
        if 'sources' in result:
            print(f"Sources: {len(result['sources'])} documents found")