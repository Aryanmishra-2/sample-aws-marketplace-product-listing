export type WorkflowStep =
  | 'credentials'
  | 'seller-registration'
  | 'product-info'
  | 'ai-analysis'
  | 'review-suggestions'
  | 'create-listing'
  | 'listing-success'
  | 'saas-integration'
  | 'workflow-orchestrator';

export interface AWSCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  sessionToken?: string;
}

export interface AccountValidation {
  success: boolean;
  accountId: string;
  regionType: 'AWS_INC' | 'AWS_INDIA' | 'UNKNOWN';
  userArn: string;
  organization: string;
}

export interface SellerStatus {
  sellerStatus: 'APPROVED' | 'PENDING' | 'NOT_REGISTERED' | 'UNKNOWN';
  productsCount?: number;
}

export interface ProductContext {
  websiteUrl: string;
  docsUrl?: string;
  pricingUrl?: string;
  productDescription?: string;
}

export interface AIAnalysis {
  productType: string;
  targetAudience: string;
  keyFeatures: string[];
  valueProposition: string;
  useCases: string[];
  competitiveAdvantages: string[];
}

export interface GeneratedContent {
  productTitle: string;
  shortDescription: string;
  longDescription: string;
  highlights: string[];
  searchKeywords: string[];
  categories: string[];
}

export interface PricingSuggestion {
  recommendedModel: 'Contract' | 'Usage' | 'Contract with Consumption';
  reasoning: string;
  suggestedDimensions: string[];
  contractDurations: string[];
}

export interface PricingDimension {
  name: string;
  key: string;
  description: string;
  type: 'Entitled' | 'Metered';
}

export interface ListingData {
  productTitle: string;
  logoS3Url: string;
  shortDescription: string;
  longDescription: string;
  highlights: string[];
  categories: string[];
  searchKeywords: string[];
  supportEmail: string;
  fulfillmentUrl: string;
  supportDescription: string;
  pricingModel: 'Contract' | 'Usage';
  uiPricingModel: 'Contract' | 'Usage' | 'Contract with Consumption';
  dimensions: PricingDimension[];
  contractDurations: string[];
  purchasingOption: string;
  refundPolicy: string;
  eulaType: 'scmp' | 'custom';
  customEulaUrl?: string;
  availabilityType: string;
  excludedCountries: string[];
  allowedCountries: string[];
  buyerAccounts: string[];
  autoPublishToLimited: boolean;
  offerName: string;
  offerDescription: string;
  buyerAccountsForLimited: string[];
}

export interface WorkflowData {
  productId?: string;
  offerId?: string;
  pricingDimensions?: PricingDimension[];
  email?: string;
  stackId?: string;
  fulfillmentUrl?: string;
  lambdaFunctionName?: string;
}

export interface WorkflowState {
  currentStep: WorkflowStep;
  credentials?: AWSCredentials;
  accountValidation?: AccountValidation;
  sellerStatus?: SellerStatus;
  productContext?: ProductContext;
  aiAnalysis?: string;
  generatedContent?: string;
  pricingSuggestion?: string;
  listingData?: ListingData;
  workflowData?: WorkflowData;
  createdProductId?: string;
  createdOfferId?: string;
  listingCreated?: boolean;
  publishedToLimited?: boolean;
}
