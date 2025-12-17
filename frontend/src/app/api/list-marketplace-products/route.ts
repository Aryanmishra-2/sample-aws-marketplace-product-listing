import { NextRequest, NextResponse } from 'next/server';
import { 
  MarketplaceCatalogClient, 
  ListEntitiesCommand,
  DescribeEntityCommand 
} from '@aws-sdk/client-marketplace-catalog';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = body;

    if (!aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing credentials' },
        { status: 400 }
      );
    }

    const catalogClient = new MarketplaceCatalogClient({
      region: 'us-east-1',
      credentials: {
        accessKeyId: aws_access_key_id,
        secretAccessKey: aws_secret_access_key,
        sessionToken: aws_session_token,
      },
    });

    // List all SaaS products
    const listCommand = new ListEntitiesCommand({
      Catalog: 'AWSMarketplace',
      EntityType: 'SaaSProduct',
    });

    const response = await catalogClient.send(listCommand);
    
    const products = (response.EntitySummaryList || []).map((entity) => ({
      product_id: entity.EntityId,
      title: entity.Name || 'Untitled Product',
      status: 'Active',
      visibility: entity.Visibility || 'Limited',
      entity_type: entity.EntityType,
      last_modified: entity.LastModifiedDate,
    }));

    return NextResponse.json({
      success: true,
      products: products,
      total: products.length,
    });
  } catch (error: any) {
    console.error('List marketplace products API error:', error);
    
    // Handle specific AWS errors
    if (error.name === 'AccessDeniedException') {
      return NextResponse.json({
        success: true,
        products: [],
        total: 0,
        message: 'No marketplace access or no products found',
      });
    }
    
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to list marketplace products' },
      { status: 500 }
    );
  }
}
