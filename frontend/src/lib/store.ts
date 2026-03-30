// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AWSCredentials {
  accessKeyId?: string;
  secretAccessKey?: string;
  sessionToken?: string;
  region?: string;
  // Legacy snake_case aliases for compatibility
  aws_access_key_id?: string;
  aws_secret_access_key?: string;
  aws_session_token?: string;
}

export interface AccountInfo {
  account_id: string;
  user_arn: string;
  user_name?: string;
  region_type: 'AWS_INC' | 'AWS_INDIA' | 'UNKNOWN';
  organization: string;
}

export interface SellerStatus {
  is_registered: boolean;
  seller_id?: string;
  status?: string;
  account_id?: string;
  seller_status?: string;
  products?: Array<{
    product_id: string;
    title: string;
    status: string;
    visibility: string;
    product_type?: string;
    saas_status?: string;
  }>;
  owned_products?: Array<{
    product_id: string;
    title: string;
    status: string;
    visibility: string;
    product_type?: string;
    saas_status?: string;
  }>;
}

export interface ProductContext {
  product_urls: string[];
  documentation_urls?: string[];
  documentation_url?: string;
  product_name?: string;
  product_description?: string;
  additional_context?: string;
}

export interface AnalysisResult {
  title: string;
  short_description: string;
  long_description: string;
  highlights: string[];
  categories: string[];
  search_keywords: string[];
  pricing_model: string;
  pricing_dimensions: any[];
  support_description: string;
  features: string[];
  // Legacy fields for compatibility
  product_type?: string;
  target_audience?: string;
  key_features?: string[];
  value_proposition?: string;
  use_cases?: string[];
  competitive_advantages?: string[];
  generated_content?: {
    title: string;
    short_description: string;
    long_description: string;
    highlights: string[];
    search_keywords: string[];
  };
}

export interface PricingDimension {
  name: string;
  key: string;
  description: string;
  type: 'Entitled' | 'Metered';
  unit?: string;
  rates?: Record<string, number>;
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
  pricing_dimensions?: any[];
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

export type WorkflowStep = 
  | 'credentials'
  | 'seller_registration'
  | 'gather_context'
  | 'ai_analysis'
  | 'analyze_product'
  | 'review_suggestions'
  | 'create_listing'
  | 'listing_success'
  | 'saas_deployment'
  | number;

interface StoreState {
  // Authentication
  isAuthenticated: boolean;
  credentials: AWSCredentials | null;
  accountInfo: AccountInfo | null;
  sellerStatus: SellerStatus | null;
  
  // Workflow
  currentStep: WorkflowStep;
  completedSteps: WorkflowStep[];
  
  // Product data
  productContext: ProductContext | null;
  analysisResult: AnalysisResult | null;
  listingData: ListingData | null;
  
  // IDs
  productId: string | null;
  offerId: string | null;
  stackId: string | null;
  
  // Actions
  setCredentials: (credentials: AWSCredentials, sessionId?: string) => void;
  setAccountInfo: (info: AccountInfo) => void;
  setSellerStatus: (status: SellerStatus) => void;
  setCurrentStep: (step: WorkflowStep) => void;
  setProductContext: (context: ProductContext) => void;
  setAnalysisResult: (result: AnalysisResult) => void;
  setListingData: (data: Partial<ListingData>) => void;
  setProductId: (id: string) => void;
  setOfferId: (id: string) => void;
  setStackId: (id: string) => void;
  clearCredentials: () => void;
  reset: () => void;
}


const initialState = {
  isAuthenticated: false,
  credentials: null,
  accountInfo: null,
  sellerStatus: null,
  currentStep: 'credentials' as WorkflowStep,
  completedSteps: [] as WorkflowStep[],
  productContext: null,
  analysisResult: null,
  listingData: null,
  productId: null,
  offerId: null,
  stackId: null,
};

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setCredentials: (credentials, _sessionId) =>
        set({ credentials, isAuthenticated: true }),

      setAccountInfo: (accountInfo) =>
        set({ accountInfo }),

      setSellerStatus: (sellerStatus) =>
        set({ sellerStatus }),

      setCurrentStep: (currentStep) => {
        const { completedSteps } = get();
        const steps: WorkflowStep[] = [
          'credentials',
          'seller_registration',
          'gather_context',
          'ai_analysis',
          'review_suggestions',
          'create_listing',
          'listing_success',
          'saas_deployment',
        ];
        const currentIndex = steps.indexOf(currentStep);
        const newCompletedSteps = steps.slice(0, currentIndex);
        set({
          currentStep,
          completedSteps: Array.from(new Set([...completedSteps, ...newCompletedSteps])),
        });
      },

      setProductContext: (productContext) =>
        set({ productContext }),

      setAnalysisResult: (analysisResult) =>
        set({ analysisResult }),

      setListingData: (data) =>
        set((state) => ({
          listingData: state.listingData
            ? { ...state.listingData, ...data }
            : (data as ListingData),
        })),

      setProductId: (productId) =>
        set({ productId }),

      setOfferId: (offerId) =>
        set({ offerId }),

      setStackId: (stackId) =>
        set({ stackId }),

      clearCredentials: () =>
        set({
          ...initialState,
        }),

      reset: () =>
        set({
          ...initialState,
        }),
    }),
    {
      name: 'marketplace-store',
    }
  )
);
