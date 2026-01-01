/**
 * Test mode routes - used when VITE_E2E_MODE=true
 * These routes bypass MSAL authentication for E2E testing
 */
import { Routes, Route } from "react-router-dom";
import { StoreMapPage } from "./pages/StoreMap";
import { AboutPage } from "./pages/About";
import { DashboardPage } from "./pages/Dashboard";
import { DailySales } from "./pages/financial/DailySales";
import { InvoiceSync } from "./pages/financial/InvoiceSync";
import { BillSplit } from "./pages/financial/BillSplit";
import { EmailTips } from "./pages/payroll/EmailTips";
import { TransformTips } from "./pages/payroll/TransformTips";
import { MPVs } from "./pages/payroll/MPVs";
import { FoodHandlerLinks } from "./pages/utilities/FoodHandlerLinks";
import { ErrorTester } from "./pages/utilities/ErrorTester";
import { PageLayout, AppShell } from "./components/layout";
import { ErrorBoundary } from "./components/ErrorBoundary";

export function TestModeRoutes() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Landing redirects to dashboard in test mode */}
        <Route
          path="/"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <DashboardPage />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/map"
          element={
            <PageLayout>
              <ErrorBoundary>
                <StoreMapPage />
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/about"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AboutPage />
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <DashboardPage />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/financial/daily-sales"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <DailySales />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/financial/invoice-sync"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <InvoiceSync />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/financial/bill-split"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <BillSplit />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/email-tips"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <EmailTips />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/transform-tips"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <TransformTips />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/mpvs"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <MPVs />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/utilities/food-handler-links"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <FoodHandlerLinks />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/utilities/error-tester"
          element={
            <PageLayout>
              <ErrorBoundary>
                <AppShell showSidebar={true}>
                  <ErrorTester />
                </AppShell>
              </ErrorBoundary>
            </PageLayout>
          }
        />
      </Routes>
    </ErrorBoundary>
  );
}
