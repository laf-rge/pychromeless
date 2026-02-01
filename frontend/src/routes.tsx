import { Routes, Route } from "react-router-dom";
import { AuthenticatedTemplate, UnauthenticatedTemplate } from "@azure/msal-react";
import { LandingPage } from "./pages/Landing";
import { StoreMapPage } from "./pages/StoreMap";
import { AboutPage } from "./pages/About";
import { DashboardPage } from "./pages/Dashboard";
import { DailySales } from "./pages/financial/DailySales";
import { InvoiceSync } from "./pages/financial/InvoiceSync";
import { BillSplit } from "./pages/financial/BillSplit";
import { GrubhubImport } from "./pages/financial/GrubhubImport";
import { FdmsImport } from "./pages/financial/FdmsImport";
import { EmailTips } from "./pages/payroll/EmailTips";
import { TransformTips } from "./pages/payroll/TransformTips";
import { MPVs } from "./pages/payroll/MPVs";
import { PayrollAllocation } from "./pages/payroll/PayrollAllocation";
import { FoodHandlerLinks } from "./pages/utilities/FoodHandlerLinks";
import { ErrorTester } from "./pages/utilities/ErrorTester";
import { QuickBooksConnection } from "./pages/settings/QuickBooksConnection";
import { QBCallback } from "./pages/settings/QBCallback";
import { POS } from "./pages/POS";
import { CareersPage } from "./pages/Careers";
import { AboutNextPage } from "./pages/AboutNext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { PageLayout, AppShell } from "./components/layout";
import { ErrorBoundary } from "./components/ErrorBoundary";

export function AppRoutes() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route
          path="/"
          element={
            <PageLayout>
              <UnauthenticatedTemplate>
                <ErrorBoundary>
                  <LandingPage />
                </ErrorBoundary>
              </UnauthenticatedTemplate>
              <AuthenticatedTemplate>
                <ProtectedRoute>
                  <ErrorBoundary>
                    <AppShell showSidebar={true}>
                      <DashboardPage />
                    </AppShell>
                  </ErrorBoundary>
                </ProtectedRoute>
              </AuthenticatedTemplate>
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
          path="/locations"
          element={
            <PageLayout>
              <ErrorBoundary>
                <StoreMapPage />
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/careers"
          element={
            <PageLayout>
              <ErrorBoundary>
                <CareersPage />
              </ErrorBoundary>
            </PageLayout>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <DashboardPage />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/financial/daily-sales"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <DailySales />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/financial/invoice-sync"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <InvoiceSync />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/financial/bill-split"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <BillSplit />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/financial/grubhub-import"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <GrubhubImport />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/financial/fdms-import"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <FdmsImport />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/email-tips"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <EmailTips />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/transform-tips"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <TransformTips />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/mpvs"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <MPVs />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/payroll/allocation"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <PayrollAllocation />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/utilities/food-handler-links"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <FoodHandlerLinks />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        {import.meta.env.DEV && (
          <Route
            path="/about-next"
            element={
              <PageLayout>
                <ErrorBoundary>
                  <AboutNextPage />
                </ErrorBoundary>
              </PageLayout>
            }
          />
        )}
        {import.meta.env.DEV && (
          <Route
            path="/utilities/error-tester"
            element={
              <PageLayout>
                <ProtectedRoute>
                  <ErrorBoundary>
                    <AppShell showSidebar={true}>
                      <ErrorTester />
                    </AppShell>
                  </ErrorBoundary>
                </ProtectedRoute>
              </PageLayout>
            }
          />
        )}
        <Route
          path="/settings/quickbooks"
          element={
            <PageLayout>
              <ProtectedRoute>
                <ErrorBoundary>
                  <AppShell showSidebar={true}>
                    <QuickBooksConnection />
                  </AppShell>
                </ErrorBoundary>
              </ProtectedRoute>
            </PageLayout>
          }
        />
        <Route
          path="/qb-callback"
          element={
            <ErrorBoundary>
              <QBCallback />
            </ErrorBoundary>
          }
        />
        <Route
          path="/pos"
          element={
            <ErrorBoundary>
              <POS />
            </ErrorBoundary>
          }
        />
      </Routes>
    </ErrorBoundary>
  );
}
