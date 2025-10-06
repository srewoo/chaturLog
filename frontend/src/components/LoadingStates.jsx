import React from 'react';
import { Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Skeleton } from './ui/skeleton';

/**
 * Loading Spinner Component
 * Simple centered loading spinner with optional text
 */
export const LoadingSpinner = ({ text = 'Loading...', size = 'default' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="flex flex-col items-center justify-center py-12" data-testid="loading-spinner">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600 mb-4`} />
      {text && <p className="text-sm text-slate-600">{text}</p>}
    </div>
  );
};

/**
 * Full Page Loading Component
 * Covers the entire viewport with a loading indicator
 */
export const FullPageLoading = ({ text = 'Loading...' }) => {
  return (
    <div 
      className="fixed inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50"
      data-testid="full-page-loading"
    >
      <div className="text-center">
        <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-lg font-medium text-slate-700">{text}</p>
      </div>
    </div>
  );
};

/**
 * Analysis Card Skeleton
 * Loading state for analysis history items
 */
export const AnalysisCardSkeleton = () => {
  return (
    <div 
      className="p-4 border border-slate-200 rounded-lg space-y-3"
      data-testid="analysis-card-skeleton"
    >
      <div className="flex items-center space-x-2">
        <Skeleton className="h-4 w-4 rounded" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="flex items-center space-x-3">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-3 w-3 rounded-full" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
};

/**
 * Pattern Card Skeleton
 * Loading state for error pattern displays
 */
export const PatternCardSkeleton = () => {
  return (
    <div 
      className="p-4 border border-slate-200 rounded-lg space-y-3"
      data-testid="pattern-card-skeleton"
    >
      <div className="flex items-center justify-between">
        <div className="space-y-2 flex-1">
          <div className="flex items-center space-x-2">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
        <Skeleton className="h-5 w-8" />
      </div>
    </div>
  );
};

/**
 * Test Case Card Skeleton
 * Loading state for generated test cases
 */
export const TestCaseCardSkeleton = () => {
  return (
    <div 
      className="border border-slate-200 rounded-lg overflow-hidden"
      data-testid="test-case-skeleton"
    >
      <div className="p-4 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="space-y-2 flex-1">
            <div className="flex items-center space-x-2">
              <Skeleton className="h-5 w-16 rounded" />
              <Skeleton className="h-5 w-24 rounded-full" />
            </div>
            <Skeleton className="h-4 w-3/4" />
          </div>
          <Skeleton className="h-9 w-28 rounded" />
        </div>
      </div>
      <div className="p-4 space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
};

/**
 * Dashboard Loading State
 * Complete loading state for the main dashboard
 */
export const DashboardLoading = () => {
  return (
    <div className="space-y-6" data-testid="dashboard-loading">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Upload Area Skeleton */}
          <div className="border-2 border-dashed border-slate-200 rounded-lg p-8 text-center">
            <Skeleton className="h-12 w-12 mx-auto mb-4 rounded" />
            <Skeleton className="h-5 w-48 mx-auto mb-2" />
            <Skeleton className="h-4 w-32 mx-auto" />
          </div>

          {/* Config Options Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full rounded" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full rounded" />
            </div>
          </div>

          {/* Action Button Skeleton */}
          <Skeleton className="h-10 w-full rounded" />
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Analysis Results Loading
 * Loading state for analysis results section
 */
export const AnalysisResultsLoading = () => {
  return (
    <div className="space-y-6" data-testid="analysis-results-loading">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          <PatternCardSkeleton />
          <PatternCardSkeleton />
          <PatternCardSkeleton />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          <TestCaseCardSkeleton />
          <TestCaseCardSkeleton />
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * History Loading
 * Loading state for analysis history tab
 */
export const HistoryLoading = () => {
  return (
    <div className="space-y-3" data-testid="history-loading">
      <AnalysisCardSkeleton />
      <AnalysisCardSkeleton />
      <AnalysisCardSkeleton />
      <AnalysisCardSkeleton />
      <AnalysisCardSkeleton />
    </div>
  );
};

export default {
  LoadingSpinner,
  FullPageLoading,
  AnalysisCardSkeleton,
  PatternCardSkeleton,
  TestCaseCardSkeleton,
  DashboardLoading,
  AnalysisResultsLoading,
  HistoryLoading
};

