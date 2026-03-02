import { NextRequest, NextResponse } from 'next/server';
import { MarketplaceCatalogClient, DescribeEntityCommand } from '@aws-sdk/client-marketplace-catalog';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { product_id, credentials } = body;

    const { aws_access_key_id, aws_secret_access_key, aws_session_token } = credentials;

    if (!product_id || !aws_access_key_id || !aws_secret_access_key) {
      return NextResponse.json(
        { success: false, error: 'Missing required parameters' },
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

    // Describe the product entity to get pricing dimensions
    const describeCommand = new DescribeEntityCommand({
      Catalog: 'AWSMarketplace',
      EntityId: product_id,
    });

    const response = await catalogClient.send(describeCommand);
    
    if (!response.Details) {
      return NextResponse.json(
        { success: false, error: 'No product details found' },
        { status: 404 }
      );
    }

    const details = JSON.parse(response.Details);
    
    // Extract pricing dimensions from product details
    let pricingDimensions = [];
    
    // Dimensions are at the top level of the product details
    if (details.Dimensions && Array.isArray(details.Dimensions)) {
      pricingDimensions = details.Dimensions.map((dim: any) => ({
        name: dim.Name,
        key: dim.Key,
        description: dim.Description || '',
        unit: dim.Unit || '',
        types: dim.Types || [],
        // Determine if it's metered based on Types array
        type: dim.Types && dim.Types.includes('ExternallyMetered') ? 'Metered' : 'Entitled',
      }));
    }
    
    // Legacy: Also check in Versions for backward compatibility
    if (pricingDimensions.length === 0 && details.Versions && details.Versions.length > 0) {
      const latestVersion = details.Versions[details.Versions.length - 1];
      
      // For SaaS products, dimensions might be in DeliveryOptions
      if (latestVersion.DeliveryOptions && latestVersion.DeliveryOptions.length > 0) {
        const deliveryOption = latestVersion.DeliveryOptions[0];
        
        if (deliveryOption.Details && deliveryOption.Details.SaaSUrlDeliveryOptionDetails) {
          const saasDetails = deliveryOption.Details.SaaSUrlDeliveryOptionDetails;
          
          // Extract dimensions from pricing
          if (saasDetails.Pricing) {
            const pricing = saasDetails.Pricing;
            
            // Contract pricing dimensions
            if (pricing.ContractPricing && pricing.ContractPricing.Dimensions) {
              pricingDimensions = pricing.ContractPricing.Dimensions.map((dim: any) => ({
                name: dim.Name,
                key: dim.Key,
                description: dim.Description || '',
                type: 'Entitled',
              }));
            }
            
            // Subscription (usage-based) pricing dimensions
            if (pricing.SubscriptionPricing && pricing.SubscriptionPricing.Dimensions) {
              const subscriptionDims = pricing.SubscriptionPricing.Dimensions.map((dim: any) => ({
                name: dim.Name,
                key: dim.Key,
                description: dim.Description || '',
                type: 'Metered',
              }));
              pricingDimensions = [...pricingDimensions, ...subscriptionDims];
            }
          }
        }
      }
    }

    return NextResponse.json({
      success: true,
      pricing_dimensions: pricingDimensions,
      product_id,
    });
  } catch (error: any) {
    console.error('[GET PRICING DIMENSIONS] Error:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Failed to retrieve pricing dimensions' },
      { status: 500 }
    );
  }
}
