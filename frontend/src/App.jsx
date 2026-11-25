import { useEffect } from "react";

import { AppShell, PublicLayout } from "./components/Layout";
import { Loading } from "./components/ui";
import { AuthProvider, useAuth } from "./context/AuthContext";
import AnalysisPage from "./pages/AnalysisPage";
import AuditPage from "./pages/AuditPage";
import CaseDetailPage from "./pages/CaseDetailPage";
import ComplaintsPage from "./pages/ComplaintsPage";
import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import EmergencyPage from "./pages/EmergencyPage";
import EvidencePage from "./pages/EvidencePage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RegulatoryPage from "./pages/RegulatoryPage";
import ReportWizardPage from "./pages/ReportWizardPage";
import RoadmapPage from "./pages/RoadmapPage";
import TransactionsPage from "./pages/TransactionsPage";
import { Link, matchCaseRoute, navigate, usePath } from "./router";

function NotFound() {
  return (
    <div className="stack">
      <h1>Page not found</h1>
      <p className="muted">That address does not exist in this prototype.</p>
      <p>
        <Link to="/dashboard" className="button button-primary">
          Back to the dashboard
        </Link>
      </p>
    </div>
  );
}

function Routes() {
  const { user, loading } = useAuth();
  const path = usePath();
  const caseRoute = matchCaseRoute(path);
  const isAuthRoute = path === "/login" || path === "/register";
  const isPublic = path === "/" || path === "/emergency";

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!user && !isAuthRoute && !isPublic) {
      navigate("/login");
    }
    if (user && isAuthRoute) {
      navigate("/dashboard");
    }
  }, [loading, user, isAuthRoute, isPublic]);

  if (loading) {
    return (
      <div className="auth-shell" style={{ gridTemplateColumns: "1fr" }}>
        <div className="auth-main">
          <Loading label="Checking your session…" />
        </div>
      </div>
    );
  }

  if (!user) {
    if (path === "/register") {
      return <RegisterPage />;
    }
    if (path === "/") {
      return (
        <PublicLayout>
          <LandingPage />
        </PublicLayout>
      );
    }
    if (path === "/emergency") {
      return (
        <PublicLayout>
          <div className="public-section" style={{ paddingTop: "2.5rem" }}>
            <EmergencyPage />
          </div>
        </PublicLayout>
      );
    }
    return <LoginPage />;
  }

  if (path === "/") {
    return (
      <PublicLayout>
        <LandingPage />
      </PublicLayout>
    );
  }

  let page = <DashboardPage />;
  if (path === "/dashboard") {
    page = <DashboardPage />;
  } else if (path === "/emergency") {
    page = <EmergencyPage />;
  } else if (path === "/report") {
    page = <ReportWizardPage />;
  } else if (path === "/transactions") {
    page = <TransactionsPage />;
  } else if (path === "/evidence") {
    page = <EvidencePage />;
  } else if (path === "/analysis") {
    page = <AnalysisPage />;
  } else if (path === "/regulatory") {
    page = <RegulatoryPage />;
  } else if (path === "/roadmap") {
    page = <RoadmapPage />;
  } else if (path === "/complaints") {
    page = <ComplaintsPage />;
  } else if (path === "/documents") {
    page = <DocumentsPage />;
  } else if (path === "/audit") {
    page = <AuditPage />;
  } else if (caseRoute) {
    page = <CaseDetailPage caseId={caseRoute.caseId} section={caseRoute.section} />;
  } else if (path !== "/login" && path !== "/register") {
    page = <NotFound />;
  }

  return <AppShell>{page}</AppShell>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes />
    </AuthProvider>
  );
}
