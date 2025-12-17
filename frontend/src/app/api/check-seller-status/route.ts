import { NextRequest, NextResponse } from 'next/server';
import { 
  MarketplaceCatalogClient, 
  ListEntitiesCommand 
} from '@aws-sdk/client-marketplace-catalog';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = body;

    if (!aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing required credentials' },
        { status: 400 }
      );
    }

    // Use AWS SDK directly to check seller status
    const catalogClient = new MarketplaceCatalogClient({
      region: 'us-east-1',
      credentials: {
        accessKeyId: aws_access_key_id,
        secretAccessKey: aws_secret_access_key,
        sessionToken: aws_session_token,
      },
    });

    let sellerStatus = 'NOT_REGISTERED';
    let ownedProducts: any[] = [];

    try {
      // Try to list products - if this works, seller is registered
      const listCommand = new ListEntitiesCommand({
        Catalog: 'AWSMarketplace',
        EntityType: 'SaaSProduct',
      });
      
      const response = await catalogClient.send(listCommand);
      
      if (response.EntitySummaryList) {
        sellerStatus = 'APPROVED';
        ownedProducts = response.EntitySummaryList.map((entity) => ({
          product_id: entity.EntityId,
          title: entity.Name || 'Untitled Product',
          status: entity.EntityType || 'Unknown',
          visibility: 'Limited',
        }));
      }
    } catch (err: any) {
      // If access denied, seller might not be registered
      if (err.name === 'AccessDeniedException') {
        sellerStatus = 'NOT_REGISTERED';
      } else {
        // Other errors - assume registered but no products
        sellerStatus = 'APPROVED';
      }
    }

    return NextResponse.json({
      success: true,
      seller_status: sellerStatus,
      is_registered: sellerStatus === 'APPROVED',
      account_id: '',
      owned_products: ownedProducts,
      products: ownedProducts,
      message: sellerStatus === 'APPROVED' 
        ? 'Seller account is active' 
        : 'Please register as a seller first',
    });
  } catch (error: any) {
    console.error('Check seller status error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
